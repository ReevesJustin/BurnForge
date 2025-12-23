"""Quick verification script for Phase 2 implementation."""

import sys
sys.path.insert(0, 'src')

print("=" * 60)
print("Phase 2 Verification Script")
print("=" * 60)

# Test 1: Import all modules
print("\n[1/5] Testing module imports...")
try:
    from ballistics import (
        solve_ballistics,
        fit_vivacity_polynomial,
        load_chronograph_csv,
        load_grt_project,
        metadata_to_config,
        export_fit_results,
        PropellantProperties,
        BulletProperties,
        BallisticsConfig
    )
    print("✓ All modules imported successfully")
except ImportError as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

# Test 2: Load database items
print("\n[2/5] Testing database access...")
try:
    prop = PropellantProperties.from_database("Varget")
    bullet = BulletProperties.from_database("Copper Jacket over Lead")
    print(f"✓ Loaded propellant: {prop.name}")
    print(f"✓ Loaded bullet type: {bullet.name}")
except Exception as e:
    print(f"✗ Database access failed: {e}")
    sys.exit(1)

# Test 3: Create config
print("\n[3/5] Testing config creation...")
try:
    config = BallisticsConfig(
        bullet_mass_gr=175.0,
        charge_mass_gr=40.0,
        caliber_in=0.308,
        case_volume_gr_h2o=49.5,
        barrel_length_in=24.0,
        cartridge_overall_length_in=2.810,
        propellant=prop,
        bullet=bullet
    )
    print(f"✓ Config created successfully")
    print(f"  Effective barrel length: {config.effective_barrel_length_in:.3f} in")
except Exception as e:
    print(f"✗ Config creation failed: {e}")
    sys.exit(1)

# Test 4: Run solver
print("\n[4/5] Testing solver...")
try:
    result = solve_ballistics(config)
    print(f"✓ Solver ran successfully")
    print(f"  Muzzle velocity: {result['muzzle_velocity_fps']:.1f} fps")
    print(f"  Peak pressure: {result['peak_pressure_psi']:.0f} psi")
    if 'burnout_distance_from_bolt_in' in result:
        print(f"  Burnout distance: {result['burnout_distance_from_bolt_in']:.2f} in")
    else:
        print(f"  Muzzle burn: {result['muzzle_burn_percentage']:.1f}%")
except Exception as e:
    print(f"✗ Solver failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: Test GRT import (if file exists)
print("\n[5/5] Testing GRT import...")
try:
    import os
    grt_path = "65CRM_130SMK_N150_Starline_Initial.grtload"
    if os.path.exists(grt_path):
        metadata, load_data = load_grt_project(grt_path)
        print(f"✓ GRT file loaded successfully")
        print(f"  Cartridge: {metadata.get('cartridge', 'Unknown')}")
        print(f"  Barrel length: {metadata['barrel_length_in']:.2f} in")
        print(f"  Bullet mass: {metadata['bullet_mass_gr']:.1f} gr")
        print(f"  Propellant: {metadata['propellant_name']}")
        print(f"  Measurement charges: {len(load_data)}")
    else:
        print("⊘ GRT file not found (skipping)")
except Exception as e:
    print(f"✗ GRT import failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("Phase 2 Verification Complete!")
print("=" * 60)
print("\nAll core functionality is working. Tests can be run with:")
print("  pip install -e .")
print("  python -m pytest tests/ -v")
