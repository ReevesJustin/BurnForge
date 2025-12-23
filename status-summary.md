# IB_Solver Project Status Summary

## Current Date
Tue Dec 23 2025

## Project Phase Status
- **Phase 1 & 2**: Complete - Core ODE solver (DOP853), database integration, CLI, tests.
- **Physics V3**: Complete - Heat loss models, temperature sensitivity in fitting/burn rate, Noble-Abel EOS extensions, Gemini AI integration.
- **Hybrid Burn Rate Stabilization**: In progress - Implementing and validating geometric + pressure-dependent + temperature-sensitive burn rate model.
- **Goal**: Achieve state-of-the-art fitting accuracy for precise burnout distance prediction from chrono data (low RMSE <100-150 fps).

## Burn Rate Model Status
- **Formula**: dZ/dt = (Lambda_base + alpha * p) * pi(Z) * exp(sigma * (T_prop_K - 294K))
  - Lambda_base: Base vivacity at reference conditions.
  - alpha: Pressure-dependent correction coefficient (fitted or default 0.0).
  - pi(Z): Geometric form function based on grain_geometry.
    - Spherical/degressive: pi(Z) = (1 - Z)^{2/3}
    - Neutral/single-perf: pi(Z) = 1 - Z
    - Progressive/7-perf: pi(Z) = 1 + Z (up to Z=0.9)
  - sigma: Temperature sensitivity (default 0.002 /K).
- **Implementation**: Use_form_function=True in solver/fitting, pressure correction via alpha, temp via Arrhenius-like multiplier.
- **Current Status**: Formula confirmed, geometry support added, alpha/temp fields in DB.

## Recent Changes
- Applied database migrations: Added grain_geometry, alpha, temp_sensitivity_sigma_per_K, covolume_m3_per_kg columns.
- Updated propellant geometries: N150 and Varget set to 'single-perf' (neutral).
- Solidified hybrid burn rate in calc_vivacity and fitting.py.
- Ran diagnostics on N150 GRT data.

## Latest Diagnostics
- **Test Suite**: Pytest - 1 failed (test_solve_ivp_convergence: pressure 83237 psi > 80000 limit), 15 passed, 2 skipped. Indicates burn rate too slow, excessive pressure.
- **Type Checking**: Mypy - 33 errors in solver.py, fitting.py, io.py (type incompatibilities, undefined variables).
- **Fitting Results** (N150, 6.5CM 130gr 18" barrel, 87°F):
  - RMSE: 208 fps (target <100-150 fps not met).
  - Residuals: -238 to -173 fps, systematic under-prediction worse at low charges.
  - Bias: Yes, under-prediction decreases with increasing charge.
  - Fitted: Lambda_base=0.041, alpha=0.000, geometry=single-perf.
- **Plots**: Generated fit_diagnostics.png, fit_diagnostics_advanced.png showing poor fit and bias.

## Remaining Issues/Next Steps
- Fix mypy errors for type safety.
- Improve fitting accuracy: Test progressive geometry, fit temp sensitivity, investigate heat loss/effective mass models.
- Validate on multiple propellants (Varget, ball powders) across temperatures.
- Address pressure bias in ODE solver.
- Integrate Gemini for automated optimization.

Last updated: Tue Dec 23 2025 12:00 PM  
Task just completed: Created status reporter agent and generated initial project status summary.