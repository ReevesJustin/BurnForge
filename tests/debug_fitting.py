#!/usr/bin/env python3
"""Debug fitting issues."""

import numpy as np
from ballistics import load_grt_project, metadata_to_config
from ballistics.core.solver import solve_ballistics

# Load test data
grt_file = "data/grt_files/65CM_130SMK_Varget_Starline.grtload"
metadata, load_data = load_grt_project(grt_file)
config = metadata_to_config(metadata)

print("Testing basic solve with database propellant parameters...")
print(f"Propellant: {config.propellant.name}")
print(f"Lambda_base (from DB): {config.propellant.Lambda_base:.6f}")
print(f"Poly coeffs (from DB): {config.propellant.poly_coeffs}")
print()

# Test with first charge
test_charge = load_data.iloc[0]
config.charge_mass_gr = test_charge['charge_grains']

print(f"Test charge: {test_charge['charge_grains']:.2f} gr")
print(f"Measured velocity: {test_charge['mean_velocity_fps']:.1f} fps")
print()

try:
    result = solve_ballistics(config)
    print(f"Predicted velocity: {result['muzzle_velocity_fps']:.1f} fps")
    print(f"Peak pressure: {result['peak_pressure_psi']:.0f} psi")
    print(f"Final Z: {result['final_Z']:.3f}")
    print(f"Success!")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*70)
print("Testing with initial guess parameters (1, -1, 0, 0)...")
print("="*70 + "\n")

# Test with initial guess
from copy import deepcopy
config2 = deepcopy(config)
config2.propellant.poly_coeffs = (1.0, -1.0, 0.0, 0.0)

try:
    result2 = solve_ballistics(config2)
    print(f"With (1,-1,0,0) coeffs: {result2['muzzle_velocity_fps']:.1f} fps")
except Exception as e:
    print(f"Error with (1,-1,0,0): {e}")
