# Troubleshooting Guide: Ballistics Solver and Fitting Issues

## Overview
This document summarizes code errors, physics model limitations, and optimization strategies investigated during testing against experimental GRT data.

---

## 🔴 CRITICAL BUG - Database Propellant Force Values (2024-12-24)

### Issue
**ALL propellants in database have incorrect force values causing predictions to be 2-3x too high.**

**Symptoms:**
- Predicted velocities: ~6000 fps (should be ~2600 fps)
- RMSE: ~3200 fps (completely unusable)
- All predictions systematically too high

**Root Cause:**
Database contains `force = 3,650,000 ft·lbf/lbm` for all propellants when correct values should be ~350,000-400,000 ft·lbf/lbm (10x lower).

**Fix:**
See **docs/DATABASE_FIX_GUIDE.md** for complete fix procedure.

**Quick Fix:**
```bash
# Backup first!
cp data/db/ballistics_data.db data/db/ballistics_data.db.backup

# Apply fix
sqlite3 data/db/ballistics_data.db "UPDATE propellants SET force = force / 10.0;"

# Verify
python test_bias_analysis.py
```

**Status:** ⚠️ Must be fixed before any other work can proceed.

---

## Code Errors and Fixes

### Bugs Identified (2024-12-24)
- **🔴 CRITICAL - Propellant Force Values**: All propellants have force = 3,650,000 (10x too high). Fixed via database update.
- **Solver Trace Output Bug**: solver.py:541 - `return_trace` used undefined variables `t`, `Z`, `P`, `v`, `x`. Fixed to use `sol.t` and `sol.y`.
- **Fitting Indentation Bug**: fitting.py:274-373 - Code outside function scope due to incorrect indentation. Fixed.
- **Force Units Assumption**: PropellantProperties.from_database assumed incorrect force unit conversion (fixed to use ft-lbf/lbm consistently).
- **Burnout Distance Calculation**: Failed silently when Z >= 0.999 (fixed to properly set distance from bolt face).
- **ODE Solver Stability**: Added max_step adjustment and debug logging parameter for convergence monitoring.

### Fixes Applied
- Corrected unit conversions throughout the codebase.
- Enhanced burnout event detection in solve_ivp.
- Added solver robustness with parameter validation.
- Implemented debug mode for detailed logging.

## Physics Model Validation

### RMSE Analysis
- **N150 Dataset**: RMSE ~134-410 fps (5-16% of mean velocity)
- **Varget Dataset**: RMSE ~49-384 fps (2-14% of mean velocity)
- **Systematic Bias**: Present in both datasets, worse for lower charge weights.

### Model Limitations
- High RMSE likely due to physics assumptions, not code errors.
- Covolume correction in Noble-Abel EOS may cause numerical issues at high Z.
- Temperature sensitivity and bore friction have limited impact on single-temp datasets.

## Optimization Strategy Improvements

### Sequential Fitting Implementation
**Rationale**: Simultaneous fitting of many parameters can lead to local minima. Hierarchical approach fits parameters in order of impact.

**Method**:
1. Fit vivacity polynomial (Lambda_base, a, b, c, d) with advanced physics disabled
2. Fix vivacity parameters and fit h_base (convective heat transfer)

**Results**:
- More stable convergence than simultaneous optimization
- Comparable or better RMSE in test cases
- Reduced risk of parameter interaction issues

### Parameter Impact Hierarchy
1. **Lambda_base** (Most impactful - base burn rate)
2. **Polynomial coefficients** (a, b, c, d - burn rate shape)
3. **h_base** (Heat transfer coefficient)
4. **Temperature sensitivity** (σ)
5. **Bore friction** (psi)
6. **Covolume, start pressure** (Least impactful)

## Recommendations

### For Improved Accuracy
1. Use sequential fitting for production models
2. Validate against multi-temperature datasets for temp sensitivity
3. Consider additional physics terms (e.g., engraving work, gas leakage)
4. Implement cross-validation with held-out data points

### For Code Stability
1. Add comprehensive unit testing for all conversions
2. Implement parameter bounds validation in fitting
3. Add convergence monitoring and early stopping
4. Document physics assumptions and limitations

### Testing Protocol
- Always test on multiple datasets with different propellants
- Check for systematic bias patterns
- Validate burnout distance calculations
- Monitor parameter sensitivity and correlation

## Future Improvements
- Implement adaptive parameter fitting based on dataset characteristics
- Add physics model selection based on propellant type
- Integrate with GRT for real-time validation
- Develop automated model selection criteria

Last updated: December 2025</content>
<parameter name="filePath">docs/troubleshooting.md