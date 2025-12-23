"""Multi-parameter optimization routines for vivacity fitting.

This module provides functions to fit dynamic vivacity polynomials from
chronograph data, with optional physics parameter calibration.
"""

import numpy as np
from scipy.optimize import minimize
import pandas as pd
from copy import deepcopy as copy

from .solver import solve_ballistics
from .burn_rate import validate_vivacity_positive
from .props import BallisticsConfig


def fit_vivacity_polynomial(
    load_data: pd.DataFrame,
    config_base: BallisticsConfig,
    initial_guess: tuple[float, ...] | None = None,
    bounds: tuple[tuple[float, float], ...] | None = None,
    regularization: float = 0.0,
    method: str = 'L-BFGS-B',
    verbose: bool = True,
    fit_temp_sensitivity: bool = False,
    fit_bore_friction: bool = False,
    fit_start_pressure: bool = False,
    fit_covolume: bool = False
) -> dict:
    """Fit vivacity polynomial and optional physics parameters from load ladder data.

    Parameters
    ----------
    load_data : pd.DataFrame
        Columns: charge_grains, mean_velocity_fps, velocity_sd (optional)
    config_base : BallisticsConfig
        Base configuration (charge_mass_gr will be overridden per row)
    initial_guess : tuple, optional
        (Lambda_base, a, b, c, d [, temp_sens, bore_fric, start_p, covolume])
        Defaults to database values + (1, -1, 0, 0)
        Additional parameters added if fit_* flags are True
    bounds : tuple, optional
        ((Lambda_min, a_min, ...), (Lambda_max, a_max, ...))
        Default: Lambda ∈ [0.01, 0.15], a,b,c,d ∈ [-2, 2]
        Additional bounds auto-added for physics parameters if fit_* flags True
    regularization : float
        L2 penalty on coefficients (default 0.0)
    method : str
        Optimization method ('L-BFGS-B', 'trust-constr')
    verbose : bool
        Print iteration progress
    fit_temp_sensitivity : bool
        If True, fit temperature sensitivity coefficient (sigma_per_K)
    fit_bore_friction : bool
        If True, fit bore friction (psi)
    fit_start_pressure : bool
        If True, fit shot-start pressure threshold (psi)
    fit_covolume : bool
        If True, fit Noble-Abel covolume (m³/kg) - usually not recommended

    Returns
    -------
    dict
        Keys: Lambda_base, coeffs (a,b,c,d), rmse_velocity, residuals, success, message
        Additional keys if physics parameters fitted: temp_sensitivity_sigma_per_K,
        bore_friction_psi, start_pressure_psi, covolume_m3_per_kg
    """
    # Validate input data
    required_cols = ['charge_grains', 'mean_velocity_fps']
    for col in required_cols:
        if col not in load_data.columns:
            raise ValueError(f"Missing required column: {col}")

    if len(load_data) < 3:
        raise ValueError(f"Need at least 3 data points for fitting, got {len(load_data)}")

    # Build parameter names list (for tracking what we're fitting)
    param_names = ['Lambda_base', 'a', 'b', 'c', 'd']

    # Set default initial guess
    if initial_guess is None:
        Lambda_base_init = config_base.propellant.Lambda_base
        a_init, b_init, c_init, d_init = config_base.propellant.poly_coeffs
        # Use database values if they're reasonable, else use defaults
        if a_init == 0 and b_init == 0 and c_init == 0 and d_init == 0:
            a_init, b_init, c_init, d_init = 1.0, -1.0, 0.0, 0.0
        initial_guess = [Lambda_base_init, a_init, b_init, c_init, d_init]

        # Add physics parameters if requested
        if fit_temp_sensitivity:
            initial_guess.append(config_base.propellant.temp_sensitivity_sigma_per_K)
            param_names.append('temp_sens')
        if fit_bore_friction:
            initial_guess.append(config_base.bore_friction_psi)
            param_names.append('bore_fric')
        if fit_start_pressure:
            initial_guess.append(config_base.start_pressure_psi)
            param_names.append('start_p')
        if fit_covolume:
            initial_guess.append(config_base.propellant.covolume_m3_per_kg)
            param_names.append('covolume')

        initial_guess = tuple(initial_guess)

    # Set default bounds for base parameters
    if bounds is None:
        bounds_lower = [0.01, -2.0, -2.0, -2.0, -2.0]
        bounds_upper = [0.15, 2.0, 2.0, 2.0, 2.0]

        # Add physics parameter bounds if requested
        if fit_temp_sensitivity:
            bounds_lower.append(0.0)      # temp_sens ∈ [0.0, 0.01] /K
            bounds_upper.append(0.01)
        if fit_bore_friction:
            bounds_lower.append(0.0)      # bore_friction ∈ [0, 4000] psi
            bounds_upper.append(4000.0)
        if fit_start_pressure:
            bounds_lower.append(1000.0)   # start_pressure ∈ [1000, 12000] psi
            bounds_upper.append(12000.0)
        if fit_covolume:
            bounds_lower.append(0.0008)   # covolume ∈ [0.0008, 0.0012] m³/kg
            bounds_upper.append(0.0012)

        bounds = (tuple(bounds_lower), tuple(bounds_upper))

    # Iteration counter for verbose output
    iteration = {'count': 0}

    def _objective_function(params, load_data, config_base, param_names, fit_temp_sensitivity, fit_bore_friction, fit_start_pressure, fit_covolume):
        """Objective function for scipy.optimize.minimize."""

        # Unpack parameters
        Lambda_base = params[0]
        a, b, c, d = params[1:5]
        coeffs = (a, b, c, d)

        # Extract physics parameters
        idx = 5
        temp_sens = params[idx] if fit_temp_sensitivity else config_base.propellant.temp_sensitivity_sigma_per_K
        idx += 1 if fit_temp_sensitivity else 0
        bore_fric = params[idx] if fit_bore_friction else config_base.bore_friction_psi
        idx += 1 if fit_bore_friction else 0
        start_p = params[idx] if fit_start_pressure else config_base.start_pressure_psi
        idx += 1 if fit_start_pressure else 0
        covolume = params[idx] if fit_covolume else config_base.propellant.covolume_m3_per_kg

        # Check vivacity positivity constraint
        T_prop_K = config_base.temperature_f * 5/9 + 255.372  # Convert to Kelvin
        if not validate_vivacity_positive(Lambda_base, coeffs, T_prop_K, temp_sens, n_points=50):
            return 1e10  # Large penalty for invalid parameters

        residuals = []
        weights = []

        for idx_row, row in load_data.iterrows():
            # Update charge
            config = copy(config_base)
            config.charge_mass_gr = float(row['charge_grains'])

            # Apply physics parameters
            config.propellant = copy(config.propellant)
            config.propellant.Lambda_base = Lambda_base
            config.propellant.poly_coeffs = coeffs
            config.propellant.temp_sensitivity_sigma_per_K = temp_sens
            config.propellant.covolume_m3_per_kg = covolume
            config.bore_friction_psi = bore_fric
            config.start_pressure_psi = start_p

            # Solve ballistics
            try:
                results = solve_ballistics(config)
                predicted_v = results['muzzle_velocity_fps']
                measured_v = float(row['mean_velocity_fps'])
                residual = predicted_v - measured_v
                residuals.append(residual)

                # Weight by inverse variance if available
                if 'velocity_sd' in row and pd.notna(row['velocity_sd']) and row['velocity_sd'] > 0:
                    weight = 1.0 / (row['velocity_sd'] ** 2)
                else:
                    weight = 1.0
                weights.append(weight)

            except Exception:
                # If solver fails, return large penalty
                return 1e10

        # Calculate weighted RMSE
        residuals_np = np.array(residuals)
        weights_np = np.array(weights)
        if np.sum(weights_np) > 0:
            weighted_rmse = np.sqrt(np.sum(weights_np * residuals_np**2) / np.sum(weights_np))
        else:
            weighted_rmse = np.sqrt(np.mean(residuals_np**2))
        return weighted_rmse
    
    def objective_with_logging(params):
        """Wrapper to add logging to objective function."""
        obj_val = _objective_function(
            params, load_data, config_base, param_names, fit_temp_sensitivity,
            fit_bore_friction, fit_start_pressure, fit_covolume
        )
        iteration['count'] += 1
        if verbose and iteration['count'] % 10 == 0:
            # Build logging string
            Lambda_base = params[0]
            a, b, c, d = params[1:5]
            log_str = f"Iteration {iteration['count']}: RMSE = {obj_val:.2f} fps, " \
                     f"Lambda = {Lambda_base:.3f}, coeffs = ({a:.3f}, {b:.3f}, {c:.3f}, {d:.3f})"

            # Add physics parameters if being fitted
            idx = 5
            if fit_temp_sensitivity:
                temp_sens = params[idx]
                log_str += f", temp_sens = {temp_sens:.6f}"
                idx += 1
            if fit_bore_friction:
                bore_fric = params[idx]
                log_str += f", bore_fric = {bore_fric:.1f}"
                idx += 1
            if fit_start_pressure:
                start_p = params[idx]
                log_str += f", start_p = {start_p:.0f}"
                idx += 1
            if fit_covolume:
                covolume = params[idx]
                log_str += f", covolume = {covolume:.6f}"

            print(log_str)

        return obj_val

    # Run optimization
    result = minimize(
        objective_with_logging,
        x0=initial_guess,
        method=method,
        bounds=list(zip(bounds[0], bounds[1])),
        options={'maxiter': 500, 'ftol': 1e-6}
    )

    # Extract results
    Lambda_base_fit = result.x[0]
    a_fit, b_fit, c_fit, d_fit = result.x[1:5]
    coeffs_fit = (a_fit, b_fit, c_fit, d_fit)

    # Extract physics parameters if fitted
    idx = 5
    temp_sens_fit = None
    bore_fric_fit = None
    start_p_fit = None
    covolume_fit = None

    if fit_temp_sensitivity:
        temp_sens_fit = result.x[idx]
        idx += 1
    if fit_bore_friction:
        bore_fric_fit = result.x[idx]
        idx += 1
    if fit_start_pressure:
        start_p_fit = result.x[idx]
        idx += 1
    if fit_covolume:
        covolume_fit = result.x[idx]
        idx += 1

    # Validate vivacity positivity
    # Use fitted temperature sensitivity if available, else use config value
    temp_sens_check = temp_sens_fit if temp_sens_fit is not None else config_base.propellant.temp_sensitivity_sigma_per_K
    is_positive = validate_vivacity_positive(
        Lambda_base_fit, coeffs_fit,
        T_prop_K=config_base.temperature_f * 5/9 + 255.372,  # Convert to Kelvin
        temp_sensitivity_sigma_per_K=temp_sens_check,
        n_points=100
    )

    # Compute final residuals and predicted velocities
    # Apply fitted physics parameters to config
    predicted_velocities = []
    residuals = []
    weights: list[float] = []

    for idx_row, row in load_data.iterrows():
        # Update charge
        config = copy(config_base)
        config.charge_mass_gr = row['charge_grains']

        # Apply physics parameters
        if fit_temp_sensitivity or fit_covolume:
            from .props import PropellantProperties
            prop_updated = PropellantProperties(
                name=config.propellant.name,
                vivacity=config.propellant.vivacity,
                base=config.propellant.base,
                force=config.propellant.force,
                temp_0=config.propellant.temp_0,
                gamma=config.propellant.gamma,
                bulk_density=config.propellant.bulk_density,
                Lambda_base=config.propellant.Lambda_base,
                poly_coeffs=config.propellant.poly_coeffs,
                covolume_m3_per_kg=covolume,
                temp_sensitivity_sigma_per_K=temp_sens
            )
            config.propellant = prop_updated

        if fit_bore_friction:
            config.bore_friction_psi = bore_fric
        if fit_start_pressure:
            config.start_pressure_psi = start_p

        try:
            # Solve with overrides
            result = solve_ballistics(
                config,
                Lambda_override=Lambda_base,
                coeffs_override=coeffs
            )

            # Compute weighted residual
            v_pred = result['muzzle_velocity_fps']
            v_obs = row['mean_velocity_fps']
            residual = v_pred - v_obs

            # Weight by inverse variance if available
            if 'velocity_sd' in row and row['velocity_sd'] > 0:
                weight = 1.0 / (row['velocity_sd'] ** 2)
            else:
                weight = 1.0

            residuals.append(residual)
            weights.append(weight)

        except (ValueError, RuntimeError):
            # If solver fails, return large penalty
            return 1e10

    residuals = np.array(residuals)
    weights = np.array(weights)

    # Normalize weights
    weights = weights / np.sum(weights) * len(weights)

    # Weighted RMSE
    rmse = np.sqrt(np.mean(residuals**2 * weights))

    # L2 regularization on coefficients (not Lambda_base)
    penalty = regularization * (a**2 + b**2 + c**2 + d**2)

    return rmse + penalty
