import sys

sys.path.insert(0, "src")

from ballistics.core.props import PropellantProperties

prop = PropellantProperties.from_database("N150")

print(f"Name: {prop.name}")
print(f"Vivacity: {prop.vivacity}")
print(f"Force: {prop.force}")
print(f"Lambda_base: {prop.Lambda_base}")
print(f"Coeffs: {prop.poly_coeffs}")
print(f"Gamma: {prop.gamma}")
print(f"Temp_0: {prop.temp_0}")
print(f"Bulk density: {prop.bulk_density}")
print(f"Covolume: {prop.covolume_m3_per_kg}")
print(f"Temp sensitivity: {prop.temp_sensitivity_sigma_per_K}")
