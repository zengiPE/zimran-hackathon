// Small localStorage helpers. Every read and write is wrapped in try/catch:
// private mode or blocked storage must never break the game.

import type { Invite } from "./types";

export function readJSON<T>(key: string): T | null {
  try {
    const raw = window.localStorage.getItem(key);
    return raw ? (JSON.parse(raw) as T) : null;
  } catch {
    return null;
  }
}

export function writeJSON(key: string, value: unknown) {
  try {
    window.localStorage.setItem(key, JSON.stringify(value));
  } catch {
    // Storage blocked or full: nothing to do.
  }
}

/** What this browser remembers about a case it created (for the host and the demo). */
export interface SavedCase {
  case_id: string;
  host_token: string;
  invites: Invite[];
  demo: boolean;
}

const caseKey = (id: string) => `casefile:case:${id}`;

export const saveCase = (c: SavedCase) => writeJSON(caseKey(c.case_id), c);
export const loadCase = (id: string) => readJSON<SavedCase>(caseKey(id));

/** Path + query of a full link from the API ("http://x/play/ab?token=1" → "/play/ab?token=1"). */
export function localPath(url: string): string {
  try {
    const u = new URL(url);
    return u.pathname + u.search;
  } catch {
    return url;
  }
}
