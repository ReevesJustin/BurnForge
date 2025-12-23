# Gemini CLI Assistant - IB_Solver Project Guide

**Version:** Phase 2 + Physics v3 Complete
**Date:** 2025-12-23
**Purpose:** LLM-optimized guide for interacting with IB_Solver using Gemini

---

## System Prompt for Gemini

```
You are a technical assistant for the IB_Solver internal ballistics modeling project. Your role is to help users:
1. Process GRT (Gordon's Reloading Tool) load files from data/grt_files/
2. Run fitting and analysis using existing Python tools
3. Interpret results and generate reports
4. Query the SQLite database
5. Generate predictions for new loads

CRITICAL CONSTRAINTS:
- Use clinical, technical language only (no marketing, no motivational text)
- Use EXISTING Python scripts only - DO NOT modify any Python code
- Database manipulation limited to existing script capabilities
- Always show commands for user to execute
- Validate all inputs (units, bounds, required fields)
- Report errors clearly with diagnostic suggestions
- Units: grain (gr), fps, inches (in), psi, Fahrenheit (°F), Kelvin (K)

PROJECT CONTEXT:
- Working directory: /home/justin/projects/IB_Solver
- Python environment: ./venv/bin/python
- Database: data/ballistics_data.db (SQLite)
- GRT files: data/grt_files/*.grtload (user copies files here)
- Source code: src/ballistics/*.py (importable modules - DO NOT MODIFY)

WORKFLOW:
1. User specifies GRT file (by name or partial match)
2. Run baseline fit (Lambda + polynomial)
3. Optionally run multi-parameter fit (user specifies: temp, friction, start, covolume)
4. Generate report (user chooses: summary or detail)
5. Compare baseline vs enhanced (if multi-parameter run)
6. Optionally show database update commands (user executes)

PRIMARY TOOL:
  ./venv/bin/python gemini_workflow.py --file <name> [options]

EXECUTION MODEL:
- You generate commands using existing scripts
- User executes commands and shares output
- You interpret results and suggest next steps
- For database updates, you show SQL/Python commands for user review
```

---

## PRIMARY TOOL: gemini_workflow.py

**Location:** Project root
**Purpose:** Complete GRT file analysis workflow - Baseline + Multi-Parameter Fitting + Reporting

### Command Syntax

```bash
./venv/bin/python gemini_workflow.py --file <name> [--detail] [--fit params] [--update-db]
```

### Parameters

| Parameter | Required | Description | Examples |
|-----------|----------|-------------|----------|
| `--file` | Yes | GRT file name (full or partial) | `65CRM`, `my_load.grtload` |
| `--detail` | No | Generate detailed report (vs summary) | `--detail` |
| `--fit` | No | Physics parameters to fit | `temp`, `temp,friction`, `temp,friction,start` |
| `--update-db` | No | Show database update commands | `--update-db` |
| `--verbose` | No | Show fitting iteration details | `--verbose` |

### Fit Parameter Options

| Keyword | Parameter | Effect |
|---------|-----------|--------|
| `temp` or `temperature` | Temperature sensitivity | Calibrate σ (/K) |
| `friction` or `bore` | Bore friction | Calibrate bore_friction_psi |
| `start` or `pressure` | Shot-start pressure | Calibrate start_pressure_psi |
| `covolume` | Noble-Abel covolume | Calibrate covolume (rarely used) |

**Combine with commas:** `--fit temp,friction,start`

### Examples

```bash
# Summary report, baseline fit only
./venv/bin/python gemini_workflow.py --file 65CRM

# Detailed report, baseline fit
./venv/bin/python gemini_workflow.py --file my_load.grtload --detail

# Multi-parameter fit with temperature + friction
./venv/bin/python gemini_workflow.py --file 65CRM --fit temp,friction

# Full analysis with all physics parameters
./venv/bin/python gemini_workflow.py --file 65CRM --fit temp,friction,start --detail

# Show database update commands after fitting
./venv/bin/python gemini_workflow.py --file 65CRM --fit temp,friction --update-db

# Verbose output to see fitting progress
./venv/bin/python gemini_workflow.py --file 65CRM --fit temp --verbose --detail
```

---

## Additional Tools

### Core Modules (Read-Only Reference)

**Location:** `src/ballistics/` (DO NOT MODIFY)

| Module | Purpose | Used By |
|--------|---------|---------|
| `solver.py` | Core ODE ballistics solver | gemini_workflow.py |
| `fitting.py` | Parameter optimization | gemini_workflow.py |
| `io.py` | GRT/CSV file loading | gemini_workflow.py |
| `database.py` | Database operations | gemini_workflow.py |
| `props.py` | Property classes | All scripts |

### Diagnostic Scripts

**Location:** Project root

| Script | Purpose | When to Use |
|--------|---------|-------------|
| `diagnose_physics_v3.py` | Individual physics parameter effects | When RMSE is high (>200 fps) |
| `verify_phase2.py` | System installation check | First-time setup verification |
| `tests/test_solver.py` | Unit tests | After any system changes |

---

## Common Workflows

### Setup: Copy GRT Files

**First time setup:**

```bash
# Copy your GRT files to the data directory
cp /path/to/your/*.grtload data/grt_files/

# Verify files are there
ls data/grt_files/
```

**Gemini can then find files automatically:**
- By full name: `65CRM_130SMK_N150_Starline_Initial.grtload`
- By partial match: `65CRM`, `N150`, `130SMK`
- By extension: searches all `.grtload` files

---

### 1. Basic Analysis (Summary Report)

**Goal:** Quick fit quality assessment

**Command:**
```bash
./venv/bin/python gemini_workflow.py --file 65CRM
```

**What you get:**
- Cartridge/propellant/bullet info
- Data point count and charge range
- Baseline fit RMSE
- Residual statistics
- Systematic bias check
- Recommendations

**Plain language to Gemini:**
> "Analyze the 65CRM file with a summary report"

### 2. Detailed Analysis

**Goal:** Full breakdown of fit quality and residuals

**Command:**
```bash
./venv/bin/python gemini_workflow.py --file 65CRM --detail
```

**What you get (in addition to summary):**
- Individual charge/velocity/residual table
- Fitted parameter values (Lambda_base, a, b, c, d)
- Detailed residual statistics
- Caliber, case brand, bullet type (if in GRT file)

**Plain language to Gemini:**
> "Give me a detailed analysis of the 65CRM file"

### 3. Multi-Parameter Fitting (Temperature Sensitivity)

**Goal:** Include temperature sensitivity in the fit

**Command:**
```bash
./venv/bin/python gemini_workflow.py --file 65CRM --fit temp
```

**What you get:**
- Baseline fit results
- Enhanced fit results (with temp sensitivity)
- Comparison table showing improvement
- Fitted σ value (/K and /°F)
- Recommendation on whether enhancement is worth it

**Plain language to Gemini:**
> "Fit the 65CRM data with temperature sensitivity and compare to baseline"

---

### 4. Multi-Parameter Fitting (Multiple Physics)

**Goal:** Fit temperature sensitivity + bore friction + shot-start pressure

**Command:**
```bash
./venv/bin/python gemini_workflow.py --file 65CRM --fit temp,friction,start --detail
```

**What you get:**
- Baseline fit
- Enhanced fit with all three parameters
- Detailed comparison
- All fitted physics parameter values
- Bias reduction analysis

**Plain language to Gemini:**
> "Fit the 65CRM data with temperature, friction, and shot-start pressure, with detailed output"

### 5. Database Update Preparation

**Goal:** Generate commands to save fitted parameters to database

**Command:**
```bash
./venv/bin/python gemini_workflow.py --file 65CRM --fit temp,friction --update-db
```

**What you get:**
- Complete analysis report
- Python code block for database update (for review)
- SQL code block for database update (alternative)
- Warning to verify parameters before executing

**YOU execute the update** (after review):
```python
from ballistics import database

database.update_propellant_coefficients(
    'N150',
    0.047181,
    (1.059, -0.822, 0.119, 0.119)
)
```

**Plain language to Gemini:**
> "Analyze 65CRM with temp and friction fitting, and show me how to update the database"

### 6. Find Best Fit Strategy

**Goal:** Compare different fitting approaches to find optimal strategy

**Commands (run sequentially):**
```bash
# 1. Baseline
./venv/bin/python gemini_workflow.py --file 65CRM

# 2. With temperature
./venv/bin/python gemini_workflow.py --file 65CRM --fit temp

# 3. With friction
./venv/bin/python gemini_workflow.py --file 65CRM --fit friction

# 4. With both
./venv/bin/python gemini_workflow.py --file 65CRM --fit temp,friction
```

**Share all 4 RMSEs with Gemini**, who will analyze:
- Which parameters provide most improvement
- Whether improvements justify added complexity
- Recommended strategy for similar loads

**Plain language to Gemini:**
> "Help me figure out the best fitting strategy for my 65CRM data. Here are the RMSEs I got: [paste results]"

### 7. Query Database

**Goal:** Check what's in the database

**Commands:**
```python
# Quick check via Python one-liner
./venv/bin/python -c "from ballistics import database; print(database.list_propellants())"

# Or via SQL
sqlite3 data/ballistics_data.db "SELECT name FROM propellants ORDER BY name;"

# Get specific propellant details
./venv/bin/python -c "
from ballistics import PropellantProperties
prop = PropellantProperties.from_database('N150')
print(f'Lambda_base: {prop.Lambda_base:.6f}')
print(f'Coeffs: {prop.poly_coeffs}')
print(f'Temp sens: {prop.temp_sensitivity_sigma_per_K:.6f} /K')
"
```

**Plain language to Gemini:**
> "List all propellants in the database"

> "What are the current parameters for N150?"

### 7. Generate Prediction for New Load

**Goal:** Predict velocity for a specific charge weight

**Step-by-step:**

```python
from ballistics import solve_ballistics, PropellantProperties, BulletProperties, BallisticsConfig

# Define your load
prop = PropellantProperties.from_database("N150")
bullet = BulletProperties.from_database("Copper Jacket over Lead")

config = BallisticsConfig(
    bullet_mass_gr=130.0,
    charge_mass_gr=38.0,  # Your test charge
    caliber_in=0.264,
    case_volume_gr_h2o=52.58,
    barrel_length_in=18.0,
    cartridge_overall_length_in=2.780,
    propellant=prop,
    bullet=bullet,
    temperature_f=70.0
)

# Solve
result = solve_ballistics(config)

# Results
print(f"Predicted velocity: {result['muzzle_velocity_fps']:.1f} fps")
print(f"Peak pressure: {result['peak_pressure_psi']:.0f} psi")
print(f"Muzzle energy: {result['muzzle_energy_ft_lbs']:.0f} ft-lbs")

if 'burnout_distance_from_bolt_in' in result:
    print(f"Burnout at: {result['burnout_distance_from_bolt_in']:.2f} in from bolt")
else:
    print(f"Muzzle burn: {result['muzzle_burn_percentage']:.1f}%")
```

**Plain language command:**
> "What velocity will I get with 38.0 grains of N150 behind a 130gr bullet in 6.5 Creedmoor at 70°F?"

---

## Database Schema Quick Reference

### Propellants Table

**Columns:**
- `name` (TEXT PRIMARY KEY)
- `manufacturer` (TEXT)
- `vivacity` (REAL) - s⁻¹ per 100 bar
- `base` (TEXT) - 'S' (single-base) or 'D' (double-base)
- `force` (REAL) - ft-lbf/lbm
- `temp_0` (REAL) - Flame temperature (K)
- `temp_coeff_v`, `temp_coeff_p` (REAL) - Legacy temp coefficients
- `bulk_density` (REAL) - lbm/in³
- `poly_a`, `poly_b`, `poly_c`, `poly_d` (REAL) - Polynomial coefficients
- `covolume_m3_per_kg` (REAL) - Noble-Abel covolume (m³/kg)
- `temp_sensitivity_sigma_per_K` (REAL) - Temperature sensitivity (/K)

### Bullet Types Table

**Columns:**
- `name` (TEXT PRIMARY KEY)
- `s` (REAL) - Strength factor
- `rho_p` (REAL) - Density (lbm/in³)
- `start_pressure_psi` (REAL) - Shot-start pressure threshold (psi)

### Adding New Entries

**Propellant:**
```sql
INSERT INTO propellants (
    name, manufacturer, vivacity, base, force, temp_0,
    bulk_density, poly_a, poly_b, poly_c, poly_d,
    covolume_m3_per_kg, temp_sensitivity_sigma_per_K
) VALUES (
    'H4350', 'Hodgdon', 60.0, 'S', 387000, 3500,
    0.0584, 1.0, -1.0, 0.0, 0.0,
    0.001, 0.002
);
```

**Bullet Type:**
```sql
INSERT INTO bullet_types (name, s, rho_p, start_pressure_psi)
VALUES ('Monolithic Copper', 4.0, 0.324, 4000.0);
```

---

## Example Interactions with Gemini

### Example 1: Basic Analysis

**User:** "I have a GRT file called `65CRM_130SMK_N150_Starline_Initial.grtload`. Can you analyze the fit quality?"

**Gemini Response:**
```
I'll help you analyze that GRT file. Here's the command to run:

./venv/bin/python quick_fit_analysis.py

This script will:
1. Load the GRT file data
2. Fit Lambda_base and polynomial coefficients
3. Show RMSE, residuals, and systematic bias
4. Compare to constant-Lambda fit
5. Analyze vivacity curve shape

Would you like me to walk through running this, or would you prefer
to run it yourself and share the output for me to interpret?
```

### Example 2: Multi-Step Workflow

**User:** "I want to fit this data with temperature sensitivity included and see if it improves the fit"

**Gemini Response:**
```
I'll guide you through a two-step fitting comparison:

Step 1: Baseline fit (Lambda + polynomial only)
```python
from ballistics import load_grt_project, metadata_to_config, fit_vivacity_polynomial

metadata, load_data = load_grt_project("65CRM_130SMK_N150_Starline_Initial.grtload")
config = metadata_to_config(metadata)

# Baseline
fit_baseline = fit_vivacity_polynomial(load_data, config, verbose=True)
print(f"Baseline RMSE: {fit_baseline['rmse_velocity']:.2f} fps")
```

Step 2: With temperature sensitivity
```python
# With temp sensitivity
fit_with_temp = fit_vivacity_polynomial(
    load_data, config,
    fit_temp_sensitivity=True,
    verbose=True
)
print(f"With temp sens RMSE: {fit_with_temp['rmse_velocity']:.2f} fps")
print(f"Improvement: {fit_baseline['rmse_velocity'] - fit_with_temp['rmse_velocity']:.2f} fps")
```

Run these and share the RMSE values - I'll help interpret whether the
improvement justifies the additional parameter.
```

### Example 3: Database Update

**User:** "How do I add the fitted parameters for N150 to the database?"

**Gemini Response:**
```
After you've completed the fit, use this code:

```python
from ballistics import database

# Your fitted values (replace with actual values from fit)
propellant_name = "N150"
Lambda_base_fitted = 0.047181  # From fit_result['Lambda_base']
coeffs_fitted = (1.059, -0.822, 0.119, 0.119)  # From fit_result['coeffs']

# Update database
database.update_propellant_coefficients(
    propellant_name,
    Lambda_base_fitted,
    coeffs_fitted
)

print(f"✓ Updated {propellant_name} with fitted parameters")

# Verify
from ballistics import PropellantProperties
prop = PropellantProperties.from_database(propellant_name)
print(f"Database now shows Lambda_base = {prop.Lambda_base:.6f}")
```

Note: This updates the vivacity parameters only. If you also fitted
temperature sensitivity, you'll need to update that separately via SQL.
```

### Example 4: Prediction Query

**User:** "What's the expected velocity for 37.5 grains of N150 in my 6.5 Creedmoor?"

**Gemini Response:**
```
I'll generate a prediction. Please confirm these parameters:

From your GRT file:
- Cartridge: 6.5 Creedmoor
- Barrel length: 18.0 in
- Bullet: 130 gr
- COAL: 2.780 in
- Case volume: 52.58 gr H2O
- Temperature: (please specify, default 70°F)

Charge weight: 37.5 gr N150

Command to run:

```python
from ballistics import solve_ballistics, PropellantProperties, BulletProperties, BallisticsConfig

prop = PropellantProperties.from_database("N150")
bullet = BulletProperties.from_database("Copper Jacket over Lead")

config = BallisticsConfig(
    bullet_mass_gr=130.0,
    charge_mass_gr=37.5,
    caliber_in=0.264,
    case_volume_gr_h2o=52.58,
    barrel_length_in=18.0,
    cartridge_overall_length_in=2.780,
    propellant=prop,
    bullet=bullet,
    temperature_f=70.0
)

result = solve_ballistics(config)
print(f"Velocity: {result['muzzle_velocity_fps']:.1f} fps")
print(f"Pressure: {result['peak_pressure_psi']:.0f} psi")
print(f"Energy: {result['muzzle_energy_ft_lbs']:.0f} ft-lbs")
```

Shall I proceed with these parameters?
```

---

## Advanced Usage: Custom Analysis Scripts

### Template for Custom Fitting Analysis

Save as `my_custom_fit.py`:

```python
"""Custom fitting analysis script."""

import sys
sys.path.insert(0, 'src')

from ballistics import load_grt_project, metadata_to_config, fit_vivacity_polynomial
import numpy as np

# Configuration
GRT_FILE = "path/to/your/file.grtload"
FIT_TEMP_SENS = True
FIT_BORE_FRIC = True

# Load data
metadata, load_data = load_grt_project(GRT_FILE)
config = metadata_to_config(metadata)

print(f"Cartridge: {metadata['cartridge']}")
print(f"Propellant: {metadata['propellant_name']}")
print(f"Data points: {len(load_data)}")

# Fit
fit_result = fit_vivacity_polynomial(
    load_data, config,
    fit_temp_sensitivity=FIT_TEMP_SENS,
    fit_bore_friction=FIT_BORE_FRIC,
    verbose=True
)

# Analyze residuals
residuals = np.array(fit_result['residuals'])
charges = load_data['charge_grains'].values
measured = load_data['mean_velocity_fps'].values
predicted = np.array(fit_result['predicted_velocities'])

print(f"\nFit Quality:")
print(f"  RMSE: {fit_result['rmse_velocity']:.2f} fps")
print(f"  Max residual: {np.max(np.abs(residuals)):.2f} fps")
print(f"  Mean bias: {np.mean(residuals):+.2f} fps")

# Systematic bias check
mid = len(residuals) // 2
print(f"\nSystematic Bias:")
print(f"  Lower charges: {np.mean(residuals[:mid]):+.2f} fps")
print(f"  Upper charges: {np.mean(residuals[mid:]):+.2f} fps")

# Detail table
print(f"\n{'Charge':>8} {'Measured':>10} {'Predicted':>10} {'Error':>10}")
print("-" * 42)
for i in range(len(charges)):
    print(f"{charges[i]:8.1f} {measured[i]:10.1f} {predicted[i]:10.1f} {residuals[i]:+10.1f}")
```

**Plain language command:**
> "Create a custom analysis script that fits my data with temperature sensitivity and shows a detailed residual breakdown"

---

## Troubleshooting Guide

### Common Issues

**1. "Propellant 'XXX' not found in database"**

**Solution:** Add the propellant to the database first:
```python
# Check what's available
from ballistics import database
print(database.list_propellants())

# Add new propellant via SQL or use closest match
```

**2. "RMSE very high (>500 fps)"**

**Diagnosis:**
```python
# Run physics diagnostics
./venv/bin/python diagnose_physics_v3.py
```

**Likely causes:**
- Lambda_base far from optimal (dominant effect)
- Wrong propellant selected from database
- Data quality issues (inconsistent velocities)

**3. "Fitting not converging (Success: False)"**

**Solution:** Try sequential fitting:
```python
# Step 1: Fit Lambda only (reduce parameters)
fit1 = fit_vivacity_polynomial(
    load_data, config,
    bounds=([0.01, 1.0, -0.1, -0.1, -0.1],
            [0.15, 1.0, 0.1, 0.1, 0.1])  # Tighter polynomial bounds
)

# Step 2: Use fit1 as initial guess for full fit
initial = (fit1['Lambda_base'],) + fit1['coeffs']
fit2 = fit_vivacity_polynomial(load_data, config, initial_guess=initial)
```

**4. "Negative vivacity warning"**

**Cause:** Polynomial goes negative somewhere in [0, 1]

**Solution:** Add regularization or tighter bounds:
```python
fit = fit_vivacity_polynomial(
    load_data, config,
    regularization=0.01,  # Penalize large coefficients
    bounds=([0.01, 0.5, -1.0, -1.0, -1.0],  # Tighter bounds
            [0.15, 1.5, 1.0, 1.0, 1.0])
)
```

---

## Physics Parameters Reference

### Conservative Defaults (Post-v3)

| Parameter | Default | Range | Effect |
|-----------|---------|-------|--------|
| `covolume_m3_per_kg` | 0.001 | [0.0008, 0.0012] | +304 fps (largest) |
| `temp_sensitivity_sigma_per_K` | 0.002 | [0.0, 0.01] | ~1 fps/°F |
| `bore_friction_psi` | 0 | [0, 4000] | 0 fps (disabled) |
| `start_pressure_psi` | 3626 | [1000, 12000] | Threshold mechanism |

### When to Fit Each Parameter

**Lambda_base + polynomial:** Always (baseline)

**temp_sensitivity:** If you have:
- Temperature-varying data, OR
- Want to predict temperature effects

**bore_friction:** If residuals show:
- Systematic under-prediction across all charges, OR
- Linear bias pattern

**start_pressure:** If you observe:
- Poor prediction at lowest charges, OR
- Bullet seating significantly different from standard

**covolume:** Rarely (usually keep fixed at 0.001)

---

## Quick Command Reference

```bash
# Environment setup
source venv/bin/activate  # If using venv manually
./venv/bin/python         # Prefix for all Python commands

# Verification
./venv/bin/python verify_phase2.py

# Analysis scripts
./venv/bin/python quick_fit_analysis.py
./venv/bin/python diagnose_physics_v3.py
./venv/bin/python test_enhanced_fitting.py

# Tests
./venv/bin/python tests/test_solver.py
./venv/bin/python tests/test_io.py

# Database inspection (via Python)
./venv/bin/python -c "from ballistics import database; print(database.list_propellants())"

# Database inspection (via sqlite3)
sqlite3 data/ballistics_data.db "SELECT name, Lambda_base FROM propellants;"
```

---

## Best Practices for Gemini Interactions

### DO:
✅ Provide clear, specific information (file names, cartridge, propellant)
✅ Share actual output/errors for Gemini to diagnose
✅ Ask for explanations of fitted parameters
✅ Request incremental workflows (fit baseline, then add physics)
✅ Verify database contents before fitting

### DON'T:
❌ Assume Gemini knows your file names (always specify)
❌ Skip baseline fit and go straight to multi-parameter
❌ Ignore systematic bias warnings
❌ Update database without verifying fitted parameters are reasonable
❌ Use fitted parameters outside their calibration range

---

## Appendix: Unit Conversion Quick Reference

| Quantity | Common Units | Conversion |
|----------|-------------|------------|
| Mass | grain (gr), pound (lb) | 1 lb = 7000 gr |
| Pressure | psi, bar | 1 bar ≈ 14.5 psi |
| Temperature | °F, K | K = (°F - 32) × 5/9 + 273.15 |
| Velocity | fps (ft/s), m/s | 1 m/s ≈ 3.28 fps |
| Energy | ft-lbf, Joules | 1 J ≈ 0.738 ft-lbf |
| Volume | in³, gr H₂O | -- (direct measurement) |
| Length | inches (in), mm | 1 in = 25.4 mm |

---

**End of Gemini CLI Guide**
**For questions or issues, refer to:** `IMPLEMENTATION_SUMMARY.md`, `PHYSICS_V3_COMPLETE.md`
