"""
ti_physics_loss.py — Transversely Isotropic Physics Loss for DPC-GNN.

Extends Neo-Hookean with fiber-reinforced anisotropic term (Holzapfel-Ogden style):

    Ψ_TI = C₁(Ī₁ - 3) + D₁(J - 1)² + (k₁/2k₂)[exp(k₂⟨Ī₄-1⟩²) - 1] + Ψ_barrier(J)

where:
    Ī₁ = J^{-2/3} I₁               : isochoric first invariant
    Ī₄ = J^{-2/3} (a₀ · C · a₀)   : isochoric fiber stretch invariant
    J   = det(F)                    : volume ratio
    ⟨x⟩ = max(x, 0)                : Macaulay bracket (tension-only fiber activation)
    C   = F^T F                     : right Cauchy-Green deformation tensor

Backward compatibility: when k1=0, reduces exactly to the standard Neo-Hookean
formulation in physics_loss.py (with isochoric I₁ instead of standard I₁).

Material parameters:
    C₁  : matrix shear stiffness (Pa) — Neo-Hookean base
    D₁  : volumetric bulk stiffness (Pa) — compressibility
    k₁  : fiber stiffness (Pa) — linear fiber response
    k₂  : fiber nonlinearity (dimensionless) — exponential stiffening
    a₀  : fiber direction unit vector in reference config (3,)

References:
    Holzapfel GA, Ogden RW (2010) Constitutive modelling of arteries.
        Proc R Soc A 466:1551–1597.
    Weiss JA et al. (1996) Finite element implementation of incompressible,
        transversely isotropic hyperelasticity. CMAME 135:107–128.
    Reilly DT, Burstein AH (1975) The elastic and ultimate properties of
        compact bone tissue. J Biomech 8:393–405.

Expert Review:
    - 计算力学专家: TI formulation, isochoric corrections, Macaulay bracket
    - PIGNN专家: energy-based loss, autograd compatibility
    - 数值方法专家: barrier function, numerical stability
    - GNN架构专家: gradient flow, per-element vs global fiber direction
"""

import torch
import torch.nn.functional as F_nn
from typing import Tuple, Dict, Optional, Union


# ─────────────────────────────────────────────────────────────
# Low-level tensor utilities (self-contained, no mesh_utils dep)
# ─────────────────────────────────────────────────────────────

def _det3x3(F: torch.Tensor) -> torch.Tensor:
    """Compute determinant of 3×3 matrices without torch.det (autograd-safe).

    Args:
        F: (T, 3, 3) batch of 3×3 matrices

    Returns:
        det: (T,) determinants
    """
    a = F[..., 0, 0]; b = F[..., 0, 1]; c = F[..., 0, 2]
    d = F[..., 1, 0]; e = F[..., 1, 1]; f = F[..., 1, 2]
    g = F[..., 2, 0]; h = F[..., 2, 1]; k = F[..., 2, 2]
    return a * (e * k - f * h) - b * (d * k - f * g) + c * (d * h - e * g)


def _compute_deformation_gradient(
    positions: torch.Tensor,
    rest_positions: torch.Tensor,
    tet_indices: torch.Tensor,
) -> torch.Tensor:
    """Compute deformation gradient F = ds/dS for each tetrahedron.

    For a tetrahedron with vertices {X₀, X₁, X₂, X₃} at rest and
    {x₀, x₁, x₂, x₃} in deformed config:

        F = Ds · Dm^{-1}

    where:
        Dm = [X₁-X₀, X₂-X₀, X₃-X₀]  (reference edge matrix, 3×3)
        Ds = [x₁-x₀, x₂-x₀, x₃-x₀]  (deformed edge matrix, 3×3)

    Args:
        positions:      (N, 3) deformed nodal positions
        rest_positions: (N, 3) reference (rest) nodal positions
        tet_indices:    (T, 4) tetrahedron vertex indices

    Returns:
        F: (T, 3, 3) deformation gradient per element
    """
    # Gather vertices
    v0_r = rest_positions[tet_indices[:, 0]]  # (T, 3)
    v1_r = rest_positions[tet_indices[:, 1]]
    v2_r = rest_positions[tet_indices[:, 2]]
    v3_r = rest_positions[tet_indices[:, 3]]

    v0_d = positions[tet_indices[:, 0]]  # (T, 3)
    v1_d = positions[tet_indices[:, 1]]
    v2_d = positions[tet_indices[:, 2]]
    v3_d = positions[tet_indices[:, 3]]

    # Reference edge matrix Dm: columns are edge vectors
    Dm = torch.stack([v1_r - v0_r, v2_r - v0_r, v3_r - v0_r], dim=-1)  # (T, 3, 3)

    # Deformed edge matrix Ds
    Ds = torch.stack([v1_d - v0_d, v2_d - v0_d, v3_d - v0_d], dim=-1)  # (T, 3, 3)

    # F = Ds @ Dm^{-1}
    Dm_inv = torch.linalg.inv(Dm)  # (T, 3, 3)
    F = Ds @ Dm_inv                 # (T, 3, 3)

    return F


# ─────────────────────────────────────────────────────────────
# Isochoric Invariants
# ─────────────────────────────────────────────────────────────

def _compute_isochoric_invariants(
    F: torch.Tensor,
    fiber_dir: torch.Tensor,
) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """Compute isochoric invariants Ī₁ and Ī₄.

    Isochoric decomposition: F = J^{-1/3} F̄, where F̄ is volume-preserving.

    Ī₁ = J^{-2/3} I₁  where I₁ = tr(C) = ||F||²_F
    Ī₄ = J^{-2/3} I₄  where I₄ = a₀ · C · a₀ = ||F · a₀||²

    Note: Ī₄ is invariant to pure volumetric deformations (F = λI),
    because (λ³)^{-2/3} × λ² × 1 = λ^{-2} × λ² = 1. ✓

    Args:
        F:         (T, 3, 3) deformation gradient
        fiber_dir: (T, 3) or (3,) fiber direction unit vector(s) in reference config

    Returns:
        J:    (T,) volume ratio det(F)
        I1bar:(T,) isochoric first invariant Ī₁
        I4bar:(T,) isochoric fourth invariant Ī₄
    """
    T = F.shape[0]

    J = _det3x3(F)                          # (T,)
    J_safe = torch.clamp(J, min=1e-8)
    J_23 = J_safe.pow(2.0 / 3.0)           # J^{2/3}

    # I₁ = tr(F^T F) = ||F||²_Frobenius
    I1 = (F * F).sum(dim=(-2, -1))          # (T,)
    I1bar = I1 / J_23                        # Ī₁ = J^{-2/3} I₁

    # Broadcast fiber direction to (T, 3)
    if fiber_dir.dim() == 1:
        a0 = fiber_dir.unsqueeze(0).expand(T, -1)   # (T, 3)
    else:
        a0 = fiber_dir                               # already (T, 3)

    # I₄ = a₀ · C · a₀ = ||F · a₀||²  (since C = F^T F)
    Fa0 = (F @ a0.unsqueeze(-1)).squeeze(-1)        # (T, 3)
    I4 = (Fa0 * Fa0).sum(dim=-1)                    # (T,)
    I4bar = I4 / J_23                               # Ī₄ = J^{-2/3} I₄

    return J, I1bar, I4bar


# ─────────────────────────────────────────────────────────────
# TI Strain Energy Density
# ─────────────────────────────────────────────────────────────

def ti_energy_density(
    F: torch.Tensor,
    C1: float,
    D1: float,
    k1: float,
    k2: float,
    fiber_dir: torch.Tensor,
    barrier_threshold: float = 0.3,
    lambda_barrier: float = 100.0,
) -> Tuple[torch.Tensor, torch.Tensor, Dict[str, torch.Tensor]]:
    """Compute Transversely Isotropic strain energy density per element.

    Ψ_TI = C₁(Ī₁ - 3) + D₁(J - 1)² + (k₁/2k₂)[exp(k₂⟨Ī₄-1⟩²) - 1] + Ψ_barrier(J)

    The fiber term uses exponential stiffening (Holzapfel-Ogden):
        Ψ_fiber = (k₁/2k₂)[exp(k₂⟨Ī₄-1⟩²) - 1]

    where ⟨Ī₄-1⟩ = max(Ī₄-1, 0) activates fiber only under tension (Macaulay bracket).
    When k1=0, Ψ_fiber=0 and Ψ_TI reduces to Neo-Hookean (with isochoric correction).

    Barrier: log-barrier prevents element inversion (J→0⁺):
        Ψ_barrier = -λ_b × ln(J / J_threshold)  if J < J_threshold, else 0

    Args:
        F:                (T, 3, 3) deformation gradient
        C1:               matrix shear stiffness (Pa)
        D1:               volumetric stiffness (Pa)
        k1:               fiber stiffness (Pa), set 0 to recover Neo-Hookean
        k2:               fiber nonlinearity (dimensionless)
        fiber_dir:        (T, 3) or (3,) fiber direction unit vector
        barrier_threshold: J threshold for barrier activation (default 0.3)
        lambda_barrier:   barrier strength (default 100.0)

    Returns:
        psi:   (T,) total energy density per element
        J:     (T,) volume ratios (for diagnostics)
        info:  dict with component energies
    """
    J, I1bar, I4bar = _compute_isochoric_invariants(F, fiber_dir)

    # ── Matrix (isochoric Neo-Hookean) term ──
    psi_matrix = C1 * (I1bar - 3.0) + D1 * (J - 1.0) ** 2  # (T,)

    # ── Fiber (Holzapfel-Ogden exponential) term ──
    if k1 > 0.0:
        # Macaulay bracket: only tension activates fibers
        E4 = torch.clamp(I4bar - 1.0, min=0.0)      # ⟨Ī₄-1⟩ ≥ 0
        # Numerical safety: clamp k2*E4² to avoid exp overflow
        exponent = torch.clamp(k2 * E4 ** 2, max=80.0)
        psi_fiber = (k1 / (2.0 * k2)) * (torch.exp(exponent) - 1.0)  # (T,)
    else:
        psi_fiber = torch.zeros_like(psi_matrix)

    # ── Barrier term ──
    J_safe = torch.clamp(J, min=1e-8)
    barrier_mask = J_safe < barrier_threshold
    psi_barrier = torch.zeros_like(psi_matrix)
    if barrier_mask.any():
        log_ratio = torch.log(J_safe / barrier_threshold)   # ≤ 0 when J < thresh
        barrier_vals = -lambda_barrier * log_ratio            # ≥ 0
        psi_barrier = torch.where(barrier_mask, barrier_vals, psi_barrier)

    psi = psi_matrix + psi_fiber + psi_barrier

    info = {
        "J": J.detach(),
        "I1bar": I1bar.detach(),
        "I4bar": I4bar.detach(),
        "psi_matrix": psi_matrix.detach(),
        "psi_fiber": psi_fiber.detach(),
        "psi_barrier": psi_barrier.detach(),
    }

    return psi, J, info


# ─────────────────────────────────────────────────────────────
# Total TI Energy (volume-integrated)
# ─────────────────────────────────────────────────────────────

def compute_ti_energy(
    positions: torch.Tensor,
    rest_positions: torch.Tensor,
    tet_indices: torch.Tensor,
    C1: float,
    D1: float,
    k1: float,
    k2: float,
    fiber_dir: torch.Tensor,
    volumes: torch.Tensor,
    barrier_threshold: float = 0.3,
    lambda_barrier: float = 100.0,
) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
    """Compute total TI strain energy (volume-integrated).

    W = Σ_e Ψ_e × V₀_e

    Args:
        positions:        (N, 3) deformed nodal positions (requires_grad should be True)
        rest_positions:   (N, 3) reference nodal positions
        tet_indices:      (T, 4) tetrahedron vertex index array
        C1:               matrix shear stiffness (Pa)
        D1:               volumetric stiffness (Pa)
        k1:               fiber stiffness (Pa)
        k2:               fiber nonlinearity (dimensionless)
        fiber_dir:        (T, 3) or (3,) fiber direction unit vector
        volumes:          (T,) reference element volumes (m³)
        barrier_threshold: J threshold for barrier activation
        lambda_barrier:   barrier strength

    Returns:
        W_total: scalar total strain energy
        info:    dict with diagnostic quantities
    """
    F = _compute_deformation_gradient(positions, rest_positions, tet_indices)  # (T, 3, 3)
    psi, J, elem_info = ti_energy_density(
        F, C1, D1, k1, k2, fiber_dir, barrier_threshold, lambda_barrier
    )

    W_total = (psi * volumes).sum()  # scalar

    info = {
        **elem_info,
        "W_total": W_total.detach(),
        "W_matrix": (elem_info["psi_matrix"] * volumes).sum().item(),
        "W_fiber": (elem_info["psi_fiber"] * volumes).sum().item(),
        "W_barrier": (elem_info["psi_barrier"] * volumes).sum().item(),
        "J_min": J.min().item(),
        "J_max": J.max().item(),
        "J_mean": J.mean().item(),
        "n_inverted": (J <= 0).sum().item(),
        "I4bar_mean": elem_info["I4bar"].mean().item(),
        "I4bar_max": elem_info["I4bar"].max().item(),
    }

    return W_total, info


# ─────────────────────────────────────────────────────────────
# Nodal Force Computation via Autograd
# ─────────────────────────────────────────────────────────────

def compute_ti_stress_forces(
    positions: torch.Tensor,
    rest_positions: torch.Tensor,
    tet_indices: torch.Tensor,
    C1: float,
    D1: float,
    k1: float,
    k2: float,
    fiber_dir: torch.Tensor,
    volumes: torch.Tensor,
    barrier_threshold: float = 0.3,
    lambda_barrier: float = 100.0,
) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
    """Compute internal nodal forces via autograd of strain energy.

    f_internal = -∂W/∂x   (negative gradient = internal restoring force)

    This is exact (no analytical stress tensor needed) and automatically
    satisfies Newton's 3rd law when summed over elements.

    Args:
        positions: (N, 3) deformed positions, will be detached and re-wrapped
        rest_positions: (N, 3) reference positions
        tet_indices: (T, 4) vertex indices
        C1, D1, k1, k2: material parameters
        fiber_dir: (T, 3) or (3,) fiber direction
        volumes: (T,) reference element volumes
        barrier_threshold: J threshold
        lambda_barrier: barrier strength

    Returns:
        forces: (N, 3) internal nodal forces f = -∂W/∂x
        info:   diagnostic dict
    """
    pos = positions.detach().requires_grad_(True)

    W, info = compute_ti_energy(
        pos, rest_positions, tet_indices,
        C1, D1, k1, k2, fiber_dir, volumes,
        barrier_threshold, lambda_barrier,
    )

    W.backward()
    forces = -pos.grad.clone()  # internal restoring force = -∂W/∂x

    return forces, info


# ─────────────────────────────────────────────────────────────
# TI Physics Loss (main training objective)
# ─────────────────────────────────────────────────────────────

def ti_physics_loss(
    predicted_pos: torch.Tensor,
    rest_pos: torch.Tensor,
    tet_indices: torch.Tensor,
    params: Dict,
    external_forces: torch.Tensor,
    barrier_threshold: float = 0.3,
    lambda_barrier: float = 100.0,
) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
    """Compute TI physics loss: minimum potential energy principle.

    L = W_internal(x) - W_external(x)
      = Σ_e [Ψ_e(F_e) × V₀_e] - Σ_i [f_ext_i · u_i]

    where u_i = x_i - X_i is the displacement from rest.

    At mechanical equilibrium, dL/dx = 0 (∂W/∂x = f_ext).
    The GNN learns to predict x that minimizes this loss.

    Backward compatibility: when params['k1']=0, degenerates to Neo-Hookean
    with isochoric correction (Ī₁ instead of I₁).

    Args:
        predicted_pos:   (N, 3) predicted deformed positions from GNN
        rest_pos:        (N, 3) reference positions
        tet_indices:     (T, 4) tetrahedron vertex indices
        params:          dict with keys:
                           'C1' (float), 'D1' (float),
                           'k1' (float), 'k2' (float),
                           'fiber_dir' (Tensor, shape (3,) or (T,3)),
                           'volumes' (Tensor, shape (T,))
                           optionally 'boundary_mask' (BoolTensor, shape (N,))
        external_forces: (N, 3) external nodal force vector
        barrier_threshold: J threshold for barrier
        lambda_barrier:   barrier strength

    Returns:
        loss:  scalar loss value (total potential energy)
        info:  diagnostic dict with component values
    """
    C1 = float(params["C1"])
    D1 = float(params["D1"])
    k1 = float(params.get("k1", 0.0))
    k2 = float(params.get("k2", 1.0))  # avoid div-by-zero if k1=0
    fiber_dir = params["fiber_dir"]
    volumes = params["volumes"]

    # Enforce Dirichlet BC if boundary_mask provided
    pos = predicted_pos
    if "boundary_mask" in params and params["boundary_mask"] is not None:
        mask = params["boundary_mask"]
        # Zero displacement at fixed nodes: x_fixed = X_fixed
        pos = predicted_pos.clone()
        pos[mask] = rest_pos[mask]

    # ── Internal strain energy ──
    W_internal, info = compute_ti_energy(
        pos, rest_pos, tet_indices,
        C1, D1, k1, k2, fiber_dir, volumes,
        barrier_threshold, lambda_barrier,
    )

    # ── External work: f_ext · u  (u = x - X) ──
    displacements = pos - rest_pos  # (N, 3)
    W_external = (external_forces * displacements).sum()

    # ── Total potential energy ──
    loss = W_internal - W_external

    info.update({
        "W_external": W_external.detach().item(),
        "loss_total": loss.detach().item(),
        "k1": k1,
        "k2": k2,
    })

    return loss, info


# ─────────────────────────────────────────────────────────────
# Material Parameter Helpers
# ─────────────────────────────────────────────────────────────

def ti_params_from_engineering(
    E_L: float,
    E_T: float,
    nu_LT: float,
    G_LT: float,
    k2: float = 10.0,
) -> Dict[str, float]:
    """Convert engineering constants to TI constitutive parameters.

    For a transversely isotropic material with longitudinal axis L and
    transverse plane T, the engineering constants are:
        E_L:   longitudinal Young's modulus (Pa)
        E_T:   transverse Young's modulus (Pa)
        nu_LT: Poisson's ratio (longitudinal-transverse coupling)
        G_LT:  longitudinal shear modulus (Pa)

    We map to TI hyperelastic parameters via:
        μ_T = E_T / (2(1 + ν_TT))  ≈ G_LT  (transverse shear modulus)
        C₁  = μ_T / 2              (half transverse shear modulus, as in Neo-Hookean)
        D₁  = E_T / (6(1 - 2ν_TT)) (bulk modulus approximation)
        k₁  = E_L - E_T            (fiber stiffness excess over matrix, Pa)
        k₂  = user-specified        (nonlinearity, calibrated separately)

    This is an approximation valid for moderate strains. For large deformations,
    use fully nonlinear TI fitting (e.g., via experimental stress-stretch curves).

    Args:
        E_L:   longitudinal Young's modulus (Pa)
        E_T:   transverse Young's modulus (Pa)
        nu_LT: longitudinal-transverse Poisson ratio
        G_LT:  longitudinal shear modulus (Pa)
        k2:    fiber nonlinearity (dimensionless, default 10.0)

    Returns:
        dict with C1, D1, k1, k2
    """
    # Transverse Poisson ratio (approximate for TI): nu_TT ≈ nu_LT
    nu_TT = nu_LT

    # Transverse shear modulus
    G_T = E_T / (2.0 * (1.0 + nu_TT))

    # Map to Neo-Hookean-style constants
    C1 = G_T / 2.0                          # half shear modulus (matrix)
    D1 = E_T / (6.0 * (1.0 - 2.0 * nu_TT))  # bulk modulus approximation

    # Fiber stiffness: excess over isotropic matrix
    k1 = max(0.0, E_L - E_T)               # fiber reinforcement stiffness

    return {"C1": C1, "D1": D1, "k1": k1, "k2": k2}
