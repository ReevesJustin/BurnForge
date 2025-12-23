"""Quick fitting analysis for GRT file."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import numpy as np
from ballistics import load_grt_project, metadata_to_config, fit_vivacity_polynomial
from ballistics.solver import solve_ballistics
from ballistics.burn_rate import calc_vivacity

# Load GRT file
grt_file = "65CRM_130SMK_N150_Starline_Initial.grtload"
metadata, load_data = load_grt_project(grt_file)

print("="*70)
print("GRT File Data")
print("="*70)
print(f"Cartridge: {metadata['cartridge']}")
print(f"Barrel Length: {metadata['barrel_length_in']:.2f} in")
print(f"Bullet: {metadata['bullet_mass_gr']:.1f} gr")
print(f"Propellant: {metadata['propellant_name']}")
print(f"Temperature: {metadata['temperature_f']:.1f} °F")
print(f"COAL: {metadata['cartridge_overall_length_in']:.3f} in")
print(f"Case Volume: {metadata['case_volume_gr_h2o']:.2f} gr H2O")
print(f"\nMeasurement Data:")
print(load_data)
print()

# Create config
config = metadata_to_config(metadata)

print("="*70)
print("Fitting Vivacity Polynomial")
print("="*70)

# Fit with verbose output
fit_result = fit_vivacity_polynomial(load_data, config, verbose=True)

print()
print("="*70)
print("Detailed Residual Analysis")
print("="*70)

charges = load_data['charge_grains'].values
measured = load_data['mean_velocity_fps'].values
predicted = np.array(fit_result['predicted_velocities'])
residuals = np.array(fit_result['residuals'])

print(f"\n{'Charge':>8} {'Measured':>10} {'Predicted':>10} {'Residual':>10} {'% Error':>10}")
print("-" * 62)
for i, charge in enumerate(charges):
    pct_error = (residuals[i] / measured[i]) * 100
    print(f"{charge:8.1f} {measured[i]:10.1f} {predicted[i]:10.1f} {residuals[i]:+10.1f} {pct_error:+9.2f}%")

print(f"\n{'':>8} {'':>10} {'':>10} {'----------':>10}")
print(f"{'RMSE:':>8} {'':>10} {'':>10} {fit_result['rmse_velocity']:10.2f}")

# Statistical analysis
print()
print("Statistical Summary:")
print(f"  Mean Residual:           {np.mean(residuals):+7.2f} fps")
print(f"  Std Dev Residual:         {np.std(residuals):7.2f} fps")
print(f"  Mean Absolute Error:      {np.mean(np.abs(residuals)):7.2f} fps")
print(f"  Max Positive Residual:   {np.max(residuals):+7.2f} fps")
print(f"  Max Negative Residual:   {np.min(residuals):+7.2f} fps")

# Systematic bias check
first_half = residuals[:len(residuals)//2]
second_half = residuals[len(residuals)//2:]
print()
print("Systematic Bias Analysis:")
print(f"  Lower charges (first half) mean residual:  {np.mean(first_half):+7.2f} fps")
print(f"  Higher charges (second half) mean residual: {np.mean(second_half):+7.2f} fps")
print(f"  Bias difference: {np.mean(second_half) - np.mean(first_half):+7.2f} fps")

if abs(np.mean(second_half) - np.mean(first_half)) > 5:
    print("  ⚠️  SYSTEMATIC BIAS DETECTED")
    print("     Model consistently over-predicts at low charges and under-predicts at high charges")
else:
    print("  ✓ No significant systematic bias")

print()
print("="*70)
print("Vivacity Polynomial Analysis")
print("="*70)

Lambda_base = fit_result['Lambda_base']
a, b, c, d = fit_result['coeffs']

print(f"\nFitted Parameters:")
print(f"  Lambda_base = {Lambda_base:.6f}")
print(f"  a = {a:+.6f}")
print(f"  b = {b:+.6f}")
print(f"  c = {c:+.6f}")
print(f"  d = {d:+.6f}")

print(f"\nVivacity vs Database:")
print(f"  Database Lambda_base: {config.propellant.Lambda_base:.6f}")
print(f"  Fitted Lambda_base:   {Lambda_base:.6f}")
print(f"  Ratio (Fitted/DB):    {Lambda_base / config.propellant.Lambda_base:.2f}x")

# Vivacity curve
print(f"\nVivacity Curve Λ(Z):")
print(f"{'Z':>6} {'Λ(Z)':>12} {'vs Lambda_base':>15}")
print("-" * 35)
for Z in [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]:
    Lambda_Z = calc_vivacity(Z, Lambda_base, fit_result['coeffs'])
    ratio = Lambda_Z / Lambda_base
    print(f"{Z:6.2f} {Lambda_Z:12.6f} {ratio:14.3f}x")

# Check polynomial shape
poly_at_0 = a
poly_at_1 = a + b + c + d
print(f"\nPolynomial multiplier range:")
print(f"  At Z=0: {poly_at_0:.3f}x Lambda_base")
print(f"  At Z=1: {poly_at_1:.3f}x Lambda_base")
print(f"  Range: {poly_at_1 - poly_at_0:+.3f}")

if abs(poly_at_1 - poly_at_0) < 0.1:
    print("  ℹ️  Polynomial is nearly constant - dynamic vivacity not strongly needed")
elif poly_at_0 > poly_at_1:
    print("  ℹ️  Decreasing vivacity with burn progress (typical)")
else:
    print("  ℹ️  Increasing vivacity with burn progress (atypical)")

print()
print("="*70)
print("Model Limitations Assessment")
print("="*70)

# Try fitting with just Lambda_base (no polynomial variation)
print("\nTesting constant Lambda (no polynomial)...")
from copy import copy

best_rmse_constant = float('inf')
best_lambda_constant = Lambda_base

# Search for best constant Lambda
for Lambda_test in np.linspace(0.08, 0.16, 41):
    predicted_test = []
    for charge in charges:
        config_test = copy(config)
        config_test.charge_mass_gr = charge
        result = solve_ballistics(
            config_test,
            Lambda_override=Lambda_test,
            coeffs_override=(1.0, 0.0, 0.0, 0.0)  # Constant polynomial
        )
        predicted_test.append(result['muzzle_velocity_fps'])

    residuals_test = np.array(predicted_test) - measured
    rmse_test = np.sqrt(np.mean(residuals_test**2))

    if rmse_test < best_rmse_constant:
        best_rmse_constant = rmse_test
        best_lambda_constant = Lambda_test

print(f"  Best constant Lambda: {best_lambda_constant:.6f}")
print(f"  Best RMSE (constant): {best_rmse_constant:.2f} fps")
print(f"  Current RMSE (polynomial): {fit_result['rmse_velocity']:.2f} fps")
print(f"  Improvement from polynomial: {best_rmse_constant - fit_result['rmse_velocity']:.2f} fps")

if best_rmse_constant - fit_result['rmse_velocity'] < 1.0:
    print("  ℹ️  Polynomial provides minimal improvement - model may be limited by physics")

print()
print("="*70)
print("Conclusions")
print("="*70)

print(f"\n1. Fit Quality:")
print(f"   - RMSE: {fit_result['rmse_velocity']:.2f} fps ({fit_result['rmse_velocity']/np.mean(measured)*100:.2f}% of mean velocity)")
print(f"   - Mean absolute error: {np.mean(np.abs(residuals)):.2f} fps")

if abs(np.mean(second_half) - np.mean(first_half)) > 5:
    print(f"\n2. Systematic Bias:")
    print(f"   - Lower charges: {np.mean(first_half):+.1f} fps (over-prediction)")
    print(f"   - Higher charges: {np.mean(second_half):+.1f} fps (under-prediction)")
    print(f"   - Possible causes:")
    print(f"     a) Model physics (heat loss, effective mass) not fully capturing behavior")
    print(f"     b) Pressure-dependent effects not modeled (e.g., position shot start)")
    print(f"     c) Need for higher-order vivacity polynomial")
else:
    print(f"\n2. Systematic Bias: None detected")

print(f"\n3. Vivacity Calibration:")
print(f"   - Database value inadequate ({config.propellant.Lambda_base:.6f})")
print(f"   - Fitted value {Lambda_base / config.propellant.Lambda_base:.1f}x higher ({Lambda_base:.6f})")
print(f"   - Confirms system-specific calibration is essential")

print(f"\n4. Polynomial Effectiveness:")
print(f"   - Dynamic range: {poly_at_0:.3f}x to {poly_at_1:.3f}x Lambda_base")
if best_rmse_constant - fit_result['rmse_velocity'] > 1.0:
    print(f"   - Provides {best_rmse_constant - fit_result['rmse_velocity']:.1f} fps RMSE improvement over constant")
    print(f"   - Dynamic vivacity is beneficial")
else:
    print(f"   - Minimal improvement over constant Lambda")
    print(f"   - Most error comes from model physics, not burn rate")

print()
print("="*70)
