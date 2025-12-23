"""Analyze fitting accuracy for GRT file."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import numpy as np
import matplotlib.pyplot as plt
from ballistics import load_grt_project, metadata_to_config, fit_vivacity_polynomial
from ballistics.solver import solve_ballistics
from ballistics.burn_rate import calc_vivacity

# Load GRT file
grt_file = "65CRM_130SMK_N150_Starline_Initial.grtload"
metadata, load_data = load_grt_project(grt_file)

print("="*60)
print("GRT File Analysis")
print("="*60)
print(f"Cartridge: {metadata['cartridge']}")
print(f"Barrel Length: {metadata['barrel_length_in']:.2f} in")
print(f"Bullet: {metadata['bullet_mass_gr']:.1f} gr")
print(f"Propellant: {metadata['propellant_name']}")
print(f"Temperature: {metadata['temperature_f']:.1f} °F")
print(f"COAL: {metadata['cartridge_overall_length_in']:.3f} in")
print(f"Case Volume: {metadata['case_volume_gr_h2o']:.2f} gr H2O")
print(f"Number of charges: {len(load_data)}")
print()

# Create config
config = metadata_to_config(metadata)

print("="*60)
print("Fitting Vivacity Polynomial")
print("="*60)

# Fit with verbose output
fit_result = fit_vivacity_polynomial(load_data, config, verbose=True)

print()
print("="*60)
print("Residual Analysis")
print("="*60)

# Detailed residual analysis
charges = load_data['charge_grains'].values
measured = load_data['mean_velocity_fps'].values
predicted = np.array(fit_result['predicted_velocities'])
residuals = np.array(fit_result['residuals'])

print(f"{'Charge':>8} {'Measured':>10} {'Predicted':>10} {'Residual':>10} {'% Error':>10}")
print("-" * 60)
for i, charge in enumerate(charges):
    pct_error = (residuals[i] / measured[i]) * 100
    print(f"{charge:8.1f} {measured[i]:10.1f} {predicted[i]:10.1f} {residuals[i]:10.1f} {pct_error:9.2f}%")

print()
print(f"RMSE: {fit_result['rmse_velocity']:.2f} fps")
print(f"Mean Residual: {np.mean(residuals):.2f} fps")
print(f"Std Residual: {np.std(residuals):.2f} fps")
print(f"Max Positive Residual: {np.max(residuals):.2f} fps")
print(f"Max Negative Residual: {np.min(residuals):.2f} fps")

# Check for systematic bias
print()
print("Systematic Bias Check:")
first_half_mean = np.mean(residuals[:len(residuals)//2])
second_half_mean = np.mean(residuals[len(residuals)//2:])
print(f"  First half mean residual: {first_half_mean:.2f} fps")
print(f"  Second half mean residual: {second_half_mean:.2f} fps")
if abs(second_half_mean - first_half_mean) > 5:
    print(f"  WARNING: Systematic bias detected ({second_half_mean - first_half_mean:.2f} fps difference)")

print()
print("="*60)
print("Vivacity Curve Analysis")
print("="*60)

Lambda_base = fit_result['Lambda_base']
coeffs = fit_result['coeffs']
a, b, c, d = coeffs

print(f"Lambda_base: {Lambda_base:.6f}")
print(f"Coefficients: a={a:.6f}, b={b:.6f}, c={c:.6f}, d={d:.6f}")
print()

# Evaluate vivacity at different burn fractions
Z_vals = np.linspace(0, 1, 11)
print(f"{'Z':>6} {'Λ(Z)':>12} {'Poly(Z)':>12}")
print("-" * 32)
for Z in Z_vals:
    Lambda_Z = calc_vivacity(Z, Lambda_base, coeffs)
    poly_val = a + b*Z + c*Z**2 + d*Z**3
    print(f"{Z:6.2f} {Lambda_Z:12.6f} {poly_val:12.6f}")

# Check for database comparison
print()
print("="*60)
print("Database Comparison")
print("="*60)
print(f"Database Lambda_base: {config.propellant.Lambda_base:.6f}")
print(f"Fitted Lambda_base: {Lambda_base:.6f}")
print(f"Ratio (Fitted/Database): {Lambda_base / config.propellant.Lambda_base:.2f}x")

print()
print("="*60)
print("Optimization Investigation")
print("="*60)

# Try different optimization approaches
print("\nTrying alternative optimization methods...")

# Try with tighter tolerance
print("\n1. L-BFGS-B with tighter tolerance:")
from ballistics.fitting import fit_vivacity_polynomial as fit_func
from scipy.optimize import minimize
import pandas as pd

# Custom fit with different options
def try_fit_with_options(load_data, config, method='L-BFGS-B', ftol=1e-6, maxiter=500):
    """Try fitting with custom options."""
    from ballistics.fitting import _objective_function
    from ballistics.burn_rate import validate_vivacity_positive

    Lambda_base_init = Lambda_base  # Use previous fit as initial guess
    initial_guess = (Lambda_base_init, a, b, c, d)

    bounds = (
        (0.01, -2.0, -2.0, -2.0, -2.0),
        (0.15, 2.0, 2.0, 2.0, 2.0)
    )

    result = minimize(
        lambda params: _objective_function(params, load_data, config, 0.0),
        x0=initial_guess,
        method=method,
        bounds=list(zip(bounds[0], bounds[1])),
        options={'maxiter': maxiter, 'ftol': ftol}
    )

    return result

# Try tighter tolerance
result_tight = try_fit_with_options(load_data, config, ftol=1e-9, maxiter=1000)
print(f"  Final objective: {result_tight.fun:.4f}")
print(f"  Iterations: {result_tight.nit}")
print(f"  Success: {result_tight.success}")

# Try with regularization to see if overfitting is an issue
print("\n2. With L2 regularization (0.001):")
fit_reg = fit_vivacity_polynomial(load_data, config, regularization=0.001, verbose=False)
print(f"  RMSE: {fit_reg['rmse_velocity']:.2f} fps")
print(f"  Lambda_base: {fit_reg['Lambda_base']:.6f}")
print(f"  Coeffs: ({fit_reg['coeffs'][0]:.3f}, {fit_reg['coeffs'][1]:.3f}, {fit_reg['coeffs'][2]:.3f}, {fit_reg['coeffs'][3]:.3f})")

print("\n3. With wider Lambda bounds:")
wider_bounds = (
    (0.005, -2.0, -2.0, -2.0, -2.0),
    (0.25, 2.0, 2.0, 2.0, 2.0)
)
fit_wide = fit_vivacity_polynomial(load_data, config, bounds=wider_bounds, verbose=False)
print(f"  RMSE: {fit_wide['rmse_velocity']:.2f} fps")
print(f"  Lambda_base: {fit_wide['Lambda_base']:.6f}")
print(f"  Coeffs: ({fit_wide['coeffs'][0]:.3f}, {fit_wide['coeffs'][1]:.3f}, {fit_wide['coeffs'][2]:.3f}, {fit_wide['coeffs'][3]:.3f})")

# Check residuals for wide bounds fit
predicted_wide = np.array(fit_wide['predicted_velocities'])
residuals_wide = predicted_wide - measured
print(f"\n  Residuals with wider bounds:")
for i, charge in enumerate(charges):
    print(f"    {charge:.1f} gr: {residuals_wide[i]:+7.1f} fps")

print()
print("="*60)
print("Model Limitation Analysis")
print("="*60)

# Check if model can theoretically achieve better fit
# by testing if residuals can be reduced with manual parameter tweaks

print("\nTesting if model structure is limiting fit quality...")
print("(Trying Lambda_base adjustments to see if RMSE improves)")

lambda_test_vals = np.linspace(0.08, 0.16, 9)
rmse_vals = []

for Lambda_test in lambda_test_vals:
    predicted_test = []
    for charge in charges:
        config_test = metadata_to_config(metadata)
        config_test.charge_mass_gr = charge
        result = solve_ballistics(config_test, Lambda_override=Lambda_test, coeffs_override=coeffs)
        predicted_test.append(result['muzzle_velocity_fps'])

    residuals_test = np.array(predicted_test) - measured
    rmse_test = np.sqrt(np.mean(residuals_test**2))
    rmse_vals.append(rmse_test)
    if Lambda_test == Lambda_base:
        print(f"  Lambda = {Lambda_test:.4f}: RMSE = {rmse_test:.2f} fps (current fit)")
    else:
        print(f"  Lambda = {Lambda_test:.4f}: RMSE = {rmse_test:.2f} fps")

best_lambda_idx = np.argmin(rmse_vals)
print(f"\nBest single Lambda (no polynomial): {lambda_test_vals[best_lambda_idx]:.4f}")
print(f"Best RMSE achievable with constant Lambda: {rmse_vals[best_lambda_idx]:.2f} fps")

print("\n" + "="*60)
print("Summary")
print("="*60)
print(f"Current fit RMSE: {fit_result['rmse_velocity']:.2f} fps")
print(f"Mean absolute error: {np.mean(np.abs(residuals)):.2f} fps")
print(f"Max absolute error: {np.max(np.abs(residuals)):.2f} fps")
print(f"\nSystematic bias: {'Yes' if abs(second_half_mean - first_half_mean) > 5 else 'No'}")
if abs(second_half_mean - first_half_mean) > 5:
    print(f"  Lower charges: {first_half_mean:+.2f} fps average residual")
    print(f"  Higher charges: {second_half_mean:+.2f} fps average residual")
    print(f"  Suggests model may need additional terms or physics")
print("\n" + "="*60)
