# BurnForge Workflow Guide

## Primary Workflow: Propellant Characterization

### Overview
The BurnForge workflow is designed for professional propellant characterization using chronograph velocity data. The process transforms experimental measurements into calibrated physics models that predict propellant burnout distance and pressure development.

### Step-by-Step Workflow

#### 1. Data Acquisition (GRT Project Files)
**Primary Method:** Gordon's Reloading Tool (GRT) project files (.grtload, .grtproject)
- **Why GRT?** User-friendly interface for data collection and storage
- **Data Included:** Complete system metadata (firearm, bullet, propellant, environmental conditions)
- **Measurements:** Multiple charge weights with chronograph velocity data

**Alternative:** Manual JSON entry using provided templates

#### 2. Data Import & Validation
```bash
# Import GRT file (CLI)
ballistics import-grt path/to/project.grtload

# Or programmatically
from ballistics import load_grt_project, metadata_to_config
metadata, load_data = load_grt_project("project.grtload")
config = metadata_to_config(metadata)
```

**Validation Checks:**
- Required metadata fields present
- Charge weights positive and reasonable
- Velocity data within physical bounds
- Metadata units converted correctly

#### 3. Database Storage
**System-Specific Storage:** Each fitted model is stored per unique combination of:
- Firearm (barrel length, chamber specs)
- Bullet (weight, jacket type, part number)
- Propellant (name, lot number)
- Environmental conditions (temperature, humidity)

**Benefits:**
- Tracks propellant behavior across different systems
- Enables comparison of same propellant in different rifles
- Supports temperature sensitivity analysis
- Maintains data integrity and traceability

#### 4. Multi-Physics Parameter Fitting
**Core Parameters (Always Fitted):**
- Λ_base: Base vivacity at reference conditions
- Polynomial coefficients (a, b, c, d): Dynamic burn rate shape
- Form function parameters (if using hybrid model)

**Advanced Physics Parameters (Optional, Fitted):**
- Temperature sensitivity (σ): Burn rate temperature dependence
- Bore friction (psi): Continuous energy loss to barrel
- Shot-start pressure (psi): Bullet motion threshold
- Heat transfer coefficient (h_base): Convective heat loss scaling
- Noble-Abel covolume (m³/kg): Finite molecular volume correction

**Fitting Process:**
```python
from ballistics import fit_vivacity_polynomial

# Basic fitting (vivacity only)
fit_result = fit_vivacity_polynomial(load_data, config)

# Advanced fitting (multi-physics)
fit_result = fit_vivacity_polynomial(
    load_data, config,
    fit_temp_sensitivity=True,
    fit_bore_friction=True,
    fit_start_pressure=True,
    fit_covolume=True,
    fit_h_base=True,
    verbose=True
)
```

#### 5. Model Validation & Analysis
**Validation Metrics:**
- RMSE (Root Mean Square Error) < 50 fps
- R² correlation coefficient
- Residual pattern analysis (no systematic bias)
- Vivacity positivity check

**Advanced Validation (New):**
```python
from ballistics import leave_one_out_cv

# Leave-one-out cross-validation for robustness
loo_result = leave_one_out_cv(load_data, config)
print(f"LOO RMSE: {loo_result['loo_rmse']:.1f} fps")

# Bias detection is automatic in fit_vivacity_polynomial
# Warnings appear for systematic bias or trends
```

**Analysis Tools:**
- Burnout distance prediction
- Pressure development curves
- Sensitivity analysis
- Cross-system comparison

#### 6. Results Export & Database Update
**Export Options:**
- JSON format for model persistence
- Python snippet for database updates
- CSV reports for documentation

**Database Update:**
```python
from ballistics import export_fit_results
export_fit_results(fit_result, "varget_model.json", format="json")
export_fit_results(fit_result, "update_script.py", format="python", propellant_name="Varget")
```

### Configuration System

#### Physics Model Selection
```python
# Simple lumped-parameter model (fast, basic accuracy)
config = BallisticsConfig(
    bullet_mass_gr=175,
    charge_mass_gr=42,
    caliber_in=0.308,
    # ... other parameters
    heat_loss_model="convective",  # Default
    # Advanced parameters use defaults
)

# Advanced physics model (accurate, slower)
config = BallisticsConfig(
    # ... basic parameters
    heat_loss_model="convective",
    bore_friction_psi=0.0,  # Will be fitted
    start_pressure_psi=3626.0,  # Default, can be fitted
    # Propellant physics parameters handled in fitting
)
```

#### Fitting Complexity Levels
1. **Basic:** Vivacity polynomial only
2. **Standard:** + Temperature sensitivity, bore friction
3. **Advanced:** + All physics parameters
4. **Research:** Custom parameter selection and bounds

### Quality Assurance

#### Data Requirements
- **Minimum:** 3 charge weights
- **Recommended:** 5-8 charge weights spanning 85-115% of target load
- **Optimal:** 8+ charges with consistent SD < 15 fps

#### Validation Checks
- **Physics:** Vivacity > 0 for all Z ∈ [0,1]
- **Numerical:** Convergence achieved, reasonable parameter bounds
- **Statistical:** RMSE < 50 fps, no systematic residual patterns
- **Consistency:** Model predictions match experimental trends

### Error Handling & Troubleshooting

#### Common Issues
1. **Poor Fit Quality:** Check data consistency, consider physics parameter fitting
2. **Numerical Instability:** Verify parameter bounds, check for extreme values
3. **Import Errors:** Validate GRT file format, check metadata completeness
4. **Database Issues:** Ensure proper permissions, check schema compatibility

#### Diagnostic Tools
- Fit diagnostics plots (residual analysis, vivacity curves)
- Parameter sensitivity analysis
- Cross-validation with held-out data points
- Comparison to published ballistic data

### Integration with GRT Workflow

#### Typical GRT → BurnForge Workflow
1. **GRT:** Collect chronograph data across charge ladder
2. **GRT:** Save project file with complete metadata
3. **BurnForge:** Import GRT file
4. **BurnForge:** Fit multi-physics model
5. **BurnForge:** Validate results and update database
6. **BurnForge:** Generate analysis plots and reports
7. **GRT:** Use fitted parameters for load predictions (future integration)

This workflow enables professional propellant characterization with scientific rigor while maintaining practical usability for reloaders.</content>
<parameter name="filePath">WORKFLOW.md