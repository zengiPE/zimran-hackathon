"use client";

import { Fragment } from "react";

/** Event that asks the notebook to show a suspect's row (see Notebook). */
export const SUSPECT_EVENT = "cf:suspect";

export function showSuspectInNotebook(name: string) {
  window.dispatchEvent(new CustomEvent(SUSPECT_EVENT, { detail: name }));
}

const escape = (s: string) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

/**
 * Text where suspect names become link buttons that open their row in the notebook.
 * Exact names only, longest first, on word boundaries; "Priya's" counts as Priya.
 * Player names are never passed here (players and suspects are different people).
 */
export function SuspectText({ text, names }: { text: string; names?: string[] }) {
  if (!names || names.length === 0) return <>{text}</>;
  const sorted = [...names].sort((a, b) => b.length - a.length).map(escape);
  const re = new RegExp(`(?<![\\p{L}\\p{N}])(${sorted.join("|")})(?![\\p{L}\\p{N}])`, "gu");
  const parts = text.split(re); // odd indexes are the matched names

  return (
    <>
      {parts.map((part, i) =>
        i % 2 === 1 ? (
          <button
            key={i}
            type="button"
            className="cf-namelink"
            onClick={() => showSuspectInNotebook(part)}
            aria-label={`${part}: show in your notebook`}
          >
            {part}
          </button>
        ) : (
          <Fragment key={i}>{part}</Fragment>
        ),
      )}
    </>
  );
}
