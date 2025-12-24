"""Tests for plotting module."""

import pytest
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from unittest.mock import patch, Mock

from ballistics.analysis.plotting import plot_velocity_fit, plot_burnout_map


class TestPlotVelocityFit:
    """Test velocity fit plotting functionality."""

    @patch("ballistics.analysis.plotting.plt")
    def test_plot_velocity_fit_basic(self, mock_plt):
        """Test basic velocity fit plotting."""
        # Mock fit results
        fit_results = {
            "rmse_velocity": 25.3,
            "residuals": [-10, 5, -3, 8],
            "predicted_velocities": [2580, 2620, 2660, 2700],
        }

        # Mock load data
        load_data = pd.DataFrame(
            {
                "charge_grains": [40, 41, 42, 43],
                "mean_velocity_fps": [2570, 2625, 2657, 2708],
                "velocity_sd": [5, 6, 4, 7],
            }
        )

        # Mock subplots
        mock_fig = Mock()
        mock_ax1 = Mock()
        mock_ax2 = Mock()
        mock_plt.subplots.return_value = (mock_fig, (mock_ax1, mock_ax2))
        mock_plt.ioff.return_value = None

        result = plot_velocity_fit(fit_results, load_data)

        assert result == mock_fig
        mock_plt.subplots.assert_called_once()
        mock_ax1.errorbar.assert_called_once()
        mock_ax1.plot.assert_called_once()
        mock_ax2.scatter.assert_called_once()

    @patch("ballistics.analysis.plotting.plt")
    def test_plot_with_save_path(self, mock_plt):
        """Test plotting with save path."""
        fit_results = {
            "rmse_velocity": 20.0,
            "residuals": [0, 0],
            "predicted_velocities": [2500, 2600],
        }

        load_data = pd.DataFrame(
            {"charge_grains": [40, 42], "mean_velocity_fps": [2500, 2600]}
        )

        mock_fig = Mock()
        mock_plt.subplots.return_value = (mock_fig, (Mock(), Mock()))
        mock_plt.ioff.return_value = None

        result = plot_velocity_fit(fit_results, load_data, save_path="test.png")

        mock_fig.savefig.assert_called_once_with(
            "test.png", dpi=150, bbox_inches="tight"
        )


class TestPlotBurnoutMap:
    """Test burnout map plotting functionality."""

    @patch("ballistics.analysis.plotting.plt")
    def test_plot_burnout_map_charge(self, mock_plt):
        """Test burnout map plotting for charge sweep."""
        analysis_df = pd.DataFrame(
            {
                "charge_grains": [40, 41, 42],
                "muzzle_velocity_fps": [2500, 2550, 2600],
                "peak_pressure_psi": [45000, 47000, 49000],
                "final_Z": [0.8, 0.85, 0.9],
                "burnout_distance_from_bolt_in": [16.5, 17.2, 17.8],
            }
        )

        mock_fig = Mock()
        mock_ax1 = Mock()
        mock_ax2 = Mock()
        mock_plt.subplots.return_value = (mock_fig, mock_ax1)
        mock_ax1.twinx.return_value = mock_ax2
        mock_plt.ioff.return_value = None

        result = plot_burnout_map(analysis_df, x_col="charge_grains")

        assert result == mock_fig
        mock_ax1.plot.assert_called()
        mock_ax2.plot.assert_called()

    @patch("ballistics.analysis.plotting.plt")
    def test_plot_burnout_map_barrel(self, mock_plt):
        """Test burnout map plotting for barrel sweep."""
        analysis_df = pd.DataFrame(
            {
                "barrel_length_in": [20, 22, 24],
                "muzzle_velocity_fps": [2450, 2550, 2600],
                "peak_pressure_psi": [48000, 50000, 51000],
                "final_Z": [0.9, 0.95, 1.0],
                "burnout_distance_from_bolt_in": [18.0, 20.5, 22.0],
            }
        )

        mock_fig = Mock()
        mock_ax1 = Mock()
        mock_ax2 = Mock()
        mock_plt.subplots.return_value = (mock_fig, mock_ax1)
        mock_ax1.twinx.return_value = mock_ax2
        mock_plt.ioff.return_value = None

        result = plot_burnout_map(
            analysis_df, x_col="barrel_length_in", save_path="barrel.png"
        )

        assert result == mock_fig
        mock_fig.savefig.assert_called_once_with(
            "barrel.png", dpi=150, bbox_inches="tight"
        )
