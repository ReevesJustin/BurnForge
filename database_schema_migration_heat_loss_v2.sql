-- ============================================================
-- Database Schema Migration: Heat Loss Model v2 Parameters
-- ============================================================
--
-- This migration adds support for the modern convective heat transfer
-- coefficient h(t) model and upgraded secondary work coefficient.
--
-- New columns store per-propellant defaults for heat loss and secondary
-- work parameters, enabling calibration from velocity-only data.
--
-- Migration Date: 2025-01-XX
-- Compatibility: Backward compatible (all new columns have defaults)
--
-- ============================================================

-- Add convective heat loss model parameters to propellants table
-- These columns store propellant-specific defaults that can be
-- overridden per-session or per-fit if needed.

ALTER TABLE propellants ADD COLUMN h_base REAL DEFAULT 2000.0;
    -- Base heat transfer coefficient (W/m²·K)
    -- Typical range: 500-5000 W/m²·K
    -- Primary calibration parameter for convective model
    -- Higher values → more heat loss → lower velocity

ALTER TABLE propellants ADD COLUMN h_alpha REAL DEFAULT 0.8;
    -- Pressure scaling exponent (dimensionless)
    -- Literature range: 0.7-0.85
    -- Controls how heat loss scales with pressure
    -- α ≈ 0.8: Turbulent convection pressure dependence

ALTER TABLE propellants ADD COLUMN h_beta REAL DEFAULT 0.3;
    -- Temperature scaling exponent (dimensionless)
    -- Literature range: 0.25-0.35
    -- Controls how heat loss scales with gas temperature
    -- β ≈ 0.3: Thermal conductivity and viscosity effects

ALTER TABLE propellants ADD COLUMN h_gamma REAL DEFAULT 0.3;
    -- Velocity scaling exponent (dimensionless)
    -- Literature range: 0.2-0.4
    -- Controls how heat loss scales with gas velocity
    -- γ ≈ 0.3: Convective transport enhancement

ALTER TABLE propellants ADD COLUMN T_wall_K REAL DEFAULT 500.0;
    -- Barrel wall temperature (K)
    -- Typical range: 400-600 K (260-620°F)
    -- For first-shot cold bore: ~400 K
    -- For hot barrel (rapid fire): ~600 K

ALTER TABLE propellants ADD COLUMN secondary_work_mu REAL DEFAULT 3.0;
    -- Gas entrainment reciprocal coefficient (dimensionless)
    -- Modern replacement for fixed "1/3 rule"
    -- Literature range: 2.2-3.8 for small arms
    -- μ = 3.0: Equivalent to classical 1/3 assumption
    -- μ = 2.5: More aggressive gas entrainment (higher recoil)
    -- μ = 3.5: Conservative entrainment (lower recoil)

-- ============================================================
-- Optional: Add heat loss model selection to test_sessions
-- ============================================================
--
-- If you want to track which heat loss model was used for each test
-- session or fit, add this column to test_sessions:
--
-- ALTER TABLE test_sessions ADD COLUMN heat_loss_model TEXT DEFAULT 'convective';
--     CHECK(heat_loss_model IN ('empirical', 'convective'))
--
-- This allows mixed-mode analysis where legacy and modern fits coexist.

-- ============================================================
-- Optional: Store fitted heat loss parameters in fitted_vivacity
-- ============================================================
--
-- For advanced calibration workflows where h_base is fitted alongside
-- vivacity coefficients, add these columns to fitted_vivacity:
--
-- ALTER TABLE fitted_vivacity ADD COLUMN h_base_fitted REAL;
-- ALTER TABLE fitted_vivacity ADD COLUMN secondary_work_mu_fitted REAL;
--
-- These store the optimized values from multi-parameter fits.
-- If NULL, the propellant defaults were used.

-- ============================================================
-- Migration Verification Query
-- ============================================================
--
-- After running this migration, verify the new columns:
--
-- PRAGMA table_info(propellants);
--
-- Expected output should include:
-- h_base | REAL | 0 | 2000.0 | 0
-- h_alpha | REAL | 0 | 0.8 | 0
-- h_beta | REAL | 0 | 0.3 | 0
-- h_gamma | REAL | 0 | 0.3 | 0
-- T_wall_K | REAL | 0 | 500.0 | 0
-- secondary_work_mu | REAL | 0 | 3.0 | 0

-- ============================================================
-- Usage Notes
-- ============================================================
--
-- 1. BACKWARD COMPATIBILITY:
--    Existing code will continue to work. New columns have sensible defaults
--    that match literature values. The solver automatically uses convective
--    model by default (can be switched to 'empirical' in config).
--
-- 2. CALIBRATION WORKFLOW:
--    - Initial fit: Use default h_base=2000, optimize only vivacity coefficients
--    - Refined fit: If systematic bias remains, add h_base as fit parameter
--      with bounds [500, 5000]
--    - Advanced fit: Co-optimize h_base and secondary_work_mu with vivacity
--
-- 3. PROPELLANT-SPECIFIC TUNING:
--    Fast-burning propellants (pistol powders): May need higher h_base (3000-4000)
--    Slow-burning propellants (magnum rifle): May need lower h_base (1500-2500)
--    This is because burn time affects heat transfer duration.
--
-- 4. REFERENCE VALUES (from literature):
--    Anderson (2020): h ~ 1000-4000 W/m²·K for small arms
--    NATO STANAG 4367: Recommends pressure-dependent h(P) models
--    Gough (2018): μ ∈ [2.5, 3.5] for modern rifle cartridges
--
-- ============================================================
-- Example: Updating propellant with custom parameters
-- ============================================================
--
-- -- Set higher heat loss for fast-burning pistol powder
-- UPDATE propellants
-- SET h_base = 3500.0, secondary_work_mu = 2.8
-- WHERE name = 'TiteGroup';
--
-- -- Set lower heat loss for slow-burning magnum rifle powder
-- UPDATE propellants
-- SET h_base = 1800.0, secondary_work_mu = 3.2
-- WHERE name = 'H1000';
--
-- ============================================================
