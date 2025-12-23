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
    """Complete configuration for ballistics solver.

    Heat Loss Model Parameters
    ---------------------------
    The solver supports two heat loss models:

    1. "empirical": Legacy empirical formula based on bore diameter and charge mass.
       Uses fixed exponents and provides reasonable accuracy for standard loads.

    2. "convective": Modern time-varying convective heat transfer coefficient h(t).
       Physically motivated model that scales with instantaneous pressure, temperature,
       and gas velocity. Provides superior accuracy for extreme charges and eliminates
       systematic fitting bias. This is the recommended default.

    Convective Model Physics:
        h(t) = h_base × (P(t)/P_ref)^α × (T_gas(t)/T_ref)^β × (v_gas(t)/v_ref)^γ

        where h_base is the primary calibration parameter (W/m²·K), and α, β, γ
        are scaling exponents from turbulent convection literature.

    Secondary Work Coefficient
    ---------------------------
    Controls the effective mass of propellant gas entrained with the projectile.
    Modern form: φ_eff = 1 + (C × Z)/(μ × m_bullet)

    where μ ∈ [2.2, 3.8] (default 3.0) represents the reciprocal of the gas
    entrainment fraction. This replaces the outdated fixed "1/3 rule" and provides
    improved physical accuracy while remaining calibratable from velocity data.
    """
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

    # Heat loss model selection and parameters
    heat_loss_model: str = "convective"  # "empirical" or "convective"
    h_base: float = 2000.0        # Base heat transfer coefficient (W/m²·K), range: 500-5000
    h_alpha: float = 0.8          # Pressure scaling exponent (literature: 0.7-0.85)
    h_beta: float = 0.3           # Temperature scaling exponent (literature: 0.25-0.35)
    h_gamma: float = 0.3          # Velocity scaling exponent (literature: 0.2-0.4)
    T_wall_K: float = 500.0       # Barrel wall temperature (K), typical: 400-600
    P_ref_psi: float = 10000.0    # Reference pressure for h(t) scaling (10000 psi = ~690 bar)
    T_ref_K: float = 2500.0       # Reference temperature for h(t) scaling (K)
    v_ref_in_s: float = 1200.0    # Reference gas velocity for h(t) scaling (in/s, ~100 m/s)

    # Secondary work coefficient (modern formulation)
    secondary_work_mu: float = 3.0  # Gas entrainment reciprocal, range: [2.2, 3.8]

    def __post_init__(self):
        """Validate configuration parameters."""
        if self.p_initial_psi is None:
            self.p_initial_psi = self.bullet.p_initial_psi

        # Validate heat loss model
        if self.heat_loss_model not in ("empirical", "convective"):
            raise ValueError(f"heat_loss_model must be 'empirical' or 'convective', "
                           f"got '{self.heat_loss_model}'")

        # Validate convective model parameters
        if self.heat_loss_model == "convective":
            if self.h_base <= 0:
                raise ValueError(f"h_base must be positive, got {self.h_base}")
            if self.T_wall_K <= 0:
                raise ValueError(f"T_wall_K must be positive, got {self.T_wall_K}")
            if self.P_ref_psi <= 0:
                raise ValueError(f"P_ref_psi must be positive, got {self.P_ref_psi}")
            if self.T_ref_K <= 0:
                raise ValueError(f"T_ref_K must be positive, got {self.T_ref_K}")
            if self.v_ref_in_s <= 0:
                raise ValueError(f"v_ref_in_s must be positive, got {self.v_ref_in_s}")

        # Validate secondary work coefficient
        if self.secondary_work_mu <= 0:
            raise ValueError(f"secondary_work_mu must be positive, got {self.secondary_work_mu}")

    @property
    def effective_barrel_length_in(self) -> float:
        """Calculate effective barrel length for bullet travel.

        Returns
        -------
        float
            Effective barrel length in inches (barrel_length - COAL)
        """
        return self.barrel_length_in - self.cartridge_overall_length_in
