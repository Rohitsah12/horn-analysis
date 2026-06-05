/**
 * A stand-in for the React dashboard: connects via Socket.IO and prints every
 * horn the server PUSHES in real time. Used to verify Phase 4 live streaming.
 * Run:  tsx src/test_client.ts
 */
import { io } from "socket.io-client";

const socket = io("http://localhost:4000");

socket.on("connect", () => console.log("test client connected to backend"));
socket.on("horn", (e) =>
  console.log(`PUSHED -> ${e.location} conf=${e.confidence} @ ${e.timestamp}`)
);
socket.on("disconnect", () => console.log("test client disconnected"));
