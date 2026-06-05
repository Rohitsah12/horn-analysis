"""
Generalization test: the model was trained ONLY on UrbanSound8K. Does it hold
up on a completely independent dataset — real Melbourne street recordings
(MELAUDIS) it has never seen?

MELAUDIS has NO horns, so every clip here is a true negative. The question is:
how often does the model FALSE-ALARM (cry "horn" at ordinary traffic)?
A low false-alarm rate = the model learned "horn", not "UrbanSound8K quirks".

Run with:  uv run python src/test_generalization.py
"""

from pathlib import Path

import joblib
import librosa
import numpy as np

# Reuse the EXACT same feature recipe as training (no drift).
from extract_features import fingerprint_from_audio

N_SAMPLE = 600  # how many MELAUDIS clips to test

bundle = joblib.load("models/horn_rf.pkl")
model = bundle["model"]
thr = bundle["threshold"]
print(f"Loaded model (decision threshold = {thr:.2f}, "
      f"{len(bundle['features'])} features).")

ROOT = Path("data/melaudis/27115870")
clips = (sorted(ROOT.glob("Final_Veh/*/*.wav"))[:N_SAMPLE // 2]
         + sorted(ROOT.glob("_BG_Final/*.wav"))[:N_SAMPLE // 2])

X = np.array([fingerprint_from_audio(*librosa.load(p, sr=None, mono=True))
              for p in clips])
prob = model.predict_proba(X)[:, 1]      # horn-probability per clip
pred = (prob >= thr).astype(int)         # 1 = horn (= false alarm here)

false_alarms = int(pred.sum())
print(f"\nTested {len(clips)} real Melbourne clips (all genuinely NOT horns).")
print(f"False alarms at threshold {thr:.2f}: {false_alarms} "
      f"({false_alarms/len(clips)*100:.1f}%)")
print(f"True-negative rate: {(1 - false_alarms/len(clips))*100:.1f}%")
print(f"Highest horn-probability assigned to any clip: {prob.max():.2f}")
print("\nLow false-alarm rate here = the model generalizes across datasets.")
