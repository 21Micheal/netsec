const rawApiBase = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/+$/, "");

function normalizeApiBase(base: string): string {
  if (!base) {
    return "/api";
  }
  if (base.endsWith("/api")) {
    return base;
  }
  return `${base}/api`;
}

export const API_BASE_URL = normalizeApiBase(rawApiBase);

export const SOCKET_URL =
  rawApiBase || (typeof window !== "undefined" ? window.location.origin : "http://localhost:5000");
