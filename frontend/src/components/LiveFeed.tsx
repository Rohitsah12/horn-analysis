/** The scrolling live feed: newest horn at the top. */
import type { HornEvent } from "../types.ts";

function timeAgo(iso: string): string {
  const d = new Date(iso).toLocaleTimeString();
  return d;
}

export function LiveFeed({ events }: { events: HornEvent[] }) {
  return (
    <div className="panel feed">
      <h2>Live feed</h2>
      <ul>
        {events.map((e, i) => (
          <li key={e.event_id} className={i === 0 ? "fresh" : ""}>
            <span className="loc">🔊 {e.location}</span>
            <span className="conf">{(e.confidence * 100).toFixed(0)}%</span>
            <span className="time">{timeAgo(e.timestamp)}</span>
          </li>
        ))}
        {events.length === 0 && <li className="empty">waiting for horns…</li>}
      </ul>
    </div>
  );
}
