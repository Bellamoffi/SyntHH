import pandas as pd
import os
from glob import glob
import re
from functools import reduce

# =========================
# CONFIG
# =========================
base_dir = "/Users/isabella/Library/Mobile Documents/com~apple~CloudDocs/Graduated/UCL EvidENT/DOWNLOADED DATA/CSV READABLE"
output_dir = os.path.join(base_dir, "MERGED_OUTPUT")
os.makedirs(output_dir, exist_ok=True)

include_folders = [
    "Audiometry - Tympanometry",
    "Audiometry - Wideband Reflectance",
    "Audiometry - Acoustic Reflex",
    "Audiometry",
]

# Optional CSV engine
try:
    import pyarrow
    csv_engine = "pyarrow"
except ImportError:
    csv_engine = "c"

# =========================
# Helper functions
# =========================
def extract_year(fname):
    match = re.search(r"\d{4}(?:-\d{4})?", os.path.basename(fname))
    if match:
        return match.group(0).replace("-", "_")
    return "UnknownYear"

# =========================
# Find CSV files
# =========================
all_csv_files = []
for folder in include_folders:
    folder_path = os.path.join(base_dir, folder)
    all_csv_files.extend(glob(os.path.join(folder_path, "**", "*.csv"), recursive=True))

csv_files = [
    f for f in all_csv_files
    if "mapping" not in os.path.basename(f).lower()
    and re.search(r"\d{4}(?:-\d{4})?", os.path.basename(f))
]

if not csv_files:
    print("No relevant CSV files found. Check your directory or year patterns.")
    exit()

# =========================
# Group files by year
# =========================
files_by_year = {}
for f in csv_files:
    year = extract_year(f)
    files_by_year.setdefault(year, []).append(f)

# =========================
# Process each year (CSV only)
# =========================
for year, files in files_by_year.items():
    print(f"\nProcessing year: {year} ({len(files)} files)")

    dfs = []
    for file in files:
        try:
            df = pd.read_csv(file, engine=csv_engine)
        except Exception as e:
            print(f" - Failed to read {file}: {e}")
            continue

        seqn_col = next((c for c in df.columns if "SEQN" in c.upper().strip()), None)
        if seqn_col is None:
            print(f" - No SEQN column in {file}, skipping")
            continue

        df = df.rename(columns={seqn_col: "SEQN"})
        if df["SEQN"].duplicated().any():
            df = df.drop_duplicates(subset="SEQN", keep="first")

        # Add suffix to avoid column collisions
        file_base = os.path.splitext(os.path.basename(file))[0].replace(" ", "_")
        df = df.rename(columns={c: f"{c}_{file_base}" for c in df.columns if c != "SEQN"})
        dfs.append(df.set_index("SEQN"))

    if not dfs:
        print(f"No valid data for year {year}, skipping.")
        continue

    # Merge all files by SEQN
    merged_df = reduce(lambda left, right: pd.merge(left, right, on="SEQN", how="outer"), dfs)
    output_csv = os.path.join(output_dir, f"{year}_MERGED.csv")
    merged_df.reset_index().to_csv(output_csv, index=False)
    print(f"✅ Saved CSV: {output_csv}")
