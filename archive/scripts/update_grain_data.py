import sqlite3
import re

# Connect to the database
conn = sqlite3.connect("ballistics_data.db")
cursor = conn.cursor()

# Read the markdown file
with open("research/propellant_grain_data.md", "r") as f:
    content = f.read()

# Find the table
table_match = re.search(
    r"\| Name \|.*?\n\|------\|.*?\n((?:\|.*?\n)+)", content, re.MULTILINE
)
if not table_match:
    print("Table not found")
    exit(1)

table_lines = table_match.group(1).strip().split("\n")

# Skip header
data_lines = table_lines[1:]

for line in data_lines:
    if not line.strip():
        continue
    parts = [p.strip() for p in line.split("|")[1:-1]]
    if len(parts) < 9:
        continue

    (
        name,
        manufacturer,
        geometry,
        perforations,
        diameter,
        length,
        web,
        coating,
        confidence,
        sources,
    ) = parts

    # Convert to appropriate types
    perforations_count = int(perforations) if perforations.isdigit() else 0
    grain_diameter_mm = float(diameter) if diameter.replace(".", "").isdigit() else None
    grain_length_mm = float(length) if length.replace(".", "").isdigit() else None
    web_thickness_mm = float(web) if web.replace(".", "").isdigit() else None

    # Update the database
    cursor.execute(
        """
        UPDATE propellants 
        SET grain_geometry_type = ?, 
            perforations_count = ?, 
            grain_diameter_mm = ?, 
            grain_length_mm = ?, 
            web_thickness_mm = ?, 
            coating = ?, 
            grain_confidence = ?, 
            grain_sources = ?
        WHERE name = ? AND manufacturer = ?
    """,
        (
            geometry,
            perforations_count,
            grain_diameter_mm,
            grain_length_mm,
            web_thickness_mm,
            coating,
            confidence,
            sources,
            name,
            manufacturer,
        ),
    )

# Commit and close
conn.commit()
conn.close()

print("Database updated successfully")
