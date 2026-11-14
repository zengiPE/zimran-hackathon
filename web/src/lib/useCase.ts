"use client";

// SWR hooks for the game screens. /me and /host are polled every 5 seconds
// (there is no realtime). /reveal is loaded once, only in the reveal phase.

import useSWR, { type SWRConfiguration } from "swr";
import { ApiError, getHost, getMe, getReveal } from "./api";
import type { HostOut, MeOut, RevealOut } from "./types";

const POLL_MS = 5000;

const polling: SWRConfiguration = {
  refreshInterval: POLL_MS,
  revalidateOnFocus: true,
  keepPreviousData: true,
  // A bad link (403) or a missing case (404) won't fix itself: stop retrying.
  onErrorRetry(err, _key, _config, revalidate, { retryCount }) {
    if (err instanceof ApiError && (err.status === 403 || err.status === 404)) return;
    if (retryCount >= 5) return;
    setTimeout(() => revalidate({ retryCount }), POLL_MS);
  },
};

/** The player's view of the case. Pass null while id or token is unknown. */
export function useMe(id: string | null, token: string | null) {
  return useSWR<MeOut, Error>(
    id && token ? ["me", id, token] : null,
    ([, i, t]: [string, string, string]) => getMe(i, t),
    polling,
  );
}

/** The host's view: players with links, votes count. */
export function useHost(id: string | null, token: string | null) {
  return useSWR<HostOut, Error>(
    id && token ? ["host", id, token] : null,
    ([, i, t]: [string, string, string]) => getHost(i, t),
    polling,
  );
}

/** The reveal. Only asks the API when `enabled` (phase is "reveal"). */
export function useReveal(id: string | null, enabled: boolean) {
  return useSWR<RevealOut, Error>(
    id && enabled ? ["reveal", id] : null,
    ([, i]: [string, string]) => getReveal(i),
    { revalidateOnFocus: false, shouldRetryOnError: false },
  );
}
