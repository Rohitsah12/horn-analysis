"""
Step 2 of the real detector: train the Random Forest (Lesson 5) and judge it
with honest metrics (Lesson 6) — now with delta features and HONEST threshold
tuning.

Run with:  uv run python src/train_model.py

Three-way split so tuning doesn't cheat (Lesson 6):
  - Train      : folds 1-8   (the forest learns)
  - Validation : fold 9      (we pick the decision threshold here)
  - Test       : fold 10     (locked vault; final honest score, touched once)
"""

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (classification_report, confusion_matrix,
                             precision_recall_fscore_support)

FEATURES = Path("data/features/us8k_mfcc.csv")
MODEL_OUT = Path("models/horn_rf.pkl")
MODEL_OUT.parent.mkdir(exist_ok=True)

df = pd.read_csv(FEATURES)
feat_cols = [c for c in df.columns if c not in ("fold", "label", "class")]
print(f"Using {len(feat_cols)} features per clip.")

train = df[df.fold <= 8]
val = df[df.fold == 9]
test = df[df.fold == 10]
Xtr, ytr = train[feat_cols].values, train.label.values
Xva, yva = val[feat_cols].values, val.label.values
Xte, yte = test[feat_cols].values, test.label.values
print(f"Train {len(train)} ({ytr.sum()} horns) | "
      f"Val {len(val)} ({yva.sum()} horns) | Test {len(test)} ({yte.sum()} horns)")

# ---- Train the forest (Lesson 5) ----
clf = RandomForestClassifier(
    n_estimators=400, class_weight="balanced", n_jobs=-1, random_state=42)
clf.fit(Xtr, ytr)


def metrics_at(X, y, thr):
    """Precision/recall/F1 when we call 'horn' if horn-probability >= thr."""
    prob = clf.predict_proba(X)[:, 1]
    pred = (prob >= thr).astype(int)
    p, r, f, _ = precision_recall_fscore_support(
        y, pred, average="binary", zero_division=0)
    return p, r, f, pred


# ---- Sweep thresholds on VALIDATION, pick the best F1 (honest tuning) ----
print("\nThreshold sweep on validation fold 9 (pick best F1 here):")
print("  thr   precision  recall    F1")
best_thr, best_f1 = 0.5, -1.0
for thr in np.arange(0.10, 0.91, 0.05):
    p, r, f, _ = metrics_at(Xva, yva, thr)
    star = ""
    if f > best_f1:
        best_f1, best_thr, star = f, thr, "  <-- best"
    print(f"  {thr:.2f}   {p*100:5.1f}    {r*100:5.1f}   {f*100:5.1f}{star}")
print(f"\nChosen threshold (from validation): {best_thr:.2f}")

# ---- FINAL honest score on the locked test fold 10, at chosen threshold ----
p, r, f, pred = metrics_at(Xte, yte, best_thr)
print("\n============ FINAL RESULTS (test fold 10) ============")
print(f"At default 0.50 threshold: F1 = {metrics_at(Xte, yte, 0.50)[2]*100:.1f}%")
print(f"At tuned {best_thr:.2f} threshold:  "
      f"Precision {p*100:.1f}%  Recall {r*100:.1f}%  F1 {f*100:.1f}%")

cm = confusion_matrix(yte, pred)
print("\nConfusion matrix (rows=truth, cols=prediction):")
print(f"                 pred not-horn   pred horn")
print(f"  truth not-horn      {cm[0,0]:5d}        {cm[0,1]:4d}   <- false alarms")
print(f"  truth horn          {cm[1,0]:5d}        {cm[1,1]:4d}   <- {cm[1,1]} caught, {cm[1,0]} missed")
print("\n" + classification_report(yte, pred,
      target_names=["not-horn", "horn"], zero_division=0))

# ---- Save model + the tuned threshold for the pipeline ----
joblib.dump({"model": clf, "features": feat_cols,
             "target_sr": 22050, "threshold": float(best_thr)}, MODEL_OUT)
print(f"Saved model + threshold {best_thr:.2f} to {MODEL_OUT}")
