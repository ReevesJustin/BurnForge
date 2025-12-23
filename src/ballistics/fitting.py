"""Multi-parameter optimization routines with bounds."""

import numpy as np
from scipy.optimize import minimize
import pandas as pd
from copy import copy

from .solver import solve_ballistics
from .burn_rate import validate_vivacity_positive
from .props import BallisticsConfig


def fit_vivacity_polynomial(
    load_data: pd.DataFrame,
    config_base: BallisticsConfig,
    initial_guess: tuple[float, float, float, float, float] | None = None,
    bounds: tuple | None = None,
    regularization: float = 0.0,
    method: str = 'L-BFGS-B',
    verbose: bool = True
) -> dict:
    """Fit full 5-parameter vivacity polynomial from load ladder data.

    Parameters
    ----------
    load_data : pd.DataFrame
        Columns: charge_grains, mean_velocity_fps, velocity_sd (optional)
    config_base : BallisticsConfig
        Base configuration (charge_mass_gr will be overridden per row)
    initial_guess : tuple, optional
        (Lambda_base, a, b, c, d). Defaults to database values + (1, -1, 0, 0)
    bounds : tuple, optional
        ((Lambda_min, a_min, ...), (Lambda_max, a_max, ...))
        Default: Lambda ∈ [20, 200], a,b,c,d ∈ [-2, 2]
    regularization : float
        L2 penalty on coefficients (default 0.0)
    method : str
        Optimization method ('L-BFGS-B', 'trust-constr')
    verbose : bool
        Print iteration progress

    Returns
    -------
    dict
        Keys: Lambda_base, coeffs (a,b,c,d), rmse_velocity, residuals, success, message
    """
    # Validate input data
    required_cols = ['charge_grains', 'mean_velocity_fps']
    for col in required_cols:
        if col not in load_data.columns:
            raise ValueError(f"Missing required column: {col}")

    if len(load_data) < 3:
        raise ValueError(f"Need at least 3 data points for fitting, got {len(load_data)}")

    # Set default initial guess
    if initial_guess is None:
        Lambda_base_init = config_base.propellant.Lambda_base
        a_init, b_init, c_init, d_init = config_base.propellant.poly_coeffs
        # Use database values if they're reasonable, else use defaults
        if a_init == 0 and b_init == 0 and c_init == 0 and d_init == 0:
            a_init, b_init, c_init, d_init = 1.0, -1.0, 0.0, 0.0
        initial_guess = (Lambda_base_init, a_init, b_init, c_init, d_init)

    # Set default bounds
    # Lambda_base is normalized (vivacity/1450), so typical range is 0.01-0.15
    if bounds is None:
        bounds = (
            (0.01, -2.0, -2.0, -2.0, -2.0),   # Lower bounds
            (0.15, 2.0, 2.0, 2.0, 2.0)        # Upper bounds
        )

    # Iteration counter for verbose output
    iteration = {'count': 0}

    def objective_with_logging(params):
        """Wrapper to add logging to objective function."""
        obj_val = _objective_function(params, load_data, config_base, regularization)
        iteration['count'] += 1
        if verbose and iteration['count'] % 10 == 0:
            Lambda_base, a, b, c, d = params
            print(f"Iteration {iteration['count']}: RMSE = {obj_val:.2f} fps, "
                  f"Lambda_base = {Lambda_base:.2f}, coeffs = ({a:.3f}, {b:.3f}, {c:.3f}, {d:.3f})")
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
    Lambda_base_fit, a_fit, b_fit, c_fit, d_fit = result.x
    coeffs_fit = (a_fit, b_fit, c_fit, d_fit)

    # Validate vivacity positivity
    is_positive = validate_vivacity_positive(Lambda_base_fit, coeffs_fit, n_points=100)

    # Compute final residuals and predicted velocities
    predicted_velocities = []
    residuals = []

    for idx, row in load_data.iterrows():
        config = copy(config_base)
        config.charge_mass_gr = row['charge_grains']

        result_sim = solve_ballistics(
            config,
            Lambda_override=Lambda_base_fit,
            coeffs_override=coeffs_fit
        )

        v_pred = result_sim['muzzle_velocity_fps']
        v_obs = row['mean_velocity_fps']
        residual = v_pred - v_obs

        predicted_velocities.append(v_pred)
        residuals.append(residual)

    predicted_velocities = np.array(predicted_velocities)
    residuals = np.array(residuals)

    # Compute weighted RMSE
    if 'velocity_sd' in load_data.columns:
        weights = 1.0 / (load_data['velocity_sd'].values ** 2)
        weights = weights / np.sum(weights) * len(weights)  # Normalize
        rmse = np.sqrt(np.mean(residuals**2 * weights))
    else:
        rmse = np.sqrt(np.mean(residuals**2))

    if verbose:
        print(f"\nFitting complete:")
        print(f"  Lambda_base = {Lambda_base_fit:.2f} s⁻¹ per 100 bar")
        print(f"  Coefficients: ({a_fit:.3f}, {b_fit:.3f}, {c_fit:.3f}, {d_fit:.3f})")
        print(f"  RMSE = {rmse:.2f} fps")
        print(f"  Success: {result.success}")
        print(f"  Vivacity positive: {is_positive}")
        if not is_positive:
            print("  WARNING: Vivacity polynomial has negative values in [0,1]!")

    return {
        'Lambda_base': Lambda_base_fit,
        'coeffs': coeffs_fit,
        'rmse_velocity': rmse,
        'residuals': residuals.tolist(),
        'predicted_velocities': predicted_velocities.tolist(),
        'success': result.success and is_positive,
        'message': result.message,
        'iterations': iteration['count']
    }


def _objective_function(
    params: np.ndarray,
    load_data: pd.DataFrame,
    config_base: BallisticsConfig,
    regularization: float
) -> float:
    """Objective function: weighted velocity RMSE + regularization.

    Parameters
    ----------
    params : np.ndarray
        [Lambda_base, a, b, c, d]
    load_data : pd.DataFrame
        Load ladder data with charge_grains, mean_velocity_fps, velocity_sd (optional)
    config_base : BallisticsConfig
        Base configuration
    regularization : float
        L2 penalty coefficient

    Returns
    -------
    float
        Objective value (weighted RMSE + penalty)
    """
    Lambda_base, a, b, c, d = params
    coeffs = (a, b, c, d)

    # Check vivacity positivity constraint
    if not validate_vivacity_positive(Lambda_base, coeffs, n_points=50):
        return 1e10  # Large penalty for invalid parameters

    residuals = []
    weights = []

    for idx, row in load_data.iterrows():
        # Update charge
        config = copy(config_base)
        config.charge_mass_gr = row['charge_grains']

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

        except (ValueError, RuntimeError) as e:
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
