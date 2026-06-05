# Day 5 Report — Phase 4: REST API + Socket.IO
**Date:** 2026-06-04
**Phase:** 4 (Backend API + real-time push)
**Status:** ✅ Complete — REST snapshot reads + live Socket.IO push, verified.

## What was done today

1. **Learned REST vs WebSockets (Lesson 10).** REST = pull/request-response, ideal for the dashboard's initial snapshot. Socket.IO = persistent connection where the server pushes, ideal for live updates. A live dashboard needs both: pull the snapshot, then subscribe to the stream.
2. **Reader functions** in `backend/src/stores.ts`: `getRecent()` + `getStats()` (Redis), `getHistory({site,limit})` (Mongo).
3. **Unified server** `backend/src/server.ts` — one process that (a) runs the Kafka consumer, (b) serves Express REST, (c) holds Socket.IO connections. On each event it stores to Mongo + Redis AND `io.emit("horn", event)` to push live.
4. **REST endpoints:** `/api/health`, `/api/recent?limit=`, `/api/stats`, `/api/history?site=&limit=`. CORS enabled for the React dev server.
5. **Verified** with `src/test_client.ts` (Socket.IO client standing in for the dashboard): REST reads returned current state; producing 4 new horns pushed all 4 to the connected client live; `/api/stats` total grew 6 → 10 consistently.

## Architecture now
```
producer.py → Kafka → server.ts ─┬→ MongoDB (history)
                                  ├→ Redis (live state)
                                  ├→ REST  /api/recent /api/stats /api/history
                                  └→ Socket.IO  emit("horn") → browsers (live)
```

## Viva-prep questions for today's work

| Q | A |
|---|---|
| Why does the dashboard need both REST and WebSockets? | REST gives the initial snapshot (current stats, recent feed, history) via pull. WebSockets/Socket.IO keep a connection open so the server pushes new horns the instant they arrive — no polling. Snapshot once, then subscribe. |
| Which endpoints read Redis vs Mongo, and why? | `/api/recent` and `/api/stats` read Redis (fast in-memory live state for frequent dashboard reads). `/api/history` queries Mongo (durable, supports filtering/sorting for analytics). |
| How does a new horn reach the browser without a refresh? | The Kafka consumer (same server process) receives it, stores it, then `io.emit("horn", event)` pushes it over the open Socket.IO connection to every connected client. |
| Why is CORS enabled? | The React dev server runs on a different origin (port) than the API (4000). Browsers block cross-origin requests unless the server sends CORS headers. |

## Next (Day 6)
- **Phase 5:** React + Vite + TypeScript dashboard — fetch the snapshot from REST on load, subscribe to Socket.IO for live horns, render a Leaflet heatmap (using lat/lon), a live feed list, and Recharts time-series / per-site bar charts.
