# Day 6 Report — Phase 5: React Dashboard
**Date:** 2026-06-05
**Phase:** 5 (Live dashboard)
**Status:** ✅ Complete — React + Vite + TS dashboard: live map, charts, feed.

## What was done today

1. **Learned React's state→render model (Lesson 11).** UI is a function of state; updating state re-renders. `useEffect` runs side-effects (fetch snapshot, open socket) after mount and cleans them up.
2. **Scaffolded** `frontend/` with Vite (`react-ts`). Added `socket.io-client`, `leaflet`, `react-leaflet`, `recharts`.
3. **Data layer** `src/api.ts` — REST helpers (`fetchRecent`, `fetchStats`) + one shared Socket.IO connection to the backend (port 4000).
4. **Components:**
   - `HornMap.tsx` — Leaflet/OpenStreetMap, each horn a translucent `CircleMarker` at its lat/lon (red >80% confidence). Overlaps read as hotspots.
   - `StatsCharts.tsx` — Recharts bar (horns per site) + line (horns per minute).
   - `LiveFeed.tsx` — newest-first list; freshest row flashes.
5. **`App.tsx`** — the snapshot-then-subscribe pattern: on mount, REST-fetch the snapshot into state, then subscribe to `socket.on("horn")`; each push prepends to `events` and bumps `stats`, and React re-renders map + charts + feed automatically. Connection status dot + total in the header.
6. **Verified** the full stack live: backend + Vite dev server up, producer bursts → pins/feed/counters update in real time. `npm run build` passes (tsc + vite).

## Architecture (complete real-time path)
```
producer.py → Kafka → server.ts ─┬→ MongoDB / Redis
                                  └→ Socket.IO ──→ React (map + charts + feed, live)
                          REST  ──────────────────↑ (initial snapshot)
```

## Viva-prep questions for today's work

| Q | A |
|---|---|
| How does the dashboard show a new horn without refreshing? | `App.tsx` subscribes to Socket.IO once in `useEffect`. Each pushed event is prepended to React state; since the UI is a function of state, the map, charts, and feed re-render automatically. |
| Why fetch via REST AND subscribe via socket? | REST gives the initial snapshot on load (recent + stats); the socket delivers live updates after. Snapshot once, then stream. |
| Why CircleMarkers instead of a true heatmap plugin? | Simplicity — overlapping translucent circles convey density without an extra dependency. A `leaflet.heat` layer is a drop-in upgrade later. |
| What does the useEffect cleanup do? | Removes the socket listeners on unmount so we don't leak handlers or double-handle events on re-render. |

## Next (Day 7)
- **Phase 6:** compute the **Horn Discipline Score** per site from stored history (normalize horn rate → 0–100), add `/api/insights`, surface a ranking panel on the dashboard. Demo polish + viva prep.
