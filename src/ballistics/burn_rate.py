"""Vivacity polynomial evaluation and validation.

Temperature Sensitivity Implementation
--------------------------------------
The burn rate exhibits temperature dependence following Arrhenius-type
activation energy for propellant deflagration. The temperature multiplier
is applied to the base vivacity before polynomial evaluation:

    Λ(Z, T) = Λ_base × exp(σ × (T_prop - T_ref)) × [a + b×Z + c×Z² + d×Z³]

where:
    σ = temp_sensitivity_sigma_per_K (typically 0.002-0.008 /K)
    T_ref = 294 K (70°F, standard reference temperature)
    T_prop = propellant temperature (K)

Physical Interpretation:
- Higher temperature → faster initial burn → earlier burnout → lower net sensitivity
- Lower temperature → slower initial burn → later burnout → higher net sensitivity
- This nonlinear coupling naturally reproduces experimental observations that
  loads with early burnout (high charge) show lower temperature sensitivity
  than loads with late burnout (low charge).

References: NATO STANAG 4115, Vihtavuori temperature sensitivity data,
            Arrhenius deflagration kinetics (Kubota, 2002)
"""

import math
import numpy as np


def form_function(Z: float, geometry: str) -> float:
    """Compute geometric form function π(Z) for different grain types.

    Parameters
    ----------
    Z : float
        Burn fraction (0 ≤ Z ≤ 1)
    geometry : str
        Grain geometry type: 'spherical', 'degressive', 'single-perf', 'neutral', '7-perf', 'progressive', 'solid_extruded', 'tubular_progressive'

    Returns
    -------
    float
        Form function value π(Z)
    """
    if geometry in ("spherical", "degressive"):
        # Spherical/degressive: π(Z) ≈ (1-Z)^{2/3}
        return (1 - Z) ** (2 / 3) if Z < 1 else 0.0
    elif geometry in ("single-perf", "tubular_progressive", "single-perforated"):
        # Single-perf tubular: Slightly progressive, internal surface grows faster
        # Approximation: π(Z) = 1 + 0.3*Z (slight progression)
        return 1 + 0.3 * Z if Z < 0.9 else 0.0  # Sliver at Z=0.9
    elif geometry in ("neutral", "solid_extruded"):
        # Neutral cylinder or solid extruded: π(Z) = 1 - Z
        return 1 - Z if Z < 1 else 0.0
    elif geometry in ("7-perf", "progressive"):
        # Progressive 7-perf: Standard quadratic 1 + λZ + μZ² (up to slivering point)
        # Typical values: λ ≈ 1.5, μ ≈ -0.5 for 7-perf, but simplified to 1 + Z for now
        # For simplicity, use 1 + Z (linear progressive)
        return 1 + Z if Z < 0.9 else 0.0  # Sliver at Z=0.9
    else:
        # Default neutral
        return 1 - Z if Z < 1 else 0.0


def calc_vivacity(
    Z: float,
    Lambda_base: float,
    coeffs: tuple[float, float, float, float],
    T_prop_K: float = 294.0,
    temp_sensitivity_sigma_per_K: float = 0.0,
    use_form_function: bool = False,
    geometry: str = "spherical",
    p_psi: float | None = None,
    alpha: float = 0.0,
    use_hybrid: bool = False,
    Lambda_base_hybrid: float = 0.0,
    coeffs_hybrid: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0),
) -> float:
    """Compute dynamic vivacity Λ(Z, T) with optional temperature sensitivity and form function.

    Parameters
    ----------
    Z : float
        Burn fraction (0 ≤ Z ≤ 1)
    Lambda_base : float
        Base vivacity at reference temperature (s⁻¹ per PSI)
    coeffs : tuple
        (a, b, c, d) polynomial coefficients for Λ(p) or (α, β, γ, Λ_linear) for form function
    T_prop_K : float, optional
        Propellant temperature (K). Default: 294 K (70°F)
    temp_sensitivity_sigma_per_K : float, optional
        Temperature sensitivity coefficient (1/K). Default: 0.0
        Typical range: [0.002, 0.008] /K
    use_form_function : bool, optional
        Use geometric form function instead of pure polynomial. Default: False
    geometry : str, optional
        Grain geometry type if use_form_function=True. Default: 'spherical'
    p_psi : float, optional
        Current chamber pressure (psi) for pressure-dependent correction. Default: None
    alpha : float, optional
        Pressure-dependent correction coefficient (s⁻¹/psi²). Default: 0.0
    use_hybrid : bool, optional
        Use hybrid mode combining form function and polynomial. Default: False
    Lambda_base_hybrid : float, optional
        Base vivacity for hybrid polynomial component. Default: 0.0
    coeffs_hybrid : tuple, optional
        (a, b, c, d) polynomial coefficients for hybrid component. Default: (0,0,0,0)

    Returns
    -------
    float
        Dynamic vivacity Λ(Z, T) in s⁻¹ per PSI

    Notes
    -----
    Temperature effect applied as exponential multiplier:
        Λ(T) = Λ_base × exp(σ × (T - T_ref))
    where T_ref = 294 K (70°F).

    Form function mode: Λ(Z, p) = (Λ_base(T) + α × p) × π(Z)
    where π(Z) is the geometric form function based on grain geometry.

    Hybrid mode: Λ(Z, p) = [(Λ_base(T) + α × p) × π(Z)] + [Λ_base_hybrid(T) × (a + b×Z + c×Z² + d×Z³)]
    Combines geometric form function baseline with polynomial correction.
    """
    # Clamp Z to [0, 1]
    Z = max(0.0, min(1.0, Z))

    # After burnout, vivacity is zero
    if Z >= 1.0:
        return 0.0

    # Temperature sensitivity multiplier (exponential Arrhenius form)
    # Reference temperature: 294 K (70°F)
    T_ref = 294.0  # K
    if abs(temp_sensitivity_sigma_per_K) > 1e-9:  # Apply if non-zero
        temp_multiplier = math.exp(temp_sensitivity_sigma_per_K * (T_prop_K - T_ref))
    else:
        temp_multiplier = 1.0

    # Apply temperature correction to base vivacity
    Lambda_temp_corrected = Lambda_base * temp_multiplier

    if use_hybrid:
        # Hybrid mode: geometric form + polynomial correction
        pi_z = form_function(Z, geometry)
        if p_psi is not None and alpha > 0:
            Lambda_pressure_corrected = Lambda_temp_corrected + alpha * p_psi
        else:
            Lambda_pressure_corrected = Lambda_temp_corrected
        form_contribution = Lambda_pressure_corrected * pi_z

        # Polynomial correction component
        Lambda_temp_corrected_hybrid = Lambda_base_hybrid * temp_multiplier
        a_h, b_h, c_h, d_h = coeffs_hybrid
        poly_value_hybrid = a_h + b_h * Z + c_h * Z**2 + d_h * Z**3
        poly_contribution = Lambda_temp_corrected_hybrid * poly_value_hybrid

        return form_contribution + poly_contribution

    elif use_form_function:
        # Geometric form function with pressure-dependent correction
        pi_z = form_function(Z, geometry)
        if p_psi is not None and alpha > 0:
            Lambda_pressure_corrected = Lambda_temp_corrected + alpha * p_psi
        else:
            Lambda_pressure_corrected = Lambda_temp_corrected
        return Lambda_pressure_corrected * pi_z
    else:
        # Original polynomial: Λ(Z, T) = Λ_base(T) × (a + b×Z + c×Z² + d×Z³)
        a, b, c, d = coeffs
        poly_value = a + b * Z + c * Z**2 + d * Z**3
        return Lambda_temp_corrected * poly_value


def validate_vivacity_positive(
    Lambda_base: float,
    coeffs: tuple[float, float, float, float],
    T_prop_K: float = 294.0,
    temp_sensitivity_sigma_per_K: float = 0.0,
    n_points: int = 100,
    use_form_function: bool = False,
    geometry: str = "spherical",
    alpha: float = 0.0,
    use_hybrid: bool = False,
    Lambda_base_hybrid: float = 0.0,
    coeffs_hybrid: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0),
) -> bool:
    """Check that Λ(Z, T) > 0 for all Z ∈ [0, 1] at given temperature.

    Parameters
    ----------
    Lambda_base : float
        Base vivacity at reference temperature
    coeffs : tuple
        (a, b, c, d) polynomial coefficients
    T_prop_K : float, optional
        Propellant temperature (K). Default: 294 K
    temp_sensitivity_sigma_per_K : float, optional
        Temperature sensitivity coefficient (1/K). Default: 0.0
    n_points : int
        Number of points to sample

    Returns
    -------
    bool
        True if vivacity is positive throughout burn at the given temperature
    """
    Z_values = np.linspace(0, 0.99, n_points)  # Stop just before Z=1

    for Z in Z_values:
        viv = calc_vivacity(
            Z,
            Lambda_base,
            coeffs,
            T_prop_K,
            temp_sensitivity_sigma_per_K,
            use_form_function,
            geometry,
            None,
            alpha,
            use_hybrid,
            Lambda_base_hybrid,
            coeffs_hybrid,
        )
        if viv <= 0:
            return False

    return True
