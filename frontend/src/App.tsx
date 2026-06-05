import { useEffect, useState } from "react";

import { fetchRecent, fetchStats, socket } from "./api.ts";
import { HornMap } from "./components/HornMap.tsx";
import { LiveFeed } from "./components/LiveFeed.tsx";
import { StatsCharts } from "./components/StatsCharts.tsx";
import type { HornEvent, Stats } from "./types.ts";
import "./App.css";

const MAX_EVENTS = 200; // keep the in-browser list bounded

export default function App() {
  const [events, setEvents] = useState<HornEvent[]>([]);
  const [stats, setStats] = useState<Stats>({ total: 0, bySite: {} });
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    // 1. Snapshot: pull current state once on load (Lesson 10/11).
    fetchRecent(50).then(setEvents).catch(console.error);
    fetchStats().then(setStats).catch(console.error);

    // 2. Subscribe: live pushes update state, React re-renders everything.
    socket.on("connect", () => setConnected(true));
    socket.on("disconnect", () => setConnected(false));
    socket.on("horn", (e: HornEvent) => {
      setEvents((prev) => [e, ...prev].slice(0, MAX_EVENTS));
      setStats((s) => ({
        total: s.total + 1,
        bySite: { ...s.bySite, [e.location]: (s.bySite[e.location] ?? 0) + 1 },
      }));
    });

    // 3. Cleanup listeners when the component unmounts.
    return () => {
      socket.off("connect");
      socket.off("disconnect");
      socket.off("horn");
    };
  }, []);

  return (
    <div className="app">
      <header>
        <h1>🔊 Urban Horn Noise Intelligence</h1>
        <div className="status">
          <span className={connected ? "dot on" : "dot off"} />
          {connected ? "live" : "disconnected"}
          <span className="total">{stats.total} horns detected</span>
        </div>
      </header>

      <main>
        <HornMap events={events} />
        <div className="side">
          <StatsCharts stats={stats} events={events} />
          <LiveFeed events={events} />
        </div>
      </main>
    </div>
  );
}
