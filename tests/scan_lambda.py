#!/usr/bin/env python3
"""Scan Lambda_base values to find correct range."""

import numpy as np
from ballistics import load_grt_project, metadata_to_config
from ballistics.core.solver import solve_ballistics
from copy import deepcopy

# Load test data
grt_file = "data/grt_files/65CM_130SMK_Varget_Starline.grtload"
metadata, load_data = load_grt_project(grt_file)
config_base = metadata_to_config(metadata)

print("Scanning Lambda_base values...")
print(f"Target velocity for 37.0 gr: {load_data.iloc[0]['mean_velocity_fps']:.0f} fps\n")

# Test a range of Lambda values
lambda_values = [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.10, 0.12, 0.15]
test_charge = load_data.iloc[0]['charge_grains']
target_vel = load_data.iloc[0]['mean_velocity_fps']

print(f"{'Lambda':<10} {'Predicted':<12} {'Error':<10} {'Status'}")
print("-" * 45)

best_lambda = None
best_error = float('inf')

for lam in lambda_values:
    config = deepcopy(config_base)
    config.charge_mass_gr = test_charge
    config.propellant.Lambda_base = lam
    config.propellant.poly_coeffs = (1.0, -1.0, 0.0, 0.0)

    try:
        result = solve_ballistics(config)
        pred_vel = result['muzzle_velocity_fps']
        error = pred_vel - target_vel

        status = ""
        if abs(error) < 50:
            status = "✓ GOOD"
        elif abs(error) < 100:
            status = "~ OK"

        print(f"{lam:<10.6f} {pred_vel:<12.1f} {error:+10.1f} {status}")

        if abs(error) < abs(best_error):
            best_error = error
            best_lambda = lam

    except Exception as e:
        print(f"{lam:<10.6f} {'FAILED':<12} {str(e)[:20]}")

print(f"\nBest Lambda: {best_lambda:.6f} (error: {best_error:+.1f} fps)")
print(f"\nDatabase Lambda was: {config_base.propellant.Lambda_base:.6f}")
