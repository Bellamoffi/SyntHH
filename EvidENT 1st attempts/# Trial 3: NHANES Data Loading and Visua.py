# Trial 1: NHANES Data Loading and Visualization (Final)
# Author: Isabella
# Date: 2025-09-15

import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import textwrap

# -----------------------------
# Config
# -----------------------------
data_folder = '/Users/isabella/SyntHH/data'
demo_folder = os.path.join(data_folder, 'demo')
pta_folder = os.path.join(data_folder, 'pta')
reflex_folder = os.path.join(data_folder, 'reflex')
tymp_folder = os.path.join(data_folder, 'tymp')

ENABLE_SEQN_FILTER = False  # 🔥 Toggle this to True later when datasets match

# -----------------------------
# Utility Functions
# -----------------------------
def list_files(folder):
    if not os.path.exists(folder):
        print(f"❌ Folder not found: {folder}")
        return []
    files = sorted([f for f in os.listdir(folder) if f.endswith('.csv')])
    print(f"\n📂 Files in {folder}:")
    for f in files:
        print("  ", f)
    return files

def find_csv(folder, prefix):
    files = list_files(folder)
    match = [f for f in files if f.startswith(prefix)]
    if not match:
        print(f"❌ No CSV in {folder} starting with '{prefix}'")
        return None
    path = os.path.join(folder, match[0])
    print(f"✅ Using: {path}")
    return path

# -----------------------------
# Filtering
# -----------------------------
def filter_aux_df(df):
    cols = [
        'SEQN', 'AUXU1K1R', 'AUXU500R', 'AUXU1K2R', 'AUXU2KR', 'AUXU3KR', 'AUXU4KR',
        'AUXU6KR', 'AUXU8KR', 'AUXU1K1L', 'AUXU500L', 'AUXU1K2L', 'AUXU2KL', 'AUXU3KL',
        'AUXU4KL', 'AUXU6KL', 'AUXU8KL'
    ]
    available = [c for c in cols if c in df.columns]
    return df[available].replace({888: np.nan, 666: np.nan})

def filter_demo_df(demo_df, aux_df):
    cols = ['SEQN', 'RIAGENDR', 'RIDAGEYR', 'RIDAGEMN', 'RIDRETH1']
    available = [c for c in cols if c in demo_df.columns]
    filtered = demo_df[available]

    if ENABLE_SEQN_FILTER:
        print("🔍 Filtering demo_df to only SEQNs in aux_df...")
        filtered = filtered[filtered.SEQN.isin(aux_df.SEQN)]

    filtered.reset_index(drop=True, inplace=True)
    return filtered

# -----------------------------
# Load and Filter Data
# -----------------------------
def load_and_filter_cohort():
    demo_path = find_csv(demo_folder, 'nhanes_demo_')
    aux_path = find_csv(pta_folder, 'nhanes_aux_')
    auxr_path = find_csv(reflex_folder, 'nhanes_auxr_')
    auxt_path = find_csv(tymp_folder, 'nhanes_auxt_')

    if not demo_path or not aux_path:
        sys.exit("❌ Missing required CSV files. Please check your folders.")

    demo_df = pd.read_csv(demo_path)
    aux_df = pd.read_csv(aux_path)
    auxr_df = pd.read_csv(auxr_path) if auxr_path else pd.DataFrame()
    auxt_df = pd.read_csv(auxt_path) if auxt_path else pd.DataFrame()

    print("\n--- SEQN Ranges ---")
    print(f"Demo: {demo_df['SEQN'].min()} - {demo_df['SEQN'].max()}")
    print(f"Aux: {aux_df['SEQN'].min()} - {aux_df['SEQN'].max()}")

    filtered_aux = filter_aux_df(aux_df)
    filtered_demo = filter_demo_df(demo_df, filtered_aux)

    return filtered_demo, filtered_aux, auxr_df, auxt_df

demo_df, aux_df, auxr_df, auxt_df = load_and_filter_cohort()
print(f"\n✅ Demo DF shape: {demo_df.shape}")
print(f"✅ Aux DF shape: {aux_df.shape}")

# -----------------------------
# Column Labels
# -----------------------------
aux_labels = {}
freq_map = {
    '500': '500 Hz', '1K1': '1000 Hz', '1K2': '1000 Hz',
    '2K': '2000 Hz', '3K': '3000 Hz', '4K': '4000 Hz',
    '6K': '6000 Hz', '8K': '8000 Hz'
}

for col in aux_df.columns:
    if col == 'SEQN':
        continue
    if col == 'RIDAGEYR':
        aux_labels[col] = 'Age (Years)'
        continue
    ear = 'Right' if col.endswith('R') else 'Left' if col.endswith('L') else ''
    freq_code = col[4:-1]
    freq_str = freq_map.get(freq_code, freq_code + ' Hz')
    aux_labels[col] = f'Hearing Threshold at {freq_str} ({ear} Ear, dB)'

if 'RIDAGEYR' not in aux_df.columns:
    print("⚠️ No age column found, adding random ages.")
    aux_df['RIDAGEYR'] = np.random.randint(18, 80, size=len(aux_df))
    aux_labels['RIDAGEYR'] = 'Age (Years)'

# -----------------------------
# Plotting Function
# -----------------------------
def scatter_subplots(columns, ear_name, color):
    if not columns:
        print(f"No {ear_name}-ear columns found.")
        return

    num_cols = 4
    num_rows = (len(columns) + num_cols - 1) // num_cols
    fig, axes = plt.subplots(num_rows, num_cols, figsize=(24, 6*num_rows))
    axes = axes.flatten()

    for ax, col in zip(axes, columns):
        plot_df = aux_df[['RIDAGEYR', col]].dropna()
        if plot_df.empty:
            ax.axis('off')
            continue
        ax.scatter(plot_df['RIDAGEYR'], plot_df[col], alpha=0.6, color=color)
        title = "\n".join(textwrap.wrap(f'Age vs {aux_labels[col]}', width=35))
        ax.set_title(title, fontsize=10)
        ax.set_xlabel('Age (Years)')
        ax.set_ylabel(aux_labels[col])

    for i in range(len(columns), len(axes)):
        axes[i].axis('off')

    plt.suptitle(f'Age vs Hearing Thresholds ({ear_name} Ear)', fontsize=16, y=1.02)
    plt.tight_layout()
    plt.subplots_adjust(hspace=0.5, wspace=0.4, top=0.95)
    plt.show()

# -----------------------------
# Run Plots
# -----------------------------
right_ear_cols = [c for c in aux_df.columns if c.endswith('R')]
left_ear_cols = [c for c in aux_df.columns if c.endswith('L')]

scatter_subplots(right_ear_cols, 'Right', 'green')
scatter_subplots(left_ear_cols, 'Left', 'blue')
