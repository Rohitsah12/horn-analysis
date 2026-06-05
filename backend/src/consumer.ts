/**
 * Phase 2 + 3: the Kafka CONSUMER (Node + TypeScript backend).
 *
 * Subscribes to `horn-events` and, for each horn the Python detector publishes:
 *   - appends it to MongoDB  (durable history)
 *   - updates Redis          (fast live state for the dashboard)
 *
 * Prereq: infra running  (cd docker && docker compose up -d)
 * Run:    cd backend && npm install && npm run consumer
 *         (then, elsewhere: cd ml-service && uv run python src/producer.py)
 */

import { Kafka, logLevel } from "kafkajs";

import type { HornEvent } from "./types.ts";
import {
  connectStores,
  saveToHistory,
  updateLiveState,
  closeStores,
} from "./stores.ts";

const kafka = new Kafka({
  clientId: "horn-backend",
  brokers: ["localhost:9092"],
  logLevel: logLevel.ERROR,
});

// Consumer group: Kafka tracks this group's offset, so restarts resume cleanly.
const consumer = kafka.consumer({ groupId: "horn-backend" });

let count = 0;

async function run() {
  await connectStores();
  await consumer.connect();
  await consumer.subscribe({ topic: "horn-events", fromBeginning: true });
  console.log("Backend consumer connected. Waiting for horn events...\n");

  await consumer.run({
    eachMessage: async ({ message, partition }) => {
      const event: HornEvent = JSON.parse(message.value!.toString());

      // Write to BOTH stores (Lesson 9): durable record + fast live view.
      await saveToHistory(event);
      await updateLiveState(event);

      count++;
      console.log(
        `#${count}  🔊 ${event.location.padEnd(10)} ` +
          `conf=${event.confidence.toFixed(2)}  ` +
          `[partition ${partition}, offset ${message.offset}]  ` +
          `-> saved to Mongo + Redis`
      );
    },
  });
}

const shutdown = async () => {
  console.log(`\nShutting down. Processed ${count} events this session.`);
  await consumer.disconnect();
  await closeStores();
  process.exit(0);
};
process.on("SIGINT", shutdown);
process.on("SIGTERM", shutdown);

run().catch((err) => {
  console.error("Consumer error:", err);
  process.exit(1);
});
