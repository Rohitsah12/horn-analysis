# Day 7 Report — Phase 6: Insights & Horn Discipline Score (FINAL)
**Date:** 2026-06-05
**Phase:** 6 (Insights + demo polish)
**Status:** ✅ Complete — project end-to-end functional.

## What was done today

1. **Learned insight design (Lesson 12).** Raw counts aren't actionable; an insight compresses data into a comparable, interpretable number (like a credit score). Designed the **Horn Discipline Score**: `HDS = 100 · e^(−horns / K)` (K=15), 100 = silent/disciplined, low = chronic honking. Exponential decay so a few horns don't tank the score but persistent honking drives it down sharply; bounded 0–100.
2. **Backend analytics** (`stores.ts` `getInsights()` + `disciplineScore()`), exposed at `GET /api/insights` — aggregates the durable MongoDB history into per-site scores (worst first) + a city average. This is *why* we kept Mongo.
3. **Dashboard panel** (`InsightsPanel.tsx`) — big city score + a color-graded ranking bar per site, computed live from the streaming stats (mirrors the backend formula) so it updates with every push.
4. **Verified:** `/api/insights` returns ranked scores; as horns streamed in, the city score moved 73 → 65 and Fitzroy surfaced as the worst offender (51) — the intended policy signal.

## The complete system
```
.wav → Python (MFCC+RF, F1 82.5%) → Kafka → Node server ─┬→ MongoDB (history → /api/insights)
                                                          ├→ Redis (live state)
                                                          └→ Socket.IO → React (map, charts, feed, HDS)
```

## Limitations / honest caveats (good viva material)
- **HDS scores volume, not rate.** A real metric would normalize by time window and traffic density (horns/hour/vehicle). Easy extension given the timestamps already stored.
- **Demo horns are injected** UrbanSound8K clips mixed into MELAUDIS traffic, because MELAUDIS has no horns. The detector and pipeline are real; the live feed is a realistic simulation.
- **Single-broker / single-node infra** (dev). Production would replicate Kafka and the DBs.
- **Recall ~79%** — the detector misses ~1 in 5 horns at the tuned threshold; tunable via the threshold knob per policy priorities.

## Viva-prep questions for today's work

| Q | A |
|---|---|
| What is the Horn Discipline Score and why exponential? | A 0–100 per-site metric, `100·e^(−horns/K)`. Exponential so the first horns barely move it but sustained honking drops it sharply, and it stays bounded 0–100 — more intuitive than a linear count. |
| Why compute it from MongoDB, not Redis? | Mongo holds the full durable history needed for correct aggregates over time; Redis only holds the recent/live slice. The dashboard panel mirrors the formula client-side for instant updates. |
| How would you make the score fairer? | Normalize by time window and traffic density (horns per hour per vehicle), and possibly weight by time of day (night honking penalised more). |

## Project status: COMPLETE
All six build phases done. See per-phase reports `day-01`…`day-07`. The system runs end to end: detect → stream → store → serve → visualise → score.
