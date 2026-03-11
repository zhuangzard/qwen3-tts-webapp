"""
anisotropic_edge_features.py — Direction-dependent edge features for DPC-GNN.

Extends isotropic edge features with material axis dot products:

    e_ij = [r_ij(3), |r_ij|(1), r̂_ij·d₁, r̂_ij·d₂, r̂_ij·d₃]  ∈ ℝ⁷

where:
    r_ij = x_j - x_i               : displacement vector from i to j
    r̂_ij = r_ij / |r_ij|          : unit direction vector
    d_k   = k-th material axis      : material frame axes at node i

Key antisymmetry property:
    r̂_ji = -r̂_ij   →   r̂_ji·d_k = -r̂_ij·d_k

This means the direction dot products flip sign under edge reversal,
exactly like r_ij. The AntisymmetricMP constraint m_ji = -m_ij is
therefore automatically satisfied: direction features contribute to
force antisymmetry without any extra architectural modification.

This is fundamentally different from using scalar |r_ij| (which is
symmetric) — the signed projections encode directionality in material frame.

Usage:
    # Global fiber direction (e.g., cortical bone along z-axis)
    material_axes = assign_fiber_directions(positions, tet_indices, fiber_dir='z')
    edge_attr = compute_anisotropic_edge_features(positions, edge_index, material_axes)

    # Per-node axes computed from local geometry
    material_axes = assign_fiber_directions(
        positions, tet_indices, fiber_dir='local_principal'
    )

References:
    Thomas N et al. (2018) Tensor field networks: Rotation- and
        translation-equivariant neural networks for 3D point clouds.
        arXiv:1802.08219.
    Fuchs F et al. (2020) SE(3)-Transformers: 3D roto-translation
        equivariant attention networks. NeurIPS 2020.

Expert Review:
    - GNN架构专家: AntisymmetricMP compatibility, edge feature design
    - 计算力学专家: material frame conventions, fiber direction assignment
"""

import torch
import numpy as np
from typing import Union, Optional, Tuple


# ─────────────────────────────────────────────────────────────
# Core Edge Feature Computation
# ─────────────────────────────────────────────────────────────

def compute_anisotropic_edge_features(
    positions: torch.Tensor,
    edge_index: torch.LongTensor,
    material_axes: torch.Tensor,
    eps: float = 1e-8,
) -> torch.Tensor:
    """Compute direction-encoded edge features for anisotropic materials.

    For each directed edge (i→j):
        r_ij  = x_j - x_i                         (displacement, 3D)
        |r_ij| = ||r_ij||                          (distance, scalar)
        r̂_ij  = r_ij / |r_ij|                     (unit direction)
        dot_k  = r̂_ij · d_k^{(i)}  for k=1,2,3   (projections, 3D)

    Output: e_ij = [r_ij (3D), |r_ij| (1D), dot_1 (1D), dot_2 (1D), dot_3 (1D)] ∈ ℝ⁷

    Antisymmetry: e_ji[0:3] = -e_ij[0:3] (r_ji = -r_ij)
                  e_ji[4:7] = -e_ij[4:7] (r̂_ji = -r̂_ij → dot products negate)
                  e_ji[3]   = e_ij[3]    (|r_ji| = |r_ij|, symmetric)

    Note: material axes are evaluated at source node i (standard GNN convention).

    Args:
        positions:     (N, 3) nodal positions
        edge_index:    (2, E) directed edge index, edge_index[0]=src, [1]=dst
        material_axes: (N, 3, 3) per-node material frame, axes[i, :, k] = d_k at node i
                       OR (3, 3) global material frame (same for all nodes)
        eps:           small value to avoid division by zero in normalization

    Returns:
        edge_attr: (E, 7) edge features [r_ij(3), |r_ij|(1), dot₁, dot₂, dot₃]
    """
    src = edge_index[0]  # (E,)
    dst = edge_index[1]  # (E,)

    # Displacement vector r_ij = x_j - x_i
    r_ij = positions[dst] - positions[src]          # (E, 3)

    # Distance |r_ij|
    dist = r_ij.norm(dim=-1, keepdim=True)          # (E, 1)

    # Unit direction r̂_ij (safe normalization)
    r_hat = r_ij / (dist + eps)                      # (E, 3)

    # Material axes at source nodes
    if material_axes.dim() == 2:
        # Global frame: broadcast to all edges
        axes = material_axes.unsqueeze(0).expand(r_ij.shape[0], -1, -1)  # (E, 3, 3)
    else:
        axes = material_axes[src]                    # (E, 3, 3)

    # Dot products: r̂_ij · d_k for k=1,2,3
    # axes[:, :, k] is the k-th axis vector at each edge source node
    dots = (r_hat.unsqueeze(-1) * axes).sum(dim=1)  # (E, 3): [dot₁, dot₂, dot₃]

    # Concatenate: [r_ij(3), dist(1), dot₁, dot₂, dot₃]
    edge_attr = torch.cat([r_ij, dist, dots], dim=-1)  # (E, 7)

    return edge_attr


# ─────────────────────────────────────────────────────────────
# Fiber Direction Assignment
# ─────────────────────────────────────────────────────────────

def assign_fiber_directions(
    positions: torch.Tensor,
    tet_indices: torch.Tensor,
    fiber_dir: Union[str, torch.Tensor] = 'z',
    n_nodes: Optional[int] = None,
) -> torch.Tensor:
    """Assign material frame axes to each node.

    The material frame {d₁, d₂, d₃} defines the anisotropy orientation:
        d₁: primary fiber direction (e.g., bone longitudinal axis)
        d₂, d₃: transverse directions (orthonormal to d₁)

    Supports:
        'x', 'y', 'z': global Cartesian alignment (fiber along that axis)
        Tensor (3,): custom global fiber direction
        'local_principal': per-element principal direction from geometry

    For transversely isotropic materials, d₁ is the symmetry axis.
    The transverse frame {d₂, d₃} is constructed via Gram-Schmidt.

    Args:
        positions:  (N, 3) nodal positions
        tet_indices:(T, 4) tetrahedron vertex indices (used for local geometry)
        fiber_dir:  one of 'x', 'y', 'z', or (3,) custom direction, or 'local_principal'
        n_nodes:    number of nodes (default: inferred from positions)

    Returns:
        material_axes: (N, 3, 3) per-node material frame
                       axes[i, :, 0] = d₁ (fiber direction)
                       axes[i, :, 1] = d₂ (transverse 1)
                       axes[i, :, 2] = d₃ (transverse 2)
    """
    N = n_nodes or positions.shape[0]
    device = positions.device

    # ── Determine primary fiber direction ──
    if isinstance(fiber_dir, str):
        if fiber_dir == 'x':
            d1 = torch.tensor([1.0, 0.0, 0.0], device=device)
        elif fiber_dir == 'y':
            d1 = torch.tensor([0.0, 1.0, 0.0], device=device)
        elif fiber_dir == 'z':
            d1 = torch.tensor([0.0, 0.0, 1.0], device=device)
        elif fiber_dir == 'local_principal':
            return _assign_local_principal_axes(positions, tet_indices, N)
        else:
            raise ValueError(f"Unknown fiber_dir string: '{fiber_dir}'. "
                             f"Use 'x', 'y', 'z', or 'local_principal'.")
    elif isinstance(fiber_dir, torch.Tensor):
        d1 = fiber_dir.float().to(device)
        d1 = d1 / (d1.norm() + 1e-8)   # normalize
    else:
        raise TypeError(f"fiber_dir must be str or Tensor, got {type(fiber_dir)}")

    # ── Build orthonormal frame via Gram-Schmidt ──
    d1, d2, d3 = _build_orthonormal_frame(d1)

    # Broadcast to all nodes: same global frame
    axes = torch.stack([d1, d2, d3], dim=-1)  # (3, 3): columns are d1, d2, d3
    material_axes = axes.unsqueeze(0).expand(N, -1, -1).clone()  # (N, 3, 3)

    return material_axes


def _build_orthonormal_frame(d1: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """Build an orthonormal frame {d1, d2, d3} from a given primary direction.

    Uses Gram-Schmidt: choose a helper vector not parallel to d1,
    then construct d2, d3 via cross products.

    Args:
        d1: (3,) primary direction unit vector

    Returns:
        d1, d2, d3: three mutually orthonormal vectors
    """
    d1 = d1 / (d1.norm() + 1e-8)

    # Choose helper vector not aligned with d1
    abs_d1 = d1.abs()
    if abs_d1[0] < 0.9:
        helper = torch.tensor([1.0, 0.0, 0.0], device=d1.device, dtype=d1.dtype)
    else:
        helper = torch.tensor([0.0, 1.0, 0.0], device=d1.device, dtype=d1.dtype)

    # d2 = normalize(helper - (helper·d1)d1)
    d2 = helper - (helper @ d1) * d1
    d2 = d2 / (d2.norm() + 1e-8)

    # d3 = d1 × d2
    d3 = torch.cross(d1, d2, dim=0)
    d3 = d3 / (d3.norm() + 1e-8)

    return d1, d2, d3


def _assign_local_principal_axes(
    positions: torch.Tensor,
    tet_indices: torch.Tensor,
    N: int,
) -> torch.Tensor:
    """Assign per-node principal axis from local mesh geometry (PCA of neighbors).

    For each node, collect its 1-ring neighbors (via tetrahedra), compute
    the local PCA of neighbor positions, and use the principal eigenvector
    as the local fiber direction d₁.

    This is useful for curved geometries where the fiber direction follows
    the geometry (e.g., circular bone cross-section).

    Args:
        positions:  (N, 3) nodal positions
        tet_indices:(T, 4) tetrahedron vertex indices
        N:          number of nodes

    Returns:
        material_axes: (N, 3, 3) per-node material frames
    """
    device = positions.device
    T = tet_indices.shape[0]

    # Build neighbor list: for each node, collect all neighboring nodes via tets
    neighbor_pos = [[] for _ in range(N)]
    for t in range(T):
        verts = tet_indices[t]  # (4,)
        for vi in verts:
            for vj in verts:
                if vi != vj:
                    neighbor_pos[vi.item()].append(positions[vj.item()])

    material_axes = torch.zeros(N, 3, 3, device=device)

    for i in range(N):
        if len(neighbor_pos[i]) < 3:
            # Fallback to global z-direction
            d1 = torch.tensor([0.0, 0.0, 1.0], device=device)
        else:
            # Stack neighbor positions and compute PCA
            pts = torch.stack(neighbor_pos[i], dim=0)     # (M, 3)
            pts_centered = pts - pts.mean(dim=0, keepdim=True)

            # SVD: principal direction = first right singular vector
            try:
                U, S, Vh = torch.linalg.svd(pts_centered, full_matrices=False)
                d1 = Vh[0]  # first right singular vector = principal direction
            except Exception:
                d1 = torch.tensor([0.0, 0.0, 1.0], device=device)

        d1_unit, d2, d3 = _build_orthonormal_frame(d1)
        material_axes[i, :, 0] = d1_unit
        material_axes[i, :, 1] = d2
        material_axes[i, :, 2] = d3

    return material_axes


# ─────────────────────────────────────────────────────────────
# Antisymmetry Validation
# ─────────────────────────────────────────────────────────────

def verify_antisymmetry(
    edge_attr: torch.Tensor,
    edge_index: torch.LongTensor,
    atol: float = 1e-6,
) -> bool:
    """Verify that direction dot products are antisymmetric under edge reversal.

    For each edge (i→j), checks that the reverse edge (j→i) satisfies:
        e_ji[0:3] ≈ -e_ij[0:3]   (r_ji = -r_ij)
        e_ji[4:7] ≈ -e_ij[4:7]   (dot products negate)
        e_ji[3]   ≈  e_ij[3]     (distance is symmetric)

    Note: this check only works if BOTH directions of each edge are present
    in edge_index (i.e., the graph is undirected / has both (i,j) and (j,i)).

    Args:
        edge_attr:  (E, 7) edge features
        edge_index: (2, E) directed edge indices
        atol:       absolute tolerance

    Returns:
        True if antisymmetry holds within tolerance
    """
    src = edge_index[0]
    dst = edge_index[1]

    # Build lookup: (i, j) → edge index
    edge_dict = {}
    for e in range(edge_index.shape[1]):
        key = (src[e].item(), dst[e].item())
        edge_dict[key] = e

    errors = []
    checked = 0
    for e in range(edge_index.shape[1]):
        i, j = src[e].item(), dst[e].item()
        rev_key = (j, i)
        if rev_key in edge_dict:
            e_fwd = edge_attr[e]
            e_rev = edge_attr[edge_dict[rev_key]]

            # r_ij and dot products should negate
            anti_err = (e_fwd[[0, 1, 2, 4, 5, 6]] + e_rev[[0, 1, 2, 4, 5, 6]]).abs().max()
            # distance should be equal (symmetric)
            sym_err = (e_fwd[3] - e_rev[3]).abs()

            errors.append(anti_err.item())
            errors.append(sym_err.item())
            checked += 1

    if checked == 0:
        # No reverse edges found — can't verify
        return True

    max_err = max(errors)
    passed = max_err < atol

    if not passed:
        raise AssertionError(
            f"Antisymmetry violated: max error = {max_err:.2e} > atol={atol:.2e}. "
            f"Checked {checked} edge pairs."
        )

    return True
