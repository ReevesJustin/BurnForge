"""Command-line interface for BurnForge ballistics calculations.

This module provides a Typer-based CLI for fitting, simulation, and analysis
of internal ballistics problems.
"""

import typer
from pathlib import Path
from typing import Optional

# Import core modules
from ballistics import (
    load_grt_project,
    metadata_to_config,
    fit_vivacity_polynomial,
)
from ballistics.core.solver import solve_ballistics
from ballistics.analysis.analysis import (
    burnout_scan_charge,
    burnout_scan_barrel,
)
from ballistics.analysis.plotting import (
    plot_burnout_map,
)

app = typer.Typer(help="BurnForge - Internal Ballistics Solver")


@app.command()
def fit(
    grt_file: Path = typer.Argument(..., help="Path to GRT load file"),
    db_path: Optional[Path] = typer.Option(None, help="Database path override"),
    verbose: bool = typer.Option(True, help="Show fitting progress"),
    output: Optional[Path] = typer.Option(None, help="Save fit results to JSON"),
):
    """Fit vivacity parameters from GRT chronograph data."""
    typer.echo(f"Loading GRT file: {grt_file}")

    try:
        metadata, load_data = load_grt_project(str(grt_file))
        config = metadata_to_config(metadata)

        typer.echo(f"Fitting {len(load_data)} data points...")
        fit_results = fit_vivacity_polynomial(
            load_data,
            config,
            verbose=verbose,
            fit_h_base=True,
            fit_temp_sensitivity=True,
            fit_start_pressure=True,
            fit_bore_friction=True,
        )

        typer.echo(f"Fitted Lambda_base: {fit_results['Lambda_base']:.6f}")
        typer.echo(f"Coefficients: {fit_results['coeffs']}")
        typer.echo(f"RMSE: {fit_results['rmse_velocity']:.1f} fps")

        if output:
            import json

            with open(output, "w") as f:
                json.dump(fit_results, f, indent=2, default=str)
            typer.echo(f"Results saved to {output}")

    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def simulate(
    grt_file: Path = typer.Argument(..., help="Path to GRT load file"),
    charge: Optional[float] = typer.Option(
        None, help="Charge weight override (grains)"
    ),
    output: Optional[Path] = typer.Option(None, help="Save results to JSON"),
):
    """Simulate single shot with current configuration."""
    typer.echo(f"Loading GRT file: {grt_file}")

    try:
        metadata, _ = load_grt_project(str(grt_file))
        config = metadata_to_config(metadata)

        if charge is not None:
            config.charge_mass_gr = charge

        typer.echo("Simulating shot...")
        results = solve_ballistics(config)

        typer.echo(f"Muzzle Velocity: {results['muzzle_velocity_fps']:.0f} fps")
        typer.echo(f"Peak Pressure: {results['peak_pressure_psi']:.0f} psi")
        typer.echo(f"Final Z: {results['final_Z']:.3f}")

        if output:
            import json

            with open(output, "w") as f:
                json.dump(results, f, indent=2, default=str)
            typer.echo(f"Results saved to {output}")

    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def scan_charge(
    grt_file: Path = typer.Argument(..., help="Path to GRT load file"),
    min_charge: float = typer.Option(..., help="Minimum charge (grains)"),
    max_charge: float = typer.Option(..., help="Maximum charge (grains)"),
    n_points: int = typer.Option(20, help="Number of points"),
    output: Optional[Path] = typer.Option(None, help="Save results to CSV"),
    plot: Optional[Path] = typer.Option(None, help="Save plot to PNG"),
):
    """Scan charge weights and analyze burnout characteristics."""
    typer.echo(f"Loading GRT file: {grt_file}")

    try:
        metadata, _ = load_grt_project(str(grt_file))
        config = metadata_to_config(metadata)

        typer.echo(
            f"Scanning {n_points} charges from {min_charge} to {max_charge} grains..."
        )
        results_df = burnout_scan_charge(config, (min_charge, max_charge), n_points)

        typer.echo(
            f"Scan complete. Max velocity: {results_df['muzzle_velocity_fps'].max():.0f} fps"
        )

        if output:
            results_df.to_csv(output, index=False)
            typer.echo(f"Results saved to {output}")

        if plot:
            plot_burnout_map(results_df, x_col="charge_grains", save_path=str(plot))
            typer.echo(f"Plot saved to {plot}")

    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def scan_barrel(
    grt_file: Path = typer.Argument(..., help="Path to GRT load file"),
    min_barrel: float = typer.Option(..., help="Minimum barrel length (inches)"),
    max_barrel: float = typer.Option(..., help="Maximum barrel length (inches)"),
    n_points: int = typer.Option(20, help="Number of points"),
    output: Optional[Path] = typer.Option(None, help="Save results to CSV"),
    plot: Optional[Path] = typer.Option(None, help="Save plot to PNG"),
):
    """Scan barrel lengths and analyze burnout characteristics."""
    typer.echo(f"Loading GRT file: {grt_file}")

    try:
        metadata, _ = load_grt_project(str(grt_file))
        config = metadata_to_config(metadata)

        typer.echo(
            f"Scanning {n_points} barrel lengths from {min_barrel} to {max_barrel} inches..."
        )
        results_df = burnout_scan_barrel(config, (min_barrel, max_barrel), n_points)

        typer.echo(
            f"Scan complete. Max velocity: {results_df['muzzle_velocity_fps'].max():.0f} fps"
        )

        if output:
            results_df.to_csv(output, index=False)
            typer.echo(f"Results saved to {output}")

        if plot:
            plot_burnout_map(results_df, x_col="barrel_length_in", save_path=str(plot))
            typer.echo(f"Plot saved to {plot}")

    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def import_grt(
    grt_file: Path = typer.Argument(..., help="Path to GRT load file"),
    db_path: Optional[Path] = typer.Option(None, help="Database path"),
):
    """Import GRT file data into database."""
    typer.echo(f"Importing GRT file: {grt_file}")

    try:
        # TODO: Implement database import functionality
        typer.echo("Database import not yet implemented")
        raise typer.Exit(1)

    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
