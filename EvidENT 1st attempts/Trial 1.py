# Trial 1: NHANES Data Loading and Visualization
# Author: Isabella
# Date: 2025-09-11

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# -----------------------------
# -----------------------------
# Step 1: Set absolute paths to your actual data
# -----------------------------
data_folder = '/Users/isabella/SyntHH/data'  # Your real data folder
demo_folder  = os.path.join(data_folder, 'demo')
pta_folder   = os.path.join(data_folder, 'pta')
reflex_folder = os.path.join(data_folder, 'reflex')
tymp_folder   = os.path.join(data_folder, 'tymp')


demo_folder  = os.path.join(data_folder, 'demo')
pta_folder   = os.path.join(data_folder, 'pta')
reflex_folder = os.path.join(data_folder, 'reflex')
tymp_folder   = os.path.join(data_folder, 'tymp')

# -----------------------------
# Step 2: Helper function to find CSVs automatically
# -----------------------------
def find_csv(folder, prefix):
    files = [f for f in os.listdir(folder) if f.startswith(prefix) and f.endswith('.csv')]
    if not files:
        raise FileNotFoundError(f"No CSV in {folder} starting with {prefix}")
    return os.path.join(folder, files[0])

# -----------------------------
# Step 3: Filtering functions
# -----------------------------
def filter_aux_df(nhanes_aux_df):
    subset_col_names = [
        'SEQN', 'AUXU1K1R', 'AUXU500R', 'AUXU1K2R', 'AUXU2KR', 'AUXU3KR', 'AUXU4KR',
        'AUXU6KR', 'AUXU8KR', 'AUXU1K1L', 'AUXU500L', 'AUXU1K2L', 'AUXU2KL', 'AUXU3KL',
        'AUXU4KL', 'AUXU6KL', 'AUXU8KL'
    ]
    filtered = nhanes_aux_df[subset_col_names].replace({888: np.nan, 666: np.nan})
    return filtered

def filter_demo_df(nhanes_demo_df, nhanes_aux_df):
    subset_col_names = ['SEQN', 'RIAGENDR', 'RIDAGEYR', 'RIDAGEMN', 'RIDRETH1']
    filtered = nhanes_demo_df[subset_col_names]
    filtered = filtered[filtered.SEQN.isin(nhanes_aux_df.SEQN)]
    filtered.reset_index(drop=True, inplace=True)
    return filtered

# -----------------------------
# Step 4: Load and filter cohort
# -----------------------------
def load_and_filter_cohort():
    """
    Load NHANES cohort data from data folders and filter auxiliary and demographic info.
    Returns:
        tuple: filtered_demo_df, filtered_aux_df, auxr_df, auxt_df
    """
    try:
        nhanes_demo_df = pd.read_csv(find_csv(demo_folder, 'nhanes_demo_'))
        nhanes_aux_df  = pd.read_csv(find_csv(pta_folder, 'nhanes_aux_'))
        nhanes_auxr_df = pd.read_csv(find_csv(reflex_folder, 'nhanes_auxr_'))
        nhanes_auxt_df = pd.read_csv(find_csv(tymp_folder, 'nhanes_auxt_'))
    except FileNotFoundError as e:
        print("Could not find data:", e)
        return None, None, None, None

    filtered_aux_df  = filter_aux_df(nhanes_aux_df)
    filtered_demo_df = filter_demo_df(nhanes_demo_df, filtered_aux_df)

    return filtered_demo_df, filtered_aux_df, nhanes_auxr_df, nhanes_auxt_df

# -----------------------------
# Step 5: Run the loader
# -----------------------------
demo_df, aux_df, auxr_df, auxt_df = load_and_filter_cohort()

if demo_df is None or aux_df is None:
    print("Data not loaded. Check your data folder structure.")
else:
    print("Demo DF shape:", demo_df.shape)
    print("Aux DF shape:", aux_df.shape)

    # ----------------
# -----------------------------
# Quick check of data
# -----------------------------
print("Demo DF shape:", demo_df.shape)
print(demo_df.head())   # Check first few rows and SEQN values

print("Aux DF shape:", aux_df.shape)
print(aux_df.head())    # Check first few rows and SEQN values

# -----------------------------
# -----------------------------
# Step 6: Visualizations
# -----------------------------

import textwrap  # for wrapping long titles

if demo_df is None or aux_df is None or demo_df.empty or aux_df.empty:
    print("Data not loaded. Check your data folder structure or filters.")
else:
    print("Demo DF shape:", demo_df.shape)
    print("Aux DF shape:", aux_df.shape)

    # 1️⃣ Age distribution
    plt.hist(demo_df['RIDAGEYR'], bins=20, color='skyblue', edgecolor='black')
    plt.title('Age Distribution')
    plt.xlabel('Age (years)')
    plt.ylabel('Number of Participants')
    plt.show()

    # 2️⃣ Create descriptive labels for all auxiliary columns
    aux_labels = {}
    freq_map = {
        '500': '500 Hz', '1K1': '1000 Hz', '1K2': '1000 Hz', '2K': '2000 Hz', 
        '3K': '3000 Hz', '4K': '4000 Hz', '6K': '6000 Hz', '8K': '8000 Hz'
    }
    for col in aux_df.columns:
        if col == 'SEQN':
            continue
        ear = 'Right' if col.endswith('R') else 'Left' if col.endswith('L') else ''
        freq_code = col[4:-1]  # Extract middle part of column name
        freq_str = freq_map.get(freq_code, freq_code + ' Hz')
        aux_labels[col] = f'Hearing Threshold at {freq_str} ({ear} Ear, dB)'

    # 3️⃣ Histograms for right ear
    right_ear_cols = [col for col in aux_df.columns if col.endswith('R')]
    rows = 2
    cols = 4
    fig, axes = plt.subplots(rows, cols, figsize=(24, 12))
    for ax, col in zip(axes.flatten(), right_ear_cols):
        if aux_df[col].dropna().empty:
            ax.axis('off')  # Skip empty columns
            continue
        ax.hist(aux_df[col].dropna(), bins=20, color='lightgreen', edgecolor='black')
        wrapped_title = "\n".join(textwrap.wrap(aux_labels[col], width=25))
        ax.set_title(wrapped_title, fontsize=10)
        ax.set_xlabel('dB')
        ax.set_ylabel('Count')
    plt.tight_layout()
    plt.subplots_adjust(hspace=0.4, wspace=0.4)
    plt.show()

    # 4️⃣ Histograms for left ear
    left_ear_cols = [col for col in aux_df.columns if col.endswith('L')]
    fig, axes = plt.subplots(rows, cols, figsize=(24, 12))
    for ax, col in zip(axes.flatten(), left_ear_cols):
        if aux_df[col].dropna().empty:
            ax.axis('off')  # Skip empty columns
            continue
        ax.hist(aux_df[col].dropna(), bins=20, color='lightblue', edgecolor='black')
        wrapped_title = "\n".join(textwrap.wrap(aux_labels[col], width=25))
        ax.set_title(wrapped_title, fontsize=10)
        ax.set_xlabel('dB')
        ax.set_ylabel('Count')
    plt.tight_layout()
    plt.subplots_adjust(hspace=0.4, wspace=0.4)
    plt.show()
# -----------------------------
# Add dummy Age column for scatter plots
# -----------------------------
if 'RIDAGEYR' not in aux_df.columns:
    aux_df['RIDAGEYR'] = np.random.randint(18, 80, size=len(aux_df))

# 5️⃣ Scatter plots using dummy Age
def scatter_subplots(columns, ear_name, color):
    import matplotlib.pyplot as plt
    import textwrap

    if not columns:
        print(f"No {ear_name}-ear columns to plot.")
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
        wrapped_title = "\n".join(textwrap.wrap(f'Age vs {aux_labels[col]}', width=35))
        ax.set_title(wrapped_title, fontsize=10)
        ax.set_xlabel('Age (years)')
        ax.set_ylabel(aux_labels[col])

    # Turn off any unused axes
    for i in range(len(columns), len(axes)):
        axes[i].axis('off')

    plt.suptitle(f'Age vs Hearing Thresholds ({ear_name} Ear)', fontsize=16, y=1.02)
    plt.tight_layout()
    plt.subplots_adjust(hspace=0.5, wspace=0.4, top=0.95)
    plt.show()

# Right-ear scatter plots
right_ear_cols = [col for col in aux_df.columns if col.endswith('R')]
scatter_subplots(right_ear_cols, 'Right', 'green')

# Left-ear scatter plots
left_ear_cols = [col for col in aux_df.columns if col.endswith('L')]
scatter_subplots(left_ear_cols, 'Left', 'blue')
