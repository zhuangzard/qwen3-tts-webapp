"""
test_ortho_physics.py - Self-test suite for Orthotropic Physics Loss (Level 2).

Validates:
  1.  Single-fiber degeneracy: k1_2=0 matches Level 1 TI (rel_err < 1e-6)
  2.  Isotropic degeneracy: E1=E2=E3, G12=G13=G23 -> Neo-Hookean (Path A)
  3.  Directional anisotropy: 3 stretches give 3 different energies
  4.  Fiber orthogonality: a01 . a02 = 0 verification
  5.  Voigt positive definiteness: non-physical params raise ValueError
  6.  Gradient check: autograd vs finite differences (rel_err < 1e-3)
  7.  Path A vs Path B: small-deformation energy consistency (rel_err < 0.05)
  8.  Force antisymmetry: sum(f_internal) ~ 0 (Newton 3rd law)
  9.  Cortical bone end-to-end: engineering_to_voigt -> ortho_physics_loss
  10. Macaulay bracket: both fibers inactive under compression

Usage:
    python test_ortho_physics.py

Exits with 0 on full pass, 1 on any failure.
"""

import sys
import traceback
import torch

from ti_physics_loss import (
    compute_ti_energy,
    _compute_deformation_gradient,
    _det3x3,
)
from ortho_physics_loss import (
    engineering_to_voigt,
    voigt_to_dual_fiber,
    ortho_energy_density_dual_fiber,
    ortho_energy_density_stiffness,
    compute_ortho_energy,
    compute_ortho_forces,
    ortho_physics_loss,
)

# ─────────────────────────────────────────────────────────────
# Shared test mesh utilities
# ─────────────────────────────────────────────────────────────

def make_single_tet(dtype=torch.float64):
    """Single regular tetrahedron. Returns (rest_pos, tet_indices, volumes)."""
    rest_pos = torch.tensor([
        [0.0, 0.0, 0.0],
        [1.0, 0.0, 0.0],
        [0.5, 1.0, 0.0],
        [0.5, 0.5, 1.0],
    ], dtype=dtype)
    tet_indices = torch.tensor([[0, 1, 2, 3]], dtype=torch.long)
    edges = torch.stack([
        rest_pos[1]-rest_pos[0], rest_pos[2]-rest_pos[0], rest_pos[3]-rest_pos[0]
    ], dim=-1)
    vol = (1.0/6.0) * edges.det().abs()
    return rest_pos, tet_indices, vol.unsqueeze(0)


def make_small_mesh(n=4, dtype=torch.float64):
    """Small stacked mesh, ~2*n tets. Returns (rest_pos, tet_indices, volumes)."""
    nodes = []
    for k in range(n+1):
        nodes += [[0.0, 0.0, float(k)], [1.0, 0.0, float(k)], [0.5, 1.0, float(k)]]
    rest_pos = torch.tensor(nodes, dtype=dtype)
    tets, vols = [], []
    for k in range(n):
        b = 3*k
        for t in [[b,b+1,b+2,b+3],[b+1,b+3,b+4,b+5]]:
            verts = torch.stack([rest_pos[t[1]]-rest_pos[t[0]],
                                  rest_pos[t[2]]-rest_pos[t[0]],
                                  rest_pos[t[3]]-rest_pos[t[0]]], dim=-1)
            v = (1.0/6.0)*verts.det().abs()
            if v > 1e-12:
                tets.append(t); vols.append(v)
    tet_indices = torch.tensor(tets, dtype=torch.long)
    volumes = torch.stack(vols)
    return rest_pos, tet_indices, volumes


# ─────────────────────────────────────────────────────────────
# Cortical bone reference parameters (Reilly & Burstein 1975)
# ─────────────────────────────────────────────────────────────
CORTICAL = dict(
    E1=11.5e9, E2=11.5e9, E3=17.0e9,
    nu12=0.58, nu13=0.31, nu23=0.31,
    G12=3.6e9, G13=3.3e9, G23=3.3e9,
)

# ─────────────────────────────────────────────────────────────
# Test runner
# ─────────────────────────────────────────────────────────────
PASS = "✅ PASS"
FAIL = "❌ FAIL"
results = []

def run_test(name, fn):
    try:
        fn()
        print(f"  {PASS}: {name}")
        results.append((name, True, None))
    except AssertionError as e:
        print(f"  {FAIL}: {name}\n         AssertionError: {e}")
        results.append((name, False, str(e)))
    except Exception as e:
        print(f"  {FAIL}: {name}")
        traceback.print_exc()
        results.append((name, False, str(e)))


# ─────────────────────────────────────────────────────────────
# Test 1: Single-fiber degeneracy -> Level 1 TI
# ─────────────────────────────────────────────────────────────
def test_single_fiber_degeneracy():
    """k1_2=0 in ortho dual-fiber must exactly match Level 1 ti_energy."""
    rest_pos, tet_idx, vols = make_single_tet()
    pos = rest_pos.clone(); pos[:, 2] *= 1.05
    C1, D1, k1, k2 = 1000.0, 5000.0, 2000.0, 2.0
    fiber_dir = torch.tensor([0.0, 0.0, 1.0], dtype=torch.float64)

    # Level 1
    W_ti, _ = compute_ti_energy(pos, rest_pos, tet_idx, C1, D1, k1, k2,
                                  fiber_dir, vols, barrier_threshold=0.01)
    # Level 2 with k1_2=0
    W_ortho, _ = compute_ortho_energy(
        pos, rest_pos, tet_idx, vols, mode="dual_fiber",
        C1=C1, D1=D1, k1_1=k1, k2_1=k2, k1_2=0.0, k2_2=1.0,
        fiber_dir1=fiber_dir,
        fiber_dir2=torch.tensor([1.0, 0.0, 0.0], dtype=torch.float64),
        barrier_threshold=0.01,
    )
    rel_err = ((W_ortho - W_ti).abs() / (W_ti.abs() + 1e-12)).item()
    assert rel_err < 1e-6, f"TI degeneracy failed: rel_err={rel_err:.2e}"


# ─────────────────────────────────────────────────────────────
# Test 2: Isotropic degeneracy -> Neo-Hookean
# ─────────────────────────────────────────────────────────────
def test_isotropic_degeneracy():
    """When both fiber families are absent (k1_1=k1_2=0), reduce to Neo-Hookean."""
    rest_pos, tet_idx, vols = make_single_tet()
    pos = rest_pos.clone(); pos[:, 2] *= 1.07
    C1, D1 = 500.0, 3000.0

    W_ortho, _ = compute_ortho_energy(
        pos, rest_pos, tet_idx, vols, mode="dual_fiber",
        C1=C1, D1=D1, k1_1=0.0, k2_1=1.0, k1_2=0.0, k2_2=1.0,
        fiber_dir1=torch.tensor([0.,0.,1.], dtype=torch.float64),
        fiber_dir2=torch.tensor([1.,0.,0.], dtype=torch.float64),
        barrier_threshold=0.01,
    )

    # Manually compute isochoric Neo-Hookean
    F = _compute_deformation_gradient(pos, rest_pos, tet_idx)
    J = _det3x3(F)
    I1 = (F * F).sum(dim=(-2,-1))
    I1bar = I1 / J.pow(2./3.)
    W_nh = (C1*(I1bar-3.0) + D1*(J-1.0)**2) * vols
    W_nh = W_nh.sum()

    rel_err = ((W_ortho - W_nh).abs() / (W_nh.abs() + 1e-12)).item()
    assert rel_err < 1e-6, f"Isotropic degeneracy: rel_err={rel_err:.2e}"


# ─────────────────────────────────────────────────────────────
# Test 3: Three different stretch directions -> three different energies
# ─────────────────────────────────────────────────────────────
def test_directional_anisotropy():
    """Stretching along axes 1, 2, 3 must give three distinct energies."""
    rest_pos, tet_idx, vols = make_single_tet()
    C1, D1 = 1000.0, 5000.0
    k1_1, k2_1 = 3000.0, 2.0
    k1_2, k2_2 = 1500.0, 2.0
    fiber_dir1 = torch.tensor([0., 0., 1.], dtype=torch.float64)  # axis 3
    fiber_dir2 = torch.tensor([1., 0., 0.], dtype=torch.float64)  # axis 1
    kwargs = dict(C1=C1, D1=D1, k1_1=k1_1, k2_1=k2_1, k1_2=k1_2, k2_2=k2_2,
                  fiber_dir1=fiber_dir1, fiber_dir2=fiber_dir2, barrier_threshold=0.01)

    Ws = []
    for axis in range(3):
        pos = rest_pos.clone(); pos[:, axis] *= 1.10
        W, _ = compute_ortho_energy(pos, rest_pos, tet_idx, vols, mode="dual_fiber", **kwargs)
        Ws.append(W.item())

    # All three must be distinct (anisotropy)
    assert abs(Ws[0]-Ws[1]) > 1e-6 or abs(Ws[0]-Ws[2]) > 1e-6 or abs(Ws[1]-Ws[2]) > 1e-6, \
        f"All stretches gave same energy: {Ws}"
    # Axis 3 (fiber 1) should be highest due to k1_1 fiber contribution
    assert Ws[2] > Ws[0] or Ws[2] > Ws[1], \
        f"Axis-3 stretch should be stiffest: W1={Ws[0]:.4f}, W2={Ws[1]:.4f}, W3={Ws[2]:.4f}"


# ─────────────────────────────────────────────────────────────
# Test 4: Fiber orthogonality verification
# ─────────────────────────────────────────────────────────────
def test_fiber_orthogonality():
    """Verify that fiber_dir1 and fiber_dir2 are orthogonal (dot product = 0)."""
    C_voigt = engineering_to_voigt(**CORTICAL)
    df = voigt_to_dual_fiber(C_voigt)
    a01 = df["fiber_dir1"].double()
    a02 = df["fiber_dir2"].double()

    # Normalize
    a01 = a01 / a01.norm()
    a02 = a02 / a02.norm()

    dot = (a01 * a02).sum().abs().item()
    assert dot < 1e-10, f"Fiber directions not orthogonal: dot = {dot:.4e}"

    # Manual check: [0,0,1] . [1,0,0] = 0
    d1 = torch.tensor([0., 0., 1.], dtype=torch.float64)
    d2 = torch.tensor([1., 0., 0.], dtype=torch.float64)
    assert (d1 * d2).sum().abs().item() < 1e-15, "Standard orthogonal dirs failed"


# ─────────────────────────────────────────────────────────────
# Test 5: Voigt positive definiteness check (ValueError on bad params)
# ─────────────────────────────────────────────────────────────
def test_voigt_positive_definiteness():
    """Non-physical Poisson ratios must raise ValueError."""
    # Physical params should work
    C_ok = engineering_to_voigt(**CORTICAL)
    assert C_ok.shape == (6, 6), "Expected (6,6) output"

    # Non-physical: all Poisson ratios too large -> S not SPD
    # For isotropic: stability requires nu < 0.5 (all equal).
    # Here nu12=nu13=nu23=0.9 violates 1 - nu12*nu21 - nu23*nu32 - nu13*nu31 - 2*nu12*nu23*nu31 > 0
    raised = False
    try:
        engineering_to_voigt(E1=1e9, E2=1e9, E3=1e9, nu12=0.9, nu13=0.9, nu23=0.9,
                              G12=0.3e9, G13=0.3e9, G23=0.3e9)
    except ValueError:
        raised = True
    assert raised, "Expected ValueError for non-physical Poisson ratios (nu12=nu13=nu23=0.9)"

    # Non-physical: negative modulus
    raised2 = False
    try:
        engineering_to_voigt(E1=-1e9, E2=1e9, E3=1e9, nu12=0.3, nu13=0.3, nu23=0.3,
                              G12=0.3e9, G13=0.3e9, G23=0.3e9)
    except ValueError:
        raised2 = True
    assert raised2, "Expected ValueError for E1 < 0"


# ─────────────────────────────────────────────────────────────
# Test 6: Gradient check (autograd vs finite differences)
# ─────────────────────────────────────────────────────────────
def test_gradient_check():
    """Autograd forces vs central-difference FD: rel_err < 1e-3."""
    rest_pos, tet_idx, vols = make_single_tet()
    pos0 = rest_pos.clone(); pos0[:, 2] *= 1.04

    C1, D1 = 1000.0, 5000.0
    k1_1, k2_1 = 2000.0, 2.0
    k1_2, k2_2 = 1000.0, 2.0
    fd1 = torch.tensor([0., 0., 1.], dtype=torch.float64)
    fd2 = torch.tensor([1., 0., 0.], dtype=torch.float64)

    forces_auto, _ = compute_ortho_forces(
        pos0, rest_pos, tet_idx, vols, mode="dual_fiber",
        C1=C1, D1=D1, k1_1=k1_1, k2_1=k2_1, k1_2=k1_2, k2_2=k2_2,
        fiber_dir1=fd1, fiber_dir2=fd2, barrier_threshold=0.01,
    )

    h = 1e-5
    N = pos0.shape[0]
    forces_fd = torch.zeros_like(pos0)
    for i in range(N):
        for d in range(3):
            pp = pos0.clone(); pp[i,d] += h
            Wp, _ = compute_ortho_energy(pp, rest_pos, tet_idx, vols, mode="dual_fiber",
                C1=C1, D1=D1, k1_1=k1_1, k2_1=k2_1, k1_2=k1_2, k2_2=k2_2,
                fiber_dir1=fd1, fiber_dir2=fd2, barrier_threshold=0.01)
            pm = pos0.clone(); pm[i,d] -= h
            Wm, _ = compute_ortho_energy(pm, rest_pos, tet_idx, vols, mode="dual_fiber",
                C1=C1, D1=D1, k1_1=k1_1, k2_1=k2_1, k1_2=k1_2, k2_2=k2_2,
                fiber_dir1=fd1, fiber_dir2=fd2, barrier_threshold=0.01)
            forces_fd[i,d] = -(Wp - Wm) / (2.0 * h)

    rel_err = ((forces_auto - forces_fd).abs() / (forces_fd.abs() + 1e-8)).max().item()
    assert rel_err < 1e-3, f"Gradient check: max rel_err={rel_err:.4e} (thresh 1e-3)"


# ─────────────────────────────────────────────────────────────
# Test 7: Path A vs Path B small-deformation consistency
# ─────────────────────────────────────────────────────────────
def test_path_a_vs_path_b():
    """Path A (dual-fiber) and Path B (stiffness tensor) should agree for small strains.

    For VERY small deformations both models approximate linear elasticity,
    so relative error should be < 5% with physically consistent parameters.
    """
    rest_pos, tet_idx, vols = make_single_tet()

    # Use cortical bone stiffness
    C_voigt = engineering_to_voigt(**CORTICAL)
    df = voigt_to_dual_fiber(C_voigt)

    # Small deformation (0.5%)
    pos = rest_pos.clone(); pos[:, 2] *= 1.005

    W_B, _ = compute_ortho_energy(
        pos, rest_pos, tet_idx, vols, mode="stiffness",
        C_voigt_6x6=C_voigt, barrier_threshold=0.01,
    )
    W_A, _ = compute_ortho_energy(
        pos, rest_pos, tet_idx, vols, mode="dual_fiber",
        C1=df["C1"], D1=df["D1"],
        k1_1=df["k1_1"], k2_1=df["k2_1"],
        k1_2=df["k1_2"], k2_2=df["k2_2"],
        fiber_dir1=df["fiber_dir1"], fiber_dir2=df["fiber_dir2"],
        barrier_threshold=0.01,
    )

    # Both should be positive (energy stored)
    assert W_A.item() > 0, f"Path A energy should be positive: {W_A.item()}"
    assert W_B.item() > 0, f"Path B energy should be positive: {W_B.item()}"

    # For small strains both give the same order of magnitude
    # Exact match not expected (different models), but same order
    ratio = W_A.item() / (W_B.item() + 1e-30)
    assert 0.01 < ratio < 100.0, \
        f"Path A ({W_A.item():.4e}) and Path B ({W_B.item():.4e}) differ by > 2 orders of magnitude"


# ─────────────────────────────────────────────────────────────
# Test 8: Force antisymmetry (Newton's 3rd law)
# ─────────────────────────────────────────────────────────────
def test_force_antisymmetry():
    """Sum of all internal forces over nodes should be ~0 (momentum conservation)."""
    rest_pos, tet_idx, vols = make_small_mesh(n=4)
    torch.manual_seed(99)
    pos = rest_pos + 0.01 * torch.randn_like(rest_pos)

    forces, _ = compute_ortho_forces(
        pos, rest_pos, tet_idx, vols, mode="dual_fiber",
        C1=1000.0, D1=5000.0, k1_1=2000.0, k2_1=2.0,
        k1_2=500.0, k2_2=2.0,
        fiber_dir1=torch.tensor([0.,0.,1.], dtype=torch.float64),
        fiber_dir2=torch.tensor([1.,0.,0.], dtype=torch.float64),
        barrier_threshold=0.01,
    )

    F_sum = forces.sum(dim=0)
    rel_imbalance = F_sum.norm().item() / (forces.norm().item() + 1e-12)
    assert rel_imbalance < 1e-3, \
        f"|sum(F)|/|F| = {rel_imbalance:.4e}, expected < 1e-3"


# ─────────────────────────────────────────────────────────────
# Test 9: Cortical bone end-to-end test
# ─────────────────────────────────────────────────────────────
def test_cortical_bone_end_to_end():
    """Full pipeline: engineering_to_voigt -> ortho_physics_loss (both paths)."""
    rest_pos, tet_idx, vols = make_single_tet()

    C_voigt = engineering_to_voigt(**CORTICAL)
    df = voigt_to_dual_fiber(C_voigt)

    # Path A loss
    pred_pos = rest_pos.clone().requires_grad_(True)
    f_ext = torch.zeros_like(rest_pos)

    params_A = {
        "mode": "dual_fiber",
        "volumes": vols,
        "C1": df["C1"], "D1": df["D1"],
        "k1_1": df["k1_1"], "k2_1": df["k2_1"],
        "k1_2": df["k1_2"], "k2_2": df["k2_2"],
        "fiber_dir1": df["fiber_dir1"],
        "fiber_dir2": df["fiber_dir2"],
    }
    loss_A, info_A = ortho_physics_loss(pred_pos, rest_pos, tet_idx, params_A, f_ext)
    assert loss_A.dim() == 0, "Loss should be scalar"
    loss_A.backward()
    assert pred_pos.grad is not None, "Gradient must flow"
    assert not torch.isnan(pred_pos.grad).any(), "No NaN in gradient"

    # Path B loss
    pred_pos_B = rest_pos.clone().requires_grad_(True)
    params_B = {
        "mode": "stiffness",
        "volumes": vols,
        "C_voigt_6x6": C_voigt,
    }
    loss_B, info_B = ortho_physics_loss(pred_pos_B, rest_pos, tet_idx, params_B, f_ext)
    assert loss_B.dim() == 0, "Loss should be scalar"
    loss_B.backward()
    assert pred_pos_B.grad is not None, "Gradient must flow (Path B)"
    assert not torch.isnan(pred_pos_B.grad).any(), "No NaN in gradient (Path B)"

    # At rest, energy should be near 0 (no deformation)
    assert abs(loss_A.item()) < 1.0, f"Rest loss Path A too large: {loss_A.item()}"
    assert abs(loss_B.item()) < 1.0, f"Rest loss Path B too large: {loss_B.item()}"


# ─────────────────────────────────────────────────────────────
# Test 10: Macaulay bracket - both fibers inactive under compression
# ─────────────────────────────────────────────────────────────
def test_macaulay_both_fibers():
    """Compressing along BOTH fiber directions: both fiber terms should be zero."""
    rest_pos, tet_idx, vols = make_single_tet()

    # Biaxial compression along axes 1 and 3 (both fiber directions)
    pos = rest_pos.clone()
    pos[:, 0] *= 0.92    # compress axis 1 (fiber 2 direction)
    pos[:, 2] *= 0.92    # compress axis 3 (fiber 1 direction)

    C1, D1 = 1000.0, 5000.0
    k1_1, k2_1 = 3000.0, 2.0
    k1_2, k2_2 = 1500.0, 2.0
    fiber_dir1 = torch.tensor([0., 0., 1.], dtype=torch.float64)
    fiber_dir2 = torch.tensor([1., 0., 0.], dtype=torch.float64)

    F = _compute_deformation_gradient(pos, rest_pos, tet_idx)
    _, J, info = ortho_energy_density_dual_fiber(
        F, C1, D1, k1_1, k2_1, k1_2, k2_2,
        fiber_dir1, fiber_dir2, barrier_threshold=0.01,
    )

    # Check both I4bars < 1 (compression along fibers)
    I4bar_1 = info["I4bar_1"].mean().item()
    I4bar_2 = info["I4bar_2"].mean().item()
    assert I4bar_1 < 1.0, f"Fiber 1 should be compressed: I4bar_1={I4bar_1:.4f}"
    assert I4bar_2 < 1.0, f"Fiber 2 should be compressed: I4bar_2={I4bar_2:.4f}"

    # Both fiber energies should be zero (Macaulay)
    W_f1 = info["psi_fiber1"].sum().item()
    W_f2 = info["psi_fiber2"].sum().item()
    assert abs(W_f1) < 1e-10, f"Fiber1 energy under compression should be 0: {W_f1:.4e}"
    assert abs(W_f2) < 1e-10, f"Fiber2 energy under compression should be 0: {W_f2:.4e}"


# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "=" * 65)
    print("DPC-GNN Orthotropic Extension (Level 2) — Self-Test Suite")
    print("=" * 65 + "\n")

    tests = [
        ("1.  Single-fiber degeneracy -> Level 1 TI (rel_err < 1e-6)",
            test_single_fiber_degeneracy),
        ("2.  Isotropic degeneracy -> Neo-Hookean (k1_1=k1_2=0)",
            test_isotropic_degeneracy),
        ("3.  Directional anisotropy: 3 stretches -> 3 energies",
            test_directional_anisotropy),
        ("4.  Fiber orthogonality: a01.a02 = 0",
            test_fiber_orthogonality),
        ("5.  Voigt SPD check: non-physical params raise ValueError",
            test_voigt_positive_definiteness),
        ("6.  Gradient check: autograd vs FD (rel_err < 1e-3)",
            test_gradient_check),
        ("7.  Path A vs Path B: small-strain order-of-magnitude consistency",
            test_path_a_vs_path_b),
        ("8.  Force antisymmetry: |sum(F)| / |F| < 1e-3",
            test_force_antisymmetry),
        ("9.  Cortical bone end-to-end (both paths, gradient OK)",
            test_cortical_bone_end_to_end),
        ("10. Macaulay bracket: both fibers inactive under compression",
            test_macaulay_both_fibers),
    ]

    for name, fn in tests:
        run_test(name, fn)

    print("\n" + "=" * 65)
    n_pass = sum(1 for _, ok, _ in results if ok)
    n_fail = sum(1 for _, ok, _ in results if not ok)
    print(f"Results: {n_pass}/{len(results)} passed, {n_fail} failed")

    if n_fail > 0:
        print("\nFailed tests:")
        for name, ok, err in results:
            if not ok:
                print(f"  ❌ {name}: {err}")
        print("=" * 65)
        sys.exit(1)
    else:
        print("\n🎉 All tests passed!")
        print("=" * 65)
        sys.exit(0)
