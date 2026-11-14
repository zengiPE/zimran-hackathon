"use client";

import clsx from "clsx";
import {
  animate,
  motion,
  useMotionValue,
  useReducedMotion,
  useTransform,
  type AnimationPlaybackControls,
} from "framer-motion";
import { useEffect, useRef, useState } from "react";
import { caseCopy } from "@/lib/caseCopy";
import { formatNumber } from "@/lib/format";
import type { RevealOut, Suspect } from "@/lib/types";
import { Button, ButtonLink } from "./Button";
import { Stamp } from "./Stamp";
import { SuspectCard } from "./SuspectCard";

interface Props {
  reveal: RevealOut;
  suspects: Suspect[]; // from /me or /host
}

interface StringPath {
  d: string; // SVG path from the note to the culprit's pin
  x: number; // knot at the note end
  y: number;
}

// Timings from design/components/RevealBoard/README.md.
const PUBLIC_MS = 500; // counter: total → public worlds
const START_MS = 600; // first string starts
const GUILTY_PAUSE_MS = 400; // after the last string lands
const easeOutCubic = [0.33, 1, 0.68, 1] as const;

/**
 * The final reveal on cork: the counter of possible worlds melts down while a
 * red string runs from each clue to the culprit; "Cleared" lands on suspects
 * as their string finishes; then "Guilty" and the verdict.
 * Under prefers-reduced-motion everything shows in its final state at once.
 */
export function RevealBoard({ reveal, suspects }: Props) {
  const { culprit, chain, stats, votes, truth } = reveal;
  const reduce = useReducedMotion() ?? false;

  const boardRef = useRef<HTMLDivElement>(null);
  const noteRefs = useRef<(HTMLDivElement | null)[]>([]);
  const pinRef = useRef<HTMLSpanElement>(null);
  const [paths, setPaths] = useState<StringPath[]>([]);

  // Animation progress. `run` bumps on Replay to restart the sequence.
  const [run, setRun] = useState(0);
  const [drawn, setDrawn] = useState(0); // strings started
  const [clearedSteps, setClearedSteps] = useState(0); // steps whose "Cleared" stamps landed
  const [done, setDone] = useState(false); // "Guilty" + verdict

  const lastWorlds = chain.at(-1)?.worlds_left ?? stats.worlds_left;
  const count = useMotionValue(reduce ? lastWorlds : stats.worlds_total);
  const countText = useTransform(count, (v) => formatNumber(Math.round(v)));

  const step = Math.min(850, 8000 / Math.max(1, chain.length));
  const draw = Math.round(step * 0.7);

  // Under reduced motion, show the end state no matter what.
  const shownDrawn = reduce ? chain.length : drawn;
  const shownCleared = reduce ? chain.length : clearedSteps;
  const shownDone = reduce || done;

  const cleared = new Set(chain.slice(0, shownCleared).flatMap((c) => c.eliminated));
  const verdictOf = (s: Suspect) =>
    s.id === culprit.id && shownDone ? "guilty" : cleared.has(s.name) ? "cleared" : "none";
  const fact = truth.find((t) => t.suspect === culprit.name);

  // 1. Measure where the notes and the culprit's pin are, to draw the strings.
  useEffect(() => {
    const board = boardRef.current;
    if (!board) return;

    function measure() {
      const pin = pinRef.current;
      if (!board || !pin) return;
      const b = board.getBoundingClientRect();
      const p = pin.getBoundingClientRect();
      const zx = p.left - b.left + p.width / 2;
      const zy = p.top - b.top + p.height / 2;
      const next: StringPath[] = [];
      noteRefs.current.forEach((note) => {
        if (!note) return;
        const r = note.getBoundingClientRect();
        const ax = r.left - b.left + r.width / 2;
        const ay = r.bottom - b.top; // bottom edge: the knot peeks out under the note
        const mx = (ax + zx) / 2;
        const my = (ay + zy) / 2 + 36; // the string sags 36px
        next.push({ d: `M${ax} ${ay} Q${mx} ${my} ${zx} ${zy}`, x: ax, y: ay });
      });
      setPaths(next);
    }

    const observer = new ResizeObserver(measure);
    observer.observe(board);
    document.fonts?.ready.then(measure);
    return () => observer.disconnect();
  }, [chain.length]);

  // 2. Play the sequence with timers (restarts when `run` changes).
  useEffect(() => {
    if (reduce) {
      count.set(lastWorlds);
      return;
    }
    const timers: number[] = [];
    let tween: AnimationPlaybackControls | null = null;
    const at = (ms: number, fn: () => void) => timers.push(window.setTimeout(fn, ms));
    const tweenTo = (to: number, ms: number) => {
      tween?.stop();
      tween = animate(count, to, { duration: ms / 1000, ease: easeOutCubic });
    };

    count.set(stats.worlds_total);
    tweenTo(stats.worlds_public, PUBLIC_MS);

    let t = START_MS;
    chain.forEach((c, i) => {
      at(t, () => {
        setDrawn(i + 1);
        tweenTo(c.worlds_left, draw);
      });
      at(t + draw, () => setClearedSteps(i + 1));
      t += step;
    });
    at(t - (step - draw) + GUILTY_PAUSE_MS, () => {
      // Land on the exact final number even if frames were skipped (hidden tab).
      tween?.stop();
      count.set(lastWorlds);
      setDone(true);
    });

    return () => {
      timers.forEach(clearTimeout);
      tween?.stop();
    };
  }, [run, reduce, chain, count, draw, step, lastWorlds, stats.worlds_total, stats.worlds_public]);

  function replay() {
    setDrawn(0);
    setClearedSteps(0);
    setDone(false);
    setRun((r) => r + 1);
  }

  return (
    <div className="cf-reveal" ref={boardRef}>
      <div className="cf-reveal__head">
        <div className="cf-worlds" aria-live="polite">
          <span className="cf-label">Possible worlds left</span>
          <motion.p className="cf-worlds__num">{countText}</motion.p>
        </div>
        {!reduce && (
          <Button small onClick={replay}>
            Replay
          </Button>
        )}
      </div>

      <div className="cf-reveal__clues">
        {chain.map((c, i) => (
          <div
            key={c.clue_id}
            className="cf-note"
            ref={(el) => {
              noteRefs.current[i] = el;
            }}
          >
            <span className="cf-label">
              {c.from} · Day {c.day}
            </span>
            <p className="cf-note__text">{c.text}</p>
          </div>
        ))}
      </div>

      <div className="cf-reveal__suspects">
        {suspects.map((s) => (
          <SuspectCard
            key={s.id}
            suspect={s}
            verdict={verdictOf(s)}
            thunk={!reduce}
            pinRef={s.id === culprit.id ? pinRef : undefined}
          />
        ))}
      </div>

      <div className={clsx("cf-verdict", !reduce && "cf-fade")} hidden={!shownDone}>
        <Stamp big thunk={!reduce}>
          Solved
        </Stamp>
        <p className="cf-verdict__line">
          {culprit.name} {caseCopy(reveal.title).deed}.
        </p>
        <p className="cf-caption">
          {fact && `${fact.room} · ${fact.time} · ${fact.item}. `}
          {formatNumber(lastWorlds)} possible worlds are left, and in every one of them it&apos;s {culprit.name}.
        </p>
        {votes.length > 0 && (
          <ul className="cf-votes" aria-label="Votes">
            {votes.map((v) => (
              <li key={v.player}>
                <span>
                  <b>{v.player}</b> voted {v.suspect}
                </span>
                <Stamp straight tone={v.correct ? "stamp" : "muted"}>
                  {v.correct ? "Correct" : "Missed"}
                </Stamp>
              </li>
            ))}
          </ul>
        )}
        <ButtonLink variant="primary" href={`/paywall?case_id=${encodeURIComponent(reveal.case_id)}`}>
          Open the next case
        </ButtonLink>
      </div>

      <svg className="cf-reveal__strings" aria-hidden="true">
        {paths.slice(0, shownDrawn).map((p, i) => (
          <g key={`${run}-${i}`}>
            <motion.path
              className="cf-string-under"
              d={p.d}
              initial={reduce ? false : { pathLength: 0 }}
              animate={{ pathLength: 1 }}
              transition={{ duration: draw / 1000, ease: "easeInOut" }}
            />
            <motion.path
              className="cf-string"
              d={p.d}
              initial={reduce ? false : { pathLength: 0 }}
              animate={{ pathLength: 1 }}
              transition={{ duration: draw / 1000, ease: "easeInOut" }}
            />
            <circle className="cf-knot" cx={p.x} cy={p.y} r={4} />
          </g>
        ))}
      </svg>
    </div>
  );
}
