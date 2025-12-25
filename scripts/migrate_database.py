#!/usr/bin/env python3
"""Database migration script for BurnForge.

Upgrades the database schema from simple propellant storage
to full relational design with system-specific characterization.
"""

import sqlite3
import os
from pathlib import Path


def migrate_database(db_path: str = None) -> None:
    """Migrate database to full relational schema.

    Parameters
    ----------
    db_path : str, optional
        Path to database file. Uses default if None.
    """
    if db_path is None:
        # Import here to avoid circular imports
        from ballistics.database.database import get_default_db_path

        db_path = get_default_db_path()

    print(f"Migrating database: {db_path}")

    # Read schema file
    schema_path = Path(__file__).parent.parent / "data" / "db" / "database_schema.sql"
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    with open(schema_path, "r") as f:
        schema_sql = f.read()

    # Connect and execute schema
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Execute schema (all CREATE TABLE IF NOT EXISTS)
        cursor.executescript(schema_sql)
        conn.commit()
        print("Migration completed successfully")

        # Verify tables exist
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = [row[0] for row in cursor.fetchall()]
        print(f"Tables in database: {tables}")

        # Check for required tables
        required_tables = [
            "firearms",
            "bullets",
            "propellants",
            "cases",
            "bullet_types",
            "test_sessions",
            "measurements",
            "fitted_vivacity",
            "fit_residuals",
        ]

        missing = [t for t in required_tables if t not in tables]
        if missing:
            print(f"Warning: Missing tables: {missing}")
        else:
            print("All required tables present")

    except Exception as e:
        conn.rollback()
        raise RuntimeError(f"Migration failed: {e}") from e
    finally:
        conn.close()


def main():
    """Command-line entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Migrate BurnForge database schema")
    parser.add_argument(
        "--db-path",
        help="Database file path (default: from BALLISTICS_DB_PATH env var or data/db/ballistics_data.db)",
    )
    parser.add_argument(
        "--backup", action="store_true", help="Create backup before migration"
    )

    args = parser.parse_args()

    db_path = args.db_path

    if args.backup:
        from ballistics.database.database import create_backup

        backup_path = create_backup(db_path)
        print(f"Backup created: {backup_path}")

    migrate_database(db_path)


if __name__ == "__main__":
    main()
