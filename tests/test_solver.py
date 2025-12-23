"""Unit tests for solver.py integration accuracy."""

import sys
sys.path.insert(0, 'src')

from ballistics import (
    solve_ballistics,
    PropellantProperties,
    BulletProperties,
    BallisticsConfig
)


def test_solve_ivp_convergence():
    """Test that solve_ivp produces reasonable results."""
    # Load propellant and bullet from database
    prop = PropellantProperties.from_database("N140")
    bullet = BulletProperties.from_database("Copper Jacket over Lead")

    # Create configuration (similar to legacy default)
    config = BallisticsConfig(
        bullet_mass_gr=175.0,
        charge_mass_gr=42.0,
        caliber_in=0.308,
        case_volume_gr_h2o=47.4,
        barrel_length_in=16.625,
        cartridge_overall_length_in=2.810,  # COAL
        propellant=prop,
        bullet=bullet,
        temperature_f=36.0
    )

    # Solve
    results = solve_ballistics(config)

    # Basic sanity checks
    assert 'muzzle_velocity_fps' in results
    assert 'peak_pressure_psi' in results
    assert 'final_Z' in results

    # Velocity should be positive and reasonable for .308
    assert 1500 < results['muzzle_velocity_fps'] < 3500, \
        f"Velocity {results['muzzle_velocity_fps']:.1f} fps out of reasonable range"

    # Pressure should be positive and not exceed extreme values
    assert 10000 < results['peak_pressure_psi'] < 80000, \
        f"Pressure {results['peak_pressure_psi']:.0f} psi out of reasonable range"

    # Burn fraction should be between 0 and 1
    assert 0 <= results['final_Z'] <= 1, \
        f"Burn fraction {results['final_Z']:.3f} out of valid range"

    # Energy should be positive
    assert results['muzzle_energy_ft_lbs'] > 0, \
        f"Muzzle energy {results['muzzle_energy_ft_lbs']:.0f} ft-lbs should be positive"

    print(f"✓ Convergence test passed")
    print(f"  Muzzle velocity: {results['muzzle_velocity_fps']:.1f} fps")
    print(f"  Muzzle energy: {results['muzzle_energy_ft_lbs']:.0f} ft-lbs")
    print(f"  Peak pressure: {results['peak_pressure_psi']:.0f} psi")
    print(f"  Final Z: {results['final_Z']:.3f}")


def test_burnout_detection():
    """Test that burnout event is detected correctly."""
    # Use a moderate charge that should achieve burnout
    prop = PropellantProperties.from_database("Varget")
    bullet = BulletProperties.from_database("Copper Jacket over Lead")

    config = BallisticsConfig(
        bullet_mass_gr=175.0,
        charge_mass_gr=43.0,  # Moderate charge
        caliber_in=0.308,
        case_volume_gr_h2o=49.5,
        barrel_length_in=24.0,  # Long barrel
        cartridge_overall_length_in=2.810,
        propellant=prop,
        bullet=bullet,
        temperature_f=70.0
    )

    results = solve_ballistics(config)

    # Check if burnout occurred
    if results['final_Z'] >= 0.999:
        assert 'burnout_distance_from_bolt_in' in results, \
            "Burnout occurred but distance not reported"

        burnout_dist = results['burnout_distance_from_bolt_in']
        assert 0 < burnout_dist < config.barrel_length_in, \
            f"Burnout distance {burnout_dist:.2f} in should be within barrel length"

        print(f"✓ Burnout detection test passed")
        print(f"  Burnout at: {burnout_dist:.2f} in from bolt face")
        print(f"  Barrel length: {config.barrel_length_in} in")
        print(f"  Burnout fraction: {burnout_dist / config.barrel_length_in:.1%} of barrel")
    else:
        assert 'muzzle_burn_percentage' in results, \
            "Incomplete burn but muzzle_burn_percentage not reported"

        print(f"✓ Incomplete burn detected correctly")
        print(f"  Muzzle burn: {results['muzzle_burn_percentage']:.1f}%")


def test_trace_output():
    """Test that trace output is returned when requested."""
    prop = PropellantProperties.from_database("N140")
    bullet = BulletProperties.from_database("Copper Jacket over Lead")

    config = BallisticsConfig(
        bullet_mass_gr=175.0,
        charge_mass_gr=42.0,
        caliber_in=0.308,
        case_volume_gr_h2o=47.4,
        barrel_length_in=16.625,
        cartridge_overall_length_in=2.810,
        propellant=prop,
        bullet=bullet,
        temperature_f=70.0
    )

    results = solve_ballistics(config, return_trace=True)

    # Check trace arrays exist
    assert 't' in results, "Time trace not in results"
    assert 'Z' in results, "Burn fraction trace not in results"
    assert 'v' in results, "Velocity trace not in results"
    assert 'x' in results, "Distance trace not in results"
    assert 'P' in results, "Pressure trace not in results"

    # Check arrays are same length
    assert len(results['t']) == len(results['Z']) == len(results['v']) == \
           len(results['x']) == len(results['P']), "Trace arrays have mismatched lengths"

    print(f"✓ Trace output test passed")
    print(f"  Trace length: {len(results['t'])} points")
    print(f"  Time range: {results['t'][0]:.6f} to {results['t'][-1]:.6f} s")


if __name__ == '__main__':
    print("Running solver unit tests...")
    print()

    test_solve_ivp_convergence()
    print()

    test_burnout_detection()
    print()

    test_trace_output()
    print()

    print("=" * 50)
    print("All tests passed! ✓")
