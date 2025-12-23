"""Create diagnostic plots for fit analysis."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import numpy as np
import matplotlib.pyplot as plt
from ballistics import load_grt_project, metadata_to_config, fit_vivacity_polynomial
from ballistics.burn_rate import calc_vivacity

# Load and fit
grt_file = "65CRM_130SMK_N150_Starline_Initial.grtload"
metadata, load_data = load_grt_project(grt_file)
config = metadata_to_config(metadata)
fit_result = fit_vivacity_polynomial(load_data, config, verbose=False)

charges = load_data['charge_grains'].values
measured = load_data['mean_velocity_fps'].values
predicted = np.array(fit_result['predicted_velocities'])
residuals = np.array(fit_result['residuals'])

# Create figure with subplots
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('Fitting Diagnostics: 6.5 Creedmoor, 130gr, N150, 18" Barrel, 87°F', fontsize=14, fontweight='bold')

# Plot 1: Measured vs Predicted
ax1 = axes[0, 0]
ax1.scatter(measured, predicted, s=100, alpha=0.7, edgecolors='black', linewidths=1.5)
min_v = min(measured.min(), predicted.min()) - 10
max_v = max(measured.max(), predicted.max()) + 10
ax1.plot([min_v, max_v], [min_v, max_v], 'k--', label='Perfect fit', linewidth=2)
ax1.set_xlabel('Measured Velocity (fps)', fontsize=11, fontweight='bold')
ax1.set_ylabel('Predicted Velocity (fps)', fontsize=11, fontweight='bold')
ax1.set_title('Predicted vs Measured', fontsize=12, fontweight='bold')
ax1.legend(fontsize=10)
ax1.grid(True, alpha=0.3)
ax1.set_aspect('equal')

# Add R² text
ss_res = np.sum(residuals**2)
ss_tot = np.sum((measured - np.mean(measured))**2)
r_squared = 1 - (ss_res / ss_tot)
ax1.text(0.05, 0.95, f'R² = {r_squared:.4f}\nRMSE = {fit_result["rmse_velocity"]:.2f} fps',
         transform=ax1.transAxes, fontsize=10, verticalalignment='top',
         bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

# Plot 2: Residuals vs Charge Weight
ax2 = axes[0, 1]
ax2.scatter(charges, residuals, s=100, alpha=0.7, edgecolors='black', linewidths=1.5, c=residuals, cmap='RdYlGn_r')
ax2.axhline(y=0, color='k', linestyle='--', linewidth=2, label='Zero error')
ax2.set_xlabel('Charge Weight (grains)', fontsize=11, fontweight='bold')
ax2.set_ylabel('Residual (fps)', fontsize=11, fontweight='bold')
ax2.set_title('Residuals vs Charge Weight', fontsize=12, fontweight='bold')
ax2.legend(fontsize=10)
ax2.grid(True, alpha=0.3)

# Add trend line to show systematic bias
z = np.polyfit(charges, residuals, 1)
p = np.poly1d(z)
charge_line = np.linspace(charges.min(), charges.max(), 100)
ax2.plot(charge_line, p(charge_line), 'r-', linewidth=2, alpha=0.7, label=f'Trend: {z[0]:.1f}x + {z[1]:.1f}')
ax2.legend(fontsize=10)

# Plot 3: Vivacity Curve
ax3 = axes[1, 0]
Z_vals = np.linspace(0, 1, 101)
Lambda_vals = [calc_vivacity(Z, fit_result['Lambda_base'], fit_result['coeffs']) for Z in Z_vals]
ax3.plot(Z_vals, Lambda_vals, 'b-', linewidth=2.5, label='Fitted Λ(Z)')
ax3.axhline(y=fit_result['Lambda_base'], color='r', linestyle='--', linewidth=2, label=f'Lambda_base = {fit_result["Lambda_base"]:.6f}')
ax3.axhline(y=config.propellant.Lambda_base, color='g', linestyle=':', linewidth=2, label=f'Database = {config.propellant.Lambda_base:.6f}')
ax3.set_xlabel('Burn Fraction Z', fontsize=11, fontweight='bold')
ax3.set_ylabel('Vivacity Λ(Z)', fontsize=11, fontweight='bold')
ax3.set_title('Dynamic Vivacity Curve', fontsize=12, fontweight='bold')
ax3.legend(fontsize=10)
ax3.grid(True, alpha=0.3)
ax3.set_xlim(0, 1)
ax3.set_ylim(bottom=0)

# Add polynomial formula
a, b, c, d = fit_result['coeffs']
formula_text = f'Λ(Z) = {fit_result["Lambda_base"]:.4f} × ({a:.3f} + {b:.3f}Z + {c:.3f}Z² + {d:.3f}Z³)'
ax3.text(0.5, 0.95, formula_text, transform=ax3.transAxes, fontsize=9,
         verticalalignment='top', horizontalalignment='center',
         bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))

# Plot 4: Velocity vs Charge (with fit)
ax4 = axes[1, 1]
ax4.scatter(charges, measured, s=100, alpha=0.7, edgecolors='black', linewidths=1.5, label='Measured', zorder=3)
ax4.plot(charges, predicted, 'r-', linewidth=2.5, label='Fitted model', zorder=2)

# Add error bars if available
if 'velocity_sd' in load_data.columns:
    velocity_sd = load_data['velocity_sd'].values
    ax4.errorbar(charges, measured, yerr=velocity_sd, fmt='none', ecolor='gray', alpha=0.5, capsize=5, zorder=1)

ax4.set_xlabel('Charge Weight (grains)', fontsize=11, fontweight='bold')
ax4.set_ylabel('Muzzle Velocity (fps)', fontsize=11, fontweight='bold')
ax4.set_title('Velocity Ladder Fit', fontsize=12, fontweight='bold')
ax4.legend(fontsize=10)
ax4.grid(True, alpha=0.3)

# Add fit statistics
stats_text = f'RMSE: {fit_result["rmse_velocity"]:.2f} fps\nMean Error: {np.mean(residuals):.2f} fps\nStd Dev: {np.std(residuals):.2f} fps'
ax4.text(0.05, 0.95, stats_text, transform=ax4.transAxes, fontsize=9,
         verticalalignment='top',
         bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

plt.tight_layout()
plt.savefig('fit_diagnostics.png', dpi=150, bbox_inches='tight')
print("Saved fit_diagnostics.png")
plt.close()

# Create second figure for deeper analysis
fig2, axes2 = plt.subplots(1, 2, figsize=(14, 5))
fig2.suptitle('Advanced Fit Diagnostics', fontsize=14, fontweight='bold')

# Plot 5: Cumulative residual to show systematic bias
ax5 = axes2[0]
cumulative_residuals = np.cumsum(residuals)
ax5.plot(charges, cumulative_residuals, 'b-o', linewidth=2.5, markersize=8)
ax5.set_xlabel('Charge Weight (grains)', fontsize=11, fontweight='bold')
ax5.set_ylabel('Cumulative Residual (fps)', fontsize=11, fontweight='bold')
ax5.set_title('Cumulative Residual (Shows Systematic Bias)', fontsize=12, fontweight='bold')
ax5.grid(True, alpha=0.3)
ax5.axhline(y=0, color='k', linestyle='--', linewidth=1)

# Annotate trend
if cumulative_residuals[-1] < -20:
    ax5.text(0.05, 0.05, 'Negative trend:\nUnder-prediction\nat high charges',
             transform=ax5.transAxes, fontsize=10,
             bbox=dict(boxstyle='round', facecolor='salmon', alpha=0.7))
elif cumulative_residuals[-1] > 20:
    ax5.text(0.05, 0.95, 'Positive trend:\nOver-prediction\nat high charges',
             transform=ax5.transAxes, fontsize=10, verticalalignment='top',
             bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.7))

# Plot 6: Polynomial multiplier vs Z
ax6 = axes2[1]
poly_multipliers = [(a + b*Z + c*Z**2 + d*Z**3) for Z in Z_vals]
ax6.plot(Z_vals, poly_multipliers, 'g-', linewidth=2.5)
ax6.axhline(y=1.0, color='k', linestyle='--', linewidth=1, label='No modification')
ax6.set_xlabel('Burn Fraction Z', fontsize=11, fontweight='bold')
ax6.set_ylabel('Polynomial Multiplier', fontsize=11, fontweight='bold')
ax6.set_title('Vivacity Multiplier vs Burn Fraction', fontsize=12, fontweight='bold')
ax6.legend(fontsize=10)
ax6.grid(True, alpha=0.3)
ax6.set_xlim(0, 1)

# Shade regions
ax6.axhspan(1.0, max(poly_multipliers), alpha=0.2, color='green', label='Increased burn rate')
ax6.axhspan(0.0, 1.0, alpha=0.2, color='red', label='Decreased burn rate')

poly_text = f'At Z=0: {a:.3f}x\nAt Z=0.5: {a + b*0.5 + c*0.25 + d*0.125:.3f}x\nAt Z=1: {a+b+c+d:.3f}x'
ax6.text(0.95, 0.95, poly_text, transform=ax6.transAxes, fontsize=10,
         verticalalignment='top', horizontalalignment='right',
         bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.7))

plt.tight_layout()
plt.savefig('fit_diagnostics_advanced.png', dpi=150, bbox_inches='tight')
print("Saved fit_diagnostics_advanced.png")
plt.close()

print("\nDiagnostic plots created successfully!")
print("  - fit_diagnostics.png (main diagnostics)")
print("  - fit_diagnostics_advanced.png (advanced analysis)")
