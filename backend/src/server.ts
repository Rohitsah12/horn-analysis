/**
 * Phase 4: the backend SERVER (Lesson 10).
 *
 * One process doing three jobs:
 *   1. runs the Kafka consumer (ingest + store, as in Phase 3)
 *   2. serves a REST API for the dashboard's initial "snapshot" reads
 *   3. holds Socket.IO connections and PUSHES each new horn live
 *
 * Prereq: infra running  (cd docker && docker compose up -d)
 * Run:    cd backend && npm run server
 */

import http from "node:http";

import cors from "cors";
import express from "express";
import { Kafka, logLevel } from "kafkajs";
import { Server as SocketServer } from "socket.io";

import type { HornEvent } from "./types.ts";
import {
  connectStores,
  saveToHistory,
  updateLiveState,
  getRecent,
  getStats,
  getHistory,
  closeStores,
} from "./stores.ts";

const PORT = 4000;

// ---- Express REST API (the "pull" snapshot reads) ----
const app = express();
app.use(cors()); // let the React dev server (different port) call us

app.get("/api/health", (_req, res) => res.json({ ok: true }));

// Live feed + stats come from Redis (fast); history comes from Mongo.
app.get("/api/recent", async (req, res) => {
  res.json(await getRecent(Number(req.query.limit) || 50));
});
app.get("/api/stats", async (_req, res) => {
  res.json(await getStats());
});
app.get("/api/history", async (req, res) => {
  res.json(
    await getHistory({
      site: req.query.site as string | undefined,
      limit: Number(req.query.limit) || 100,
    })
  );
});

// ---- Socket.IO (the "push" live stream) ----
const server = http.createServer(app);
const io = new SocketServer(server, { cors: { origin: "*" } });
io.on("connection", (socket) => {
  console.log(`Dashboard connected (${socket.id}). Clients: ${io.engine.clientsCount}`);
  socket.on("disconnect", () =>
    console.log(`Dashboard disconnected (${socket.id}).`)
  );
});

// ---- Kafka consumer (ingest → store → push) ----
const kafka = new Kafka({
  clientId: "horn-backend",
  brokers: ["localhost:9092"],
  logLevel: logLevel.ERROR,
});
const consumer = kafka.consumer({ groupId: "horn-backend" });

async function startConsumer() {
  await consumer.connect();
  await consumer.subscribe({ topic: "horn-events", fromBeginning: false });
  await consumer.run({
    eachMessage: async ({ message }) => {
      const event: HornEvent = JSON.parse(message.value!.toString());
      await saveToHistory(event); // durable
      await updateLiveState(event); // live state
      io.emit("horn", event); // PUSH to every connected dashboard
      console.log(`🔊 ${event.location} (conf ${event.confidence.toFixed(2)}) -> stored + pushed`);
    },
  });
}

async function main() {
  await connectStores();
  await startConsumer();
  server.listen(PORT, () =>
    console.log(`Backend listening on http://localhost:${PORT} (REST + Socket.IO)`)
  );
}

const shutdown = async () => {
  console.log("\nShutting down...");
  await consumer.disconnect();
  await closeStores();
  io.close();
  server.close();
  process.exit(0);
};
process.on("SIGINT", shutdown);
process.on("SIGTERM", shutdown);

main().catch((err) => {
  console.error("Server error:", err);
  process.exit(1);
});
