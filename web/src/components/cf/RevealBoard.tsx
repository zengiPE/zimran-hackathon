"use client";

import { useEffect, useRef, useState } from "react";
import { caseCopy } from "@/lib/caseCopy";
import { formatNumber } from "@/lib/format";
import type { RevealOut, Suspect } from "@/lib/types";
import { ButtonLink } from "./Button";
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

/**
 * The final reveal on cork: counter of possible worlds, one note per clue,
 * the five suspects, a red string from every clue to the culprit, the verdict.
 * For now it shows the final state; the animation comes in phase 3.
 */
export function RevealBoard({ reveal, suspects }: Props) {
  const { culprit, chain, stats, votes, truth } = reveal;
  const boardRef = useRef<HTMLDivElement>(null);
  const noteRefs = useRef<(HTMLDivElement | null)[]>([]);
  const pinRef = useRef<HTMLSpanElement>(null);
  const [paths, setPaths] = useState<StringPath[]>([]);

  // Everyone some clue cleared gets "Cleared"; the culprit gets "Guilty".
  const cleared = new Set(chain.flatMap((c) => c.eliminated));
  const verdictOf = (s: Suspect) =>
    s.id === culprit.id ? "guilty" : cleared.has(s.name) ? "cleared" : "none";

  const fact = truth.find((t) => t.suspect === culprit.name);
  const worldsLeft = chain.at(-1)?.worlds_left ?? stats.worlds_left;

  // Measure where the notes and the culprit's pin are, then draw strings.
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

  return (
    <div className="cf-reveal" ref={boardRef}>
      <div className="cf-reveal__head">
        <div className="cf-worlds" aria-live="polite">
          <span className="cf-label">Possible worlds left</span>
          <p className="cf-worlds__num">{formatNumber(worldsLeft)}</p>
        </div>
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
            pinRef={s.id === culprit.id ? pinRef : undefined}
          />
        ))}
      </div>

      <div className="cf-verdict">
        <Stamp big>Solved</Stamp>
        <p className="cf-verdict__line">
          {culprit.name} {caseCopy(reveal.title).deed}.
        </p>
        <p className="cf-caption">
          {fact && `${fact.room} · ${fact.time} · ${fact.item}. `}
          {formatNumber(worldsLeft)} possible worlds are left, and in every one of them it&apos;s {culprit.name}.
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
        {paths.map((p, i) => (
          <g key={i}>
            <path className="cf-string-under" d={p.d} />
            <path className="cf-string" d={p.d} />
            <circle className="cf-knot" cx={p.x} cy={p.y} r={4} />
          </g>
        ))}
      </svg>
    </div>
  );
}
