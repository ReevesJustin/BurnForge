-- Migration to add pressure-dependent burn rate correction (alpha)
-- Adds alpha parameter for dZ/dt = (Lambda_base + alpha * p) * pi(Z)

ALTER TABLE propellants ADD COLUMN alpha REAL DEFAULT 0.0 CHECK (alpha >= 0.0 AND alpha <= 0.001);

-- Update version (optional)
-- INSERT OR IGNORE INTO version (version, description) VALUES (5, 'Added pressure-dependent burn rate correction alpha');