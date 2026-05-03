# Day 1 Report — Phase 0 Setup
**Date:** 2026-05-03
**Phase:** 0 (Environment + Scaffolding)
**Status:** ✅ Complete

## What was done today

1. **Environment audit** — confirmed Python 3.14, Node 25, Docker 29, Git 2.52, Homebrew available. Installed `uv` (modern Python package manager) for clean Python 3.11 environments per project (avoids breaking system Python).
2. **Project scaffold** — created `horn-analysis/` with subfolders for `ml-service/`, `backend/`, `frontend/`, `docker/`, and `docs/`.
3. **Initial files** — wrote `.gitignore` (ignores datasets, models, node_modules, .env), `README.md` (project overview + tech stack + phase tracker), `docker/docker-compose.yml` (commented skeleton; services enabled phase-by-phase).
4. **Git** — initialized repo and made first commit.

## Decisions made

- **Python 3.11 (not 3.14)** for the ML service. Reason: librosa and TensorFlow consistently lag on the newest CPython. uv pins this per-project so system Python is untouched.
- **Docker Compose for infra** (Kafka/Redis/Mongo) rather than native installs. Reason: reproducible across machines; teardown is `docker compose down`.
- **Datasets gitignored.** MELAUDIS is several GB; lives only on local disk, not in version control.

## Viva-prep questions for today's work

| Q | A |
|---|---|
| Why a separate `ml-service/` folder rather than mixing Python with Node? | Python and Node are different runtimes and dependency systems. Keeping them physically separated mirrors the runtime separation and avoids package conflicts. |
| Why Docker for Kafka/Redis/Mongo instead of installing them natively? | Reproducibility (any teammate gets the exact same versions), easy teardown, no system pollution. One `docker compose up` command. |
| Why `uv` instead of `pip`? | uv is a fast, modern Python package + version manager. Pins Python version per project (we use 3.11 for ML compatibility), creates virtualenvs automatically, dependency resolution is 10–100× faster than pip. |
| Why is the `data/melaudis/` folder gitignored? | The dataset is several GB. Git is for source code, not data blobs. The folder structure is preserved with `.gitkeep`. |

## Next (Day 2)

Begin **Phase 1 — Python ML standalone**:
- Initialize uv project in `ml-service/`
- Install librosa, scikit-learn, jupyter, matplotlib
- Open one .wav file from MELAUDIS
- Plot waveform → understand what audio "looks like" as data
