# IB_Solver v2.0.0 - Project Goals & Plan

## Primary Mission
**Characterize propellant burn characteristics** through multi-physics parameter fitting from chronograph velocity data, enabling accurate prediction of propellant burnout distance and pressure development for ballisticians, engineers, and professional reloaders.

## Core Use Cases
1. **Propellant Characterization**: Fit complete burn rate models (vivacity polynomials + physics parameters) from experimental data
2. **Load Development**: Predict optimal charge weights for target burnout positions using fitted models
3. **System Analysis**: Compare propellant performance across different firearms, bullets, and environmental conditions
4. **Research & Validation**: Validate fitted models against published ballistic data and conduct sensitivity analysis

## Target Capabilities
- **Data Import**: Primary via GRT project files, secondary via JSON templates
- **Multi-Physics Fitting**: Vivacity parameters + heat transfer + EOS + friction + temperature effects
- **Database Storage**: System-specific parameter storage with metadata tracking
- **Analysis Tools**: Burnout scans, parameter sensitivity, model validation
- **Modular Design**: Clean separation of physics, fitting, I/O, and analysis components

## Key Differentiators
- **Velocity-Only Calibration**: No pressure traces required - fits from chronograph data alone
- **Advanced Physics**: Noble-Abel EOS, convective heat transfer, temperature sensitivity
- **Professional Workflow**: GRT integration, comprehensive validation, database persistence
- **Scientific Rigor**: Physically motivated models with literature-based parameter bounds

## Design Principles
- **Modular Architecture**: Package per task (physics, fitting, data, analysis)
- **Configurable Complexity**: Simple API for basic fitting, advanced options for research
- **Data Integrity**: Comprehensive validation, error handling, unit consistency
- **Performance Focus**: Fast solving (<100ms), efficient fitting (<10s)
- **Professional Quality**: Full type hints, comprehensive testing, clear documentation

## Implementation Priorities
1. **Workflow Clarification** (establish data flow and user interaction patterns)
2. **Directory Restructuring** (modular packages, archive cleanup)
3. **Documentation Consolidation** (unified, current, comprehensive)
4. **Missing Module Implementation** (analysis, plotting, CLI)
5. **Database Refinement** (optimized for propellant characterization)
6. **Advanced Feature Organization** (optional physics, configuration system)

## Success Metrics
- **Accuracy**: <50 fps RMSE on velocity predictions across charge ranges
- **Reliability**: 100% test pass rate, robust error handling
- **Usability**: Clear workflow from GRT import to validated propellant model
- **Maintainability**: Clean modular architecture, comprehensive documentation</content>
<parameter name="filePath">PROJECT_GOALS.md