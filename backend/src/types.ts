/** The horn-event contract — must match what ml-service/src/producer.py emits. */
export interface HornEvent {
  event_id: string;
  timestamp: string; // ISO 8601, UTC
  location: string;
  lat: number;
  lon: number;
  confidence: number;
  source: string;
}
