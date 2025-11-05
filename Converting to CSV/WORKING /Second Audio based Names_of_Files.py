import pandas as pd
import numpy as np
import glob, os
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.inspection import permutation_importance

# ----------------------------
# 1. Base directory
# ----------------------------
base_dir = "/Users/isabella/Library/Mobile Documents/com~apple~CloudDocs/Graduated/UCL EvidENT/DOWNLOADED DATA/CSV DATA/"

# ----------------------------
# 2. Detect Demographics folder
# ----------------------------
demo_folder = os.path.join(base_dir, "Demographic_Variables_Sample_Weights")
if os.path.exists(demo_folder) and os.path.isdir(demo_folder):
    print(f"✅ Using demographics folder: Demographic_Variables_Sample_Weights")
else:
    raise FileNotFoundError("❌ Could not find 'Demographic_Variables_Sample_Weights' folder in CSV DATA.")

# ----------------------------
# 3. Helper: load CSVs safely
# ----------------------------
def load_data(path_pattern, name=None):
    files = glob.glob(path_pattern)
    if not files:
        print(f"Warning: no files found for {name or path_pattern}")
        return pd.DataFrame()
    dfs = [pd.read_csv(f) for f in files if "SEQN" in pd.read_csv(f, nrows=1).columns]
    if not dfs:
        print(f"Skipping {name}: no SEQN found")
        return pd.DataFrame()
    return pd.concat(dfs, ignore_index=True)

# ----------------------------
# 4. Load datasets
# ----------------------------
au   = load_data(os.path.join(base_dir, "Audiometry/*.csv"), "Audiometry")
demo = load_data(os.path.join(demo_folder, "*.csv"), "Demographics")
bmx  = load_data(os.path.join(base_dir, "Body Measures/*.csv"), "Body Measures")
smq  = load_data(os.path.join(base_dir, "Smoking - Cigarette Use/*.csv"), "Smoking")
alq  = load_data(os.path.join(base_dir, "Alcohol Use/*.csv"), "Alcohol")
mcq  = load_data(os.path.join(base_dir, "Medical Conditions/*.csv"), "Medical Conditions")
diq  = load_data(os.path.join(base_dir, "Diabetes/*.csv"), "Diabetes")
ghb  = load_data(os.path.join(base_dir, "Glycohemoglobin/*.csv"), "HbA1c")
hep  = load_data(os.path.join(base_dir, "Hepatitis/*.csv"), "Hepatitis")
slq  = load_data(os.path.join(base_dir, "Sleep Disorders/*.csv"), "Sleep")

# ----------------------------
# 5. Merge datasets safely
# ----------------------------
if demo.empty:
    raise ValueError("No demographics data loaded. Check the folder contents.")

df = demo.copy()
for dset in [au, bmx, smq, alq, mcq, diq, ghb, hep, slq]:
    if not dset.empty and "SEQN" in dset.columns:
        df = df.merge(dset, on="SEQN", how="left")

# ----------------------------
# 6. Features
# ----------------------------
audiometry_features = [
    "AUXU1K1","AUXU2K1","AUXU3K1","AUXU4K1",  # Left ear thresholds 1–4 kHz
    "AUXU1K2","AUXU2K2","AUXU3K2","AUXU4K2"   # Right ear thresholds 1–4 kHz
]

classic_features = [
    "RIDAGEYR","RIAGENDR","RIDRETH1","DMDEDUC2","INDFMIN2", # demographics
    "BMXBMI","BMXWAIST","BPXSY1","BPXDI1",                  # body measures
    "SMQ020","SMQ040","ALQ120Q",                           # lifestyle
    "MCQ160E","DIQ010",                                    # diabetes
    "LBXGH","LBXGLU","LBXTC","LBDHDD","LBXTR"              # labs
]

exploratory_features = [
    "HSD010","HSD070",   # general health
    "SLQ050","SLQ100",   # sleep
    "LBXALT","LBXSAPSI", # liver
    "MCQ160B","MCQ160C", # CVD history
    "LBXHEPA","LBXHBS"   # infections (hepatitis markers)
]

all_features = [f for f in audiometry_features + classic_features + exploratory_features if f in df.columns]
df_features = df[all_features].copy()

# ----------------------------
# 7. Define hearing loss outcome
# ----------------------------
df["pta_left"]   = df[["AUXU1K1","AUXU2K1","AUXU3K1","AUXU4K1"]].mean(axis=1, skipna=True)
df["pta_right"]  = df[["AUXU1K2","AUXU2K2","AUXU3K2","AUXU4K2"]].mean(axis=1, skipna=True)
df["pta_better"] = df[["pta_left","pta_right"]].min(axis=1)
df["hearing_loss"] = (df["pta_better"] > 25).astype(int)  # WHO mild HL threshold

# ----------------------------
# 8. Preprocess
# ----------------------------
X = df_features.fillna(df_features.median())
X = pd.get_dummies(X, drop_first=True)
y = df["hearing_loss"]

# ----------------------------
# 9. Human-readable labels
# ----------------------------
feature_labels = {
    # Audiometry
    "AUXU1K1":"Left Ear 1kHz","AUXU2K1":"Left Ear 2kHz","AUXU3K1":"Left Ear 3kHz","AUXU4K1":"Left Ear 4kHz",
    "AUXU1K2":"Right Ear 1kHz","AUXU2K2":"Right Ear 2kHz","AUXU3K2":"Right Ear 3kHz","AUXU4K2":"Right Ear 4kHz",
    # Demographics
    "RIDAGEYR":"Age","RIAGENDR":"Sex","RIDRETH1":"Ethnicity","DMDEDUC2":"Education","INDFMIN2":"Family Income",
    # Lifestyle
    "SMQ020":"Current Smoker","SMQ040":"Cigs/Day","ALQ120Q":"Alcohol Use",
    # Body
    "BMXBMI":"BMI","BMXWAIST":"Waist","BPXSY1":"Systolic BP","BPXDI1":"Diastolic BP",
    # Diabetes / CVD
    "MCQ160E":"Doctor said diabetes","DIQ010":"Diabetes Questionnaire",
    "MCQ160B":"CHF","MCQ160C":"Heart Attack",
    # Labs
    "LBXGH":"HbA1c","LBXGLU":"Glucose","LBXTC":"Total Cholesterol","LBDHDD":"HDL","LBXTR":"Triglycerides",
    "LBXALT":"ALT","LBXSAPSI":"AST","LBXHEPA":"Hepatitis A","LBXHBS":"Hepatitis B",
    # General health / sleep
    "HSD010":"General Health","HSD070":"Health Limits Activity","SLQ050":"Sleep Trouble","SLQ100":"Sleep Apnea"
}

# ----------------------------
# 10. Train/test split
# ----------------------------
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# ----------------------------
# 11. Train model
# ----------------------------
model = RandomForestClassifier(n_estimators=300, random_state=42)
model.fit(X_train, y_train)

# ----------------------------
# 12. Evaluate
# ----------------------------
y_pred = model.predict(X_test)
print(classification_report(y_test, y_pred))
print("AUC:", roc_auc_score(y_test, model.predict_proba(X_test)[:,1]))

# ----------------------------
# 13. Permutation Importance
# ----------------------------
perm_result = permutation_importance(model, X_test, y_test, n_repeats=10, random_state=42)
perm_importances = perm_result.importances_mean
indices = np.argsort(perm_importances)[::-1]

labels = [feature_labels.get(f, f) for f in X.columns]

plt.figure(figsize=(10,10))
plt.barh(range(len(indices)), perm_importances[indices][::-1])
plt.yticks(range(len(indices)), [labels[i] for i in indices][::-1])
plt.xlabel("Permutation Importance (Decrease in Accuracy)")
plt.title("Feature Importance for Hearing Loss Prediction")
plt.tight_layout()
plt.show()
