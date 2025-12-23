"""Tests for io.py CSV parsing and GRT import."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import tempfile
import pytest
import pandas as pd

from ballistics.io import (
    load_chronograph_csv, parse_metadata, metadata_to_config,
    export_fit_results, load_grt_project
)


def test_csv_parsing():
    """Test CSV parsing with metadata extraction."""
    # Create temporary CSV file
    csv_content = """# Cartridge: .308 Winchester
# Barrel Length (in): 24.0
# Cartridge Overall Length (in): 2.810
# Bullet Weight (gr): 175
# Bullet Jacket Type: Copper Jacket over Lead
# Effective Case Volume (gr H2O): 49.47
# Propellant: Varget
# Temperature (°F): 70
# Caliber (in): 0.308
# Initial Pressure (psi): 5000

charge_grains,mean_velocity_fps,velocity_sd,notes
40.0,2575,9,
40.5,2607,11,
41.0,2639,10,
41.5,2671,12,
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(csv_content)
        temp_path = f.name

    try:
        # Load CSV
        metadata, load_data = load_chronograph_csv(temp_path)

        # Check metadata
        assert metadata['cartridge'] == '.308 Winchester'
        assert metadata['barrel_length_in'] == 24.0
        assert metadata['cartridge_overall_length_in'] == 2.810
        assert metadata['bullet_mass_gr'] == 175.0
        assert metadata['case_volume_gr_h2o'] == 49.47
        assert metadata['propellant_name'] == 'Varget'
        assert metadata['bullet_jacket_type'] == 'Copper Jacket over Lead'
        assert metadata['temperature_f'] == 70.0
        assert metadata['caliber_in'] == 0.308

        # Check load data
        assert len(load_data) == 4
        assert list(load_data.columns) == ['charge_grains', 'mean_velocity_fps', 'velocity_sd', 'notes']
        assert load_data['charge_grains'].tolist() == [40.0, 40.5, 41.0, 41.5]
        assert load_data['mean_velocity_fps'].tolist() == [2575, 2607, 2639, 2671]

    finally:
        os.unlink(temp_path)


def test_parse_metadata():
    """Test metadata parsing and validation."""
    metadata_raw = {
        'Cartridge': '.308 Winchester',
        'Barrel Length (in)': '24.0',
        'Cartridge Overall Length (in)': '2.810',
        'Bullet Weight (gr)': '175',
        'Bullet Jacket Type': 'Copper Jacket over Lead',
        'Effective Case Volume (gr H2O)': '49.47',
        'Propellant': 'Varget',
        'Temperature (°F)': '70',
        'Caliber (in)': '0.308'
    }

    metadata = parse_metadata(metadata_raw)

    assert metadata['cartridge'] == '.308 Winchester'
    assert metadata['barrel_length_in'] == 24.0
    assert metadata['bullet_mass_gr'] == 175.0
    assert metadata['propellant_name'] == 'Varget'


def test_parse_metadata_missing_field():
    """Test that missing required field raises error."""
    metadata_raw = {
        'Cartridge': '.308 Winchester',
        'Barrel Length (in)': '24.0',
        # Missing Cartridge Overall Length
    }

    with pytest.raises(ValueError, match="Missing required metadata field"):
        parse_metadata(metadata_raw)


def test_metadata_to_config():
    """Test conversion of metadata to BallisticsConfig."""
    metadata = {
        'cartridge': '.308 Winchester',
        'barrel_length_in': 24.0,
        'cartridge_overall_length_in': 2.810,
        'bullet_mass_gr': 175.0,
        'case_volume_gr_h2o': 49.47,
        'propellant_name': 'Varget',
        'bullet_jacket_type': 'Copper Jacket over Lead',
        'temperature_f': 70.0,
        'p_initial_psi': 5000.0,
        'caliber_in': 0.308
    }

    config = metadata_to_config(metadata)

    assert config.bullet_mass_gr == 175.0
    assert config.barrel_length_in == 24.0
    assert config.cartridge_overall_length_in == 2.810
    assert config.caliber_in == 0.308
    assert config.case_volume_gr_h2o == 49.47
    assert config.propellant.name == 'Varget'
    assert config.bullet.name == 'Copper Jacket over Lead'
    assert config.temperature_f == 70.0


def test_metadata_to_config_invalid_propellant():
    """Test that invalid propellant name raises error with helpful message."""
    metadata = {
        'cartridge': '.308 Winchester',
        'barrel_length_in': 24.0,
        'cartridge_overall_length_in': 2.810,
        'bullet_mass_gr': 175.0,
        'case_volume_gr_h2o': 49.47,
        'propellant_name': 'InvalidPropellant123',
        'bullet_jacket_type': 'Copper Jacket over Lead',
        'temperature_f': 70.0,
        'p_initial_psi': 5000.0,
        'caliber_in': 0.308
    }

    with pytest.raises(ValueError, match="not found in database"):
        metadata_to_config(metadata)


def test_export_fit_results_json():
    """Test exporting fit results to JSON."""
    fit_result = {
        'Lambda_base': 63.5,
        'coeffs': (1.040, -0.614, 0.225, -0.005),
        'rmse_velocity': 8.3,
        'residuals': [1.2, -0.5, 0.3],
        'predicted_velocities': [2575.0, 2607.0, 2639.0],
        'success': True,
        'message': 'Optimization terminated successfully.',
        'iterations': 150
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = f.name

    try:
        export_fit_results(fit_result, temp_path, format='json', propellant_name='Varget')

        # Read back and verify
        import json
        with open(temp_path, 'r') as f:
            data = json.load(f)

        assert data['Lambda_base'] == 63.5
        assert data['coeffs'] == [1.040, -0.614, 0.225, -0.005]
        assert data['rmse_velocity'] == 8.3
        assert data['propellant'] == 'Varget'
        assert data['success'] is True

    finally:
        os.unlink(temp_path)


def test_export_fit_results_python():
    """Test exporting fit results to Python snippet."""
    fit_result = {
        'Lambda_base': 63.5,
        'coeffs': (1.040, -0.614, 0.225, -0.005),
        'rmse_velocity': 8.3,
        'success': True,
        'iterations': 150
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        temp_path = f.name

    try:
        export_fit_results(fit_result, temp_path, format='python', propellant_name='Varget')

        # Read back and verify
        with open(temp_path, 'r') as f:
            content = f.read()

        assert 'update_propellant_coefficients' in content
        assert 'Varget' in content
        assert '63.5' in content
        assert 'RMSE: 8.3' in content

    finally:
        os.unlink(temp_path)


def test_grt_import():
    """Test loading GRT project file."""
    grt_path = os.path.join(
        os.path.dirname(__file__), '..',
        '65CRM_130SMK_N150_Starline_Initial.grtload'
    )

    if not os.path.exists(grt_path):
        pytest.skip(f"GRT test file not found: {grt_path}")

    metadata, load_data = load_grt_project(grt_path)

    # Check metadata extraction
    assert 'barrel_length_in' in metadata
    assert 'cartridge_overall_length_in' in metadata
    assert 'bullet_mass_gr' in metadata
    assert 'case_volume_gr_h2o' in metadata
    assert 'propellant_name' in metadata
    assert 'caliber_in' in metadata

    # Values should be positive
    assert metadata['barrel_length_in'] > 0
    assert metadata['bullet_mass_gr'] > 0
    assert metadata['case_volume_gr_h2o'] > 0
    assert metadata['caliber_in'] > 0

    # Check load data structure
    if len(load_data) > 0:
        assert 'charge_grains' in load_data.columns
        assert 'mean_velocity_fps' in load_data.columns
        assert 'velocity_sd' in load_data.columns
        assert 'notes' in load_data.columns

        # Values should be positive
        assert (load_data['charge_grains'] > 0).all()
        assert (load_data['mean_velocity_fps'] > 0).all()
        assert (load_data['velocity_sd'] >= 0).all()


def test_grt_to_config():
    """Test full pipeline: GRT -> metadata -> config."""
    grt_path = os.path.join(
        os.path.dirname(__file__), '..',
        '65CRM_130SMK_N150_Starline_Initial.grtload'
    )

    if not os.path.exists(grt_path):
        pytest.skip(f"GRT test file not found: {grt_path}")

    metadata, load_data = load_grt_project(grt_path)

    # Should be able to create config (propellant must exist in database)
    try:
        config = metadata_to_config(metadata)
        assert config.bullet_mass_gr > 0
        assert config.barrel_length_in > 0
    except ValueError as e:
        # Propellant might not be in database, that's OK for this test
        if 'not found in database' in str(e):
            pytest.skip(f"Propellant {metadata['propellant_name']} not in test database")
        else:
            raise


def test_csv_validation_negative_charge():
    """Test that negative charge values raise error."""
    csv_content = """# Cartridge: .308 Winchester
# Barrel Length (in): 24.0
# Cartridge Overall Length (in): 2.810
# Bullet Weight (gr): 175
# Bullet Jacket Type: Copper Jacket over Lead
# Effective Case Volume (gr H2O): 49.47
# Propellant: Varget
# Caliber (in): 0.308

charge_grains,mean_velocity_fps
-40.0,2575
41.0,2639
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(csv_content)
        temp_path = f.name

    try:
        with pytest.raises(ValueError, match="charge_grains values must be positive"):
            load_chronograph_csv(temp_path)
    finally:
        os.unlink(temp_path)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
