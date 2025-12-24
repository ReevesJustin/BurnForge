"""Test enhanced fitting with physics parameters."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import numpy as np
from ballistics import load_grt_project, metadata_to_config, fit_vivacity_polynomial

# Load GRT file
grt_file = "65CRM_130SMK_N150_Starline_Initial.grtload"
metadata, load_data = load_grt_project(grt_file)

print("="*80)
print("ENHANCED FITTING TEST - Physics Parameters v3")
print("="*80)
print(f"\nCartridge: {metadata['cartridge']}")
print(f"Propellant: {metadata['propellant_name']}")
print(f"Temperature: {metadata['temperature_f']:.1f} °F")
print(f"Measurement points: {len(load_data)}")

# Create config
config = metadata_to_config(metadata)

print(f"\nInitial Physics Parameters:")
print(f"  covolume: {config.propellant.covolume_m3_per_kg:.6f} m³/kg")
print(f"  temp_sensitivity: {config.propellant.temp_sensitivity_sigma_per_K:.6f} /K")
print(f"  bore_friction: {config.bore_friction_psi:.0f} psi")
print(f"  start_pressure: {config.start_pressure_psi:.0f} psi")

print("\n" + "="*80)
print("TEST 1: Baseline (Lambda + polynomial only)")
print("="*80)

fit_baseline = fit_vivacity_polynomial(
    load_data, config,
    verbose=True,
    fit_temp_sensitivity=False,
    fit_bore_friction=False,
    fit_start_pressure=False,
    fit_covolume=False
)

print("\n" + "="*80)
print("TEST 2: With Temperature Sensitivity Fitting")
print("="*80)

fit_with_temp = fit_vivacity_polynomial(
    load_data, config,
    verbose=True,
    fit_temp_sensitivity=True,
    fit_bore_friction=False,
    fit_start_pressure=False,
    fit_covolume=False
)

print("\n" + "="*80)
print("TEST 3: With Bore Friction Fitting")
print("="*80)

fit_with_friction = fit_vivacity_polynomial(
    load_data, config,
    verbose=True,
    fit_temp_sensitivity=False,
    fit_bore_friction=True,
    fit_start_pressure=False,
    fit_covolume=False
)

print("\n" + "="*80)
print("TEST 4: With All Physics Parameters (except covolume)")
print("="*80)

fit_all_physics = fit_vivacity_polynomial(
    load_data, config,
    verbose=True,
    fit_temp_sensitivity=True,
    fit_bore_friction=True,
    fit_start_pressure=True,
    fit_covolume=False
)

print("\n" + "="*80)
print("RESULTS COMPARISON")
print("="*80)

print(f"\n{'Configuration':<40} {'RMSE':>10} {'Improvement':>12}")
print("-"*64)
print(f"{'Baseline (Lambda + poly only)':<40} {fit_baseline['rmse_velocity']:>10.2f} {'--':>12}")

delta_temp = fit_baseline['rmse_velocity'] - fit_with_temp['rmse_velocity']
print(f"{'+ Temperature sensitivity':<40} {fit_with_temp['rmse_velocity']:>10.2f} {delta_temp:>+11.2f}")

delta_fric = fit_baseline['rmse_velocity'] - fit_with_friction['rmse_velocity']
print(f"{'+ Bore friction':<40} {fit_with_friction['rmse_velocity']:>10.2f} {delta_fric:>+11.2f}")

delta_all = fit_baseline['rmse_velocity'] - fit_all_physics['rmse_velocity']
print(f"{'+ All physics parameters':<40} {fit_all_physics['rmse_velocity']:>10.2f} {delta_all:>+11.2f}")

print(f"\n{'Total improvement':<40} {'':>10} {delta_all:>+11.2f} fps")
print(f"{'Percent improvement':<40} {'':>10} {delta_all/fit_baseline['rmse_velocity']*100:>+11.1f}%")

print("\n" + "="*80)
print("FITTED PHYSICS PARAMETERS (All Physics Test)")
print("="*80)

if 'temp_sensitivity_sigma_per_K' in fit_all_physics:
    temp_sens_fitted = fit_all_physics['temp_sensitivity_sigma_per_K']
    temp_sens_fps_per_f = temp_sens_fitted * 5/9 * (metadata['temperature_f'] - 70)
    print(f"\nTemperature Sensitivity:")
    print(f"  Fitted sigma: {temp_sens_fitted:.6f} /K")
    print(f"  Equivalent: {temp_sens_fitted * 5/9:.6f} /°F")
    print(f"  Effect at {metadata['temperature_f']:.0f}°F: ~{temp_sens_fps_per_f:+.1f} fps")

if 'bore_friction_psi' in fit_all_physics:
    print(f"\nBore Friction:")
    print(f"  Fitted: {fit_all_physics['bore_friction_psi']:.1f} psi")
    print(f"  Initial: {config.bore_friction_psi:.0f} psi")

if 'start_pressure_psi' in fit_all_physics:
    print(f"\nShot-Start Pressure:")
    print(f"  Fitted: {fit_all_physics['start_pressure_psi']:.1f} psi")
    print(f"  Initial: {config.start_pressure_psi:.0f} psi")

print("\n" + "="*80)
print("RESIDUAL ANALYSIS (All Physics Fit)")
print("="*80)

charges = load_data['charge_grains'].values
measured = load_data['mean_velocity_fps'].values
predicted = np.array(fit_all_physics['predicted_velocities'])
residuals = np.array(fit_all_physics['residuals'])

print(f"\n{'Charge':>8} {'Measured':>10} {'Predicted':>10} {'Residual':>10} {'% Error':>10}")
print("-" * 62)
for i, charge in enumerate(charges):
    pct_error = (residuals[i] / measured[i]) * 100
    print(f"{charge:8.1f} {measured[i]:10.1f} {predicted[i]:10.1f} {residuals[i]:+10.1f} {pct_error:+9.2f}%")

# Systematic bias check
first_half = residuals[:len(residuals)//2]
second_half = residuals[len(residuals)//2:]

print(f"\nSystematic Bias Analysis:")
print(f"  Lower charges mean residual:  {np.mean(first_half):+7.2f} fps")
print(f"  Higher charges mean residual: {np.mean(second_half):+7.2f} fps")
print(f"  Bias difference: {np.mean(second_half) - np.mean(first_half):+7.2f} fps")

if abs(np.mean(second_half) - np.mean(first_half)) > 5:
    print(f"  ⚠️  SYSTEMATIC BIAS STILL PRESENT")
else:
    print(f"  ✓ No significant systematic bias")

print("\n" + "="*80)
print("SUMMARY")
print("="*80)

print(f"\nFitting physics parameters provided:")
print(f"  RMSE reduction: {delta_all:.2f} fps ({delta_all/fit_baseline['rmse_velocity']*100:.1f}%)")
print(f"  Final RMSE: {fit_all_physics['rmse_velocity']:.2f} fps")
print(f"  Mean absolute error: {np.mean(np.abs(residuals)):.2f} fps")

if fit_all_physics['rmse_velocity'] < 50:
    print(f"\n  ✓✓ EXCELLENT FIT - residuals within chronograph accuracy")
elif fit_all_physics['rmse_velocity'] < 100:
    print(f"\n  ✓ GOOD FIT - suitable for load development")
elif fit_all_physics['rmse_velocity'] < 200:
    print(f"\n  ~ ACCEPTABLE FIT - may need model refinement")
else:
    print(f"\n  ⚠️  POOR FIT - check data or model assumptions")

print("\n" + "="*80)
