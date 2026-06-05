"""
The reusable inference unit: given audio, decide horn / not-horn + confidence.

This is the single place the rest of the system (the Kafka producer in Phase 2)
will call. It loads the trained model once and reuses the EXACT training-time
feature recipe and tuned decision threshold — so production behaviour matches
the evaluation we trusted in Phase 1.

CLI:    uv run python src/predict.py path/to/clip.wav
Import: from predict import HornDetector
        det = HornDetector(); det.predict_file("clip.wav")
            -> {"is_horn": True, "confidence": 0.83}
"""

import sys
from functools import lru_cache
from pathlib import Path

import joblib
import librosa

from extract_features import fingerprint_from_audio

DEFAULT_MODEL = Path("models/horn_rf.pkl")


class HornDetector:
    def __init__(self, model_path: Path = DEFAULT_MODEL):
        bundle = joblib.load(model_path)
        self.model = bundle["model"]
        self.threshold = bundle["threshold"]   # tuned on validation (0.15)
        self.features = bundle["features"]

    def predict_audio(self, y, sr) -> dict:
        """Classify an already-loaded waveform."""
        fp = fingerprint_from_audio(y, sr).reshape(1, -1)
        # probability that the clip is a horn = fraction of trees voting 'horn'
        confidence = float(self.model.predict_proba(fp)[0, 1])
        return {"is_horn": confidence >= self.threshold,
                "confidence": round(confidence, 3)}

    def predict_file(self, path) -> dict:
        """Classify a .wav file on disk."""
        # mono=True -> librosa returns a clean 1-D waveform, avoiding the
        # channels-first vs samples-first ambiguity between audio libraries.
        y, sr = librosa.load(path, sr=None, mono=True)
        return self.predict_audio(y, sr)


@lru_cache(maxsize=1)
def get_detector() -> HornDetector:
    """Load the model once and cache it (loading a forest isn't free)."""
    return HornDetector()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: uv run python src/predict.py path/to/clip.wav")
    result = get_detector().predict_file(sys.argv[1])
    verdict = "HORN" if result["is_horn"] else "not-horn"
    print(f"{verdict}  (confidence {result['confidence']:.2f})")
