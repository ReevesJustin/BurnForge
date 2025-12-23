-- Database Migration: Physics Enhancements v3
-- Adds support for new physics parameters introduced in PhysicsUpdate.md
--
-- New Features:
-- 1. Noble-Abel equation of state (covolume correction)
-- 2. Shot-start pressure (calibratable bullet motion threshold)
-- 3. Temperature sensitivity for burn rate
-- 4. Bore friction (pressure-equivalent resistance)
--
-- Migration Date: 2025-12-23
-- Backward Compatible: Yes (uses default values for existing records)

-- ============================================================
-- Add New Columns to propellants Table
-- ============================================================

-- Covolume for Noble-Abel EOS (m³/kg)
-- Default: 0.001 m³/kg (literature value for nitrocellulose-based propellants)
-- Typical range: [0.0008, 0.0012] m³/kg
ALTER TABLE propellants
ADD COLUMN covolume_m3_per_kg REAL DEFAULT 0.001
CHECK (covolume_m3_per_kg >= 0.0008 AND covolume_m3_per_kg <= 0.0012);

-- Temperature sensitivity coefficient (1/K)
-- Default: 0.002 /K (conservative, ~1 fps/°F for most propellants)
-- Typical range: [0.002, 0.008] /K
ALTER TABLE propellants
ADD COLUMN temp_sensitivity_sigma_per_K REAL DEFAULT 0.002
CHECK (temp_sensitivity_sigma_per_K >= 0.0 AND temp_sensitivity_sigma_per_K <= 0.01);

-- ============================================================
-- Add New Columns to bullet_types Table
-- ============================================================

-- Shot-start pressure threshold (psi)
-- Default: 3626 psi (250 bar, typical for copper jacketed bullets)
-- Typical range: [1000, 12000] psi depending on seating and crimp
ALTER TABLE bullet_types
ADD COLUMN start_pressure_psi REAL DEFAULT 3626.0
CHECK (start_pressure_psi >= 500.0 AND start_pressure_psi <= 15000.0);

-- ============================================================
-- Migration Notes
-- ============================================================

-- All existing propellants will receive default values:
--   - covolume_m3_per_kg = 0.001 (standard for gun propellants)
--   - temp_sensitivity_sigma_per_K = 0.002 (conservative, ~1 fps/°F)
--
-- All existing bullet types will receive:
--   - start_pressure_psi = 3626.0 (standard copper jacket)
--
-- These defaults ensure immediate compatibility with existing code while
-- allowing calibration to refine values from velocity data.

-- Bore friction (bore_friction_psi) is added to BallisticsConfig only,
-- not stored in database (user-adjustable parameter, not propellant property).

-- ============================================================
-- Verification Queries
-- ============================================================

-- Check that all propellants have valid covolume and temp_sensitivity:
-- SELECT name, covolume_m3_per_kg, temp_sensitivity_sigma_per_K
-- FROM propellants
-- WHERE covolume_m3_per_kg IS NULL OR temp_sensitivity_sigma_per_K IS NULL;

-- Check that all bullet types have valid start_pressure_psi:
-- SELECT name, start_pressure_psi FROM bullet_types WHERE start_pressure_psi IS NULL;

-- ============================================================
-- Rollback Instructions (if needed)
-- ============================================================

-- To rollback this migration:
-- ALTER TABLE propellants DROP COLUMN covolume_m3_per_kg;
-- ALTER TABLE propellants DROP COLUMN temp_sensitivity_sigma_per_K;
-- ALTER TABLE bullet_types DROP COLUMN start_pressure_psi;
