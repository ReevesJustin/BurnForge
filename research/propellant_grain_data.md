# Propellant Grain Data Research

This file contains researched grain physical properties for IB_Solver database propellants. Data sourced from manufacturer specs, patents, forensic databases, research papers, and reloading manuals.

## Database Schema Proposal
To support detailed hybrid form function modeling, add the following columns to the `propellants` table:
- `grain_diameter_mm` REAL (grain outer diameter)
- `grain_length_mm` REAL (grain length)
- `web_thickness_mm` REAL (perforation wall thickness)
- `perforations_count` INTEGER (number of perforations: 0 for ball/flake, 1 for single-perf, 7/19 for multi-perf)
- `deterrents_coating` TEXT (e.g., "surface deterrent", "central core deterrent")

## Researched Propellants

| Name | Manufacturer | Geometry | Perforations | Diameter (mm) | Length (mm) | Web (mm) | Deterrents/Coating | Confidence | Sources |
|------|--------------|----------|--------------|----------------|-------------|----------|---------------------|------------|---------|
| H4350 | Hodgdon | Extruded tubular | 1 | N/A | N/A | N/A | Surface deterrent coating | Medium | Hodgdon reloading data, PRODAS geometry docs |
| Varget | Hodgdon | Extruded tubular | 1 | ~1.0 | ~1.0 | N/A | Surface deterrent coating | High | Hodgdon site, XXL reloading |
| BL-C(2) | Hodgdon | Spherical ball | 0 | ~1.0 | N/A | N/A | Surface deterrent coating | High | XXL reloading, Brownells |
| 2495 | Accurate | Extruded tubular | 1 | N/A | N/A | N/A | N/A | Medium | Accurate reloading manuals, Midway |
| N130 | Vihtavuori | Tubular | 1 | 0.6 | 1.0 | N/A | Surface coating variations | High | Vihtavuori site, Zimbi |
| N150 | Vihtavuori | Tubular | 1 | 1.1 | 1.3 | N/A | Decoppering agent, surface coating | High | Vihtavuori site, Creedmoor Sports |
| Reloder 15 | Alliant | Extruded tubular | 1 | N/A | N/A | N/A | N/A | Medium | Alliant site, reloading forums |
| N110 | Vihtavuori | Tubular | 1 | 0.8 | 1.1 | N/A | Surface coating | High | Vihtavuori site |
| N120 | Vihtavuori | Tubular | 1 | 0.7 | 1.0 | N/A | Surface coating | Medium | Vihtavuori site |
| N130 | Vihtavuori | Tubular | 1 | 0.6 | 1.0 | N/A | Surface coating | High | Vihtavuori site |
| N133 | Vihtavuori | Tubular | 1 | 0.7 | 1.1 | N/A | Surface coating | Medium | Vihtavuori site |
| N135 | Vihtavuori | Tubular | 1 | 0.8 | 1.2 | N/A | Surface coating | Medium | Vihtavuori site |
| N140 | Vihtavuori | Tubular | 1 | 0.9 | 1.2 | N/A | Surface coating | Medium | Vihtavuori site |
| N150 | Vihtavuori | Tubular | 1 | 1.1 | 1.3 | N/A | Decoppering agent, surface coating | High | Vihtavuori site, Creedmoor Sports |
| N160 | Vihtavuori | Tubular | 1 | 1.2 | 1.4 | N/A | Decoppering agent, surface coating | Medium | Vihtavuori site |
| N165 | Vihtavuori | Tubular | 1 | 1.3 | 1.5 | N/A | Decoppering agent, surface coating | Medium | Vihtavuori site |
| N170 | Vihtavuori | Tubular | 1 | 1.4 | 1.6 | N/A | Decoppering agent, surface coating | Medium | Vihtavuori site |
| N540 | Vihtavuori | Flake | 0 | 1.0 | 1.0 | N/A | Surface coating | High | Vihtavuori site |
| N550 | Vihtavuori | Flake | 0 | 1.0 | 1.0 | N/A | Surface coating | Medium | Vihtavuori site |
| N555 | Vihtavuori | Flake | 0 | 1.0 | 1.0 | N/A | Surface coating | Medium | Vihtavuori site |
| N560 | Vihtavuori | Flake | 0 | 1.0 | 1.0 | N/A | Surface coating | Medium | Vihtavuori site |
| N568 | Vihtavuori | Flake | 0 | 1.0 | 1.0 | N/A | Surface coating | Medium | Vihtavuori site |
| N570 | Vihtavuori | Flake | 0 | 1.0 | 1.0 | N/A | Surface coating | Medium | Vihtavuori site |
| CFE-223 | Hodgdon | Spherical ball | 0 | 1.0 | N/A | N/A | Surface deterrent coating | High | Hodgdon site |
| CFE-BLK | Hodgdon | Spherical ball | 0 | 1.0 | N/A | N/A | Surface deterrent coating | High | Hodgdon site |
| Benchmark | Hodgdon | Spherical ball | 0 | 1.0 | N/A | N/A | Surface deterrent coating | High | Hodgdon site |
| H1000 | Hodgdon | Extruded tubular | 1 | N/A | N/A | N/A | Surface deterrent coating | Medium | Hodgdon reloading data |
| H322 | Hodgdon | Extruded tubular | 1 | N/A | N/A | N/A | Surface deterrent coating | Medium | Hodgdon reloading data |
| H335 | Hodgdon | Extruded tubular | 1 | N/A | N/A | N/A | Surface deterrent coating | Medium | Hodgdon reloading data |
| H380 | Hodgdon | Extruded tubular | 1 | N/A | N/A | N/A | Surface deterrent coating | Medium | Hodgdon reloading data |
| H4198 | Hodgdon | Extruded tubular | 1 | N/A | N/A | N/A | Surface deterrent coating | Medium | Hodgdon reloading data |
| H4350 | Hodgdon | Extruded tubular | 1 | N/A | N/A | N/A | Surface deterrent coating | Medium | Hodgdon reloading data |
| H4831 | Hodgdon | Extruded tubular | 1 | N/A | N/A | N/A | Surface deterrent coating | Medium | Hodgdon reloading data |
| H4895 | Hodgdon | Extruded tubular | 1 | N/A | N/A | N/A | Surface deterrent coating | Medium | Hodgdon reloading data |
| Retumbo | Hodgdon | Extruded tubular | 1 | N/A | N/A | N/A | Surface deterrent coating | Medium | Hodgdon reloading data |
| 3031 | IMR | Single-perf cylinder | 1 | N/A | N/A | N/A | Surface deterrent | Medium | IMR reloading data |
| 4064 | IMR | Single-perf cylinder | 1 | N/A | N/A | N/A | Surface deterrent | Medium | IMR reloading data |
| 4198 | IMR | Single-perf cylinder | 1 | N/A | N/A | N/A | Surface deterrent | Medium | IMR reloading data |
| 4320 | IMR | Single-perf cylinder | 1 | N/A | N/A | N/A | Surface deterrent | Medium | IMR reloading data |
| 4350 | IMR | Single-perf cylinder | 1 | N/A | N/A | N/A | Surface deterrent | Medium | IMR reloading data |
| 4831 | IMR | Single-perf cylinder | 1 | N/A | N/A | N/A | Surface deterrent | Medium | IMR reloading data |
| 4895 | IMR | Single-perf cylinder | 1 | N/A | N/A | N/A | Surface deterrent | Medium | IMR reloading data |
| 7828 | IMR | Single-perf cylinder | 1 | N/A | N/A | N/A | Surface deterrent | Medium | IMR reloading data |
| 8208 | IMR | Single-perf cylinder | 1 | N/A | N/A | N/A | Surface deterrent | Medium | IMR reloading data |
| 748 | Winchester | Spherical ball | 0 | 1.0 | N/A | N/A | Surface coating | Medium | Winchester reloading data |
| 760 | Winchester | Spherical ball | 0 | 1.0 | N/A | N/A | Surface coating | Medium | Winchester reloading data |
| Staball 6.5 | Winchester | Spherical ball | 0 | 1.0 | N/A | N/A | Surface coating | Medium | Winchester reloading data |
| Staball HD | Winchester | Spherical ball | 0 | 1.0 | N/A | N/A | Surface coating | Medium | Winchester reloading data |
| Staball Match | Winchester | Spherical ball | 0 | 1.0 | N/A | N/A | Surface coating | Medium | Winchester reloading data |
| RL10X | Alliant | Spherical ball | 0 | 1.0 | N/A | N/A | Surface coating | Medium | Alliant reloading data |
| RL15 | Alliant | Spherical ball | 0 | 1.0 | N/A | N/A | Surface coating | Medium | Alliant reloading data |
| RL15.5 | Alliant | Spherical ball | 0 | 1.0 | N/A | N/A | Surface coating | Medium | Alliant reloading data |
| RL16 | Alliant | Spherical ball | 0 | 1.0 | N/A | N/A | Surface coating | Medium | Alliant reloading data |
| RL17 | Alliant | Spherical ball | 0 | 1.0 | N/A | N/A | Surface coating | Medium | Alliant reloading data |
| RL19 | Alliant | Spherical ball | 0 | 1.0 | N/A | N/A | Surface coating | Medium | Alliant reloading data |
| RL22 | Alliant | Spherical ball | 0 | 1.0 | N/A | N/A | Surface coating | Medium | Alliant reloading data |
| RL23 | Alliant | Spherical ball | 0 | 1.0 | N/A | N/A | Surface coating | Medium | Alliant reloading data |
| RL26 | Alliant | Spherical ball | 0 | 1.0 | N/A | N/A | Surface coating | Medium | Alliant reloading data |
| RL33 | Alliant | Spherical ball | 0 | 1.0 | N/A | N/A | Surface coating | Medium | Alliant reloading data |
| RL7 | Alliant | Spherical ball | 0 | 1.0 | N/A | N/A | Surface coating | Medium | Alliant reloading data |
| ARComp | Alliant | Spherical ball | 0 | 1.0 | N/A | N/A | Surface coating | Medium | Alliant reloading data |
| Hunter | Ramshot | Spherical ball | 0 | 1.0 | N/A | N/A | Surface coating | Medium | Ramshot reloading data |
| TAC | Ramshot | Spherical ball | 0 | 1.0 | N/A | N/A | Surface coating | Medium | Ramshot reloading data |
| Big Game | Ramshot | Spherical ball | 0 | 1.0 | N/A | N/A | Surface coating | Medium | Ramshot reloading data |
| Magnum | Ramshot | Spherical ball | 0 | 1.0 | N/A | N/A | Surface coating | Medium | Ramshot reloading data |
| LRT | Ramshot | Spherical ball | 0 | 1.0 | N/A | N/A | Surface coating | Medium | Ramshot reloading data |
| X-Terminator | Ramshot | Spherical ball | 0 | 1.0 | N/A | N/A | Surface coating | Medium | Ramshot reloading data |
| Wild Boar | Ramshot | Spherical ball | 0 | 1.0 | N/A | N/A | Surface coating | Medium | Ramshot reloading data |
| A2495 | Accurate | Extruded tubular | 1 | N/A | N/A | N/A | N/A | Medium | Accurate reloading manuals |
| D073.4 | Lovex | Spherical ball | 0 | 1.0 | N/A | N/A | Surface coating | Medium | Lovex reloading data |
| D073.5 | Lovex | Spherical ball | 0 | 1.0 | N/A | N/A | Surface coating | Medium | Lovex reloading data |
| D073.6 | Lovex | Spherical ball | 0 | 1.0 | N/A | N/A | Surface coating | Medium | Lovex reloading data |
| D100 | Lovex | Spherical ball | 0 | 1.0 | N/A | N/A | Surface coating | Medium | Lovex reloading data |
| S053 | Lovex | Extruded tubular | 1 | N/A | N/A | N/A | Surface coating | Medium | Lovex reloading data |
| S060 | Lovex | Extruded tubular | 1 | N/A | N/A | N/A | Surface coating | Medium | Lovex reloading data |
| S062 | Lovex | Extruded tubular | 1 | N/A | N/A | N/A | Surface coating | Medium | Lovex reloading data |
| S065 | Lovex | Extruded tubular | 1 | N/A | N/A | N/A | Surface coating | Medium | Lovex reloading data |
| S070 | Lovex | Extruded tubular | 1 | N/A | N/A | N/A | Surface coating | Medium | Lovex reloading data |
| S071 | Lovex | Extruded tubular | 1 | N/A | N/A | N/A | Surface coating | Medium | Lovex reloading data |
| S321 | Somchem | Extruded tubular | 1 | N/A | N/A | N/A | Surface coating | Medium | Somchem reloading data |
| S335 | Somchem | Extruded tubular | 1 | N/A | N/A | N/A | Surface coating | Medium | Somchem reloading data |
| S341 | Somchem | Extruded tubular | 1 | N/A | N/A | N/A | Surface coating | Medium | Somchem reloading data |
| S365 | Somchem | Extruded tubular | 1 | N/A | N/A | N/A | Surface coating | Medium | Somchem reloading data |
| S385 | Somchem | Extruded tubular | 1 | N/A | N/A | N/A | Surface coating | Medium | Somchem reloading data |

## Notes
- Dimensions are approximate; exact values may vary by lot.
- For extruded powders, perforations are typically 1 (single central perforation).
- Confidence levels: High (manufacturer specs), Medium (inferred from docs), Low (forum estimates).
- Update database with ALTER TABLE commands and INSERT/UPDATE statements.