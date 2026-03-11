"""
bone_material_params.py — Material parameters for bone tissues.

Provides literature-validated constitutive parameters for the TI hyperelastic model:

    Ψ_TI = C₁(Ī₁-3) + D₁(J-1)² + (k₁/2k₂)[exp(k₂⟨Ī₄-1⟩²)-1] + Ψ_barrier(J)

Parameter sources:
    - Cortical bone:     Reilly & Burstein (1975) J Biomech 8:393–405
    - Cancellous bone:   Morgan & Keaveny (2001) J Biomech 34:569–577
    - Vertebral body:    Kopperdahl & Keaveny (1998) J Biomech 31:601–608

Conversion from engineering constants:
    The mapping from engineering constants (E_L, E_T, ν_LT, G_LT) to TI
    hyperelastic parameters (C1, D1, k1, k2) follows the small-strain
    linearization of the hyperelastic model. For bone (small strains in vivo),
    this is a valid approximation.

    C₁ ≈ G_T/2          (half transverse shear modulus)
    D₁ ≈ K/2            (half bulk modulus, K = E_T / (3(1-2ν)))
    k₁ ≈ E_L - E_T      (fiber stiffness excess — longitudinal vs transverse)
    k₂ = 10 (cortical)  (exponential nonlinearity, calibrated to bone toe region)

    Reference: Weiss JA et al. (1996) CMAME 135:107–128 (TI hyperelastic FEM).

Usage:
    params = cortical_bone_params()
    # params = {'C1': ..., 'D1': ..., 'k1': ..., 'k2': ..., 'rho': ..., 'fiber_dir': ...}
    fiber_dir = torch.tensor(params['fiber_dir'])
    loss, info = ti_physics_loss(pred_pos, rest_pos, tet_idx, params, f_ext)

Expert Review:
    - 材料力学专家: literature parameter validation, conversion formulas
    - 骨生物力学专家: Reilly & Burstein 1975, density-dependent cancellous bone
    - 计算力学专家: hyperelastic parameter mapping
"""

import numpy as np
from typing import Dict, Tuple, Optional


# ─────────────────────────────────────────────────────────────
# Engineering Constants → TI Hyperelastic Parameters
# ─────────────────────────────────────────────────────────────

def engineering_to_ti_params(
    E_L: float,
    E_T: float,
    nu_LT: float,
    G_LT: float,
    k2: float = 10.0,
    density: float = 1900.0,
) -> Dict[str, float]:
    """Convert engineering constants to TI hyperelastic parameters.

    Small-strain linearization of TI hyperelastic model:

        C₁ = G_T / 2         where G_T = E_T / (2(1+ν_TT)) ≈ G_LT
        D₁ = K / 2           where K = E_T / (3(1-2ν_TT)) ≈ bulk modulus
        k₁ = max(0, E_L - E_T)   fiber stiffness excess
        k₂ = user-specified       nonlinearity (literature: 10 for bone)

    Note: This linearization is valid for strains < 2% (typical in vivo bone strains).
    For surgical simulation (strains up to 5–10%), the full nonlinear form is used.

    Args:
        E_L:     longitudinal (fiber) Young's modulus (Pa)
        E_T:     transverse Young's modulus (Pa)
        nu_LT:   longitudinal-transverse Poisson ratio
        G_LT:    longitudinal shear modulus (Pa)
        k2:      fiber nonlinearity (dimensionless, default 10.0 for cortical bone)
        density: mass density (kg/m³)

    Returns:
        dict with C1, D1, k1, k2, rho (Pa units for moduli)
    """
    # Transverse Poisson ratio (TI constraint): ν_TT ≈ ν_LT for bone
    # More precisely: ν_TT = E_T/(2G_T) - 1, but we use ν_LT as approximation
    nu_TT = nu_LT

    # Transverse shear modulus
    G_T = E_T / (2.0 * (1.0 + nu_TT))

    # Bulk modulus (transverse isotropy approximation)
    K = E_T / (3.0 * (1.0 - 2.0 * nu_TT))

    # TI hyperelastic parameters
    C1 = G_T / 2.0               # Pa
    D1 = K / 2.0                  # Pa
    k1 = max(0.0, E_L - E_T)     # Pa (fiber reinforcement excess)

    return {
        "C1": C1,
        "D1": D1,
        "k1": k1,
        "k2": k2,
        "rho": density,
    }


# ─────────────────────────────────────────────────────────────
# Cortical Bone (Reilly & Burstein 1975)
# ─────────────────────────────────────────────────────────────

def cortical_bone_params(fiber_axis: str = 'z') -> Dict:
    """Cortical bone TI hyperelastic parameters.

    Source: Reilly DT, Burstein AH (1975) The elastic and ultimate properties
            of compact bone tissue. J Biomech 8:393–405.
            Table 1: Human femoral cortical bone (wet specimens, 37°C)

    Engineering constants (human femoral cortical bone):
        E_L  = 17.0 GPa   (longitudinal, along bone axis)
        E_T  = 11.5 GPa   (transverse)
        ν_LT = 0.29        (longitudinal-transverse Poisson)
        ν_TT = 0.51        (transverse-transverse Poisson; approximated here)
        G_LT = 3.28 GPa   (longitudinal shear)
        ρ    = 1900 kg/m³  (cortical bone density)

    Note: We use simplified TI (5-constant) vs full orthotropic (9-constant).
    The cortical bone has approximately transverse isotropy (E_R ≈ E_C),
    making TI a valid model for most loading scenarios except detailed
    cement-line microstructure modeling.

    Fiber direction convention: along bone shaft axis (longitudinal, L).
    Default: z-axis (z = superior-inferior / longitudinal bone direction).

    Additional reference:
        Rho JY et al. (1998) Mechanical properties and the hierarchical
        structure of bone. Med Eng Phys 20:92–102. (confirms E_L ≈ 17–22 GPa)

    Args:
        fiber_axis: 'x', 'y', or 'z' (bone shaft direction in model coordinates)

    Returns:
        dict with C1, D1, k1, k2, rho, fiber_dir [1, 3] list
    """
    # Reilly & Burstein (1975) femoral cortical bone
    E_L  = 17.0e9    # Pa, longitudinal (along bone axis)
    E_T  = 11.5e9    # Pa, transverse
    nu_LT = 0.29     # longitudinal-transverse Poisson
    G_LT = 3.28e9    # Pa, longitudinal shear
    rho  = 1900.0    # kg/m³

    params = engineering_to_ti_params(E_L, E_T, nu_LT, G_LT, k2=10.0, density=rho)

    # Fiber direction
    fiber_map = {
        'x': [1.0, 0.0, 0.0],
        'y': [0.0, 1.0, 0.0],
        'z': [0.0, 0.0, 1.0],
    }
    if fiber_axis not in fiber_map:
        raise ValueError(f"fiber_axis must be 'x', 'y', or 'z', got '{fiber_axis}'")
    params["fiber_dir"] = fiber_map[fiber_axis]

    # Literature metadata
    params["_source"] = "Reilly & Burstein (1975) J Biomech 8:393-405"
    params["_tissue"] = "cortical_bone"
    params["_E_L_GPa"] = E_L / 1e9
    params["_E_T_GPa"] = E_T / 1e9
    params["_nu_LT"] = nu_LT
    params["_G_LT_GPa"] = G_LT / 1e9

    return params


# ─────────────────────────────────────────────────────────────
# Cancellous Bone (Morgan & Keaveny 2001)
# ─────────────────────────────────────────────────────────────

def cancellous_bone_params(
    BV_TV: float = 0.25,
    fiber_axis: str = 'z',
) -> Dict:
    """Cancellous (trabecular) bone TI parameters with density dependence.

    Source: Morgan EF, Keaveny TM (2001) Dependence of yield strain of
            human trabecular bone on anatomic site. J Biomech 34:569–577.

    Secondary source:
        Kopperdahl DL, Keaveny TM (1998) Yield strain behavior of trabecular
        bone. J Biomech 31:601–608.

    Density-dependent modulus (Morgan & Keaveny 2001, Eq. 2):
        E_apparent = 8920 × ρ_app^1.83   (Pa, with ρ_app in g/cm³)

    where:
        ρ_apparent = BV/TV × ρ_tissue    (apparent density)
        ρ_tissue   ≈ 1.79 g/cm³          (tissue density of bone matrix)

    Cancellous bone is approximately transversely isotropic along the
    trabecular grain direction (typically superior-inferior in vertebrae,
    longitudinal in long bones).

    Anisotropy ratio: E_L/E_T ≈ 1.5–2.0 for trabecular bone
        (less anisotropic than cortical bone E_L/E_T ≈ 1.5)

    Args:
        BV_TV:      Bone Volume / Total Volume fraction (0.05–0.40 typical)
                    0.05 = very osteoporotic; 0.35 = dense young trabecular
        fiber_axis: 'x', 'y', or 'z' (trabecular grain direction)

    Returns:
        dict with C1, D1, k1, k2, rho, fiber_dir
    """
    # Validate BV/TV range
    if not (0.03 <= BV_TV <= 0.50):
        raise ValueError(
            f"BV/TV = {BV_TV:.2f} outside typical range [0.03, 0.50]. "
            "Clinical range: 0.05 (osteoporotic) to 0.40 (young dense)."
        )

    # Apparent density (g/cm³ = 1000 kg/m³)
    rho_tissue = 1.79   # g/cm³ (bone matrix tissue density)
    rho_apparent = BV_TV * rho_tissue  # g/cm³

    # Density-dependent apparent modulus (Morgan & Keaveny 2001)
    # E_apparent = 8920 × ρ^1.83  (Pa), ρ in g/cm³
    # Coefficient from regression of human vertebral trabecular bone
    E_apparent = 8920.0 * (rho_apparent ** 1.83) * 1e6  # convert MPa → Pa
    # Note: original equation gives E in MPa (Morgan&Keaveny 2001, Fig. 3)
    # Actually: E in MPa = 8920 * rho^1.83 when rho in g/cm³
    # → For BV/TV=0.25: ρ=0.45 g/cm³, E=8920*0.45^1.83 ≈ 2188 MPa = 2.19 GPa

    # Transverse modulus: ≈ 60% of apparent (longitudinal) modulus
    E_L = E_apparent           # longitudinal (trabecular grain direction)
    E_T = 0.60 * E_apparent    # transverse

    # Cancellous bone Poisson ratio and shear modulus
    nu_LT = 0.30               # Kopperdahl & Keaveny 1998
    G_LT  = E_L / (2.0 * (1.0 + nu_LT) * 1.5)  # empirical: ≈ E/3.9

    # Mass density (kg/m³)
    rho_kgm3 = rho_apparent * 1000.0  # g/cm³ → kg/m³

    params = engineering_to_ti_params(E_L, E_T, nu_LT, G_LT, k2=5.0, density=rho_kgm3)

    # Fiber direction
    fiber_map = {
        'x': [1.0, 0.0, 0.0],
        'y': [0.0, 1.0, 0.0],
        'z': [0.0, 0.0, 1.0],
    }
    params["fiber_dir"] = fiber_map[fiber_axis]

    # Metadata
    params["_source"] = "Morgan & Keaveny (2001) J Biomech 34:569-577"
    params["_tissue"] = "cancellous_bone"
    params["_BV_TV"] = BV_TV
    params["_rho_apparent_gcm3"] = rho_apparent
    params["_E_apparent_GPa"] = E_apparent / 1e9

    return params


# ─────────────────────────────────────────────────────────────
# Vertebral Body (Kopperdahl & Keaveny 1998)
# ─────────────────────────────────────────────────────────────

def vertebral_body_params(fiber_axis: str = 'z') -> Dict:
    """Vertebral body (mixed cortical shell + cancellous core) parameters.

    Source: Kopperdahl DL, Keaveny TM (1998) Yield strain behavior of
            trabecular bone. J Biomech 31:601–608.

    The vertebral body is modeled as trabecular bone (BV/TV ≈ 0.10–0.15)
    with a thin cortical shell (not modeled separately here).

    Typical values for lumbar vertebral trabecular bone:
        E_L  ≈ 340 MPa   (superior-inferior, compressive loading direction)
        E_T  ≈ 170 MPa   (anterior-posterior / medial-lateral)
        ν_LT ≈ 0.25
        G_LT ≈ 105 MPa

    These are for average adult lumbar spine (BV/TV ≈ 0.12).

    Additional reference:
        Pollintine P et al. (2004) Neural arch load-bearing in old and
        degenerated spines. J Biomech 37:197–204.

    Args:
        fiber_axis: 'x', 'y', or 'z' (superior-inferior axis in model)

    Returns:
        dict with C1, D1, k1, k2, rho, fiber_dir
    """
    # Kopperdahl & Keaveny (1998) lumbar vertebral trabecular bone
    E_L  = 340e6    # Pa, superior-inferior (compressive loading direction)
    E_T  = 170e6    # Pa, transverse
    nu_LT = 0.25    # Poisson ratio (Kopperdahl & Keaveny 1998)
    G_LT = 105e6    # Pa, shear modulus
    rho  = 350.0    # kg/m³ (BV/TV ≈ 0.12 → ρ_app ≈ 0.21 g/cm³ × 1790 → ~376 kg/m³)

    params = engineering_to_ti_params(E_L, E_T, nu_LT, G_LT, k2=5.0, density=rho)

    # Fiber direction
    fiber_map = {
        'x': [1.0, 0.0, 0.0],
        'y': [0.0, 1.0, 0.0],
        'z': [0.0, 0.0, 1.0],
    }
    params["fiber_dir"] = fiber_map[fiber_axis]

    # Metadata
    params["_source"] = "Kopperdahl & Keaveny (1998) J Biomech 31:601-608"
    params["_tissue"] = "vertebral_body"
    params["_E_L_MPa"] = E_L / 1e6
    params["_E_T_MPa"] = E_T / 1e6
    params["_nu_LT"] = nu_LT

    return params


# ─────────────────────────────────────────────────────────────
# Summary / Parameter Comparison
# ─────────────────────────────────────────────────────────────

def print_bone_params_summary() -> None:
    """Print a summary table of all bone material parameters."""
    print("\n{'='*72}")
    print("Bone Material Parameters — TI Hyperelastic Model")
    print("=" * 72)
    print(f"{'Tissue':<20} {'C1 (MPa)':>10} {'D1 (MPa)':>10} {'k1 (GPa)':>10} {'k2':>6} {'ρ (kg/m³)':>10}")
    print("-" * 72)

    tissues = [
        ("Cortical bone", cortical_bone_params()),
        ("Cancellous (BV/TV=0.25)", cancellous_bone_params(BV_TV=0.25)),
        ("Cancellous (BV/TV=0.10)", cancellous_bone_params(BV_TV=0.10)),
        ("Vertebral body", vertebral_body_params()),
    ]

    for name, p in tissues:
        print(
            f"{name:<20} {p['C1']/1e6:>10.2f} {p['D1']/1e6:>10.2f} "
            f"{p['k1']/1e9:>10.3f} {p['k2']:>6.1f} {p['rho']:>10.0f}"
        )

    print("=" * 72)
    print("C1: matrix shear stiffness | D1: volumetric stiffness")
    print("k1: fiber stiffness excess | k2: fiber nonlinearity")
    print("Sources: Reilly&Burstein 1975, Morgan&Keaveny 2001, Kopperdahl&Keaveny 1998")


if __name__ == "__main__":
    print_bone_params_summary()
