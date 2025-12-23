# Internal Ballistics Solver

Modular Python package for lumped-parameter internal ballistics modeling with dynamic vivacity fitting. Optimizes 5-parameter vivacity polynomials from velocity-only chronograph data to predict propellant burnout distance.

## Installation

```bash
cd IB_Solver
pip install -e .  # Core library only

# Or with CLI tools
pip install -e .[cli]

# Or for development
pip install -e .[cli,dev]
```

## Quick Start

### Run existing solver test

```bash
python3 tests/test_solver.py
```

### List available propellants

```python
from ballistics import list_propellants
print(list_propellants())  # Shows all 84 propellants
```

### Simple ballistics calculation

```python
from ballistics import (
    PropellantProperties,
    BulletProperties,
    BallisticsConfig,
    solve_ballistics
)

# Load from database
propellant = PropellantProperties.from_database("Varget")
bullet = BulletProperties.from_database("Copper Jacket over Lead")

# Configure
config = BallisticsConfig(
    bullet_mass_gr=175.0,
    charge_mass_gr=42.0,
    caliber_in=0.308,
    case_volume_gr_h2o=49.5,
    barrel_length_in=24.0,
    cartridge_overall_length_in=2.810,  # COAL
    propellant=propellant,
    bullet=bullet,
    temperature_f=70.0
)

# Solve
results = solve_ballistics(config)

print(f"Muzzle velocity: {results['muzzle_velocity_fps']:.1f} fps")
print(f"Muzzle energy: {results['muzzle_energy_ft_lbs']:.0f} ft-lbs")
print(f"Peak pressure: {results['peak_pressure_psi']:.0f} psi")

if 'burnout_distance_from_bolt_in' in results:
    print(f"Burnout at: {results['burnout_distance_from_bolt_in']:.2f} in from bolt")
else:
    print(f"Still burning at muzzle: {results['muzzle_burn_percentage']:.1f}%")
```

## Features

- **Adaptive ODE integration** using scipy.integrate.solve_ivp with DOP853 method
- **Event detection** for burnout (Z=1.0) and muzzle exit
- **5-parameter vivacity fitting** (Λ_base, a, b, c, d) from chronograph data
- **Burnout prediction** with distance from bolt face reporting
- **Database** of 84 propellants and bullet types
- **Type-safe** with full type hints on public API
- **Zero global state** for clean imports and testing

## Project Structure

```
IB_Solver/
├── src/ballistics/       # Core solver package
│   ├── solver.py         # ODE system and solve_ivp integration
│   ├── props.py          # Dataclasses for configuration
│   ├── database.py       # SQLite operations
│   ├── burn_rate.py      # Vivacity polynomial
│   └── utils.py          # Constants and conversions
├── tests/                # Unit and integration tests
├── data/                 # Database and examples
│   ├── ballistics_data.db
│   └── examples/
└── archive/              # Legacy solver (for comparison)
```

## Database

List propellants:
```python
from ballistics import list_propellants
propellants = list_propellants()
```

Get propellant properties:
```python
from ballistics import get_propellant
props = get_propellant("Varget")
```

Update vivacity coefficients after fitting:
```python
from ballistics import update_propellant_coefficients
update_propellant_coefficients(
    name="Varget",
    Lambda_base=63.5,
    coeffs=(1.03, -0.61, 0.22, -0.01)
)
```

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test
python3 tests/test_solver.py
```

## Environment Variables

- `BALLISTICS_DB_PATH`: Override default database location

```bash
export BALLISTICS_DB_PATH=/path/to/custom/ballistics.db
```

## Requirements

- Python ≥3.10
- numpy ≥1.24
- scipy ≥1.10
- pandas ≥2.0
- matplotlib >=3.7

## Output Metrics

Always returned:
- `muzzle_velocity_fps`: Muzzle velocity in ft/s
- `muzzle_energy_ft_lbs`: Muzzle energy in ft-lbs
- `peak_pressure_psi`: Peak pressure in psi
- `muzzle_pressure_psi`: Pressure at muzzle exit in psi
- `final_Z`: Final burn fraction (0-1)
- `total_time_s`: Total simulation time in seconds

Conditional (if burnout occurs):
- `burnout_distance_from_bolt_in`: Distance from bolt face where Z=1.0

Conditional (if still burning at muzzle):
- `muzzle_burn_percentage`: Percentage of propellant burned at muzzle

## Design Goals

Target: Burnout at 80-90% of barrel travel (10-20% before muzzle) to accommodate environmental variations and manufacturing tolerances.

## License

See LICENSE file for details.
