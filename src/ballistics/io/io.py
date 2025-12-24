"""CSV/JSON loaders with metadata parsing and result exporters."""

import json
import xml.etree.ElementTree as ET
from io import StringIO
import pandas as pd
from typing import cast

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
from ..database.database import insert_firearm, insert_bullet, insert_test_session


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
    if not data_lines:
        load_data = pd.DataFrame(
            data=[],
            columns=["charge_grains", "mean_velocity_fps", "velocity_sd", "notes"],
        )  # type: ignore
    else:
        load_data = pd.read_csv(StringIO("".join(data_lines)))

    # Validate required columns
    required_cols = ["charge_grains", "mean_velocity_fps"]
    for col in required_cols:
        if col not in load_data.columns:
            raise ValueError(f"Missing required column in CSV: {col}")

    # Validate data
    if len(load_data) > 0:
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

    def _safe_float(value: str, default: float) -> float:
        if not value.strip():
            return default
        try:
            return float(value)
        except ValueError:
            return default

    for field in required_fields:
        if field not in metadata_raw or not metadata_raw[field].strip():
            raise ValueError(f"Missing or empty required metadata field: {field}")

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
        "temperature_f": _safe_float(
            metadata_raw.get("Temperature (°F)", "70.0"), 70.0
        ),
        "p_initial_psi": _safe_float(
            metadata_raw.get("Initial Pressure (psi)", "5000.0"), 5000.0
        ),
        "caliber_in": _safe_float(metadata_raw.get("Caliber (in)", "0.308"), 0.308),
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
        value = elem.get("value")
        if value is None:
            if required:
                raise ValueError(f"Required field '{name}' has no value in GRT file")
            return default
        return value

    # Barrel length (xe in mm)
    xe_value = get_input_value("xe")
    barrel_length_mm = float(xe_value) if xe_value is not None else 0.0
    barrel_length_in = barrel_length_mm * MM_TO_IN if barrel_length_mm > 0 else None

    # COAL (oal in mm)
    oal_value = get_input_value("oal")
    coal_mm = float(oal_value) if oal_value is not None else 0.0
    coal_in = coal_mm * MM_TO_IN if coal_mm > 0 else None

    # Case volume (casevol in cm³)
    casevol_value = get_input_value("casevol")
    casevol_cm3 = float(casevol_value) if casevol_value is not None else 0.0
    casevol_gr_h2o = casevol_cm3 * CM3_TO_GRAINS_H2O if casevol_cm3 > 0 else None

    # Bullet mass (mp in grams)
    mp_value = get_input_value("mp")
    bullet_mass_g = float(mp_value) if mp_value is not None else 0.0
    bullet_mass_gr = bullet_mass_g * GRAMS_TO_GRAINS if bullet_mass_g > 0 else None

    # Caliber diameter (Dz in mm)
    Dz_value = get_input_value("Dz")
    caliber_mm = float(Dz_value) if Dz_value is not None else 0.0
    caliber_in = caliber_mm * MM_TO_IN if caliber_mm > 0 else None

    # Initial pressure (ps in bar)
    ps_value = get_input_value("ps", required=False, default="250")
    p_initial_psi = float(ps_value or "250") * BAR_TO_PSI if ps_value else None

    # Temperature (pt in Celsius)
    pt_value = get_input_value("pt", required=False, default="21")
    temperature_f = float(pt_value or "21") * 9.0 / 5.0 + 32.0 if pt_value else None

    # Propellant name (pname under propellant element)
    import urllib.parse

    propellant_elem = root.find(".//propellant")
    if propellant_elem is not None:
        pname_elem = propellant_elem.find(".//input[@name='pname']")
        if pname_elem is not None:
            pname_value = pname_elem.get("value")
            propellant_name_full = (
                urllib.parse.unquote(pname_value) if pname_value else "Unknown"
            )
            propellant_name = _map_grt_propellant_name(propellant_name_full)
        else:
            propellant_name = "Unknown"
    else:
        propellant_name = "Unknown"

    # Cartridge name (CaliberName)
    cartridge_name_value = get_input_value(
        "CaliberName", required=False, default="Unknown"
    )
    cartridge_name = urllib.parse.unquote(cartridge_name_value or "Unknown")

    # Build metadata
    metadata = {
        "cartridge": cartridge_name,
        "barrel_length_in": barrel_length_in if barrel_length_in is not None else 0.0,
        "cartridge_overall_length_in": coal_in if coal_in is not None else 0.0,
        "bullet_mass_gr": bullet_mass_gr if bullet_mass_gr is not None else 0.0,
        "case_volume_gr_h2o": casevol_gr_h2o if casevol_gr_h2o is not None else 0.0,
        "propellant_name": propellant_name,
        "bullet_jacket_type": "Copper Jacket over Lead",  # Assume default
        "p_initial_psi": p_initial_psi if p_initial_psi is not None else 5000.0,
        "temperature_f": temperature_f if temperature_f is not None else 70.0,
        "caliber_in": caliber_in if caliber_in is not None else 0.308,
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
        return pd.DataFrame(  # type: ignore
            data=[],
            columns=["charge_grains", "mean_velocity_fps", "velocity_sd", "notes"],
        )

    df = pd.DataFrame(measurements)

    # Sort by charge weight
    df = df.sort_values("charge_grains").reset_index(drop=True)

    return cast(
        pd.DataFrame, df[["charge_grains", "mean_velocity_fps", "velocity_sd", "notes"]]
    )


def load_json_data(
    filepath: str, units: str = "imperial", db_path: str | None = None
) -> tuple[dict, pd.DataFrame]:
    """Load chronograph data from JSON file with unit conversion support.

    Parameters
    ----------
    filepath : str
        Path to JSON file following the manual entry template
    units : str
        Input units: 'imperial' or 'metric'. Default 'imperial'
    db_path : str, optional
        Database path for validation

    Returns
    -------
    tuple
        (metadata: dict in imperial units, load_data: pd.DataFrame)
    """
    with open(filepath, "r") as f:
        data = json.load(f)

    metadata_raw = data["metadata"]
    load_data_raw = data["load_data"]

    # Unit conversion if metric
    if units == "metric":
        metadata = _convert_metadata_to_imperial(metadata_raw)
    else:
        metadata = metadata_raw.copy()

    # Convert load_data to DataFrame
    load_data = pd.DataFrame(load_data_raw)

    # Validate
    required_meta = [
        "barrel_length_in",
        "cartridge_overall_length_in",
        "bullet_mass_gr",
        "case_volume_gr_h2o",
        "propellant_name",
        "bullet_jacket_type",
        "temperature_f",
        "caliber_in",
    ]
    for field in required_meta:
        if field not in metadata:
            raise ValueError(f"Missing required metadata field: {field}")

    required_cols = ["charge_grains", "mean_velocity_fps"]
    for col in required_cols:
        if col not in load_data.columns:
            raise ValueError(f"Missing required column in load_data: {col}")

    return metadata, load_data


def _convert_metadata_to_imperial(metadata: dict) -> dict:
    """Convert metric metadata to imperial units."""
    converted = metadata.copy()

    # Lengths: mm to in
    if "barrel_length_mm" in metadata:
        converted["barrel_length_in"] = metadata["barrel_length_mm"] * MM_TO_IN
    if "cartridge_overall_length_mm" in metadata:
        converted["cartridge_overall_length_in"] = (
            metadata["cartridge_overall_length_mm"] * MM_TO_IN
        )
    if "caliber_mm" in metadata:
        converted["caliber_in"] = metadata["caliber_mm"] * MM_TO_IN

    # Mass: g to gr
    if "bullet_mass_g" in metadata:
        converted["bullet_mass_gr"] = metadata["bullet_mass_g"] * GRAMS_TO_GRAINS

    # Volume: cm³ to gr H2O
    if "case_volume_cm3" in metadata:
        converted["case_volume_gr_h2o"] = (
            metadata["case_volume_cm3"] * CM3_TO_GRAINS_H2O
        )

    # Temperature: C to F
    if "temperature_c" in metadata:
        converted["temperature_f"] = metadata["temperature_c"] * 9.0 / 5.0 + 32.0

    # Velocity: m/s to fps
    if "load_data" in metadata:
        for charge in converted["load_data"]:
            if "mean_velocity_ms" in charge:
                charge["mean_velocity_fps"] = charge["mean_velocity_ms"] * MS_TO_FPS

    return converted


def load_grt_project_with_db(
    filepath: str, db_path: str | None = None
) -> tuple[dict, pd.DataFrame, int]:
    """Load GRT project and insert firearm, bullet, session into database.

    Returns metadata, load_data, and session_id.
    """
    metadata, load_data = load_grt_project(filepath)

    # Extract additional details from GRT
    firearm_info = _extract_grt_firearm_info(filepath)
    bullet_info = _extract_grt_bullet_info(filepath)

    # Insert into DB
    firearm_id = insert_firearm(
        manufacturer=firearm_info.get("manufacturer", "Unknown"),
        model=firearm_info.get("model", "Unknown"),
        barrel_length_in=metadata["barrel_length_in"],
        caliber_in=metadata["caliber_in"],
        db_path=db_path,
    )

    bullet_id = insert_bullet(
        manufacturer=bullet_info.get("manufacturer", "Unknown"),
        model=bullet_info.get("model", "Unknown"),
        weight_gr=metadata["bullet_mass_gr"],
        caliber_in=metadata["caliber_in"],
        jacket_type=metadata["bullet_jacket_type"],
        db_path=db_path,
    )

    session_id = insert_test_session(
        firearm_id=firearm_id,
        bullet_id=bullet_id,
        propellant_name=metadata["propellant_name"],
        temperature_f=metadata["temperature_f"],
        cartridge_overall_length_in=metadata["cartridge_overall_length_in"],
        case_volume_gr_h2o=metadata["case_volume_gr_h2o"],
        grt_filename=filepath.split("/")[-1],
        db_path=db_path,
    )

    return metadata, load_data, session_id


def _extract_grt_firearm_info(filepath: str) -> dict:
    """Extract firearm details from GRT file."""
    # Placeholder - in real GRT, might have more info
    return {"manufacturer": "Unknown", "model": "Unknown"}


def _extract_grt_bullet_info(filepath: str) -> dict:
    """Extract bullet details from GRT file."""
    # Placeholder
    return {"manufacturer": "Unknown", "model": "Unknown"}
