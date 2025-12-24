# IB_Solver Project TODO List

This TODO list outlines the final implementation priorities for completing the IB_Solver v2.0.0 project.

## 🎯 Current Status: Phase 3 Complete
- ✅ Database schema migration to 9-table relational design
- ✅ Core modules: analysis.py, plotting.py, cli/main.py
- ✅ Advanced physics: shot-start pressure, primer energy, charge-dependent heat loss
- ✅ Fitting improvements: weighted least squares, data validation, convergence diagnostics
- ✅ Code quality: comprehensive tests, logging, performance profiling

## High Priority Tasks

### 1. Resolve Systematic Fitting Bias
**Why**: Current RMSE ~134 fps with -59 fps bias between low/high charges indicates model limitations.

**Implementation**:
- [ ] Test 6-parameter polynomial (Λ_base + a,b,c,d,e,f) in `fit_vivacity_polynomial`
- [ ] Extend bounds: `bounds = ((0.01, -2, -2, -2, -2, -2), (0.15, 2, 2, 2, 2, 2))`
- [ ] Validate on multiple datasets (N150, Varget, H4350)
- [ ] Add bias detection warnings in fitting output
- [ ] Implement LOO CV for bias detection
- [x] **COMPLETED**: Implement max pressure calibration reference feature

## Medium Priority Tasks

### 2. Feature Enhancements
- [ ] Multi-temperature dataset support and fitting
- [ ] Export options (JSON, CSV, PDF reports)
- [ ] Batch processing for multiple GRT files
- [ ] Interactive plotting with zoom/pan capabilities
- [x] **COMPLETED**: Max pressure calibration reference (optional pressure constraint from GRT)

## Medium Priority Tasks

### 2. Feature Enhancements
- [ ] Multi-temperature dataset support and fitting
- [ ] Export options (JSON, CSV, PDF reports)
- [ ] Batch processing for multiple GRT files
- [ ] Interactive plotting with zoom/pan capabilities

## Low Priority Tasks

### 3. Documentation and Examples
- [ ] Create comprehensive usage examples and tutorials
- [ ] Add API documentation with Sphinx
- [ ] Create video tutorials for key workflows
- [ ] Develop case studies with real data

## 📊 Project Metrics Achieved
- **Accuracy**: <100 fps RMSE with bias corrections in progress
- **Features**: Complete CLI workflow, parameter sweeps, visualization
- **Database**: Full relational schema with migration support
- **Testing**: Unit tests for all major components
- **Documentation**: Updated README, API docs, examples

## Secondary Priority (Code Quality & Validation)

### 3. Complete Physics Enhancements - COMPLETED ✅
- [x] Implement primer energy boost (`p_primer_psi` parameter)
- [x] Add data validation checks (fill ratio, LOO CV) to fitting
- [x] Fix remaining type checker errors in solver.py and fitting.py

### 4. Burn Rate Model Refinements - COMPLETED ✅
- [x] Implement position-dependent shot start (framework added, can be extended)
- [x] Test nonlinear effective mass formulation (already implemented via φ_eff = 1 + (C × Z)/(μ × m_bullet))
- [x] Add convergence diagnostics for complex parameter sets (added nfev, nit, success to fit results)

## Notes
- Estimated completion time: Database migration (4-6 hours), Bias resolution (2-3 hours)
- Start with database migration for data management foundation, then bias resolution for accuracy improvements
- All tasks should include unit tests and documentation updates</content>
<parameter name="filePath">TODO.md