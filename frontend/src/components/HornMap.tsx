/**
 * The Melbourne map. Each horn is a translucent circle at its lat/lon; many
 * overlapping circles at one site read as a "hot" area — a simple heatmap.
 * Brighter/redder = higher confidence.
 */
import { MapContainer, TileLayer, CircleMarker, Tooltip } from "react-leaflet";
import "leaflet/dist/leaflet.css";

import type { HornEvent } from "../types.ts";

const MELBOURNE: [number, number] = [-37.806, 144.967];

export function HornMap({ events }: { events: HornEvent[] }) {
  return (
    <div className="panel map">
      <h2>Horn map — Melbourne</h2>
      <MapContainer center={MELBOURNE} zoom={14} className="leaflet">
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution="© OpenStreetMap"
        />
        {events.map((e) => (
          <CircleMarker
            key={e.event_id}
            center={[e.lat, e.lon]}
            radius={8}
            pathOptions={{
              color: e.confidence > 0.8 ? "#ff3b3b" : "#ffa93b",
              fillOpacity: 0.35,
              weight: 1,
            }}
          >
            <Tooltip>
              {e.location} — {(e.confidence * 100).toFixed(0)}%
            </Tooltip>
          </CircleMarker>
        ))}
      </MapContainer>
    </div>
  );
}
