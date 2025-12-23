"""Internal ballistics solver package."""

__version__ = "2.0.0"

# Re-export key functions for convenience
from .solver import solve_ballistics
from .props import PropellantProperties, BulletProperties, BallisticsConfig
from .database import (
    get_propellant,
    get_bullet_type,
    list_propellants,
    update_propellant_coefficients
)

__all__ = [
    'solve_ballistics',
    'PropellantProperties',
    'BulletProperties',
    'BallisticsConfig',
    'get_propellant',
    'get_bullet_type',
    'list_propellants',
    'update_propellant_coefficients',
]
