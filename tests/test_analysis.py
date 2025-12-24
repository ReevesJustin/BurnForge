"""Tests for analysis module."""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock

from ballistics.analysis.analysis import (
    burnout_scan_charge,
    burnout_scan_barrel,
    charge_ladder_analysis,
)


class TestBurnoutScanCharge:
    """Test charge weight scanning functionality."""

    def test_basic_scan(self):
        """Test basic charge scan with mock solver."""
        # Mock config and solver
        mock_config = Mock()
        mock_config.model_copy.return_value = mock_config

        # Mock solve_ballistics to return test data
        mock_results = {
            "muzzle_velocity_fps": 2500.0,
            "peak_pressure_psi": 50000.0,
            "final_Z": 0.8,
            "burnout_distance_from_bolt_in": None,
        }

        from ballistics.core.solver import solve_ballistics

        original_solve = solve_ballistics
        solve_ballistics_mock = Mock(return_value=mock_results)

        # Patch the function
        import ballistics.analysis.analysis

        ballistics.analysis.analysis.solve_ballistics = solve_ballistics_mock

        try:
            result = burnout_scan_charge(mock_config, (40.0, 45.0), 3)

            assert isinstance(result, pd.DataFrame)
            assert len(result) == 3
            assert "charge_grains" in result.columns
            assert "muzzle_velocity_fps" in result.columns
            assert result["charge_grains"].tolist() == [40.0, 42.5, 45.0]

            # Verify solver was called 3 times
            assert solve_ballistics_mock.call_count == 3

        finally:
            # Restore original
            ballistics.analysis.analysis.solve_ballistics = original_solve

    def test_solver_failure_handling(self):
        """Test handling of solver failures."""
        mock_config = Mock()
        mock_config.model_copy.return_value = mock_config

        from ballistics.core.solver import solve_ballistics

        original_solve = solve_ballistics
        solve_ballistics_mock = Mock(side_effect=Exception("Solver failed"))

        import ballistics.analysis.analysis

        ballistics.analysis.analysis.solve_ballistics = solve_ballistics_mock

        try:
            result = burnout_scan_charge(mock_config, (40.0, 42.0), 2)

            assert len(result) == 2
            assert pd.isna(result.iloc[0]["muzzle_velocity_fps"])
            assert pd.isna(result.iloc[0]["peak_pressure_psi"])

        finally:
            ballistics.analysis.analysis.solve_ballistics = original_solve


class TestBurnoutScanBarrel:
    """Test barrel length scanning functionality."""

    def test_barrel_scan(self):
        """Test barrel length scanning."""
        mock_config = Mock()
        mock_config.model_copy.return_value = mock_config

        mock_results = {
            "muzzle_velocity_fps": 2600.0,
            "peak_pressure_psi": 55000.0,
            "final_Z": 1.0,
            "burnout_distance_from_bolt_in": 18.5,
        }

        from ballistics.core.solver import solve_ballistics

        original_solve = solve_ballistics
        solve_ballistics_mock = Mock(return_value=mock_results)

        import ballistics.analysis.analysis

        ballistics.analysis.analysis.solve_ballistics = solve_ballistics_mock

        try:
            result = burnout_scan_barrel(mock_config, (20.0, 24.0), 3)

            assert isinstance(result, pd.DataFrame)
            assert len(result) == 3
            assert "barrel_length_in" in result.columns
            assert result["barrel_length_in"].tolist() == [20.0, 22.0, 24.0]
            assert result.iloc[0]["burnout_distance_from_bolt_in"] == 18.5

        finally:
            ballistics.analysis.analysis.solve_ballistics = original_solve


class TestChargeLadderAnalysis:
    """Test charge ladder analysis with target velocity."""

    def test_target_velocity_interpolation(self):
        """Test interpolation for target velocity."""
        mock_config = Mock()
        mock_config.model_copy.return_value = mock_config

        # Mock results with increasing velocity
        results_data = [
            {
                "muzzle_velocity_fps": 2400.0,
                "peak_pressure_psi": 45000.0,
                "final_Z": 0.6,
                "burnout_distance_from_bolt_in": None,
            },
            {
                "muzzle_velocity_fps": 2500.0,
                "peak_pressure_psi": 48000.0,
                "final_Z": 0.7,
                "burnout_distance_from_bolt_in": None,
            },
            {
                "muzzle_velocity_fps": 2600.0,
                "peak_pressure_psi": 51000.0,
                "final_Z": 0.8,
                "burnout_distance_from_bolt_in": None,
            },
        ]

        from ballistics.core.solver import solve_ballistics

        original_solve = solve_ballistics
        solve_ballistics_mock = Mock(side_effect=results_data)

        import ballistics.analysis.analysis

        ballistics.analysis.analysis.solve_ballistics = solve_ballistics_mock

        try:
            result = charge_ladder_analysis(
                mock_config, (40.0, 42.0), target_velocity_fps=2450.0, n_points=2
            )

            assert isinstance(result, pd.DataFrame)
            assert len(result) >= 3  # Original 2 + interpolated 1
            assert 2450.0 in result["muzzle_velocity_fps"].values

        finally:
            ballistics.analysis.analysis.solve_ballistics = original_solve
