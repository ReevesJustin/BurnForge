-- Internal Ballistics Database Schema
-- Designed for GRT project file imports and fitted vivacity storage
-- Captures system-specific combinations: firearm + bullet + propellant + temperature

-- ============================================================
-- Core Component Tables
-- ============================================================

CREATE TABLE IF NOT EXISTS firearms (
    firearm_id INTEGER PRIMARY KEY AUTOINCREMENT,
    manufacturer TEXT,
    model TEXT,
    serial_number TEXT,
    caliber_in REAL NOT NULL,
    barrel_length_in REAL NOT NULL,
    twist_rate TEXT,  -- e.g., "1:8", "1:10"
    chamber_spec TEXT,  -- e.g., "SAAMI", "Match", ".223 Wylde"
    throat_in REAL,  -- Freebore/throat length
    groove_diameter_in REAL,
    bore_diameter_in REAL,
    rifling_type TEXT,  -- e.g., "conventional", "polygonal", "5R"
    notes TEXT,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(manufacturer, model, serial_number, barrel_length_in)
);

CREATE TABLE IF NOT EXISTS bullets (
    bullet_id INTEGER PRIMARY KEY AUTOINCREMENT,
    manufacturer TEXT NOT NULL,
    model TEXT NOT NULL,
    part_number TEXT,  -- Specific part number (e.g., "1729" for Sierra 130gr HPBT)
    weight_gr REAL NOT NULL,
    caliber_in REAL NOT NULL,
    diameter_in REAL,  -- Actual measured diameter
    length_in REAL,
    jacket_type TEXT NOT NULL,  -- e.g., "Copper Jacket over Lead", "Monolithic Copper"
    bc_g1 REAL,
    bc_g7 REAL,
    construction TEXT,  -- e.g., "HPBT", "FMJ", "Soft Point"
    notes TEXT,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(manufacturer, model, part_number, weight_gr)
);

CREATE TABLE IF NOT EXISTS propellants (
    name TEXT PRIMARY KEY,
    manufacturer TEXT,          -- Manufacturer name
    vivacity REAL,              -- s^-1 per 100 bar
    base TEXT,                  -- 'S' for single-base, 'D' for double-base
    force REAL,                 -- Force constant (ft-lbf/lbm)
    temp_0 REAL,                -- Flame temperature at reference condition (K)
    temp_coeff_v REAL,          -- Temperature coefficient for vivacity (1/K)
    temp_coeff_p REAL,          -- Temperature coefficient for pressure (1/K)
    bulk_density REAL,          -- Bulk density (lbm/in^3)
    poly_a REAL,                -- Polynomial coefficient a
    poly_b REAL,                -- Polynomial coefficient b
    poly_c REAL,                -- Polynomial coefficient c
    poly_d REAL                 -- Polynomial coefficient d
    , grain_geometry TEXT DEFAULT 'spherical', alpha REAL DEFAULT 0.0, temp_sensitivity_sigma_per_K REAL DEFAULT 0.002, covolume_m3_per_kg REAL DEFAULT 0.001, grain_geometry_type TEXT, perforations_count INTEGER DEFAULT 0, grain_diameter_mm REAL, grain_length_mm REAL, web_thickness_mm REAL, coating TEXT, composition TEXT, grain_confidence TEXT DEFAULT 'medium', grain_sources TEXT
);

CREATE TABLE IF NOT EXISTS calibrated_propellants (
    calibrated_id INTEGER PRIMARY KEY AUTOINCREMENT,
    firearm_id INTEGER NOT NULL,
    bullet_id INTEGER NOT NULL,
    propellant_id TEXT NOT NULL,
    temperature_f REAL NOT NULL,
    fitted_params TEXT,  -- JSON string of fitted parameters (lambda_base, coeffs, etc.)
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (firearm_id) REFERENCES firearms(firearm_id),
    FOREIGN KEY (bullet_id) REFERENCES bullets(bullet_id),
    FOREIGN KEY (propellant_id) REFERENCES propellants(name),
    UNIQUE(firearm_id, bullet_id, propellant_id, temperature_f)
);

CREATE TABLE IF NOT EXISTS cases (
    case_id INTEGER PRIMARY KEY AUTOINCREMENT,
    manufacturer TEXT NOT NULL,
    headstamp TEXT,
    caliber TEXT NOT NULL,
    case_volume_gr_h2o REAL NOT NULL,  -- Measured case volume
    lot_number TEXT,
    times_fired INTEGER DEFAULT 0,
    neck_tension TEXT,
    primer_pocket_spec TEXT,
    notes TEXT,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bullet_types (
    name TEXT PRIMARY KEY,
    s REAL,                     -- Strength factor
    rho_p REAL,                 -- Density (lbm/in^3)
    start_pressure_psi REAL DEFAULT 3626.0  -- Shot-start pressure threshold (psi)
);

-- ============================================================
-- Test Session Tables
-- ============================================================

CREATE TABLE IF NOT EXISTS test_sessions (
    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
    firearm_id INTEGER NOT NULL,
    bullet_id INTEGER NOT NULL,
    propellant_id TEXT NOT NULL,
    case_id INTEGER,  -- Optional - can use generic case volume

    -- Environmental conditions
    temperature_f REAL NOT NULL,
    humidity_percent REAL,
    pressure_inhg REAL,
    altitude_ft REAL,

    -- Loading specifications
    cartridge_overall_length_in REAL NOT NULL,  -- COAL
    case_volume_gr_h2o REAL NOT NULL,  -- Effective case volume with bullet seated
    primer_type TEXT,

    -- Session metadata
    test_date DATE NOT NULL,
    location TEXT,
    purpose TEXT,  -- e.g., "load development", "temperature sensitivity", "velocity ladder"
    shooter TEXT,
    notes TEXT,

    -- GRT import tracking
    grt_filename TEXT,  -- Original GRT file name
    imported_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (firearm_id) REFERENCES firearms(firearm_id),
    FOREIGN KEY (bullet_id) REFERENCES bullets(bullet_id),
    FOREIGN KEY (propellant_id) REFERENCES propellants(name),
    FOREIGN KEY (case_id) REFERENCES cases(case_id)
);

CREATE TABLE IF NOT EXISTS measurements (
    measurement_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,

    -- Load data
    charge_grains REAL NOT NULL,

    -- Velocity data
    shot_count INTEGER,  -- Number of shots in this charge
    velocity_fps REAL NOT NULL,  -- Mean velocity
    velocity_sd REAL,  -- Standard deviation
    velocity_es REAL,  -- Extreme spread
    velocity_min_fps REAL,
    velocity_max_fps REAL,

    -- Pressure data (if available)
    pressure_psi REAL,
    pressure_sd REAL,

    -- Individual shot data (optional, JSON array)
    shot_velocities_json TEXT,  -- JSON array of individual shot velocities

    -- Measurement conditions
    chronograph_distance_ft REAL,
    chronograph_model TEXT,

    -- Observations
    case_condition TEXT,  -- e.g., "normal", "ejector mark", "flattened primer"
    notes TEXT,

    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (session_id) REFERENCES test_sessions(session_id),
    UNIQUE(session_id, charge_grains)
);

-- ============================================================
-- Fitted Results Tables
-- ============================================================

CREATE TABLE IF NOT EXISTS fitted_vivacity (
    fit_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL UNIQUE,  -- One fit per session

    -- Fitted parameters
    lambda_base REAL NOT NULL,  -- Base vivacity (normalized: vivacity/1450)
    coeff_a REAL NOT NULL,
    coeff_b REAL NOT NULL,
    coeff_c REAL NOT NULL,
    coeff_d REAL NOT NULL,

    -- Fit quality metrics
    rmse_velocity_fps REAL NOT NULL,
    max_residual_fps REAL,
    r_squared REAL,

    -- Fitting metadata
    optimization_method TEXT DEFAULT 'L-BFGS-B',
    iterations INTEGER,
    regularization REAL DEFAULT 0.0,
    bounds_json TEXT,  -- JSON of bounds used

    -- Validation flags
    vivacity_positive BOOLEAN DEFAULT 1,  -- Vivacity > 0 for all Z ∈ [0,1]
    fit_success BOOLEAN NOT NULL,

    fit_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,

    FOREIGN KEY (session_id) REFERENCES test_sessions(session_id)
);

CREATE TABLE IF NOT EXISTS fit_residuals (
    residual_id INTEGER PRIMARY KEY AUTOINCREMENT,
    fit_id INTEGER NOT NULL,
    charge_grains REAL NOT NULL,
    measured_velocity_fps REAL NOT NULL,
    predicted_velocity_fps REAL NOT NULL,
    residual_fps REAL NOT NULL,

    FOREIGN KEY (fit_id) REFERENCES fitted_vivacity(fit_id)
);

-- ============================================================
-- Analysis Results Tables (for future use)
-- ============================================================

CREATE TABLE IF NOT EXISTS simulation_results (
    simulation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER,
    fit_id INTEGER,  -- Which fitted vivacity was used

    -- Input parameters
    charge_grains REAL NOT NULL,

    -- Simulation outputs
    muzzle_velocity_fps REAL,
    muzzle_energy_ft_lbs REAL,
    peak_pressure_psi REAL,
    muzzle_pressure_psi REAL,
    burnout_distance_in REAL,
    final_burn_percent REAL,
    total_time_s REAL,

    simulation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,

    FOREIGN KEY (session_id) REFERENCES test_sessions(session_id),
    FOREIGN KEY (fit_id) REFERENCES fitted_vivacity(fit_id)
);

-- ============================================================
-- Indexes for Performance
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_measurements_session ON measurements(session_id);
CREATE INDEX IF NOT EXISTS idx_test_sessions_firearm ON test_sessions(firearm_id);
CREATE INDEX IF NOT EXISTS idx_test_sessions_bullet ON test_sessions(bullet_id);
CREATE INDEX IF NOT EXISTS idx_test_sessions_propellant ON test_sessions(propellant_id);
CREATE INDEX IF NOT EXISTS idx_test_sessions_date ON test_sessions(test_date);
CREATE INDEX IF NOT EXISTS idx_fitted_vivacity_session ON fitted_vivacity(session_id);
CREATE INDEX IF NOT EXISTS idx_fit_residuals_fit ON fit_residuals(fit_id);

-- ============================================================
-- Useful Views
-- ============================================================

CREATE VIEW IF NOT EXISTS v_test_session_details AS
SELECT
    ts.session_id,
    ts.test_date,
    ts.temperature_f,
    f.manufacturer AS firearm_mfg,
    f.model AS firearm_model,
    f.barrel_length_in,
    f.caliber_in,
    b.manufacturer AS bullet_mfg,
    b.model AS bullet_model,
    b.weight_gr AS bullet_weight_gr,
    p.manufacturer AS propellant_mfg,
    p.name AS propellant_name,
    p.lot_number AS propellant_lot,
    ts.cartridge_overall_length_in,
    ts.case_volume_gr_h2o,
    COUNT(m.measurement_id) AS num_measurements,
    MIN(m.charge_grains) AS min_charge,
    MAX(m.charge_grains) AS max_charge,
    ts.grt_filename
FROM test_sessions ts
LEFT JOIN firearms f ON ts.firearm_id = f.firearm_id
LEFT JOIN bullets b ON ts.bullet_id = b.bullet_id
LEFT JOIN propellants p ON ts.propellant_id = p.propellant_id
LEFT JOIN measurements m ON ts.session_id = m.session_id
GROUP BY ts.session_id;

CREATE VIEW IF NOT EXISTS v_fitted_results AS
SELECT
    fv.fit_id,
    ts.session_id,
    ts.test_date,
    f.model AS firearm,
    f.barrel_length_in,
    b.model AS bullet,
    b.weight_gr,
    p.name AS propellant,
    ts.temperature_f,
    fv.lambda_base,
    fv.coeff_a,
    fv.coeff_b,
    fv.coeff_c,
    fv.coeff_d,
    fv.rmse_velocity_fps,
    fv.fit_success,
    fv.vivacity_positive
FROM fitted_vivacity fv
JOIN test_sessions ts ON fv.session_id = ts.session_id
JOIN firearms f ON ts.firearm_id = f.firearm_id
JOIN bullets b ON ts.bullet_id = b.bullet_id
JOIN propellants p ON ts.propellant_id = p.propellant_id;

-- ============================================================
-- Example Queries
-- ============================================================

-- Find all test sessions for a specific propellant across different systems
-- SELECT * FROM v_test_session_details WHERE propellant_name = 'N150' ORDER BY test_date;

-- Compare fitted vivacity for same propellant in different configurations
-- SELECT * FROM v_fitted_results WHERE propellant = 'N150' ORDER BY barrel_length_in;

-- Temperature sensitivity analysis (same system, different temps)
-- SELECT temperature_f, lambda_base, rmse_velocity_fps
-- FROM v_fitted_results
-- WHERE firearm = 'Bolt Action' AND bullet = 'Sierra 130gr HPBT' AND propellant = 'N150'
-- ORDER BY temperature_f;
