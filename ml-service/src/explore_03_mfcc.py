"""
Lesson 4: MFCC — the compact "timbre fingerprint" of a sound.

Run with:  uv run python src/explore_03_mfcc.py

We compute MFCCs for one clip, show the 13 x 188 matrix, then collapse it
to ONE 13-number fingerprint per clip (mean over time) — the exact feature
we will feed the model in Lesson 5.
"""

from pathlib import Path

import librosa
import librosa.display
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path("data/melaudis/27115870")
clip = sorted((ROOT / "Final_Veh/SW_03").glob("*.wav"))[0]

y, sr = librosa.load(clip, sr=None, mono=True)

# ---- Compute MFCCs ----
# n_mfcc=13 -> keep the first 13 cepstral coefficients (the standard choice).
# Under the hood librosa does: STFT -> Mel filterbank (~40 bands) -> log -> DCT.
mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
print(f"MFCC matrix shape: {mfcc.shape}  (13 coefficients x time windows)")
print(f"That is {mfcc.size:,} numbers — vs {y.size:,} raw samples. Big shrink.\n")

# ---- Collapse time -> ONE fingerprint per clip ----
# A horn is a horn no matter WHEN in the clip it happens, so we average each
# coefficient across all time windows. 13 numbers describe the whole clip.
fingerprint = mfcc.mean(axis=1)
print("The 13-number fingerprint for this clip (mean of each coefficient):")
print(np.round(fingerprint, 2))
print("\nThis 13-vector is exactly what one row of our training table will be.")

# ---- Picture it ----
fig, ax = plt.subplots(figsize=(11, 3.5))
img = librosa.display.specshow(mfcc, x_axis="time", sr=sr, ax=ax, cmap="viridis")
ax.set_title(f"MFCC (13 coefficients over time) — {clip.name}")
ax.set_ylabel("MFCC coefficient #")
fig.colorbar(img, ax=ax)
plt.tight_layout()
out = Path("notebooks/03_mfcc.png")
plt.savefig(out, dpi=110)
print(f"\nSaved MFCC picture to: {out}")
