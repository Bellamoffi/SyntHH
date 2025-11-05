import os
import glob
import pandas as pd
from functools import reduce

# --------------------------
# Base folder containing all dataset folders
base_folder = "/Users/isabella/Library/Mobile Documents/com~apple~CloudDocs/Graduated/UCL EvidENT/DOWNLOADED DATA/CSV READABLE"

# Dataset folders to merge
dataset_folders = [
    "Audiometry",
    "Audiometry - Acoustic Reflex",
    "Audiometry - Tympanometry",
    "Audiometry - Wideband Reflectance"
]

# Output folder inside CSV READABLE
output_folder = os.path.join(base_folder, "Merged_Audiometry")
os.makedirs(output_folder, exist_ok=True)
output_file = os.path.join(output_folder, "Merged_Audiometry.csv")

# --------------------------
# Name of the key column
expected_key_column = "SEQN - Respondent sequence number"

all_dfs = []

for folder_name in dataset_folders:
    folder_path = os.path.join(base_folder, folder_name)
    print(f"\n🔍 Processing folder: {folder_path}")

    if not os.path.exists(folder_path):
        print(f"⚠️ Folder not found: {folder_path}")
        continue

    # Recursive search for CSV files
    csv_files = glob.glob(os.path.join(folder_path, "**/*.csv"), recursive=True)
    print(f"Found {len(csv_files)} CSV files")

    if not csv_files:
        print(f"⚠️ No CSVs found in folder: {folder_path}")
        continue

    dfs = []
    for f in csv_files:
        try:
            df = pd.read_csv(f, encoding='utf-8', low_memory=False)
        except Exception as e:
            print(f"❌ Failed to read {f}: {e}")
            continue

        # Detect key column in this CSV
        key_col = None
        for col in df.columns:
            if col.strip().lower() == expected_key_column.strip().lower():
                key_col = col
                break
        if not key_col:
            print(f"⚠️ Key column not found in {f}. Skipping this file.")
            continue

        # Add folder prefix to all columns except key column
        df = df.rename(
            columns={col: f"{folder_name}_{col}" if col != key_col else col for col in df.columns}
        )

        print(f"✅ Read {f} ({len(df)} rows, {len(df.columns)} columns)")
        dfs.append(df)

    # Concatenate multiple years for this folder
    if dfs:
        combined = pd.concat(dfs, ignore_index=True)
        print(f"📌 Combined folder {folder_name}: {len(combined)} rows, {len(combined.columns)} columns")
        all_dfs.append(combined)

# --------------------------
# Merge all datasets on the key column
if all_dfs:
    merged_df = reduce(lambda left, right: pd.merge(left, right, on=expected_key_column, how="outer"), all_dfs)
    merged_df.to_csv(output_file, index=False, encoding='utf-8')
    print(f"\n🎉 Merged CSV saved to: {output_file} ({len(merged_df)} rows, {len(merged_df.columns)} columns)")
else:
    print("❌ No datasets found to merge.")

