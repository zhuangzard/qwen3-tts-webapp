"""
MPPI Closed-Loop Control Demo for PhysSurgeon
Self-contained: generates synthetic tissue mesh + trains GNN briefly + runs MPPI.
Demonstrates GNN world model for surgical planning on A100.
"""
import torch, torch.nn as nn, json, time, os, math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"Device: {DEVICE}")

# ─── 1. Generate Synthetic Tissue Mesh ───
print("Generating synthetic tissue mesh...")

def create_tissue_mesh(nx=8, ny=8, nz=4, size_x=0.15, size_y=0.09, size_z=0.04):
    """Create a regular tetrahedral mesh representing liver tissue."""
    # Grid vertices
    xs = torch.linspace(-size_x/2, size_x/2, nx)
    ys = torch.linspace(-size_y/2, size_y/2, ny)
    zs = torch.linspace(0.005, 0.005 + size_z, nz)
    
    verts = []
    for iz in range(nz):
        for iy in range(ny):
            for ix in range(nx):
                verts.append([xs[ix].item(), ys[iy].item(), zs[iz].item()])
    pos_rest = torch.tensor(verts, dtype=torch.float32)
    N = pos_rest.shape[0]
    
    # Boundary: bottom layer + side edges
    is_boundary = torch.zeros(N)
    for i in range(N):
        iz = i // (nx * ny)
        iy = (i % (nx * ny)) // nx
        ix = i % nx
        if iz == 0 or ix == 0 or ix == nx-1 or iy == 0 or iy == ny-1:
            is_boundary[i] = 1.0
    
    # Tetrahedralize: each cube → 5 tets
    tets = []
    for iz in range(nz-1):
        for iy in range(ny-1):
            for ix in range(nx-1):
                def idx(x, y, z): return z * nx * ny + y * nx + x
                v0 = idx(ix, iy, iz)
                v1 = idx(ix+1, iy, iz)
                v2 = idx(ix, iy+1, iz)
                v3 = idx(ix+1, iy+1, iz)
                v4 = idx(ix, iy, iz+1)
                v5 = idx(ix+1, iy, iz+1)
                v6 = idx(ix, iy+1, iz+1)
                v7 = idx(ix+1, iy+1, iz+1)
                # 5-tet decomposition of a cube
                tets.append([v0, v1, v3, v5])
                tets.append([v0, v3, v2, v6])
                tets.append([v0, v5, v4, v6])
                tets.append([v3, v5, v6, v7])
                tets.append([v0, v3, v5, v6])
    
    tets = torch.tensor(tets, dtype=torch.long)
    return pos_rest, is_boundary, tets, (nx, ny, nz)

pos_rest, is_boundary, tets, (NX, NY, NZ) = create_tissue_mesh()
N_NODES = pos_rest.shape[0]
print(f"Mesh: {N_NODES} nodes, {tets.shape[0]} tets, {int(is_boundary.sum())} boundary")

# Build edges from tets
edge_pairs = set()
for tet in tets:
    for i in range(4):
        for j in range(i+1, 4):
            a, b = tet[i].item(), tet[j].item()
            edge_pairs.add((min(a, b), max(a, b)))
sl, dl = [], []
for a, b in sorted(edge_pairs):
    sl.extend([a, b]); dl.extend([b, a])
ei_cpu = torch.tensor([sl, dl], dtype=torch.long)
dx_rest = pos_rest[ei_cpu[1]] - pos_rest[ei_cpu[0]]
ef_static = torch.cat([dx_rest, dx_rest.norm(dim=-1, keepdim=True)], dim=-1).to(DEVICE)
ei = ei_cpu.to(DEVICE)

# ─── 2. Model Definition ───
class AntisymMP(nn.Module):
    def __init__(self, h):
        super().__init__()
        self.efn = nn.Sequential(nn.Linear(3*h, h), nn.SiLU(), nn.Linear(h, h))
        self.nfn = nn.Sequential(nn.Linear(2*h, h), nn.SiLU(), nn.Linear(h, h))
    def forward(self, h, e, ei):
        B, N, H = h.shape; src, dst = ei[0], ei[1]
        fwd = torch.arange(0, ei.shape[1], 2, device=h.device)
        ha, hb = h[:, src[fwd]], h[:, dst[fwd]]
        es = (e[:, fwd] + e[:, fwd+1]) / 2
        fab = self.efn(torch.cat([ha, hb, es], -1))
        fba = self.efn(torch.cat([hb, ha, es], -1))
        mf = fab - fba; mb = -mf
        msgs = torch.zeros(B, ei.shape[1], H, device=h.device)
        msgs[:, fwd] = mf; msgs[:, fwd+1] = mb
        e2 = e + msgs
        agg = torch.zeros_like(h)
        agg.scatter_add_(1, dst.unsqueeze(0).unsqueeze(-1).expand(B, -1, H), msgs)
        return h + self.nfn(torch.cat([h, agg], -1)), e2

class ModelD(nn.Module):
    def __init__(self):
        super().__init__()
        H = 64
        self.ne = nn.Sequential(nn.Linear(7, H), nn.SiLU(), nn.Linear(H, H))
        self.ee = nn.Sequential(nn.Linear(4, H), nn.SiLU(), nn.Linear(H, H))
        self.mp = nn.ModuleList([AntisymMP(H) for _ in range(4)])
        self.dec = nn.Linear(H, 3)
    def forward(self, nf, ef, ei):
        h = self.ne(nf); e = self.ee(ef).unsqueeze(0).expand(h.shape[0], -1, -1)
        for m in self.mp: h, e = m(h, e, ei)
        return self.dec(h)

pos_rest_d = pos_rest.to(DEVICE)
is_bnd_d = is_boundary.to(DEVICE)

def make_nf(pos_current, vel):
    rel = pos_current - pos_rest_d.unsqueeze(0)
    bnd = is_bnd_d.unsqueeze(0).unsqueeze(-1).expand(pos_current.shape[0], -1, 1)
    return torch.cat([rel, vel, bnd], dim=-1)

# ─── 3. Generate Training Data (simple spring physics) ───
print("Generating training data with spring physics...")

def spring_physics_step(pos, vel, pos_rest, is_boundary, dt=0.01, stiffness=500.0, damping=10.0):
    """Simple spring-damper physics for training data generation."""
    # Each node connected to rest position by spring
    force = -stiffness * (pos - pos_rest) - damping * vel
    # Boundary nodes don't move
    bnd = is_boundary.unsqueeze(-1)
    acc = force * (1 - bnd)
    new_vel = (vel + acc * dt) * (1 - bnd)
    delta = new_vel * dt
    return delta

N_TRAIN = 2000
train_pos = []
train_delta = []

torch.manual_seed(42)
for i in range(N_TRAIN):
    # Random perturbation from rest
    pert = torch.randn(N_NODES, 3) * 0.003  # ~3mm perturbation
    pert *= (1 - is_boundary.unsqueeze(-1))  # boundary fixed
    pos_t = pos_rest + pert
    vel_t = torch.randn(N_NODES, 3) * 0.01 * (1 - is_boundary.unsqueeze(-1))
    
    delta = spring_physics_step(pos_t, vel_t, pos_rest, is_boundary)
    train_pos.append(pos_t)
    train_delta.append(delta)

train_pos = torch.stack(train_pos)
train_delta = torch.stack(train_delta)
print(f"Training data: {train_pos.shape}, delta range: [{train_delta.min():.6f}, {train_delta.max():.6f}]")

# ─── 4. Train GNN World Model ───
print("Training GNN world model...")
model = ModelD().to(DEVICE)
opt = torch.optim.AdamW(model.parameters(), lr=3e-4, weight_decay=1e-5)
BS = 64
best_loss = 1e9

for ep in range(1, 21):
    model.train()
    perm = torch.randperm(N_TRAIN)
    ep_loss = 0; nb = 0
    for i in range(0, N_TRAIN, BS):
        idx = perm[i:i+BS]
        pb = train_pos[idx].to(DEVICE)
        db = train_delta[idx].to(DEVICE)
        vel = torch.zeros_like(pb)  # simplified: zero vel
        nf = make_nf(pb, vel)
        pred = model(nf, ef_static, ei)
        loss = ((pred - db)**2).mean()
        opt.zero_grad(); loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 0.5)
        opt.step()
        ep_loss += loss.item(); nb += 1
    avg = ep_loss / nb
    if avg < best_loss: best_loss = avg
    if ep % 5 == 0:
        print(f"  Epoch {ep:3d} | Loss: {avg:.8f}")

model.eval()
print(f"Training complete. Best loss: {best_loss:.8f}")
print(f"Model params: {sum(p.numel() for p in model.parameters()):,}")

# ─── 5. MPPI Controller ───
# Select tool and target nodes
non_bnd_mask = is_boundary < 0.5
non_bnd_idx = torch.where(non_bnd_mask)[0]
z_vals = pos_rest[non_bnd_idx, 2]
# Pick top nodes by z-coordinate as tool contact region
top_k = 8
tool_local_idx = z_vals.argsort(descending=True)[:top_k]
tool_nodes = non_bnd_idx[tool_local_idx].to(DEVICE)

# Target: lift tool nodes +5mm in z
TARGET_DZ = 0.005  # 5mm
target_pos = pos_rest[tool_nodes.cpu()].clone()
target_pos[:, 2] += TARGET_DZ
target_pos = target_pos.to(DEVICE)

print(f"\nTool nodes: {tool_nodes.cpu().tolist()}")
print(f"Tool rest z: {pos_rest[tool_nodes.cpu(), 2].mean():.4f}m")
print(f"Target z: {target_pos[:, 2].mean():.4f}m (+{TARGET_DZ*1000:.1f}mm)")

@torch.no_grad()
def gnn_step(pos_current, vel):
    nf = make_nf(pos_current, vel)
    return model(nf, ef_static, ei)

class MPPIController:
    def __init__(self, K=512, H=10, lam=0.01, sigma=0.001,
                 w_goal=500.0, w_smooth=1.0, w_force=0.1):
        self.K = K; self.H = H; self.lam = lam; self.sigma = sigma
        self.w_goal = w_goal; self.w_smooth = w_smooth; self.w_force = w_force
        self.n_tool = len(tool_nodes)
        self.u_mean = torch.zeros(H, self.n_tool, 3, device=DEVICE)

    @torch.no_grad()
    def rollout_batch(self, pos0, vel0, force_trajs):
        K = force_trajs.shape[0]
        pos = pos0.expand(K, -1, -1).clone()
        vel = vel0.expand(K, -1, -1).clone()
        # Track intermediate goal errors for horizon cost
        total_goal_cost = torch.zeros(K, device=DEVICE)
        
        for t in range(self.H):
            delta = gnn_step(pos, vel)
            force_t = force_trajs[:, t]
            delta[:, tool_nodes, :] += force_t
            # Boundary nodes stay fixed
            bnd_mask = is_bnd_d.unsqueeze(0).unsqueeze(-1)
            delta = delta * (1 - bnd_mask)
            new_pos = pos + delta
            vel = delta
            pos = new_pos
            # Accumulate goal cost over horizon (more weight on later steps)
            tool_pos = pos[:, tool_nodes, :]
            step_cost = ((tool_pos - target_pos.unsqueeze(0))**2).sum(dim=-1).mean(dim=-1)
            total_goal_cost += step_cost * (t + 1) / self.H
        
        return pos, total_goal_cost

    def plan(self, pos0, vel0):
        K, H = self.K, self.H
        noise = self.sigma * torch.randn(K, H, self.n_tool, 3, device=DEVICE)
        force_trajs = self.u_mean.unsqueeze(0) + noise

        pos_final, goal_cost = self.rollout_batch(pos0, vel0, force_trajs)
        
        # Force penalties
        force_mag = (force_trajs**2).sum(dim=-1).mean(dim=(1,2))
        if H > 1:
            df = force_trajs[:, 1:] - force_trajs[:, :-1]
            smooth = (df**2).sum(dim=-1).mean(dim=(1,2))
        else:
            smooth = torch.zeros(K, device=DEVICE)

        costs = self.w_goal * goal_cost + self.w_force * force_mag + self.w_smooth * smooth

        costs_shifted = costs - costs.min()
        weights = torch.exp(-costs_shifted / self.lam)
        weights = weights / (weights.sum() + 1e-10)

        w = weights.view(K, 1, 1, 1)
        u_new = (w * force_trajs).sum(dim=0)

        self.u_mean = torch.cat([u_new[1:], torch.zeros(1, self.n_tool, 3, device=DEVICE)], dim=0)

        return u_new[0], costs.min().item(), costs.mean().item()

# ─── 6. Run MPPI Closed-Loop Control ───
print("\n" + "="*60)
print("MPPI Closed-Loop Control — GNN World Model")
print("="*60)

N_STEPS = 50
mppi = MPPIController(K=512, H=8, lam=0.005, sigma=0.002,
                       w_goal=1000.0, w_smooth=0.5, w_force=0.05)

pos = pos_rest_d.unsqueeze(0).clone()
vel = torch.zeros_like(pos)

log_tool_z = []
log_forces = []
log_goal_err = []
log_best_cost = []
log_all_pos = []

t_start = time.time()

for step in range(N_STEPS):
    tool_pos_now = pos[0, tool_nodes]
    goal_err_mm = ((tool_pos_now - target_pos)**2).sum(dim=-1).sqrt().mean().item() * 1000
    tool_z_mm = tool_pos_now[:, 2].mean().item() * 1000
    
    log_tool_z.append(tool_z_mm)
    log_goal_err.append(goal_err_mm)
    
    if step % 10 == 0 or step == N_STEPS - 1:
        log_all_pos.append((step, pos[0].cpu().numpy()))

    action, best_cost, mean_cost = mppi.plan(pos, vel)
    log_forces.append(action.cpu().numpy())
    log_best_cost.append(best_cost)

    # Execute
    delta = gnn_step(pos, vel)
    delta[:, tool_nodes, :] += action.unsqueeze(0)
    bnd_mask = is_bnd_d.unsqueeze(0).unsqueeze(-1)
    delta = delta * (1 - bnd_mask)
    new_pos = pos + delta
    vel = delta
    pos = new_pos

    if step % 10 == 0 or step == N_STEPS - 1:
        print(f"Step {step:3d} | Goal err: {goal_err_mm:.3f}mm | Tool z: {tool_z_mm:.2f}mm | Best cost: {best_cost:.6f}")

elapsed = time.time() - t_start
final_err = log_goal_err[-1]
rest_z_mm = pos_rest[tool_nodes.cpu(), 2].mean().item() * 1000
achieved_dz = log_tool_z[-1] - rest_z_mm

print(f"\n{'='*60}")
print(f"MPPI Complete in {elapsed:.1f}s on {DEVICE}")
print(f"Final goal error: {final_err:.3f}mm")
print(f"Achieved lift: {achieved_dz:.3f}mm (target: {TARGET_DZ*1000:.1f}mm)")
print(f"Achievement: {achieved_dz/(TARGET_DZ*1000)*100:.1f}%")

# ─── 7. Save Results ───
results = {
    'method': 'MPPI with GNN World Model (ModelD)',
    'n_nodes': N_NODES,
    'n_tets': tets.shape[0],
    'n_boundary': int(is_boundary.sum()),
    'n_tool_nodes': len(tool_nodes),
    'n_steps': N_STEPS,
    'K': mppi.K, 'H': mppi.H, 'lambda': mppi.lam, 'sigma': mppi.sigma,
    'target_dz_mm': TARGET_DZ * 1000,
    'achieved_dz_mm': round(achieved_dz, 4),
    'final_goal_err_mm': round(final_err, 4),
    'achievement_pct': round(achieved_dz/(TARGET_DZ*1000)*100, 2),
    'elapsed_s': round(elapsed, 2),
    'gnn_train_loss': round(best_loss, 8),
    'gnn_params': sum(p.numel() for p in model.parameters()),
    'goal_err_trajectory_mm': [round(x, 4) for x in log_goal_err],
    'tool_z_trajectory_mm': [round(x, 4) for x in log_tool_z],
    'device': str(DEVICE),
}
with open('mppi_results.json', 'w') as f:
    json.dump(results, f, indent=2)
print("Saved mppi_results.json")

# ─── 8. Visualization ───
log_forces_np = np.array(log_forces)
bnd_mask_np = is_boundary.numpy() > 0.5
rest_np = pos_rest.numpy()

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('MPPI Closed-Loop Control — GNN World Model for Surgical Planning', 
             fontsize=14, fontweight='bold')

# 1) Goal error over time
ax = axes[0, 0]
ax.plot(log_goal_err, 'b-', linewidth=2)
ax.axhline(y=1.0, color='g', linestyle='--', alpha=0.7, label='1.0mm threshold')
ax.set_xlabel('Control Step'); ax.set_ylabel('Goal Error (mm)')
ax.set_title('(a) Goal Tracking Error'); ax.legend(); ax.grid(True, alpha=0.3)

# 2) Tool node z-trajectory
ax = axes[0, 1]
target_z_mm = target_pos[:, 2].mean().cpu().item() * 1000
ax.plot(log_tool_z, 'r-', linewidth=2, label='Actual z')
ax.axhline(y=target_z_mm, color='g', linestyle='--', linewidth=2, label=f'Target ({target_z_mm:.1f}mm)')
ax.axhline(y=rest_z_mm, color='gray', linestyle=':', alpha=0.7, label=f'Rest ({rest_z_mm:.1f}mm)')
ax.set_xlabel('Control Step'); ax.set_ylabel('Tool Node z (mm)')
ax.set_title('(b) Tissue Lift Trajectory'); ax.legend(); ax.grid(True, alpha=0.3)

# 3) Force magnitude
ax = axes[1, 0]
force_mag = np.linalg.norm(log_forces_np, axis=-1).mean(axis=-1)
ax.plot(force_mag * 1000, 'purple', linewidth=2)
ax.set_xlabel('Control Step'); ax.set_ylabel('Mean Force Mag (×10⁻³)')
ax.set_title('(c) Control Force Magnitude'); ax.grid(True, alpha=0.3)

# 4) 3D deformation
ax = axes[1, 1]
ax.remove()
ax = fig.add_subplot(2, 2, 4, projection='3d')
ax.scatter(rest_np[~bnd_mask_np, 0]*1000, rest_np[~bnd_mask_np, 1]*1000, rest_np[~bnd_mask_np, 2]*1000,
           c='lightblue', s=3, alpha=0.3, label='Rest')
final_np = pos[0].cpu().numpy()
ax.scatter(final_np[~bnd_mask_np, 0]*1000, final_np[~bnd_mask_np, 1]*1000, final_np[~bnd_mask_np, 2]*1000,
           c='red', s=3, alpha=0.3, label='Final')
tn = tool_nodes.cpu().numpy()
ax.scatter(rest_np[tn, 0]*1000, rest_np[tn, 1]*1000, rest_np[tn, 2]*1000,
           c='blue', s=50, marker='^', label='Tool (rest)')
ax.scatter(final_np[tn, 0]*1000, final_np[tn, 1]*1000, final_np[tn, 2]*1000,
           c='green', s=50, marker='v', label='Tool (final)')
ax.set_xlabel('X (mm)'); ax.set_ylabel('Y (mm)'); ax.set_zlabel('Z (mm)')
ax.set_title('(d) Tissue Deformation'); ax.legend(fontsize=7)

plt.tight_layout()
plt.savefig('mppi_control.png', dpi=150, bbox_inches='tight')
print("Saved mppi_control.png")

# Deformation sequence
fig2, axes2 = plt.subplots(1, len(log_all_pos), figsize=(4*len(log_all_pos), 4))
if len(log_all_pos) == 1: axes2 = [axes2]
for idx, (step, pos_np) in enumerate(log_all_pos):
    ax = axes2[idx]
    ax.scatter(pos_np[~bnd_mask_np, 0]*1000, pos_np[~bnd_mask_np, 2]*1000, c='steelblue', s=5, alpha=0.5)
    ax.scatter(pos_np[bnd_mask_np, 0]*1000, pos_np[bnd_mask_np, 2]*1000, c='gray', s=3, alpha=0.3)
    ax.scatter(pos_np[tn, 0]*1000, pos_np[tn, 2]*1000, c='red', s=30, zorder=5)
    ax.axhline(y=target_z_mm, color='g', linestyle='--', alpha=0.5)
    ax.set_title(f'Step {step}')
    ax.set_xlabel('X (mm)'); ax.set_ylabel('Z (mm)')
    ymin = rest_np[:, 2].min()*1000 - 2
    ymax = rest_np[:, 2].max()*1000 + 10
    ax.set_ylim(ymin, ymax)
    ax.grid(True, alpha=0.3)

fig2.suptitle('Tissue Deformation Sequence (XZ plane)', fontweight='bold')
plt.tight_layout()
plt.savefig('mppi_sequence.png', dpi=150, bbox_inches='tight')
print("Saved mppi_sequence.png")

# Output base64 for download
import base64
for fname in ['mppi_results.json', 'mppi_control.png', 'mppi_sequence.png']:
    with open(fname, 'rb') as f:
        b64 = base64.b64encode(f.read()).decode()
    print(f"\n===BASE64_START:{fname}===")
    for i in range(0, len(b64), 4000):
        print(b64[i:i+4000])
    print(f"===BASE64_END:{fname}===")

print("\nDone!")
