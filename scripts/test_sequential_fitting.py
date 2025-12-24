#!/usr/bin/env python3
"""Test sequential fitting on GRT files and compare to simultaneous fitting."""

import pandas as pd
from ballistics import (
    load_grt_project,
    metadata_to_config,
    fit_vivacity_polynomial,
    fit_vivacity_sequential,
)


def test_parameter_sensitivities():
    """Test parameter impact order on GRT files."""
    grt_files = [
        "data/grt_files/65CM_130SMK_N150_Starline_Initial.grtload",  # Test on N150
    ]

    for grt_file in grt_files:
        print(f"\n{'=' * 60}")
        print(f"Testing file: {grt_file}")
        print(f"{'=' * 60}")

        # Load data
        metadata, load_data = load_grt_project(grt_file)
        config = metadata_to_config(metadata)

        print(f"Cartridge: {metadata['cartridge']}")
        print(f"Propellant: {metadata['propellant_name']}")
        print(f"Bullet: {metadata['bullet_mass_gr']} gr")
        print(f"Charges: {len(load_data)}")
        print(
            f"Velocities: {load_data['mean_velocity_fps'].min():.0f} - {load_data['mean_velocity_fps'].max():.0f} fps"
        )

        # Fit parameters in order of impact: Lambda_base > coeffs > h_base > temp_sens > bore_friction
        results = {}

        # 1. Only Lambda_base
        print("\n--- 1. Fitting only Lambda_base ---")
        result1 = fit_vivacity_polynomial(
            load_data,
            config,
            verbose=False,
            fit_h_base=False,
            fit_temp_sensitivity=False,
            fit_bore_friction=False,
            fit_start_pressure=False,
            fit_covolume=False,
            use_form_function=True,  # Only Lambda
        )
        results["Lambda_only"] = result1
        print(
            f"RMSE: {result1['rmse_velocity']:.2f} fps, Lambda: {result1['Lambda_base']:.4f}"
        )

        # 2. Lambda + coeffs
        print("\n--- 2. Fitting Lambda_base + coeffs ---")
        result2 = fit_vivacity_polynomial(
            load_data,
            config,
            verbose=False,
            fit_h_base=False,
            fit_temp_sensitivity=False,
            fit_bore_friction=False,
            fit_start_pressure=False,
            fit_covolume=False,
            use_form_function=False,  # Lambda + coeffs
        )
        results["Lambda_coeffs"] = result2
        print(
            f"RMSE: {result2['rmse_velocity']:.2f} fps, Lambda: {result2['Lambda_base']:.4f}, Coeffs: {result2['coeffs']}"
        )

        # 3. Lambda + coeffs + h_base
        print("\n--- 3. Fitting Lambda_base + coeffs + h_base ---")
        result3 = fit_vivacity_polynomial(
            load_data,
            config,
            verbose=False,
            fit_h_base=True,
            fit_temp_sensitivity=False,
            fit_bore_friction=False,
            fit_start_pressure=False,
            fit_covolume=False,
        )
        results["Lambda_coeffs_h"] = result3
        print(
            f"RMSE: {result3['rmse_velocity']:.2f} fps, Lambda: {result3['Lambda_base']:.4f}, Coeffs: {result3['coeffs']}, h_base: {result3.get('h_base', 'N/A')}"
        )

        # 4. Lambda + coeffs + h_base + temp_sens
        print("\n--- 4. Fitting Lambda_base + coeffs + h_base + temp_sens ---")
        result4 = fit_vivacity_polynomial(
            load_data,
            config,
            verbose=False,
            fit_h_base=True,
            fit_temp_sensitivity=True,
            fit_bore_friction=False,
            fit_start_pressure=False,
            fit_covolume=False,
        )
        results["Lambda_coeffs_h_temp"] = result4
        print(
            f"RMSE: {result4['rmse_velocity']:.2f} fps, temp_sens: {result4.get('temp_sensitivity_sigma_per_K', 'N/A')}"
        )

        # 5. Lambda + coeffs + h_base + start_pressure
        print("\n--- 5. Fitting Lambda_base + coeffs + h_base + start_pressure ---")
        result5 = fit_vivacity_polynomial(
            load_data,
            config,
            verbose=True,
            fit_h_base=True,
            fit_temp_sensitivity=False,
            fit_bore_friction=False,
            fit_start_pressure=True,
            fit_covolume=False,
        )
        results["Lambda_coeffs_h_start"] = result5
        print(
            f"RMSE: {result5['rmse_velocity']:.2f} fps, start_p: {result5.get('start_pressure_psi', 'N/A')}"
        )

        # 6. All parameters
        print("\n--- 6. Fitting all parameters ---")
        result6 = fit_vivacity_polynomial(
            load_data,
            config,
            verbose=False,
            fit_h_base=True,
            fit_temp_sensitivity=True,
            fit_bore_friction=True,
            fit_start_pressure=False,
            fit_covolume=False,
        )
        results["all"] = result6
        print(
            f"RMSE: {result6['rmse_velocity']:.2f} fps, bore_fric: {result6.get('bore_friction_psi', 'N/A')}"
        )

        # Summary of improvements
        print("\n--- Parameter Impact Summary ---")
        rmse_base = results["Lambda_only"]["rmse_velocity"]
        print(f"Base RMSE (Lambda only): {rmse_base:.2f} fps")
        print(
            f"Improvement adding coeffs: {rmse_base - results['Lambda_coeffs']['rmse_velocity']:.2f} fps ({(rmse_base - results['Lambda_coeffs']['rmse_velocity']) / rmse_base * 100:.1f}%)"
        )
        print(
            f"Improvement adding h_base: {results['Lambda_coeffs']['rmse_velocity'] - results['Lambda_coeffs_h']['rmse_velocity']:.2f} fps ({(results['Lambda_coeffs']['rmse_velocity'] - results['Lambda_coeffs_h']['rmse_velocity']) / results['Lambda_coeffs']['rmse_velocity'] * 100:.1f}%)"
        )
        print(
            f"Improvement adding start_pressure: {results['Lambda_coeffs_h']['rmse_velocity'] - results['Lambda_coeffs_h_start']['rmse_velocity']:.2f} fps ({(results['Lambda_coeffs_h']['rmse_velocity'] - results['Lambda_coeffs_h_start']['rmse_velocity']) / results['Lambda_coeffs_h']['rmse_velocity'] * 100:.1f}%)"
        )
        print(
            f"Improvement adding temp_sens: {results['Lambda_coeffs_h_start']['rmse_velocity'] - results['Lambda_coeffs_h_temp']['rmse_velocity']:.2f} fps ({(results['Lambda_coeffs_h_start']['rmse_velocity'] - results['Lambda_coeffs_h_temp']['rmse_velocity']) / results['Lambda_coeffs_h_start']['rmse_velocity'] * 100:.1f}%)"
        )
        print(
            f"Improvement adding bore_fric: {results['Lambda_coeffs_h_temp']['rmse_velocity'] - results['all']['rmse_velocity']:.2f} fps ({(results['Lambda_coeffs_h_temp']['rmse_velocity'] - results['all']['rmse_velocity']) / results['Lambda_coeffs_h_temp']['rmse_velocity'] * 100:.1f}%)"
        )

        # Sequential vs Simultaneous for Lambda + coeffs + h_base
        print("\n--- Sequential vs Simultaneous (Lambda + coeffs + h_base) ---")
        seq_result = fit_vivacity_sequential(load_data, config, verbose=False)
        print(f"Sequential RMSE: {seq_result['rmse_velocity']:.2f} fps")
        print(f"Simultaneous RMSE: {result3['rmse_velocity']:.2f} fps")
        print(
            f"Difference: {seq_result['rmse_velocity'] - result3['rmse_velocity']:.2f} fps"
        )


if __name__ == "__main__":
    test_parameter_sensitivities()
