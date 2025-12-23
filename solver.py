#!/usr/bin/env python3
# Lumped Parameter Internal Ballistics Solver with Propellant-Specific Vivacity Polynomials

import math
import sys
import sqlite3

# Constants
GRAINS_TO_LB = 1 / 7000
GRAINS_H2O_TO_IN3 = 1 / 252.9
G = 386.4
PRESSURE_THRESHOLD = 62000
PROPELLANT_DENSITY = 0.0584

def load_properties_from_db(powder_type, bullet_type, db_path="ballistics_data.db"):
    """Load propellant and bullet properties from SQLite database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # Ensure powder_type is a string
    powder_type = str(powder_type)
    cursor.execute("""
        SELECT vivacity, base, force, temp_0, temp_coeff_v, temp_coeff_p, bulk_density, 
               poly_a, poly_b, poly_c, poly_d 
        FROM propellants WHERE name = ?
    """, (powder_type,))
    prop_data = cursor.fetchone()
    if not prop_data:
        raise ValueError(f"Propellant '{powder_type}' not found in database.")
    vivacity, base, F, T_0, temp_coeff_v, temp_coeff_p, bulk_density, poly_a, poly_b, poly_c, poly_d = prop_data
    gamma = 1.24 if base == "S" else 1.22
    Lambda_base = vivacity / 1450
    density = bulk_density if bulk_density is not None else PROPELLANT_DENSITY
    poly_coeffs = (poly_a, poly_b, poly_c, poly_d)
    cursor.execute("SELECT s, rho_p FROM bullet_types WHERE name = ?", (bullet_type,))
    bullet_data = cursor.fetchone()
    if not bullet_data:
        raise ValueError(f"Bullet type '{bullet_type}' not found in database.")
    s, rho_p = bullet_data
    conn.close()
    return gamma, F, Lambda_base, T_0, s, rho_p, temp_coeff_v, temp_coeff_p, density, poly_coeffs

def calc_lambda_z(z, lambda_base, poly_coeffs):
    """Calculate dynamic vivacity, using original model for default coefficients."""
    a, b, c, d = poly_coeffs
    if z < 0 or z > 1:
        z = max(0.0, min(1.0, z))
    # Use original polynomial for default coefficients (1, -1, 0, 0)
    if a == 1.0 and b == -1.0 and c == 0.0 and d == 0.0:
        if z < 0.6:
            return lambda_base * (1.0 + 0.294 * z - 0.131 * z**2 - 0.278 * z**3)
        elif z < 1.0:
            return lambda_base * (-0.544 + 4.83 * z - 2.57 * z**2 - 1.67 * z**3)
        return 0.0
    # Use custom polynomial for fitted coefficients
    if z < 1.0:
        return lambda_base * (a + b * z + c * z**2 + d * z**3)
    return 0.0

def internal_ballistics_solver(M_gr, C_gr, D, V_C, barrel_length, case_length, powder_type, bullet_type, 
                              propellant_temp_F=70, Phi=0.9, P_IN=5000, calibrate_mv=None, 
                              Lambda_base_override=None, poly_coeffs_override=None, verbose=True):
    """Solve internal ballistics with optional vivacity overrides for fitting."""
    if M_gr <= 0 or C_gr <= 0 or D <= 0 or V_C <= 0 or barrel_length <= 0 or case_length < 0 or barrel_length <= case_length:
        raise ValueError("Invalid input values.")
    m = M_gr * GRAINS_TO_LB
    C = C_gr * GRAINS_TO_LB
    A = math.pi * (D / 2)**2
    V_C = V_C * GRAINS_H2O_TO_IN3
    V_0 = V_C - (C / PROPELLANT_DENSITY)
    if V_0 <= 0:
        raise ValueError(f"Initial volume V_0 = {V_0:.3f} in^3 is non-positive.")
    L_eff = barrel_length - case_length
    T_1 = (propellant_temp_F - 32) * 5 / 9 + 273.15

    gamma, F, Lambda_base, T_0, s, rho_p, temp_coeff_v, temp_coeff_p, density, poly_coeffs = load_properties_from_db(powder_type, bullet_type)
    Lambda_initial = Lambda_base_override if Lambda_base_override is not None else Lambda_base
    poly_coeffs_used = poly_coeffs_override if poly_coeffs_override is not None else poly_coeffs

    def run_solver(Lambda):
        Theta = 2.5 * (m * s) / (D * rho_p)
        shot_start_pressure = Theta / A
        time, Z, pressure, velocity, distance = 0.0, 0.0, P_IN, 0.0, 0.0
        peak_pressure = P_IN
        P_prev, P_prev2 = 0.0, 0.0
        v_prev, v_prev2 = 0.0, 0.0
        m_eff = m
        delta_t = 1e-6
        max_iterations = 10**6
        iteration = 0
        distance_max_pressure = 0.0
        distance_burnout = None
        muzzle_pressure = P_IN
        P_const = None
        volume_prev = V_0
        distance_prev = 0.0

        while distance < L_eff and iteration < max_iterations:
            P_integral = (23 * pressure - 16 * P_prev + 5 * P_prev2) * delta_t / 12
            Lambda_Z = calc_lambda_z(Z, Lambda, poly_coeffs_used)
            Z += Lambda_Z * P_integral
            if Z >= 1.0:
                Z = 1.0
                if distance_burnout is None:
                    distance_burnout = distance
                    P_const = pressure * (volume_prev ** gamma)
            m_eff = m + (C * Z / 3)
            if pressure > shot_start_pressure:
                accel_term = (A * Phi * P_integral - Theta * delta_t)
                velocity += (G / m_eff) * accel_term
                V_integral = (5 * velocity + 8 * v_prev - v_prev2) * delta_t / 12
                distance += V_integral
                if distance >= L_eff:
                    muzzle_pressure = pressure
                    break
            E_h_base = (0.38 * (T_0 - T_1) * D**1.5) / (1 + 0.6 * (D**2.175 / C**0.8375)) * 12
            E_h = E_h_base * Z
            kinetic_energy = (m_eff * velocity**2) / (2 * G)
            energy_loss = (gamma - 1) * (kinetic_energy + E_h + Theta * distance)
            volume = V_0 + A * distance
            if Z >= 1.0 and P_const is not None:
                pressure = P_const / (volume ** gamma)
            else:
                pressure = max(0, (C * Z * F - energy_loss) / volume) if volume > 0 else 0
            if pressure > peak_pressure:
                peak_pressure = float(pressure)
                distance_max_pressure = distance
            P_prev2, P_prev = P_prev, pressure
            v_prev2, v_prev = v_prev, velocity
            time += delta_t
            distance_prev = distance
            volume_prev = volume
            iteration += 1

        if iteration >= max_iterations and verbose:
            print(f"!WARNING! Max iterations reached. Final distance: {distance:.3f} in vs. {L_eff:.3f} in")
            if distance < 0.9 * L_eff:
                print("Simulation stopped prematurely; results may be unreliable.")
            muzzle_pressure = pressure
        if peak_pressure > PRESSURE_THRESHOLD and verbose:
            print(f"!WARNING! Peak pressure {float(peak_pressure):.0f} PSI exceeds {PRESSURE_THRESHOLD} PSI")
        muzzle_velocity_fps = velocity / 12
        return muzzle_velocity_fps, peak_pressure, Z, distance_burnout if distance_burnout is not None else float('inf'), time, distance_max_pressure, muzzle_pressure

    if calibrate_mv is not None and verbose:
        print(f"Calibrating vivacity to match muzzle velocity: {calibrate_mv} ft/s")
        lambda_min = Lambda_initial * 0.5
        lambda_max = Lambda_initial * 2.0
        tolerance = 1.0
        max_attempts = 20
        attempt = 0
        while attempt < max_attempts:
            Lambda = (lambda_min + lambda_max) / 2
            mv, peak_p, Z, burnout_dist, time, d_max_p, muzzle_p = run_solver(Lambda)
            if abs(mv - calibrate_mv) < tolerance:
                break
            elif mv < calibrate_mv:
                lambda_min = Lambda
            else:
                lambda_max = Lambda
            attempt += 1
        if attempt >= max_attempts and verbose:
            print("Calibration failed to converge.")
    else:
        if verbose:
            print("No calibration requested or data unavailable; using base vivacity.")
        Lambda = Lambda_initial
        mv, peak_p, Z, burnout_dist, time, d_max_p, muzzle_p = run_solver(Lambda)

    results = {
        "M_gr": M_gr, "C_gr": C_gr, "D": D, "V_C": V_C, "barrel_length": barrel_length, "case_length": case_length,
        "powder_type": powder_type, "bullet_type": bullet_type, "propellant_temp_F": propellant_temp_F,
        "vivacity_base": Lambda_base * 1450, "vivacity": Lambda * 1450, "muzzle_velocity_fps": mv,
        "muzzle_pressure_psi": muzzle_p, "peak_pressure_psi": peak_p, "distance_max_pressure_in": d_max_p,
        "distance_burnout_in": burnout_dist if burnout_dist < L_eff else "Not reached", "final_burn_fraction": Z,
        "total_time_s": time
    }

    if verbose:
        print(f"Vivacity (Base): {results['vivacity_base']:.1f} s^-1 per 100 bar")
        print(f"Vivacity (Corrected): {results['vivacity']:.1f} s^-1 per 100 bar")
        print(f"Muzzle Velocity: {results['muzzle_velocity_fps']:.1f} ft/s")
        print(f"Muzzle Pressure: {results['muzzle_pressure_psi']:.0f} PSI")
        print(f"Peak Pressure: {results['peak_pressure_psi']:.0f} PSI")
        print(f"Distance to Max Pressure: {results['distance_max_pressure_in']:.3f} in")
        print(f"Distance to Burnout: {results['distance_burnout_in']}")
        print(f"Final Burn Fraction (Z): {results['final_burn_fraction']:.3f}")
        print(f"Total Time: {results['total_time_s']:.6f} s")

        if len(sys.argv) > 2:
            with open(sys.argv[2], "w") as f:
                for key, value in results.items():
                    f.write(f"{key}={value}\n")
            print(f"Results saved to '{sys.argv[2]}'")

    return results

def read_input_file(filename):
    """Read input parameters from a file."""
    inputs = {}
    with open(filename, "r") as f:
        for line in f:
            key, value = line.strip().split("=")
            # Preserve powder_type as a string, convert other fields to float if possible
            if key == "powder_type":
                inputs[key] = value
            else:
                try:
                    inputs[key] = float(value)
                except ValueError:
                    inputs[key] = value
    return inputs

if __name__ == "__main__":
    default_inputs = {
        "M_gr": 175, "C_gr": 42, "D": 0.308, "V_C": 47.4, "barrel_length": 16.625, "case_length": 2.010,
        "powder_type": "N140", "bullet_type": "Copper Jacket over Lead", "propellant_temp_F": 36
    }
    if len(sys.argv) > 1:
        try:
            inputs = read_input_file(sys.argv[1])
            print(f"Loaded inputs from '{sys.argv[1]}'")
        except FileNotFoundError:
            print(f"Error: Input file '{sys.argv[1]}' not found. Using defaults.")
            inputs = default_inputs
    else:
        inputs = default_inputs
    calibrate_mv = inputs.get("calibrate_mv", None)
    results = internal_ballistics_solver(
        inputs["M_gr"], inputs["C_gr"], inputs["D"], inputs["V_C"],
        inputs["barrel_length"], inputs["case_length"],
        inputs["powder_type"], inputs["bullet_type"],
        inputs["propellant_temp_F"], calibrate_mv=calibrate_mv
    )