"use client";

import { useState } from "react";
import { errorText, isStatus } from "@/lib/api";
import type { Phase } from "@/lib/types";
import { Button } from "./Button";

interface Props {
  names: string[]; // every player of the demo case
  current: string; // whose screen is shown
  day: number;
  daysTotal: number;
  phase: Phase;
  onViewAs: (name: string) => void;
  onNextDay: () => Promise<void>;
  onHint: () => Promise<void>;
}

/** Demo controls: play every seat, move the day, ask for a hint. */
export function DemoBar({ names, current, day, daysTotal, phase, onViewAs, onNextDay, onHint }: Props) {
  const [busy, setBusy] = useState(false);
  const [note, setNote] = useState<string | null>(null);

  async function run(action: () => Promise<void>, hint = false) {
    setBusy(true);
    setNote(null);
    try {
      await action();
      if (hint) setNote("A clue is now open for everyone.");
    } catch (err) {
      setNote(hint && isStatus(err, 409) ? "No hints yet." : errorText(err));
    } finally {
      setBusy(false);
    }
  }

  const where = phase === "play" ? `Day ${day} of ${daysTotal}` : phase === "vote" ? "Voting" : "Reveal";
  const nextLabel = phase === "vote" ? "Show the reveal" : day >= daysTotal ? "Open voting" : "Next day";

  return (
    <div className="cf-demobar" role="region" aria-label="Demo controls">
      <div className="cf-demobar__row">
        <span className="cf-label">Demo case · View as</span>
        <span className="cf-caption">{where}</span>
      </div>
      <div className="cf-seg" role="group" aria-label="View as">
        {names.map((n) => (
          <button
            key={n}
            className="cf-seg__btn"
            type="button"
            aria-pressed={n === current}
            onClick={() => onViewAs(n)}
          >
            {n}
          </button>
        ))}
      </div>
      {phase !== "reveal" && (
        <div className="cf-demobar__row">
          <Button small disabled={busy || phase !== "play"} onClick={() => run(onHint, true)}>
            Hint
          </Button>
          <Button variant="primary" small disabled={busy} onClick={() => run(onNextDay)}>
            {nextLabel}
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
