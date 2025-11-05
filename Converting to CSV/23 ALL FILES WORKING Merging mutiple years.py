import pandas as pd
import os
from glob import glob
import re

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
    """Extract year or year range from filename"""
    match = re.search(r"\d{4}(?:-\d{4})?", os.path.basename(fname))
    if match:
        return match.group(0).replace("-", "_")
    return "UnknownYear"

def strip_suffix(col_name):
    """Remove year/file suffix from column names, keep only tag/description"""
    if col_name != "SEQN" and "_" in col_name:
        # Remove everything after the last underscore if it's from filename/year
        parts = col_name.split("_")
        return "_".join(parts[:-1])
    return col_name

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
# Process each year and collect for master CSV
# =========================
master_dfs_list = []
seqn_years_map = {}  # track years per SEQN

for year, files in files_by_year.items():
    output_csv = os.path.join(output_dir, f"{year}_MERGED.csv")

    # Skip if the per-year merged CSV exists
    if os.path.exists(output_csv):
        print(f"Skipping year {year}: merged CSV already exists ({output_csv})")
        merged_year_df = pd.read_csv(output_csv, low_memory=False)
        # Track years for SEQN
        for seqn in merged_year_df["SEQN"]:
            seqn_years_map.setdefault(seqn, set()).add(year)
        master_dfs_list.append(merged_year_df)
        continue

    print(f"\nProcessing year: {year} ({len(files)} files)")
    year_dfs = []

    for file in files:
        try:
            df = pd.read_csv(file, engine=csv_engine, low_memory=False)
        except Exception as e:
            print(f" - Failed to read {file}: {e}")
            continue

        # Identify SEQN column
        seqn_col = next((c for c in df.columns if "SEQN" in c.upper().strip()), None)
        if seqn_col is None:
            print(f" - No SEQN column in {file}, skipping")
            continue
        df = df.rename(columns={seqn_col: "SEQN"})

        # Remove duplicates
        if df["SEQN"].duplicated().any():
            df = df.drop_duplicates(subset="SEQN", keep="first")

        # Track years for each SEQN
        for seqn in df["SEQN"]:
            seqn_years_map.setdefault(seqn, set()).add(year)

        # Keep column names clean; no suffix
        df.columns = [strip_suffix(c) for c in df.columns]

        year_dfs.append(df)

    if not year_dfs:
        print(f"No valid data for year {year}, skipping.")
        continue

    # Merge all files for the year horizontally on SEQN
    merged_year_df = year_dfs[0]
    for df in year_dfs[1:]:
        merged_year_df = pd.merge(merged_year_df, df, on="SEQN", how="outer")

    # Add Year column
    merged_year_df["Year"] = year

    # Save per-year CSV
    merged_year_df.to_csv(output_csv, index=False)
    print(f"✅ Saved per-year CSV: {output_csv}")

    # Append to master list
    master_dfs_list.append(merged_year_df)

# =========================
# Create master CSV (stack all years vertically)
# =========================
master_csv = os.path.join(output_dir, "MASTER_MERGED.csv")

if master_dfs_list:
    # Stack all years vertically
    master_df = pd.concat(master_dfs_list, axis=0, ignore_index=True)

    # Optional: convert Year to sortable numeric if needed
    master_df['Year_Sort'] = master_df['Year'].apply(lambda x: int(x.split('_')[0]))

    # Sort by Year (earliest first)
    master_df = master_df.sort_values('Year_Sort').drop(columns=['Year_Sort'])

    # Drop duplicate SEQN entries (shouldn't happen if SEQNs are unique per year)
    master_df = master_df.drop_duplicates(subset=["SEQN"], keep="first")

    # Add Years_Present column
    master_df["Years_Present"] = master_df["SEQN"].map(lambda x: ",".join(sorted(seqn_years_map.get(x, []))))

    # Optional: sort columns
    fixed_cols = ["SEQN", "Years_Present", "Year"]
    other_cols = sorted([c for c in master_df.columns if c not in fixed_cols])
    master_df = master_df[fixed_cols + other_cols]

    master_df.to_csv(master_csv, index=False)
    print(f"\n✅ Saved MASTER CSV with all years in order: {master_csv}")
else:
    print("No data collected for master merge.")
