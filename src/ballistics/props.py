"""Propellant and bullet property dataclasses."""

from dataclasses import dataclass


@dataclass
class PropellantProperties:
    """Propellant thermochemical and burn rate properties."""
    name: str
    vivacity: float              # s⁻¹ per 100 bar
    base: str                    # 'S' or 'D'
    force: float                 # ft-lbf/lbm
    temp_0: float                # K
    gamma: float                 # Specific heat ratio (computed from base)
    bulk_density: float          # lbm/in³
    Lambda_base: float           # Vivacity normalized (vivacity / 1450)
    poly_coeffs: tuple[float, float, float, float]  # (a, b, c, d)

    @classmethod
    def from_database(cls, name: str, db_path: str | None = None):
        """Load propellant from database.

        Parameters
        ----------
        name : str
            Propellant name
        db_path : str, optional
            Path to database (uses default if None)

        Returns
        -------
        PropellantProperties
            Propellant properties loaded from database
        """
        from . import database
        props = database.get_propellant(name, db_path)

        # Compute gamma from base
        gamma = 1.24 if props['base'] == 'S' else 1.22

        # Normalize vivacity: Lambda_base for use with PSI
        # If vivacity is in s^-1 per 100 bar, and 100 bar ≈ 1450 PSI,
        # then Lambda_base_PSI = vivacity / 1450 gives s^-1 per PSI
        Lambda_base = props['vivacity'] / 1450

        # Extract polynomial coefficients
        poly_coeffs = (props['poly_a'], props['poly_b'],
                       props['poly_c'], props['poly_d'])

        return cls(
            name=name,
            vivacity=props['vivacity'],
            base=props['base'],
            force=props['force'],
            temp_0=props['temp_0'],
            gamma=gamma,
            bulk_density=props['bulk_density'] if props['bulk_density'] else 0.0584,
            Lambda_base=Lambda_base,
            poly_coeffs=poly_coeffs
        )


@dataclass
class BulletProperties:
    """Bullet material properties."""
    name: str
    s: float                     # Strength factor
    rho_p: float                 # lbm/in³
    p_initial_psi: float = 3626.0  # Initial pressure for copper jacketed bullets

    @classmethod
    def from_database(cls, name: str, db_path: str | None = None):
        """Load bullet type from database.

        Parameters
        ----------
        name : str
            Bullet type name
        db_path : str, optional
            Path to database (uses default if None)

        Returns
        -------
        BulletProperties
            Bullet properties loaded from database
        """
        from . import database
        props = database.get_bullet_type(name, db_path)

        # Set initial pressure based on bullet type
        # Copper jacketed bullets: 3626 psi (250 bar)
        # Other types can be added as needed
        p_initial = 3626.0  # Default for copper jacketed

        return cls(
            name=name,
            s=props['s'],
            rho_p=props['rho_p'],
            p_initial_psi=p_initial
        )


@dataclass
class BallisticsConfig:
    """Complete configuration for ballistics solver."""
    bullet_mass_gr: float
    charge_mass_gr: float
    caliber_in: float
    case_volume_gr_h2o: float
    barrel_length_in: float
    cartridge_overall_length_in: float  # COAL - measured from bolt face to bullet tip
    propellant: PropellantProperties
    bullet: BulletProperties
    temperature_f: float = 70.0
    phi: float = 0.9              # Piezometric coefficient
    p_initial_psi: float | None = None  # If None, uses bullet.p_initial_psi

    def __post_init__(self):
        """Set initial pressure from bullet if not provided."""
        if self.p_initial_psi is None:
            self.p_initial_psi = self.bullet.p_initial_psi

    @property
    def effective_barrel_length_in(self) -> float:
        """Calculate effective barrel length for bullet travel.

        Returns
        -------
        float
            Effective barrel length in inches (barrel_length - COAL)
        """
        return self.barrel_length_in - self.cartridge_overall_length_in
