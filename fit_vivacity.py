#!/usr/bin/env python3
# Script to fit base vivacity for a propellant using load data for multiple bullet weights in different cartridges

from scipy.optimize import minimize
import sys
import numpy as np
from solver import internal_ballistics_solver

def run_solver_with_params(Lambda_base, inputs_list, targets, iteration=None, debug=False):
    """Run solver with overridden Lambda_base and default polynomial."""
    Lambda_base = Lambda_base.item() if isinstance(Lambda_base, (np.ndarray, np.generic)) else Lambda_base
    poly_coeffs = (1.0, -1.0, 0.0, 0.0)  # Default coefficients for original polynomial
    errors = []
    for idx, (inputs, (target_mv, target_p)) in enumerate(zip(inputs_list, targets)):
        results = internal_ballistics_solver(
            inputs["M_gr"], inputs["C_gr"], inputs["D"], inputs["V_C"],
            inputs["barrel_length"], inputs["case_length"],
            inputs["powder_type"], inputs["bullet_type"],
            inputs["propellant_temp_F"],
            Lambda_base_override=Lambda_base / 1450,
            poly_coeffs_override=poly_coeffs,
            verbose=debug
        )
        mv_error = ((results["muzzle_velocity_fps"] - target_mv) / 2500) ** 2
        p_error = ((results["peak_pressure_psi"] - target_p) / 60000) ** 2
        errors.append(0.1 * mv_error + 0.2 * p_error)  # Increased P weight
        if debug:
            print(f"Run {idx+1}: Bullet={inputs['M_gr']} gr, Charge={inputs['C_gr']} gr, "
                  f"MV={results['muzzle_velocity_fps']:.1f} ft/s (Target={target_mv}), "
                  f"P={results['peak_pressure_psi']:.0f} PSI (Target={target_p})")
    total_error = sum(errors)
    if iteration is not None and iteration[0] % 100 == 0:
        print(f"Iteration {iteration[0]}: Total Error={total_error:.2f}, Lambda_base={Lambda_base:.1f}")
    return total_error

def fit_vivacity(inputs_list, targets, initial_guess=79.0):
    """Fit only Lambda_base, using the default vivacity polynomial."""
    bounds = [(40, 150)]  # Widened bounds
    iteration = [0]
    def callback(xk):
        iteration[0] += 1
    def objective(Lambda_base):
        return run_solver_with_params(Lambda_base, inputs_list, targets, iteration, debug=False)
    
    result = minimize(
        objective, [initial_guess], 
        bounds=bounds, method='L-BFGS-B',
        options={'ftol': 1e-6, 'maxiter': 500},
        callback=callback
    )
    Lambda_base = result.x[0]
    print(f"Optimized: Lambda_base={Lambda_base:.1f} s^-1 per 100 bar")
    print(f"Sum of squared errors: {result.fun:.2f}")
    
    # Run solver one final time with debug=True to show final fit
    print("\nFinal fit results:")
    run_solver_with_params(Lambda_base, inputs_list, targets, debug=True)
    return Lambda_base

if __name__ == "__main__":
    # .308 Winchester: 175-grain and 150-grain
    print("Fitting for .308 Winchester (175-grain and 150-grain):")
    inputs_308 = [
        # 175-grain SMK
        {"M_gr": 175, "C_gr": 38.8, "D": 0.308, "V_C": 49.47, "barrel_length": 24, "case_length": 2.010, 
         "powder_type": "A2495", "bullet_type": "Copper Jacket over Lead", "propellant_temp_F": 70},
        {"M_gr": 175, "C_gr": 43.1, "D": 0.308, "V_C": 49.47, "barrel_length": 24, "case_length": 2.010, 
         "powder_type": "A2495", "bullet_type": "Copper Jacket over Lead", "propellant_temp_F": 70},
        # 150-grain Hornady FMJ-BT
        {"M_gr": 150, "C_gr": 41.0, "D": 0.308, "V_C": 50.0, "barrel_length": 24, "case_length": 2.010, 
         "powder_type": "A2495", "bullet_type": "Copper Jacket over Lead", "propellant_temp_F": 70},
        {"M_gr": 150, "C_gr": 46.6, "D": 0.308, "V_C": 50.0, "barrel_length": 24, "case_length": 2.010, 
         "powder_type": "A2495", "bullet_type": "Copper Jacket over Lead", "propellant_temp_F": 70}
    ]
    targets_308 = [
        (2440, 55100),  # 175-grain, 38.8 gr
        (2668, 61200),  # 175-grain, 43.1 gr
        (2428, 41100),  # 150-grain, 41.0 gr
        (2750, 54500)   # 150-grain, 46.6 gr
    ]
    Lambda_base_308 = fit_vivacity(inputs_308, targets_308)
    print(f".308 Winchester Optimized Lambda_base: {Lambda_base_308:.1f} s^-1 per 100 bar")

    # .223 Remington: 77-grain and 55-grain
    print("\nFitting for .223 Remington (77-grain and 55-grain):")
    inputs_223 = [
        # 77-grain Sierra HPBT MatchKing
        {"M_gr": 77, "C_gr": 20.0, "D": 0.224, "V_C": 28.0, "barrel_length": 24, "case_length": 1.760, 
         "powder_type": "A2495", "bullet_type": "Copper Jacket over Lead", "propellant_temp_F": 70},
        {"M_gr": 77, "C_gr": 22.5, "D": 0.224, "V_C": 28.0, "barrel_length": 24, "case_length": 1.760, 
         "powder_type": "A2495", "bullet_type": "Copper Jacket over Lead", "propellant_temp_F": 70},
        # 55-grain Nosler BT
        {"M_gr": 55, "C_gr": 22.5, "D": 0.224, "V_C": 28.5, "barrel_length": 24, "case_length": 1.760, 
         "powder_type": "A2495", "bullet_type": "Copper Jacket over Lead", "propellant_temp_F": 70},
        {"M_gr": 55, "C_gr": 25.0, "D": 0.224, "V_C": 28.5, "barrel_length": 24, "case_length": 1.760, 
         "powder_type": "A2495", "bullet_type": "Copper Jacket over Lead", "propellant_temp_F": 70}
    ]
    targets_223 = [
        (2450, 43200),  # 77-grain, 20.0 gr
        (2700, 53500),  # 77-grain, 22.5 gr
        (2800, 41100),  # 55-grain, 22.5 gr
        (3050, 50200)   # 55-grain, 25.0 gr
    ]
    Lambda_base_223 = fit_vivacity(inputs_223, targets_223)
    print(f".223 Remington Optimized Lambda_base: {Lambda_base_223:.1f} s^-1 per 100 bar")