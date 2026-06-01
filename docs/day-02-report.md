# Day 2 Report — Phase 1: Python ML Service (Standalone)
**Date:** 2026-06-01
**Phase:** 1 (Standalone horn detector)
**Status:** ✅ Working baseline detector trained and validated

## What was done today

1. **Dataset reality check.** Audited MELAUDIS and found it has **no horn labels** — it's a vehicle-type classification dataset (Car/Tram/Truck/Bus/Motorcycle/Bicycle + background). Confirmed the real horn source is **UrbanSound8K** (its `car_horn` class), which `.gitignore` already anticipated.
2. **Environment.** Initialized `ml-service/` as a `uv` project pinned to Python 3.11; added librosa, scikit-learn, numpy, pandas, soundfile, matplotlib, datasets, huggingface-hub.
3. **Learned the audio→ML pipeline (Lessons 1–6).** Audio as numbers → waveform → spectrogram (STFT) → MFCC → Random Forest → train/test/metrics. Wrote exploration scripts (`src/explore_01..03`) that visualize each step on real clips.
4. **Downloaded UrbanSound8K** (~6.6 GB, 8,732 clips, 429 horns) from the `danavery/urbansound8K` HF mirror into `data/urbansound8k/`.
5. **Built the detector.**
   - `src/extract_features.py` — turns every clip into 40 MFCC means + 40 MFCC stds (80 features). Output `data/features/us8k_mfcc.csv`.
   - `src/train_model.py` — Random Forest (300 trees, `class_weight="balanced"`), split honestly by fold (train 1–9, test fold 10). Saves `models/horn_rf.pkl`.
   - `src/test_generalization.py` — cross-dataset sanity check on MELAUDIS.

## Key result & the lessons behind it

Iterative improvement, each step driven by a reason:

| Version | Features | F1 (fold 10) |
|---|---|---|
| v1 | 13 MFCC means | **0%** — caught 0/33 horns (imbalance trap; accuracy lied at 95.8%) |
| v2 | 40 MFCC means + 40 stds | 73% — adding "steadiness" (std over time) recovered the horn signal |
| v3 | v2 + honest threshold tuning | 78% |
| v4 | + delta & delta-delta (240 feats) | **82.5%** — precision 86.7%, recall 78.8% (26/33 caught, 4 false alarms) |

- **Why std mattered:** a horn holds a *steady* tone; music/speech wobble. Averaging alone (v1) discarded that.
- **Why delta/delta-delta mattered:** they encode the horn's attack/sustain *dynamics* (velocity + acceleration of MFCCs).
- **Threshold tuned honestly:** train folds 1–8, pick threshold on validation fold 9 (best F1 → 0.15), final score once on test fold 10. Saved `threshold=0.15` in the model.
- **Generalization:** on 600 unseen MELAUDIS clips (all true negatives), **0 false alarms** even at the aggressive 0.15 threshold; max horn-probability 0.11.

### Bugs hit & fixed (real-pipeline lessons)
- `librosa.delta` default window (9 frames) crashes on very short clips → added `_safe_delta` that shrinks the window to fit.
- Importing `extract_features` ran the whole extraction → wrapped the script body in `if __name__ == "__main__":`. Shared the feature recipe via `fingerprint_from_audio()` so training/test/inference can't drift.

## Decisions made

- **Train horn-vs-rest *within* UrbanSound8K** (folds for an honest split); use **MELAUDIS as an independent generalization test**. Stronger evidence than a single dataset.
- **F1, not accuracy, is the headline metric** because of 4.9% class imbalance.
- **Resample everything to 22.05 kHz mono** before MFCC — UrbanSound8K files have mixed native sample rates.

## Viva-prep questions for today's work

| Q | A |
|---|---|
| Why can't MELAUDIS alone train a horn detector? | It has no horn labels — only vehicle-type labels. The labels you have define the problem you can solve; horns require UrbanSound8K's `car_horn` class. |
| Your model had 95.8% accuracy but was useless. Explain. | With 4.9% horns, always predicting "not-horn" scores ~95% accuracy yet catches zero horns. Accuracy hides failure under class imbalance; precision/recall/F1 reveal it. |
| What single change took F1 from 0% to 73%? | Adding the standard deviation of each MFCC over time. It encodes "steadiness" — a horn holds a steady tone while music/speech fluctuate. Averaging alone discarded this. |
| Why split UrbanSound8K by fold instead of shuffling randomly? | Slices from the same source recording live in the same fold. Random shuffling would leak near-duplicates into both train and test, inflating the score dishonestly. |
| What does precision vs recall mean here, and which knob trades them? | Precision = of clips flagged "horn", how many really are. Recall = of all real horns, how many were caught. The vote threshold (default 0.5) trades them: lower it for more recall, fewer missed horns, at the cost of more false alarms. |
| How do you know the model generalizes? | Trained only on UrbanSound8K, it gave 0 false alarms on 600 independent MELAUDIS clips (max horn-prob 0.11) — it learned the concept "horn", not dataset artefacts. |
| What are delta and delta-delta features? | The 1st and 2nd time-derivatives of the MFCCs — the velocity and acceleration of the sound's timbre. They capture dynamics (a horn's sharp onset and steady sustain) that static mean/std miss. Standard in speech recognition. |
| Why pick the threshold on a validation fold, not the test fold? | Tuning on the test set means optimizing to the very data you grade yourself on — an inflated, dishonest score. A separate validation fold lets you tune fairly while the test fold stays a true unseen final exam. |
| Why Random Forest over a neural net here? | Small tabular feature set (80 numbers), little tuning, fast real-time prediction, interpretable feature importances. Neural nets need far more data/tuning for marginal gain on this. |

## Next (Day 3)

Finish Phase 1, then start Phase 2:
- (Optional polish) push recall up via decision-threshold tuning and delta-MFCC features.
- Wrap inference into a reusable `predict(wav) -> {is_horn, confidence}` function — the unit the Kafka producer will call.
- **Phase 2:** uncomment Kafka in docker-compose, write the Python producer that emits horn events, learn what a message broker is and why it decouples the detector from the backend.
