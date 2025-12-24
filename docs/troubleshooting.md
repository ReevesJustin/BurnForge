# Troubleshooting Guide: Ballistics Solver and Fitting Issues

## Overview
This document summarizes code errors, physics model limitations, and optimization strategies investigated during testing against experimental GRT data.

## Code Errors and Fixes

### Bugs Identified
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