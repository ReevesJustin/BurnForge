# Systematic Fitting Bias Analysis Report

**Date:** 2025-12-24
**Status:** Critical Database Bug Identified
**Impact:** ALL predictions are 2-3x too high due to incorrect propellant force values

---

## Executive Summary

Testing revealed that **ALL velocity predictions are systematically 2-3x too high** (predicting ~6000 fps when measured ~2600 fps). The root cause is **incorrect propellant force values in the database** - all propellants have `force = 3,650,000` when they should be ~350,000-400,000.

**Before any bias mitigation strategies can be evaluated, the database must be corrected.**

---

## Testing Results

### Test Data

- **Dataset 1:** 65CM_130SMK_Varget_Starline.grtload (5 points, 37-39 gr)
- **Dataset 2:** 65CM_130SMK_N150_Starline.grtload (6 points, 36.5-39 gr)

### Current Performance (WITH DATABASE BUG)

| Metric | Varget | N150 |
|--------|--------|------|
| RMSE | 3211 fps | 3206 fps |
| Mean Residual | +3237 fps | +3224 fps |
| Low Charge Bias | +3187 fps | +3156 fps |
| High Charge Bias | +3290 fps | +3293 fps |
| Bias Delta | -103 fps | -137 fps |

### Example Predictions

```
Varget, 37.0 gr:
  Measured: 2555 fps
  Predicted: 5727 fps  ❌ (2.2x too high)
  Residual: +3172 fps

Varget, 39.0 gr:
  Measured: 2679 fps
  Predicted: 5993 fps  ❌ (2.2x too high)
  Residual: +3314 fps
```

---

## Root Cause Analysis

### 1. Database Propellant Force Values (CRITICAL BUG)

**All propellants have incorrect force values:**

```sql
SELECT name, force FROM propellants WHERE name IN ('Varget', 'N150', 'H4350');
-- Result:
-- H4350  | 3,650,000.0
-- N150   | 3,650,000.0
-- Varget | 3,650,000.0
```

**Expected values:**
- Typical propellant force: 1000-1050 kJ/kg
- Converting to ft·lbf/lbm: ~350,000-400,000 ft·lbf/lbm
- **Database values are ~10x too high**

**Impact on physics:**
```python
# From solver.py line 273:
P_estimate = (C * Z * F) / volume

# F = 3,650,000 → pressures ~10x too high → velocities ~3x too high
```

### 2. Code Bugs Fixed

✅ **solver.py:541** - `return_trace` variables not defined
✅ **fitting.py:274-373** - Incorrect indentation in `_objective_function`

### 3. Optimizer Issues (Secondary)

- Solver becomes unstable with certain parameter combinations
- Error: "Required step size is less than spacing between numbers"
- Optimizer converges prematurely (2 iterations) due to bad initial conditions
- Initial guess (1.0, -1.0, 0.0, 0.0) gives terrible predictions

---

## Solutions & Recommendations

### IMMEDIATE (Critical Priority)

#### 1. **Fix Propellant Database Force Values**

```sql
-- Divide all force values by 10 as first approximation:
UPDATE propellants SET force = force / 10.0;

-- Or set specific values based on literature:
UPDATE propellants SET force = 365000.0 WHERE name = 'Varget';  -- ~1000 kJ/kg
UPDATE propellants SET force = 355000.0 WHERE name = 'N150';    -- ~975 kJ/kg
UPDATE propellants SET force = 368000.0 WHERE name = 'H4350';   -- ~1010 kJ/kg
```

**Verification needed:**
- Cross-reference with QuickLOAD, GRT, or manufacturer data
- Verify unit conversions (kJ/kg → ft·lbf/lbm)
- Test predictions against known velocity data

#### 2. **Better Initial Guess for Fitting**

```python
# Instead of using database defaults (which may be wrong):
initial_guess = [
    0.015,    # Lambda_base (lower starting point)
    1.0,      # a
    -0.3,     # b (less aggressive)
    0.0,      # c
    0.0       # d
]
```

### HIGH PRIORITY (After Database Fix)

#### 3. **Implement 6-Parameter Polynomial**

Extend from 4-parameter (a,b,c,d) to 6-parameter (a,b,c,d,e,f):

```python
# In burn_rate.py calc_vivacity():
poly_value = a + b*Z + c*Z**2 + d*Z**3 + e*Z**4 + f*Z**5

# Update bounds in fitting.py:
bounds_lower = [0.001, -2.0, -2.0, -2.0, -2.0, -2.0, -2.0]
bounds_upper = [0.15,   2.0,  2.0,  2.0,  2.0,  2.0,  2.0]
```

**Benefits:**
- Can capture more complex burn rate evolution
- Better fit for early vs late burn behavior
- Should reduce systematic bias between low/high charges

#### 4. **Bias Detection & Reporting**

Add to `fit_vivacity_polynomial()`:

```python
def detect_systematic_bias(residuals, charges, threshold=30):
    """Detect low-charge vs high-charge bias."""
    max_charge = charges.max()
    min_charge = charges.min()

    # Split into thirds
    low_mask = charges <= min_charge + (max_charge - min_charge) / 3
    high_mask = charges >= max_charge - (max_charge - min_charge) / 3

    low_bias = np.mean(residuals[low_mask])
    high_bias = np.mean(residuals[high_mask])
    bias_delta = abs(low_bias - high_bias)

    if bias_delta > threshold:
        warnings.warn(
            f"Systematic bias detected: {bias_delta:.1f} fps difference "
            f"between low ({low_bias:.1f}) and high ({high_bias:.1f}) charges. "
            f"Consider using higher-order polynomial or checking physics parameters."
        )

    return {
        'low_bias': low_bias,
        'high_bias': high_bias,
        'bias_delta': bias_delta,
        'has_systematic_bias': bias_delta > threshold
    }
```

#### 5. **Leave-One-Out Cross-Validation**

```python
def cross_validate_fit(load_data, config_base, **fit_kwargs):
    """Perform LOO-CV to assess fit robustness."""
    cv_errors = []

    for i in range(len(load_data)):
        # Leave one out
        train_data = load_data.drop(i)
        test_data = load_data.iloc[[i]]

        # Fit on training data
        fit_result = fit_vivacity_polynomial(train_data, config_base, **fit_kwargs)

        # Predict on test data
        test_config = copy(config_base)
        test_config.charge_mass_gr = test_data['charge_grains'].values[0]
        test_config.propellant.Lambda_base = fit_result['Lambda_base']
        test_config.propellant.poly_coeffs = fit_result['coeffs']

        result = solve_ballistics(test_config)
        predicted = result['muzzle_velocity_fps']
        measured = test_data['mean_velocity_fps'].values[0]
        cv_errors.append(predicted - measured)

    return {
        'cv_rmse': np.sqrt(np.mean(np.array(cv_errors)**2)),
        'cv_errors': cv_errors,
        'cv_mean_error': np.mean(cv_errors)
    }
```

### MEDIUM PRIORITY

#### 6. **Multi-Parameter Fitting Enhancements**

Allow fitting more physics parameters simultaneously:

```python
fit_vivacity_polynomial(
    load_data,
    config,
    fit_temp_sensitivity=True,      # σ temperature coefficient
    fit_bore_friction=True,          # Friction losses
    fit_start_pressure=True,         # Shot-start threshold
    fit_h_base=True,                 # Heat transfer coefficient
    include_pressure_penalty=True,   # Use GRT pressure reference
    pressure_weight=0.3,             # Balance velocity vs pressure fit
)
```

**Note:** Only enable if you have pressure data from GRT. More parameters risk overfitting with limited data.

#### 7. **Geometric Form Function Mode**

For propellants with known grain geometry:

```python
# Instead of polynomial vivacity:
config.use_form_function = True
config.propellant.grain_geometry = 'single-perf'  # or '7-perf', 'spherical'

fit_result = fit_vivacity_polynomial(
    load_data,
    config,
    use_form_function=True,  # Fits Lambda_base + alpha instead of polynomial
)
```

**Benefits:**
- Physics-based instead of empirical
- Fewer parameters to fit
- Better extrapolation outside data range

---

## Alternative Bias Mitigation Strategies

### Strategy 1: Charge-Weighted Residuals (Already Implemented)

Current fitting already weights by charge fraction:
```python
charge_weight = row["charge_grains"] / max_charge
```

**Effect:** Prioritizes higher charges (which are typically more important for safety).

### Strategy 2: Tikhonov Regularization

Add L2 penalty to discourage extreme coefficients:

```python
penalty = regularization * (b**2 + c**2 + d**2)
objective = rmse + penalty
```

**Usage:**
```python
fit_result = fit_vivacity_polynomial(
    load_data,
    config,
    regularization=0.01,  # Small penalty
)
```

### Strategy 3: Bounded Optimization with Physics Constraints

Tighten bounds based on physical reasoning:

```python
bounds = (
    (0.01,  0.5, -1.0, -0.5, -0.2),  # Lower bounds
    (0.08,  1.5,  0.0,  0.5,  0.2),  # Upper bounds
)
```

**Reasoning:**
- `a` (base vivacity multiplier): must be positive, typically 0.5-1.5
- `b` (linear term): usually negative (degressive) -1.0 to 0
- `c,d` (higher order): small corrections

---

## Testing Protocol (After Database Fix)

1. **Fix database force values**
2. **Re-run baseline test:**
   ```bash
   python test_bias_analysis.py
   ```
   Expected: RMSE < 100 fps, bias delta < 50 fps

3. **Test 6-parameter polynomial:**
   - Modify `fit_vivacity_polynomial()` to support 6 params
   - Compare RMSE and bias vs 4-parameter

4. **Test LOO cross-validation:**
   - Ensure model generalizes (CV-RMSE ≈ training RMSE)

5. **Test with additional datasets:**
   - Import more GRT files from various cartridges/propellants
   - Check consistency across different load ranges

---

## Expected Outcomes (Post-Fix)

| Metric | Current (Broken) | Target (Fixed) |
|--------|------------------|----------------|
| RMSE | ~3200 fps | < 50 fps |
| Mean Bias | +3200 fps | < 10 fps |
| Low-High Bias Delta | ~100 fps | < 30 fps |
| Solver Stability | Frequent failures | > 99% success |

---

## Implementation Checklist

- [ ] Fix propellant database force values (CRITICAL)
- [ ] Verify unit conversions (kJ/kg ↔ ft·lbf/lbm)
- [ ] Re-test with corrected database
- [ ] Implement 6-parameter polynomial option
- [ ] Add systematic bias detection warnings
- [ ] Implement LOO cross-validation
- [ ] Create bias diagnostic plots
- [ ] Document correct propellant force values for common powders
- [ ] Add database validation tests
- [ ] Update documentation with correct units

---

## References & Resources

**Propellant Force Values (Literature):**
- QuickLOAD database
- GRT (Gordon's Reloading Tool) database
- STANAG 4367 (NATO propellant testing)
- Manufacturer data sheets

**Unit Conversions:**
- 1 kJ/kg = 429.923 Btu/lbm
- 1 kJ/kg = 334.553 ft·lbf/lbm (verify!)
- 1 J/g = 1000 kJ/kg

**Contact:**
- Check GRT source code for force value definitions
- Cross-reference with published ballistics data

---

*End of Report*
