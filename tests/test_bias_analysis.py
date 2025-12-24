#!/usr/bin/env python3
"""Test current fitting and analyze bias patterns."""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from ballistics import load_grt_project, metadata_to_config, fit_vivacity_polynomial
from ballistics.core.solver import solve_ballistics

def analyze_fit_bias(grt_file):
    """Load data, fit, and analyze bias patterns."""

    print(f"\n{'='*70}")
    print(f"Analyzing: {grt_file}")
    print(f"{'='*70}\n")

    # Load data
    metadata, load_data = load_grt_project(grt_file)
    config = metadata_to_config(metadata)

    print(f"Propellant: {metadata['propellant_name']}")
    print(f"Barrel: {metadata['barrel_length_in']:.1f} in")
    print(f"Bullet: {metadata['bullet_mass_gr']:.1f} gr")
    print(f"Data points: {len(load_data)}\n")

    print("Load Data:")
    print(load_data[['charge_grains', 'mean_velocity_fps']].to_string(index=False))
    print()

    # Fit with current 4-parameter polynomial
    print("Fitting 4-parameter polynomial...")
    fit_result = fit_vivacity_polynomial(
        load_data,
        config,
        verbose=False,
        fit_temp_sensitivity=False,
        fit_bore_friction=False,
        fit_start_pressure=False,
    )

    print(f"\nFit Results:")
    print(f"  Lambda_base: {fit_result['Lambda_base']:.6f}")
    print(f"  Coefficients: {fit_result['coeffs']}")
    print(f"  RMSE: {fit_result['rmse_velocity']:.2f} fps")
    print(f"  Success: {fit_result['convergence']['success']}")

    # Analyze residuals
    residuals = np.array(fit_result['residuals'])
    charges = load_data['charge_grains'].values
    measured_vel = load_data['mean_velocity_fps'].values
    predicted_vel = np.array(fit_result['predicted_velocities'])

    # Compute bias metrics
    mean_residual = np.mean(residuals)
    max_charge = charges.max()
    min_charge = charges.min()

    # Low charge residuals (bottom 1/3)
    low_threshold = min_charge + (max_charge - min_charge) / 3
    low_mask = charges <= low_threshold
    low_residuals = residuals[low_mask]
    low_bias = np.mean(low_residuals) if len(low_residuals) > 0 else 0

    # High charge residuals (top 1/3)
    high_threshold = max_charge - (max_charge - min_charge) / 3
    high_mask = charges >= high_threshold
    high_residuals = residuals[high_mask]
    high_bias = np.mean(high_residuals) if len(high_residuals) > 0 else 0

    print(f"\nBias Analysis:")
    print(f"  Mean residual: {mean_residual:.2f} fps")
    print(f"  Low charge bias ({charges[low_mask].min():.1f}-{charges[low_mask].max():.1f} gr): {low_bias:.2f} fps")
    print(f"  High charge bias ({charges[high_mask].min():.1f}-{charges[high_mask].max():.1f} gr): {high_bias:.2f} fps")
    print(f"  Low-High delta: {low_bias - high_bias:.2f} fps")

    # Check for systematic bias
    if abs(low_bias - high_bias) > 30:
        print(f"  ⚠️  SYSTEMATIC BIAS DETECTED (>{30} fps difference)")

    # Detailed residual breakdown
    print(f"\nDetailed Residuals:")
    for i, (charge, meas, pred, res) in enumerate(zip(charges, measured_vel, predicted_vel, residuals)):
        print(f"  {charge:5.1f} gr: measured={meas:4.0f} fps, predicted={pred:4.0f} fps, residual={res:+6.1f} fps")

    return {
        'grt_file': grt_file,
        'rmse': fit_result['rmse_velocity'],
        'mean_residual': mean_residual,
        'low_bias': low_bias,
        'high_bias': high_bias,
        'bias_delta': low_bias - high_bias,
        'charges': charges,
        'residuals': residuals,
        'fit_result': fit_result,
        'load_data': load_data
    }

if __name__ == "__main__":
    # Test both GRT files
    grt_files = [
        "data/grt_files/65CM_130SMK_Varget_Starline.grtload",
        "data/grt_files/65CM_130SMK_N150_Starline.grtload",
    ]

    results = []
    for grt_file in grt_files:
        try:
            result = analyze_fit_bias(grt_file)
            results.append(result)
        except Exception as e:
            print(f"Error with {grt_file}: {e}")
            import traceback
            traceback.print_exc()

    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}\n")

    for r in results:
        print(f"{r['grt_file'].split('/')[-1]}:")
        print(f"  RMSE: {r['rmse']:.2f} fps")
        print(f"  Bias delta (low-high): {r['bias_delta']:.2f} fps")
        print()
