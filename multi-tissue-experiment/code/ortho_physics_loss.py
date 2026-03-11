"""
ortho_physics_loss.py - Orthotropic Physics Loss for DPC-GNN (Level 2).

Extends Level 1 (Transversely Isotropic, 5 constants) to full orthotropic symmetry
with 9 independent elastic constants, supporting complete cortical bone mechanics.

Two implementation paths:
  Path A: Dual-fiber HGO extension (recommended for fiber-reinforced tissues)
    Psi = C1*(I1bar-3) + D1*(J-1)^2 + sum_i (k1i/2k2i)*[exp(k2i*<I4i-1>^2)-1] + Psi_barrier
  Path B: Full stiffness tensor C_ijkl (Voigt 6x6 SPD matrix), Saint Venant-Kirchhoff
    Psi = 0.5 * E : C : E  where E = 0.5*(F^T F - I)

Backward compatibility:
  - k1_2=0 -> Level 1 TI (single fiber family)
  - k1_1=k1_2, k2_1=k2_2, a01 perp a02: TI-like symmetric anisotropy

Material ref: Cortical bone (Reilly & Burstein 1975, human femur)
  E1=E2=11.5 GPa (rad/circ), E3=17.0 GPa (axial)
  G12=3.6 GPa, G13=G23=3.3 GPa; nu12=0.58, nu13=nu23=0.31

References:
    Reilly DT, Burstein AH (1975) J Biomech 8:393-405.
    Holzapfel GA, Ogden RW (2010) Proc R Soc A 466:1551-1597.
    Holzapfel GA (2000) Nonlinear Solid Mechanics. Wiley.
    Gasser TC, Ogden RW, Holzapfel GA (2006) J R Soc Interface 3:15-35.
"""

import torch
from typing import Tuple, Dict, Optional

from ti_physics_loss import (
    _det3x3,
    _compute_deformation_gradient,
    _compute_isochoric_invariants,
)


# ─────────────────────────────────────────────────────────────
# Engineering Constants -> Voigt Stiffness Matrix
# ─────────────────────────────────────────────────────────────

def engineering_to_voigt(
    E1: float, E2: float, E3: float,
    nu12: float, nu13: float, nu23: float,
    G12: float, G13: float, G23: float,
) -> torch.Tensor:
    """Convert 9 orthotropic engineering constants to 6x6 Voigt stiffness matrix.

    Compliance S (6x6):
        eps = S . sigma
        S[0,0]=1/E1, S[1,1]=1/E2, S[2,2]=1/E3
        S[0,1]=S[1,0]=-nu21/E2, S[0,2]=S[2,0]=-nu31/E3, S[1,2]=S[2,1]=-nu32/E3
        S[3,3]=1/G23, S[4,4]=1/G13, S[5,5]=1/G12
    where nu21=nu12*E2/E1, nu31=nu13*E3/E1, nu32=nu23*E3/E2 (symmetry conditions).
    Stiffness C = S^{-1}.

    Args:
        E1, E2, E3:       Young's moduli along axes 1, 2, 3 (Pa)
                          [Reilly & Burstein 1975: E1=E2=11.5e9, E3=17.0e9 Pa]
        nu12, nu13, nu23: Poisson ratios [Reilly & Burstein 1975: 0.58, 0.31, 0.31]
        G12, G13, G23:    Shear moduli (Pa) [Reilly & Burstein 1975: 3.6e9, 3.3e9, 3.3e9]

    Returns:
        C_voigt: (6, 6) float64 SPD stiffness matrix (Pa)

    Raises:
        ValueError: if compliance or stiffness is not positive definite

    References:
        Lekhnitskii SG (1963) Theory of Elasticity of an Anisotropic Body.
        Jones RM (1975) Mechanics of Composite Materials.
    """
    for name, val in [("E1",E1),("E2",E2),("E3",E3),("G12",G12),("G13",G13),("G23",G23)]:
        if val <= 0:
            raise ValueError(f"{name} must be > 0, got {val}")

    # Reciprocal relations: nuij/Ei = nuji/Ej
    nu21 = nu12 * E2 / E1
    nu31 = nu13 * E3 / E1
    nu32 = nu23 * E3 / E2

    S = torch.zeros(6, 6, dtype=torch.float64)
    S[0, 0] =  1.0/E1;  S[0, 1] = -nu21/E2; S[0, 2] = -nu31/E3
    S[1, 0] = -nu12/E1; S[1, 1] =  1.0/E2;  S[1, 2] = -nu32/E3
    S[2, 0] = -nu13/E1; S[2, 1] = -nu23/E2; S[2, 2] =  1.0/E3
    S[3, 3] = 1.0/G23
    S[4, 4] = 1.0/G13
    S[5, 5] = 1.0/G12

    # Check S symmetry
    sym_err = (S - S.T).abs().max().item()
    if sym_err > 1e-12:
        raise ValueError(f"Compliance matrix not symmetric: {sym_err:.2e}")

    # Check S positive definiteness
    eig_S = torch.linalg.eigvalsh(S)
    if eig_S.min().item() <= 0:
        raise ValueError(
            f"Compliance S not positive definite. Min eigenvalue = {eig_S.min().item():.4e}. "
            f"Check: nu12^2 < E2/E1, nu13^2 < E3/E1, nu23^2 < E3/E2 required."
        )

    # Stiffness C = S^{-1}, symmetrize
    C_voigt = torch.linalg.inv(S)
    C_voigt = 0.5 * (C_voigt + C_voigt.T)

    # Check C positive definiteness
    eig_C = torch.linalg.eigvalsh(C_voigt)
    if eig_C.min().item() <= 0:
        raise ValueError(f"Stiffness C not positive definite. Min eig = {eig_C.min().item():.4e}.")

    # Check diagonal elements > 0
    for i in range(6):
        if C_voigt[i, i].item() <= 0:
            raise ValueError(f"C[{i},{i}] = {C_voigt[i,i].item():.4e} <= 0.")

    return C_voigt


# ─────────────────────────────────────────────────────────────
# Voigt -> Dual-Fiber Approximate Conversion
# ─────────────────────────────────────────────────────────────

def voigt_to_dual_fiber(C_voigt: torch.Tensor) -> Dict[str, object]:
    """Approximate mapping from 6x6 Voigt stiffness to dual-fiber HGO parameters.

    Strategy (physics-motivated, valid for small-moderate strains):
      mu_avg = (C44 + C55 + C66)/3  [Voigt: C44=G23, C55=G13, C66=G12]
      C1 = mu_avg/2
      kappa = (C11+C22+C33+2C12+2C13+2C23)/9
      D1 = kappa/2
      iso_base = 2*mu_avg + kappa  [isotropic reference stiffness]
      k1_1 = max(0, C33 - iso_base)  [axial fiber excess, for long-bone axis 3]
      k1_2 = max(0, max(C11,C22) - iso_base)  [in-plane secondary fiber]
      fiber_dir1 = [0,0,1] (axial), fiber_dir2 = [1,0,0] or [0,1,0]

    Args:
        C_voigt: (6, 6) Voigt stiffness (Pa), from engineering_to_voigt()

    Returns:
        dict: 'C1','D1','k1_1','k2_1','k1_2','k2_2','fiber_dir1','fiber_dir2'

    References:
        Gasser TC, Ogden RW, Holzapfel GA (2006) J R Soc Interface 3:15-35.
    """
    C = C_voigt.double()
    mu_avg = (C[3,3] + C[4,4] + C[5,5]) / 3.0
    C1 = (mu_avg / 2.0).item()
    kappa = (C[0,0]+C[1,1]+C[2,2] + 2.0*C[0,1]+2.0*C[0,2]+2.0*C[1,2]) / 9.0
    D1 = (kappa / 2.0).item()
    iso_base = 2.0 * mu_avg + kappa

    # Fiber 1: axial (axis 3), typically dominant in long bones
    k1_1 = max(0.0, (C[2,2] - iso_base).item())

    # Fiber 2: in-plane secondary
    max_inplane = max(C[0,0].item(), C[1,1].item())
    k1_2 = max(0.0, max_inplane - iso_base.item())

    fiber_dir1 = torch.tensor([0.0, 0.0, 1.0], dtype=torch.float64)
    if C[1,1].item() > C[0,0].item():
        fiber_dir2 = torch.tensor([0.0, 1.0, 0.0], dtype=torch.float64)
    else:
        fiber_dir2 = torch.tensor([1.0, 0.0, 0.0], dtype=torch.float64)

    return {
        "C1": C1, "D1": D1,
        "k1_1": k1_1, "k2_1": 1.0,
        "k1_2": k1_2, "k2_2": 1.0,
        "fiber_dir1": fiber_dir1,
        "fiber_dir2": fiber_dir2,
    }


# ─────────────────────────────────────────────────────────────
# Path A: Dual-Fiber HGO Energy Density
# ─────────────────────────────────────────────────────────────

def ortho_energy_density_dual_fiber(
    F: torch.Tensor,
    C1: float,
    D1: float,
    k1_1: float,
    k2_1: float,
    k1_2: float,
    k2_2: float,
    fiber_dir1: torch.Tensor,
    fiber_dir2: torch.Tensor,
    barrier_threshold: float = 0.3,
    lambda_barrier: float = 100.0,
) -> Tuple[torch.Tensor, torch.Tensor, Dict[str, torch.Tensor]]:
    """Orthotropic energy density via dual-fiber HGO model (Path A).

    Psi = C1*(I1bar-3) + D1*(J-1)^2
          + (k1_1/2k2_1)*[exp(k2_1*<I4bar_1-1>^2)-1]
          + (k1_2/2k2_2)*[exp(k2_2*<I4bar_2-1>^2)-1]
          + Psi_barrier(J)

    Isochoric invariants:
      I1bar = J^{-2/3} * tr(F^T F)
      I4bar_i = J^{-2/3} * ||F * a0i||^2    (i=1,2)
      <x> = max(x, 0)  Macaulay bracket: fibers activate only in tension.

    Backward compat: k1_2=0 -> exactly Level 1 TI.

    Args:
        F:               (T, 3, 3) deformation gradient
        C1:              matrix shear stiffness (Pa) [Holzapfel&Ogden 2010]
        D1:              volumetric stiffness (Pa) [Holzapfel&Ogden 2010]
        k1_1:            fiber 1 linear stiffness (Pa) [Holzapfel&Ogden 2010 eq 3.4]
        k2_1:            fiber 1 exponential nonlinearity (dimensionless, >0)
        k1_2:            fiber 2 linear stiffness (Pa); 0 -> TI degeneracy
        k2_2:            fiber 2 nonlinearity (dimensionless, >0)
        fiber_dir1:      (T,3) or (3,) primary fiber unit vector (reference config)
        fiber_dir2:      (T,3) or (3,) secondary fiber unit vector (a01.a02 should=0)
        barrier_threshold: J threshold for log-barrier (default 0.3)
        lambda_barrier:  log-barrier strength (default 100.0)

    Returns:
        psi:  (T,) energy density (Pa)
        J:    (T,) volume ratios
        info: dict with component energies and invariants
    """
    T = F.shape[0]

    # Family 1 invariants (also computes J, I1bar)
    J, I1bar, I4bar_1 = _compute_isochoric_invariants(F, fiber_dir1)

    # Family 2: compute I4bar_2 using same J^{2/3}
    J_safe = torch.clamp(J, min=1e-8)
    J_23 = J_safe.pow(2.0 / 3.0)

    if fiber_dir2.dim() == 1:
        a02 = fiber_dir2.unsqueeze(0).expand(T, -1)   # (T, 3)
    else:
        a02 = fiber_dir2

    Fa02 = (F @ a02.unsqueeze(-1)).squeeze(-1)         # (T, 3)
    I4bar_2 = (Fa02 * Fa02).sum(dim=-1) / J_23         # (T,)

    # Matrix term
    psi_matrix = C1 * (I1bar - 3.0) + D1 * (J - 1.0) ** 2

    # Fiber 1
    if k1_1 > 0.0:
        E4_1 = torch.clamp(I4bar_1 - 1.0, min=0.0)
        exp1  = torch.clamp(k2_1 * E4_1 ** 2, max=80.0)
        psi_fiber1 = (k1_1 / (2.0 * k2_1)) * (torch.exp(exp1) - 1.0)
    else:
        psi_fiber1 = torch.zeros_like(psi_matrix)

    # Fiber 2
    if k1_2 > 0.0:
        E4_2 = torch.clamp(I4bar_2 - 1.0, min=0.0)
        exp2  = torch.clamp(k2_2 * E4_2 ** 2, max=80.0)
        psi_fiber2 = (k1_2 / (2.0 * k2_2)) * (torch.exp(exp2) - 1.0)
    else:
        psi_fiber2 = torch.zeros_like(psi_matrix)

    # Barrier
    barrier_mask = J_safe < barrier_threshold
    psi_barrier = torch.zeros_like(psi_matrix)
    if barrier_mask.any():
        log_ratio  = torch.log(J_safe / barrier_threshold)
        psi_barrier = torch.where(barrier_mask, -lambda_barrier * log_ratio, psi_barrier)

    psi = psi_matrix + psi_fiber1 + psi_fiber2 + psi_barrier

    info = {
        "J": J.detach(),
        "I1bar": I1bar.detach(),
        "I4bar_1": I4bar_1.detach(),
        "I4bar_2": I4bar_2.detach(),
        "psi_matrix": psi_matrix.detach(),
        "psi_fiber1": psi_fiber1.detach(),
        "psi_fiber2": psi_fiber2.detach(),
        "psi_barrier": psi_barrier.detach(),
    }
    return psi, J, info


# ─────────────────────────────────────────────────────────────
# Path B: Full Stiffness Tensor (Saint Venant-Kirchhoff)
# ─────────────────────────────────────────────────────────────

def ortho_energy_density_stiffness(
    F: torch.Tensor,
    C_voigt_6x6: torch.Tensor,
    barrier_threshold: float = 0.3,
    lambda_barrier: float = 100.0,
) -> Tuple[torch.Tensor, torch.Tensor, Dict[str, torch.Tensor]]:
    """Orthotropic energy density via full stiffness tensor (Path B, SVK model).

    Saint Venant-Kirchhoff:
        E = 0.5*(F^T F - I)      Green-Lagrange strain
        Psi = 0.5 * eps^T . C_voigt . eps

    Voigt strain: eps = [E11, E22, E33, 2E23, 2E13, 2E12]  (engineering shear convention)

    Properties:
      - Reduces to linear elasticity as F -> I
      - Psi >= 0 when C_voigt is SPD
      - Valid for small-to-moderate strains; add barrier for large deformations

    Args:
        F:             (T, 3, 3) deformation gradient
        C_voigt_6x6:  (6, 6) SPD Voigt stiffness (Pa), from engineering_to_voigt()
                      Row/col order: [11, 22, 33, 23(=4), 13(=5), 12(=6)]
        barrier_threshold: J threshold (default 0.3)
        lambda_barrier:    barrier strength (default 100.0)

    Returns:
        psi:  (T,) energy density (Pa)
        J:    (T,) volume ratios
        info: dict with strain components

    References:
        Bonet J, Wood RD (2008) Nonlinear Continuum Mechanics for FEA. Cambridge.
        Holzapfel GA (2000) Nonlinear Solid Mechanics. Wiley. Sec 6.4.
    """
    # Right Cauchy-Green C = F^T F
    C_tens = F.transpose(-2, -1) @ F    # (T, 3, 3)

    # Green-Lagrange E = 0.5*(C-I)
    I3 = torch.eye(3, dtype=F.dtype, device=F.device).unsqueeze(0)
    E_tens = 0.5 * (C_tens - I3)        # (T, 3, 3)

    # Voigt strain vector (engineering shear: factor 2 on off-diagonal)
    eps = torch.stack([
        E_tens[:, 0, 0],           # E11
        E_tens[:, 1, 1],           # E22
        E_tens[:, 2, 2],           # E33
        2.0 * E_tens[:, 1, 2],    # 2E23
        2.0 * E_tens[:, 0, 2],    # 2E13
        2.0 * E_tens[:, 0, 1],    # 2E12
    ], dim=-1)   # (T, 6)

    C_mat = C_voigt_6x6.to(dtype=F.dtype, device=F.device)
    Ce = eps @ C_mat.T                     # (T, 6): C_mat symmetric, .T=C_mat
    psi_elastic = 0.5 * (Ce * eps).sum(dim=-1)   # (T,)

    J = _det3x3(F)
    J_safe = torch.clamp(J, min=1e-8)

    barrier_mask = J_safe < barrier_threshold
    psi_barrier = torch.zeros_like(psi_elastic)
    if barrier_mask.any():
        log_ratio   = torch.log(J_safe / barrier_threshold)
        psi_barrier = torch.where(barrier_mask, -lambda_barrier * log_ratio, psi_barrier)

    psi = psi_elastic + psi_barrier

    info = {
        "J": J.detach(),
        "E11": E_tens[:,0,0].detach(), "E22": E_tens[:,1,1].detach(),
        "E33": E_tens[:,2,2].detach(), "E23": E_tens[:,1,2].detach(),
        "E13": E_tens[:,0,2].detach(), "E12": E_tens[:,0,1].detach(),
        "eps_voigt": eps.detach(),
        "psi_elastic": psi_elastic.detach(),
        "psi_barrier": psi_barrier.detach(),
    }
    return psi, J, info


# ─────────────────────────────────────────────────────────────
# Volume-Integrated Energies
# ─────────────────────────────────────────────────────────────

def compute_ortho_energy(
    positions: torch.Tensor,
    rest_positions: torch.Tensor,
    tet_indices: torch.Tensor,
    volumes: torch.Tensor,
    mode: str = "dual_fiber",
    # Path A
    C1: float = 0.0,
    D1: float = 0.0,
    k1_1: float = 0.0,
    k2_1: float = 1.0,
    k1_2: float = 0.0,
    k2_2: float = 1.0,
    fiber_dir1: Optional[torch.Tensor] = None,
    fiber_dir2: Optional[torch.Tensor] = None,
    # Path B
    C_voigt_6x6: Optional[torch.Tensor] = None,
    # Common
    barrier_threshold: float = 0.3,
    lambda_barrier: float = 100.0,
) -> Tuple[torch.Tensor, Dict[str, object]]:
    """Compute total orthotropic strain energy W = sum_e Psi_e * V0_e.

    Args:
        positions:      (N, 3) deformed positions (requires_grad True for autograd)
        rest_positions: (N, 3) reference positions
        tet_indices:    (T, 4) tetrahedron vertex indices
        volumes:        (T,) reference element volumes (m^3)
        mode:           'dual_fiber' (Path A) or 'stiffness' (Path B)
        C1, D1, k1_1, k2_1, k1_2, k2_2: Path A material parameters
        fiber_dir1:     (T,3)|(3,) primary fiber direction [Path A]
        fiber_dir2:     (T,3)|(3,) secondary fiber direction [Path A]
        C_voigt_6x6:   (6,6) Voigt stiffness [Path B]
        barrier_threshold, lambda_barrier: barrier parameters

    Returns:
        W_total: scalar total strain energy
        info:    diagnostic dict
    """
    if fiber_dir1 is None:
        fiber_dir1 = torch.tensor([0.0, 0.0, 1.0], dtype=positions.dtype, device=positions.device)
    if fiber_dir2 is None:
        fiber_dir2 = torch.tensor([1.0, 0.0, 0.0], dtype=positions.dtype, device=positions.device)

    F = _compute_deformation_gradient(positions, rest_positions, tet_indices)

    if mode == "dual_fiber":
        psi, J, elem_info = ortho_energy_density_dual_fiber(
            F, C1, D1, k1_1, k2_1, k1_2, k2_2,
            fiber_dir1, fiber_dir2, barrier_threshold, lambda_barrier
        )
        W_total = (psi * volumes).sum()
        info = {
            **elem_info,
            "W_total": W_total.detach(),
            "W_matrix":   (elem_info["psi_matrix"] * volumes).sum().item(),
            "W_fiber1":   (elem_info["psi_fiber1"] * volumes).sum().item(),
            "W_fiber2":   (elem_info["psi_fiber2"] * volumes).sum().item(),
            "W_barrier":  (elem_info["psi_barrier"] * volumes).sum().item(),
            "J_min": J.min().item(), "J_max": J.max().item(), "J_mean": J.mean().item(),
            "n_inverted": (J <= 0).sum().item(),
            "I4bar_1_mean": elem_info["I4bar_1"].mean().item(),
            "I4bar_2_mean": elem_info["I4bar_2"].mean().item(),
        }
    elif mode == "stiffness":
        if C_voigt_6x6 is None:
            raise ValueError("C_voigt_6x6 must be provided for mode='stiffness'")
        psi, J, elem_info = ortho_energy_density_stiffness(
            F, C_voigt_6x6, barrier_threshold, lambda_barrier
        )
        W_total = (psi * volumes).sum()
        info = {
            **elem_info,
            "W_total":   W_total.detach(),
            "W_elastic": (elem_info["psi_elastic"] * volumes).sum().item(),
            "W_barrier": (elem_info["psi_barrier"] * volumes).sum().item(),
            "J_min": J.min().item(), "J_max": J.max().item(), "J_mean": J.mean().item(),
            "n_inverted": (J <= 0).sum().item(),
        }
    else:
        raise ValueError(f"Unknown mode '{mode}'. Use 'dual_fiber' or 'stiffness'.")

    return W_total, info


# ─────────────────────────────────────────────────────────────
# Nodal Forces via Autograd
# ─────────────────────────────────────────────────────────────

def compute_ortho_forces(
    positions: torch.Tensor,
    rest_positions: torch.Tensor,
    tet_indices: torch.Tensor,
    volumes: torch.Tensor,
    mode: str = "dual_fiber",
    C1: float = 0.0,
    D1: float = 0.0,
    k1_1: float = 0.0,
    k2_1: float = 1.0,
    k1_2: float = 0.0,
    k2_2: float = 1.0,
    fiber_dir1: Optional[torch.Tensor] = None,
    fiber_dir2: Optional[torch.Tensor] = None,
    C_voigt_6x6: Optional[torch.Tensor] = None,
    barrier_threshold: float = 0.3,
    lambda_barrier: float = 100.0,
) -> Tuple[torch.Tensor, Dict[str, object]]:
    """Compute internal nodal forces via autograd of orthotropic strain energy.

    f_internal = -dW/dx   (negative gradient = restoring force)

    Satisfies Newton's 3rd law automatically (energy is translationally invariant).

    Args:
        positions:      (N, 3) deformed positions
        rest_positions: (N, 3) reference positions
        tet_indices:    (T, 4) vertex indices
        volumes:        (T,) reference volumes
        mode:           'dual_fiber' or 'stiffness'
        (material parameters as in compute_ortho_energy)

    Returns:
        forces: (N, 3) internal nodal forces f = -dW/dx
        info:   diagnostic dict
    """
    pos = positions.detach().requires_grad_(True)
    W, info = compute_ortho_energy(
        pos, rest_positions, tet_indices, volumes, mode=mode,
        C1=C1, D1=D1, k1_1=k1_1, k2_1=k2_1, k1_2=k1_2, k2_2=k2_2,
        fiber_dir1=fiber_dir1, fiber_dir2=fiber_dir2,
        C_voigt_6x6=C_voigt_6x6,
        barrier_threshold=barrier_threshold, lambda_barrier=lambda_barrier,
    )
    W.backward()
    forces = -pos.grad.clone()
    return forces, info


# ─────────────────────────────────────────────────────────────
# Orthotropic Physics Loss
# ─────────────────────────────────────────────────────────────

def ortho_physics_loss(
    predicted_pos: torch.Tensor,
    rest_pos: torch.Tensor,
    tet_indices: torch.Tensor,
    params: Dict,
    external_forces: torch.Tensor,
    barrier_threshold: float = 0.3,
    lambda_barrier: float = 100.0,
) -> Tuple[torch.Tensor, Dict[str, object]]:
    """Compute orthotropic physics loss: minimum potential energy principle.

    L = W_internal(x) - W_external(x)
      = sum_e [Psi_e(F_e) * V0_e] - sum_i [f_ext_i . u_i]

    where u_i = x_i - X_i is displacement from rest.

    At mechanical equilibrium, dL/dx = 0 (dW/dx = f_ext).
    GNN learns to predict x minimizing this loss.

    Backward compat: params['k1_2']=0 -> Level 1 TI loss.

    Args:
        predicted_pos:            (N, 3) predicted deformed positions from GNN
        rest_pos:      (N, 3) reference positions
        tet_indices:   (T, 4) tetrahedron vertex indices
        params:        dict with keys:
                         mode: 'dual_fiber' (default) or 'stiffness'
                         volumes: (T,) element volumes
                         --- dual_fiber params ---
                         C1, D1, k1_1, k2_1, k1_2, k2_2 (floats)
                         fiber_dir1, fiber_dir2 (Tensors)
                         --- stiffness params ---
                         C_voigt_6x6: (6,6) Tensor
                         --- optional ---
                         boundary_mask: BoolTensor (N,) for Dirichlet BC
        external_forces: (N, 3) external nodal force vector
        barrier_threshold: J threshold for barrier
        lambda_barrier:   barrier strength

    Returns:
        loss: scalar total potential energy
        info: diagnostic dict
    """
    mode      = params.get("mode", "dual_fiber")
    volumes   = params["volumes"]
    C1        = float(params.get("C1",   0.0))
    D1        = float(params.get("D1",   0.0))
    k1_1      = float(params.get("k1_1", 0.0))
    k2_1      = float(params.get("k2_1", 1.0))
    k1_2      = float(params.get("k1_2", 0.0))
    k2_2      = float(params.get("k2_2", 1.0))
    fiber_dir1    = params.get("fiber_dir1", None)
    fiber_dir2    = params.get("fiber_dir2", None)
    C_voigt_6x6   = params.get("C_voigt_6x6", None)

    # Enforce Dirichlet BC (fixed nodes)
    pos = predicted_pos
    if "boundary_mask" in params and params["boundary_mask"] is not None:
        mask = params["boundary_mask"]
        pos = predicted_pos.clone()
        pos[mask] = rest_pos[mask]

    W_internal, info = compute_ortho_energy(
        pos, rest_pos, tet_indices, volumes, mode=mode,
        C1=C1, D1=D1, k1_1=k1_1, k2_1=k2_1, k1_2=k1_2, k2_2=k2_2,
        fiber_dir1=fiber_dir1, fiber_dir2=fiber_dir2,
        C_voigt_6x6=C_voigt_6x6,
        barrier_threshold=barrier_threshold, lambda_barrier=lambda_barrier,
    )

    # External work: f_ext . u  (u = x - X)
    displacements = pos - rest_pos
    W_external = (external_forces * displacements).sum()

    loss = W_internal - W_external

    info.update({
        "W_external": W_external.detach().item(),
        "loss_total": loss.detach().item(),
        "mode": mode,
    })
    return loss, info
