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
    return os.environ.get('BALLISTICS_DB_PATH', 'data/ballistics_data.db')


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

    cursor.execute("""
        SELECT vivacity, base, force, temp_0, temp_coeff_v, temp_coeff_p, bulk_density,
               poly_a, poly_b, poly_c, poly_d
        FROM propellants WHERE name = ?
    """, (name,))

    row = cursor.fetchone()
    conn.close()

    if not row:
        raise ValueError(f"Propellant '{name}' not found in database. "
                        f"Use list_propellants() to see available options.")

    return {
        'vivacity': row[0],
        'base': row[1],
        'force': row[2],
        'temp_0': row[3],
        'temp_coeff_v': row[4],
        'temp_coeff_p': row[5],
        'bulk_density': row[6],
        'poly_a': row[7],
        'poly_b': row[8],
        'poly_c': row[9],
        'poly_d': row[10]
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

    cursor.execute("""
        SELECT s, rho_p
        FROM bullet_types WHERE name = ?
    """, (name,))

    row = cursor.fetchone()
    conn.close()

    if not row:
        raise ValueError(f"Bullet type '{name}' not found in database.")

    return {
        's': row[0],
        'rho_p': row[1]
    }


def update_propellant_coefficients(name: str, Lambda_base: float,
                                    coeffs: tuple[float, float, float, float],
                                    db_path: str | None = None) -> None:
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
    cursor.execute("""
        UPDATE propellants
        SET vivacity = ?, poly_a = ?, poly_b = ?, poly_c = ?, poly_d = ?
        WHERE name = ?
    """, (vivacity, a, b, c, d, name))

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
