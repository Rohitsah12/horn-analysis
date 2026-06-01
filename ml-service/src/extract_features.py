"""
Step 1 of the real detector: turn every UrbanSound8K clip into a row of
features. This applies Lessons 1-4 (audio -> MFCC fingerprint) to all 8,732
clips and writes one big table we can train on.

Run with:  uv run python src/extract_features.py

Output: data/features/us8k_mfcc.csv
  columns: mean_0..mean_39, std_0..std_39, fold, label, class
  label = 1 if the clip is a car_horn, else 0  (our binary target)

We keep BOTH the mean (timbre) AND the std-over-time (steadiness) of 40 MFCCs.
The std is what tells a steady horn apart from wobbly music/speech — averaging
alone (our first attempt) threw that signal away and the model caught 0 horns.
"""

import glob
import io
from pathlib import Path

import librosa
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import soundfile as sf

# All clips get resampled to this rate so every fingerprint is comparable.
# UrbanSound8K files have MIXED sample rates (they came from Freesound), so we
# MUST standardize — otherwise "frequency bin 5" means different Hz per clip.
TARGET_SR = 22050
N_MFCC = 40

SHARDS = sorted(glob.glob("data/urbansound8k/data/*.parquet"))
OUT = Path("data/features/us8k_mfcc.csv")
OUT.parent.mkdir(parents=True, exist_ok=True)


def _safe_delta(mfcc: np.ndarray, order: int) -> np.ndarray:
    """librosa.delta needs an odd window >= 3 that fits the number of time
    frames. Very short clips have few frames, so pick the largest valid window
    (and return zeros if the clip is too short for any delta at all)."""
    n_frames = mfcc.shape[1]
    if n_frames < 3:
        return np.zeros_like(mfcc)
    width = min(9, n_frames if n_frames % 2 == 1 else n_frames - 1)
    return librosa.feature.delta(mfcc, order=order, width=width)


def fingerprint_from_audio(y: np.ndarray, sr: int) -> np.ndarray:
    """Core feature extractor: a waveform -> 240-number fingerprint.

    Shared by training (UrbanSound8K bytes), the generalization test (MELAUDIS
    files), and live inference, so the feature recipe can never drift apart.

    For MFCC, its delta (velocity) and delta-delta (acceleration), we keep the
    mean (timbre/dynamics) AND the std (variability) over time: 40 x 2 x 3 = 240.
    """
    # force mono: average channels if stereo (Lesson 1).
    if y.ndim > 1:
        y = y.mean(axis=1)
    # resample to a common rate so all clips line up.
    if sr != TARGET_SR:
        y = librosa.resample(y, orig_sr=sr, target_sr=TARGET_SR)
    # MFCC matrix (40 x time) (Lesson 4).
    mfcc = librosa.feature.mfcc(y=y, sr=TARGET_SR, n_mfcc=N_MFCC)
    # delta = velocity, delta-delta = acceleration: the attack/sustain dynamics
    # that static stats miss. Short clips shrink the smoothing window.
    delta = _safe_delta(mfcc, order=1)
    delta2 = _safe_delta(mfcc, order=2)
    # summarize each over time with mean + std.
    parts = []
    for mat in (mfcc, delta, delta2):
        parts.append(mat.mean(axis=1))
        parts.append(mat.std(axis=1))
    return np.concatenate(parts)


def fingerprint(wav_bytes: bytes) -> np.ndarray:
    """Decode raw .wav bytes (from UrbanSound8K parquet) -> 240-number vector."""
    y, sr = sf.read(io.BytesIO(wav_bytes), dtype="float32")
    return fingerprint_from_audio(y, sr)


FEATURE_NAMES = [
    f"{kind}_{stat}_{i}"
    for kind in ("mfcc", "d1", "d2")
    for stat in ("mean", "std")
    for i in range(N_MFCC)
]


def main():
    """Extract features for every clip and write the table. Runs ONLY when this
    file is executed directly — importing it (e.g. for fingerprint_from_audio)
    does not trigger a multi-minute re-extraction."""
    rows = []
    total = 0
    for shard in SHARDS:
        table = pq.read_table(shard)  # columns: audio{bytes,path}, class, fold
        audio = table.column("audio").to_pylist()
        classes = table.column("class").to_pylist()
        folds = table.column("fold").to_pylist()
        for au, cls, fold in zip(audio, classes, folds):
            fp = fingerprint(au["bytes"])
            rows.append({
                **dict(zip(FEATURE_NAMES, fp)),
                "fold": fold,
                "label": 1 if cls == "car_horn" else 0,
                "class": cls,
            })
            total += 1
            if total % 500 == 0:
                print(f"  ...processed {total} clips")

    df = pd.DataFrame(rows)
    df.to_csv(OUT, index=False)

    print(f"\nDone. Wrote {len(df)} rows to {OUT}")
    print(f"Horns (label=1):     {int(df.label.sum())}")
    print(f"Not-horns (label=0): {int((df.label == 0).sum())}")
    print(f"\nThis imbalance ({df.label.mean()*100:.1f}% horns) is exactly why we")
    print("will use precision/recall/F1, not raw accuracy (Lesson 6).")


if __name__ == "__main__":
    main()
