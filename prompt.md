Prompt:
You are an expert Python developer specializing in scientific computing and internal ballistics modeling. Your task is to design a clean, modular, production-grade Python project that significantly improves an existing lumped-parameter internal ballistics solver.

The current code base includes:
    create_database.py: Builds SQLite database with propellant and bullet data, including vivacity polynomial coefficients (a, b, c, d).
    solver.py: Core 0D internal ballistics solver using dynamic vivacity Λ(Z), energy balance, and database lookup.
    fit_vivacity.py: Fits only base vivacity using a few published data points.
    plot_vivacity.py: Plots vivacity curve.
    help.md: Basic usage notes.

Project Goal
    Enable high-confidence prediction of propellant burnout distance (barrel location where Z = 1.0) by fitting full dynamic vivacity polynomials using extensive chronograph data from load ladders (typically 3-7 charge weights in ~0.5 gr increments, mean velocity from 10+ shot strings).

Core Requirements
    Fit the full cubic vivacity model:
        Λ(Z) = Λ_base × (a + b·Z + c·Z² + d·Z³)
    Optimize all 5 parameters (Λ_base, a, b, c, d) to match velocity across a wide charge range.
    Use velocity-only data (no pressure required). Support CSV input with columns: charge_grains, mean_velocity_fps (optional: velocity_sd for future weighting).
    Replace fixed-timestep integration in the solver with scipy.integrate.solve_ivp (adaptive step, RK45 or DOP853). Add events for burnout (Z=1) and muzzle exit.
    Highly modular structure to support future GUI development (similar to Gordon's Reloading Tool). The core solver, database, and fitting logic must be importable without side effects.
    Clinical, concise documentation:
    No marketing fluff, no motivational text.
    Clear, direct, technical language only.
    Docstrings: purpose, parameters, returns, units.
    README: installation, usage examples, file formats.
    No excessive commentary in code.


Deliverables:
    Produce the following in markdown sections:

Project Overview:
    One-paragraph summary of purpose and scope.
    Directory Structure
    Full tree with file names and one-line purpose each.
    Module Details For each module/file:
        Purpose
        Key public functions/classes with signatures and brief description
        Dependencies

Key Implementation Notes:
    Solver integration upgrade (solve_ivp + events)
    Fitting objective function and regularization
    Data loading format
    Database update workflow
    Plotting utilities

Documentation Standards:
    Explicit rules for docstrings, README, comments.
    Example Usage Workflow
Step-by-step commands:
    Install dependencies
    Run a fit from CSV
    Generate plots/report
    Update database entry
    Run burnout scan across charges or barrel lengths

Technical Constraints:
    Use only: numpy, scipy, pandas, matplotlib, sqlite3
    Type hints required on public API
    No global state in core modules
    All file I/O explicit and configurable
    Output only the requested markdown sections. Be precise, clinical, and thorough.


1. Replace Fixed-Timestep Integration with Modern ODE Solver
Current: Fixed Δt = 1e-6 s with manual Simpson quadrature → inefficient, prone to truncation error, hard to debug.
Improvement: Use scipy.integrate.solve_ivp with adaptive stepsize (method='DOP853' or 'Radau' for stiff problems) and terminal events for:

Burnout (Z == 1.0)
Muzzle exit (distance == L_eff)

Benefits:
    10–100× faster
    Higher accuracy
    Automatic detection of exact burnout distance (critical for your goal)
    Easier to add new state variables later

2. Full Dynamic Vivacity Polynomial Fitting (5 Parameters)
    Current: Fits only Λ_base, fixed polynomial (1, -1, 0, 0).
    Improvement: Optimize all five parameters:
        Λ_base (s⁻¹ per 100 bar)
        a, b, c, d → Λ(Z) = Λ_base × (a + bZ + cZ² + dZ³)
        Use scipy.optimize.minimize (method='L-BFGS-B' or 'trust-constr') with:

    Velocity residuals only
    Bounds to prevent negative vivacity (e.g., require Λ(Z) > 0 for Z ∈ [0,1])
    Optional L2 regularization on coefficients to favor smooth, physical curves
    Result: Much better fit across wide charge range → more reliable burnout distance prediction.

3. Proper Modular Package Structure
Current: Flat scripts with side effects.

Improvement:
textballistics_solver/
├── __init__.py
├── database.py          # CRUD operations, schema management
├── props.py             # Propellant & bullet property classes/loaders
├── solver.py            # Core ODE system, solve_ivp integration
├── burn_rate.py         # Vivacity functions, polynomial evaluation
├── fitting.py           # Multi-point fitting routines
├── analysis.py          # Burnout scans, charge ladders, barrel length sweeps
├── io.py                # CSV/JSON loaders, result exporters
├── plotting.py          # Velocity vs charge, vivacity curve, burnout maps
└── utils.py             # Unit conversions, constants
Benefits:
    Clean imports
    No global state
    GUI can import solver/fitting/database directly without running scripts

4. Standardized Experimental Data Input Example
Format (CSV):
    # Cartridge: .308 Winchester
    # Barrel Length (in): 24.0
    # Case Length (in): 2.015
    # Bullet Weight (gr): 175
    # Bullet Length (in): 1.25
    # Bullet Jacket Type: Copper Jacket over Lead
    # Cartridge Overall Length (in): 2.810
    # Firearm Weight (lb): 12.5
    # Initial Pressure (psi): 5000
    # Effective Case Volume (gr H2O): 49.47
    # Propellant: Accurate 2495
    # Powder Base: Single
    # Propellant Geometry: Extruded
    # Propellant Qex (kJ/kg): 4200
    # Propellant Bulk Density (g/cm³): 0.95
    # Temperature (°F): 70
    # Firearm: Tikka T3x CTR
    # Notes: COAL to lands -0.020", primer CCI 250, brass Lapua, annealed necks
charge_grains,mean_velocity_fps,velocity_sd,notes
40.0,2575,9,
40.5,2607,11,
41.0,2639,10,
41.5,2670,12,
42.0,2701,11,
42.5,2730,14,compressed
43.0,2760,15,"primer flattening"
...

Load with pandas → easy weighting by 1/SD² if desired.

Field Summary:
    Metadata - (# comment lines — required for key fields)
    Cartridge — for reference and future grouping
    Barrel Length (in)
    Case Length (in)
    Bullet Weight (gr)
    Bullet Length (in) — optional now, useful later
    Bullet Jacket Type — maps to database bullet_types table
    Cartridge Overall Length (in)
    Firearm Weight (lb) — informational/recoil context
    Initial Pressure (psi) — P_IN override
    Effective Case Volume (gr H2O) — critical (directly affects loading density and V₀)
    Propellant — exact name matching database
    Powder Base: "Single" or "Double"
    Propellant Geometry: "Extruded" | "Spherical" | "Flake"
    Propellant Qex (kJ/kg) — explosive energy
    Propellant Bulk Density (g/cm³)
    Temperature (°F)
    Firearm and general Notes

Data columns:
    charge_grains — required
    mean_velocity_fps — required (from ≥10-shot strings)
    velocity_sd — required (enables weighted fitting: higher weight for tighter SD's)
    notes — optional per-charge comments
    Solver Output Requirements (Always Returned)

The loader in io.py should:
    Parse metadata strictly
    Validate required fields
    Convert input values to correct units used by the solver (suggest using SI units for calculations, but use units listed in inputs and outputs)
    Pass fixed parameters directly to solver/fitting calls

5. Automatic Database Update Workflow
After successful fit:
    Output formatted Python dict snippet ready for create_database.py
    Optional: direct SQLite UPDATE via database.py module

6. Burnout Position Analysis Tools
Add functions to:
    Sweep charge weight → plot burnout distance vs charge
    Sweep barrel length → find charges achieving burnout at desired position (e.g., 90–95% travel)
    Report muzzle pressure and final Z for each case

7. Clinical Documentation Standard
Enforce:
    Docstrings: one-line summary + Parameters/Returns sections only
    No motivational or explanatory fluff
Example:
Pythondef calc_dynamic_vivacity(Z: float, Lambda_base: float, coeffs: tuple[float, float, float, float]) -> float:
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
8. GUI-Ready Design Principles
    All core modules pure functions or classes → no print() statements, no sys.argv parsing
    Configuration via explicit parameters or dataclass
    Plotting functions return matplotlib Figure/Axes objects (GUI can display or save)
    Solver outputs structured dict or dataclass → easy to tabulate

9. Implement in this order:
    1. Modular structure + solve_ivp upgrade
    2. Full 5-parameter fitting
    3. Data input + burnout analysis
    4. Documentation enforcement

10. Published Load Data Comparison (Future Feature)
Add a utility in analysis.py:
Pythondef compare_to_published(
    simulated_results: list[dict],
    published_data: list[dict]  # e.g., from Hodgdon/Lapua manuals: charge, velocity, pressure
) -> pd.DataFrame:
    """
    Align simulated peak pressure and velocity against published values.
    Return DataFrame with deltas and % errors for sanity check.
    """
Load published data from separate CSV/JSON (manual entry or scraped).
Match on nearest charge weight.
Flag loads where simulated pressure exceeds published by >5–10% (safety check).

