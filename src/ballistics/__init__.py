"""Internal ballistics solver package."""

__version__ = "2.0.0"

# Re-export key functions for convenience
from .core.solver import solve_ballistics
from .core.props import PropellantProperties, BulletProperties, BallisticsConfig
from .database.database import (
    get_propellant,
    get_bullet_type,
    list_propellants,
    update_propellant_coefficients,
)
from .fitting.fitting import fit_vivacity_polynomial, fit_vivacity_sequential
from .io.io import (
    load_chronograph_csv,
    load_grt_project,
    metadata_to_config,
    export_fit_results,
)

__all__ = [
    "solve_ballistics",
    "PropellantProperties",
    "BulletProperties",
    "BallisticsConfig",
    "get_propellant",
    "get_bullet_type",
    "list_propellants",
    "update_propellant_coefficients",
    "fit_vivacity_polynomial",
    "fit_vivacity_sequential",
    "load_chronograph_csv",
    "load_grt_project",
    "metadata_to_config",
    "export_fit_results",
]
