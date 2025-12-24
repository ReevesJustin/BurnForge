"""Gemini Assistant Workflow Script - Master Analysis Tool

This script provides a complete workflow for GRT file analysis:
1. Find and load GRT file
2. Run baseline fit (Lambda + polynomial)
3. Run multi-parameter fit (user-specified)
4. Generate comparison report
5. Optionally update database

Usage:
    python gemini_workflow.py --file <name> [--detail] [--fit temp,friction,start] [--update-db]

Examples:
    # Search by partial name, summary report
    python gemini_workflow.py --file 65CRM

    # Specific file, detailed report
    python gemini_workflow.py --file 65CRM_130SMK_N150_Starline_Initial.grtload --detail

    # Multi-parameter fit with specific physics
    python gemini_workflow.py --file 65CRM --fit temp,friction

    # Update database with fitted parameters
    python gemini_workflow.py --file 65CRM --update-db
"""

import sys
import os
import glob
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import numpy as np
import pandas as pd
from ballistics import (
    load_grt_project,
    metadata_to_config,
    fit_vivacity_polynomial,
    database
)

# Constants
GRT_DIR = "data/grt_files"
DEFAULT_GRT_FALLBACK = "65CRM_130SMK_N150_Starline_Initial.grtload"


def find_grt_file(name_hint):
    """Find GRT file by name hint, extension, or content.

    Parameters
    ----------
    name_hint : str
        Partial filename, full filename, or search term

    Returns
    -------
    str
        Path to GRT file

    Raises
    ------
    FileNotFoundError
        If no matching file found
    """
    # Try exact path first
    if os.path.exists(name_hint):
        return name_hint

    # Try in GRT directory
    grt_path = os.path.join(GRT_DIR, name_hint)
    if os.path.exists(grt_path):
        return grt_path

    # Try adding .grtload extension
    if not name_hint.endswith('.grtload'):
        grt_path_ext = os.path.join(GRT_DIR, name_hint + '.grtload')
        if os.path.exists(grt_path_ext):
            return grt_path_ext

    # Search in GRT directory
    search_pattern = os.path.join(GRT_DIR, '*.grtload')
    grt_files = glob.glob(search_pattern)

    # Search by partial name match
    matches = [f for f in grt_files if name_hint.lower() in os.path.basename(f).lower()]

    if len(matches) == 1:
        return matches[0]
    elif len(matches) > 1:
        print(f"Multiple matches found:")
        for i, match in enumerate(matches, 1):
            print(f"  {i}. {os.path.basename(match)}")
        raise ValueError(f"Ambiguous file name '{name_hint}'. Please be more specific.")

    # Try root directory as fallback
    root_pattern = '*.grtload'
    root_files = glob.glob(root_pattern)
    matches = [f for f in root_files if name_hint.lower() in os.path.basename(f).lower()]

    if len(matches) == 1:
        return matches[0]
    elif len(matches) > 1:
        print(f"Multiple matches found in root:")
        for i, match in enumerate(matches, 1):
            print(f"  {i}. {os.path.basename(match)}")
        raise ValueError(f"Ambiguous file name '{name_hint}'. Please be more specific.")

    # Check if default fallback exists
    if os.path.exists(DEFAULT_GRT_FALLBACK):
        print(f"Warning: Using default file {DEFAULT_GRT_FALLBACK}")
        return DEFAULT_GRT_FALLBACK

    raise FileNotFoundError(
        f"No GRT file matching '{name_hint}' found.\n"
        f"Searched in:\n"
        f"  - {GRT_DIR}/\n"
        f"  - Current directory\n"
        f"Available files:\n" +
        "\n".join(f"  - {os.path.basename(f)}" for f in grt_files)
    )


def print_metadata(metadata, detail=False):
    """Print GRT file metadata."""
    print("\n" + "="*80)
    print("GRT FILE METADATA")
    print("="*80)

    print(f"\nCartridge:     {metadata['cartridge']}")
    print(f"Propellant:    {metadata['propellant_name']}")
    print(f"Bullet:        {metadata['bullet_mass_gr']:.1f} gr")
    print(f"Barrel:        {metadata['barrel_length_in']:.2f} in")
    print(f"Temperature:   {metadata['temperature_f']:.1f} °F")
    print(f"COAL:          {metadata['cartridge_overall_length_in']:.3f} in")
    print(f"Case Volume:   {metadata['case_volume_gr_h2o']:.2f} gr H2O")

    if detail:
        print(f"\nAdditional Details:")
        print(f"  Caliber:     {metadata['caliber_in']:.3f} in")
        if 'bullet_type' in metadata:
            print(f"  Bullet Type: {metadata['bullet_type']}")
        if 'case_brand' in metadata:
            print(f"  Case Brand:  {metadata['case_brand']}")


def print_load_data(load_data, detail=False):
    """Print load ladder data."""
    print("\n" + "="*80)
    print("LOAD LADDER DATA")
    print("="*80)
    print(f"\nMeasurement points: {len(load_data)}")
    print(f"Charge range: {load_data['charge_grains'].min():.2f} - {load_data['charge_grains'].max():.2f} gr")
    print(f"Velocity range: {load_data['mean_velocity_fps'].min():.0f} - {load_data['mean_velocity_fps'].max():.0f} fps")

    if detail:
        print(f"\n{'Charge (gr)':>12} {'Velocity (fps)':>15} {'SD (fps)':>12}")
        print("-" * 42)
        for _, row in load_data.iterrows():
            sd_str = f"{row['velocity_sd']:.1f}" if 'velocity_sd' in row and pd.notna(row['velocity_sd']) else "N/A"
            print(f"{row['charge_grains']:12.2f} {row['mean_velocity_fps']:15.1f} {sd_str:>12}")


def run_baseline_fit(load_data, config, verbose=False):
    """Run baseline fit (Lambda + polynomial only)."""
    print("\n" + "="*80)
    print("BASELINE FIT (Lambda + Polynomial)")
    print("="*80)
    print("\nFitting parameters: Lambda_base, a, b, c, d")

    fit_result = fit_vivacity_polynomial(
        load_data, config,
        verbose=verbose
    )

    return fit_result


def run_enhanced_fit(load_data, config, fit_params, verbose=False):
    """Run enhanced fit with specified physics parameters."""
    print("\n" + "="*80)
    print("ENHANCED FIT (Multi-Parameter)")
    print("="*80)

    # Parse fit parameters
    fit_temp = 'temp' in fit_params or 'temperature' in fit_params
    fit_friction = 'friction' in fit_params or 'bore' in fit_params
    fit_start = 'start' in fit_params or 'pressure' in fit_params
    fit_cov = 'covolume' in fit_params

    params_list = []
    if fit_temp:
        params_list.append("temperature sensitivity")
    if fit_friction:
        params_list.append("bore friction")
    if fit_start:
        params_list.append("shot-start pressure")
    if fit_cov:
        params_list.append("covolume")

    print(f"\nFitting parameters: Lambda_base, a, b, c, d, {', '.join(params_list)}")

    fit_result = fit_vivacity_polynomial(
        load_data, config,
        fit_temp_sensitivity=fit_temp,
        fit_bore_friction=fit_friction,
        fit_start_pressure=fit_start,
        fit_covolume=fit_cov,
        verbose=verbose
    )

    return fit_result


def print_fit_summary(fit_result, label, detail=False):
    """Print fit results summary."""
    print(f"\n{label} Results:")
    print("-" * 60)
    print(f"  RMSE:                {fit_result['rmse_velocity']:>10.2f} fps")
    print(f"  Success:             {fit_result['success']}")
    print(f"  Iterations:          {fit_result['iterations']}")

    if detail:
        print(f"\n  Fitted Parameters:")
        print(f"    Lambda_base:       {fit_result['Lambda_base']:>10.6f}")
        a, b, c, d = fit_result['coeffs']
        print(f"    Coefficients:      a={a:+.3f}, b={b:+.3f}, c={c:+.3f}, d={d:+.3f}")

        if 'temp_sensitivity_sigma_per_K' in fit_result:
            temp_sens = fit_result['temp_sensitivity_sigma_per_K']
            print(f"    Temp sensitivity:  {temp_sens:.6f} /K  (~{temp_sens*5/9:.6f} /°F)")

        if 'bore_friction_psi' in fit_result:
            print(f"    Bore friction:     {fit_result['bore_friction_psi']:.1f} psi")

        if 'start_pressure_psi' in fit_result:
            print(f"    Shot-start P:      {fit_result['start_pressure_psi']:.1f} psi")

        if 'covolume_m3_per_kg' in fit_result:
            print(f"    Covolume:          {fit_result['covolume_m3_per_kg']:.6f} m³/kg")


def print_residual_analysis(fit_result, load_data, label, detail=False):
    """Print residual analysis."""
    residuals = np.array(fit_result['residuals'])
    predicted = np.array(fit_result['predicted_velocities'])
    measured = load_data['mean_velocity_fps'].values
    charges = load_data['charge_grains'].values

    print(f"\n{label} Residual Analysis:")
    print("-" * 60)
    print(f"  Mean residual:       {np.mean(residuals):>+10.2f} fps")
    print(f"  Std dev:             {np.std(residuals):>10.2f} fps")
    print(f"  Max absolute:        {np.max(np.abs(residuals)):>10.2f} fps")

    # Systematic bias check
    mid = len(residuals) // 2
    bias_low = np.mean(residuals[:mid])
    bias_high = np.mean(residuals[mid:])
    bias_diff = bias_high - bias_low

    print(f"\n  Systematic Bias:")
    print(f"    Lower charges:     {bias_low:>+10.2f} fps")
    print(f"    Upper charges:     {bias_high:>+10.2f} fps")
    print(f"    Difference:        {bias_diff:>+10.2f} fps")

    if abs(bias_diff) > 5:
        print(f"    Status:            ⚠️  BIAS DETECTED")
    else:
        print(f"    Status:            ✓ No significant bias")

    if detail:
        print(f"\n  Detailed Residuals:")
        print(f"  {'Charge':>8} {'Measured':>10} {'Predicted':>10} {'Residual':>10} {'% Error':>10}")
        print("  " + "-" * 62)
        for i in range(len(charges)):
            pct_err = (residuals[i] / measured[i]) * 100
            print(f"  {charges[i]:8.1f} {measured[i]:10.1f} {predicted[i]:10.1f} "
                  f"{residuals[i]:+10.1f} {pct_err:+9.2f}%")


def print_comparison(baseline, enhanced, detail=False):
    """Print comparison between baseline and enhanced fits."""
    print("\n" + "="*80)
    print("FIT COMPARISON")
    print("="*80)

    rmse_base = baseline['rmse_velocity']
    rmse_enh = enhanced['rmse_velocity']
    improvement = rmse_base - rmse_enh
    pct_improvement = (improvement / rmse_base) * 100

    print(f"\n{'Configuration':<40} {'RMSE':>10} {'vs Baseline':>15}")
    print("-" * 68)
    print(f"{'Baseline (Lambda + polynomial)':<40} {rmse_base:>10.2f} {'--':>15}")
    print(f"{'Enhanced (multi-parameter)':<40} {rmse_enh:>10.2f} {improvement:>+14.2f}")
    print(f"\n{'Improvement:':<40} {improvement:>+10.2f} fps ({pct_improvement:+.1f}%)")

    if improvement > 10:
        print(f"\n  ✓✓ Significant improvement - enhanced fit recommended")
    elif improvement > 5:
        print(f"\n  ✓ Moderate improvement - consider enhanced fit")
    elif improvement > 0:
        print(f"\n  ~ Marginal improvement - baseline may be sufficient")
    else:
        print(f"\n  ⚠️  No improvement - baseline fit is better")

    if detail:
        # Compare residual patterns
        res_base = np.array(baseline['residuals'])
        res_enh = np.array(enhanced['residuals'])

        print(f"\n  Residual Pattern Comparison:")
        print(f"    Baseline std dev:  {np.std(res_base):.2f} fps")
        print(f"    Enhanced std dev:  {np.std(res_enh):.2f} fps")

        mid = len(res_base) // 2
        bias_base = np.mean(res_base[mid:]) - np.mean(res_base[:mid])
        bias_enh = np.mean(res_enh[mid:]) - np.mean(res_enh[:mid])

        print(f"    Baseline bias:     {bias_base:+.2f} fps")
        print(f"    Enhanced bias:     {bias_enh:+.2f} fps")
        print(f"    Bias reduction:    {bias_base - bias_enh:+.2f} fps")


def generate_report(grt_file, metadata, load_data, baseline_fit, enhanced_fit,
                   detail=False, fit_params=None):
    """Generate complete analysis report."""
    print("\n" + "="*80)
    print("INTERNAL BALLISTICS FITTING REPORT")
    print("="*80)
    print(f"File: {os.path.basename(grt_file)}")
    print(f"Analysis Date: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Metadata
    print_metadata(metadata, detail)

    # Load data
    print_load_data(load_data, detail)

    # Baseline fit
    print_fit_summary(baseline_fit, "BASELINE", detail)
    print_residual_analysis(baseline_fit, load_data, "BASELINE", detail)

    # Enhanced fit
    if enhanced_fit:
        print_fit_summary(enhanced_fit, "ENHANCED", detail)
        print_residual_analysis(enhanced_fit, load_data, "ENHANCED", detail)
        print_comparison(baseline_fit, enhanced_fit, detail)

    # Recommendations
    print("\n" + "="*80)
    print("RECOMMENDATIONS")
    print("="*80)

    rmse = baseline_fit['rmse_velocity']

    if rmse < 50:
        print(f"\n✓✓ EXCELLENT FIT (RMSE < 50 fps)")
        print(f"   Residuals within chronograph measurement accuracy")
        print(f"   Fitted parameters are highly reliable")
    elif rmse < 100:
        print(f"\n✓ GOOD FIT (RMSE < 100 fps)")
        print(f"   Suitable for load development and prediction")
        print(f"   Consider enhanced fit to reduce systematic bias")
    elif rmse < 200:
        print(f"\n~ ACCEPTABLE FIT (RMSE < 200 fps)")
        print(f"   May benefit from enhanced physics parameters")
        print(f"   Check for data quality issues")
    else:
        print(f"\n⚠️  POOR FIT (RMSE ≥ 200 fps)")
        print(f"   Recommended actions:")
        print(f"   1. Verify correct propellant selected from database")
        print(f"   2. Check data quality (chronograph issues?)")
        print(f"   3. Run physics diagnostics: ./venv/bin/python diagnose_physics_v3.py")

    # Physics parameter recommendations
    if enhanced_fit:
        improvement = baseline_fit['rmse_velocity'] - enhanced_fit['rmse_velocity']
        if improvement > 10:
            print(f"\n  Enhanced fit provides {improvement:.1f} fps improvement")
            print(f"  Consider updating database with enhanced parameters")

    print(f"\n" + "="*80)


def update_database_prompt(metadata, fit_result):
    """Generate database update commands for review."""
    print("\n" + "="*80)
    print("DATABASE UPDATE")
    print("="*80)

    propellant_name = metadata['propellant_name']
    Lambda_base = fit_result['Lambda_base']
    coeffs = fit_result['coeffs']

    print(f"\nTo update database with fitted parameters:")
    print(f"\nPython command:")
    print(f"```python")
    print(f"from ballistics import database")
    print(f"")
    print(f"database.update_propellant_coefficients(")
    print(f"    '{propellant_name}',")
    print(f"    {Lambda_base:.6f},")
    print(f"    {coeffs}")
    print(f")")
    print(f"```")

    print(f"\nSQL command (alternative):")
    print(f"```sql")
    print(f"UPDATE propellants")
    print(f"SET vivacity = {Lambda_base * 1450:.2f},")
    print(f"    poly_a = {coeffs[0]:.6f},")
    print(f"    poly_b = {coeffs[1]:.6f},")
    print(f"    poly_c = {coeffs[2]:.6f},")
    print(f"    poly_d = {coeffs[3]:.6f}")
    print(f"WHERE name = '{propellant_name}';")
    print(f"```")

    if 'temp_sensitivity_sigma_per_K' in fit_result:
        temp_sens = fit_result['temp_sensitivity_sigma_per_K']
        print(f"\nTemperature sensitivity:")
        print(f"```sql")
        print(f"UPDATE propellants")
        print(f"SET temp_sensitivity_sigma_per_K = {temp_sens:.6f}")
        print(f"WHERE name = '{propellant_name}';")
        print(f"```")

    print(f"\n⚠️  Review fitted parameters before updating database!")
    print(f"="*80)


def main():
    """Main workflow."""
    parser = argparse.ArgumentParser(
        description='GRT File Analysis Workflow',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --file 65CRM
  %(prog)s --file my_load.grtload --detail
  %(prog)s --file 65CRM --fit temp,friction
  %(prog)s --file 65CRM --fit temp,friction,start --update-db
        """
    )

    parser.add_argument('--file', type=str, required=True,
                       help='GRT file name or search term')
    parser.add_argument('--detail', action='store_true',
                       help='Generate detailed report (vs summary)')
    parser.add_argument('--fit', type=str, default='',
                       help='Physics parameters to fit (comma-separated): temp, friction, start, covolume')
    parser.add_argument('--update-db', action='store_true',
                       help='Show database update commands')
    parser.add_argument('--verbose', action='store_true',
                       help='Verbose fitting output')

    args = parser.parse_args()

    try:
        # Find GRT file
        print("Searching for GRT file...")
        grt_file = find_grt_file(args.file)
        print(f"✓ Found: {grt_file}")

        # Load data
        print("\nLoading GRT file...")
        metadata, load_data = load_grt_project(grt_file)
        print(f"✓ Loaded {len(load_data)} data points")

        # Create config
        config = metadata_to_config(metadata)

        # Run baseline fit
        baseline_fit = run_baseline_fit(load_data, config, verbose=args.verbose)

        # Run enhanced fit if requested
        enhanced_fit = None
        if args.fit:
            fit_params = [p.strip().lower() for p in args.fit.split(',')]
            enhanced_fit = run_enhanced_fit(load_data, config, fit_params, verbose=args.verbose)

        # Generate report
        generate_report(
            grt_file, metadata, load_data,
            baseline_fit, enhanced_fit,
            detail=args.detail,
            fit_params=args.fit
        )

        # Database update prompt
        if args.update_db:
            fit_to_use = enhanced_fit if enhanced_fit else baseline_fit
            update_database_prompt(metadata, fit_to_use)

    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
