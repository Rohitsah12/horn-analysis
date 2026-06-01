"""
Lesson 1 & 2: Audio as data, and what sound "looks like".

Run with:  uv run python src/explore_01_audio_as_data.py

The whole point of this script is to PROVE to your own eyes that a .wav file
is just a long list of numbers, and then to plot those numbers so you can see
the shape of the sound.
"""

from pathlib import Path

import librosa          # the audio-loading + analysis library
import numpy as np      # numbers / arrays
import matplotlib
matplotlib.use("Agg")   # "Agg" = render to an image file instead of a popup window
import matplotlib.pyplot as plt

# ----------------------------------------------------------------------
# 1. Pick one real clip from YOUR dataset.
# ----------------------------------------------------------------------
# This is a 2-second single-vehicle clip from MELAUDIS. Any clip works for
# learning what audio "is" — we are not classifying anything yet.
DATA = Path("data/melaudis/27115870/Final_Veh/SW_03")
clip_path = sorted(DATA.glob("*.wav"))[0]
print(f"Loading: {clip_path.name}\n")

# ----------------------------------------------------------------------
# 2. Load it. This is the key line.
# ----------------------------------------------------------------------
# librosa.load returns:
#   y  -> the list of numbers (the waveform). A NumPy array.
#   sr -> the sample rate (how many numbers per second).
#
# sr=None    means "keep the file's real sample rate" (48000 here).
# mono=True  means "if stereo, average the 2 channels into 1 list" so we
#            always get a single 1-D list of numbers. Simpler to reason about.
y, sr = librosa.load(clip_path, sr=None, mono=True)

# ----------------------------------------------------------------------
# 3. Look at what we got. THIS is the mental model made concrete.
# ----------------------------------------------------------------------
print("=== Audio is just numbers ===")
print(f"Type of y:            {type(y).__name__}")          # numpy.ndarray
print(f"How many numbers:     {y.shape[0]:,}")              # ~96,000
print(f"Sample rate (sr):     {sr:,} numbers per second")   # 48,000
print(f"Duration:             {y.shape[0] / sr:.2f} seconds")
print()
print(f"The first 10 numbers: {np.round(y[:10], 4)}")
print(f"Smallest value:       {y.min():.4f}")
print(f"Largest value:        {y.max():.4f}")
print()
print("Notice: every value sits between about -1.0 and +1.0.")
print("That is the 'height' of the sound wave at each instant, scaled.")
print("Silence ~ 0. Loud ~ near -1 or +1.")

# ----------------------------------------------------------------------
# 4. Plot those numbers so you can SEE the sound.
# ----------------------------------------------------------------------
# x-axis = time in seconds, y-axis = the height value. Plotting the list of
# numbers in order IS the waveform.
time_axis = np.arange(y.shape[0]) / sr   # convert sample index -> seconds

plt.figure(figsize=(11, 3))
plt.plot(time_axis, y, linewidth=0.5)
plt.title(f"Waveform — {clip_path.name}")
plt.xlabel("Time (seconds)")
plt.ylabel("Amplitude (wave height)")
plt.tight_layout()

out = Path("notebooks/01_waveform.png")
out.parent.mkdir(exist_ok=True)
plt.savefig(out, dpi=110)
print(f"\nSaved a picture of the sound to: {out}")
print("Open it: you are literally looking at those 96,000 numbers plotted in order.")
