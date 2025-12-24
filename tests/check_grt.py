import sys

sys.path.insert(0, "src")

from ballistics.io.io import load_grt_project

metadata, load_data = load_grt_project(
    "data/grt_files/65CM_130SMK_N150_Starline_Initial.grtload"
)

print("Metadata:")
for k, v in metadata.items():
    print(f"  {k}: {v}")

print("\nLoad data:")
print(load_data)
