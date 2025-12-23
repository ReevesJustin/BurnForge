"""Core ODE system definition and solve_ivp integration."""

import math
import numpy as np
from scipy.integrate import solve_ivp

from .props import BallisticsConfig
from .burn_rate import calc_vivacity
from .utils import GRAINS_TO_LB, GRAINS_H2O_TO_IN3, G_ACCEL, calc_muzzle_energy


def solve_ballistics(config: BallisticsConfig,
                     Lambda_override: float | None = None,
                     coeffs_override: tuple[float, float, float, float] | None = None,
                     method: str = 'DOP853',
                     return_trace: bool = False) -> dict:
    """Solve internal ballistics using adaptive ODE integration.

    Parameters
    ----------
    config : BallisticsConfig
        Complete ballistics configuration
    Lambda_override : float, optional
        Override base vivacity (for fitting)
    coeffs_override : tuple, optional
        Override polynomial coefficients (for fitting)
    method : str
        Integration method ('RK45', 'DOP853', 'Radau')
    return_trace : bool
        If True, return full time-series trajectory

    Returns
    -------
    dict
        Always returned: muzzle_velocity_fps, muzzle_energy_ft_lbs, peak_pressure_psi,
                        muzzle_pressure_psi, final_Z, total_time_s
        If final_Z = 1.0 (burnout occurred):
            burnout_distance_from_bolt_in (inches from bolt face where Z = 1.0)
        If final_Z < 1.0 (still burning at muzzle):
            muzzle_burn_percentage (percent of propellant consumed at muzzle)
        If return_trace=True, also includes: t, Z, P, v, x (arrays)
    """
    # Extract parameters
    m = config.bullet_mass_gr * GRAINS_TO_LB
    C = config.charge_mass_gr * GRAINS_TO_LB
    D = config.caliber_in
    A = math.pi * (D / 2)**2
    V_C = config.case_volume_gr_h2o * GRAINS_H2O_TO_IN3
    V_0 = V_C - (C / config.propellant.bulk_density)
    L_eff = config.effective_barrel_length_in
    COAL = config.cartridge_overall_length_in

    # Validate V_0
    if V_0 <= 0:
        raise ValueError(f"Initial volume V_0 = {V_0:.3f} in^3 is non-positive. "
                        f"Check case volume and charge mass.")

    # Temperature
    T_1 = (config.temperature_f - 32) * 5 / 9 + 273.15

    # Propellant properties
    Lambda_base = Lambda_override if Lambda_override is not None else config.propellant.Lambda_base
    poly_coeffs = coeffs_override if coeffs_override is not None else config.propellant.poly_coeffs
    gamma = config.propellant.gamma
    F = config.propellant.force
    T_0 = config.propellant.temp_0

    # Bullet properties
    s = config.bullet.s
    rho_p = config.bullet.rho_p

    # Derived parameters
    Theta = 2.5 * (m * s) / (D * rho_p)
    shot_start_pressure = Theta / A
    Phi = config.phi
    P_IN = config.p_initial_psi

    # State tracking
    peak_pressure = P_IN
    burnout_distance = None
    burnout_time = None
    P_const = None
    volume_at_burnout = None

    def ode_system(t: float, y: np.ndarray) -> np.ndarray:
        """ODE system: dy/dt for [Z, v, x].

        State vector y = [Z, v, x]
        Returns dy/dt = [dZ/dt, dv/dt, dx/dt]
        """
        Z, v, x = y

        # Clamp Z
        Z = max(0.0, min(1.0, Z))

        # Current volume
        volume = V_0 + A * x

        # Heat loss
        E_h_base = (0.38 * (T_0 - T_1) * D**1.5) / (1 + 0.6 * (D**2.175 / C**0.8375)) * 12
        E_h = E_h_base * Z

        # Effective mass
        m_eff = m + (C * Z / 3)

        # Kinetic energy
        kinetic_energy = (m_eff * v**2) / (2 * G_ACCEL)

        # Energy loss
        energy_loss = (gamma - 1) * (kinetic_energy + E_h + Theta * x)

        # Pressure calculation
        if Z >= 1.0 and P_const is not None:
            # Post-burnout: adiabatic expansion
            P = P_const / (volume ** gamma)
        else:
            # Pre-burnout: energy balance
            P = max(0, (C * Z * F - energy_loss) / volume) if volume > 0 else 0

        # Vivacity
        Lambda_Z = calc_vivacity(Z, Lambda_base, poly_coeffs)

        # Derivatives
        dZ_dt = Lambda_Z * P
        if P > shot_start_pressure and x < L_eff:
            dv_dt = (G_ACCEL / m_eff) * (A * Phi * P - Theta)
        else:
            dv_dt = 0.0
        dx_dt = v if x < L_eff else 0.0

        return np.array([dZ_dt, dv_dt, dx_dt])

    def burnout_event(t: float, y: np.ndarray) -> float:
        """Event function for burnout detection (Z = 1.0)."""
        return y[0] - 1.0

    burnout_event.terminal = True
    burnout_event.direction = 1  # Trigger on increasing Z

    def muzzle_event(t: float, y: np.ndarray) -> float:
        """Event function for muzzle exit (x = L_eff)."""
        return y[2] - L_eff

    muzzle_event.terminal = True
    muzzle_event.direction = 1  # Trigger on increasing x

    # Initial conditions: [Z, v, x]
    y0 = np.array([0.0, 0.0, 0.0])

    # Time span (generous upper bound)
    t_span = (0, 0.1)  # 100ms should be more than enough

    # Solve ODE
    sol = solve_ivp(
        ode_system,
        t_span,
        y0,
        method=method,
        events=[burnout_event, muzzle_event],
        dense_output=True,
        max_step=1e-5
    )

    if not sol.success:
        raise RuntimeError(f"ODE solver failed: {sol.message}")

    # Extract final state
    t_final = sol.t[-1]
    Z_final, v_final, x_final = sol.y[:, -1]

    # Track peak pressure during integration
    peak_pressure = P_IN
    for i in range(len(sol.t)):
        Z_i, v_i, x_i = sol.y[:, i]
        Z_i = max(0.0, min(1.0, Z_i))
        volume_i = V_0 + A * x_i
        E_h_base_i = (0.38 * (T_0 - T_1) * D**1.5) / (1 + 0.6 * (D**2.175 / C**0.8375)) * 12
        E_h_i = E_h_base_i * Z_i
        m_eff_i = m + (C * Z_i / 3)
        ke_i = (m_eff_i * v_i**2) / (2 * G_ACCEL)
        energy_loss_i = (gamma - 1) * (ke_i + E_h_i + Theta * x_i)

        if Z_i >= 1.0 and P_const is not None:
            P_i = P_const / (volume_i ** gamma)
        else:
            P_i = max(0, (C * Z_i * F - energy_loss_i) / volume_i) if volume_i > 0 else 0

        if P_i > peak_pressure:
            peak_pressure = P_i

        # Set P_const at burnout
        if Z_i >= 0.999 and P_const is None:
            P_const = P_i * (volume_i ** gamma)

    # Check for burnout event
    if sol.t_events[0].size > 0:  # Burnout event triggered
        burnout_time = sol.t_events[0][0]
        burnout_state = sol.sol(burnout_time)
        burnout_distance = burnout_state[2]  # x at burnout

    # Compute muzzle pressure
    Z_muzzle = Z_final
    volume_muzzle = V_0 + A * x_final
    E_h_base_muzzle = (0.38 * (T_0 - T_1) * D**1.5) / (1 + 0.6 * (D**2.175 / C**0.8375)) * 12
    E_h_muzzle = E_h_base_muzzle * Z_muzzle
    m_eff_muzzle = m + (C * Z_muzzle / 3)
    ke_muzzle = (m_eff_muzzle * v_final**2) / (2 * G_ACCEL)
    energy_loss_muzzle = (gamma - 1) * (ke_muzzle + E_h_muzzle + Theta * x_final)

    if Z_muzzle >= 1.0 and P_const is not None:
        muzzle_pressure = P_const / (volume_muzzle ** gamma)
    else:
        muzzle_pressure = max(0, (C * Z_muzzle * F - energy_loss_muzzle) / volume_muzzle) if volume_muzzle > 0 else 0

    # Convert velocity to fps
    muzzle_velocity_fps = v_final / 12

    # Calculate muzzle energy
    muzzle_energy = calc_muzzle_energy(config.bullet_mass_gr, muzzle_velocity_fps)

    # Build results dictionary
    results = {
        'muzzle_velocity_fps': muzzle_velocity_fps,
        'muzzle_energy_ft_lbs': muzzle_energy,
        'peak_pressure_psi': peak_pressure,
        'muzzle_pressure_psi': muzzle_pressure,
        'final_Z': Z_final,
        'total_time_s': t_final
    }

    # Add burnout-specific metrics
    if Z_final >= 0.999:  # Burnout occurred
        if burnout_distance is not None:
            results['burnout_distance_from_bolt_in'] = COAL + burnout_distance
        else:
            # Burnout happened but not detected by event (very close to muzzle)
            results['burnout_distance_from_bolt_in'] = COAL + x_final
    else:  # Still burning at muzzle
        results['muzzle_burn_percentage'] = Z_final * 100

    # Add trace if requested
    if return_trace:
        results['t'] = sol.t
        results['Z'] = sol.y[0, :]
        results['v'] = sol.y[1, :]
        results['x'] = sol.y[2, :]
        # Compute pressure trace
        P_trace = []
        for i in range(len(sol.t)):
            Z_i, v_i, x_i = sol.y[:, i]
            Z_i = max(0.0, min(1.0, Z_i))
            volume_i = V_0 + A * x_i
            E_h_base_i = (0.38 * (T_0 - T_1) * D**1.5) / (1 + 0.6 * (D**2.175 / C**0.8375)) * 12
            E_h_i = E_h_base_i * Z_i
            m_eff_i = m + (C * Z_i / 3)
            ke_i = (m_eff_i * v_i**2) / (2 * G_ACCEL)
            energy_loss_i = (gamma - 1) * (ke_i + E_h_i + Theta * x_i)

            if Z_i >= 1.0 and P_const is not None:
                P_i = P_const / (volume_i ** gamma)
            else:
                P_i = max(0, (C * Z_i * F - energy_loss_i) / volume_i) if volume_i > 0 else 0
            P_trace.append(P_i)
        results['P'] = np.array(P_trace)

    return results
