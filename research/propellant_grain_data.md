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

## Notes
- Dimensions are approximate; exact values may vary by lot.
- For extruded powders, perforations are typically 1 (single central perforation).
- Confidence levels: High (manufacturer specs), Medium (inferred from docs), Low (forum estimates).
- Update database with ALTER TABLE commands and INSERT/UPDATE statements.