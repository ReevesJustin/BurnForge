"""Diagnostic script for new physics parameters impact."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import numpy as np
from ballistics import load_grt_project, metadata_to_config
from ballistics.solver import solve_ballistics
from copy import copy

# Load GRT file
grt_file = "/home/justin/projects/IB_Solver/data/grt_files/65CM_130SMK_N150_Starline_Initial.grtload"
metadata, load_data = load_grt_project(grt_file)

# Create base config
config_base = metadata_to_config(metadata)

# Test single charge case
test_charge = load_data.iloc[0]
config = copy(config_base)
config.charge_mass_gr = test_charge['charge_grains']

print("="*80)
print("NEW PHYSICS PARAMETERS DIAGNOSTIC")
print("="*80)
print(f"\nCartridge: {metadata['cartridge']}")
print(f"Bullet: {metadata['bullet_mass_gr']:.1f} gr")
print(f"Propellant: {metadata['propellant_name']}")
print(f"Temperature: {metadata['temperature_f']:.1f} °F")
print(f"Test Charge: {test_charge['charge_grains']:.1f} gr")
print(f"Measured Velocity: {test_charge['mean_velocity_fps']:.1f} fps")

print("\n" + "="*80)
print("NEW PHYSICS PARAMETERS (from database)")
print("="*80)

print(f"\n1. PROPELLANT PROPERTIES:")
print(f"   covolume_m3_per_kg: {config.propellant.covolume_m3_per_kg:.6f} m³/kg")
print(f"   temp_sensitivity_sigma_per_K: {config.propellant.temp_sensitivity_sigma_per_K:.6f} /K")
print(f"   Lambda_base: {config.propellant.Lambda_base:.6f}")

print(f"\n2. BULLET PROPERTIES:")
print(f"   start_pressure_psi: {config.bullet.start_pressure_psi:.1f} psi")

print(f"\n3. BALLISTICS CONFIG:")
print(f"   bore_friction_psi: {config.bore_friction_psi:.1f} psi")
print(f"   start_pressure_psi: {config.start_pressure_psi:.1f} psi")

print("\n" + "="*80)
print("PARAMETER SENSITIVITY ANALYSIS")
print("="*80)

# Baseline with current settings
print("\nRunning baseline simulation...")
result_baseline = solve_ballistics(config)
v_baseline = result_baseline['muzzle_velocity_fps']
p_baseline = result_baseline['peak_pressure_psi']

print(f"\nBaseline Results:")
print(f"  Muzzle velocity: {v_baseline:.1f} fps (measured: {test_charge['mean_velocity_fps']:.1f} fps)")
print(f"  Error: {v_baseline - test_charge['mean_velocity_fps']:.1f} fps ({(v_baseline - test_charge['mean_velocity_fps'])/test_charge['mean_velocity_fps']*100:+.2f}%)")
print(f"  Peak pressure: {p_baseline:.0f} psi")
print(f"  Final Z: {result_baseline['final_Z']:.3f}")

# Test 1: Disable temperature sensitivity
print("\n" + "-"*80)
print("TEST 1: Temperature Sensitivity Impact")
print("-"*80)

config_test = copy(config)
# Temporarily override propellant to disable temperature sensitivity
from ballistics.props import PropellantProperties
prop_no_temp = PropellantProperties(
    name=config.propellant.name,
    vivacity=config.propellant.vivacity,
    base=config.propellant.base,
    force=config.propellant.force,
    temp_0=config.propellant.temp_0,
    gamma=config.propellant.gamma,
    bulk_density=config.propellant.bulk_density,
    Lambda_base=config.propellant.Lambda_base,
    poly_coeffs=config.propellant.poly_coeffs,
    covolume_m3_per_kg=config.propellant.covolume_m3_per_kg,
    temp_sensitivity_sigma_per_K=0.0  # DISABLE
)
config_test.propellant = prop_no_temp

result_no_temp = solve_ballistics(config_test)
v_no_temp = result_no_temp['muzzle_velocity_fps']
delta_temp = v_baseline - v_no_temp

print(f"\nWith temperature sensitivity disabled:")
print(f"  Muzzle velocity: {v_no_temp:.1f} fps")
print(f"  Change from baseline: {delta_temp:+.1f} fps")
print(f"  Temperature effect: {delta_temp:+.1f} fps for {metadata['temperature_f']-70:.1f}°F above 70°F")
print(f"  Sensitivity: {delta_temp / (metadata['temperature_f']-70):+.2f} fps/°F")

# Test 2: Disable bore friction
print("\n" + "-"*80)
print("TEST 2: Bore Friction Impact")
print("-"*80)

config_test = copy(config)
config_test.bore_friction_psi = 0.0  # DISABLE

result_no_friction = solve_ballistics(config_test)
v_no_friction = result_no_friction['muzzle_velocity_fps']
delta_friction = v_baseline - v_no_friction

print(f"\nWith bore friction = 0 psi (was {config.bore_friction_psi:.0f} psi):")
print(f"  Muzzle velocity: {v_no_friction:.1f} fps")
print(f"  Change from baseline: {delta_friction:+.1f} fps")
print(f"  Bore friction effect: {delta_friction:+.1f} fps")

# Test 3: Disable Noble-Abel (use ideal gas)
print("\n" + "-"*80)
print("TEST 3: Noble-Abel EOS (Covolume) Impact")
print("-"*80)

config_test = copy(config)
prop_no_covolume = PropellantProperties(
    name=config.propellant.name,
    vivacity=config.propellant.vivacity,
    base=config.propellant.base,
    force=config.propellant.force,
    temp_0=config.propellant.temp_0,
    gamma=config.propellant.gamma,
    bulk_density=config.propellant.bulk_density,
    Lambda_base=config.propellant.Lambda_base,
    poly_coeffs=config.propellant.poly_coeffs,
    covolume_m3_per_kg=0.0,  # DISABLE (ideal gas)
    temp_sensitivity_sigma_per_K=config.propellant.temp_sensitivity_sigma_per_K
)
config_test.propellant = prop_no_covolume

result_no_covolume = solve_ballistics(config_test)
v_no_covolume = result_no_covolume['muzzle_velocity_fps']
p_no_covolume = result_no_covolume['peak_pressure_psi']
delta_covolume = v_baseline - v_no_covolume

print(f"\nWith covolume = 0 (ideal gas, was {config.propellant.covolume_m3_per_kg:.6f} m³/kg):")
print(f"  Muzzle velocity: {v_no_covolume:.1f} fps")
print(f"  Peak pressure: {p_no_covolume:.0f} psi (was {p_baseline:.0f} psi)")
print(f"  Change from baseline: {delta_covolume:+.1f} fps")
print(f"  Covolume effect: {delta_covolume:+.1f} fps")

# Test 4: Vary shot-start pressure
print("\n" + "-"*80)
print("TEST 4: Shot-Start Pressure Impact")
print("-"*80)

print(f"\nCurrent shot-start pressure: {config.start_pressure_psi:.0f} psi")
print(f"\nTesting range of shot-start pressures:")
print(f"{'Pressure':>12} {'Velocity':>12} {'Delta':>12}")
print("-"*40)

for start_p in [1000, 2000, 3000, 3626, 4000, 5000, 6000]:
    config_test = copy(config)
    config_test.start_pressure_psi = start_p
    result_test = solve_ballistics(config_test)
    v_test = result_test['muzzle_velocity_fps']
    delta = v_test - v_baseline
    marker = " <-- current" if abs(start_p - config.start_pressure_psi) < 1 else ""
    print(f"{start_p:>12.0f} {v_test:>12.1f} {delta:>+12.1f}{marker}")

# Test 5: All new physics DISABLED
print("\n" + "-"*80)
print("TEST 5: ALL NEW PHYSICS DISABLED (Legacy Behavior)")
print("-"*80)

config_test = copy(config)
# Disable all new physics
prop_legacy = PropellantProperties(
    name=config.propellant.name,
    vivacity=config.propellant.vivacity,
    base=config.propellant.base,
    force=config.propellant.force,
    temp_0=config.propellant.temp_0,
    gamma=config.propellant.gamma,
    bulk_density=config.propellant.bulk_density,
    Lambda_base=config.propellant.Lambda_base,
    poly_coeffs=config.propellant.poly_coeffs,
    covolume_m3_per_kg=0.0,  # DISABLE Noble-Abel
    temp_sensitivity_sigma_per_K=0.0  # DISABLE temperature sensitivity
)
config_test.propellant = prop_legacy
config_test.bore_friction_psi = 0.0  # DISABLE bore friction
# Shot-start pressure stays as-is (was present before as Theta/A)

result_legacy = solve_ballistics(config_test)
v_legacy = result_legacy['muzzle_velocity_fps']
delta_total = v_baseline - v_legacy

print(f"\nWith ALL new physics disabled:")
print(f"  Muzzle velocity: {v_legacy:.1f} fps")
print(f"  Current (with new physics): {v_baseline:.1f} fps")
print(f"  Change from legacy: {delta_total:+.1f} fps")
print(f"  Measured velocity: {test_charge['mean_velocity_fps']:.1f} fps")
print(f"  Legacy error: {v_legacy - test_charge['mean_velocity_fps']:+.1f} fps ({(v_legacy - test_charge['mean_velocity_fps'])/test_charge['mean_velocity_fps']*100:+.2f}%)")
print(f"  Current error: {v_baseline - test_charge['mean_velocity_fps']:+.1f} fps ({(v_baseline - test_charge['mean_velocity_fps'])/test_charge['mean_velocity_fps']*100:+.2f}%)")

print("\n" + "="*80)
print("SUMMARY")
print("="*80)

print(f"\nNet impact of all new physics enhancements:")
print(f"  Temperature sensitivity: {delta_temp:+.1f} fps ({delta_temp/delta_total*100:+.1f}%)")
print(f"  Bore friction:           {delta_friction:+.1f} fps ({delta_friction/delta_total*100:+.1f}%)")
print(f"  Noble-Abel covolume:     {delta_covolume:+.1f} fps ({delta_covolume/delta_total*100:+.1f}%)")
print(f"  Total change:            {delta_total:+.1f} fps")

print(f"\nRecommendations:")
if abs(delta_total) > 50:
    print(f"  ⚠️  New physics changes velocity by {delta_total:+.1f} fps")
    print(f"  This affects fitting - default parameters may need adjustment")
    print(f"  Consider:")
    if abs(delta_temp) > 10:
        print(f"    - Reducing temp_sensitivity_sigma_per_K (currently {config.propellant.temp_sensitivity_sigma_per_K:.6f})")
    if abs(delta_friction) > 10:
        print(f"    - Reducing bore_friction_psi (currently {config.bore_friction_psi:.0f})")
    if abs(delta_covolume) > 10:
        print(f"    - Adjusting covolume_m3_per_kg (currently {config.propellant.covolume_m3_per_kg:.6f})")
else:
    print(f"  ✓ New physics has modest impact ({delta_total:+.1f} fps)")
    print(f"  Defaults are reasonable for this load")

print("\n" + "="*80)
