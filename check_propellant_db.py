#!/usr/bin/env python3
"""Check propellant database values."""

from ballistics.database.database import get_propellant
from ballistics.core.props import PropellantProperties

# Check Varget properties
propellant_name = "Varget"
props_dict = get_propellant(propellant_name)

print(f"Propellant: {propellant_name}")
print(f"\nDatabase values:")
for key, value in props_dict.items():
    print(f"  {key}: {value}")

# Create PropellantProperties object
props = PropellantProperties.from_database(propellant_name)

print(f"\nPropellantProperties object:")
print(f"  Lambda_base: {props.Lambda_base:.6f}")
print(f"  poly_coeffs: {props.poly_coeffs}")
print(f"  force (in*lbf/lbm): {props.force:.1f}")
print(f"  gamma: {props.gamma:.3f}")
print(f"  covolume (m3/kg): {props.covolume_m3_per_kg:.6f}")
print(f"  temp_sensitivity (1/K): {props.temp_sensitivity_sigma_per_K:.6f}")
print(f"  grain_geometry: {props.grain_geometry}")
print(f"  bulk_density (lb/ft³): {props.bulk_density:.1f}")

# Check vivacity conversion
print(f"\nVivacity check:")
print(f"  vivacity (raw from DB): {props_dict['vivacity']:.1f}")
print(f"  Lambda_base (converted): {props.Lambda_base:.6f}")
print(f"  Conversion factor: {props_dict['vivacity'] / props.Lambda_base:.1f}")
print(f"  Expected conversion (1450): 1450")

# Typical values for reference
print(f"\nTypical ballistics values for reference:")
print(f"  Force: 900-1200 in*lbf/lbm")
print(f"  Gamma: 1.20-1.30")
print(f"  Covolume: 0.0008-0.0012 m³/kg")
print(f"  Lambda_base: 0.02-0.08 s⁻¹/psi (for medium burn rate)")
