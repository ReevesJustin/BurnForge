"""Analysis tools for ballistics simulations.

This module provides functions for scanning parameter spaces and analyzing
ballistics behavior across different operating conditions.
"""

import numpy as np
import pandas as pd
from typing import Tuple

from copy import deepcopy as copy
from ballistics.core.solver import solve_ballistics
from ballistics.core.props import BallisticsConfig


def burnout_scan_charge(
    config: BallisticsConfig, charge_range: Tuple[float, float], n_points: int = 20
) -> pd.DataFrame:
    """Sweep charge weights and compute burnout metrics for each.

    Parameters
    ----------
    config : BallisticsConfig
        Base configuration to modify
    charge_range : tuple of float
        (min_charge_grains, max_charge_grains)
    n_points : int
        Number of charge weights to test

    Returns
    -------
    pd.DataFrame
        Columns: charge_grains, muzzle_velocity_fps, peak_pressure_psi,
        final_Z, burnout_distance_from_bolt_in, muzzle_burn_percentage
    """
    charges = np.linspace(charge_range[0], charge_range[1], n_points)
    results = []

    for charge in charges:
        config_scan = copy(config)
        config_scan.charge_mass_gr = charge

        try:
            sol = solve_ballistics(config_scan)
            final_Z = sol["final_Z"]
            muzzle_velocity = sol["muzzle_velocity_fps"]
            peak_pressure = sol["peak_pressure_psi"]

            # Compute burnout metrics
            if final_Z >= 1.0:
                # Fully burned out - find burnout distance
                burnout_distance = sol["burnout_distance_from_bolt_in"]
                muzzle_burn_percentage = 100.0
            else:
                # Not fully burned - compute percentage at muzzle
                burnout_distance = np.nan
                muzzle_burn_percentage = final_Z * 100.0

            results.append(
                {
                    "charge_grains": charge,
                    "muzzle_velocity_fps": muzzle_velocity,
                    "peak_pressure_psi": peak_pressure,
                    "final_Z": final_Z,
                    "burnout_distance_from_bolt_in": burnout_distance,
                    "muzzle_burn_percentage": muzzle_burn_percentage,
                }
            )

        except Exception as e:
            # If solver fails, add NaN results
            results.append(
                {
                    "charge_grains": charge,
                    "muzzle_velocity_fps": np.nan,
                    "peak_pressure_psi": np.nan,
                    "final_Z": np.nan,
                    "burnout_distance_from_bolt_in": np.nan,
                    "muzzle_burn_percentage": np.nan,
                }
            )

    return pd.DataFrame(results)


def burnout_scan_barrel(
    config: BallisticsConfig, barrel_range: Tuple[float, float], n_points: int = 20
) -> pd.DataFrame:
    """Sweep barrel lengths and compute burnout metrics for each.

    Parameters
    ----------
    config : BallisticsConfig
        Base configuration to modify
    barrel_range : tuple of float
        (min_barrel_in, max_barrel_in)
    n_points : int
        Number of barrel lengths to test

    Returns
    -------
    pd.DataFrame
        Columns: barrel_length_in, muzzle_velocity_fps, peak_pressure_psi,
        final_Z, burnout_distance_from_bolt_in, muzzle_burn_percentage
    """
    barrels = np.linspace(barrel_range[0], barrel_range[1], n_points)
    results = []

    for barrel in barrels:
        config_scan = copy(config)
        config_scan.barrel_length_in = barrel

        try:
            sol = solve_ballistics(config_scan)
            final_Z = sol["final_Z"]
            muzzle_velocity = sol["muzzle_velocity_fps"]
            peak_pressure = sol["peak_pressure_psi"]

            # Compute burnout metrics
            if final_Z >= 1.0:
                burnout_distance = sol["burnout_distance_from_bolt_in"]
                muzzle_burn_percentage = 100.0
            else:
                burnout_distance = np.nan
                muzzle_burn_percentage = final_Z * 100.0

            results.append(
                {
                    "barrel_length_in": barrel,
                    "muzzle_velocity_fps": muzzle_velocity,
                    "peak_pressure_psi": peak_pressure,
                    "final_Z": final_Z,
                    "burnout_distance_from_bolt_in": burnout_distance,
                    "muzzle_burn_percentage": muzzle_burn_percentage,
                }
            )

        except Exception as e:
            results.append(
                {
                    "barrel_length_in": barrel,
                    "muzzle_velocity_fps": np.nan,
                    "peak_pressure_psi": np.nan,
                    "final_Z": np.nan,
                    "burnout_distance_from_bolt_in": np.nan,
                    "muzzle_burn_percentage": np.nan,
                }
            )

    return pd.DataFrame(results)


def charge_ladder_analysis(
    config: BallisticsConfig,
    charge_range: Tuple[float, float],
    target_velocity_fps: float | None = None,
    n_points: int = 20,
) -> pd.DataFrame:
    """Analyze charge ladder with optional target velocity interpolation.

    Parameters
    ----------
    config : BallisticsConfig
        Base configuration to modify
    charge_range : tuple of float
        (min_charge_grains, max_charge_grains)
    target_velocity_fps : float, optional
        If provided, interpolate charge weight for target velocity
    n_points : int
        Number of charge weights to test

    Returns
    -------
    pd.DataFrame
        Charge ladder results with interpolated target if requested
    """
    results_df = burnout_scan_charge(config, charge_range, n_points)

    if target_velocity_fps is not None:
        # Interpolate charge for target velocity
        valid_data = results_df.dropna(subset=["muzzle_velocity_fps", "charge_grains"])
        if len(valid_data) >= 2:
            target_charge = np.interp(
                target_velocity_fps,
                valid_data["muzzle_velocity_fps"],
                valid_data["charge_grains"],
            )

            # Add interpolated point to results
            interp_row = pd.DataFrame(
                [
                    {
                        "charge_grains": target_charge,
                        "muzzle_velocity_fps": target_velocity_fps,
                        "peak_pressure_psi": np.nan,
                        "final_Z": np.nan,
                        "burnout_distance_from_bolt_in": np.nan,
                        "muzzle_burn_percentage": np.nan,
                    }
                ]
            )
            results_df = pd.concat([results_df, interp_row], ignore_index=True)

    return results_df.sort_values("charge_grains")
