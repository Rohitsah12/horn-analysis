# Day 4 Report — Phase 3: Storage Layer (MongoDB + Redis)
**Date:** 2026-06-04
**Phase:** 3 (Persistence)
**Status:** ✅ Complete — consumer writes every event to MongoDB (history) and Redis (live state).

## What was done today

1. **Learned the two-database pattern (Lesson 9).** Why one store can't serve both access patterns: durable, query-rich **history** vs. constantly-read **live state**. MongoDB (document DB) for the former, Redis (in-memory) for the latter.
2. **Enabled Redis + MongoDB in Docker.** Uncommented the Phase 3 block in `docker/docker-compose.yml` (redis:7-alpine, mongo:7) with named volumes (`redis-data`, `mongo-data`) so data survives `docker compose down`. Verified: Redis `PONG`, Mongo `ping=1`.
3. **Built the storage layer.** `backend/src/types.ts` holds the shared `HornEvent` contract. `backend/src/stores.ts`:
   - `saveToHistory(event)` → `insertOne` into `horn_analysis.events`; indexes on `timestamp` and `location`.
   - `updateLiveState(event)` → Redis `LPUSH`+`LTRIM` recent feed (cap 50), `HINCRBY` per-site counts, `INCR` total.
4. **Wired the consumer.** `backend/src/consumer.ts` now calls both writers for every event (dual-write).
5. **Verified both stores.** Ran producer (6 horns). MongoDB: 6 documents + an aggregation (horns per site, avg confidence). Redis: `horn:total=6`, per-site hash (Lygon 3, Rathdowne 2, Fitzroy 1), recent feed length 6. The two views are consistent.

## Architecture now
```
producer.py → Kafka(horn-events) → consumer.ts ─┬→ MongoDB  (durable history)
                                                 └→ Redis    (live: recent[], counts{}, total)
```

## Redis keys (the contract between writer and future API reader)
- `horn:recent` — list, newest-first, last 50 events (JSON strings)
- `horn:counts_by_site` — hash, site → count
- `horn:total` — integer counter

## Viva-prep questions for today's work

| Q | A |
|---|---|
| Why use two databases instead of one? | Two access patterns. MongoDB stores the full event history for rich analytical queries (write-once, read-occasionally). Redis holds live state in RAM for the dashboard's constant, microsecond reads. Neither tool is great at both jobs. |
| Why MongoDB (not SQL) for the events? | Events are already JSON documents with a possibly-evolving schema. A document DB ingests them directly and tolerates added fields without migrations. |
| Why Redis for live state, and which structures? | In-memory = microsecond reads for the dashboard. A list (`LPUSH`/`LTRIM`) for the recent feed, a hash (`HINCRBY`) for per-site counts, a counter (`INCR`) for the total — each updated in place. |
| What happens to the data on `docker compose down`? | Named volumes (`redis-data`, `mongo-data`) persist it on disk, so it survives restarts. A `down -v` would wipe the volumes. |
| What is "dual-write" and a risk of it? | Writing the same event to two stores for two read patterns. Risk: the two can drift if one write fails. Acceptable here (Kafka can replay; the analytics store is the source of truth). |

## Next (Day 5)
- **Phase 4:** REST API (Express) exposing the stored data — `/api/recent`, `/api/stats` (read from Redis), `/api/history` (query Mongo) — plus **Socket.IO** to push new events to the dashboard live as the consumer receives them.
