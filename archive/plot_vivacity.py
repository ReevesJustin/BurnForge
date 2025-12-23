#!/usr/bin/env python3
# Script to plot dynamic vivacity vs. burn fraction Z

import numpy as np
import matplotlib.pyplot as plt
from solver import calc_lambda_z  # Import the solver's vivacity function

# Fitted A2495 parameters
Lambda_base_fitted = 81.8  # s^-1 per 100 bar
poly_coeffs_fitted = (1.040, -0.614, 0.225, -0.005)

# Default parameters (triggers original polynomial in solver)
Lambda_base_default = 71.2  # s^-1 per 100 bar (for comparison)
poly_coeffs_default = (1.0, -1.0, 0.0, 0.0)

# Generate Z values
z = np.linspace(0, 1, 100)

# Calculate vivacity for fitted and default models
vivacity_fitted = [calc_lambda_z(z_val, Lambda_base_fitted / 1450, poly_coeffs_fitted) * 1450 for z_val in z]
vivacity_default = [calc_lambda_z(z_val, Lambda_base_default / 1450, poly_coeffs_default) * 1450 for z_val in z]

# Plotting
plt.figure(figsize=(10, 6))
plt.plot(z, vivacity_fitted, label=f'Fitted A2495 (Λ_base={Lambda_base_fitted:.1f})', color='blue')
plt.plot(z, vivacity_default, label=f'Default (Λ_base={Lambda_base_default:.1f})', color='red', linestyle='--')
plt.xlabel('Burn Fraction (Z)')
plt.ylabel('Dynamic Vivacity (s⁻¹ per 100 bar)')
plt.title('Dynamic Vivacity vs. Burn Fraction')
plt.legend()
plt.grid(True)
plt.savefig('vivacity_plot.png')
plt.show()