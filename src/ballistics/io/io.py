"""CSV/JSON loaders with metadata parsing and result exporters."""

import json
import xml.etree.ElementTree as ET
from io import StringIO
import pandas as pd

from ..core.props import BallisticsConfig, PropellantProperties, BulletProperties
from ..database.database import list_propellants
from ..utils.utils import (
    MM_TO_IN,
    GRAMS_TO_GRAINS,
    KG_TO_GRAINS,
    CM3_TO_GRAINS_H2O,
    MS_TO_FPS,
    BAR_TO_PSI,
)


def load_chronograph_csv(filepath: str) -> tuple[dict, pd.DataFrame]:
    """Load chronograph data CSV with metadata and load ladder.

    Parameters
    ----------
    filepath : str
        Path to CSV file following standardized format

    Returns
    -------
    tuple
        (metadata: dict, load_data: pd.DataFrame)
        metadata includes: cartridge, barrel_length_in, bullet_mass_gr, propellant_name, etc.
        load_data columns: charge_grains, mean_velocity_fps, velocity_sd, notes
    """
    metadata = {}
    data_lines = []

    with open(filepath, "r") as f:
        for line in f:
            if line.startswith("#"):
                # Parse metadata: # Key: Value
                if ":" in line:
                    key, value = line[1:].split(":", 1)
                    metadata[key.strip()] = value.strip()
            else:
                data_lines.append(line)

    # Parse metadata
    metadata = parse_metadata(metadata)

    # Load data
    load_data = pd.read_csv(StringIO("".join(data_lines)))

    # Validate required columns
    required_cols = ["charge_grains", "mean_velocity_fps"]
    for col in required_cols:
        if col not in load_data.columns:
            raise ValueError(f"Missing required column in CSV: {col}")

    # Validate data
    if load_data["charge_grains"].min() <= 0:
        raise ValueError("All charge_grains values must be positive")
    if load_data["mean_velocity_fps"].min() <= 0:
        raise ValueError("All mean_velocity_fps values must be positive")

    return metadata, load_data


def parse_metadata(metadata_raw: dict) -> dict:
    """Parse metadata comment lines from CSV header.

    Parameters
    ----------
    metadata_raw : dict
        Raw key-value pairs from CSV header comments

    Returns
    -------
    dict
        Validated and converted metadata
    """
    # Required fields
    required_fields = [
        "Barrel Length (in)",
        "Cartridge Overall Length (in)",
        "Bullet Weight (gr)",
        "Effective Case Volume (gr H2O)",
        "Propellant",
        "Bullet Jacket Type",
    ]

    for field in required_fields:
        if field not in metadata_raw:
            raise ValueError(f"Missing required metadata field: {field}")

    # Extract and convert values
    metadata = {
        "cartridge": metadata_raw.get("Cartridge", "Unknown"),
        "barrel_length_in": float(metadata_raw["Barrel Length (in)"]),
        "cartridge_overall_length_in": float(
            metadata_raw["Cartridge Overall Length (in)"]
        ),
        "bullet_mass_gr": float(metadata_raw["Bullet Weight (gr)"]),
        "case_volume_gr_h2o": float(metadata_raw["Effective Case Volume (gr H2O)"]),
        "propellant_name": metadata_raw["Propellant"],
        "bullet_jacket_type": metadata_raw["Bullet Jacket Type"],
        "temperature_f": float(metadata_raw.get("Temperature (°F)", 70.0)),
        "p_initial_psi": float(metadata_raw.get("Initial Pressure (psi)", 5000.0)),
        "caliber_in": float(metadata_raw.get("Caliber (in)", 0.308)),  # Optional
    }

    return metadata


def metadata_to_config(metadata: dict, db_path: str | None = None) -> BallisticsConfig:
    """Convert parsed metadata dict to BallisticsConfig.

    Parameters
    ----------
    metadata : dict
        Metadata from parse_metadata or load_grt_project
    db_path : str, optional
        Path to database (uses default if None)

    Returns
    -------
    BallisticsConfig
        Complete configuration for solver
    """
    # Load propellant from database
    try:
        propellant = PropellantProperties.from_database(
            metadata["propellant_name"], db_path=db_path
        )
    except ValueError as e:
        available = list_propellants(db_path=db_path)
        raise ValueError(
            f"Propellant '{metadata['propellant_name']}' not found in database. "
            f"Available propellants: {', '.join(available[:10])}..."
        ) from e

    # Load bullet type from database
    try:
        bullet = BulletProperties.from_database(
            metadata["bullet_jacket_type"], db_path=db_path
        )
    except ValueError as e:
        raise ValueError(
            f"Bullet jacket type '{metadata['bullet_jacket_type']}' not found in database. "
            f"Common types: 'Copper Jacket over Lead', 'Solid Copper', 'Lead'"
        ) from e

    # Create config
    config = BallisticsConfig(
        bullet_mass_gr=metadata["bullet_mass_gr"],
        charge_mass_gr=metadata.get(
            "charge_mass_gr", 40.0
        ),  # Will be overridden in fitting
        caliber_in=metadata["caliber_in"],
        case_volume_gr_h2o=metadata["case_volume_gr_h2o"],
        barrel_length_in=metadata["barrel_length_in"],
        cartridge_overall_length_in=metadata["cartridge_overall_length_in"],
        propellant=propellant,
        bullet=bullet,
        temperature_f=metadata.get("temperature_f", 70.0),
        p_initial_psi=metadata.get(
            "p_initial_psi"
        ),  # Uses bullet.p_initial_psi if None
    )

    return config


def export_fit_results(
    fit_result: dict,
    output_path: str,
    format: str = "json",
    propellant_name: str | None = None,
) -> None:
    """Export fitting results to JSON or Python dict snippet.

    Parameters
    ----------
    fit_result : dict
        Output from fit_vivacity_polynomial
    output_path : str
        Output file path
    format : str
        'json' or 'python' (for database update snippet)
    propellant_name : str, optional
        Propellant name (required for 'python' format)
    """
    if format == "json":
        output = {
            "Lambda_base": fit_result["Lambda_base"],
            "coeffs": list(fit_result["coeffs"]),
            "rmse_velocity": fit_result["rmse_velocity"],
            "success": fit_result["success"],
            "iterations": fit_result["iterations"],
        }
        if propellant_name:
            output["propellant"] = propellant_name

        with open(output_path, "w") as f:
            json.dump(output, f, indent=2)

    elif format == "python":
        if not propellant_name:
            raise ValueError("propellant_name required for 'python' format")

        a, b, c, d = fit_result["coeffs"]
        snippet = f"""# Update database with fitted coefficients
from ballistics.database import update_propellant_coefficients

update_propellant_coefficients(
    name="{propellant_name}",
    Lambda_base={fit_result["Lambda_base"]:.4f},
    coeffs=({a:.6f}, {b:.6f}, {c:.6f}, {d:.6f})
)
# RMSE: {fit_result["rmse_velocity"]:.2f} fps
# Iterations: {fit_result["iterations"]}
"""
        with open(output_path, "w") as f:
            f.write(snippet)

    else:
        raise ValueError(f"Unknown format: {format}. Use 'json' or 'python'.")


def load_grt_project(filepath: str) -> tuple[dict, pd.DataFrame]:
    """Load chronograph data from Gordon's Reloading Tool (GRT) project file.

    GRT project files (.grtload, .grtproject) are XML-based. Extracts metadata
    and measurement charges, returns same format as load_chronograph_csv() for
    pipeline compatibility.

    Parameters
    ----------
    filepath : str
        Path to GRT project file (.grtload or .grtproject)

    Returns
    -------
    tuple
        (metadata: dict, load_data: pd.DataFrame)
        metadata includes: cartridge, barrel_length_in, bullet_mass_gr, propellant_name,
                          cartridge_overall_length_in, case_volume_gr_h2o, etc.
        load_data columns: charge_grains, mean_velocity_fps, velocity_sd, notes
        Returns (metadata, empty DataFrame) if no measurement charges present
    """
    # Parse XML
    tree = ET.parse(filepath)
    root = tree.getroot()

    # Helper function to get input value
    def get_input_value(name, required=True, default=None):
        elem = root.find(f".//input[@name='{name}']")
        if elem is None:
            if required:
                raise ValueError(f"Required field '{name}' not found in GRT file")
            return default
        return elem.get("value")

    # Barrel length (xe in mm)
    barrel_length_mm = float(get_input_value("xe"))
    barrel_length_in = barrel_length_mm * MM_TO_IN

    # COAL (oal in mm)
    coal_mm = float(get_input_value("oal"))
    coal_in = coal_mm * MM_TO_IN

    # Case volume (casevol in cm³)
    casevol_cm3 = float(get_input_value("casevol"))
    casevol_gr_h2o = casevol_cm3 * CM3_TO_GRAINS_H2O

    # Bullet mass (mp in grams)
    bullet_mass_g = float(get_input_value("mp"))
    bullet_mass_gr = bullet_mass_g * GRAMS_TO_GRAINS

    # Caliber diameter (Dz in mm)
    caliber_mm = float(get_input_value("Dz"))
    caliber_in = caliber_mm * MM_TO_IN

    # Initial pressure (ps in bar)
    ps_value = get_input_value("ps", required=False, default="250")
    p_initial_psi = float(ps_value) * BAR_TO_PSI

    # Temperature (pt in Celsius)
    pt_value = get_input_value("pt", required=False, default="21")
    temperature_f = float(pt_value) * 9.0 / 5.0 + 32.0

    # Propellant name (pname under propellant element)
    import urllib.parse

    propellant_elem = root.find(".//propellant")
    if propellant_elem is not None:
        pname_elem = propellant_elem.find(".//input[@name='pname']")
        if pname_elem is not None:
            propellant_name_full = urllib.parse.unquote(pname_elem.get("value"))
            propellant_name = _map_grt_propellant_name(propellant_name_full)
        else:
            propellant_name = "Unknown"
    else:
        propellant_name = "Unknown"

    # Cartridge name (CaliberName)
    cartridge_name = get_input_value("CaliberName", required=False, default="Unknown")
    cartridge_name = urllib.parse.unquote(cartridge_name)

    # Build metadata
    metadata = {
        "cartridge": cartridge_name,
        "barrel_length_in": barrel_length_in,
        "cartridge_overall_length_in": coal_in,
        "bullet_mass_gr": bullet_mass_gr,
        "case_volume_gr_h2o": casevol_gr_h2o,
        "propellant_name": propellant_name,
        "bullet_jacket_type": "Copper Jacket over Lead",  # Assume default
        "p_initial_psi": p_initial_psi,
        "temperature_f": temperature_f,
        "caliber_in": caliber_in,
    }

    # Extract measurement charges
    load_data = _extract_grt_measurements(root)

    return metadata, load_data


def _map_grt_propellant_name(grt_name: str) -> str:
    """Map GRT propellant name to database name.

    Parameters
    ----------
    grt_name : str
        Full GRT propellant name (e.g., "Vihtavuori N150")

    Returns
    -------
    str
        Database-compatible name (e.g., "N150")
    """
    # Common mappings
    mappings = {
        "Vihtavuori": "",
        "Hodgdon": "",
        "IMR": "IMR ",
        "Alliant": "",
        "Accurate": "",
    }

    name = grt_name
    for prefix, replacement in mappings.items():
        if name.startswith(prefix):
            name = name.replace(prefix, replacement).strip()
            break

    return name


def _extract_grt_measurements(root_elem) -> pd.DataFrame:
    """Extract measurement charges from GRT root element.

    Parameters
    ----------
    root_elem : xml.etree.ElementTree.Element
        Root XML element

    Returns
    -------
    pd.DataFrame
        Load ladder data with columns: charge_grains, mean_velocity_fps, velocity_sd, notes
    """
    measurements = []

    # Find Measurement element (capital M)
    measurement_elem = root_elem.find(".//Measurement")
    if measurement_elem is None:
        return pd.DataFrame(
            columns=["charge_grains", "mean_velocity_fps", "velocity_sd", "notes"]
        )

    # Find all charge elements
    for charge in measurement_elem.findall(".//charge"):
        # Charge mass from 'value' attribute (in kg)
        charge_value = charge.get("value")
        if not charge_value:
            continue

        try:
            charge_kg = float(charge_value)
            charge_gr = charge_kg * KG_TO_GRAINS
        except ValueError:
            continue

        # Extract velocities from shot elements
        velocities_m_s = []
        for shot in charge.findall(".//shot"):
            velocity_str = shot.get("velocity")
            if velocity_str:
                try:
                    v_m_s = float(velocity_str)
                    velocities_m_s.append(v_m_s)
                except ValueError:
                    continue

        if len(velocities_m_s) == 0:
            continue

        # Convert to fps
        velocities_fps = [v * MS_TO_FPS for v in velocities_m_s]

        # Compute mean and SD
        mean_velocity = sum(velocities_fps) / len(velocities_fps)
        if len(velocities_fps) > 1:
            variance = sum((v - mean_velocity) ** 2 for v in velocities_fps) / (
                len(velocities_fps) - 1
            )
            sd_velocity = variance**0.5
        else:
            sd_velocity = 0.0

        measurements.append(
            {
                "charge_grains": charge_gr,
                "mean_velocity_fps": mean_velocity,
                "velocity_sd": sd_velocity,
                "notes": "",
            }
        )

    if len(measurements) == 0:
        return pd.DataFrame(
            columns=["charge_grains", "mean_velocity_fps", "velocity_sd", "notes"]
        )

    df = pd.DataFrame(measurements)

    # Sort by charge weight
    df = df.sort_values("charge_grains").reset_index(drop=True)

    return df[["charge_grains", "mean_velocity_fps", "velocity_sd", "notes"]]
