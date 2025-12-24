"""Published load data loading and validation utilities."""

import pandas as pd
import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional

from ..database.database import get_default_db_path


def load_published_data_csv(filepath: Path) -> pd.DataFrame:
    """Load published load data from CSV file.

    Expected CSV columns:
    - cartridge: Cartridge name (e.g., ".308 Winchester")
    - propellant_name: Propellant name (e.g., "N150")
    - bullet_weight_gr: Bullet weight in grains
    - published_pressure_psi: Published pressure in PSI
    - pressure_type: 'MAP', 'CIP', 'SAAMI', etc.
    - source: Data source (e.g., "SAAMI", "Hodgdon")
    - charge_grains: Reference charge weight (optional)
    - uncertainty_psi: Pressure uncertainty (optional)
    - confidence_level: 'high', 'medium', 'low' (optional)

    Parameters
    ----------
    filepath : Path
        Path to CSV file

    Returns
    -------
    pd.DataFrame
        DataFrame with published load data
    """
    df = pd.read_csv(filepath)

    # Validate required columns
    required_cols = [
        "cartridge",
        "propellant_name",
        "bullet_weight_gr",
        "published_pressure_psi",
        "pressure_type",
        "source",
    ]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    # Set defaults for optional columns
    if "uncertainty_psi" not in df.columns:
        df["uncertainty_psi"] = 0.0
    if "confidence_level" not in df.columns:
        df["confidence_level"] = "medium"
    if "charge_grains" not in df.columns:
        df["charge_grains"] = None

    return df


def load_published_data_json(filepath: Path) -> pd.DataFrame:
    """Load published load data from JSON file.

    Parameters
    ----------
    filepath : Path
        Path to JSON file

    Returns
    -------
    pd.DataFrame
        DataFrame with published load data
    """
    with open(filepath, "r") as f:
        data = json.load(f)

    if isinstance(data, list):
        df = pd.DataFrame(data)
    else:
        df = pd.DataFrame([data])

    return df


def import_published_data_to_db(
    data: pd.DataFrame, db_path: Optional[str] = None
) -> int:
    """Import published load data to database.

    Parameters
    ----------
    data : pd.DataFrame
        Published load data
    db_path : str, optional
        Database path override

    Returns
    -------
    int
        Number of records imported
    """
    if db_path is None:
        db_path = get_default_db_path()

    conn = sqlite3.connect(db_path)

    try:
        # Insert data
        records_imported = 0
        for _, row in data.iterrows():
            try:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO published_load_specs
                    (cartridge, propellant_name, bullet_weight_gr, published_pressure_psi,
                     pressure_type, source, charge_grains, uncertainty_psi, confidence_level, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        row["cartridge"],
                        row["propellant_name"],
                        row["bullet_weight_gr"],
                        row["published_pressure_psi"],
                        row["pressure_type"],
                        row["source"],
                        row.get("charge_grains"),
                        row.get("uncertainty_psi", 0.0),
                        row.get("confidence_level", "medium"),
                        row.get("notes", ""),
                    ),
                )
                records_imported += 1
            except Exception as e:
                print(f"Warning: Failed to import row: {e}")

        conn.commit()
        return records_imported

    finally:
        conn.close()


def get_published_pressures(
    cartridge: str,
    propellant_name: str,
    bullet_weight_gr: Optional[float] = None,
    db_path: Optional[str] = None,
) -> List[Dict]:
    """Retrieve published pressure data for a given combination.

    Parameters
    ----------
    cartridge : str
        Cartridge name
    propellant_name : str
        Propellant name
    bullet_weight_gr : float, optional
        Bullet weight filter
    db_path : Path, optional
        Database path override

    Returns
    -------
    List[Dict]
        List of published pressure records
    """
    if db_path is None:
        db_path = get_default_db_path()

    conn = sqlite3.connect(db_path)

    try:
        query = """
            SELECT * FROM published_load_specs
            WHERE cartridge LIKE ? AND propellant_name LIKE ?
        """
        params: List = [f"%{cartridge}%", f"%{propellant_name}%"]

        if bullet_weight_gr is not None:
            query += " AND bullet_weight_gr BETWEEN ? AND ?"
            params.extend(
                [bullet_weight_gr * 0.95, bullet_weight_gr * 1.05]
            )  # ±5% tolerance

        query += " ORDER BY confidence_level DESC, published_pressure_psi"

        cursor = conn.execute(query, params)
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]

        return results

    finally:
        conn.close()


def validate_published_data(data: pd.DataFrame) -> List[str]:
    """Validate published load data for consistency and completeness.

    Parameters
    ----------
    data : pd.DataFrame
        Published load data to validate

    Returns
    -------
    List[str]
        List of validation warnings/errors
    """
    warnings = []

    # Check required fields
    required_fields = [
        "cartridge",
        "propellant_name",
        "bullet_weight_gr",
        "published_pressure_psi",
        "pressure_type",
        "source",
    ]

    for field in required_fields:
        if field not in data.columns:
            warnings.append(f"Missing required column: {field}")

    # Check data types and ranges
    if "published_pressure_psi" in data.columns:
        pressures = data["published_pressure_psi"].dropna()
        if len(pressures) > 0:
            if (pressures <= 0).any():
                warnings.append("Published pressures must be positive")
            if (pressures > 100000).any():
                warnings.append("Published pressures seem unreasonably high (>100ksi)")

    if "bullet_weight_gr" in data.columns:
        weights = data["bullet_weight_gr"].dropna()
        if len(weights) > 0:
            if (weights <= 0).any():
                warnings.append("Bullet weights must be positive")
            if (weights > 1000).any():
                warnings.append("Bullet weights seem unreasonably high (>1000gr)")

    # Check for duplicate entries
    if len(data) > 0:
        duplicates = data.duplicated(
            subset=["cartridge", "propellant_name", "bullet_weight_gr", "source"]
        )
        if duplicates.any():
            warnings.append(f"Found {duplicates.sum()} duplicate entries")

    return warnings
