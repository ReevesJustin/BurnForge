# Manual Data Entry Template

Use this JSON template for manual data entry when GRT project files are not available. All fields are required unless marked optional.

```json
{
  "metadata": {
    "cartridge": ".308 Winchester",
    "barrel_length_in": 24.0,
    "cartridge_overall_length_in": 2.810,
    "bullet_mass_gr": 175.0,
    "case_volume_gr_h2o": 49.47,
    "propellant_name": "Varget",
    "bullet_jacket_type": "Copper Jacket over Lead",
    "temperature_f": 70.0,
    "p_initial_psi": 5000.0,
    "caliber_in": 0.308,
    "firearm": "Tikka T3x CTR",
    "notes": "COAL to lands -0.020\", primer CCI 250, brass Lapua, annealed necks"
  },
  "load_data": [
    {
      "charge_grains": 40.0,
      "mean_velocity_fps": 2575,
      "velocity_sd": 9,
      "notes": ""
    },
    {
      "charge_grains": 40.5,
      "mean_velocity_fps": 2607,
      "velocity_sd": 11,
      "notes": ""
    },
    {
      "charge_grains": 41.0,
      "mean_velocity_fps": 2639,
      "velocity_sd": 10,
      "notes": ""
    },
    {
      "charge_grains": 41.5,
      "mean_velocity_fps": 2671,
      "velocity_sd": 12,
      "notes": ""
    },
    {
      "charge_grains": 42.0,
      "mean_velocity_fps": 2701,
      "velocity_sd": 11,
      "notes": ""
    }
  ]
}
```

## Field Descriptions

### Metadata Fields

| Field | Type | Required | Description | Units |
|-------|------|----------|-------------|-------|
| `cartridge` | string | Yes | Cartridge designation | - |
| `barrel_length_in` | number | Yes | Total barrel length | inches |
| `cartridge_overall_length_in` | number | Yes | COAL (bolt face to bullet tip) | inches |
| `bullet_mass_gr` | number | Yes | Bullet weight | grains |
| `case_volume_gr_h2o` | number | Yes | Case volume measured with water | grains H₂O |
| `propellant_name` | string | Yes | Propellant name (must match database) | - |
| `bullet_jacket_type` | string | Yes | Bullet type (must match database) | - |
| `temperature_f` | number | Yes | Ambient temperature | °F |
| `p_initial_psi` | number | No | Initial chamber pressure (default: 5000) | psi |
| `caliber_in` | number | Yes | Bullet diameter | inches |
| `firearm` | string | No | Firearm description | - |
| `notes` | string | No | General notes | - |

### Load Data Fields

| Field | Type | Required | Description | Units |
|-------|------|----------|-------------|-------|
| `charge_grains` | number | Yes | Powder charge weight | grains |
| `mean_velocity_fps` | number | Yes | Mean muzzle velocity | ft/s |
| `velocity_sd` | number | No | Velocity standard deviation (for weighting) | ft/s |
| `notes` | string | No | Charge-specific notes | - |

## Usage

```python
import json
from ballistics import metadata_to_config, fit_vivacity_polynomial

# Load JSON data
with open('my_load_data.json', 'r') as f:
    data = json.load(f)

# Convert to config
config = metadata_to_config(data['metadata'])

# Create DataFrame for fitting
import pandas as pd
load_data = pd.DataFrame(data['load_data'])

# Fit model
fit_result = fit_vivacity_polynomial(load_data, config, verbose=True)
```

## Notes

- Velocity measurements should be from 10+ shot strings for statistical validity
- Include velocity_sd when available for weighted fitting
- Ensure propellant_name and bullet_jacket_type match database entries
- For best results, use 5-8 charge weights spanning 85-115% of target load</content>
<parameter name="filePath">data/examples/json_templates/manual_entry_template.md