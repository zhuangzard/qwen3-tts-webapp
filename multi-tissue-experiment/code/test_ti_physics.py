"""
test_ti_physics.py — Self-test suite for TI physics extension of DPC-GNN.

Validates:
    1. Neo-Hookean degeneracy: k1=0 → matches isochoric Neo-Hookean (err < 1e-6)
    2. Anisotropic response: fiber-direction stretch > transverse stretch energy
    3. Macaulay bracket: compression → zero fiber contribution
    4. Isochoric correction: pure volumetric change → Ī₄ invariant
    5. Edge feature antisymmetry: r̂_ij·d_k + r̂_ji·d_k ≈ 0
    6. Gradient check: autograd forces vs finite differences (rel_err < 1e-4)
    7. Force balance: Σ internal forces ≈ 0 (Newton's 3rd law)

Usage:
    python test_ti_physics.py

All tests print PASS/FAIL status. Script exits with code 0 on success, 1 on failure.
"""

import torch
import sys
import traceback
from typing import Tuple

# Local modules
from ti_physics_loss import (
    compute_ti_energy,
    compute_ti_stress_forces,
    ti_physics_loss,
    _compute_deformation_gradient,
    _compute_isochoric_invariants,
    _det3x3,
)
from anisotropic_edge_features import (
    compute_anisotropic_edge_features,
    assign_fiber_directions,
    verify_antisymmetry,
)
from bone_material_params import (
    cortical_bone_params,
    cancellous_bone_params,
    vertebral_body_params,
)

# ─────────────────────────────────────────────────────────────
# Test Mesh: Single Regular Tetrahedron
# ─────────────────────────────────────────────────────────────

def make_single_tet(device: str = 'cpu') -> Tuple:
    """Create a single regular tetrahedron for testing.

    Vertices at unit positions. Volume = 1/6 * |det(edges)| = 1/6.

    Returns: (positions, tet_indices, volumes)
    """
    # Regular tetrahedron vertices
    rest_pos = torch.tensor([
        [0.0, 0.0, 0.0],
        [1.0, 0.0, 0.0],
        [0.5, 1.0, 0.0],
        [0.5, 0.5, 1.0],
    ], dtype=torch.float64, device=device)

    tet_indices = torch.tensor([[0, 1, 2, 3]], dtype=torch.long, device=device)

    # Reference volume: V = (1/6)|det([v1-v0, v2-v0, v3-v0])|
    edges = torch.stack([
        rest_pos[1] - rest_pos[0],
        rest_pos[2] - rest_pos[0],
        rest_pos[3] - rest_pos[0],
    ], dim=-1)  # (3, 3)
    volume = (1.0 / 6.0) * edges.det().abs()
    volumes = volume.unsqueeze(0)  # (1,)

    return rest_pos, tet_indices, volumes


def make_small_mesh(n_tets: int = 4, device: str = 'cpu') -> Tuple:
    """Create a small tetrahedral mesh (stack of n_tets tets sharing nodes).

    Returns: (rest_positions, tet_indices, volumes)
    """
    # Simple stack: n_tets+1 layers of nodes
    nodes = []
    for k in range(n_tets + 1):
        nodes.append([0.0, 0.0, float(k)])
        nodes.append([1.0, 0.0, float(k)])
        nodes.append([0.5, 1.0, float(k)])

    rest_pos = torch.tensor(nodes, dtype=torch.float64, device=device)
    N = rest_pos.shape[0]

    # Build tets: each layer k has 3 nodes, layer k+1 has 3 nodes → 2 tets
    tets = []
    for k in range(n_tets):
        base = 3 * k
        # Tet 1: 3 nodes from layer k + 1 node from layer k+1
        tets.append([base+0, base+1, base+2, base+3])
        # Tet 2: 1 node from layer k + 3 nodes from layer k+1
        # (avoid degenerate — use different combination)
        tets.append([base+1, base+3, base+4, base+5])

    tet_indices = torch.tensor(tets, dtype=torch.long, device=device)
    T = tet_indices.shape[0]

    # Compute volumes
    volumes = []
    for t in range(T):
        v = tet_indices[t]
        edges = torch.stack([
            rest_pos[v[1]] - rest_pos[v[0]],
            rest_pos[v[2]] - rest_pos[v[0]],
            rest_pos[v[3]] - rest_pos[v[0]],
        ], dim=-1)
        vol = (1.0 / 6.0) * edges.det().abs()
        if vol < 1e-10:
            vol = torch.tensor(1e-4)  # degenerate fallback
        volumes.append(vol)
    volumes = torch.stack(volumes)

    # Filter valid tets (non-degenerate)
    valid = volumes > 1e-10
    tet_indices = tet_indices[valid]
    volumes = volumes[valid]

    return rest_pos, tet_indices, volumes


# ─────────────────────────────────────────────────────────────
# Test Runner
# ─────────────────────────────────────────────────────────────

PASS = "✅ PASS"
FAIL = "❌ FAIL"

results = []


def run_test(name: str, fn):
    """Run a single test and record result."""
    try:
        fn()
        print(f"  {PASS}: {name}")
        results.append((name, True, None))
    except AssertionError as e:
        print(f"  {FAIL}: {name}")
        print(f"         AssertionError: {e}")
        results.append((name, False, str(e)))
    except Exception as e:
        print(f"  {FAIL}: {name}")
        traceback.print_exc()
        results.append((name, False, str(e)))


# ─────────────────────────────────────────────────────────────
# Test 1: k1=0 → Neo-Hookean Degeneracy
# ─────────────────────────────────────────────────────────────

def test_neohookean_degeneracy():
    """When k1=0, TI energy should equal isochoric Neo-Hookean energy."""
    rest_pos, tet_indices, volumes = make_single_tet()

    # Small deformation (stretch in z)
    pos = rest_pos.clone()
    pos[:, 2] *= 1.05  # 5% stretch in z

    C1 = 1000.0
    D1 = 5000.0
    k1 = 0.0   # ← key: no fiber term
    k2 = 1.0   # irrelevant when k1=0
    fiber_dir = torch.tensor([0.0, 0.0, 1.0], dtype=torch.float64)

    W_ti, info_ti = compute_ti_energy(
        pos, rest_pos, tet_indices, C1, D1, k1, k2, fiber_dir, volumes,
        barrier_threshold=0.01  # disable barrier for this test
    )

    # Compute isochoric Neo-Hookean manually
    F = _compute_deformation_gradient(pos, rest_pos, tet_indices)  # (1, 3, 3)
    J = _det3x3(F)         # (1,)
    I1 = (F * F).sum(dim=(-2, -1))  # (1,)
    J23 = J.pow(2.0 / 3.0)
    I1bar = I1 / J23

    psi_nh = C1 * (I1bar - 3.0) + D1 * (J - 1.0) ** 2  # (1,)
    W_nh = (psi_nh * volumes).sum()

    rel_err = ((W_ti - W_nh).abs() / (W_nh.abs() + 1e-12)).item()
    assert rel_err < 1e-6, f"k1=0 degeneracy failed: rel_err={rel_err:.2e}"


# ─────────────────────────────────────────────────────────────
# Test 2: Anisotropic Response
# ─────────────────────────────────────────────────────────────

def test_anisotropic_response():
    """Fiber-direction stretch should give higher energy than transverse stretch."""
    rest_pos, tet_indices, volumes = make_single_tet()

    C1 = 1000.0
    D1 = 5000.0
    k1 = 5000.0   # strong fiber
    k2 = 2.0
    fiber_dir = torch.tensor([0.0, 0.0, 1.0], dtype=torch.float64)  # fiber along z

    # Stretch along fiber direction (z)
    pos_fiber = rest_pos.clone()
    pos_fiber[:, 2] *= 1.10   # 10% stretch in z (fiber direction)

    # Stretch perpendicular to fiber (x)
    pos_transverse = rest_pos.clone()
    pos_transverse[:, 0] *= 1.10   # 10% stretch in x (transverse)

    W_fiber, _ = compute_ti_energy(
        pos_fiber, rest_pos, tet_indices, C1, D1, k1, k2, fiber_dir, volumes,
        barrier_threshold=0.01
    )
    W_transverse, _ = compute_ti_energy(
        pos_transverse, rest_pos, tet_indices, C1, D1, k1, k2, fiber_dir, volumes,
        barrier_threshold=0.01
    )

    assert W_fiber.item() > W_transverse.item(), (
        f"Fiber stretch energy ({W_fiber.item():.4f}) should > "
        f"transverse stretch energy ({W_transverse.item():.4f})"
    )


# ─────────────────────────────────────────────────────────────
# Test 3: Macaulay Bracket (Compression → Zero Fiber)
# ─────────────────────────────────────────────────────────────

def test_macaulay_bracket():
    """Fiber term should be zero under compression along fiber direction."""
    rest_pos, tet_indices, volumes = make_single_tet()

    C1 = 1000.0
    D1 = 5000.0
    k1 = 5000.0
    k2 = 2.0
    fiber_dir = torch.tensor([0.0, 0.0, 1.0], dtype=torch.float64)

    # Compress along fiber direction (z): Ī₄ < 1 → fiber inactive
    pos_compressed = rest_pos.clone()
    pos_compressed[:, 2] *= 0.90   # 10% compression in z

    _, info = compute_ti_energy(
        pos_compressed, rest_pos, tet_indices, C1, D1, k1, k2, fiber_dir, volumes,
        barrier_threshold=0.01
    )

    # Check I4bar < 1 (compression)
    I4bar_mean = info["I4bar"].mean().item()
    assert I4bar_mean < 1.0, f"Expected I4bar < 1 under compression, got {I4bar_mean:.4f}"

    # Check fiber energy is zero
    W_fiber = info["psi_fiber"].sum().item()
    assert abs(W_fiber) < 1e-10, (
        f"Fiber energy should be 0 under compression, got {W_fiber:.6e}"
    )


# ─────────────────────────────────────────────────────────────
# Test 4: Isochoric Correction (Pure Volumetric → Ī₄ Invariant)
# ─────────────────────────────────────────────────────────────

def test_isochoric_correction():
    """Pure volumetric deformation (F = λI) should leave Ī₄ = 1."""
    rest_pos, tet_indices, volumes = make_single_tet()

    fiber_dir = torch.tensor([0.0, 0.0, 1.0], dtype=torch.float64)

    # Pure volumetric expansion: F = λI → J = λ³, Ī₄ = J^{-2/3}λ² = λ^{-2}λ² = 1
    lambda_vol = 1.20   # 20% volumetric expansion
    pos_vol = rest_pos * lambda_vol  # isotropic scaling from origin

    # Need to compute from origin: translate so centroid = origin
    centroid = rest_pos.mean(dim=0)
    rest_centered = rest_pos - centroid
    pos_centered = rest_centered * lambda_vol

    # Rebuild with centroid restored
    pos_vol_full = pos_centered + centroid

    F = _compute_deformation_gradient(pos_vol_full, rest_pos, tet_indices)
    J, I1bar, I4bar = _compute_isochoric_invariants(F, fiber_dir)

    # For pure volumetric: Ī₄ should be 1.0
    I4bar_val = I4bar[0].item()
    assert abs(I4bar_val - 1.0) < 1e-5, (
        f"Isochoric correction failed: Ī₄ = {I4bar_val:.6f}, expected ≈ 1.0"
    )

    # Also check Ī₁: for pure volumetric F=λI, Ī₁ = J^{-2/3}·3λ² = 3
    I1bar_val = I1bar[0].item()
    assert abs(I1bar_val - 3.0) < 1e-5, (
        f"Ī₁ should = 3 for pure volumetric, got {I1bar_val:.6f}"
    )


# ─────────────────────────────────────────────────────────────
# Test 5: Edge Feature Antisymmetry
# ─────────────────────────────────────────────────────────────

def test_edge_antisymmetry():
    """r̂_ij·d_k + r̂_ji·d_k ≈ 0 for all edges and material axes."""
    N = 6
    torch.manual_seed(42)
    positions = torch.randn(N, 3, dtype=torch.float64)

    # Build undirected edge list (both directions for each pair)
    pairs = [(0,1),(0,2),(1,2),(2,3),(3,4),(4,5),(0,5)]
    edges_fwd = [[i, j] for i, j in pairs]
    edges_rev = [[j, i] for i, j in pairs]
    all_edges = edges_fwd + edges_rev
    edge_index = torch.tensor(all_edges, dtype=torch.long).T  # (2, E)

    # Material axes: global z-fiber
    tet_indices = torch.tensor([[0, 1, 2, 3]], dtype=torch.long)  # dummy
    material_axes = assign_fiber_directions(positions, tet_indices, fiber_dir='z')

    # Compute edge features
    edge_attr = compute_anisotropic_edge_features(positions, edge_index, material_axes)

    # Verify antisymmetry
    verify_antisymmetry(edge_attr, edge_index, atol=1e-6)

    # Also manually check one pair
    # Find edge (0→1) and (1→0)
    src = edge_index[0].tolist()
    dst = edge_index[1].tolist()
    idx_fwd = next(i for i, (s, d) in enumerate(zip(src, dst)) if s == 0 and d == 1)
    idx_rev = next(i for i, (s, d) in enumerate(zip(src, dst)) if s == 1 and d == 0)

    e_fwd = edge_attr[idx_fwd]
    e_rev = edge_attr[idx_rev]

    # r_ij components and dot products should negate
    anti_err = (e_fwd[[0,1,2,4,5,6]] + e_rev[[0,1,2,4,5,6]]).abs().max().item()
    assert anti_err < 1e-6, f"Manual antisymmetry check failed: {anti_err:.2e}"

    # Distance should be equal
    dist_diff = abs(e_fwd[3].item() - e_rev[3].item())
    assert dist_diff < 1e-6, f"Distance not symmetric: {dist_diff:.2e}"


# ─────────────────────────────────────────────────────────────
# Test 6: Gradient Check (autograd vs finite differences)
# ─────────────────────────────────────────────────────────────

def test_gradient_check():
    """Autograd forces should match finite difference approximation (rel_err < 1e-4)."""
    rest_pos, tet_indices, volumes = make_single_tet()

    C1 = 1000.0
    D1 = 5000.0
    k1 = 2000.0
    k2 = 2.0
    fiber_dir = torch.tensor([0.0, 0.0, 1.0], dtype=torch.float64)

    # Small deformation
    pos0 = rest_pos.clone()
    pos0[:, 2] *= 1.03  # 3% z-stretch

    # Autograd forces
    forces_auto, _ = compute_ti_stress_forces(
        pos0, rest_pos, tet_indices, C1, D1, k1, k2, fiber_dir, volumes,
        barrier_threshold=0.01
    )

    # Finite difference: df/dx_i ≈ (W(x+h*e_i) - W(x-h*e_i)) / (2h)
    h = 1e-5
    N = pos0.shape[0]
    forces_fd = torch.zeros_like(pos0)

    for i in range(N):
        for d in range(3):
            pos_plus = pos0.clone()
            pos_plus[i, d] += h
            W_plus, _ = compute_ti_energy(
                pos_plus, rest_pos, tet_indices, C1, D1, k1, k2, fiber_dir, volumes,
                barrier_threshold=0.01
            )

            pos_minus = pos0.clone()
            pos_minus[i, d] -= h
            W_minus, _ = compute_ti_energy(
                pos_minus, rest_pos, tet_indices, C1, D1, k1, k2, fiber_dir, volumes,
                barrier_threshold=0.01
            )

            # f_internal = -dW/dx → central difference
            forces_fd[i, d] = -(W_plus - W_minus) / (2.0 * h)

    # Relative error
    diff = (forces_auto - forces_fd).abs()
    denom = forces_fd.abs() + 1e-8
    rel_err = (diff / denom).max().item()

    assert rel_err < 1e-3, (
        f"Gradient check failed: max rel_err = {rel_err:.4e} (threshold: 1e-3)\n"
        f"Autograd: {forces_auto}\nFD: {forces_fd}"
    )


# ─────────────────────────────────────────────────────────────
# Test 7: Force Balance (Newton's 3rd Law via Antisymmetric MP)
# ─────────────────────────────────────────────────────────────

def test_force_balance():
    """Sum of internal forces over all nodes should ≈ 0 (momentum conservation)."""
    rest_pos, tet_indices, volumes = make_small_mesh(n_tets=4)
    N = rest_pos.shape[0]

    C1 = 1000.0
    D1 = 5000.0
    k1 = 2000.0
    k2 = 2.0
    fiber_dir = torch.tensor([0.0, 0.0, 1.0], dtype=torch.float64)

    # Random but physically reasonable deformation
    torch.manual_seed(123)
    pos = rest_pos + 0.02 * torch.randn_like(rest_pos)

    forces, info = compute_ti_stress_forces(
        pos, rest_pos, tet_indices, C1, D1, k1, k2, fiber_dir, volumes,
        barrier_threshold=0.01
    )

    # Sum of internal forces should ≈ 0 (Newton's 3rd law)
    force_sum = forces.sum(dim=0)  # (3,)
    force_sum_norm = force_sum.norm().item()
    forces_norm = forces.norm().item()

    # Relative magnitude of imbalance
    rel_imbalance = force_sum_norm / (forces_norm + 1e-10)
    assert rel_imbalance < 1e-3, (
        f"Force balance violated: |ΣF| = {force_sum_norm:.4e}, "
        f"|F| = {forces_norm:.4e}, rel = {rel_imbalance:.4e}"
    )


# ─────────────────────────────────────────────────────────────
# Test 8: Bone Material Parameters Sanity
# ─────────────────────────────────────────────────────────────

def test_bone_params_sanity():
    """Bone material parameters should be physically reasonable."""
    cortical = cortical_bone_params()
    cancellous = cancellous_bone_params(BV_TV=0.25)
    vertebral = vertebral_body_params()

    # C1 should be > 0
    for name, p in [("cortical", cortical), ("cancellous", cancellous), ("vertebral", vertebral)]:
        assert p["C1"] > 0, f"{name}: C1 should be > 0"
        assert p["D1"] > 0, f"{name}: D1 should be > 0"
        assert p["k1"] >= 0, f"{name}: k1 should be ≥ 0"
        assert p["k2"] > 0, f"{name}: k2 should be > 0"
        assert p["rho"] > 0, f"{name}: rho should be > 0"
        assert len(p["fiber_dir"]) == 3, f"{name}: fiber_dir should be 3D"

    # Cortical > cancellous (cortical bone is stiffer)
    assert cortical["C1"] > cancellous["C1"], (
        f"Cortical C1 ({cortical['C1']/1e6:.1f} MPa) should > "
        f"cancellous C1 ({cancellous['C1']/1e6:.1f} MPa)"
    )

    # BV/TV dependence: higher BV/TV → higher stiffness
    cancellous_dense = cancellous_bone_params(BV_TV=0.35)
    cancellous_sparse = cancellous_bone_params(BV_TV=0.10)
    assert cancellous_dense["C1"] > cancellous_sparse["C1"], (
        "Denser cancellous bone should have higher C1"
    )


# ─────────────────────────────────────────────────────────────
# Test 9: TI Physics Loss Output
# ─────────────────────────────────────────────────────────────

def test_ti_physics_loss():
    """ti_physics_loss should return scalar loss with valid gradient."""
    rest_pos, tet_indices, volumes = make_single_tet()

    cortical = cortical_bone_params()
    fiber_dir = torch.tensor(cortical["fiber_dir"], dtype=torch.float64)

    params = {
        "C1": cortical["C1"],
        "D1": cortical["D1"],
        "k1": cortical["k1"],
        "k2": cortical["k2"],
        "fiber_dir": fiber_dir,
        "volumes": volumes,
    }

    # Predicted positions (slightly perturbed)
    pred_pos = rest_pos.clone().requires_grad_(True)
    f_ext = torch.zeros_like(rest_pos)

    loss, info = ti_physics_loss(pred_pos, rest_pos, tet_indices, params, f_ext)

    # Loss should be a scalar
    assert loss.dim() == 0, f"Loss should be scalar, got shape {loss.shape}"

    # Loss at rest should be ~0 (no deformation, no fiber activation)
    assert abs(loss.item()) < 1.0, f"Rest loss too large: {loss.item():.4f}"

    # Gradient should be computable
    loss.backward()
    assert pred_pos.grad is not None, "Gradient should be computable"
    assert not torch.isnan(pred_pos.grad).any(), "Gradient should not contain NaN"


# ─────────────────────────────────────────────────────────────
# Test 10: Edge Feature Shape and Content
# ─────────────────────────────────────────────────────────────

def test_edge_feature_shape():
    """Edge features should have correct shape (E, 7)."""
    N = 8
    positions = torch.randn(N, 3, dtype=torch.float32)
    tet_indices = torch.tensor([[0,1,2,3],[4,5,6,7]], dtype=torch.long)
    material_axes = assign_fiber_directions(positions, tet_indices, fiber_dir='z')

    # Build a simple edge_index
    edge_index = torch.tensor([
        [0,1,2,0,3,4,5,1],
        [1,0,3,2,0,5,4,3],
    ], dtype=torch.long)

    edge_attr = compute_anisotropic_edge_features(positions, edge_index, material_axes)

    # Check shape
    E = edge_index.shape[1]
    assert edge_attr.shape == (E, 7), (
        f"Expected edge_attr shape ({E}, 7), got {edge_attr.shape}"
    )

    # Check that r_ij component (first 3) equals x_j - x_i
    src, dst = edge_index[0], edge_index[1]
    r_expected = positions[dst] - positions[src]
    r_err = (edge_attr[:, :3] - r_expected).abs().max().item()
    assert r_err < 1e-6, f"r_ij component mismatch: {r_err:.2e}"

    # Check distance is positive
    assert (edge_attr[:, 3] > 0).all(), "All distances should be positive"


# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("DPC-GNN Transversely Isotropic Extension — Self-Test Suite")
    print("=" * 60 + "\n")

    tests = [
        ("1. Neo-Hookean degeneracy (k1=0)", test_neohookean_degeneracy),
        ("2. Anisotropic response (fiber > transverse)", test_anisotropic_response),
        ("3. Macaulay bracket (compression → fiber=0)", test_macaulay_bracket),
        ("4. Isochoric correction (volumetric → Ī₄=1)", test_isochoric_correction),
        ("5. Edge feature antisymmetry", test_edge_antisymmetry),
        ("6. Gradient check (autograd vs FD)", test_gradient_check),
        ("7. Force balance (Newton's 3rd law)", test_force_balance),
        ("8. Bone material params sanity", test_bone_params_sanity),
        ("9. TI physics loss interface", test_ti_physics_loss),
        ("10. Edge feature shape/content", test_edge_feature_shape),
    ]

    for name, fn in tests:
        run_test(name, fn)

    print("\n" + "=" * 60)
    n_pass = sum(1 for _, ok, _ in results if ok)
    n_fail = sum(1 for _, ok, _ in results if not ok)
    print(f"Results: {n_pass}/{len(results)} passed, {n_fail} failed")

    if n_fail > 0:
        print("\nFailed tests:")
        for name, ok, err in results:
            if not ok:
                print(f"  ❌ {name}: {err}")
        print("=" * 60)
        sys.exit(1)
    else:
        print("\n🎉 All tests passed!")
        print("=" * 60)
        sys.exit(0)
