/**
 * Two charts:
 *  - bar: horns per site (from the live stats)
 *  - line: horns over time, bucketed by minute (from the recent events)
 */
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { HornEvent, Stats } from "../types.ts";

function perMinute(events: HornEvent[]) {
  const buckets = new Map<string, number>();
  for (const e of events) {
    const d = new Date(e.timestamp);
    const key = `${d.getHours()}:${String(d.getMinutes()).padStart(2, "0")}`;
    buckets.set(key, (buckets.get(key) ?? 0) + 1);
  }
  return [...buckets.entries()]
    .map(([minute, horns]) => ({ minute, horns }))
    .reverse();
}

export function StatsCharts({
  stats,
  events,
}: {
  stats: Stats;
  events: HornEvent[];
}) {
  const bySite = Object.entries(stats.bySite)
    .map(([site, horns]) => ({ site, horns }))
    .sort((a, b) => b.horns - a.horns);
  const timeline = perMinute(events);

  return (
    <div className="panel charts">
      <h2>Horns per site</h2>
      <ResponsiveContainer width="100%" height={180}>
        <BarChart data={bySite}>
          <CartesianGrid strokeDasharray="3 3" stroke="#333" />
          <XAxis dataKey="site" stroke="#aaa" fontSize={11} />
          <YAxis stroke="#aaa" allowDecimals={false} fontSize={11} />
          <Tooltip />
          <Bar dataKey="horns" fill="#ff3b3b" />
        </BarChart>
      </ResponsiveContainer>

      <h2>Horns over time</h2>
      <ResponsiveContainer width="100%" height={160}>
        <LineChart data={timeline}>
          <CartesianGrid strokeDasharray="3 3" stroke="#333" />
          <XAxis dataKey="minute" stroke="#aaa" fontSize={11} />
          <YAxis stroke="#aaa" allowDecimals={false} fontSize={11} />
          <Tooltip />
          <Line type="monotone" dataKey="horns" stroke="#ffa93b" strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
