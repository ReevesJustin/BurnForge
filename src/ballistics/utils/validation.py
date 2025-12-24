"""Validation utilities for ballistics calculations."""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
from ..core.props import BallisticsConfig


def validate_config(config: BallisticsConfig) -> List[str]:
    """Validate a ballistics configuration for physical consistency.

    Parameters
    ----------
    config : BallisticsConfig
        Configuration to validate

    Returns
    -------
    List[str]
        List of validation warnings/errors (empty if all checks pass)
    """
    warnings = []

    # Check charge weight
    if config.charge_mass_gr <= 0:
        warnings.append(f"Charge mass must be positive, got {config.charge_mass_gr} gr")
    elif config.max_charge_gr and config.charge_mass_gr > config.max_charge_gr:
        warnings.append(
            f"Charge mass {config.charge_mass_gr} gr exceeds maximum {config.max_charge_gr} gr"
        )

    # Check barrel length
    if config.barrel_length_in <= 0:
        warnings.append(
            f"Barrel length must be positive, got {config.barrel_length_in} in"
        )

    # Check caliber
    if config.caliber_in <= 0:
        warnings.append(f"Caliber must be positive, got {config.caliber_in} in")

    # Check case volume
    if config.case_volume_gr_h2o <= 0:
        warnings.append(
            f"Case volume must be positive, got {config.case_volume_gr_h2o} gr H2O"
        )

    # Check propellant properties
    if config.propellant.Lambda_base <= 0:
        warnings.append(
            f"Base vivacity must be positive, got {config.propellant.Lambda_base}"
        )

    # Check temperature
    if config.temperature_f < -100 or config.temperature_f > 200:
        warnings.append(f"Temperature {config.temperature_f}°F seems unreasonable")

    # Check heat transfer coefficient
    if config.heat_loss_model == "convective" and config.h_base <= 0:
        warnings.append(
            f"Heat transfer coefficient must be positive, got {config.h_base}"
        )

    # Check bore friction
    if config.bore_friction_psi < 0:
        warnings.append(
            f"Bore friction cannot be negative, got {config.bore_friction_psi} psi"
        )

    return warnings


def validate_fit_results(
    fit_results: Dict[str, Any], load_data: Optional[pd.DataFrame] = None
) -> List[str]:
    """Validate fitting results for physical consistency and quality.

    Parameters
    ----------
    fit_results : Dict[str, Any]
        Results from fitting function
    load_data : pd.DataFrame, optional
        Original load data for additional validation

    Returns
    -------
    List[str]
        List of validation warnings (empty if all checks pass)
    """
    warnings = []

    # Check RMSE is reasonable
    rmse = fit_results.get("rmse_velocity", float("inf"))
    if rmse > 100:  # fps
        warnings.append(f"RMSE {rmse:.1f} fps is very high - check data quality")

    # Check Lambda_base is in reasonable range
    lambda_base = fit_results.get("Lambda_base", 0)
    if lambda_base <= 0:
        warnings.append("Lambda_base must be positive")
    elif lambda_base > 0.5:
        warnings.append(f"Lambda_base {lambda_base:.4f} seems unusually high")

    # Check polynomial coefficients are reasonable
    coeffs = fit_results.get("coeffs", [])
    if len(coeffs) >= 1 and abs(coeffs[0]) > 5:  # First coefficient
        warnings.append(f"Polynomial coefficient a0 = {coeffs[0]:.3f} seems large")

    # Check temperature sensitivity is reasonable
    temp_sens = fit_results.get("temp_sensitivity_sigma_per_K")
    if temp_sens is not None:
        if temp_sens < 0:
            warnings.append("Temperature sensitivity cannot be negative")
        elif temp_sens > 0.01:
            warnings.append(
                f"Temperature sensitivity {temp_sens:.6f} /K seems very high"
            )

    # Check bore friction is reasonable
    bore_fric = fit_results.get("bore_friction_psi")
    if bore_fric is not None and bore_fric > 10000:
        warnings.append(f"Bore friction {bore_fric:.0f} psi seems unreasonably high")

    # Check residuals for systematic bias
    residuals = fit_results.get("residuals", [])
    if len(residuals) > 3:
        residual_std = np.std(residuals)
        residual_mean = np.mean(residuals)
        if abs(residual_mean) > 2 * residual_std:
            warnings.append(
                f"Residuals show systematic bias (mean = {residual_mean:.1f} fps)"
            )

    # Check convergence
    convergence = fit_results.get("convergence", {})
    if not convergence.get("success", False):
        warnings.append(
            f"Optimization did not converge: {convergence.get('message', 'Unknown error')}"
        )

    return warnings


def validate_simulation_results(results: Dict[str, Any]) -> List[str]:
    """Validate simulation results for physical consistency.

    Parameters
    ----------
    results : Dict[str, Any]
        Results from solve_ballistics

    Returns
    -------
    List[str]
        List of validation warnings (empty if all checks pass)
    """
    warnings = []

    # Check muzzle velocity is reasonable
    v_muzzle = results.get("muzzle_velocity_fps", 0)
    if v_muzzle <= 0:
        warnings.append("Muzzle velocity must be positive")
    elif v_muzzle > 5000:  # Very high velocity
        warnings.append(f"Muzzle velocity {v_muzzle:.0f} fps seems unreasonably high")

    # Check peak pressure is reasonable
    p_peak = results.get("peak_pressure_psi", 0)
    if p_peak <= 0:
        warnings.append("Peak pressure must be positive")
    elif p_peak > 150000:  # Very high pressure
        warnings.append(f"Peak pressure {p_peak:.0f} psi seems dangerously high")

    # Check final Z (burn fraction)
    final_z = results.get("final_Z", 0)
    if final_z < 0 or final_z > 1.1:  # Allow slight overshoot
        warnings.append(
            f"Final burn fraction {final_z:.3f} is outside valid range [0, 1]"
        )

    # Check time to target is reasonable
    time_s = results.get("total_time_s", 0)
    if time_s <= 0:
        warnings.append("Simulation time must be positive")
    elif time_s > 0.1:  # Very long time
        warnings.append(f"Simulation time {time_s:.4f} s seems very long")

    # Check burnout distance is reasonable
    burnout_dist = results.get("burnout_distance_from_bolt_in")
    if burnout_dist is not None:
        if burnout_dist < 0:
            warnings.append("Burnout distance cannot be negative")
        elif burnout_dist > 50:  # Very long burnout distance
            warnings.append(
                f"Burnout distance {burnout_dist:.1f} in seems unusually long"
            )

    return warnings
