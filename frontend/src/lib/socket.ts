/// <reference types="vite/client" />
// src/lib/socket.ts
import { io } from "socket.io-client";
import { SOCKET_URL } from "../config/runtime";

export const socket = io(SOCKET_URL, {
  transports: ["websocket"],
  reconnectionAttempts: 5,
  reconnectionDelay: 2000,
});
