"use client";

import clsx from "clsx";
import type { CSSProperties } from "react";
import { timeLeft } from "@/lib/format";
import type { Phase } from "@/lib/types";
import { useNow } from "@/lib/useNow";

interface Props {
  title: string;
  day: number;
  daysTotal: number;
  phase: Phase;
  nextUnlockAt: string;
  demo: boolean;
  playersCount: number;
  openedCount: number; // how many opened today's clue
}

/** Top of the player screen: folder tab, title, day track and countdown. */
export function CaseHeader(props: Props) {
  const { title, day, daysTotal, phase, nextUnlockAt, demo, playersCount, openedCount } = props;
  const now = useNow();
  const voting = phase !== "play";

  // Left side of the bottom line: what happens next.
  let next = "";
  if (voting) next = "Voting is open";
  else if (demo) next = "Demo: the host moves the days";
  else if (now !== null) {
    const left = timeLeft(nextUnlockAt, now);
    const what = day >= daysTotal ? "Voting opens" : "Next clue";
    next = left ? `${what} in ${left}` : `${what} any minute`;
  }

  const days = Array.from({ length: daysTotal }, (_, i) => i + 1);
  const where = voting ? "Voting" : `Day ${day} of ${daysTotal}`;

  return (
    <header className="cf-case">
      <span className="cf-case__tab">Case file</span>
      <div className="cf-case__body">
        <p className="cf-case__theme">
          {where} · {playersCount} players
        </p>
        <h1 className="cf-case__title">{title}</h1>
        <ol className="cf-days" style={{ "--days": daysTotal + 1 } as CSSProperties} aria-label={where}>
          {days.map((d) => {
            const done = voting || d < day;
            const today = !voting && d === day;
            return (
              <li
                key={d}
                className={clsx("cf-day", done && "cf-day--done", today && "cf-day--today")}
                aria-current={today ? "step" : undefined}
              >
                Day {d}
              </li>
            );
          })}
          <li
            className={clsx("cf-day", voting ? "cf-day--today" : "cf-day--vote")}
            aria-current={voting ? "step" : undefined}
          >
            Vote
          </li>
        </ol>
        <p className="cf-case__next">
          <span>{next}</span>
          {!voting && (
            <span>
              {openedCount} of {playersCount} opened today
            </span>
          )}
        </p>
      </div>
    </header>
  );
}
