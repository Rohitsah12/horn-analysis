# Real-Time Urban Horn Noise Intelligence System

**College Final-Year Project** — Acoustic Analysis of Vehicle Horn Usage: Insights for Urban Noise Management and Policy Redesign.

## What this project does

Detects vehicle horns from audio in real-time, streams the events through a distributed pipeline, stores them, visualizes them on a live dashboard, and produces policy-relevant insights for urban noise management.

## Architecture

```
Audio (.wav)  →  Python (MFCC + Random Forest)  →  Kafka  →  Node.js
                                                                 ├─→  Redis (hot cache, live feed, scores)
                                                                 ├─→  MongoDB (history)
                                                                 └─→  Socket.IO  →  React Dashboard
```

## Tech Stack

| Layer | Tech | Why |
|---|---|---|
| ML / Audio | Python 3.11, librosa, scikit-learn (Random Forest) | Mature audio + ML libs |
| Message broker | Apache Kafka (via Docker) | Decouples Python detector from Node backend |
| Backend | Node.js + Express + TypeScript | Strong fit, async-friendly |
| Hot cache | Redis | Microsecond reads for live dashboard |
| Database | MongoDB | Flexible event schema, free Atlas tier |
| Real-time | Socket.IO | Push events to dashboard live |
| Frontend | React + Vite + TypeScript | Modern, fast dev server |
| Maps | Leaflet + OpenStreetMap | Free, no billing |
| Charts | Recharts | Easy time-series + bar charts |
| Orchestration | Docker Compose | One-command Kafka + Redis + Mongo |

## Project Structure

```
horn-analysis/
├── ml-service/         # Python: audio feature extraction + model training + Kafka producer
│   ├── data/melaudis/  # MELAUDIS dataset (gitignored)
│   ├── models/         # Trained model artifacts (.pkl)
│   ├── notebooks/      # Exploration notebooks
│   └── src/            # Production scripts
├── backend/            # Node + TS: Kafka consumer, Express API, Socket.IO
│   └── src/
├── frontend/           # React + TS: dashboard
├── docker/             # docker-compose.yml for Kafka, Redis, MongoDB
└── docs/               # Daily reports, viva-prep notes
```

## Build Phases

| Phase | Goal | Status |
|---|---|---|
| 0 | Environment setup, folder scaffold | ✅ Day 1 (May 3, 2026) |
| 1 | Python ML service standalone | ✅ Day 2 (Jun 4, 2026) — RF horn detector, F1 82.5%, 0 false alarms on MELAUDIS |
| 2 | Add Kafka pipeline (Python → Node) | ✅ Day 3 — full Python→Kafka→Node loop, offset-resume verified |
| 3 | Add MongoDB + Redis storage | ✅ Day 4 — consumer writes Mongo (history) + Redis (live state) |
| 4 | REST APIs + Socket.IO | ✅ Day 5 — Express REST + Socket.IO live push, verified |
| 5 | React dashboard (live feed, heatmap, charts) | ⏳ |
| 6 | Insights, Horn Discipline Score, demo polish | ⏳ |

**Target completion:** June 1, 2026.

## References

- MELAUDIS dataset: https://doi.org/10.6084/m9.figshare.27115870
- Lemaitre et al. 2007 — Psychoacoustical study of car horn timbre
- Parineh et al. 2025 — MELAUDIS benchmark for ITS research
