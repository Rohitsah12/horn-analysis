/**
 * Phase 6: the Horn Discipline Score panel (Lesson 12).
 * Computed live from the current stats so it updates with every push.
 * Mirrors the backend formula in stores.ts (HDS = 100 * e^(-horns / K)).
 */
import type { Stats } from "../types.ts";

const K = 15;
const score = (horns: number) => Math.round(100 * Math.exp(-horns / K));

function grade(s: number): string {
  if (s >= 70) return "good";
  if (s >= 40) return "warn";
  return "bad";
}

export function InsightsPanel({ stats }: { stats: Stats }) {
  const sites = Object.entries(stats.bySite)
    .map(([site, horns]) => ({ site, horns, s: score(horns) }))
    .sort((a, b) => a.s - b.s); // worst first

  const city = sites.length
    ? Math.round(sites.reduce((sum, x) => sum + x.s, 0) / sites.length)
    : 100;

  return (
    <div className="panel insights">
      <h2>Horn Discipline Score</h2>
      <div className={`cityscore ${grade(city)}`}>
        <span className="num">{city}</span>
        <span className="lbl">city score / 100</span>
      </div>
      <ul className="ranking">
        {sites.map(({ site, horns, s }) => (
          <li key={site}>
            <span className="site">{site}</span>
            <span className="bar">
              <span className={`fill ${grade(s)}`} style={{ width: `${s}%` }} />
            </span>
            <span className={`score ${grade(s)}`}>{s}</span>
            <span className="n">{horns}🔊</span>
          </li>
        ))}
        {sites.length === 0 && <li className="empty">no data yet</li>}
      </ul>
    </div>
  );
}
