# Day 3 Report — Phase 2: Kafka Pipeline (Python → Kafka → Node)
**Date:** 2026-06-04
**Phase:** 2 (Kafka pipeline, Python → Node)
**Status:** ✅ Complete — full loop works, offset-resume verified.

## What was done today

1. **Reusable inference unit.** Built `src/predict.py` — `HornDetector.predict_file(wav) -> {is_horn, confidence}`. Loads the model + tuned threshold once, reuses the exact training feature recipe (`fingerprint_from_audio`).
2. **Learned message brokers (Lesson 7).** Why we don't let Python call Node's API directly (tight coupling, lost events on downtime, backpressure, burst overflow, single-consumer). A broker decouples producer/consumer via a durable, replayable log. Kafka vocabulary: topic, producer, consumer, partition, offset.
3. **Kafka running in Docker.** Enabled Zookeeper + Kafka (cp 7.5.0, reused cached images) in `docker/docker-compose.yml`. Created the `horn-events` topic.
4. **Python producer.** `src/producer.py` simulates a live street-sensor feed: interleaves MELAUDIS traffic (negatives) with real UrbanSound8K horns (positives), tags each with a Melbourne site + coordinates, detects, and publishes a JSON horn event to Kafka per detection.
5. **Verified end to end.** Producer published events; read them back with `kafka-console-consumer` *after* the producer disconnected — proving Kafka's durability/decoupling.
6. **Node + TypeScript backend + consumer (Lesson 8).** Scaffolded `backend/` (package.json, tsconfig, KafkaJS, tsx). `backend/src/consumer.ts` joins consumer group `horn-backend`, subscribes to `horn-events`, and logs each event (typed `HornEvent` interface = the shared contract). Ran producer + consumer together: events flowed Python → Kafka → Node live with sequential offsets.
7. **Offset-resume demonstrated.** Restarted the consumer (same group): it did NOT replay the 5 old events (resumed from committed offset 5); a new event then arrived at offset 5. Proves "nothing lost, nothing double-processed".

## Event schema (the contract for all downstream services)
```json
{ "event_id", "timestamp" (ISO UTC), "location", "lat", "lon", "confidence", "source" }
```

## Key results
- Producer run: all injected real horns detected (conf 0.94–0.99), all Melbourne traffic correctly ignored. Events landed in Kafka and were consumable afterwards.

## Bugs hit & fixed
- `kafka-console-consumer --from-beginning` printed nothing until `--max-messages N` was added (timeout behaviour).
- **Location/coordinate mismatch:** `site_from_name()` is random for injected horns and was called twice, so the `location` label and `lat/lon` disagreed (would scatter heatmap pins). Fixed by picking the site once. Purged + recreated the topic to drop the corrupt events.

## Viva-prep questions for today's work

| Q | A |
|---|---|
| Why put Kafka between the Python detector and the Node backend instead of a direct HTTP call? | Decoupling. Direct calls mean lost events if the backend is down, blocking under backpressure, overflow on bursts, and one hard-wired consumer. Kafka buffers durably, lets each side run/restart independently, and lets new consumers join without touching the producer. |
| What is a topic / partition / offset? | A topic is a named event stream (`horn-events`). It's split into partitions for parallelism/scale. An offset is an event's position in the log; consumers track their offset so they resume exactly where they left off after a restart. |
| How is Kafka different from a normal message queue? | A queue typically deletes a message once consumed. Kafka is an append-only log that retains events, so multiple independent consumers can read them and new consumers can replay history from offset 0. |
| What does Zookeeper do here? | Cluster coordination — broker registration, leader election, partition ownership. (Newer Kafka "KRaft" mode removes it; we kept it to match the scaffold.) |
| How did you prove the pipeline is decoupled? | The producer published events and disconnected; a separate consumer read them afterwards straight from the topic — neither needed the other to be online at the same moment. |
| What is a consumer group and why does it matter? | A named set of consumers that share a topic's partitions (each partition → one consumer in the group). Kafka tracks the group's offset, so restarts resume exactly where they left off. Add instances to the same group to scale; use a different group to read the same events independently. |
| You restarted the backend — why didn't it re-process old events? | Kafka had committed group `horn-backend`'s offset (5). `fromBeginning` only applies when a group has no committed offset; otherwise it resumes from the commit. So old events weren't replayed; the next new event arrived at offset 5. |

## Next (Day 4)
- **Phase 3:** enable Redis + MongoDB in compose; consumer writes history to Mongo and live state (recent feed, per-site counts) to Redis.
