-- Migration to extended database schema for system-specific vivacity
-- Run this after backing up current database

-- Add new tables
CREATE TABLE IF NOT EXISTS firearms (
    firearm_id INTEGER PRIMARY KEY AUTOINCREMENT,
    manufacturer TEXT,
    model TEXT,
    serial_number TEXT,
    caliber_in REAL NOT NULL,
    barrel_length_in REAL NOT NULL,
    twist_rate TEXT,
    chamber_spec TEXT,
    throat_in REAL,
    groove_diameter_in REAL,
    bore_diameter_in REAL,
    rifling_type TEXT,
    notes TEXT,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(manufacturer, model, serial_number, barrel_length_in)
);

CREATE TABLE IF NOT EXISTS bullets (
    bullet_id INTEGER PRIMARY KEY AUTOINCREMENT,
    manufacturer TEXT NOT NULL,
    model TEXT NOT NULL,
    part_number TEXT,
    weight_gr REAL NOT NULL,
    caliber_in REAL NOT NULL,
    diameter_in REAL,
    length_in REAL,
    jacket_type TEXT NOT NULL,
    bc_g1 REAL,
    bc_g7 REAL,
    construction TEXT,
    notes TEXT,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(manufacturer, model, part_number, weight_gr)
);

-- Extend propellants table
ALTER TABLE propellants ADD COLUMN manufacturer TEXT DEFAULT 'Vihtavuori';
ALTER TABLE propellants ADD COLUMN lot_number TEXT;
ALTER TABLE propellants ADD COLUMN production_date TEXT;

-- Add test_sessions and measurements
CREATE TABLE IF NOT EXISTS test_sessions (
    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
    firearm_id INTEGER REFERENCES firearms(firearm_id),
    bullet_id INTEGER REFERENCES bullets(bullet_id),
    propellant_id INTEGER REFERENCES propellants(propellant_id),
    temperature_f REAL NOT NULL,
    date TEXT,
    chronograph_model TEXT,
    light_conditions TEXT,
    weather_notes TEXT,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS measurements (
    measurement_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER REFERENCES test_sessions(session_id),
    charge_grains REAL NOT NULL,
    velocity_fps REAL,
    velocity_sd REAL,
    extreme_spread REAL,
    group_size_in REAL,
    notes TEXT
);

-- Add fitted results storage
CREATE TABLE IF NOT EXISTS fitted_vivacity (
    fit_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER REFERENCES test_sessions(session_id),
    Lambda_base REAL NOT NULL,
    poly_a REAL NOT NULL,
    poly_b REAL NOT NULL,
    poly_c REAL NOT NULL,
    poly_d REAL NOT NULL,
    temp_sensitivity_sigma_per_K REAL,
    bore_friction_psi REAL,
    start_pressure_psi REAL,
    covolume_m3_per_kg REAL,
    rmse_velocity REAL,
    iterations INTEGER,
    success INTEGER,
    fit_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Update version
INSERT OR REPLACE INTO version (version, description) VALUES (3, 'Extended schema with system-specific storage');
