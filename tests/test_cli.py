"""Tests for CLI module."""

import pytest
import pandas as pd
from unittest.mock import patch, Mock
from typer.testing import CliRunner

from ballistics.cli.main import app


class TestCLI:
    """Test CLI commands."""

    def setup_method(self):
        """Set up test runner."""
        self.runner = CliRunner()

    @patch("ballistics.cli.main.load_grt_project")
    @patch("ballistics.cli.main.metadata_to_config")
    @patch("ballistics.cli.main.fit_vivacity_polynomial")
    def test_fit_command(self, mock_fit, mock_config, mock_load):
        """Test fit command."""
        # Mock data
        mock_load.return_value = (
            {"cartridge": "test"},
            pd.DataFrame(
                {"charge_grains": [40, 42], "mean_velocity_fps": [2500, 2600]}
            ),
        )
        mock_config.return_value = Mock()
        mock_fit.return_value = {"rmse_velocity": 25.0, "Lambda_base": 0.05}

        result = self.runner.invoke(app, ["fit", "test.grtload"])

        assert result.exit_code == 0
        assert "Fitted Lambda_base" in result.output
        mock_fit.assert_called_once()

    @patch("ballistics.cli.main.solve_ballistics")
    @patch("ballistics.cli.main.load_grt_project")
    @patch("ballistics.cli.main.metadata_to_config")
    def test_simulate_command(self, mock_config, mock_load, mock_solve):
        """Test simulate command."""
        mock_load.return_value = ({"cartridge": "test"}, pd.DataFrame())
        mock_config.return_value = Mock()
        mock_solve.return_value = {
            "muzzle_velocity_fps": 2550.0,
            "peak_pressure_psi": 50000.0,
        }

        result = self.runner.invoke(app, ["simulate", "test.grtload"])

        assert result.exit_code == 0
        assert "2550.0 fps" in result.output
        mock_solve.assert_called_once()

    @patch("ballistics.cli.main.burnout_scan_charge")
    @patch("ballistics.cli.main.load_grt_project")
    @patch("ballistics.cli.main.metadata_to_config")
    def test_scan_charge_command(self, mock_config, mock_load, mock_scan):
        """Test scan-charge command."""
        mock_load.return_value = ({"cartridge": "test"}, pd.DataFrame())
        mock_config.return_value = Mock()
        mock_scan.return_value = pd.DataFrame(
            {"charge_grains": [40, 42], "muzzle_velocity_fps": [2500, 2600]}
        )

        result = self.runner.invoke(
            app,
            ["scan-charge", "test.grtload", "--min-charge", "40", "--max-charge", "42"],
        )

        assert result.exit_code == 0
        assert "Scan complete" in result.output
        mock_scan.assert_called_once()

    def test_import_grt_not_implemented(self):
        """Test import-grt command (not implemented)."""
        result = self.runner.invoke(app, ["import-grt", "test.grtload"])

        assert result.exit_code == 1
        assert "not yet implemented" in result.output
