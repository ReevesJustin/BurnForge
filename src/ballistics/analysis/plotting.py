"""Plotting utilities for ballistics analysis.

This module provides matplotlib-based plotting functions for visualizing
vivacity curves, velocity fits, and burnout maps. All plots are designed
for non-interactive use and save to PNG files.
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from typing import Optional, Dict, Any
from matplotlib.figure import Figure

from ballistics.core.props import BallisticsConfig


def plot_velocity_fit(
    fit_results: Dict[str, Any],
    load_data: pd.DataFrame,
    save_path: Optional[str] = None,
    **kwargs,
) -> Figure:
    """Plot velocity fit with error bars and residuals.

    Parameters
    ----------
    fit_results : dict
        Results from fit_vivacity_polynomial
    load_data : pd.DataFrame
        Original load data
    save_path : str, optional
        Path to save PNG file
    **kwargs
        Additional plot styling options

    Returns
    -------
    plt.Figure
        Matplotlib figure object
    """
    plt.ioff()

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), height_ratios=[3, 1])

    # Main velocity plot
    charges = load_data["charge_grains"]
    measured_vel = load_data["mean_velocity_fps"]
    predicted_vel = fit_results["predicted_velocities"]
    residuals = fit_results["residuals"]

    # Plot data
    ax1.errorbar(
        charges,
        measured_vel,
        yerr=load_data.get("velocity_sd", 0),
        fmt="ko",
        markersize=4,
        capsize=3,
        label="Measured",
        alpha=0.7,
    )

    ax1.plot(charges, predicted_vel, "r-", linewidth=2, label="Fitted")

    # Styling
    ax1.set_ylabel("Velocity (fps)")
    ax1.set_title(f"Velocity Fit - RMSE: {fit_results['rmse_velocity']:.1f} fps")
    ax1.grid(True, alpha=0.3)
    ax1.legend()

    # Residual plot
    ax2.scatter(charges, residuals, c="blue", alpha=0.7)
    ax2.axhline(y=0, color="r", linestyle="--", alpha=0.7)
    ax2.set_xlabel("Charge (grains)")
    ax2.set_ylabel("Residual (fps)")
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")

    return fig


def plot_burnout_map(
    analysis_df: pd.DataFrame,
    x_col: str = "charge_grains",
    save_path: Optional[str] = None,
    **kwargs,
) -> Figure:
    """Plot burnout map with dual y-axes.

    Parameters
    ----------
    analysis_df : pd.DataFrame
        Results from analysis functions
    x_col : str
        Column for x-axis ('charge_grains' or 'barrel_length_in')
    save_path : str, optional
        Path to save PNG file
    **kwargs
        Additional plot styling options

    Returns
    -------
    plt.Figure
        Matplotlib figure object
    """
    plt.ioff()

    fig, ax1 = plt.subplots(figsize=(10, 6))

    # Primary y-axis: velocity
    color1 = "tab:blue"
    ax1.set_xlabel(f"{x_col.replace('_', ' ').title()}")
    ax1.set_ylabel("Velocity (fps)", color=color1)
    ax1.plot(
        analysis_df[x_col],
        analysis_df["muzzle_velocity_fps"],
        color=color1,
        linewidth=2,
        marker="o",
        markersize=4,
    )
    ax1.tick_params(axis="y", labelcolor=color1)

    # Secondary y-axis: burnout metrics
    ax2 = ax1.twinx()
    color2 = "tab:red"
    ax2.set_ylabel("Burnout Distance (in)", color=color2)

    # Plot burnout distance where available
    valid_burnout = analysis_df.dropna(subset=["burnout_distance_from_bolt_in"])
    if not valid_burnout.empty:
        ax2.plot(
            valid_burnout[x_col],
            valid_burnout["burnout_distance_from_bolt_in"],
            color=color2,
            linewidth=2,
            marker="s",
            markersize=4,
            linestyle="--",
        )

    ax2.tick_params(axis="y", labelcolor=color2)

    # Title
    title_suffix = "Charge Sweep" if x_col == "charge_grains" else "Barrel Sweep"
    plt.title(f"Burnout Map - {title_suffix}")

    # Grid
    ax1.grid(True, alpha=0.3)

    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")

    return fig
