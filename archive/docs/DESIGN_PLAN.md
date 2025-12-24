# Internal Ballistics Solver - Design Plan

## Project Overview

A modular, production-grade Python package for lumped-parameter internal ballistics modeling with dynamic vivacity fitting. Optimizes full 5-parameter vivacity polynomials (Λ_base, a, b, c, d) from velocity-only chronograph data to predict propellant burnout distance with high confidence. Uses adaptive ODE integration with event detection, structured for GUI integration and scientific computing workflows.

---

## Directory Structure

```
IB_Solver/
├── src/
│   └── ballistics/
│       ├── __init__.py           # Package initialization, version, public API exports
│       ├── database.py           # SQLite CRUD operations, schema management, queries
│       ├── props.py              # Propellant and bullet property dataclasses and loaders
│       ├── solver.py             # Core ODE system definition and solve_ivp integration
│       ├── burn_rate.py          # Vivacity polynomial evaluation and validation
│       ├── fitting.py            # Multi-parameter optimization routines with bounds
│       ├── analysis.py           # Burnout scans, charge ladders, barrel length sweeps
│       ├── io.py                 # CSV/JSON loaders with metadata parsing, result exporters
│       ├── plotting.py           # Matplotlib figure generators (velocity, vivacity, burnout maps)
│       └── utils.py              # Unit conversions, physical constants, validation helpers
├── cli/
│   ├── __init__.py           # CLI package initialization
│   └── main.py               # Thin CLI wrapper using typer, calls ballistics/* functions
├── tests/
│   ├── __init__.py           # Test package initialization
│   ├── test_solver.py        # Unit tests for solver.py integration accuracy
│   ├── test_fitting.py       # Tests for fitting convergence and bounds
│   ├── test_io.py            # CSV parsing validation tests
│   └── test_integration.py   # Integration tests comparing to legacy solver results
├── data/
│   ├── ballistics_data.db    # SQLite database with propellant/bullet properties
│   ├── examples/             # Example CSV files with load ladder data
│   │   ├── 308_win_varget_175gr.csv
│   │   └── 223_rem_h4895_77gr.csv
│   └── published/            # Published load data for future validation (Phase 2)
│       └── README.md         # Format specification for published data
├── archive/
│   ├── solver.py             # Original fixed-timestep solver (archived after migration)
│   ├── fit_vivacity.py       # Original single-parameter fitting script
│   ├── create_database.py    # Original database creation script
│   └── plot_vivacity.py      # Original plotting script
├── README.md                 # Installation, quick start, usage examples
├── DESIGN_PLAN.md            # This file
├── pyproject.toml            # Modern Python package configuration (PEP 518/621)
└── .gitignore                # Git ignore patterns
```

**Notes:**
- Using `src/` layout for cleaner package isolation and testing
- `pyproject.toml` replaces `setup.py` and `requirements.txt` (2025 best practice)
- Database path configurable via `BALLISTICS_DB_PATH` environment variable or `--db-path` CLI flag
- `data/published/` prepared for Phase 2 published load comparison feature


---

## Module Details

### `ballistics/__init__.py`
**Purpose:** Package initialization, version control, public API surface.

**Public API:**
```python
__version__ = "2.0.0"

# Re-export key functions for convenience
from .solver import solve_ballistics
from .fitting import fit_vivacity_polynomial
from .analysis import burnout_scan, charge_ladder_analysis
```

**Dependencies:** None (internal imports only)

---

### `ballistics/database.py`
**Purpose:** SQLite database operations for propellant and bullet properties.

**Key Public Functions/Classes:**
```python
def get_default_db_path() -> str:
    """Get database path from environment variable or default.

    Returns
    -------
    str
        Path from BALLISTICS_DB_PATH env var, else "data/ballistics_data.db"
    """

def get_propellant(name: str, db_path: str | None = None) -> dict:
    """Retrieve propellant properties by name.

    Parameters
    ----------
    name : str
        Propellant name (e.g., "Varget", "N140")
    db_path : str, optional
        Path to SQLite database (uses get_default_db_path() if None)

    Returns
    -------
    dict
        Keys: vivacity, base, force, temp_0, bulk_density, poly_a, poly_b, poly_c, poly_d
    """

def get_bullet_type(name: str, db_path: str | None = None) -> dict:
    """Retrieve bullet type properties by name.

    Parameters
    ----------
    name : str
        Bullet type name (e.g., "Copper Jacket over Lead")
    db_path : str, optional
        Path to SQLite database (uses get_default_db_path() if None)

    Returns
    -------
    dict
        Keys: s (strength factor), rho_p (density in lbm/in³)
    """

def update_propellant_coefficients(name: str, Lambda_base: float,
                                   coeffs: tuple[float, float, float, float],
                                   db_path: str | None = None) -> None:
    """Update vivacity polynomial coefficients for a propellant.

    Parameters
    ----------
    name : str
        Propellant name
    Lambda_base : float
        Base vivacity in s⁻¹ per 100 bar
    coeffs : tuple
        (a, b, c, d) polynomial coefficients
    db_path : str, optional
        Path to SQLite database (uses get_default_db_path() if None)
    """

def list_propellants(db_path: str | None = None) -> list[str]:
    """Return list of all propellant names in database.

    Parameters
    ----------
    db_path : str, optional
        Path to SQLite database (uses get_default_db_path() if None)
    """
```

**Dependencies:** `sqlite3` (stdlib), `os` (for environment variable)

---

### `ballistics/props.py`
**Purpose:** Data structures for propellant and bullet properties.

**Key Public Classes:**
```python
@dataclass
class PropellantProperties:
    """Propellant thermochemical and burn rate properties."""
    name: str
    vivacity: float              # s⁻¹ per 100 bar
    base: str                    # 'S' or 'D'
    force: float                 # ft-lbf/lbm
    temp_0: float                # K
    gamma: float                 # Specific heat ratio (computed from base)
    bulk_density: float          # lbm/in³
    Lambda_base: float           # Vivacity normalized (vivacity / 1450)
    poly_coeffs: tuple[float, float, float, float]  # (a, b, c, d)

    @classmethod
    def from_database(cls, name: str, db_path: str = "data/ballistics_data.db"):
        """Load propellant from database."""

@dataclass
class BulletProperties:
    """Bullet material properties."""
    name: str
    s: float                     # Strength factor
    rho_p: float                 # lbm/in³

    @classmethod
    def from_database(cls, name: str, db_path: str = "data/ballistics_data.db"):
        """Load bullet type from database."""

@dataclass
class BallisticsConfig:
    """Complete configuration for ballistics solver."""
    bullet_mass_gr: float
    charge_mass_gr: float
    caliber_in: float
    case_volume_gr_h2o: float
    barrel_length_in: float
    cartridge_overall_length_in: float  # COAL - measured from bolt face to bullet tip
    propellant: PropellantProperties
    bullet: BulletProperties
    temperature_f: float = 70.0
    phi: float = 0.9              # Piezometric coefficient
    p_initial_psi: float = 5000.0

    @property
    def effective_barrel_length_in(self) -> float:
        """Calculate effective barrel length for bullet travel."""
        return self.barrel_length_in - self.cartridge_overall_length_in
```

**Dependencies:** `dataclasses`, `ballistics.database`

---

### `ballistics/burn_rate.py`
**Purpose:** Vivacity polynomial evaluation and constraint validation.

**Key Public Functions:**
```python
def calc_vivacity(Z: float, Lambda_base: float,
                 coeffs: tuple[float, float, float, float]) -> float:
    """Compute dynamic vivacity Λ(Z) in s⁻¹ per 100 bar.

    Parameters
    ----------
    Z : float
        Burn fraction (0 ≤ Z ≤ 1)
    Lambda_base : float
        Base vivacity in s⁻¹ per 100 bar
    coeffs : tuple
        (a, b, c, d) polynomial coefficients

    Returns
    -------
    float
        Dynamic vivacity Λ(Z)
    """

def validate_vivacity_positive(Lambda_base: float,
                               coeffs: tuple[float, float, float, float],
                               n_points: int = 100) -> bool:
    """Check that Λ(Z) > 0 for all Z ∈ [0, 1].

    Parameters
    ----------
    Lambda_base : float
        Base vivacity
    coeffs : tuple
        (a, b, c, d) polynomial coefficients
    n_points : int
        Number of points to sample

    Returns
    -------
    bool
        True if vivacity is positive throughout burn
    """
```

**Dependencies:** `numpy`

---

### `ballistics/solver.py`
**Purpose:** Core ODE system and scipy.integrate.solve_ivp integration.

**Key Public Functions:**
```python
def solve_ballistics(config: BallisticsConfig,
                    Lambda_override: float | None = None,
                    coeffs_override: tuple[float, float, float, float] | None = None,
                    method: str = 'DOP853',
                    return_trace: bool = False) -> dict:
    """Solve internal ballistics using adaptive ODE integration.

    Parameters
    ----------
    config : BallisticsConfig
        Complete ballistics configuration
    Lambda_override : float, optional
        Override base vivacity (for fitting)
    coeffs_override : tuple, optional
        Override polynomial coefficients (for fitting)
    method : str
        Integration method ('RK45', 'DOP853', 'Radau')
    return_trace : bool
        If True, return full time-series trajectory

    Returns
    -------
    dict
        Always returned: muzzle_velocity_fps, muzzle_energy_ft_lbs, peak_pressure_psi,
                        muzzle_pressure_psi, final_Z, total_time_s
        If final_Z = 1.0 (burnout occurred):
            burnout_distance_from_bolt_in (inches from bolt face where Z = 1.0)
        If final_Z < 1.0 (still burning at muzzle):
            muzzle_burn_percentage (percent of propellant consumed at muzzle)
        If return_trace=True, also includes: t, Z, P, v, x (arrays)

        Note: muzzle_energy_ft_lbs = (M_lb * v_fps²) / (2 * 32.174) for load comparison
    """

def _ode_system(t: float, y: np.ndarray, config: BallisticsConfig,
               Lambda_base: float, coeffs: tuple) -> np.ndarray:
    """ODE system for internal ballistics.

    State vector y = [Z, v, x]
    Returns dy/dt = [dZ/dt, dv/dt, dx/dt]
    """

def _burnout_event(t: float, y: np.ndarray, *args) -> float:
    """Event function for burnout detection (Z = 1.0)."""

def _muzzle_event(t: float, y: np.ndarray, config: BallisticsConfig, *args) -> float:
    """Event function for muzzle exit (x = L_eff)."""
```

**Dependencies:** `numpy`, `scipy.integrate`, `ballistics.props`, `ballistics.burn_rate`

---

### `ballistics/fitting.py`
**Purpose:** Multi-parameter vivacity polynomial fitting using optimization.

**Key Public Functions:**
```python
def fit_vivacity_polynomial(load_data: pd.DataFrame,
                           config_base: BallisticsConfig,
                           initial_guess: tuple[float, float, float, float, float] | None = None,
                           bounds: tuple | None = None,
                           regularization: float = 0.0,
                           method: str = 'L-BFGS-B',
                           verbose: bool = True) -> dict:
    """Fit full 5-parameter vivacity polynomial from load ladder data.

    Parameters
    ----------
    load_data : pd.DataFrame
        Columns: charge_grains, mean_velocity_fps, velocity_sd (optional)
    config_base : BallisticsConfig
        Base configuration (charge_mass_gr will be overridden per row)
    initial_guess : tuple, optional
        (Lambda_base, a, b, c, d). Defaults to database values + (1, -1, 0, 0)
    bounds : tuple, optional
        ((Lambda_min, a_min, ...), (Lambda_max, a_max, ...))
        Default: Lambda ∈ [20, 200], a ∈ [-2, 2], b,c,d ∈ [-2, 2] with positivity constraint
    regularization : float
        L2 penalty on coefficients (default 0.0)
    method : str
        Optimization method ('L-BFGS-B', 'trust-constr')
    verbose : bool
        Print iteration progress

    Returns
    -------
    dict
        Keys: Lambda_base, coeffs (a,b,c,d), rmse_velocity, residuals, success, message
    """

def _objective_function(params: np.ndarray, load_data: pd.DataFrame,
                       config_base: BallisticsConfig,
                       regularization: float) -> float:
    """Objective function: weighted velocity RMSE + regularization.

    Weights from velocity_sd if available (weight = 1/sd²), else uniform.
    """

def _constraint_positive_vivacity(params: np.ndarray) -> np.ndarray:
    """Constraint function ensuring Λ(Z) > 0 for Z ∈ [0, 1]."""
```

**Dependencies:** `numpy`, `scipy.optimize`, `pandas`, `ballistics.solver`, `ballistics.burn_rate`

---

### `ballistics/analysis.py`
**Purpose:** High-level analysis tools for burnout prediction and load development.

**Key Public Functions:**
```python
def burnout_scan_charge(config: BallisticsConfig,
                       charge_range: tuple[float, float],
                       n_points: int = 20) -> pd.DataFrame:
    """Sweep charge weight and compute burnout distance for each.

    Parameters
    ----------
    config : BallisticsConfig
        Base configuration (charge_mass_gr will be swept)
    charge_range : tuple
        (min_grains, max_grains)
    n_points : int
        Number of charges to evaluate

    Returns
    -------
    pd.DataFrame
        Base columns: charge_grains, muzzle_velocity_fps, muzzle_energy_ft_lbs,
                      peak_pressure_psi, muzzle_pressure_psi, final_Z
        If final_Z = 1.0: burnout_distance_from_bolt_in
        If final_Z < 1.0: muzzle_burn_percentage
    """

def burnout_scan_barrel(config: BallisticsConfig,
                        barrel_range: tuple[float, float],
                        n_points: int = 20) -> pd.DataFrame:
    """Sweep barrel length and compute burnout metrics.

    Parameters
    ----------
    config : BallisticsConfig
        Base configuration (barrel_length_in will be swept)
    barrel_range : tuple
        (min_inches, max_inches)
    n_points : int
        Number of barrel lengths to evaluate

    Returns
    -------
    pd.DataFrame
        Base columns: barrel_length_in, muzzle_velocity_fps, muzzle_energy_ft_lbs,
                      peak_pressure_psi, muzzle_pressure_psi, final_Z
        If final_Z = 1.0: burnout_distance_from_bolt_in
        If final_Z < 1.0: muzzle_burn_percentage
    """

def charge_ladder_analysis(config: BallisticsConfig,
                           charges: list[float],
                           target_velocity: float | None = None) -> dict:
    """Analyze multiple charge weights and optionally find charge for target velocity.

    Parameters
    ----------
    config : BallisticsConfig
        Base configuration
    charges : list
        Charge weights in grains
    target_velocity : float, optional
        If provided, interpolate charge for this velocity

    Returns
    -------
    dict
        Keys: results (DataFrame), target_charge_gr (if target_velocity given)
    """
```

**Dependencies:** `numpy`, `pandas`, `ballistics.solver`, `ballistics.props`

---

### `ballistics/io.py`
**Purpose:** CSV/JSON loaders with metadata parsing and result exporters.

**Key Public Functions:**
```python
def load_chronograph_csv(filepath: str) -> tuple[dict, pd.DataFrame]:
    """Load chronograph data CSV with metadata and load ladder.

    Parameters
    ----------
    filepath : str
        Path to CSV file following standardized format

    Returns
    -------
    tuple
        (metadata: dict, load_data: pd.DataFrame)
        metadata includes: cartridge, barrel_length_in, bullet_mass_gr, propellant_name, etc.
        load_data columns: charge_grains, mean_velocity_fps, velocity_sd, notes
    """

def parse_metadata(lines: list[str]) -> dict:
    """Parse metadata comment lines from CSV header.

    Validates required fields and converts units as needed.
    """

def metadata_to_config(metadata: dict, db_path: str = "data/ballistics_data.db") -> BallisticsConfig:
    """Convert parsed metadata dict to BallisticsConfig.

    Loads propellant and bullet properties from database using metadata fields.
    """

def export_fit_results(fit_result: dict, output_path: str, format: str = 'json') -> None:
    """Export fitting results to JSON or Python dict snippet.

    Parameters
    ----------
    fit_result : dict
        Output from fit_vivacity_polynomial
    output_path : str
        Output file path
    format : str
        'json' or 'python' (for database update snippet)
    """

def load_grt_project(filepath: str) -> tuple[dict, pd.DataFrame]:
    """Load chronograph data from Gordon's Reloading Tool (GRT) project file.

    GRT project files (.grtload, .grtproject) are XML-based. Files may contain
    embedded images (target photos, etc.) which are ignored. Extracts metadata
    and measurement charges, returns same format as load_chronograph_csv() for
    pipeline compatibility.

    Parameters
    ----------
    filepath : str
        Path to GRT project file (.grtload or .grtproject)

    Returns
    -------
    tuple
        (metadata: dict, load_data: pd.DataFrame)
        metadata includes: cartridge, barrel_length_in, bullet_mass_gr, propellant_name,
                          cartridge_overall_length_in, case_volume_gr_h2o, etc.
        load_data columns: charge_grains, mean_velocity_fps, velocity_sd, notes
        Returns (metadata, empty DataFrame) if no measurement charges present

    Implementation Notes
    --------------------
    - Parse XML directly with xml.etree.ElementTree (GRT files are XML format)
    - Ignore embedded images or non-XML content
    - Key conversions (using constants from utils.py):
      * Barrel length (xe): mm → inches (÷ 25.4)
      * COAL (oal): mm → inches (÷ 25.4)
      * Case volume (casevol): cm³ → grains H₂O (× 15.432), override from note if present
      * Bullet mass (mp): grams → grains (× 15.432)
      * Charge mass (value): kg → grains (× 15432.4)
      * Velocity: m/s → ft/s (× 3.28084)
      * Initial pressure (ps): bar → psi (× 14.5038)
      * Temperature (pt): Celsius → Fahrenheit (× 9/5 + 32)
    - Parse note text for case volume override (e.g., "Vol 52.47gr H2O")
    - Group measurement charges by charge weight, compute mean and SD per group
    - Map propellant name: "Vihtavuori N150" → "N150" for database lookup
    - Bullet jacket type: assume "Copper Jacket over Lead" (user can override)
    - Validate required fields, raise clear ValueError if missing
    """
```

**Dependencies:** `pandas`, `json`, `xml.etree.ElementTree` (stdlib), `re` (stdlib),
                `ballistics.props`, `ballistics.database`, `ballistics.utils`

---

### `ballistics/plotting.py`
**Purpose:** Matplotlib figure generators for visualization.

**Key Public Functions:**
```python
def plot_vivacity_curve(Lambda_base: float,
                       coeffs: tuple[float, float, float, float],
                       comparison: tuple | None = None,
                       save_path: str | None = None) -> tuple:
    """Plot dynamic vivacity Λ(Z) vs burn fraction.

    Parameters
    ----------
    Lambda_base : float
        Base vivacity
    coeffs : tuple
        (a, b, c, d) polynomial coefficients
    comparison : tuple, optional
        (Lambda_base_2, coeffs_2) for comparison curve
    save_path : str, optional
        If provided, save figure to this path

    Returns
    -------
    tuple
        (fig, ax) matplotlib Figure and Axes objects
    """

def plot_velocity_fit(load_data: pd.DataFrame,
                     predicted_velocities: np.ndarray,
                     save_path: str | None = None) -> tuple:
    """Plot observed vs predicted velocities from fitting.

    Parameters
    ----------
    load_data : pd.DataFrame
        Must include charge_grains, mean_velocity_fps, velocity_sd (optional)
    predicted_velocities : np.ndarray
        Model predictions for each charge
    save_path : str, optional
        If provided, save figure

    Returns
    -------
    tuple
        (fig, ax)
    """

def plot_burnout_map(scan_results: pd.DataFrame,
                    x_col: str,
                    save_path: str | None = None) -> tuple:
    """Plot burnout distance and pressure vs sweep parameter.

    Parameters
    ----------
    scan_results : pd.DataFrame
        Output from burnout_scan_charge or burnout_scan_barrel
    x_col : str
        Column name for x-axis ('charge_grains' or 'barrel_length_in')
    save_path : str, optional
        If provided, save figure

    Returns
    -------
    tuple
        (fig, axes) with dual y-axes
    """
```

**Dependencies:** `matplotlib.pyplot`, `numpy`, `pandas`

---

### `ballistics/utils.py`
**Purpose:** Unit conversions, physical constants, validation helpers.

**Key Public Functions/Constants:**
```python
# Constants
GRAINS_TO_LB = 1 / 7000
GRAINS_H2O_TO_IN3 = 1 / 252.9
G_ACCEL = 386.4  # in/s²
PSI_TO_BAR = 0.0689476
BAR_TO_PSI = 14.5038
MM_TO_IN = 1 / 25.4
GRAMS_TO_GRAINS = 15.432358
KG_TO_GRAINS = 15432.358
CM3_TO_GRAINS_H2O = 15.432358  # 1 cm³ H₂O ≈ 15.432 grains
MS_TO_FPS = 3.28084

# Conversion functions
def fahrenheit_to_kelvin(temp_f: float) -> float:
    """Convert °F to K."""

def grains_to_kg(grains: float) -> float:
    """Convert grains to kilograms."""

def fps_to_ms(fps: float) -> float:
    """Convert ft/s to m/s."""

# Ballistics calculations
def calc_muzzle_energy(bullet_mass_gr: float, muzzle_velocity_fps: float) -> float:
    """Calculate muzzle energy in ft-lbs.

    Parameters
    ----------
    bullet_mass_gr : float
        Bullet mass in grains
    muzzle_velocity_fps : float
        Muzzle velocity in ft/s

    Returns
    -------
    float
        Muzzle energy in ft-lbs
        Formula: E = (m_lb * v²) / (2 * g) where g = 32.174 ft/s²
    """

# Validation
def validate_positive(*args, param_names: list[str]) -> None:
    """Validate that all parameters are positive, raise ValueError if not."""

def validate_range(value: float, min_val: float, max_val: float, name: str) -> None:
    """Validate that value is within [min_val, max_val]."""
```

**Dependencies:** None (stdlib only)

---

### `cli/main.py`
**Purpose:** Thin command-line interface wrapper.

**CLI Commands:**
```bash
# Fit vivacity from CSV
python -m cli.main fit <csv_path> [--output results.json] [--plot] [--db-path <path>]

# Run single simulation
python -m cli.main simulate <csv_path> --charge <grains> [--output results.json] [--db-path <path>]

# Burnout scan
python -m cli.main scan-charge <csv_path> --range <min> <max> [--plot] [--db-path <path>]
python -m cli.main scan-barrel <csv_path> --range <min> <max> [--plot] [--db-path <path>]

# Update database with fitted coefficients
python -m cli.main update-db <fit_results.json> [--db-path <path>]

# Import from GRT project file
python -m cli.main import-grt <grt_file> [--output <base_path>] [--plot] [--db-path <path>]

# List available propellants
python -m cli.main list-propellants [--db-path <path>]
```

**Implementation:** Uses `typer` with subcommands, calls `ballistics.*` functions, minimal logic.
- **Global options:** `--db-path` overrides default database location (or `BALLISTICS_DB_PATH` env var)
- **Auto-generated help:** typer provides clean, type-safe CLI with automatic documentation
- **Progress indicators:** Rich integration for fitting progress bars (optional)

**Dependencies:** `typer`, `ballistics.*`

---

## Key Implementation Notes

### 1. Solver Integration Upgrade (solve_ivp + Events)

**Current State:** Fixed timestep (Δt = 1e-6 s) with manual Simpson quadrature integration.

**New Implementation:**
- Use `scipy.integrate.solve_ivp` with adaptive stepping
- **Method:** `DOP853` (8th order Runge-Kutta) for high accuracy, fallback to `RK45` for speed
- **State Vector:** `y = [Z, v, x]` where Z = burn fraction, v = velocity (in/s), x = travel distance (in)
- **ODE System:**
  ```python
  dZ/dt = Λ(Z, P) * P
  dv/dt = (A * Φ * P - Θ) * G / m_eff
  dx/dt = v
  ```
- **Events:**
  - Burnout: `Z - 1.0 = 0` (terminal, direction=+1)
  - Muzzle: `x - L_eff = 0` (terminal, direction=+1)
- **Pressure Calculation:** Algebraic at each step from energy balance
- **Benefits:** 10-100× faster, automatic burnout detection, eliminates truncation error

**Pressure Transition at Burnout:**
- Pre-burnout: `P = (C * Z * F - energy_loss) / V`
- Post-burnout: `P = P_burnout * (V_burnout / V)^γ` (adiabatic expansion)

**Burnout Fraction Metric:**
- **Effective barrel length:** `L_eff = barrel_length - COAL` (cartridge overall length, not case length)
  - COAL measured from bolt face to bullet tip
  - L_eff is actual bullet travel distance available

- **Output metrics depend on whether burnout occurs:**

  **Scenario 1: Burnout occurs (Z reaches 1.0 before muzzle)**:
  - Report: `burnout_distance_from_bolt_in` = COAL + distance traveled when Z = 1.0
  - This is the absolute position along the barrel where propellant is fully consumed

  **Scenario 2: Still burning at muzzle (Z < 1.0 at muzzle exit)**:
  - Report: `muzzle_burn_percentage` = final_Z × 100
  - Indicates percentage of propellant consumed by muzzle exit

- **Target for optimal loads:**
  - Burnout at 80-90% of barrel travel (10-20% before muzzle exit)
  - Rationale: Provides margin for environmental variations (temperature, humidity), powder lot variations, and manufacturing tolerances
  - Example: For 24" barrel with 2.8" COAL (L_eff = 21.2"), target burnout at 19-20" from bolt face
  - Designing for exactly 100% leaves no margin - temperature swings would cause burnout before or after muzzle

---

### 2. Fitting Objective Function and Regularization

**Objective:** Minimize velocity RMSE across load ladder data.

**Formulation:**
```python
params = [Lambda_base, a, b, c, d]

# Weighted residuals
weights = 1 / velocity_sd²  (if provided, else uniform)
residuals = (v_predicted - v_observed) * sqrt(weights)
rmse = sqrt(mean(residuals²))

# Optional L2 regularization (default λ = 0)
penalty = λ * (a² + b² + c² + d²)  # Don't penalize Lambda_base

objective = rmse + penalty
```

**Constraints:**
- **Bounds:**
  - `Lambda_base ∈ [20, 200]` s⁻¹ per 100 bar
  - `a, b, c, d ∈ [-2, 2]`
- **Nonlinear Constraint:** `Λ(Z) > 0` for all `Z ∈ [0, 1]` (enforced via sampling or analytical bounds)

**Optimization Method:**
- Primary: `scipy.optimize.minimize` with `method='L-BFGS-B'`
- Alternative: `method='trust-constr'` for strict constraint enforcement
- Convergence criteria: `ftol=1e-6`, `maxiter=500`

**Initial Guess:**
- `Lambda_base` = database value
- `(a, b, c, d)` = `(1, -1, 0, 0)` (default polynomial)

---

### 3. Data Loading Format

**CSV Structure:**
```csv
# Cartridge: .308 Winchester
# Barrel Length (in): 24.0
# Case Length (in): 2.015
# Bullet Weight (gr): 175
# Bullet Jacket Type: Copper Jacket over Lead
# Cartridge Overall Length (in): 2.810
# Initial Pressure (psi): 5000
# Effective Case Volume (gr H2O): 49.47
# Propellant: Varget
# Powder Base: Single
# Temperature (°F): 70

charge_grains,mean_velocity_fps,velocity_sd,notes
40.0,2575,9,
40.5,2607,11,
41.0,2639,10,
```

**Parsing Logic:**
1. Read all lines starting with `#` as metadata
2. Extract key-value pairs: `# Key: Value`
3. Validate required fields: Barrel Length, Cartridge Overall Length, Bullet Weight, Effective Case Volume, Propellant, Bullet Jacket Type
4. Convert units: all lengths to inches, temperature to Kelvin internally, mass stays in grains until solver
5. Load data rows into `pd.DataFrame`
6. Validate: `charge_grains > 0`, `mean_velocity_fps > 0`, `velocity_sd >= 0`
7. Note: Case Length is optional (informational only); COAL is used for effective barrel length calculation

**Error Handling:**
- Missing required metadata: raise `ValueError` with clear message
- Invalid propellant/bullet name: raise `ValueError` with list of available options
- Missing data columns: raise `ValueError`

---

### 4. Database Update Workflow

**After Successful Fit:**
1. Generate formatted output:
   ```python
   {
       "propellant": "Varget",
       "Lambda_base": 63.5,
       "coeffs": [1.040, -0.614, 0.225, -0.005],
       "rmse_fps": 8.3,
       "data_source": "load_ladder_2024_308.csv"
   }
   ```

2. Export options:
   - **JSON:** `export_fit_results(fit_result, "varget_fit.json", format='json')`
   - **Python snippet:**
     ```python
     # Update database with:
     database.update_propellant_coefficients(
         name="Varget",
         Lambda_base=63.5,
         coeffs=(1.040, -0.614, 0.225, -0.005)
     )
     ```

3. **CLI command:** `python -m cli.main update-db varget_fit.json`
   - Prompts for confirmation before writing to database
   - Backs up database to `ballistics_data.db.backup` first

**Database Schema Addition:**
- Add column `last_updated TIMESTAMP` to track coefficient updates
- Add column `fit_rmse REAL` to store fit quality

---

### 5. Plotting Utilities

**Design Principles:**
- All plotting functions return `(fig, ax)` or `(fig, axes)` tuples
- GUI can embed figures or save them
- CLI can display or save via `--plot` flag
- No `plt.show()` calls inside functions (caller decides)

**Color/Style Standards:**
- Observed data: black circles with error bars
- Predicted/fitted: solid blue line
- Comparison/baseline: dashed red line
- Grid: light gray, always enabled
- Font sizes: title=12pt, axis labels=10pt, ticks=9pt

**Output Formats:**
- Default: PNG at 300 DPI
- Optional: SVG for publication quality

---

## Documentation Standards

### Docstring Format (NumPy Style)

**Requirements:**
- All public functions and classes must have docstrings
- Format: One-line summary, blank line, Parameters section, Returns section
- No motivational text, explanations, or usage examples in docstrings
- Units specified in parameter descriptions

**Template:**
```python
def function_name(param1: float, param2: str) -> dict:
    """One-line summary of purpose.

    Parameters
    ----------
    param1 : float
        Description including units (e.g., "Charge mass in grains")
    param2 : str
        Description

    Returns
    -------
    dict
        Description of return value structure
    """
```

**Private Functions:**
- Single-line docstring or comment acceptable
- Use `_function_name` naming convention

---

### README.md Structure

**Sections:**
1. **Title and one-sentence description**
2. **Installation:**
   ```bash
   pip install -e .   # Editable install from pyproject.toml
   # Or for production:
   pip install .
   ```
3. **Quick Start:** Single example command
4. **Usage Examples:** 3-4 code blocks showing common workflows
5. **CSV Format:** Link to example file in `data/examples/`
6. **Database:** How to list propellants, update coefficients
7. **Testing:** How to run test suite
8. **License:** (if applicable)

**Tone:** Direct, technical, clinical. No marketing language.

---

### Code Comments

**When to Comment:**
- Non-obvious physics equations (include reference)
- Unit conversion steps
- Constraint logic in optimization

**When NOT to Comment:**
- Self-evident code (`# Loop over charges`)
- Function names that explain themselves
- Type-hinted parameters

---

## Example Usage Workflow

### 1. Install Package
```bash
cd IB_Solver
pip install -e .  # Editable install from pyproject.toml (installs ballistics package and CLI)
```

### 2. List Available Propellants
```bash
python -m cli.main list-propellants
# Output: Varget, H4350, N140, ... (84 total)
```

### 3. Import from GRT Project File
```bash
python -m cli.main import-grt data/archive/65CRM_130SMK_N150_Starline_Initial.grtload \
    --output data/examples/65_creedmoor_n150_130gr \
    --plot \
    --db-path data/ballistics_data.db
# Output:
# Extracted metadata from GRT project:
#   Cartridge: 6.5 Creedmoor
#   Barrel Length: 18.000 in
#   COAL: 2.780 in
#   Bullet: 130.00 gr Sierra HPBT-CN 1729
#   Propellant: N150
#   Case Volume: 52.47 gr H₂O (from note override)
#   Temperature: 70.0 °F
#   6 measurement charges found
#
# Created:
#   data/examples/65_creedmoor_n150_130gr.csv          # Standardized CSV
#   data/examples/65_creedmoor_n150_130gr_fit.json     # Auto-fit results
#   data/examples/65_creedmoor_n150_130gr_velocity.png # Velocity plot
#
# Fitting results:
#   Lambda_base = 59.8 s⁻¹ per 100 bar
#   Coefficients: (1.02, -0.58, 0.19, -0.01)
#   RMSE = 6.2 fps
```

**Example extracted data** (6.5 Creedmoor, 130gr Sierra HPBT, N150, 18" barrel):

Metadata:
- Cartridge: 6.5 Creedmoor
- Barrel Length (in): 18.000
- Cartridge Overall Length (in): 2.780
- Bullet Weight (gr): 130.00
- Effective Case Volume (gr H₂O): 52.47 (from note override)
- Propellant: N150
- Bullet Jacket Type: Copper Jacket over Lead (assumed)
- Initial Pressure (psi): 3626
- Temperature (°F): 70.0

Load ladder (computed from measurement charges):
```csv
charge_grains,mean_velocity_fps,velocity_sd,notes
36.52,2534.4,9.6,
37.00,2552.7,2.0,
37.48,2589.0,2.2,
38.00,2619.3,8.7,
38.51,2655.0,6.1,
39.02,2689.1,5.6,
```

### 4. Run Fitting from CSV
```bash
python -m cli.main fit data/examples/308_win_varget_175gr.csv \
    --output results/varget_fit.json \
    --plot
# Output:
# Iteration 100: RMSE = 12.3 fps
# Iteration 200: RMSE = 8.7 fps
# Converged: Lambda_base = 63.2, coeffs = (1.03, -0.61, 0.22, -0.01)
# RMSE = 8.1 fps
# Saved to results/varget_fit.json
# Plot saved to results/varget_fit_velocity.png
```

### 5. Inspect Fit Results
```bash
cat results/varget_fit.json
# {
#   "propellant": "Varget",
#   "Lambda_base": 63.2,
#   "coeffs": [1.03, -0.61, 0.22, -0.01],
#   "rmse_fps": 8.1,
#   "residuals": [...],
#   "success": true
# }
```

### 6. Generate Vivacity Plot
```python
from ballistics.plotting import plot_vivacity_curve
from ballistics.database import get_propellant

# Load database defaults for comparison
db_props = get_propellant("Varget")
db_Lambda = db_props["vivacity"] / 1450
db_coeffs = (db_props["poly_a"], db_props["poly_b"],
             db_props["poly_c"], db_props["poly_d"])

# Plot fitted vs database
fig, ax = plot_vivacity_curve(
    Lambda_base=63.2,
    coeffs=(1.03, -0.61, 0.22, -0.01),
    comparison=(db_Lambda, db_coeffs),
    save_path="vivacity_comparison.png"
)
```

### 7. Update Database Entry
```bash
python -m cli.main update-db results/varget_fit.json
# Confirm update to Varget coefficients? [y/N]: y
# Backup created: data/ballistics_data.db.backup
# Database updated successfully.
```

### 8. Run Burnout Scan Across Charges
```bash
python -m cli.main scan-charge data/examples/308_win_varget_175gr.csv \
    --range 38 45 \
    --points 15 \
    --plot \
    --output results/burnout_scan.csv

# Output CSV columns:
# charge_grains, muzzle_velocity_fps, muzzle_energy_ft_lbs, peak_pressure_psi,
# muzzle_pressure_psi, final_Z, burnout_distance_from_bolt_in (if Z=1.0)
# or muzzle_burn_percentage (if Z<1.0)
```

### 9. Run Burnout Scan Across Barrel Lengths
```bash
python -m cli.main scan-barrel data/examples/308_win_varget_175gr.csv \
    --range 16 26 \
    --charge 42.0 \
    --points 20 \
    --plot

# Identifies barrel length where burnout occurs at 80-90% of travel (10-20% before muzzle)
```

### 10. Programmatic Usage (Python API)
```python
from ballistics.io import load_chronograph_csv, metadata_to_config
from ballistics.fitting import fit_vivacity_polynomial

# Load data
metadata, load_data = load_chronograph_csv("data/examples/308_win_varget_175gr.csv")
config = metadata_to_config(metadata)

# Fit vivacity
fit_result = fit_vivacity_polynomial(
    load_data=load_data,
    config_base=config,
    regularization=0.0,  # No regularization
    verbose=True
)

print(f"Fitted Lambda_base: {fit_result['Lambda_base']:.1f}")
print(f"Coefficients: {fit_result['coeffs']}")
print(f"RMSE: {fit_result['rmse_velocity']:.1f} fps")

# Run burnout analysis
from ballistics.analysis import burnout_scan_charge

scan_results = burnout_scan_charge(
    config=config,
    charge_range=(38, 45),
    n_points=15
)

print(scan_results[["charge_grains", "burnout_distance_from_bolt_in", "peak_pressure_psi", "final_Z"]])
# Shows where burnout occurs for each charge (target: 80-90% of barrel length)
```

### 11. Run Test Suite
```bash
pytest tests/ -v
# test_solver.py::test_solve_ivp_convergence PASSED
# test_solver.py::test_burnout_detection PASSED
# test_fitting.py::test_fit_convergence PASSED
# test_fitting.py::test_bounds_enforcement PASSED
# test_io.py::test_csv_parsing PASSED
# test_integration.py::test_legacy_comparison PASSED
# ==================== 12 passed in 3.42s ====================
```

---

## Technical Constraints

1. **Dependencies:** Core: `numpy`, `scipy`, `pandas`, `matplotlib`, `sqlite3` (stdlib); Optional CLI: `typer` (installed via `pip install .[cli]`)
2. **Package Configuration:** Use `pyproject.toml` (PEP 518/621) for modern Python packaging
3. **Type Hints:** Required on all public API functions and class methods
4. **No Global State:** No module-level mutable state in core modules
5. **File I/O:** All file paths explicit parameters; database path via `BALLISTICS_DB_PATH` env var or `--db-path` flag
6. **Python Version:** ≥3.10 (for `|` union types, `match` statements if needed)
7. **Units:** Document all units in docstrings; use SI internally where practical, but maintain input/output compatibility with imperial (grains, inches, fps, psi)
8. **Error Handling:** Raise `ValueError` with descriptive messages for invalid inputs; no silent failures
9. **Testing:** ≥80% code coverage for core modules (solver, fitting, burn_rate)
10. **Performance:** Solver should complete single run in <100ms on modern hardware; fitting should converge in <10s for typical 5-10 charge ladder
11. **Plotting:** All plots use `matplotlib` with no interactive backends (Agg backend safe for headless)

---

## Package Configuration (pyproject.toml)

**Structure:**
```toml
[build-system]
requires = ["setuptools>=65.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "ballistics"
version = "2.0.0"
description = "Lumped-parameter internal ballistics solver with dynamic vivacity fitting"
requires-python = ">=3.10"
dependencies = [
    "numpy>=1.24",
    "scipy>=1.10",
    "pandas>=2.0",
    "matplotlib>=3.7",
]

[project.optional-dependencies]
cli = ["typer>=0.9.0"]  # CLI interface (optional for GUI use)
dev = ["pytest>=7.0", "pytest-cov>=4.0", "black>=23.0", "ruff>=0.1.0"]

[project.scripts]
ballistics = "cli.main:app"  # Only installed if cli extras installed
```

**Installation modes:**
```bash
# Core library only (for GUI integration, no typer dependency)
pip install .

# With CLI tools
pip install .[cli]

# Development mode with all extras
pip install -e .[cli,dev]
```

**Benefits:**
- Core library has zero extra dependencies beyond scientific Python stack
- CLI is optional extra for users who want command-line interface
- GUI applications can import `ballistics` package without pulling in typer
- Cleaner dependency management and smaller installation footprint

---

## Implementation Sequence

### Phase 1: Core Modular Structure + solve_ivp Upgrade
1. Create package structure and `__init__.py` files
2. Implement `utils.py` (constants, conversions, validation)
3. Implement `burn_rate.py` (vivacity polynomial)
4. Implement `props.py` (dataclasses)
5. Migrate `database.py` from `create_database.py`
6. Implement `solver.py` with `solve_ivp` and events
7. Write unit tests for solver accuracy vs. legacy

### Phase 2: Fitting and I/O
8. Implement `io.py` (CSV parsing, metadata extraction)
9. Implement `fitting.py` (5-parameter optimization)
10. Write unit tests for fitting convergence
11. Write integration tests comparing fitted results to published data

### Phase 3: Analysis and CLI
12. Implement `analysis.py` (burnout scans, charge ladders)
13. Implement `plotting.py` (vivacity, velocity, burnout maps)
14. Implement `cli/main.py` (typer interface with --db-path support)
15. Create example CSV files in `data/examples/`

### Phase 4: Documentation and Archive
16. Write `README.md` with installation and usage
17. Create `pyproject.toml` for package configuration and dependencies
18. Move legacy files to `archive/` directory
19. Create `data/published/README.md` for Phase 2 published data format
20. Final testing and validation

---

**End of Design Plan**
