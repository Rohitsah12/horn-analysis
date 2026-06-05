/**
 * The data layer: REST calls for the initial snapshot + a Socket.IO connection
 * for the live stream. Both point at the Phase 4 backend on port 4000.
 */
import { io } from "socket.io-client";

import type { HornEvent, Stats } from "./types.ts";

const BASE = "http://localhost:4000";

export async function fetchRecent(limit = 50): Promise<HornEvent[]> {
  const res = await fetch(`${BASE}/api/recent?limit=${limit}`);
  return res.json();
}

export async function fetchStats(): Promise<Stats> {
  const res = await fetch(`${BASE}/api/stats`);
  return res.json();
}

// One shared socket for the whole app. The server pushes "horn" events here.
export const socket = io(BASE, { autoConnect: true });
