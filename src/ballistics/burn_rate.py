"""Vivacity polynomial evaluation and validation."""

import numpy as np


def calc_vivacity(Z: float, Lambda_base: float,
                  coeffs: tuple[float, float, float, float]) -> float:
    """Compute dynamic vivacity Λ(Z) in s⁻¹ per 100 bar.

    Parameters
    ----------
    Z : float
        Burn fraction (0 ≤ Z ≤ 1)
    Lambda_base : float
        Base vivacity in s⁻¹ per 100 bar
    coeffs : tuple
        (a, b, c, d) polynomial coefficients

    Returns
    -------
    float
        Dynamic vivacity Λ(Z)
    """
    # Clamp Z to [0, 1]
    Z = max(0.0, min(1.0, Z))

    # After burnout, vivacity is zero
    if Z >= 1.0:
        return 0.0

    a, b, c, d = coeffs

    # Evaluate polynomial: Λ(Z) = Λ_base * (a + b*Z + c*Z² + d*Z³)
    poly_value = a + b * Z + c * Z**2 + d * Z**3

    return Lambda_base * poly_value


def validate_vivacity_positive(Lambda_base: float,
                                coeffs: tuple[float, float, float, float],
                                n_points: int = 100) -> bool:
    """Check that Λ(Z) > 0 for all Z ∈ [0, 1].

    Parameters
    ----------
    Lambda_base : float
        Base vivacity
    coeffs : tuple
        (a, b, c, d) polynomial coefficients
    n_points : int
        Number of points to sample

    Returns
    -------
    bool
        True if vivacity is positive throughout burn
    """
    Z_values = np.linspace(0, 0.99, n_points)  # Stop just before Z=1

    for Z in Z_values:
        viv = calc_vivacity(Z, Lambda_base, coeffs)
        if viv <= 0:
            return False

    return True
