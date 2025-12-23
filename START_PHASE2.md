# Phase 2 Quick Start Guide

## Status Check
✅ Phase 1 committed: `549f999` (Core solver with solve_ivp)
📍 **You are here:** Ready to start Phase 2 (Fitting and I/O)
⏱️ **Estimated time:** Phase 2 will use ~50K tokens (74K remaining = plenty of room)

---

## First 3 Commands

```bash
# 1. Review what was built
cat PHASE1_COMPLETE.md

# 2. Review design specifications for Phase 2
grep -A 50 "fitting.py" DESIGN_PLAN.md | head -100

# 3. Install dependencies (if not already done)
pip install -e .
```

---

## Implementation Order

### Step 1: `src/ballistics/fitting.py` (~250 lines)

Start with this template:

```python
"""Multi-parameter optimization routines with bounds."""

import numpy as np
from scipy.optimize import minimize
import pandas as pd

from .solver import solve_ballistics
from .burn_rate import validate_vivacity_positive
from .props import BallisticsConfig


def fit_vivacity_polynomial(
    load_data: pd.DataFrame,
    config_base: BallisticsConfig,
    initial_guess: tuple[float, float, float, float, float] | None = None,
    bounds: tuple | None = None,
    regularization: float = 0.0,
    method: str = 'L-BFGS-B',
    verbose: bool = True
) -> dict:
    """Fit full 5-parameter vivacity polynomial from load ladder data.

    [See DESIGN_PLAN.md lines 310-365 for full specification]
    """
    # TODO: Implement
    pass
```

**Key requirements:**
- Minimize velocity RMSE: `sqrt(mean((v_pred - v_obs)²))`
- Weights: `1/velocity_sd²` if provided, else uniform
- Bounds: Lambda ∈ [20, 200], a,b,c,d ∈ [-2, 2]
- Constraint: Λ(Z) > 0 for all Z ∈ [0,1]
- Optional L2 regularization: `λ * (a² + b² + c² + d²)`

### Step 2: `src/ballistics/io.py` (~400 lines)

Functions in order:
1. `load_chronograph_csv()` - Parse # metadata + data rows
2. `parse_metadata()` - Extract key-value pairs
3. `metadata_to_config()` - Convert dict → BallisticsConfig
4. `export_fit_results()` - Output JSON/Python snippet
5. `load_grt_project()` - Import GRT XML (see DESIGN_PLAN.md lines 498-537)

**Test file available:** `65CRM_130SMK_N150_Starline_Initial.grtload`

### Step 3: `tests/test_fitting.py` (~100 lines)

Tests:
- `test_fit_convergence()` - Optimizer reaches solution
- `test_bounds_enforcement()` - Parameters stay in bounds
- `test_regularization()` - L2 penalty works

### Step 4: `tests/test_io.py` (~100 lines)

Tests:
- `test_csv_parsing()` - Metadata extraction
- `test_grt_import()` - Load .grtload file, verify conversion
- `test_metadata_to_config()` - Database lookup works

---

## Reference Materials

| File | Lines | What to Look At |
|------|-------|-----------------|
| `DESIGN_PLAN.md` | 310-365 | fitting.py specification |
| `DESIGN_PLAN.md` | 452-542 | io.py specification |
| `DESIGN_PLAN.md` | 498-537 | GRT import details |
| `PHASE1_COMPLETE.md` | All | Phase 1 summary, patterns |
| `src/ballistics/solver.py` | 16-60 | How to call solve_ballistics() |
| `src/ballistics/props.py` | 19-47 | How to load from database |

---

## Code Patterns to Follow

### 1. Objective Function Pattern

```python
def _objective_function(params, load_data, config_base, regularization):
    Lambda_base, a, b, c, d = params

    residuals = []
    weights = []

    for idx, row in load_data.iterrows():
        # Update charge
        config = copy(config_base)
        config.charge_mass_gr = row['charge_grains']

        # Solve with overrides
        result = solve_ballistics(
            config,
            Lambda_override=Lambda_base,
            coeffs_override=(a, b, c, d)
        )

        # Compute weighted residual
        residual = result['muzzle_velocity_fps'] - row['mean_velocity_fps']
        weight = 1.0 / (row['velocity_sd']**2) if 'velocity_sd' in row else 1.0

        residuals.append(residual)
        weights.append(weight)

    # RMSE
    rmse = np.sqrt(np.mean(np.array(residuals)**2 * np.array(weights)))

    # Regularization
    penalty = regularization * (a**2 + b**2 + c**2 + d**2)

    return rmse + penalty
```

### 2. CSV Parsing Pattern

```python
def load_chronograph_csv(filepath):
    metadata = {}
    data_lines = []

    with open(filepath, 'r') as f:
        for line in f:
            if line.startswith('#'):
                # Parse: # Key: Value
                if ':' in line:
                    key, value = line[1:].split(':', 1)
                    metadata[key.strip()] = value.strip()
            else:
                data_lines.append(line)

    # Load data
    from io import StringIO
    load_data = pd.read_csv(StringIO(''.join(data_lines)))

    return metadata, load_data
```

### 3. GRT XML Parsing Pattern

```python
import xml.etree.ElementTree as ET

tree = ET.parse(filepath)
root = tree.getroot()

# Find elements
caliber = root.find('.//caliber')
barrel_length_mm = float(caliber.find(".//input[@name='xe']").get('value'))
barrel_length_in = barrel_length_mm * MM_TO_IN  # From utils.py
```

---

## Common Pitfalls to Avoid

1. **Don't forget unit conversions** in GRT import (mm→in, kg→grains, etc.)
2. **Check for missing metadata** before creating BallisticsConfig
3. **Use `config_base` pattern** for fitting (copy config, update charge)
4. **Return structured dicts** from fitting (match DESIGN_PLAN spec)
5. **Handle missing velocity_sd** gracefully (uniform weights)

---

## Success Criteria for Phase 2

- [ ] fitting.py: Can optimize 5 parameters from velocity data
- [ ] io.py: Can load CSV with metadata
- [ ] io.py: Can import GRT project file
- [ ] Tests pass for fitting convergence
- [ ] Tests pass for CSV/GRT import
- [ ] Example fit runs successfully with generated data

---

## Quick Test After Implementation

```python
# Test fitting (mock data)
import pandas as pd
from ballistics import PropellantProperties, BulletProperties, BallisticsConfig
from ballistics.fitting import fit_vivacity_polynomial

# Create test data
load_data = pd.DataFrame({
    'charge_grains': [40.0, 41.0, 42.0, 43.0],
    'mean_velocity_fps': [2600, 2650, 2700, 2750],
    'velocity_sd': [10, 10, 10, 10]
})

# Base config
prop = PropellantProperties.from_database("Varget")
bullet = BulletProperties.from_database("Copper Jacket over Lead")
config = BallisticsConfig(
    bullet_mass_gr=175.0,
    charge_mass_gr=40.0,  # Will be overridden
    caliber_in=0.308,
    case_volume_gr_h2o=49.5,
    barrel_length_in=24.0,
    cartridge_overall_length_in=2.810,
    propellant=prop,
    bullet=bullet
)

# Fit
result = fit_vivacity_polynomial(load_data, config, verbose=True)
print(f"Lambda_base: {result['Lambda_base']:.1f}")
print(f"Coefficients: {result['coeffs']}")
print(f"RMSE: {result['rmse_velocity']:.1f} fps")
```

---

**Ready to code!** Start with `fitting.py`, reference the DESIGN_PLAN, and follow the established patterns. 🚀
