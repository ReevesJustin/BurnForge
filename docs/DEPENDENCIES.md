# Dependencies

## Core Dependencies

### Required
- **Python** ≥3.10 (type hints, dataclasses, match statements)
- **numpy** ≥1.24 (numerical arrays, mathematical operations)
- **scipy** ≥1.10 (ODE integration via solve_ivp, optimization via minimize)
- **pandas** ≥2.0 (DataFrame operations for load data and results)
- **matplotlib** ≥3.7 (plotting and visualization)
- **sqlite3** (stdlib, database operations)

### Optional
- **typer** ≥0.9.0 (command-line interface)
- **pytest** ≥7.0 (unit testing)
- **pytest-cov** ≥4.0 (test coverage reporting)
- **black** ≥23.0 (code formatting)
- **ruff** ≥0.1.0 (linting)
- **mypy** (type checking)

## Installation

### Core Package
```bash
pip install -e .
```

### With CLI Tools
```bash
pip install -e .[cli]
```

### Development Environment
```bash
pip install -e .[cli,dev]
```

## Dependency Rationale

### Scientific Computing Stack
- **numpy**: Fundamental array operations and mathematical functions
- **scipy**: Advanced numerical methods (ODE solvers, optimizers)
- **pandas**: Data manipulation for chronograph data and results
- **matplotlib**: Plotting for diagnostics and analysis

### Database
- **sqlite3**: Lightweight, file-based database included in Python stdlib
- No additional dependencies required for persistence

### Development Tools
- **pytest**: Comprehensive testing framework with fixtures and parametrization
- **black/ruff**: Code quality and consistency
- **mypy**: Static type checking (optional, as type errors exist)

## Platform Compatibility

- **Linux**: Fully supported (primary development platform)
- **macOS**: Compatible (not tested)
- **Windows**: Compatible (not tested)

## Version Constraints

Version requirements are specified to ensure:
- API compatibility (scipy.optimize interface changes)
- Performance improvements (numpy array operations)
- Bug fixes (pandas DataFrame operations)
- Security updates (stdlib components)

## Optional Dependencies

### CLI Interface
The CLI is optional because:
- GUI applications can import the library directly
- Headless/server environments may not need CLI
- Reduces installation footprint for library-only usage

### Development Tools
Development dependencies are optional because:
- End users don't need testing/linting tools
- CI/CD systems handle quality checks
- Reduces installation complexity for production use

## Known Issues

### Type Checking
Current codebase has type checking errors that prevent mypy from passing:
- None type handling in physics parameters
- Optional field access without null checks
- DataFrame/Series type inference issues

These are functional issues but affect development workflow. Recommended fix:
```bash
# Temporarily disable mypy for physics modules
# TODO: Fix type annotations for full mypy compliance
```

### Performance Notes
- Dependencies are chosen for performance over minimalism
- scipy.solve_ivp provides 10-100x speedup over custom ODE implementations
- numpy operations are vectorized for efficiency

## Future Dependencies

Potential additions based on feature expansion:
- **numba** (JIT compilation for performance-critical sections)
- **h5py** (advanced data storage formats)
- **plotly** (interactive web-based plotting)
- **sqlalchemy** (advanced ORM for database operations)</content>
<parameter name="filePath">docs/DEPENDENCIES.md