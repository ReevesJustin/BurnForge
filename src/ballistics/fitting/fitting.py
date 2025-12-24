"""Multi-parameter optimization routines for vivacity fitting.

This module provides functions to fit dynamic vivacity polynomials from
chronograph data, with optional physics parameter calibration.
"""

import numpy as np
from scipy.optimize import minimize
import pandas as pd
from copy import deepcopy as copy

from ballistics.core.solver import solve_ballistics
from ballistics.core.burn_rate import validate_vivacity_positive
from ballistics.core.props import BallisticsConfig


def fit_vivacity_polynomial(
    load_data: pd.DataFrame,
    config_base: BallisticsConfig,
    initial_guess: tuple[float, ...] | list[float] | None = None,
    bounds: tuple[tuple[float, ...], tuple[float, ...]] | None = None,
    regularization: float = 0.0,
    method: str = "L-BFGS-B",
    verbose: bool = True,
    fit_temp_sensitivity: bool = False,
    fit_bore_friction: bool = False,
    fit_start_pressure: bool = False,
    fit_covolume: bool = False,
    fit_h_base: bool = False,
    fit_k_param: bool = False,
    fit_p_primer: bool = False,
    use_form_function: bool = False,
    include_pressure_penalty: bool = False,
    pressure_weight: float = 0.3,
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
    include_pressure_penalty : bool
        If True, include max pressure reference penalty in loss function (requires p_max_psi in data)
    pressure_weight : float
        Weight for pressure penalty term in combined loss (default 0.3)

    Returns
    -------
    dict
        Keys: Lambda_base, coeffs (a,b,c,d), rmse_velocity, residuals, success, message
        Additional keys if physics parameters fitted: temp_sensitivity_sigma_per_K,
        bore_friction_psi, start_pressure_psi, covolume_m3_per_kg
    """
    # Validate input data
    required_cols = ["charge_grains", "mean_velocity_fps"]
    for col in required_cols:
        if col not in load_data.columns:
            raise ValueError(f"Missing required column: {col}")

    if len(load_data) < 3:
        raise ValueError(
            f"Need at least 3 data points for fitting, got {len(load_data)}"
        )

    # Data validation checks
    max_charge = load_data["charge_grains"].max()
    fill_ratios = load_data["charge_grains"] / max_charge

    if (fill_ratios < 0.8).any():
        print(
            "Warning: Some charges have fill ratio < 0.8, which may indicate invalid data or extreme loads"
        )
    if (fill_ratios > 1.05).any():
        print(
            "Warning: Some charges have fill ratio > 1.05, which may indicate compressed loads"
        )

    velocity_range = (
        load_data["mean_velocity_fps"].max() - load_data["mean_velocity_fps"].min()
    )
    if velocity_range < 50:
        print("Warning: Small velocity range (<50 fps) may limit fitting accuracy")

    # Extract optional max pressure reference
    grt_p_max_reference = None
    if "p_max_psi" in load_data.columns:
        # Use the value for the highest charge weight only
        max_charge_row = load_data[load_data["charge_grains"] == max_charge]
        if not max_charge_row.empty:
            p_max_val = max_charge_row["p_max_psi"].iloc[0]
            if pd.notna(p_max_val):
                grt_p_max_reference = float(p_max_val)
                print(
                    f"Using max pressure reference: {grt_p_max_reference:.0f} psi for {max_charge:.1f}gr charge"
                )

    # Build parameter names list (for tracking what we're fitting)
    if use_form_function:
        param_names = ["Lambda_base", "alpha"]
    else:
        param_names = ["Lambda_base", "a", "b", "c", "d", "e", "f"]

    # Set default initial guess
    if initial_guess is None:
        Lambda_base_init = config_base.propellant.Lambda_base
        if use_form_function:
            initial_guess = [Lambda_base_init, config_base.propellant.alpha]
        else:
            a_init, b_init, c_init, d_init, e_init, f_init = (
                config_base.propellant.poly_coeffs
            )
            # Use database values if they're reasonable, else use defaults
            if a_init == 0 and b_init == 0 and c_init == 0 and d_init == 0:
                a_init, b_init, c_init, d_init = 1.0, -1.0, 0.0, 0.0
            initial_guess = [
                Lambda_base_init,
                a_init,
                b_init,
                c_init,
                d_init,
                e_init,
                f_init,
            ]

        # Add physics parameters if requested (ensure no None values)
        if fit_temp_sensitivity:
            temp_sens_val = config_base.propellant.temp_sensitivity_sigma_per_K
            if temp_sens_val is None or temp_sens_val == 0:
                temp_sens_val = (
                    0.002  # Improved initial guess for cold data convergence
                )
            initial_guess.append(temp_sens_val)
            param_names.append("temp_sens")
        if fit_bore_friction:
            bore_fric_val = config_base.bore_friction_psi
            if bore_fric_val is not None:
                initial_guess.append(bore_fric_val)
                param_names.append("bore_fric")
        if fit_start_pressure:
            start_p_val = (
                config_base.start_pressure_psi
                if config_base.start_pressure_psi is not None
                else 2000.0
            )
            initial_guess.append(start_p_val)
            param_names.append("start_p")
        if fit_covolume:
            covolume_val = config_base.propellant.covolume_m3_per_kg
            if covolume_val is not None:
                initial_guess.append(covolume_val)
                param_names.append("covolume")
        if fit_h_base:
            h_base_val = config_base.h_base
            if h_base_val is not None:
                initial_guess.append(h_base_val)
                param_names.append("h_base")

        initial_guess = tuple(initial_guess)

    # Set default bounds for base parameters
    if bounds is None:
        if use_form_function:
            bounds_lower = [0.01, 0.0]
            bounds_upper = [0.15, 0.5]
        else:
            bounds_lower = [
                0.01,
                -2.0,
                -2.0,
                -2.0,
                -2.0,
                -1.0,
                -1.0,
            ]  # Tighter bounds for higher-order terms
            bounds_upper = [0.15, 2.0, 2.0, 2.0, 2.0, 1.0, 1.0]

        # Add physics parameter bounds if requested
        if fit_temp_sensitivity:
            bounds_lower.append(
                0.0005
            )  # temp_sens ∈ [0.0005, 0.005] /K for better convergence
            bounds_upper.append(0.005)
        if fit_bore_friction:
            bounds_lower.append(0.0)  # bore_friction ∈ [0, 4000] psi
            bounds_upper.append(4000.0)
        if fit_start_pressure:
            bounds_lower.append(1000.0)  # start_pressure ∈ [1000, 12000] psi
            bounds_upper.append(12000.0)
        if fit_covolume:
            bounds_lower.append(0.0008)  # covolume ∈ [0.0008, 0.0012] m³/kg
            bounds_upper.append(0.0012)
        if fit_h_base:
            bounds_lower.append(500.0)  # h_base ∈ [500, 10000] W/m²·K
            bounds_upper.append(10000.0)
        if fit_k_param:
            bounds_lower.append(0.0)  # k_param ∈ [0, 0.5]
            bounds_upper.append(0.5)

        bounds = (tuple(bounds_lower), tuple(bounds_upper))

    # Iteration counter for verbose output
    iteration = {"count": 0}

    def _objective_function(
        params,
        load_data,
        config_base,
        param_names,
        fit_temp_sensitivity,
        fit_bore_friction,
        fit_start_pressure,
        fit_covolume,
        fit_h_base,
        fit_k_param,
        fit_p_primer,
        use_form_function,
        geometry,
        grt_p_max_reference,
        include_pressure_penalty,
        pressure_weight,
        max_charge,
    ):
        """Objective function for scipy.optimize.minimize."""

        # Compute max charge for weighting and fill ratio
        max_charge = load_data["charge_grains"].max()

        # Unpack parameters
        Lambda_base = params[0]
        if use_form_function:
            alpha = params[1]
            coeffs = (1, 0, 0, 0)
            idx = 1
        else:
            a, b, c, d, e, f = params[1:7]
            coeffs = (a, b, c, d, e, f)
            alpha = 0.0
            idx = 7
        temp_sens = (
            params[idx]
            if fit_temp_sensitivity
            else config_base.propellant.temp_sensitivity_sigma_per_K
        )
        idx += 1 if fit_temp_sensitivity else 0
        bore_fric = params[idx] if fit_bore_friction else config_base.bore_friction_psi
        idx += 1 if fit_bore_friction else 0
        start_p = params[idx] if fit_start_pressure else config_base.start_pressure_psi
        idx += 1 if fit_start_pressure else 0
        covolume = (
            params[idx] if fit_covolume else config_base.propellant.covolume_m3_per_kg
        )
        idx += 1 if fit_covolume else 0
        h_base = params[idx] if fit_h_base else config_base.h_base
        idx += 1 if fit_h_base else 0
        k_param = params[idx] if fit_k_param else config_base.k_param
        idx += 1 if fit_k_param else 0
        p_primer = params[idx] if fit_p_primer else config_base.p_primer_psi

        # Check vivacity positivity constraint
        T_prop_K = config_base.temperature_f * 5 / 9 + 255.372  # Convert to Kelvin
        if not validate_vivacity_positive(
            Lambda_base,
            coeffs,
            T_prop_K,
            temp_sens,
            n_points=50,
            use_form_function=use_form_function,
            geometry=config_base.propellant.grain_geometry,
            alpha=alpha if use_form_function else 0.0,
        ):
            return 1e10  # Large penalty for invalid parameters

        # Compute max charge for weighting and fill ratio
        max_charge = load_data["charge_grains"].max()

        residuals = []
        weights = []

        for idx_row, row in load_data.iterrows():
            # Update charge
            config = copy(config_base)
            config.charge_mass_gr = float(row["charge_grains"])  # type: ignore

            # Apply physics parameters
            config.propellant = copy(config.propellant)
            config.propellant.Lambda_base = Lambda_base
            config.propellant.poly_coeffs = coeffs
            if use_form_function:
                config.propellant.alpha = alpha
            config.use_form_function = use_form_function
            if fit_temp_sensitivity:
                config.propellant.temp_sensitivity_sigma_per_K = temp_sens
            if fit_covolume:
                config.propellant.covolume_m3_per_kg = covolume
            if fit_bore_friction:
                config.bore_friction_psi = bore_fric
            if fit_start_pressure:
                config.start_pressure_psi = start_p

            # Solve ballistics
            try:
                results = solve_ballistics(config)
                predicted_v = results["muzzle_velocity_fps"]
                measured_v = float(row["mean_velocity_fps"])
                residual = predicted_v - measured_v
                residuals.append(residual)

                # Weight by charge fraction and inverse variance if available
                charge_weight = row["charge_grains"] / max_charge
                if (
                    "velocity_sd" in row
                    and pd.notna(row["velocity_sd"])
                    and row["velocity_sd"] > 0
                ):
                    weight = charge_weight / (row["velocity_sd"] ** 2)
                else:
                    weight = charge_weight
                weights.append(weight)

            except Exception:
                # If solver fails, return large penalty
                return 1e10

        # Calculate weighted RMSE for minimization
        residuals_np = np.array(residuals)
        weights_np = np.array(weights)
        if np.sum(weights_np) > 0:
            weighted_rmse = np.sqrt(
                np.sum(weights_np * residuals_np**2) / np.sum(weights_np)
            )
        else:
            weighted_rmse = np.sqrt(np.mean(residuals_np**2))

        # Add optional pressure penalty
        pressure_penalty = 0.0
        if include_pressure_penalty and grt_p_max_reference is not None:
            # Run simulation for the max charge only
            max_charge_config = copy(config_base)
            max_charge_config.charge_mass_gr = max_charge
            max_charge_config.max_charge_gr = max_charge

            # Apply fitted parameters
            max_charge_config.propellant.Lambda_base = Lambda_base
            max_charge_config.propellant.poly_coeffs = coeffs
            if use_form_function:
                max_charge_config.propellant.alpha = alpha
            if fit_temp_sensitivity:
                max_charge_config.propellant.temp_sensitivity_sigma_per_K = temp_sens
            if fit_covolume:
                max_charge_config.propellant.covolume_m3_per_kg = covolume
            if fit_bore_friction:
                max_charge_config.bore_friction_psi = bore_fric
            if fit_start_pressure:
                max_charge_config.start_pressure_psi = start_p
            if fit_h_base:
                max_charge_config.h_base = h_base
            if fit_k_param:
                max_charge_config.k_param = k_param
            if fit_p_primer:
                max_charge_config.p_primer_psi = p_primer

            try:
                result_max = solve_ballistics(max_charge_config)
                sim_p_max = result_max["peak_pressure_psi"]
                pressure_penalty = (
                    (sim_p_max - grt_p_max_reference) / grt_p_max_reference
                ) ** 2
            except Exception:
                pressure_penalty = 1.0  # Large penalty for solver failure

        combined_loss = weighted_rmse + pressure_weight * pressure_penalty
        return combined_loss

    def objective_with_logging(params):
        """Wrapper to add logging to objective function."""
        obj_val = _objective_function(
            params,
            load_data,
            config_base,
            param_names,
            fit_temp_sensitivity,
            fit_bore_friction,
            fit_start_pressure,
            fit_covolume,
            fit_h_base,
            fit_k_param,
            fit_p_primer,
            use_form_function,
            config_base.propellant.grain_geometry,
            grt_p_max_reference,
            include_pressure_penalty,
            pressure_weight,
            max_charge,
        )
        iteration["count"] += 1
        if verbose and iteration["count"] % 10 == 0:
            # Build logging string
            Lambda_base = params[0]
            if use_form_function:
                alpha = params[1]
                log_str = (
                    f"Iteration {iteration['count']}: RMSE = {obj_val:.2f} fps, "
                    f"Lambda = {Lambda_base:.3f}, alpha = {alpha:.3f}"
                )
            else:
                a, b, c, d = params[1:5]
                log_str = (
                    f"Iteration {iteration['count']}: RMSE = {obj_val:.2f} fps, "
                    f"Lambda = {Lambda_base:.3f}, coeffs = ({a:.3f}, {b:.3f}, {c:.3f}, {d:.3f})"
                )

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
                idx += 1
            if fit_h_base:
                h_base_val = params[idx]
                log_str += f", h_base = {h_base_val:.0f}"
                idx += 1
            if fit_k_param:
                k_param_val = params[idx]
                log_str += f", k_param = {k_param_val:.3f}"
                idx += 1

            print(log_str)

        return obj_val

    # Run optimization
    opt_result = minimize(
        objective_with_logging,
        x0=initial_guess,
        method=method,
        bounds=list(zip(bounds[0], bounds[1])),
        options={"maxiter": 100, "ftol": 1e-3},
    )

    # Extract results
    Lambda_base_fit = opt_result.x[0]
    if use_form_function:
        alpha_fit = opt_result.x[1]
        coeffs_fit = (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)  # dummy
        a_fit = b_fit = c_fit = d_fit = 0.0
        idx = 2
    else:
        a_fit, b_fit, c_fit, d_fit, e_fit, f_fit = opt_result.x[1:7]
        coeffs_fit = (a_fit, b_fit, c_fit, d_fit, e_fit, f_fit)
        alpha_fit = None
        idx = 5
    temp_sens_fit = None
    bore_fric_fit = None
    start_p_fit = None
    covolume_fit = None
    h_base_fit = None

    if fit_temp_sensitivity:
        temp_sens_fit = opt_result.x[idx]
        idx += 1
    if fit_bore_friction:
        bore_fric_fit = opt_result.x[idx]
        idx += 1
    if fit_start_pressure:
        start_p_fit = opt_result.x[idx]
        idx += 1
    if fit_covolume:
        covolume_fit = opt_result.x[idx]
        idx += 1
    if fit_h_base:
        h_base_fit = opt_result.x[idx]
        idx += 1
    k_param_fit = None
    if fit_k_param:
        k_param_fit = opt_result.x[idx]
        idx += 1

    # Validate vivacity positivity
    # Use fitted temperature sensitivity if available, else use config value
    temp_sens_check = (
        temp_sens_fit
        if temp_sens_fit is not None
        else config_base.propellant.temp_sensitivity_sigma_per_K
    )
    validate_vivacity_positive(
        Lambda_base_fit,
        coeffs_fit,
        T_prop_K=config_base.temperature_f * 5 / 9 + 255.372,  # Convert to Kelvin
        temp_sensitivity_sigma_per_K=temp_sens_check,
        n_points=100,
    )

    # Compute final residuals and predicted velocities
    # Compute max charge for fill ratio
    max_charge = load_data["charge_grains"].max()

    # Apply fitted physics parameters to config
    predicted_velocities: list[float] = []
    residuals: list[float] = []
    weights: list[float] = []

    # Set fitted physics parameters (use fitted if available, else config defaults)
    temp_sens = (
        temp_sens_fit
        if temp_sens_fit is not None
        else config_base.propellant.temp_sensitivity_sigma_per_K
    )
    covolume = (
        covolume_fit
        if covolume_fit is not None
        else config_base.propellant.covolume_m3_per_kg
    )
    bore_fric = (
        bore_fric_fit if bore_fric_fit is not None else config_base.bore_friction_psi
    )
    start_p = start_p_fit if start_p_fit is not None else config_base.start_pressure_psi
    h_base = h_base_fit if h_base_fit is not None else config_base.h_base
    k_param = k_param_fit if k_param_fit is not None else config_base.k_param

    for idx_row, row in load_data.iterrows():
        # Update charge
        config = copy(config_base)
        config.charge_mass_gr = float(row["charge_grains"])
        config.max_charge_gr = max_charge

        # Apply physics parameters
        if fit_temp_sensitivity or fit_covolume:
            from ballistics.core.props import PropellantProperties

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
                temp_sensitivity_sigma_per_K=temp_sens,
            )
            config.propellant = prop_updated

        if fit_bore_friction and bore_fric is not None:
            config.bore_friction_psi = bore_fric
        if fit_start_pressure and start_p is not None:
            config.start_pressure_psi = start_p
        if fit_h_base and h_base is not None:
            config.h_base = h_base
        if fit_k_param and k_param is not None:
            config.k_param = k_param

        try:
            # Solve with overrides
            solve_result = solve_ballistics(
                config,
            )

            # Compute weighted residual
            v_pred = solve_result["muzzle_velocity_fps"]
            v_obs = float(row["mean_velocity_fps"])
            residual = v_pred - v_obs

            # Weight by inverse variance if available
            try:
                sd_val = row.get("velocity_sd", 0)
                if sd_val is not None and float(sd_val) > 0:
                    weight = 1.0 / (float(sd_val) ** 2)
                else:
                    weight = 1.0
            except (ValueError, TypeError, KeyError):
                weight = 1.0

        except (ValueError, RuntimeError):
            # If solver fails, use large penalty for this data point
            v_pred = 1e10  # Large penalty
            v_obs = float(row["mean_velocity_fps"])
            residual = v_pred - v_obs
            weight = 1.0

        predicted_velocities.append(v_pred)
        residuals.append(residual)
        weights.append(weight)

    residuals_array = np.array(residuals)
    weights_array = np.array(weights)

    # Normalize weights
    if np.sum(weights_array) > 0:
        weights_array = weights_array / np.sum(weights_array) * len(weights_array)

    # Weighted RMSE
    rmse = float(np.sqrt(np.mean(residuals_array**2 * weights_array)))

    # L2 regularization on coefficients (not Lambda_base)
    # penalty = regularization * (a_fit**2 + b_fit**2 + c_fit**2 + d_fit**2)  # Not used

    # Convergence diagnostics
    convergence_info = {
        "success": opt_result.success,
        "message": opt_result.message,
        "nfev": getattr(opt_result, "nfev", None),  # Function evaluations
        "nit": getattr(opt_result, "nit", None),  # Iterations
        "fun_value": opt_result.fun if hasattr(opt_result, "fun") else None,
    }

    # Build return dict
    result_dict = {
        "Lambda_base": Lambda_base_fit,
        "coeffs": coeffs_fit,
        "rmse_velocity": rmse,
        "residuals": residuals,
        "predicted_velocities": predicted_velocities,
        "convergence": convergence_info,
    }

    # Add physics parameters if fitted
    alpha_fit = opt_result.x[1] if use_form_function else None
    if alpha_fit is not None:
        result_dict["alpha"] = alpha_fit
    if temp_sens_fit is not None:
        result_dict["temp_sensitivity_sigma_per_K"] = temp_sens_fit
        if temp_sens_fit < 0.001 or temp_sens_fit > 0.008:
            print(
                f"WARNING: Fitted temp_sensitivity ({temp_sens_fit:.6f}) is outside expected range [0.001, 0.008]. Check data quality."
            )
    if bore_fric_fit is not None:
        result_dict["bore_friction_psi"] = bore_fric_fit
    if h_base_fit is not None:
        result_dict["h_base"] = h_base_fit
    if start_p_fit is not None:
        result_dict["start_pressure_psi"] = start_p_fit
    if covolume_fit is not None:
        result_dict["covolume_m3_per_kg"] = covolume_fit

    # Add bias detection warnings
    if len(residuals) > 3:
        residual_std = np.std(residuals)
        residual_mean = np.mean(residuals)
        if abs(residual_mean) > 2 * residual_std:
            print(
                f"WARNING: Residuals show systematic bias (mean = {residual_mean:.1f} fps, "
                f"std = {residual_std:.1f} fps). Check model assumptions or data quality."
            )

        # Check for trends in residuals vs charge weight
        charges = np.array(load_data["charge_grains"])
        residuals_array = np.array(residuals)
        if len(charges) == len(residuals_array):
            correlation = np.corrcoef(charges, residuals_array)[0, 1]
            if abs(correlation) > 0.5:
                trend = "increasing" if correlation > 0 else "decreasing"
                print(
                    f"WARNING: Residuals show {trend} trend with charge weight "
                    f"(correlation = {correlation:.2f}). Model may have systematic bias."
                )

    return result_dict


def leave_one_out_cross_validation(
    load_data: pd.DataFrame,
    config_base: BallisticsConfig,
    fit_kwargs: dict | None = None,
) -> dict:
    """Perform leave-one-out cross-validation to assess model robustness.

    Parameters
    ----------
    load_data : pd.DataFrame
        Load data with columns: charge_grains, mean_velocity_fps, velocity_sd
    config_base : BallisticsConfig
        Base configuration
    fit_kwargs : dict, optional
        Additional arguments for fit_vivacity_polynomial

    Returns
    -------
    dict
        LOO CV results with keys:
        - loo_rmse: Root mean square error of LOO predictions
        - loo_mae: Mean absolute error of LOO predictions
        - predicted_vs_actual: List of (actual, predicted) tuples
        - fold_results: Individual fold results
    """
    if fit_kwargs is None:
        fit_kwargs = {}

    n_points = len(load_data)
    predicted_vs_actual = []
    fold_results = []

    for i in range(n_points):
        # Create training set (all points except i)
        train_data = load_data.drop(index=i).reset_index(drop=True)
        # Test point
        test_point = load_data.iloc[i]

        try:
            # Fit model on training data
            fit_result = fit_vivacity_polynomial(
                train_data, config_base, verbose=False, **fit_kwargs
            )

            # Predict test point
            from copy import deepcopy

            test_config = deepcopy(config_base)
            test_config.charge_mass_gr = test_point["charge_grains"]
            test_config.charge_mass_gr = test_point["charge_grains"]
            test_config.propellant.Lambda_base = fit_result["Lambda_base"]
            test_config.propellant.poly_coeffs = fit_result["coeffs"]

            # Add fitted physics parameters if they exist
            for param in [
                "temp_sensitivity_sigma_per_K",
                "bore_friction_psi",
                "start_pressure_psi",
                "h_base",
                "covolume_m3_per_kg",
            ]:
                if param in fit_result:
                    setattr(test_config, param, fit_result[param])

            pred_result = solve_ballistics(test_config)
            predicted_velocity = pred_result["muzzle_velocity_fps"]
            actual_velocity = test_point["mean_velocity_fps"]

            predicted_vs_actual.append((actual_velocity, predicted_velocity))
            fold_results.append(
                {
                    "fold": i,
                    "charge": test_point["charge_grains"],
                    "actual": actual_velocity,
                    "predicted": predicted_velocity,
                    "error": predicted_velocity - actual_velocity,
                    "abs_error": abs(predicted_velocity - actual_velocity),
                }
            )

        except Exception as e:
            print(f"Warning: LOO fold {i} failed: {e}")
            predicted_vs_actual.append((test_point["mean_velocity_fps"], float("nan")))
            fold_results.append(
                {
                    "fold": i,
                    "charge": test_point["charge_grains"],
                    "actual": test_point["mean_velocity_fps"],
                    "predicted": float("nan"),
                    "error": float("nan"),
                    "abs_error": float("nan"),
                }
            )

    # Calculate LOO statistics
    valid_predictions = [(a, p) for a, p in predicted_vs_actual if not np.isnan(p)]
    if valid_predictions:
        actuals, preds = zip(*valid_predictions)
        errors = np.array(preds) - np.array(actuals)
        loo_rmse = np.sqrt(np.mean(errors**2))
        loo_mae = np.mean(np.abs(errors))
    else:
        loo_rmse = loo_mae = float("nan")

    return {
        "loo_rmse": loo_rmse,
        "loo_mae": loo_mae,
        "predicted_vs_actual": predicted_vs_actual,
        "fold_results": fold_results,
        "n_folds": n_points,
        "n_valid_folds": len(valid_predictions),
    }


def fit_vivacity_sequential(
    load_data: pd.DataFrame,
    config_base: BallisticsConfig,
    initial_guess: tuple[float, ...] | list[float] | None = None,
    bounds: tuple[tuple[float, ...], tuple[float, ...]] | None = None,
    regularization: float = 0.0,
    method: str = "L-BFGS-B",
    verbose: bool = True,
) -> dict:
    """Fit vivacity parameters sequentially: first vivacity polynomial, then h_base.

    This implements a two-stage fitting process:
    1. Fit Lambda_base and polynomial coefficients (a,b,c,d) with advanced physics disabled
    2. Fix those parameters and fit h_base (heat transfer coefficient)

    Parameters
    ----------
    load_data : pd.DataFrame
        Columns: charge_grains, mean_velocity_fps, velocity_sd (optional)
    config_base : BallisticsConfig
        Base configuration (charge_mass_gr will be overridden per row)
    initial_guess : tuple, optional
        Initial guess for (Lambda_base, a, b, c, d, h_base)
        Defaults to database values + (1, -1, 0, 0, config.h_base)
    bounds : tuple, optional
        ((Lambda_min, a_min, ..., h_base_min), (Lambda_max, a_max, ..., h_base_max))
        Default bounds applied
    regularization : float
        L2 penalty on coefficients (default 0.0)
    method : str
        Optimization method ('L-BFGS-B', 'trust-constr')
    verbose : bool
        Print iteration progress

    Returns
    -------
    dict
        Keys: Lambda_base, coeffs, h_base, rmse_velocity, residuals, predicted_velocities,
        success, message, stage1_result, stage2_result
    """
    # Stage 1: Fit vivacity polynomial only
    if verbose:
        print("Stage 1: Fitting vivacity polynomial (Lambda_base, a, b, c, d)...")
    stage1_bounds = (bounds[0][:5], bounds[1][:5]) if bounds else None
    stage1_result = fit_vivacity_polynomial(
        load_data=load_data,
        config_base=config_base,
        initial_guess=initial_guess[:5] if initial_guess else None,
        bounds=stage1_bounds,
        regularization=regularization,
        method=method,
        verbose=verbose,
        fit_h_base=False,
    )

    # Extract fitted vivacity parameters
    fitted_lambda = stage1_result["Lambda_base"]
    fitted_coeffs = stage1_result["coeffs"]

    # Stage 2: Fit h_base with vivacity parameters fixed
    if verbose:
        print("Stage 2: Fitting h_base with vivacity parameters fixed...")

    # Create initial guess for stage 2: fitted vivacity + initial h_base
    h_base_initial = config_base.h_base if config_base.h_base else 1000.0
    stage2_initial = [
        fitted_lambda,
        fitted_coeffs[0],
        fitted_coeffs[1],
        fitted_coeffs[2],
        fitted_coeffs[3],
        h_base_initial,
    ]

    # Bounds for stage 2: tight bounds around fitted vivacity, normal for h_base
    if bounds:
        stage2_bounds_lower = (
            fitted_lambda,
            fitted_coeffs[0],
            fitted_coeffs[1],
            fitted_coeffs[2],
            fitted_coeffs[3],
            bounds[0][5],
        )
        stage2_bounds_upper = (
            fitted_lambda,
            fitted_coeffs[0],
            fitted_coeffs[1],
            fitted_coeffs[2],
            fitted_coeffs[3],
            bounds[1][5],
        )
    else:
        stage2_bounds_lower = (
            fitted_lambda,
            fitted_coeffs[0],
            fitted_coeffs[1],
            fitted_coeffs[2],
            fitted_coeffs[3],
            500.0,
        )
        stage2_bounds_upper = (
            fitted_lambda,
            fitted_coeffs[0],
            fitted_coeffs[1],
            fitted_coeffs[2],
            fitted_coeffs[3],
            10000.0,
        )

    stage2_result = fit_vivacity_polynomial(
        load_data=load_data,
        config_base=config_base,
        initial_guess=stage2_initial,
        bounds=(stage2_bounds_lower, stage2_bounds_upper),
        regularization=regularization,
        method=method,
        verbose=verbose,
        fit_h_base=True,
    )

    # Combine results
    combined_result = stage2_result.copy()
    combined_result["stage1_result"] = stage1_result
    combined_result["stage2_result"] = stage2_result

    if verbose:
        print(".2f")
        print(".2f")
        print(".2f")

    return combined_result


def fit_vivacity_hybrid(
    load_data: pd.DataFrame,
    config_base: BallisticsConfig,
    initial_guess_form: tuple[float, ...] | list[float] | None = None,
    initial_guess_poly: tuple[float, ...] | list[float] | None = None,
    bounds_form: tuple[tuple[float, ...], tuple[float, ...]] | None = None,
    bounds_poly: tuple[tuple[float, ...], tuple[float, ...]] | None = None,
    regularization: float = 0.0,
    method: str = "L-BFGS-B",
    verbose: bool = True,
) -> dict:
    """Fit hybrid vivacity model: geometric form + polynomial correction.

    First fits geometric form function to establish baseline propellant behavior,
    then fits polynomial correction on remaining RMSE.

    Parameters
    ----------
    load_data : pd.DataFrame
        Columns: charge_grains, mean_velocity_fps, velocity_sd (optional)
    config_base : BallisticsConfig
        Base configuration (charge_mass_gr will be overridden per row)
    initial_guess_form : tuple, optional
        Initial guess for geometric form parameters (Lambda_base, alpha)
    initial_guess_poly : tuple, optional
        Initial guess for polynomial correction (Lambda_base_hybrid, a, b, c, d)
    bounds_form : tuple, optional
        Bounds for geometric form parameters ((Lambda_min, alpha_min), (Lambda_max, alpha_max))
    bounds_poly : tuple, optional
        Bounds for polynomial parameters ((Lambda_min, a_min, b_min, c_min, d_min), (Lambda_max, a_max, b_max, c_max, d_max))
    regularization : float
        L2 penalty on polynomial coefficients (default 0.0)
    method : str
        Optimization method ('L-BFGS-B', 'trust-constr')
    verbose : bool
        Print iteration progress

    Returns
    -------
    dict
        Keys: Lambda_base, alpha, Lambda_base_hybrid, coeffs_hybrid, rmse_velocity,
        residuals, predicted_velocities, success, message
    """
    # Validate input data
    required_cols = ["charge_grains", "mean_velocity_fps"]
    for col in required_cols:
        if col not in load_data.columns:
            raise ValueError(f"Missing required column: {col}")

    if len(load_data) < 3:
        raise ValueError(
            f"Need at least 3 data points for fitting, got {len(load_data)}"
        )

    # Set default initial guesses
    if initial_guess_form is None:
        Lambda_base_init = config_base.propellant.Lambda_base
        initial_guess_form = [Lambda_base_init, config_base.propellant.alpha]

    if initial_guess_poly is None:
        Lambda_base_hybrid_init = 0.01  # Small correction
        initial_guess_poly = [Lambda_base_hybrid_init, 1.0, -1.0, 0.0, 0.0]

    # Set default bounds
    if bounds_form is None:
        bounds_form = ((0.01, 0.0), (0.15, 0.5))

    if bounds_poly is None:
        bounds_poly = ((0.0, -2.0, -2.0, -2.0, -2.0), (0.05, 2.0, 2.0, 2.0, 2.0))

    # Step 1: Fit geometric form function first
    if verbose:
        print("Step 1: Fitting geometric form function...")
    fit_result_form = fit_vivacity_polynomial(
        load_data,
        config_base,
        initial_guess=initial_guess_form,
        bounds=bounds_form,
        use_form_function=True,
        verbose=verbose,
    )

    if verbose:
        print(".2f")

    # For now, return just the geometric fit since full hybrid requires solver changes
    return fit_result_form
