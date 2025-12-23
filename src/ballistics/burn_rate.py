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


def calc_vivacity(Z: float, Lambda_base: float,
                  coeffs: tuple[float, float, float, float],
                  T_prop_K: float = 294.0,
                  temp_sensitivity_sigma_per_K: float = 0.0) -> float:
    """Compute dynamic vivacity Λ(Z, T) with optional temperature sensitivity.

    Parameters
    ----------
    Z : float
        Burn fraction (0 ≤ Z ≤ 1)
    Lambda_base : float
        Base vivacity at reference temperature (s⁻¹ per PSI)
    coeffs : tuple
        (a, b, c, d) polynomial coefficients
    T_prop_K : float, optional
        Propellant temperature (K). Default: 294 K (70°F)
    temp_sensitivity_sigma_per_K : float, optional
        Temperature sensitivity coefficient (1/K). Default: 0.0 (no sensitivity)
        Typical range: [0.002, 0.008] /K

    Returns
    -------
    float
        Dynamic vivacity Λ(Z, T) in s⁻¹ per PSI

    Notes
    -----
    Temperature effect applied as exponential multiplier:
        Λ(T) = Λ_base × exp(σ × (T - T_ref))
    where T_ref = 294 K (70°F).

    This formulation naturally produces nonlinear velocity-temperature response:
    - Early burnout (high charge) → reduced temperature sensitivity
    - Late burnout (low charge) → increased temperature sensitivity
    matching real-world chronograph data patterns.
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

    a, b, c, d = coeffs

    # Evaluate polynomial: Λ(Z, T) = Λ_base(T) × (a + b×Z + c×Z² + d×Z³)
    poly_value = a + b * Z + c * Z**2 + d * Z**3

    return Lambda_temp_corrected * poly_value


def validate_vivacity_positive(Lambda_base: float,
                                coeffs: tuple[float, float, float, float],
                                T_prop_K: float = 294.0,
                                temp_sensitivity_sigma_per_K: float = 0.0,
                                n_points: int = 100) -> bool:
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
        viv = calc_vivacity(Z, Lambda_base, coeffs, T_prop_K, temp_sensitivity_sigma_per_K)
        if viv <= 0:
            return False

    return True
