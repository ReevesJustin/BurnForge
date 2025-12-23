"""Analyze fitting accuracy for GRT file."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import numpy as np
import matplotlib.pyplot as plt
from ballistics import load_grt_project, metadata_to_config, fit_vivacity_polynomial
from ballistics.solver import solve_ballistics
from ballistics.burn_rate import calc_vivacity, form_function

# Load GRT file
grt_file = (
    sys.argv[1]
    if len(sys.argv) > 1
    else "data/grt_files/65CM_130SMK_N150_Starline_Initial.grtload"
)
metadata, load_data = load_grt_project(grt_file)

print("=" * 60)
print("GRT File Analysis")
print("=" * 60)
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

# Increase heat loss to address under-prediction
config.h_base = 5000.0

print("=" * 60)
print("Fitting Vivacity Polynomial (h_base=3000, with bore friction)")
print("=" * 60)

# Fit with verbose output, using hybrid geometric + pressure-dependent + temperature-sensitive model
# Force initial alpha positive to enable pressure correction
initial_guess = [
    0.040828,
    0.01,
    0.002,
    0.01,
    4000.0,
    0.001,
]  # Lambda_base, alpha, sigma, bore_fric, h_base, covolume
fit_result = fit_vivacity_polynomial(
    load_data,
    config,
    initial_guess=initial_guess,
    verbose=False,
    use_form_function=True,
    fit_temp_sensitivity=True,
    fit_bore_friction=True,
    fit_h_base=True,
    fit_covolume=True,
)

print()
print("=" * 60)
print("Residual Analysis")
print("=" * 60)

# Detailed residual analysis
charges = load_data["charge_grains"].values
measured = load_data["mean_velocity_fps"].values
predicted = np.array(fit_result["predicted_velocities"])
residuals = np.array(fit_result["residuals"])

print(
    f"{'Charge':>8} {'Measured':>10} {'Predicted':>10} {'Residual':>10} {'% Error':>10}"
)
print("-" * 60)
for i, charge in enumerate(charges):
    pct_error = (residuals[i] / measured[i]) * 100
    print(
        f"{charge:8.1f} {measured[i]:10.1f} {predicted[i]:10.1f} {residuals[i]:10.1f} {pct_error:9.2f}%"
    )

print()
print(f"RMSE: {fit_result['rmse_velocity']:.2f} fps")
print(f"Mean Residual: {np.mean(residuals):.2f} fps")
print(f"Std Residual: {np.std(residuals):.2f} fps")
print(f"Max Positive Residual: {np.max(residuals):.2f} fps")
print(f"Max Negative Residual: {np.min(residuals):.2f} fps")

# Check for systematic bias
print()
print("Systematic Bias Check:")
first_half_mean = np.mean(residuals[: len(residuals) // 2])
second_half_mean = np.mean(residuals[len(residuals) // 2 :])
print(f"  First half mean residual: {first_half_mean:.2f} fps")
print(f"  Second half mean residual: {second_half_mean:.2f} fps")
if abs(second_half_mean - first_half_mean) > 5:
    print(
        f"  WARNING: Systematic bias detected ({second_half_mean - first_half_mean:.2f} fps difference)"
    )

print()
print("=" * 60)
print("Hybrid Burn Rate Model Analysis")
print("=" * 60)

Lambda_base = fit_result["Lambda_base"]
alpha = fit_result.get("alpha", 0.0)
sigma = fit_result.get("temp_sensitivity_sigma_per_K", 0.0)
coeffs = (0.0, 0.0, 0.0, 0.0)  # dummy for compatibility

print(f"Lambda_base: {Lambda_base:.6f}")
print(f"Alpha (pressure correction): {alpha:.6f}")
print(f"Sigma (temperature sensitivity): {sigma:.6f}")
print(f"Grain geometry: {config.propellant.grain_geometry}")
print()

# Evaluate vivacity at different burn fractions (at reference pressure p=0 for simplicity)
Z_vals = np.linspace(0, 1, 11)
print(f"{'Z':>6} {'Λ(Z,p=0)':>12} {'π(Z)':>12}")
print("-" * 35)
for Z in Z_vals:
    Lambda_Z = calc_vivacity(
        Z,
        Lambda_base,
        coeffs,
        use_form_function=True,
        geometry=config.propellant.grain_geometry,
        p_psi=0.0,  # reference pressure
        alpha=alpha,
    )
    pi_z = form_function(Z, config.propellant.grain_geometry)
    print(f"{Z:6.2f} {Lambda_Z:12.6f} {pi_z:12.6f}")

# Check for database comparison
print()
print("=" * 60)
print("Database Comparison")
print("=" * 60)
print(f"Database Lambda_base: {config.propellant.Lambda_base:.6f}")
print(f"Fitted Lambda_base: {Lambda_base:.6f}")
print(f"Ratio (Fitted/Database): {Lambda_base / config.propellant.Lambda_base:.2f}x")

print()
print("=" * 60)
print("Optimization Investigation")
print("=" * 60)

# Try different optimization approaches
print("\nTrying alternative optimization methods...")

# Optimization investigation commented out due to errors

print()
print("=" * 60)
print("Model Limitation Analysis")
print("=" * 60)

# Check if model can theoretically achieve better fit
# by testing if residuals can be reduced with manual parameter tweaks

print("\nTesting if model structure is limiting fit quality...")
print("(Trying Lambda_base adjustments to see if RMSE improves)")

lambda_test_vals = np.linspace(0.08, 0.16, 3)
rmse_vals = []

for Lambda_test in lambda_test_vals:
    predicted_test = []
    for charge in charges:
        config_test = metadata_to_config(metadata)
        config_test.charge_mass_gr = charge
        result = solve_ballistics(
            config_test,
            Lambda_override=Lambda_test,
            coeffs_override=(1.0, 0.0, 0.0, 0.0),
        )
        predicted_test.append(result["muzzle_velocity_fps"])

    residuals_test = np.array(predicted_test) - measured
    rmse_test = np.sqrt(np.mean(residuals_test**2))
    rmse_vals.append(rmse_test)
    if Lambda_test == Lambda_base:
        print(f"  Lambda = {Lambda_test:.4f}: RMSE = {rmse_test:.2f} fps (current fit)")
    else:
        print(
            f"  Lambda = {Lambda_test:.4f}: RMSE = {rmse_test:.4f}: RMSE = {rmse_test:.2f} fps"
        )

best_lambda_idx = np.argmin(rmse_vals)
print(
    f"\nBest single Lambda (constant with geometry): {lambda_test_vals[best_lambda_idx]:.4f}"
)
print(
    f"Best RMSE achievable with constant Lambda: {rmse_vals[best_lambda_idx]:.2f} fps"
)

print("\n" + "=" * 60)
print("Summary")
print("=" * 60)
print(f"Current fit RMSE: {fit_result['rmse_velocity']:.2f} fps")
print(f"Mean absolute error: {np.mean(np.abs(residuals)):.2f} fps")
print(f"Max absolute error: {np.max(np.abs(residuals)):.2f} fps")
print(
    f"\nSystematic bias: {'Yes' if abs(second_half_mean - first_half_mean) > 5 else 'No'}"
)
if abs(second_half_mean - first_half_mean) > 5:
    print(f"  Lower charges: {first_half_mean:+.2f} fps average residual")
    print(f"  Higher charges: {second_half_mean:+.2f} fps average residual")
    print(f"  Suggests model may need additional terms or physics")

print("\n" + "=" * 60)
print("Burnout Position Diagnostics")
print("=" * 60)
print("Charge   Burnout Distance (in)   Final Burn %")
print("---------------------------------------------")
for idx, row in load_data.iterrows():
    config_sim = metadata_to_config(metadata)
    config_sim.charge_mass_gr = float(row["charge_grains"])
    # Apply fitted parameters
    config_sim.propellant.Lambda_base = fit_result["Lambda_base"]
    if "alpha" in fit_result:
        config_sim.propellant.alpha = fit_result["alpha"]
    config_sim.propellant.poly_coeffs = fit_result["coeffs"]
    if "temp_sensitivity_sigma_per_K" in fit_result:
        config_sim.propellant.temp_sensitivity_sigma_per_K = fit_result[
            "temp_sensitivity_sigma_per_K"
        ]
    if "bore_friction_psi" in fit_result:
        config_sim.bore_friction_psi = fit_result["bore_friction_psi"]
    if "h_base" in fit_result:
        config_sim.h_base = fit_result["h_base"]
    if "covolume_m3_per_kg" in fit_result:
        config_sim.propellant.covolume_m3_per_kg = fit_result["covolume_m3_per_kg"]

    try:
        results = solve_ballistics(config_sim)
        burnout_dist = results["burnout_distance_in"]
        final_burn = results["final_burn_percent"]
        print(f"{row['charge_grains']:6.1f} {burnout_dist:12.2f} {final_burn:12.1f}")
    except:
        print(f"{row['charge_grains']:6.1f} {'N/A':>12} {'N/A':>12}")

print("\n" + "=" * 60)
