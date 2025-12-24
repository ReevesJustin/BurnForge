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
from .analysis.analysis import (
    burnout_scan_charge,
    burnout_scan_barrel,
    charge_ladder_analysis,
)
from .analysis.plotting import (
    plot_velocity_fit,
    plot_burnout_map,
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
    "burnout_scan_charge",
    "burnout_scan_barrel",
    "charge_ladder_analysis",
    "plot_velocity_fit",
    "plot_burnout_map",
]
