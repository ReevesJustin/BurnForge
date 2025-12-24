#!/usr/bin/env python3
"""Test fitting with better initial guess after database fix."""

import numpy as np
from ballistics import load_grt_project, metadata_to_config, fit_vivacity_polynomial

# Load test data
grt_file = "data/grt_files/65CM_130SMK_Varget_Starline.grtload"
metadata, load_data = load_grt_project(grt_file)
config = metadata_to_config(metadata)

print(f"Testing fitting with better initial guess...")
print(f"Propellant: {config.propellant.name}")
print(f"Database Lambda_base: {config.propellant.Lambda_base:.6f}")
print()

# Test with better initial guess
print("="*70)
print("Test 1: Better initial guess")
print("="*70)

better_guess = (0.025, 1.0, -0.5, 0.0, 0.0)  # Higher Lambda_base
better_bounds = (
    (0.015, 0.5, -1.5, -1.0, -0.5),  # Lower bounds
    (0.080, 1.5, 0.5, 1.0, 0.5),     # Upper bounds
)

fit_result = fit_vivacity_polynomial(
    load_data,
    config,
    initial_guess=better_guess,
    bounds=better_bounds,
    verbose=True,
)

print(f"\nFit Results:")
print(f"  Lambda_base: {fit_result['Lambda_base']:.6f}")
print(f"  Coefficients: {fit_result['coeffs']}")
print(f"  RMSE: {fit_result['rmse_velocity']:.2f} fps")
print(f"  Convergence: {fit_result['convergence']['success']}")

# Check residuals
residuals = np.array(fit_result['residuals'])
charges = load_data['charge_grains'].values
predicted = np.array(fit_result['predicted_velocities'])
measured = load_data['mean_velocity_fps'].values

print(f"\nDetailed Results:")
for i, (charge, meas, pred, res) in enumerate(zip(charges, measured, predicted, residuals)):
    print(f"  {charge:5.1f} gr: measured={meas:4.0f} fps, predicted={pred:4.0f} fps, residual={res:+6.1f} fps")

print(f"\nBias Analysis:")
mean_residual = np.mean(residuals)
print(f"  Mean residual: {mean_residual:.2f} fps")
print(f"  Std residual: {np.std(residuals):.2f} fps")
print(f"  Max abs residual: {np.max(np.abs(residuals)):.2f} fps")
