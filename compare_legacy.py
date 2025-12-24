#!/usr/bin/env python3
import sys
import os

sys.path.insert(0, "src")
sys.path.insert(0, "archive")

import numpy as np
from scipy.optimize import minimize
from ballistics import load_grt_project
from solver import internal_ballistics_solver

# Load GRT data
metadata, load_data = load_grt_project(
    "data/grt_files/65CM_130SMK_N150_Starline_Initial.grtload"
)

print("Metadata:")
for k, v in metadata.items():
    print(f"  {k}: {v}")

measured = load_data["mean_velocity_fps"].values
charges = load_data["charge_grains"].values

print(f"\nNumber of charges: {len(charges)}")

# Common inputs for legacy solver
inputs = {
    "M_gr": metadata["bullet_mass_gr"],
    "D": metadata["caliber_in"],
    "V_C": metadata["case_volume_gr_h2o"],
    "barrel_length": metadata["barrel_length_in"],
    "case_length": metadata[
        "cartridge_overall_length_in"
    ],  # Assume COAL as case_length
    "powder_type": metadata["propellant_name"],
    "bullet_type": metadata["bullet_jacket_type"],
    "propellant_temp_F": metadata["temperature_f"],
}


# Function to run solver for all charges with given Lambda_base_override (as vivacity)
def run_solver_batch(Lambda_override=None, verbose=False):
    predicted = []
    for charge in charges:
        results = internal_ballistics_solver(
            M_gr=inputs["M_gr"],
            C_gr=charge,
            D=inputs["D"],
            V_C=inputs["V_C"],
            barrel_length=inputs["barrel_length"],
            case_length=inputs["case_length"],
            powder_type=inputs["powder_type"],
            bullet_type=inputs["bullet_type"],
            propellant_temp_F=inputs["propellant_temp_F"],
            Lambda_base_override=Lambda_override / 1450 if Lambda_override else None,
            verbose=verbose,
        )
        predicted.append(results["muzzle_velocity_fps"])
    return np.array(predicted)


# Base solver (database Lambda)
print("\n=== Base Solver (Database Lambda) ===")
predicted_base = run_solver_batch()
residuals_base = predicted_base - measured
rmse_base = np.sqrt(np.mean(residuals_base**2))
print(f"RMSE: {rmse_base:.2f} fps")
print(f"Mean residual: {np.mean(residuals_base):.2f} fps")

# Fit Lambda_base
print("\n=== Fitting Lambda_base ===")


def objective(vivacity):
    predicted = run_solver_batch(Lambda_override=vivacity)
    residuals = predicted - measured
    return np.sum(residuals**2)


# Initial guess: database vivacity, but from modern, Lambda_base=0.040828, so vivacity=0.040828*1450≈59.2
# But in legacy db, may differ.
# Use 79.0 as in fit_vivacity.py
initial_guess = 79.0
bounds = [(40, 150)]
result = minimize(
    objective, [initial_guess], bounds=bounds, method="L-BFGS-B", options={"ftol": 1e-6}
)
fitted_vivacity = result.x[0]
print(f"Fitted Vivacity: {fitted_vivacity:.1f} s^-1 per 100 bar")
print(f"Sum of squared errors: {result.fun:.2f}")

# Fitted predictions
predicted_fitted = run_solver_batch(Lambda_override=fitted_vivacity)
residuals_fitted = predicted_fitted - measured
rmse_fitted = np.sqrt(np.mean(residuals_fitted**2))
print(f"RMSE after fitting: {rmse_fitted:.2f} fps")
print(f"Mean residual: {np.mean(residuals_fitted):.2f} fps")

print("\n=== Residual Analysis ===")
print("Charge  Measured  Base Pred  Fitted Pred  Base Res  Fitted Res")
for i, charge in enumerate(charges):
    print(
        f"{charge:6.1f} {measured[i]:9.1f} {predicted_base[i]:10.1f} {predicted_fitted[i]:12.1f} {residuals_base[i]:9.1f} {residuals_fitted[i]:11.1f}"
    )
