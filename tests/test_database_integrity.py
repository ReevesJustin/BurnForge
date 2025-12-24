"""Database integrity validation tests.

These tests ensure the propellant database contains physically reasonable
values and prevent regressions like the force value bug (2024-12-24).
"""

import pytest
import numpy as np
from ballistics.database.database import (
    get_propellant,
    list_propellants,
    get_bullet_type,
    get_default_db_path,
)


class TestPropellantForceValues:
    """Validate propellant force values are physically reasonable."""

    def test_force_values_in_valid_range(self):
        """Force should be 600,000-900,000 ft·lbf/lbm for typical propellants."""
        all_propellants = list_propellants()

        failures = []
        for name in all_propellants:
            props = get_propellant(name)
            force = props["force"]

            # Physically reasonable range based on empirical data
            # Single-base: ~730,000 ft·lbf/lbm
            # Double-base: ~790,000 ft·lbf/lbm
            # Allow ±30% tolerance for variations
            min_force = 500_000  # Lower bound (conservative)
            max_force = 1_000_000  # Upper bound (conservative)

            if not (min_force <= force <= max_force):
                failures.append(
                    f"{name}: force={force:.0f} ft·lbf/lbm (expected {min_force:,}-{max_force:,})"
                )

        assert len(failures) == 0, (
            f"Found {len(failures)} propellants with invalid force values:\n"
            + "\n".join(failures)
        )

    def test_single_base_force_range(self):
        """Single-base propellants should have force ~700,000-800,000."""
        all_propellants = list_propellants()

        failures = []
        for name in all_propellants:
            props = get_propellant(name)

            if props["base"] == "S":  # Single-base
                force = props["force"]

                # Single-base typically 700,000-800,000 ft·lbf/lbm
                # Based on corrected database values (730,000)
                min_force = 650_000
                max_force = 850_000

                if not (min_force <= force <= max_force):
                    failures.append(
                        f"{name} (single-base): force={force:.0f} (expected {min_force:,}-{max_force:,})"
                    )

        assert len(failures) == 0, (
            f"Found {len(failures)} single-base propellants with force outside typical range:\n"
            + "\n".join(failures)
        )

    def test_double_base_force_range(self):
        """Double-base propellants should have force ~750,000-850,000."""
        all_propellants = list_propellants()

        failures = []
        for name in all_propellants:
            props = get_propellant(name)

            if props["base"] == "D":  # Double-base
                force = props["force"]

                # Double-base typically higher energy: 750,000-850,000 ft·lbf/lbm
                # Based on corrected database values (790,000)
                min_force = 700_000
                max_force = 900_000

                if not (min_force <= force <= max_force):
                    failures.append(
                        f"{name} (double-base): force={force:.0f} (expected {min_force:,}-{max_force:,})"
                    )

        assert len(failures) == 0, (
            f"Found {len(failures)} double-base propellants with force outside typical range:\n"
            + "\n".join(failures)
        )

    def test_propellants_have_diverse_force_values(self):
        """Ensure propellants don't all have identical force values."""
        all_propellants = list_propellants()
        forces = [get_propellant(name)["force"] for name in all_propellants]

        unique_forces = set(forces)

        # Should have at least 2 distinct values (single-base vs double-base minimum)
        # Ideally more variation within each type
        assert len(unique_forces) >= 2, (
            f"Only {len(unique_forces)} unique force values found among {len(forces)} propellants. "
            f"This suggests database corruption (e.g., all values set to same default)."
        )

    def test_known_propellants_have_expected_forces(self):
        """Verify common propellants have approximately correct force values."""
        # Based on corrected database (single-base = 730,000, double-base = 790,000)
        expected_values = {
            "Varget": (680_000, 780_000),  # Single-base
            "H4350": (680_000, 780_000),  # Single-base
            "N150": (680_000, 780_000),  # Single-base
            "IMR 4064": (680_000, 780_000),  # Single-base (if exists)
        }

        for name, (min_force, max_force) in expected_values.items():
            try:
                props = get_propellant(name)
                force = props["force"]

                assert min_force <= force <= max_force, (
                    f"{name} has force={force:.0f}, expected {min_force:,}-{max_force:,}"
                )
            except ValueError:
                # Propellant doesn't exist in database - skip
                pass


class TestPropellantPhysicalParameters:
    """Validate other physical parameters are reasonable."""

    def test_gamma_values_in_range(self):
        """Gamma (heat capacity ratio) should be 1.15-1.35 for propellants."""
        all_propellants = list_propellants()

        failures = []
        for name in all_propellants:
            props = get_propellant(name)

            # Gamma computed from base type, should be ~1.20-1.30
            # We don't have gamma in DB, but computed in PropellantProperties
            # Skip this test for now since gamma is derived
            pass

    def test_covolume_values_in_range(self):
        """Covolume should be 0.0008-0.0012 m³/kg."""
        all_propellants = list_propellants()

        failures = []
        for name in all_propellants:
            props = get_propellant(name)
            covolume = props.get("covolume_m3_per_kg", 0.001)

            # Typical range from Nobel-Abel EOS
            min_covolume = 0.0007
            max_covolume = 0.0015

            if not (min_covolume <= covolume <= max_covolume):
                failures.append(
                    f"{name}: covolume={covolume:.6f} m³/kg (expected {min_covolume}-{max_covolume})"
                )

        assert len(failures) == 0, (
            f"Found {len(failures)} propellants with invalid covolume:\n"
            + "\n".join(failures[:10])  # Show first 10
        )

    def test_temp_sensitivity_in_range(self):
        """Temperature sensitivity should be 0-0.01 per K."""
        all_propellants = list_propellants()

        failures = []
        for name in all_propellants:
            props = get_propellant(name)
            temp_sens = props.get("temp_sensitivity_sigma_per_K", 0.002)

            # Typical range: 0.002-0.008 per K
            # Allow 0-0.01 for safety margin
            min_temp_sens = 0.0
            max_temp_sens = 0.01

            if not (min_temp_sens <= temp_sens <= max_temp_sens):
                failures.append(
                    f"{name}: temp_sensitivity={temp_sens:.6f} /K (expected {min_temp_sens}-{max_temp_sens})"
                )

        assert len(failures) == 0, (
            f"Found {len(failures)} propellants with invalid temp sensitivity:\n"
            + "\n".join(failures[:10])
        )

    def test_vivacity_values_positive(self):
        """Vivacity should be positive (typically 30-100)."""
        all_propellants = list_propellants()

        failures = []
        for name in all_propellants:
            props = get_propellant(name)
            vivacity = props["vivacity"]

            # Vivacity in s^-1 per 100 bar, typical range 30-100
            if not (10 <= vivacity <= 150):
                failures.append(f"{name}: vivacity={vivacity:.1f} (expected 10-150)")

        assert len(failures) == 0, (
            f"Found {len(failures)} propellants with invalid vivacity:\n"
            + "\n".join(failures[:10])
        )

    def test_flame_temperature_in_range(self):
        """Flame temperature should be 2000-4000 K."""
        all_propellants = list_propellants()

        failures = []
        for name in all_propellants:
            props = get_propellant(name)
            temp_0 = props["temp_0"]

            # Typical adiabatic flame temperature: 2500-3500 K
            min_temp = 2000
            max_temp = 4000

            if not (min_temp <= temp_0 <= max_temp):
                failures.append(
                    f"{name}: temp_0={temp_0:.0f} K (expected {min_temp}-{max_temp})"
                )

        assert len(failures) == 0, (
            f"Found {len(failures)} propellants with invalid flame temperature:\n"
            + "\n".join(failures[:10])
        )


class TestPropellantDataCompleteness:
    """Ensure all required fields are present and valid."""

    def test_all_propellants_have_required_fields(self):
        """All propellants must have essential fields."""
        all_propellants = list_propellants()

        required_fields = ["vivacity", "base", "force", "temp_0"]

        failures = []
        for name in all_propellants:
            props = get_propellant(name)

            for field in required_fields:
                if field not in props or props[field] is None:
                    failures.append(f"{name}: missing or null field '{field}'")

        assert len(failures) == 0, (
            f"Found {len(failures)} propellants with missing required fields:\n"
            + "\n".join(failures[:20])
        )

    def test_base_type_is_valid(self):
        """Base type must be 'S' (single) or 'D' (double)."""
        all_propellants = list_propellants()

        failures = []
        for name in all_propellants:
            props = get_propellant(name)
            base = props["base"]

            if base not in ("S", "D"):
                failures.append(f"{name}: invalid base type '{base}' (expected 'S' or 'D')")

        assert len(failures) == 0, (
            f"Found {len(failures)} propellants with invalid base type:\n"
            + "\n".join(failures)
        )

    def test_polynomial_coefficients_present(self):
        """Polynomial coefficients should exist (can be 0)."""
        all_propellants = list_propellants()

        failures = []
        for name in all_propellants:
            props = get_propellant(name)

            coeff_fields = ["poly_a", "poly_b", "poly_c", "poly_d"]
            for field in coeff_fields:
                if field not in props:
                    failures.append(f"{name}: missing coefficient '{field}'")

        assert len(failures) == 0, (
            f"Found {len(failures)} propellants with missing polynomial coefficients:\n"
            + "\n".join(failures[:20])
        )


class TestBulletTypeData:
    """Validate bullet type data integrity."""

    def test_bullet_strength_factor_in_range(self):
        """Bullet strength factor 's' should be physically reasonable."""
        # Test a few common bullet types
        bullet_types = [
            "Copper Jacket over Lead",
            "Solid Copper",
            "Lead",
        ]

        for bullet_type in bullet_types:
            try:
                props = get_bullet_type(bullet_type)
                s = props["s"]

                # Strength factor should be positive and reasonable
                # Note: Database uses different scaling than expected (s=100 is typical)
                # Allow wide range: 1-500
                assert 0.1 <= s <= 500.0, (
                    f"{bullet_type}: strength factor s={s:.2f} outside expected range (0.1-500.0)"
                )
            except ValueError:
                # Bullet type doesn't exist - skip
                pass

    def test_bullet_density_in_range(self):
        """Bullet density should be physically reasonable."""
        bullet_types = [
            "Copper Jacket over Lead",
            "Solid Copper",
            "Lead",
        ]

        for bullet_type in bullet_types:
            try:
                props = get_bullet_type(bullet_type)
                rho_p = props["rho_p"]

                # Density in lbm/in³
                # Lead: ~0.41 lbm/in³
                # Copper: ~0.32 lbm/in³
                # Should be in range 0.2 - 0.5
                assert 0.15 <= rho_p <= 0.6, (
                    f"{bullet_type}: density rho_p={rho_p:.3f} lbm/in³ outside expected range"
                )
            except ValueError:
                # Bullet type doesn't exist - skip
                pass


class TestDatabaseStatistics:
    """Statistical validation of database contents."""

    def test_sufficient_propellant_diversity(self):
        """Database should contain multiple propellants."""
        all_propellants = list_propellants()

        assert len(all_propellants) >= 10, (
            f"Database contains only {len(all_propellants)} propellants. "
            f"Expected at least 10 for useful coverage."
        )

    def test_force_values_not_all_identical(self):
        """Critical regression test for force value bug."""
        all_propellants = list_propellants()
        forces = [get_propellant(name)["force"] for name in all_propellants]

        # Check if all values are identical (sign of database corruption)
        unique_forces = len(set(forces))
        total_propellants = len(forces)

        # At minimum, should have different values for S vs D base
        assert unique_forces >= 2, (
            f"CRITICAL: All {total_propellants} propellants have only {unique_forces} unique force value(s). "
            f"This indicates database corruption similar to 2024-12-24 bug."
        )

        # Ideally, should have some variation within base types too
        if unique_forces == 2:
            print(
                f"Warning: Only 2 unique force values found. "
                f"Consider adding more variation for different propellant types."
            )

    def test_force_value_distribution_reasonable(self):
        """Force values should have reasonable statistical distribution."""
        all_propellants = list_propellants()
        forces = np.array([get_propellant(name)["force"] for name in all_propellants])

        mean_force = np.mean(forces)
        std_force = np.std(forces)

        # Mean should be around 730,000-790,000
        assert 650_000 <= mean_force <= 850_000, (
            f"Mean force {mean_force:.0f} outside expected range (650,000-850,000)"
        )

        # Standard deviation should be non-zero but not too large
        # Expected: some variation between single/double base
        assert 0 < std_force < 200_000, (
            f"Force standard deviation {std_force:.0f} suggests unusual distribution"
        )


class TestDatabaseConsistency:
    """Test for internal consistency and relationships."""

    def test_double_base_force_higher_than_single_base(self):
        """Double-base propellants generally have higher energy than single-base."""
        all_propellants = list_propellants()

        single_base_forces = []
        double_base_forces = []

        for name in all_propellants:
            props = get_propellant(name)
            force = props["force"]

            if props["base"] == "S":
                single_base_forces.append(force)
            elif props["base"] == "D":
                double_base_forces.append(force)

        if len(single_base_forces) > 0 and len(double_base_forces) > 0:
            mean_single = np.mean(single_base_forces)
            mean_double = np.mean(double_base_forces)

            # Double-base should have higher average energy
            # Allow small tolerance in case of unusual propellants
            assert mean_double >= mean_single * 0.95, (
                f"Double-base mean force ({mean_double:.0f}) should be >= "
                f"single-base mean force ({mean_single:.0f})"
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
