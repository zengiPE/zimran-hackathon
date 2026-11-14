"use client";

import { useState } from "react";
import { errorText, isStatus } from "@/lib/api";
import type { Phase } from "@/lib/types";
import { Button } from "./Button";

interface Props {
  seats: { name: string; ai?: boolean }[]; // every seat of the demo case
  current: string; // whose screen is shown
  day: number;
  daysTotal: number;
  phase: Phase;
  onViewAs: (name: string) => void;
  onNextDay: () => Promise<void>;
  onHint: () => Promise<string | void>; // may return what to tell the player ("Hint: Даулет's clue…")
}

/** Demo controls: play every seat, move the day, ask for a hint. */
export function DemoBar({ seats, current, day, daysTotal, phase, onViewAs, onNextDay, onHint }: Props) {
  // Which button is waiting for the server (it can take a few seconds on prod).
  const [busy, setBusy] = useState<null | "hint" | "next">(null);
  const [note, setNote] = useState<string | null>(null);

  async function run(action: () => Promise<string | void>, hint = false) {
    setBusy(hint ? "hint" : "next");
    setNote(null);
    try {
      const message = await action();
      if (hint) setNote(message || "A clue is now open for everyone.");
    } catch (err) {
      setNote(hint && isStatus(err, 409) ? "No hints yet." : errorText(err));
    } finally {
      setBusy(null);
    }
  }

  const where = phase === "play" ? `Day ${day} of ${daysTotal}` : phase === "vote" ? "Voting" : "Reveal";
  const nextLabel = phase === "vote" ? "Show the reveal" : day >= daysTotal ? "Open voting" : "Next day";
  const nextBusy = phase === "vote" ? "Opening the reveal…" : day >= daysTotal ? "Opening voting…" : `Moving to day ${day + 1}…`;

  return (
    <div className="cf-demobar" role="region" aria-label="Demo controls">
      <div className="cf-demobar__row">
        <span className="cf-label">Demo case · View as</span>
        <span className="cf-caption">{where}</span>
      </div>
      <div className="cf-seg" role="group" aria-label="View as">
        {seats.map((s) => (
          <button
            key={s.name}
            className="cf-seg__btn"
            type="button"
            aria-pressed={s.name === current}
            aria-label={s.ai ? `${s.name}, AI teammate` : s.name}
            onClick={() => onViewAs(s.name)}
          >
            {s.name}
            {s.ai && " · AI"}
          </button>
        ))}
      </div>
      {phase !== "reveal" && (
        <div className="cf-demobar__row">
          <Button small disabled={busy !== null || phase !== "play"} onClick={() => run(onHint, true)}>
            {busy === "hint" ? "Finding a hint…" : "Hint"}
          </Button>
          <Button variant="primary" small disabled={busy !== null} onClick={() => run(onNextDay)}>
            {busy === "next" ? nextBusy : nextLabel}
          </Button>
        </div>
      )}
      {note && (
        <p className="cf-caption" role="status">
          {note}
        </p>
      )}
    </div>
  );
}
