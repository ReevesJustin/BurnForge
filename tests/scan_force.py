#!/usr/bin/env python3
"""Scan force multipliers to find correct value."""

import numpy as np
from ballistics import load_grt_project, metadata_to_config
from ballistics.core.solver import solve_ballistics
from copy import deepcopy

# Load test data
grt_file = "data/grt_files/65CM_130SMK_Varget_Starline.grtload"
metadata, load_data = load_grt_project(grt_file)
config_base = metadata_to_config(metadata)

test_charge = load_data.iloc[0]['charge_grains']
target_vel = load_data.iloc[0]['mean_velocity_fps']

print(f"Scanning force multipliers...")
print(f"Current force: {config_base.propellant.force:.0f}")
print(f"Target velocity for {test_charge:.1f} gr: {target_vel:.0f} fps\n")

# Test force multipliers
base_force = 365000.0  # Current value after /10
multipliers = [0.1, 0.5, 1.0, 2.0, 3.0, 5.0, 7.5, 10.0, 15.0, 20.0]

print(f"{'Multiplier':<12} {'Force':<15} {'Predicted':<12} {'Error':<10} {'Status'}")
print("-" * 62)

best_mult = None
best_error = float('inf')

for mult in multipliers:
    config = deepcopy(config_base)
    config.charge_mass_gr = test_charge
    config.propellant.force = base_force * mult

    try:
        result = solve_ballistics(config)
        pred_vel = result['muzzle_velocity_fps']
        error = pred_vel - target_vel

        status = ""
        if abs(error) < 50:
            status = "✓✓ EXCELLENT"
        elif abs(error) < 100:
            status = "✓ GOOD"
        elif abs(error) < 200:
            status = "~ OK"

        print(f"{mult:<12.1f} {base_force*mult:<15.0f} {pred_vel:<12.1f} {error:+10.1f} {status}")

        if abs(error) < abs(best_error):
            best_error = error
            best_mult = mult

    except Exception as e:
        print(f"{mult:<12.1f} {base_force*mult:<15.0f} {'FAILED':<12} {str(e)[:30]}")

print(f"\nBest multiplier: {best_mult:.1f}x (force = {base_force*best_mult:.0f}, error: {best_error:+.1f} fps)")
print(f"\nRecommendation: UPDATE propellants SET force = force * {best_mult};")
