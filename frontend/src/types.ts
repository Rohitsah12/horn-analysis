/** Mirrors the backend HornEvent contract (ml-service producer → API). */
export interface HornEvent {
  event_id: string;
  timestamp: string;
  location: string;
  lat: number;
  lon: number;
  confidence: number;
  source: string;
}

export interface Stats {
  total: number;
  bySite: Record<string, number>;
}
