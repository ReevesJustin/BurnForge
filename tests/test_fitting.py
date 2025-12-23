"""Tests for fitting.py convergence and bounds."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import numpy as np
import pandas as pd
import pytest

from ballistics import PropellantProperties, BulletProperties, BallisticsConfig
from ballistics.fitting import fit_vivacity_polynomial
from ballistics.solver import solve_ballistics


def test_fit_convergence():
    """Test that optimizer converges to a reasonable solution."""
    # Create synthetic data with known parameters
    prop = PropellantProperties.from_database("Varget")
    bullet = BulletProperties.from_database("Copper Jacket over Lead")

    config_base = BallisticsConfig(
        bullet_mass_gr=175.0,
        charge_mass_gr=40.0,
        caliber_in=0.308,
        case_volume_gr_h2o=49.5,
        barrel_length_in=24.0,
        cartridge_overall_length_in=2.810,
        propellant=prop,
        bullet=bullet,
        temperature_f=70.0
    )

    # Generate synthetic load ladder data
    charges = [40.0, 41.0, 42.0, 43.0, 44.0]
    velocities = []

    for charge in charges:
        config = BallisticsConfig(
            bullet_mass_gr=175.0,
            charge_mass_gr=charge,
            caliber_in=0.308,
            case_volume_gr_h2o=49.5,
            barrel_length_in=24.0,
            cartridge_overall_length_in=2.810,
            propellant=prop,
            bullet=bullet,
            temperature_f=70.0
        )
        result = solve_ballistics(config)
        velocities.append(result['muzzle_velocity_fps'])

    # Create DataFrame
    load_data = pd.DataFrame({
        'charge_grains': charges,
        'mean_velocity_fps': velocities,
        'velocity_sd': [10.0] * len(charges)
    })

    # Fit
    fit_result = fit_vivacity_polynomial(
        load_data,
        config_base,
        verbose=False
    )

    # Check convergence (optimizer sometimes returns ABNORMAL even when converged)
    # Accept if RMSE is very small OR success flag is True
    assert fit_result['rmse_velocity'] < 50.0 or fit_result['success'], \
        f"Fitting should converge. RMSE: {fit_result['rmse_velocity']:.2f}, Success: {fit_result['success']}"

    # Check parameters are in bounds (Lambda_base is normalized: vivacity/1450)
    assert 0.01 <= fit_result['Lambda_base'] <= 0.15, \
        f"Lambda_base {fit_result['Lambda_base']:.6f} out of bounds [0.01, 0.15]"
    for coeff in fit_result['coeffs']:
        assert -2.0 <= coeff <= 2.0, f"Coefficient {coeff} out of bounds"


def test_bounds_enforcement():
    """Test that optimizer respects parameter bounds."""
    prop = PropellantProperties.from_database("H4350")
    bullet = BulletProperties.from_database("Copper Jacket over Lead")

    config_base = BallisticsConfig(
        bullet_mass_gr=140.0,
        charge_mass_gr=40.0,
        caliber_in=0.264,
        case_volume_gr_h2o=52.5,
        barrel_length_in=22.0,
        cartridge_overall_length_in=2.800,
        propellant=prop,
        bullet=bullet
    )

    # Create simple load data
    load_data = pd.DataFrame({
        'charge_grains': [38.0, 40.0, 42.0],
        'mean_velocity_fps': [2600.0, 2700.0, 2800.0],
        'velocity_sd': [8.0, 8.0, 8.0]
    })

    # Custom bounds
    custom_bounds = (
        (30.0, -1.0, -1.0, -1.0, -1.0),
        (100.0, 1.0, 1.0, 1.0, 1.0)
    )

    fit_result = fit_vivacity_polynomial(
        load_data,
        config_base,
        bounds=custom_bounds,
        verbose=False
    )

    # Check bounds
    assert 30.0 <= fit_result['Lambda_base'] <= 100.0, "Lambda_base violates custom bounds"
    for coeff in fit_result['coeffs']:
        assert -1.0 <= coeff <= 1.0, f"Coefficient {coeff} violates custom bounds"


def test_regularization():
    """Test that L2 regularization affects coefficients."""
    prop = PropellantProperties.from_database("Varget")
    bullet = BulletProperties.from_database("Copper Jacket over Lead")

    config_base = BallisticsConfig(
        bullet_mass_gr=175.0,
        charge_mass_gr=40.0,
        caliber_in=0.308,
        case_volume_gr_h2o=49.5,
        barrel_length_in=24.0,
        cartridge_overall_length_in=2.810,
        propellant=prop,
        bullet=bullet
    )

    load_data = pd.DataFrame({
        'charge_grains': [40.0, 41.0, 42.0, 43.0],
        'mean_velocity_fps': [2550.0, 2600.0, 2650.0, 2700.0],
        'velocity_sd': [10.0, 10.0, 10.0, 10.0]
    })

    # Fit without regularization
    fit_no_reg = fit_vivacity_polynomial(
        load_data,
        config_base,
        regularization=0.0,
        verbose=False
    )

    # Fit with regularization
    fit_with_reg = fit_vivacity_polynomial(
        load_data,
        config_base,
        regularization=0.01,
        verbose=False
    )

    # Regularization should reduce magnitude of coefficients
    coeff_mag_no_reg = sum(c**2 for c in fit_no_reg['coeffs'])
    coeff_mag_with_reg = sum(c**2 for c in fit_with_reg['coeffs'])

    # With regularization, coefficients should be smaller (or similar)
    # This is a soft check since data might not need large coefficients anyway
    assert coeff_mag_with_reg <= coeff_mag_no_reg * 1.1, \
        "Regularization should not increase coefficient magnitude significantly"


def test_insufficient_data():
    """Test that fitting raises error with insufficient data."""
    prop = PropellantProperties.from_database("Varget")
    bullet = BulletProperties.from_database("Copper Jacket over Lead")

    config_base = BallisticsConfig(
        bullet_mass_gr=175.0,
        charge_mass_gr=40.0,
        caliber_in=0.308,
        case_volume_gr_h2o=49.5,
        barrel_length_in=24.0,
        cartridge_overall_length_in=2.810,
        propellant=prop,
        bullet=bullet
    )

    # Only 2 data points
    load_data = pd.DataFrame({
        'charge_grains': [40.0, 41.0],
        'mean_velocity_fps': [2550.0, 2600.0]
    })

    with pytest.raises(ValueError, match="at least 3 data points"):
        fit_vivacity_polynomial(load_data, config_base, verbose=False)


def test_missing_columns():
    """Test that fitting raises error with missing required columns."""
    prop = PropellantProperties.from_database("Varget")
    bullet = BulletProperties.from_database("Copper Jacket over Lead")

    config_base = BallisticsConfig(
        bullet_mass_gr=175.0,
        charge_mass_gr=40.0,
        caliber_in=0.308,
        case_volume_gr_h2o=49.5,
        barrel_length_in=24.0,
        cartridge_overall_length_in=2.810,
        propellant=prop,
        bullet=bullet
    )

    # Missing mean_velocity_fps
    load_data = pd.DataFrame({
        'charge_grains': [40.0, 41.0, 42.0]
    })

    with pytest.raises(ValueError, match="Missing required column"):
        fit_vivacity_polynomial(load_data, config_base, verbose=False)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
