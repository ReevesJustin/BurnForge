"""Unit conversions, physical constants, and validation helpers."""

# Physical constants
GRAINS_TO_LB = 1 / 7000
GRAINS_H2O_TO_IN3 = 1 / 252.9
G_ACCEL = 386.4  # in/s²
PSI_TO_BAR = 0.0689476
BAR_TO_PSI = 14.5038
MM_TO_IN = 1 / 25.4
GRAMS_TO_GRAINS = 15.432358
KG_TO_GRAINS = 15432.358
CM3_TO_GRAINS_H2O = 15.432358  # 1 cm³ H₂O ≈ 15.432 grains
MS_TO_FPS = 3.28084


def fahrenheit_to_kelvin(temp_f: float) -> float:
    """Convert °F to K.

    Parameters
    ----------
    temp_f : float
        Temperature in Fahrenheit

    Returns
    -------
    float
        Temperature in Kelvin
    """
    return (temp_f - 32) * 5 / 9 + 273.15


def grains_to_kg(grains: float) -> float:
    """Convert grains to kilograms.

    Parameters
    ----------
    grains : float
        Mass in grains

    Returns
    -------
    float
        Mass in kilograms
    """
    return grains / KG_TO_GRAINS


def fps_to_ms(fps: float) -> float:
    """Convert ft/s to m/s.

    Parameters
    ----------
    fps : float
        Velocity in ft/s

    Returns
    -------
    float
        Velocity in m/s
    """
    return fps / MS_TO_FPS


def calc_muzzle_energy(bullet_mass_gr: float, muzzle_velocity_fps: float) -> float:
    """Calculate muzzle energy in ft-lbs.

    Parameters
    ----------
    bullet_mass_gr : float
        Bullet mass in grains
    muzzle_velocity_fps : float
        Muzzle velocity in ft/s

    Returns
    -------
    float
        Muzzle energy in ft-lbs
        Formula: E = (m_lb * v²) / (2 * g) where g = 32.174 ft/s²
    """
    m_lb = bullet_mass_gr * GRAINS_TO_LB
    return (m_lb * muzzle_velocity_fps ** 2) / (2 * 32.174)


def validate_positive(*args, param_names: list[str]) -> None:
    """Validate that all parameters are positive, raise ValueError if not.

    Parameters
    ----------
    *args
        Values to validate
    param_names : list[str]
        Names of parameters for error message

    Raises
    ------
    ValueError
        If any parameter is not positive
    """
    for value, name in zip(args, param_names):
        if value <= 0:
            raise ValueError(f"{name} must be positive, got {value}")


def validate_range(value: float, min_val: float, max_val: float, name: str) -> None:
    """Validate that value is within [min_val, max_val].

    Parameters
    ----------
    value : float
        Value to validate
    min_val : float
        Minimum allowed value
    max_val : float
        Maximum allowed value
    name : str
        Parameter name for error message

    Raises
    ------
    ValueError
        If value is outside the specified range
    """
    if not (min_val <= value <= max_val):
        raise ValueError(f"{name} must be in [{min_val}, {max_val}], got {value}")
