-- Migration to add grain geometry support to propellants table
-- Run this migration to add geometry column for hybrid burn rate model

ALTER TABLE propellants ADD COLUMN grain_geometry TEXT DEFAULT 'spherical' CHECK (grain_geometry IN ('spherical', 'degressive', 'single-perf', 'neutral', '7-perf', 'progressive'));

-- Update existing propellants with common geometries
-- Many ball powders are spherical/degressive
UPDATE propellants SET grain_geometry = 'spherical' WHERE name LIKE '%ball%' OR name LIKE '%N1%' OR name LIKE '%N5%';
UPDATE propellants SET grain_geometry = 'single-perf' WHERE name LIKE '%varget%' OR name LIKE '%H4%' OR name LIKE '%IMR4%';
UPDATE propellants SET grain_geometry = '7-perf' WHERE name LIKE '%H5%' OR name LIKE '%IMR5%';

-- Version tracking not implemented in this migration