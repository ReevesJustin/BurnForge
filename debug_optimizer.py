#!/usr/bin/env python3
"""Debug optimizer behavior."""

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from ballistics import load_grt_project, metadata_to_config
from ballistics.core.solver import solve_ballistics
from copy import deepcopy

# Load test data
grt_file = "data/grt_files/65CM_130SMK_Varget_Starline.grtload"
metadata, load_data = load_grt_project(grt_file)
config_base = metadata_to_config(metadata)

print("Testing objective function manually...")
print(f"Data points: {len(load_data)}\n")

def simple_objective(params):
    """Simple objective function for testing."""
    Lambda_base, a, b, c, d = params

    residuals = []
    for _, row in load_data.iterrows():
        config = deepcopy(config_base)
        config.charge_mass_gr = row['charge_grains']

        # Update propellant params
        config.propellant.Lambda_base = Lambda_base
        config.propellant.poly_coeffs = (a, b, c, d)

        try:
            result = solve_ballistics(config)
            predicted = result['muzzle_velocity_fps']
            measured = row['mean_velocity_fps']
            residual = predicted - measured
            residuals.append(residual)
        except Exception as e:
            print(f"  Solver failed: {e}")
            return 1e10

    rmse = np.sqrt(np.mean(np.array(residuals)**2))
    return rmse

# Test with database params
print("Database params:")
params_db = [
    config_base.propellant.Lambda_base,
    *config_base.propellant.poly_coeffs
]
print(f"  Params: Lambda={params_db[0]:.6f}, coeffs={params_db[1:]}")
obj_db = simple_objective(params_db)
print(f"  RMSE: {obj_db:.2f} fps\n")

# Test with better initial guess
print("Better initial guess (lower Lambda):")
params_better = [0.01, 1.0, -0.5, 0.0, 0.0]
print(f"  Params: Lambda={params_better[0]:.6f}, coeffs={params_better[1:]}")
obj_better = simple_objective(params_better)
print(f"  RMSE: {obj_better:.2f} fps\n")

# Run actual optimization
print("Running optimization...")
initial_guess = params_better
bounds = [(0.001, 0.15), (-2, 2), (-2, 2), (-2, 2), (-2, 2)]

iteration_count = [0]

def objective_with_logging(params):
    obj_val = simple_objective(params)
    iteration_count[0] += 1
    if iteration_count[0] % 5 == 0 or iteration_count[0] == 1:
        print(f"  Iter {iteration_count[0]}: Lambda={params[0]:.6f}, RMSE={obj_val:.2f} fps")
    return obj_val

result = minimize(
    objective_with_logging,
    x0=initial_guess,
    method='L-BFGS-B',
    bounds=bounds,
    options={'maxiter': 100, 'ftol': 1e-3}
)

print(f"\nOptimization result:")
print(f"  Success: {result.success}")
print(f"  Message: {result.message}")
print(f"  Iterations: {result.nit if hasattr(result, 'nit') else 'N/A'}")
print(f"  Final Lambda: {result.x[0]:.6f}")
print(f"  Final coeffs: {result.x[1:]}")
print(f"  Final RMSE: {result.fun:.2f} fps")
