# Step 6: Visualizations
# -----------------------------

import textwrap  # for wrapping long titles

if demo_df is None or aux_df is None:
    print("Data not loaded. Check your data folder structure.")
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
        ax.hist(aux_df[col].dropna(), bins=20, color='lightblue', edgecolor='black')
        wrapped_title = "\n".join(textwrap.wrap(aux_labels[col], width=25))
        ax.set_title(wrapped_title, fontsize=10)
        ax.set_xlabel('dB')
        ax.set_ylabel('Count')
    plt.tight_layout()
    plt.subplots_adjust(hspace=0.4, wspace=0.4)
    plt.show()

    # 5️⃣ Scatter plots: Age vs each auxiliary measurement
    merged_df = pd.merge(demo_df, aux_df, on='SEQN', how='inner')
    for col in aux_df.columns:
        if col == 'SEQN':
            continue
        plot_df = merged_df[['RIDAGEYR', col]].dropna()
        plt.scatter(plot_df['RIDAGEYR'], plot_df[col], alpha=0.6)
        plt.title(f'Age vs {aux_labels[col]}')
        plt.xlabel('Age (years)')
        plt.ylabel(aux_labels[col])
        plt.show()