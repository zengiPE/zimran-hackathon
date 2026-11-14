"use client";

import { useSyncExternalStore } from "react";

// The current time, refreshed every 30 seconds. Returns null on the server,
// so prerendering never reads the clock (cacheComponents forbids it).

const TICK_MS = 30_000;

function subscribe(onTick: () => void) {
  const id = setInterval(onTick, TICK_MS);
  return () => clearInterval(id);
}

// Rounded to the tick so React sees the same value until the next tick.
const getSnapshot = () => Math.floor(Date.now() / TICK_MS) * TICK_MS;
const getServerSnapshot = () => null;

export function useNow(): number | null {
  return useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);
}
