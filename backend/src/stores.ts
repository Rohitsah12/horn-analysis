/**
 * Phase 3: the storage layer (Lesson 9).
 *
 * Two stores, two jobs:
 *   - MongoDB : durable history. Every event is appended forever (analytics).
 *   - Redis   : fast in-memory live state for the dashboard (recent feed,
 *               per-site counts, running total).
 *
 * The consumer calls saveToHistory() AND updateLiveState() for each event.
 */

import { MongoClient, type Collection } from "mongodb";
import { createClient, type RedisClientType } from "redis";

import type { HornEvent } from "./types.ts";

const MONGO_URL = "mongodb://localhost:27017";
const REDIS_URL = "redis://localhost:6379";

// Redis keys (one place so they never drift between writer and reader).
export const KEYS = {
  recent: "horn:recent", // list of recent events (newest first)
  counts: "horn:counts_by_site", // hash: site -> count
  total: "horn:total", // running total counter
};
const RECENT_MAX = 50; // how many recent events to keep on the "whiteboard"

let mongo: MongoClient;
let events: Collection<HornEvent>;
let redis: RedisClientType;

export async function connectStores() {
  mongo = new MongoClient(MONGO_URL);
  await mongo.connect();
  events = mongo.db("horn_analysis").collection<HornEvent>("events");
  // Indexes make the Phase 6 analytics queries fast (by time, by place).
  await events.createIndex({ timestamp: 1 });
  await events.createIndex({ location: 1 });

  redis = createClient({ url: REDIS_URL });
  await redis.connect();

  console.log("Connected to MongoDB (horn_analysis.events) and Redis.");
}

/** Job 1: append to the durable history (the filing cabinet). */
export async function saveToHistory(event: HornEvent) {
  await events.insertOne({ ...event });
}

/** Job 2: update the fast live view (the whiteboard). */
export async function updateLiveState(event: HornEvent) {
  await Promise.all([
    // newest-first feed, trimmed to the last RECENT_MAX events
    redis
      .multi()
      .lPush(KEYS.recent, JSON.stringify(event))
      .lTrim(KEYS.recent, 0, RECENT_MAX - 1)
      .exec(),
    // per-site tally and grand total, incremented in place
    redis.hIncrBy(KEYS.counts, event.location, 1),
    redis.incr(KEYS.total),
  ]);
}

// ---- READERS (used by the REST API) ----

/** Live recent feed from Redis (newest first). Fast in-memory read. */
export async function getRecent(limit = 50): Promise<HornEvent[]> {
  const raw = await redis.lRange(KEYS.recent, 0, limit - 1);
  return raw.map((s) => JSON.parse(s) as HornEvent);
}

/** Live aggregate stats from Redis: total + per-site counts. */
export async function getStats(): Promise<{
  total: number;
  bySite: Record<string, number>;
}> {
  const [total, bySite] = await Promise.all([
    redis.get(KEYS.total),
    redis.hGetAll(KEYS.counts),
  ]);
  const counts: Record<string, number> = {};
  for (const [site, n] of Object.entries(bySite)) counts[site] = Number(n);
  return { total: Number(total ?? 0), bySite: counts };
}

/** Historical query from MongoDB (durable store). Optional site filter. */
export async function getHistory(
  opts: { site?: string; limit?: number } = {}
): Promise<HornEvent[]> {
  const filter = opts.site ? { location: opts.site } : {};
  return events
    .find(filter, { projection: { _id: 0 } })
    .sort({ timestamp: -1 })
    .limit(opts.limit ?? 100)
    .toArray();
}

export async function closeStores() {
  await mongo?.close();
  await redis?.quit();
}
