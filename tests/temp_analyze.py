import sys

sys.path.insert(0, "src")

import numpy as np
from ballistics.io.io import load_grt_project, metadata_to_config
from ballistics.fitting.fitting import fit_vivacity_polynomial

grt_file = "data/grt_files/65CM_130SMK_N150_Starline_Initial.grtload"

metadata, load_data = load_grt_project(grt_file)

print("=" * 60)
print("GRT File Analysis")
print("=" * 60)
print(f"Cartridge: {metadata['cartridge']}")
print(f"Propellant: {metadata['propellant_name']}")

config = metadata_to_config(metadata)

fit_result = fit_vivacity_polynomial(
    load_data,
    config,
    fit_h_base=True,
    fit_bore_friction=True,
    fit_start_pressure=True,
    verbose=False,
)

charges = load_data["charge_grains"].values
measured = load_data["mean_velocity_fps"].values
predicted = np.array(fit_result["predicted_velocities"])
residuals = np.array(fit_result["residuals"])

print(f"RMSE: {fit_result['rmse_velocity']:.2f} fps")
print(f"Mean Residual: {np.mean(residuals):.2f} fps")
print(f"Std Residual: {np.std(residuals):.2f} fps")

# Systematic bias
first_half_mean = np.mean(residuals[: len(residuals) // 2])
second_half_mean = np.mean(residuals[len(residuals) // 2 :])
if abs(second_half_mean - first_half_mean) > 5:
    print(
        f"Systematic bias: Yes ({second_half_mean - first_half_mean:.2f} fps difference)"
    )
else:
    print("Systematic bias: No")

Lambda_base = fit_result["Lambda_base"]
coeffs = fit_result["coeffs"]
a, b, c, d = coeffs

print(f"Lambda_base: {Lambda_base:.6f}")
print(f"Coefficients: a={a:.6f}, b={b:.6f}, c={c:.6f}, d={d:.6f}")

# Curve shape
if b < 0:
    print("Curve shape: degressive")
else:
    print("Curve shape: progressive")
