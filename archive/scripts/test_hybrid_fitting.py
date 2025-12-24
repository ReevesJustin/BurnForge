#!/usr/bin/env python3
"""
Test script for hybrid fitting approach: geometric form first, then polynomial correction.
"""

import pandas as pd
import numpy as np
from src.ballistics.fitting import fit_vivacity_polynomial, fit_vivacity_hybrid
from src.ballistics.props import (
    BallisticsConfig,
    PropellantProperties,
    BulletProperties,
)


def test_hybrid_fitting():
    """Test the hybrid fitting approach on sample data."""

    # Create sample load data (simulated)
    charges = np.linspace(20, 50, 10)  # grains
    # Simulate velocities with some noise
    velocities = 2500 + 15 * charges + np.random.normal(0, 10, len(charges))
    load_data = pd.DataFrame(
        {"charge_grains": charges, "mean_velocity_fps": velocities}
    )

    print("Sample load data:")
    print(load_data.head())
    print()

    # Create base config using database
    prop = PropellantProperties.from_database("Varget")
    bullet = BulletProperties.from_database("Copper Jacket over Lead")

    config = BallisticsConfig(
        bullet_mass_gr=130,
        charge_mass_gr=35,  # Will be overridden
        caliber_in=0.264,
        case_volume_gr_h2o=35,
        barrel_length_in=24,
        cartridge_overall_length_in=2.8,
        propellant=prop,
        bullet=bullet,
        temperature_f=70,
    )

    print("Testing geometric form fitting first...")
    fit_form = fit_vivacity_polynomial(
        load_data, config, use_form_function=True, verbose=False
    )
    print(f"Geometric form RMSE: {fit_form['rmse_velocity']:.2f} fps")
    print(f"Lambda_base: {fit_form['Lambda_base']:.4f}")
    print(f"Alpha: {fit_form.get('alpha', 0.0):.4f}")
    print()

    print("Testing polynomial fitting...")
    fit_poly = fit_vivacity_polynomial(
        load_data, config, use_form_function=False, verbose=False
    )
    print(f"Polynomial RMSE: {fit_poly['rmse_velocity']:.2f} fps")
    print(f"Lambda_base: {fit_poly['Lambda_base']:.4f}")
    print(f"Coeffs: {fit_poly['coeffs']}")
    print()

    print("Testing hybrid fitting (currently just geometric)...")
    fit_hybrid = fit_vivacity_hybrid(load_data, config, verbose=False)
    print(f"Hybrid RMSE: {fit_hybrid['rmse_velocity']:.2f} fps")
    print()

    print("Comparison:")
    print(".2f")
    print(".2f")
    print(".2f")


if __name__ == "__main__":
    test_hybrid_fitting()
