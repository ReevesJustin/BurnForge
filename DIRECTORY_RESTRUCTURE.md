# Proposed Directory Structure

```
IB_Solver/
├── src/
│   └── ballistics/           # Main package
│       ├── __init__.py       # Public API exports
│       ├── core/             # Core physics and solving
│       │   ├── __init__.py
│       │   ├── solver.py     # ODE system, solve_ivp integration
│       │   ├── props.py      # Data classes and configurations
│       │   └── burn_rate.py  # Vivacity polynomials and form functions
│       ├── fitting/          # Parameter optimization
│       │   ├── __init__.py
│       │   └── fitting.py    # Multi-parameter optimization
│       ├── io/               # Data import/export
│       │   ├── __init__.py
│       │   └── io.py         # GRT/CSV import, export functions
│       ├── database/         # Database operations
│       │   ├── __init__.py
│       │   └── database.py   # SQLite CRUD operations
│       ├── analysis/         # Analysis and plotting (TO BE IMPLEMENTED)
│       │   ├── __init__.py
│       │   ├── analysis.py   # Burnout scans, charge ladders
│       │   └── plotting.py   # Visualization functions
│       └── utils/            # Utilities
│           ├── __init__.py
│           └── utils.py      # Constants, conversions, validation
├── cli/                      # Command-line interface (TO BE IMPLEMENTED)
│   ├── __init__.py
│   └── main.py               # Typer-based CLI
├── tests/                    # Unit and integration tests
│   ├── __init__.py
│   ├── test_core.py          # Core physics tests
│   ├── test_fitting.py       # Fitting tests
│   ├── test_io.py            # I/O tests
│   ├── test_database.py      # Database tests
│   ├── test_analysis.py      # Analysis tests (TO BE IMPLEMENTED)
│   └── test_integration.py   # End-to-end tests
├── data/                     # Database and examples
│   ├── db/
│   │   └── ballistics_data.db
│   └── examples/
│       ├── json_templates/   # JSON data entry templates
│       └── grt_samples/      # Sample GRT files
├── docs/                     # Current documentation
│   ├── PROJECT_GOALS.md      # Project goals and scope
│   ├── WORKFLOW.md           # User workflow guide
│   ├── README.md             # Installation and usage
│   ├── API_REFERENCE.md      # Function/class documentation
│   └── DEPENDENCIES.md       # Dependency information
├── archive/                  # Historical files
│   ├── docs/                 # Old documentation files
│   │   ├── DESIGN_PLAN.md
│   │   ├── PHASE1_COMPLETE.md
│   │   ├── PHASE2_COMPLETE.md
│   │   ├── FIXES_SUMMARY.md
│   │   ├── etc...
│   ├── scripts/              # Old analysis scripts
│   │   ├── quick_fit_analysis.py
│   │   ├── plot_fit_diagnostics.py
│   │   ├── diagnose_physics_v3.py
│   │   └── etc...
│   └── legacy/               # Original solver files
│       ├── solver.py
│       ├── fit_vivacity.py
│       └── plot_vivacity.py
├── pyproject.toml            # Package configuration
├── requirements.txt          # Dependencies (if needed)
└── .gitignore
```

## Key Changes from Current Structure

### 1. Modular Subpackages
- Split monolithic `ballistics/` into focused subpackages
- `core/`: Fundamental physics and solving
- `fitting/`: Optimization routines
- `io/`: Data handling
- `database/`: Persistence layer
- `analysis/`: Higher-level analysis (new)
- `utils/`: Shared utilities

### 2. Clear Separation of Concerns
- Each subpackage has single responsibility
- Easy to maintain and extend
- Clear dependency relationships

### 3. Archive Organization
- `/archive/docs/`: Old documentation files
- `/archive/scripts/`: Analysis and diagnostic scripts
- `/archive/legacy/`: Original implementation files

### 4. Testing Structure
- Dedicated `/tests/` directory
- Test files organized by functionality
- Clear naming convention

### 5. Documentation Restructuring
- `/docs/`: Current, consolidated documentation
- Separate files for different audiences/content types
- Clear navigation structure

## Implementation Plan

### Phase 1: Directory Restructuring
1. Create new subpackage directories
2. Move existing modules to appropriate subpackages
3. Update import statements throughout codebase
4. Move old files to `/archive/`
5. Update `pyproject.toml` if needed

### Phase 2: Import Consolidation
1. Update `__init__.py` files for each subpackage
2. Maintain backward compatibility in main package `__init__.py`
3. Test all imports work correctly

### Phase 3: Documentation Updates
1. Consolidate and update documentation
2. Create JSON templates for manual data entry
3. Update README with new structure

Would you like me to proceed with implementing this directory restructuring? The modular subpackage approach will make the codebase much more maintainable and allow for cleaner feature development.</content>
<parameter name="filePath">DIRECTORY_RESTRUCTURE.md