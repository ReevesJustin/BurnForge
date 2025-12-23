import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from ballistics import load_grt_project

grt_file = (
    sys.argv[1]
    if len(sys.argv) > 1
    else "data/grt_files/65CM_130SMK_N150_Starline_Initial.grtload"
)

metadata, load_data = load_grt_project(grt_file)

print(f"Cartridge: {metadata['cartridge']}")
print(f"Propellant: {metadata['propellant_name']}")
print(f"Number of charges: {len(load_data)}")
print(load_data.head())
