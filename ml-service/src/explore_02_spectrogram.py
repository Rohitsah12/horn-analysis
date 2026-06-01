"""
Lesson 3: The spectrogram — turning the waveform into a picture of
frequencies over time, using the Short-Time Fourier Transform (STFT).

Run with:  uv run python src/explore_02_spectrogram.py

We make spectrograms for two different clips side by side so you can SEE
that different sounds have different frequency "fingerprints".
"""

from pathlib import Path

import librosa
import librosa.display          # helper that draws spectrograms nicely
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path("data/melaudis/27115870")

# Two clips of different character:
#   - a vehicle pass-by (engine + tyre = broadband noise)
#   - a background/traffic clip
clips = {
    "Vehicle pass-by": sorted((ROOT / "Final_Veh/SW_03").glob("*.wav"))[0],
    "Background traffic": sorted((ROOT / "_BG_Final").glob("*.wav"))[0],
}

fig, axes = plt.subplots(1, 2, figsize=(14, 4.5))

for ax, (label, path) in zip(axes, clips.items()):
    y, sr = librosa.load(path, sr=None, mono=True)

    # ---- The STFT: chop into windows, FFT each window ----
    # n_fft   = window size in samples. 2048 samples / 48000 Hz ~= 43 ms per window.
    # hop_length = how far we slide between windows. 512 = lots of overlap = smooth.
    n_fft, hop = 2048, 512
    stft = librosa.stft(y, n_fft=n_fft, hop_length=hop)

    # stft is COMPLEX (it carries strength + phase). We only want strength,
    # so take the magnitude with np.abs, then convert to decibels (dB) because
    # human hearing is logarithmic and dB makes faint detail visible.
    magnitude = np.abs(stft)
    db = librosa.amplitude_to_db(magnitude, ref=np.max)

    print(f"{label:20s} -> spectrogram shape {db.shape}  "
          f"(= {db.shape[0]} frequency bins  x  {db.shape[1]} time windows)")

    img = librosa.display.specshow(
        db, sr=sr, hop_length=hop,
        x_axis="time", y_axis="hz", ax=ax, cmap="magma",
    )
    ax.set_title(label)
    ax.set_ylim(0, 8000)        # zoom to 0-8 kHz where most of the action is
    fig.colorbar(img, ax=ax, format="%+2.0f dB")

plt.tight_layout()
out = Path("notebooks/02_spectrograms.png")
plt.savefig(out, dpi=110)
print(f"\nSaved comparison to: {out}")
print("Bright HORIZONTAL lines = steady tones (what a horn looks like).")
print("Diffuse vertical smear  = broadband noise (engines, tyres, wind).")
