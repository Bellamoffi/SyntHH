import pandas as pd
import os
from glob import glob
import re

# =========================
# CONFIG
# =========================
base_dir = "/Users/isabella/Library/Mobile Documents/com~apple~CloudDocs/Graduated/UCL EvidENT/DOWNLOADED DATA/CSV READABLE"

# =========================
# FIND ALL CSV FILES (exclude mapping/codebook files)
# =========================
all_csv_files = glob(os.path.join(base_dir, "**", "*.csv"), recursive=True)
csv_files = [f for f in all_csv_files if "mapping" not in os.path.basename(f).lower()]

if not csv_files:
    print("No CSV files found for merging. Check your directory.")
    exit()

# =========================
# HELPER: extract year from filename
# =========================
def extract_year(fname):
    match = re.search(r"(19\d{2}[_-]\d{2}|\d{4}[_-]\d{4})", fname)
    if match:
        return match.group(1).replace("-", "_")  # normalize: 2007-2008 → 2007_2008
    else:
        return "UnknownYear"

# =========================
# GROUP FILES BY YEAR
# =========================
files_by_year = {}
for f in csv_files:
    year = extract_year(f)
    files_by_year.setdefault(year, []).append(f)

# =========================
# PROCESS EACH YEAR SEPARATELY
# =========================
for year, files in files_by_year.items():
    print(f"\n======================")
    print(f" Processing year: {year} ({len(files)} files)")
    print(f"======================")

    merged_df = None
    summary_log = []
    included_files_names = []
    all_columns_seen = set()

    for i, file in enumerate(files, start=1):
        print(f"\n[{i}/{len(files)}] Processing: {file}")
        
        try:
            df = pd.read_csv(file)
        except Exception as e:
            print(f"Failed to read {file}: {e}")
            summary_log.append(f"Failed to read: {file} ({e})")
            continue
        
        print(f" - Columns: {df.columns.tolist()[:10]}{'...' if len(df.columns) > 10 else ''}")
        print(f" - Number of rows: {len(df)}")
        
        # Detect SEQN column
        seqn_col = None
        for col in df.columns:
            if "SEQN" in col.upper().strip():
                seqn_col = col
                break
        
        if seqn_col is None:
            print(f" - No SEQN column found, skipping file")
            summary_log.append(f"Skipped: {file} (no SEQN)")
            continue
        
        df = df.rename(columns={seqn_col: "SEQN"})
        
        # Add file name suffix
        file_base = os.path.splitext(os.path.basename(file))[0].replace(" ", "_")
        included_files_names.append(file_base)
        new_columns = {}
        for col in df.columns:
            if col != "SEQN":
                col_renamed = f"{col}_{file_base}"
                new_columns[col] = col_renamed
                if col_renamed in all_columns_seen:
                    print(f"WARNING: Column {col_renamed} already exists in merged dataframe")
                all_columns_seen.add(col_renamed)
        df = df.rename(columns=new_columns)
        
        # Merge
        if merged_df is None:
            merged_df = df
            print(f" - Initialized merged dataframe with {len(df)} participants")
            summary_log.append(f"Included: {file} ({len(df)} rows, {df.shape[1]-1} columns)")
        else:
            merged_df = merged_df.merge(df, on="SEQN", how="outer")
            print(f" - Merged file; current merged participants: {len(merged_df)}")
            summary_log.append(f"Merged: {file} ({len(df)} rows, {df.shape[1]-1} columns)")

    # =========================
    # SAVE PER-YEAR OUTPUT
    # =========================
    if merged_df is not None:
        files_part = "_".join(included_files_names)
        output_file = os.path.join(base_dir, f"{year}_{files_part}.csv")
        merged_df.to_csv(output_file, index=False)
        print(f"\nMERGE COMPLETE for {year}: {len(included_files_names)} files merged.")
        print(f"Total participants (rows): {merged_df.shape[0]}")
        print(f"Total columns (including SEQN): {merged_df.shape[1]}")
        print(f"Merged CSV saved as: {output_file}")
    else:
        print(f"No files merged for {year}")

    # =========================
    # PRINT SUMMARY LOG
    # =========================
    print("\nFiles summary/log for year", year)
    for line in summary_log:
        print(line)
