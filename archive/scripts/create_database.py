#!/usr/bin/env python3
# Script to create and populate SQLite database with propellant and bullet data, including polynomial coefficients

import sqlite3

# Database version
DB_VERSION = "1.2"  # Updated for polynomial coefficients

# Propellant data organized by manufacturer with default polynomial coefficients
PROPELLANTS = {
    "Alliant": {
        "RL7": {"vivacity": 73.0, "base": "D", "F": 3950000, "T_0": 3200, "temp_coeff_v": None, "temp_coeff_p": None, "bulk_density": None, "poly_a": 1.0, "poly_b": -1.0, "poly_c": 0.0, "poly_d": 0.0},
        "RL10X": {"vivacity": 66.9, "base": "D", "F": 3950000, "T_0": 3200, "temp_coeff_v": None, "temp_coeff_p": None, "bulk_density": None, "poly_a": 1.0, "poly_b": -1.0, "poly_c": 0.0, "poly_d": 0.0},
        "ARComp": {"vivacity": 62.5, "base": "D", "F": 3950000, "T_0": 3200, "temp_coeff_v": None, "temp_coeff_p": None, "bulk_density": None, "poly_a": 1.0, "poly_b": -1.0, "poly_c": 0.0, "poly_d": 0.0},
        "RL15.5": {"vivacity": 58.4, "base": "D", "F": 3950000, "T_0": 3200, "temp_coeff_v": None, "temp_coeff_p": None, "bulk_density": None, "poly_a": 1.0, "poly_b": -1.0, "poly_c": 0.0, "poly_d": 0.0},
        "RL15": {"vivacity": 51.9, "base": "D", "F": 3950000, "T_0": 3200, "temp_coeff_v": None, "temp_coeff_p": None, "bulk_density": None, "poly_a": 1.0, "poly_b": -1.0, "poly_c": 0.0, "poly_d": 0.0},
        "2000-MR": {"vivacity": 51.1, "base": "D", "F": 3950000, "T_0": 3200, "temp_coeff_v": None, "temp_coeff_p": None, "bulk_density": None, "poly_a": 1.0, "poly_b": -1.0, "poly_c": 0.0, "poly_d": 0.0},
        "RL17": {"vivacity": 48.9, "base": "D", "F": 3950000, "T_0": 3200, "temp_coeff_v": None, "temp_coeff_p": None, "bulk_density": None, "poly_a": 1.0, "poly_b": -1.0, "poly_c": 0.0, "poly_d": 0.0},
        "RL16": {"vivacity": 46.3, "base": "D", "F": 3950000, "T_0": 3200, "temp_coeff_v": None, "temp_coeff_p": None, "bulk_density": None, "poly_a": 1.0, "poly_b": -1.0, "poly_c": 0.0, "poly_d": 0.0},
        "RL23": {"vivacity": 42.0, "base": "D", "F": 3950000, "T_0": 3200, "temp_coeff_v": None, "temp_coeff_p": None, "bulk_density": None, "poly_a": 1.0, "poly_b": -1.0, "poly_c": 0.0, "poly_d": 0.0},
        "RL19": {"vivacity": 41.2, "base": "D", "F": 3950000, "T_0": 3200, "temp_coeff_v": None, "temp_coeff_p": None, "bulk_density": None, "poly_a": 1.0, "poly_b": -1.0, "poly_c": 0.0, "poly_d": 0.0},
        "RL22": {"vivacity": 40.3, "base": "D", "F": 3950000, "T_0": 3200, "temp_coeff_v": None, "temp_coeff_p": None, "bulk_density": None, "poly_a": 1.0, "poly_b": -1.0, "poly_c": 0.0, "poly_d": 0.0},
        "RL26": {"vivacity": 39.5, "base": "D", "F": 3950000, "T_0": 3200, "temp_coeff_v": None, "temp_coeff_p": None, "bulk_density": None, "poly_a": 1.0, "poly_b": -1.0, "poly_c": 0.0, "poly_d": 0.0},
        "RL33": {"vivacity": 31.8, "base": "D", "F": 3950000, "T_0": 3200, "temp_coeff_v": None, "temp_coeff_p": None, "bulk_density": None, "poly_a": 1.0, "poly_b": -1.0, "poly_c": 0.0, "poly_d": 0.0},
    },
    "Hodgdon": {
        "H4198": {"vivacity": 91.2, "base": "S", "F": 3650000, "T_0": 3000, "temp_coeff_v": None, "temp_coeff_p": None, "bulk_density": None, "poly_a": 1.0, "poly_b": -1.0, "poly_c": 0.0, "poly_d": 0.0},
        "H322": {"vivacity": 81.3, "base": "S", "F": 3650000, "T_0": 3000, "temp_coeff_v": None, "temp_coeff_p": None, "bulk_density": None, "poly_a": 1.0, "poly_b": -1.0, "poly_c": 0.0, "poly_d": 0.0},
        "Benchmark": {"vivacity": 70.8, "base": "S", "F": 3650000, "T_0": 3000, "temp_coeff_v": None, "temp_coeff_p": None, "bulk_density": None, "poly_a": 1.0, "poly_b": -1.0, "poly_c": 0.0, "poly_d": 0.0},
        "H4895": {"vivacity": 69.5, "base": "S", "F": 3650000, "T_0": 3000, "temp_coeff_v": None, "temp_coeff_p": None, "bulk_density": None, "poly_a": 1.0, "poly_b": -1.0, "poly_c": 0.0, "poly_d": 0.0},
        "Varget": {"vivacity": 63.5, "base": "S", "F": 3650000, "T_0": 3000, "temp_coeff_v": None, "temp_coeff_p": None, "bulk_density": None, "poly_a": 1.0, "poly_b": -1.0, "poly_c": 0.0, "poly_d": 0.0},
        "CFE-223": {"vivacity": 61.8, "base": "S", "F": 3650000, "T_0": 3000, "temp_coeff_v": None, "temp_coeff_p": None, "bulk_density": None, "poly_a": 1.0, "poly_b": -1.0, "poly_c": 0.0, "poly_d": 0.0},
        "H4350": {"vivacity": 51.9, "base": "S", "F": 3650000, "T_0": 3000, "temp_coeff_v": None, "temp_coeff_p": None, "bulk_density": None, "poly_a": 1.0, "poly_b": -1.0, "poly_c": 0.0, "poly_d": 0.0},
        "H4831": {"vivacity": 45.5, "base": "S", "F": 3650000, "T_0": 3000, "temp_coeff_v": None, "temp_coeff_p": None, "bulk_density": None, "poly_a": 1.0, "poly_b": -1.0, "poly_c": 0.0, "poly_d": 0.0},
        "H1000": {"vivacity": 39.9, "base": "S", "F": 3650000, "T_0": 3000, "temp_coeff_v": None, "temp_coeff_p": None, "bulk_density": None, "poly_a": 1.0, "poly_b": -1.0, "poly_c": 0.0, "poly_d": 0.0},
        "Retumbo": {"vivacity": 36.5, "base": "S", "F": 3650000, "T_0": 3000, "temp_coeff_v": None, "temp_coeff_p": None, "bulk_density": None, "poly_a": 1.0, "poly_b": -1.0, "poly_c": 0.0, "poly_d": 0.0},
        "CFE-BLK": {"vivacity": 83.2, "base": "D", "F": 3950000, "T_0": 3200, "temp_coeff_v": None, "temp_coeff_p": None, "bulk_density": None, "poly_a": 1.0, "poly_b": -1.0, "poly_c": 0.0, "poly_d": 0.0},
        "H335": {"vivacity": 58.3, "base": "D", "F": 3950000, "T_0": 3200, "temp_coeff_v": None, "temp_coeff_p": None, "bulk_density": None, "poly_a": 1.0, "poly_b": -1.0, "poly_c": 0.0, "poly_d": 0.0},
        "BL-C(2)": {"vivacity": 55.8, "base": "D", "F": 3950000, "T_0": 3200, "temp_coeff_v": None, "temp_coeff_p": None, "bulk_density": None, "poly_a": 1.0, "poly_b": -1.0, "poly_c": 0.0, "poly_d": 0.0},
        "H380": {"vivacity": 49.8, "base": "D", "F": 3950000, "T_0": 3200, "temp_coeff_v": None, "temp_coeff_p": None, "bulk_density": None, "poly_a": 1.0, "poly_b": -1.0, "poly_c": 0.0, "poly_d": 0.0},
    },
    "IMR": {
        "4227": {"vivacity": 123, "base": "S", "F": 3650000, "T_0": 3000, "temp_coeff_v": None, "temp_coeff_p": None, "bulk_density": None, "poly_a": 1.0, "poly_b": -1.0, "poly_c": 0.0, "poly_d": 0.0},
        "4198": {"vivacity": 89.6, "base": "S", "F": 3650000, "T_0": 3000, "temp_coeff_v": None, "temp_coeff_p": None, "bulk_density": None, "poly_a": 1.0, "poly_b": -1.0, "poly_c": 0.0, "poly_d": 0.0},
        "3031": {"vivacity": 72.9, "base": "S", "F": 3650000, "T_0": 3000, "temp_coeff_v": None, "temp_coeff_p": None, "bulk_density": None, "poly_a": 1.0, "poly_b": -1.0, "poly_c": 0.0, "poly_d": 0.0},
        "8208": {"vivacity": 66.8, "base": "S", "F": 3650000, "T_0": 3000, "temp_coeff_v": None, "temp_coeff_p": None, "bulk_density": None, "poly_a": 1.0, "poly_b": -1.0, "poly_c": 0.0, "poly_d": 0.0},
        "4064": {"vivacity": 67.8, "base": "S", "F": 3650000, "T_0": 3000, "temp_coeff_v": None, "temp_coeff_p": None, "bulk_density": None, "poly_a": 1.0, "poly_b": -1.0, "poly_c": 0.0, "poly_d": 0.0},
        "4320": {"vivacity": 66.9, "base": "S", "F": 3650000, "T_0": 3000, "temp_coeff_v": None, "temp_coeff_p": None, "bulk_density": None, "poly_a": 1.0, "poly_b": -1.0, "poly_c": 0.0, "poly_d": 0.0},
        "4895": {"vivacity": 60.9, "base": "S", "F": 3650000, "T_0": 3000, "temp_coeff_v": None, "temp_coeff_p": None, "bulk_density": None, "poly_a": 1.0, "poly_b": -1.0, "poly_c": 0.0, "poly_d": 0.0},
        "4350": {"vivacity": 51.1, "base": "S", "F": 3650000, "T_0": 3000, "temp_coeff_v": None, "temp_coeff_p": None, "bulk_density": None, "poly_a": 1.0, "poly_b": -1.0, "poly_c": 0.0, "poly_d": 0.0},
        "4831": {"vivacity": 48.9, "base": "S", "F": 3650000, "T_0": 3000, "temp_coeff_v": None, "temp_coeff_p": None, "bulk_density": None, "poly_a": 1.0, "poly_b": -1.0, "poly_c": 0.0, "poly_d": 0.0},
        "7828": {"vivacity": 43.8, "base": "S", "F": 3650000, "T_0": 3000, "temp_coeff_v": None, "temp_coeff_p": None, "bulk_density": None, "poly_a": 1.0, "poly_b": -1.0, "poly_c": 0.0, "poly_d": 0.0},
    },
    "Vihtavuori": {
        "N110": {"vivacity": 122, "base": "S", "F": 3650000, "T_0": 3000, "temp_coeff_v": None, "temp_coeff_p": None, "bulk_density": None, "poly_a": 1.0, "poly_b": -1.0, "poly_c": 0.0, "poly_d": 0.0},
        "N120": {"vivacity": 98.0, "base": "S", "F": 3650000, "T_0": 3000, "temp_coeff_v": None, "temp_coeff_p": None, "bulk_density": None, "poly_a": 1.0, "poly_b": -1.0, "poly_c": 0.0, "poly_d": 0.0},
        "N130": {"vivacity": 81.3, "base": "S", "F": 3650000, "T_0": 3000, "temp_coeff_v": None, "temp_coeff_p": None, "bulk_density": None, "poly_a": 1.0, "poly_b": -1.0, "poly_c": 0.0, "poly_d": 0.0},
        "N133": {"vivacity": 76.5, "base": "S", "F": 3650000, "T_0": 3000, "temp_coeff_v": None, "temp_coeff_p": None, "bulk_density": None, "poly_a": 1.0, "poly_b": -1.0, "poly_c": 0.0, "poly_d": 0.0},
        "N135": {"vivacity": 67.8, "base": "S", "F": 3650000, "T_0": 3000, "temp_coeff_v": None, "temp_coeff_p": None, "bulk_density": None, "poly_a": 1.0, "poly_b": -1.0, "poly_c": 0.0, "poly_d": 0.0},
        "N140": {"vivacity": 61.8, "base": "S", "F": 3650000, "T_0": 2900, "temp_coeff_v": None, "temp_coeff_p": None, "bulk_density": None, "poly_a": 1.0, "poly_b": -1.0, "poly_c": 0.0, "poly_d": 0.0},
        "N150": {"vivacity": 59.2, "base": "S", "F": 3650000, "T_0": 2900, "temp_coeff_v": None, "temp_coeff_p": None, "bulk_density": None, "poly_a": 1.0, "poly_b": -1.0, "poly_c": 0.0, "poly_d": 0.0},
        "N160": {"vivacity": 48.1, "base": "S", "F": 3650000, "T_0": 2900, "temp_coeff_v": None, "temp_coeff_p": None, "bulk_density": None, "poly_a": 1.0, "poly_b": -1.0, "poly_c": 0.0, "poly_d": 0.0},
        "N165": {"vivacity": 43.8, "base": "S", "F": 3650000, "T_0": 2900, "temp_coeff_v": None, "temp_coeff_p": None, "bulk_density": None, "poly_a": 1.0, "poly_b": -1.0, "poly_c": 0.0, "poly_d": 0.0},
        "N170": {"vivacity": 37.8, "base": "S", "F": 3650000, "T_0": 2900, "temp_coeff_v": None, "temp_coeff_p": None, "bulk_density": None, "poly_a": 1.0, "poly_b": -1.0, "poly_c": 0.0, "poly_d": 0.0},
        "N540": {"vivacity": 54.0, "base": "D", "F": 3950000, "T_0": 3200, "temp_coeff_v": None, "temp_coeff_p": None, "bulk_density": None, "poly_a": 1.0, "poly_b": -1.0, "poly_c": 0.0, "poly_d": 0.0},
        "N550": {"vivacity": 48.1, "base": "D", "F": 3950000, "T_0": 3200, "temp_coeff_v": None, "temp_coeff_p": None, "bulk_density": None, "poly_a": 1.0, "poly_b": -1.0, "poly_c": 0.0, "poly_d": 0.0},
        "N555": {"vivacity": 49.3, "base": "D", "F": 3950000, "T_0": 3200, "temp_coeff_v": None, "temp_coeff_p": None, "bulk_density": None, "poly_a": 1.0, "poly_b": -1.0, "poly_c": 0.0, "poly_d": 0.0},
        "N560": {"vivacity": 39.5, "base": "D", "F": 3950000, "T_0": 3200, "temp_coeff_v": None, "temp_coeff_p": None, "bulk_density": None, "poly_a": 1.0, "poly_b": -1.0, "poly_c": 0.0, "poly_d": 0.0},
        "N568": {"vivacity": 33.5, "base": "D", "F": 3950000, "T_0": 3200, "temp_coeff_v": None, "temp_coeff_p": None, "bulk_density": None, "poly_a": 1.0, "poly_b": -1.0, "poly_c": 0.0, "poly_d": 0.0},
        "N570": {"vivacity": 34.4, "base": "D", "F": 3950000, "T_0": 3200, "temp_coeff_v": None, "temp_coeff_p": None, "bulk_density": None, "poly_a": 1.0, "poly_b": -1.0, "poly_c": 0.0, "poly_d": 0.0},
    },
    "Somchem": {
        "S321": {"vivacity": 72.9, "base": "S", "F": 3650000, "T_0": 3000, "temp_coeff_v": None, "temp_coeff_p": None, "bulk_density": None, "poly_a": 1.0, "poly_b": -1.0, "poly_c": 0.0, "poly_d": 0.0},
        "S335": {"vivacity": 66.1, "base": "S", "F": 3650000, "T_0": 3000, "temp_coeff_v": None, "temp_coeff_p": None, "bulk_density": None, "poly_a": 1.0, "poly_b": -1.0, "poly_c": 0.0, "poly_d": 0.0},
        "S341": {"vivacity": 58.3, "base": "S", "F": 3650000, "T_0": 3000, "temp_coeff_v": None, "temp_coeff_p": None, "bulk_density": None, "poly_a": 1.0, "poly_b": -1.0, "poly_c": 0.0, "poly_d": 0.0},
        "S365": {"vivacity": 49.8, "base": "S", "F": 3650000, "T_0": 3000, "temp_coeff_v": None, "temp_coeff_p": None, "bulk_density": None, "poly_a": 1.0, "poly_b": -1.0, "poly_c": 0.0, "poly_d": 0.0},
        "S385": {"vivacity": 42.9, "base": "S", "F": 3650000, "T_0": 3000, "temp_coeff_v": None, "temp_coeff_p": None, "bulk_density": None, "poly_a": 1.0, "poly_b": -1.0, "poly_c": 0.0, "poly_d": 0.0},
    },
    "Winchester": {
        "Staball Match": {"vivacity": 50.6, "base": "D", "F": 3950000, "T_0": 3200, "temp_coeff_v": None, "temp_coeff_p": None, "bulk_density": None, "poly_a": 1.0, "poly_b": -1.0, "poly_c": 0.0, "poly_d": 0.0},
        "748": {"vivacity": 48.9, "base": "D", "F": 3950000, "T_0": 3200, "temp_coeff_v": None, "temp_coeff_p": None, "bulk_density": None, "poly_a": 1.0, "poly_b": -1.0, "poly_c": 0.0, "poly_d": 0.0},
        "Staball 6.5": {"vivacity": 45.5, "base": "D", "F": 3950000, "T_0": 3200, "temp_coeff_v": None, "temp_coeff_p": None, "bulk_density": None, "poly_a": 1.0, "poly_b": -1.0, "poly_c": 0.0, "poly_d": 0.0},
        "760": {"vivacity": 43.8, "base": "D", "F": 3950000, "T_0": 3200, "temp_coeff_v": None, "temp_coeff_p": None, "bulk_density": None, "poly_a": 1.0, "poly_b": -1.0, "poly_c": 0.0, "poly_d": 0.0},
        "Staball HD": {"vivacity": 34.0, "base": "D", "F": 3950000, "T_0": 3200, "temp_coeff_v": None, "temp_coeff_p": None, "bulk_density": None, "poly_a": 1.0, "poly_b": -1.0, "poly_c": 0.0, "poly_d": 0.0},
    },
    "Lovex": {
        "S053": {"vivacity": 123, "base": "S", "F": 3650000, "T_0": 3000, "temp_coeff_v": None, "temp_coeff_p": None, "bulk_density": None, "poly_a": 1.0, "poly_b": -1.0, "poly_c": 0.0, "poly_d": 0.0},
        "S060": {"vivacity": 71.2, "base": "S", "F": 3650000, "T_0": 3000, "temp_coeff_v": None, "temp_coeff_p": None, "bulk_density": None, "poly_a": 1.0, "poly_b": -1.0, "poly_c": 0.0, "poly_d": 0.0},
        "S062": {"vivacity": 58.3, "base": "S", "F": 3650000, "T_0": 3000, "temp_coeff_v": None, "temp_coeff_p": None, "bulk_density": None, "poly_a": 1.0, "poly_b": -1.0, "poly_c": 0.0, "poly_d": 0.0},
        "S065": {"vivacity": 53.6, "base": "S", "F": 3650000, "T_0": 3000, "temp_coeff_v": None, "temp_coeff_p": None, "bulk_density": None, "poly_a": 1.0, "poly_b": -1.0, "poly_c": 0.0, "poly_d": 0.0},
        "S070": {"vivacity": 47.2, "base": "S", "F": 3650000, "T_0": 3000, "temp_coeff_v": None, "temp_coeff_p": None, "bulk_density": None, "poly_a": 1.0, "poly_b": -1.0, "poly_c": 0.0, "poly_d": 0.0},
        "S071": {"vivacity": 45.5, "base": "S", "F": 3650000, "T_0": 3000, "temp_coeff_v": None, "temp_coeff_p": None, "bulk_density": None, "poly_a": 1.0, "poly_b": -1.0, "poly_c": 0.0, "poly_d": 0.0},
        "D063": {"vivacity": 93.6, "base": "D", "F": 3950000, "T_0": 3200, "temp_coeff_v": None, "temp_coeff_p": None, "bulk_density": None, "poly_a": 1.0, "poly_b": -1.0, "poly_c": 0.0, "poly_d": 0.0},
        "D073.4": {"vivacity": 55.8, "base": "D", "F": 3950000, "T_0": 3200, "temp_coeff_v": None, "temp_coeff_p": None, "bulk_density": None, "poly_a": 1.0, "poly_b": -1.0, "poly_c": 0.0, "poly_d": 0.0},
        "D073.5": {"vivacity": 55.3, "base": "D", "F": 3950000, "T_0": 3200, "temp_coeff_v": None, "temp_coeff_p": None, "bulk_density": None, "poly_a": 1.0, "poly_b": -1.0, "poly_c": 0.0, "poly_d": 0.0},
        "D073.6": {"vivacity": 51.5, "base": "D", "F": 3950000, "T_0": 3200, "temp_coeff_v": None, "temp_coeff_p": None, "bulk_density": None, "poly_a": 1.0, "poly_b": -1.0, "poly_c": 0.0, "poly_d": 0.0},
        "D100": {"vivacity": 31.0, "base": "D", "F": 3950000, "T_0": 3200, "temp_coeff_v": None, "temp_coeff_p": None, "bulk_density": None, "poly_a": 1.0, "poly_b": -1.0, "poly_c": 0.0, "poly_d": 0.0},
    },
    "Ramshot": {
        "X-Terminator": {"vivacity": 62.5, "base": "D", "F": 3950000, "T_0": 3200, "temp_coeff_v": None, "temp_coeff_p": None, "bulk_density": None, "poly_a": 1.0, "poly_b": -1.0, "poly_c": 0.0, "poly_d": 0.0},
        "TAC": {"vivacity": 57.1, "base": "D", "F": 3950000, "T_0": 3200, "temp_coeff_v": None, "temp_coeff_p": None, "bulk_density": None, "poly_a": 1.0, "poly_b": -1.0, "poly_c": 0.0, "poly_d": 0.0},
        "Wild Boar": {"vivacity": 54.9, "base": "D", "F": 3950000, "T_0": 3200, "temp_coeff_v": None, "temp_coeff_p": None, "bulk_density": None, "poly_a": 1.0, "poly_b": -1.0, "poly_c": 0.0, "poly_d": 0.0},
        "Big Game": {"vivacity": 48.1, "base": "D", "F": 3950000, "T_0": 3200, "temp_coeff_v": None, "temp_coeff_p": None, "bulk_density": None, "poly_a": 1.0, "poly_b": -1.0, "poly_c": 0.0, "poly_d": 0.0},
        "Hunter": {"vivacity": 45.5, "base": "D", "F": 3950000, "T_0": 3200, "temp_coeff_v": None, "temp_coeff_p": None, "bulk_density": None, "poly_a": 1.0, "poly_b": -1.0, "poly_c": 0.0, "poly_d": 0.0},
        "Magnum": {"vivacity": 34.0, "base": "D", "F": 3950000, "T_0": 3200, "temp_coeff_v": None, "temp_coeff_p": None, "bulk_density": None, "poly_a": 1.0, "poly_b": -1.0, "poly_c": 0.0, "poly_d": 0.0},
        "LRT": {"vivacity": 31.0, "base": "D", "F": 3950000, "T_0": 3200, "temp_coeff_v": None, "temp_coeff_p": None, "bulk_density": None, "poly_a": 1.0, "poly_b": -1.0, "poly_c": 0.0, "poly_d": 0.0},
    },
    "Accurate": {
        "A2495": {"vivacity": 69.3, "base": "S", "F": 3650000, "T_0": 3000, "temp_coeff_v": None, "temp_coeff_p": None, "bulk_density": None, "poly_a": 1.0, "poly_b": -1.0, "poly_c": 0.0, "poly_d": 0.0},
    }
}

# Bullet type data
BULLET_TYPES = {
    "Copper Jacket over Lead": {"s": 100, "rho_p": 0.321},
    "Solid Copper": {"s": 200, "rho_p": 0.323},
    "Gilding Metal Brass": {"s": 300, "rho_p": 0.306}
}

def create_database(db_path="ballistics_data.db"):
    """Create SQLite database with versioning and populate with propellant and bullet data."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create version table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS version (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            version TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("INSERT OR IGNORE INTO version (version) VALUES (?)", (DB_VERSION,))

    # Create propellants table with polynomial coefficients
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS propellants (
            name TEXT PRIMARY KEY,
            manufacturer TEXT,          -- Manufacturer name
            vivacity REAL,              -- s^-1 per 100 bar
            base TEXT,                  -- 'S' for single-base, 'D' for double-base
            force REAL,                 -- Force constant (ft-lbf/lbm)
            temp_0 REAL,                -- Flame temperature at reference condition (K)
            temp_coeff_v REAL,          -- Temperature coefficient for vivacity (1/K)
            temp_coeff_p REAL,          -- Temperature coefficient for pressure (1/K)
            bulk_density REAL,          -- Bulk density (lbm/in^3)
            poly_a REAL,                -- Polynomial coefficient a
            poly_b REAL,                -- Polynomial coefficient b
            poly_c REAL,                -- Polynomial coefficient c
            poly_d REAL                 -- Polynomial coefficient d
        )
    """)

    # Create bullet_types table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bullet_types (
            name TEXT PRIMARY KEY,
            s REAL,                     -- Strength factor
            rho_p REAL                  -- Density (lbm/in^3)
        )
    """)

    # Insert propellant data
    for manufacturer, powders in PROPELLANTS.items():
        for name, props in powders.items():
            cursor.execute("""
                INSERT OR REPLACE INTO propellants (
                    name, manufacturer, vivacity, base, force, temp_0, temp_coeff_v, temp_coeff_p, bulk_density,
                    poly_a, poly_b, poly_c, poly_d
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                name, manufacturer, props["vivacity"], props["base"], props["F"], props["T_0"],
                props["temp_coeff_v"], props["temp_coeff_p"], props["bulk_density"],
                props["poly_a"], props["poly_b"], props["poly_c"], props["poly_d"]
            ))

    # Insert bullet type data
    for name, props in BULLET_TYPES.items():
        cursor.execute("""
            INSERT OR REPLACE INTO bullet_types (name, s, rho_p)
            VALUES (?, ?, ?)
        """, (name, props["s"], props["rho_p"]))

    conn.commit()
    cursor.execute("SELECT version FROM version WHERE version = ?", (DB_VERSION,))
    if cursor.fetchone():
        print(f"Database '{db_path}' created or updated to version {DB_VERSION} successfully.")
    else:
        print(f"Warning: Version {DB_VERSION} not set correctly in database.")
    conn.close()

def check_version(db_path="ballistics_data.db"):
    """Check the database version."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT version FROM version ORDER BY created_at DESC LIMIT 1")
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

if __name__ == "__main__":
    create_database()
    current_version = check_version()
    if current_version == DB_VERSION:
        print(f"Confirmed database version: {current_version}")
    else:
        print(f"Version mismatch! Expected {DB_VERSION}, found {current_version}")