"""SQLite CRUD operations, schema management, and queries."""

import os
import sqlite3
from pathlib import Path


def get_default_db_path() -> str:
    """Get database path from environment variable or default.

    Returns
    -------
    str
        Path from BALLISTICS_DB_PATH env var, else "data/ballistics_data.db"
    """
    return os.environ.get("BALLISTICS_DB_PATH", "data/db/ballistics_data.db")


def get_propellant(name: str, db_path: str | None = None) -> dict:
    """Retrieve propellant properties by name.

    Parameters
    ----------
    name : str
        Propellant name (e.g., "Varget", "N140")
    db_path : str, optional
        Path to SQLite database (uses get_default_db_path() if None)

    Returns
    -------
    dict
        Keys: vivacity, base, force, temp_0, bulk_density, poly_a, poly_b, poly_c, poly_d

    Raises
    ------
    ValueError
        If propellant not found in database
    """
    if db_path is None:
        db_path = get_default_db_path()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT vivacity, base, force, temp_0, temp_coeff_v, temp_coeff_p, bulk_density,
               poly_a, poly_b, poly_c, poly_d,
               covolume_m3_per_kg, temp_sensitivity_sigma_per_K,
               grain_geometry, grain_geometry_type, alpha
        FROM propellants WHERE name = ?
    """,
        (name,),
    )

    row = cursor.fetchone()
    conn.close()

    if not row:
        raise ValueError(
            f"Propellant '{name}' not found in database. "
            f"Use list_propellants() to see available options."
        )

    return {
        "vivacity": row[0],
        "base": row[1],
        "force": row[2],
        "temp_0": row[3],
        "temp_coeff_v": row[4],
        "temp_coeff_p": row[5],
        "bulk_density": row[6],
        "poly_a": row[7],
        "poly_b": row[8],
        "poly_c": row[9],
        "poly_d": row[10],
        "covolume_m3_per_kg": row[11]
        if len(row) > 11 and row[11] is not None
        else 0.001,
        "temp_sensitivity_sigma_per_K": row[12]
        if len(row) > 12 and row[12] is not None
        else 0.002,
        "grain_geometry": row[13]
        if len(row) > 13 and row[13] is not None
        else "spherical",
        "grain_geometry_type": row[14]
        if len(row) > 14 and row[14] is not None
        else None,
        "alpha": row[15] if len(row) > 15 and row[15] is not None else 0.0,
    }


def get_bullet_type(name: str, db_path: str | None = None) -> dict:
    """Retrieve bullet type properties by name.

    Parameters
    ----------
    name : str
        Bullet type name (e.g., "Copper Jacket over Lead")
    db_path : str, optional
        Path to SQLite database (uses get_default_db_path() if None)

    Returns
    -------
    dict
        Keys: s (strength factor), rho_p (density in lbm/in³)

    Raises
    ------
    ValueError
        If bullet type not found in database
    """
    if db_path is None:
        db_path = get_default_db_path()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT s, rho_p
        FROM bullet_types WHERE name = ?
    """,
        (name,),
    )

    row = cursor.fetchone()
    conn.close()

    if not row:
        raise ValueError(f"Bullet type '{name}' not found in database.")

    return {
        "s": row[0],
        "rho_p": row[1],
        "start_pressure_psi": 3626.0,
    }


def update_propellant_coefficients(
    name: str,
    Lambda_base: float,
    coeffs: tuple[float, float, float, float],
    db_path: str | None = None,
) -> None:
    """Update vivacity polynomial coefficients for a propellant.

    Parameters
    ----------
    name : str
        Propellant name
    Lambda_base : float
        Base vivacity in s⁻¹ per 100 bar
    coeffs : tuple
        (a, b, c, d) polynomial coefficients
    db_path : str, optional
        Path to SQLite database (uses get_default_db_path() if None)

    Raises
    ------
    ValueError
        If propellant not found in database
    """
    if db_path is None:
        db_path = get_default_db_path()

    # Convert Lambda_base back to vivacity
    vivacity = Lambda_base * 1450

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Verify propellant exists
    cursor.execute("SELECT name FROM propellants WHERE name = ?", (name,))
    if not cursor.fetchone():
        conn.close()
        raise ValueError(f"Propellant '{name}' not found in database.")

    # Update coefficients
    a, b, c, d = coeffs
    cursor.execute(
        """
        UPDATE propellants
        SET vivacity = ?, poly_a = ?, poly_b = ?, poly_c = ?, poly_d = ?
        WHERE name = ?
    """,
        (vivacity, a, b, c, d, name),
    )

    conn.commit()
    conn.close()


def list_propellants(db_path: str | None = None) -> list[str]:
    """Return list of all propellant names in database.

    Parameters
    ----------
    db_path : str, optional
        Path to SQLite database (uses get_default_db_path() if None)

    Returns
    -------
    list[str]
        List of propellant names sorted alphabetically
    """
    if db_path is None:
        db_path = get_default_db_path()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM propellants ORDER BY name")
    names = [row[0] for row in cursor.fetchall()]

    conn.close()
    return names


# Firearms CRUD
def insert_firearm(
    manufacturer: str,
    model: str,
    serial_number: str | None = None,
    caliber_in: float | None = None,
    barrel_length_in: float | None = None,
    twist_rate: str | None = None,
    chamber_spec: str | None = None,
    throat_in: float | None = None,
    groove_diameter_in: float | None = None,
    bore_diameter_in: float | None = None,
    rifling_type: str | None = None,
    notes: str | None = None,
    db_path: str | None = None,
) -> int:
    """Insert a new firearm into the database.

    Returns the firearm_id of the inserted or existing firearm.
    """
    if db_path is None:
        db_path = get_default_db_path()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check if exists
    cursor.execute(
        """
        SELECT firearm_id FROM firearms
        WHERE manufacturer = ? AND model = ? AND barrel_length_in = ?
        AND (serial_number = ? OR (serial_number IS NULL AND ? IS NULL))
        """,
        (manufacturer, model, barrel_length_in, serial_number, serial_number),
    )
    existing = cursor.fetchone()
    if existing:
        conn.close()
        return existing[0]

    cursor.execute(
        """
        INSERT INTO firearms (
            manufacturer, model, serial_number, caliber_in, barrel_length_in,
            twist_rate, chamber_spec, throat_in, groove_diameter_in, bore_diameter_in,
            rifling_type, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            manufacturer,
            model,
            serial_number,
            caliber_in,
            barrel_length_in,
            twist_rate,
            chamber_spec,
            throat_in,
            groove_diameter_in,
            bore_diameter_in,
            rifling_type,
            notes,
        ),
    )
    firearm_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return firearm_id


def get_firearm(firearm_id: int, db_path: str | None = None) -> dict | None:
    """Get firearm details by ID."""
    if db_path is None:
        db_path = get_default_db_path()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM firearms WHERE firearm_id = ?", (firearm_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    columns = [
        "firearm_id",
        "manufacturer",
        "model",
        "serial_number",
        "caliber_in",
        "barrel_length_in",
        "twist_rate",
        "chamber_spec",
        "throat_in",
        "groove_diameter_in",
        "bore_diameter_in",
        "rifling_type",
        "notes",
        "created_date",
    ]
    return dict(zip(columns, row))


def list_firearms(db_path: str | None = None) -> list[dict]:
    """List all firearms."""
    if db_path is None:
        db_path = get_default_db_path()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM firearms ORDER BY manufacturer, model")
    rows = cursor.fetchall()
    conn.close()

    columns = [
        "firearm_id",
        "manufacturer",
        "model",
        "serial_number",
        "caliber_in",
        "barrel_length_in",
        "twist_rate",
        "chamber_spec",
        "throat_in",
        "groove_diameter_in",
        "bore_diameter_in",
        "rifling_type",
        "notes",
        "created_date",
    ]
    return [dict(zip(columns, row)) for row in rows]


# Bullets CRUD
def insert_bullet(
    manufacturer: str,
    model: str,
    part_number: str | None = None,
    weight_gr: float | None = None,
    caliber_in: float | None = None,
    diameter_in: float | None = None,
    length_in: float | None = None,
    jacket_type: str | None = None,
    bc_g1: float | None = None,
    bc_g7: float | None = None,
    construction: str | None = None,
    notes: str | None = None,
    db_path: str | None = None,
) -> int:
    """Insert a new bullet into the database.

    Returns the bullet_id of the inserted or existing bullet.
    """
    if db_path is None:
        db_path = get_default_db_path()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check if exists
    cursor.execute(
        """
        SELECT bullet_id FROM bullets
        WHERE manufacturer = ? AND model = ? AND weight_gr = ?
        AND (part_number = ? OR (part_number IS NULL AND ? IS NULL))
        """,
        (manufacturer, model, weight_gr, part_number, part_number),
    )
    existing = cursor.fetchone()
    if existing:
        conn.close()
        return existing[0]

    cursor.execute(
        """
        INSERT INTO bullets (
            manufacturer, model, part_number, weight_gr, caliber_in, diameter_in,
            length_in, jacket_type, bc_g1, bc_g7, construction, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            manufacturer,
            model,
            part_number,
            weight_gr,
            caliber_in,
            diameter_in,
            length_in,
            jacket_type,
            bc_g1,
            bc_g7,
            construction,
            notes,
        ),
    )
    bullet_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return bullet_id


def get_bullet(bullet_id: int, db_path: str | None = None) -> dict | None:
    """Get bullet details by ID."""
    if db_path is None:
        db_path = get_default_db_path()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM bullets WHERE bullet_id = ?", (bullet_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    columns = [
        "bullet_id",
        "manufacturer",
        "model",
        "part_number",
        "weight_gr",
        "caliber_in",
        "diameter_in",
        "length_in",
        "jacket_type",
        "bc_g1",
        "bc_g7",
        "construction",
        "notes",
        "created_date",
    ]
    return dict(zip(columns, row))


def list_bullets(db_path: str | None = None) -> list[dict]:
    """List all bullets."""
    if db_path is None:
        db_path = get_default_db_path()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM bullets ORDER BY manufacturer, model")
    rows = cursor.fetchall()
    conn.close()

    columns = [
        "bullet_id",
        "manufacturer",
        "model",
        "part_number",
        "weight_gr",
        "caliber_in",
        "diameter_in",
        "length_in",
        "jacket_type",
        "bc_g1",
        "bc_g7",
        "construction",
        "notes",
        "created_date",
    ]
    return [dict(zip(columns, row)) for row in rows]


# Calibrated Propellants CRUD
def insert_calibrated_propellant(
    firearm_id: int,
    bullet_id: int,
    propellant_name: str,
    temperature_f: float,
    fitted_params: dict,
    db_path: str | None = None,
) -> int:
    """Insert or update calibrated propellant parameters."""
    if db_path is None:
        db_path = get_default_db_path()

    import json

    fitted_params_json = json.dumps(fitted_params)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Upsert
    cursor.execute(
        """
        INSERT OR REPLACE INTO calibrated_propellants (
            firearm_id, bullet_id, propellant_id, temperature_f, fitted_params
        ) VALUES (?, ?, ?, ?, ?)
        """,
        (firearm_id, bullet_id, propellant_name, temperature_f, fitted_params_json),
    )
    calibrated_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return calibrated_id


def get_calibrated_propellant(
    firearm_id: int,
    bullet_id: int,
    propellant_name: str,
    temperature_f: float,
    db_path: str | None = None,
) -> dict | None:
    """Get calibrated parameters."""
    if db_path is None:
        db_path = get_default_db_path()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT * FROM calibrated_propellants
        WHERE firearm_id = ? AND bullet_id = ? AND propellant_id = ? AND temperature_f = ?
        """,
        (firearm_id, bullet_id, propellant_name, temperature_f),
    )
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    import json

    columns = [
        "calibrated_id",
        "firearm_id",
        "bullet_id",
        "propellant_id",
        "temperature_f",
        "fitted_params",
        "created_date",
    ]
    result = dict(zip(columns, row))
    result["fitted_params"] = json.loads(result["fitted_params"])
    return result


# Test Sessions CRUD
def insert_test_session(
    firearm_id: int,
    bullet_id: int,
    propellant_name: str,
    temperature_f: float,
    cartridge_overall_length_in: float,
    case_volume_gr_h2o: float,
    case_id: int | None = None,
    humidity_percent: float | None = None,
    pressure_inhg: float | None = None,
    altitude_ft: float | None = None,
    primer_type: str | None = None,
    test_date: str | None = None,
    location: str | None = None,
    purpose: str | None = None,
    shooter: str | None = None,
    notes: str | None = None,
    grt_filename: str | None = None,
    db_path: str | None = None,
) -> int:
    """Insert a new test session."""
    if db_path is None:
        db_path = get_default_db_path()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO test_sessions (
            firearm_id, bullet_id, propellant_id, temperature_f, cartridge_overall_length_in,
            case_volume_gr_h2o, case_id, humidity_percent, pressure_inhg, altitude_ft,
            primer_type, test_date, location, purpose, shooter, notes, grt_filename
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            firearm_id,
            bullet_id,
            propellant_name,
            temperature_f,
            cartridge_overall_length_in,
            case_volume_gr_h2o,
            case_id,
            humidity_percent,
            pressure_inhg,
            altitude_ft,
            primer_type,
            test_date,
            location,
            purpose,
            shooter,
            notes,
            grt_filename,
        ),
    )
    session_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return session_id


def get_test_session(session_id: int, db_path: str | None = None) -> dict | None:
    """Get test session details."""
    if db_path is None:
        db_path = get_default_db_path()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM test_sessions WHERE session_id = ?", (session_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    columns = [
        "session_id",
        "firearm_id",
        "bullet_id",
        "propellant_id",
        "case_id",
        "temperature_f",
        "humidity_percent",
        "pressure_inhg",
        "altitude_ft",
        "cartridge_overall_length_in",
        "case_volume_gr_h2o",
        "primer_type",
        "test_date",
        "location",
        "purpose",
        "shooter",
        "notes",
        "grt_filename",
        "imported_date",
        "created_date",
    ]
    return dict(zip(columns, row))


def list_test_sessions(db_path: str | None = None) -> list[dict]:
    """List all test sessions."""
    if db_path is None:
        db_path = get_default_db_path()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM test_sessions ORDER BY test_date DESC")
    rows = cursor.fetchall()
    conn.close()

    columns = [
        "session_id",
        "firearm_id",
        "bullet_id",
        "propellant_id",
        "case_id",
        "temperature_f",
        "humidity_percent",
        "pressure_inhg",
        "altitude_ft",
        "cartridge_overall_length_in",
        "case_volume_gr_h2o",
        "primer_type",
        "test_date",
        "location",
        "purpose",
        "shooter",
        "notes",
        "grt_filename",
        "imported_date",
        "created_date",
    ]
    return [dict(zip(columns, row)) for row in rows]


def create_backup(db_path: str | None = None) -> str:
    """Create backup of database file.

    Parameters
    ----------
    db_path : str, optional
        Path to SQLite database (uses get_default_db_path() if None)

    Returns
    -------
    str
        Path to backup file

    Raises
    ------
    FileNotFoundError
        If database file does not exist
    """
    if db_path is None:
        db_path = get_default_db_path()

    if not Path(db_path).exists():
        raise FileNotFoundError(f"Database not found: {db_path}")

    backup_path = f"{db_path}.backup"

    # Copy database
    import shutil

    shutil.copy2(db_path, backup_path)

    return backup_path
