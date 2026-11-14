"use client";

import clsx from "clsx";
import { Fragment, useState } from "react";
import { dropArticle } from "@/lib/format";
import type { Labels, Suspect } from "@/lib/types";
import { Button } from "./Button";

type Mark = "" | "no" | "yes";
type Marks = Record<string, Mark>; // manual marks only, key: "Priya|Sunroom"

/** What we keep in localStorage: the manual marks and up to 20 undo steps. */
interface Saved {
  marks: Marks;
  undo: Marks[];
}

const UNDO_LIMIT = 20;
const GLYPH: Record<Mark, string> = { "": "", no: "✗", yes: "✓" };
const WORD: Record<Mark, string> = { "": "blank", no: "ruled out", yes: "confirmed" };
const NEXT: Record<Mark, Mark> = { "": "no", no: "yes", yes: "" };

export interface NotebookClue {
  id: string;
  text: string; // the exact fact
  isNew?: boolean; // today's clue: highlighted
}

interface Props {
  suspects: Suspect[];
  labels: Labels;
  storageKey: string; // "notebook:{case_id}:{token}"
  clues?: NotebookClue[]; // facts shown above the grid, newest first
}

function load(key: string): Saved {
  try {
    const raw = window.localStorage.getItem(key);
    if (!raw) return { marks: {}, undo: [] };
    const data = JSON.parse(raw);
    // Older saves were just the marks object.
    if (data && typeof data === "object" && "marks" in data) return data as Saved;
    return { marks: data as Marks, undo: [] };
  } catch {
    return { marks: {}, undo: [] };
  }
}

function save(key: string, value: Saved) {
  try {
    window.localStorage.setItem(key, JSON.stringify(value));
  } catch {
    // Private mode or storage full: the notebook still works until reload.
  }
}

/**
 * The player's private logic grid. Marks live only in this browser.
 * A ✓ rules out the rest of its row group and its column automatically
 * (faint ✗, computed, never saved). Render it inside <BrowserOnly>.
 */
export function Notebook({ suspects, labels, storageKey, clues }: Props) {
  const [saved, setSaved] = useState<Saved>(() => load(storageKey));
  const [cross, setCross] = useState<{ row: number; col: string } | null>(null);
  // Narrow screens show one group at a time (no sideways scrolling); wide ones show all three.
  const [active, setActive] = useState<"Room" | "Time" | "Item">("Room");
  const { marks, undo } = saved;

  const groups = [
    { name: "Room", values: labels.room },
    { name: "Time", values: labels.time },
    { name: "Item", values: labels.item.map(dropArticle) },
  ];

  // Automatic ✗: for every ✓, the other boxes of its group in that row,
  // and the same column for the other suspects.
  const auto = new Set<string>();
  for (const g of groups) {
    for (const s of suspects) {
      const yes = g.values.find((v) => marks[`${s.name}|${v}`] === "yes");
      if (!yes) continue;
      g.values.forEach((v) => v !== yes && auto.add(`${s.name}|${v}`));
      suspects.forEach((o) => o.id !== s.id && auto.add(`${o.name}|${yes}`));
    }
  }

  function update(next: Marks) {
    const value = { marks: next, undo: [...undo, marks].slice(-UNDO_LIMIT) };
    setSaved(value);
    save(storageKey, value);
  }

  function tap(key: string) {
    const manual = marks[key] ?? "";
    // Tapping an automatic ✗ turns it into a manual one.
    const next: Mark = !manual && auto.has(key) ? "no" : NEXT[manual];
    update({ ...marks, [key]: next });
  }

  function undoLast() {
    if (undo.length === 0) return;
    const value = { marks: undo[undo.length - 1], undo: undo.slice(0, -1) };
    setSaved(value);
    save(storageKey, value);
  }

  return (
    <div className="cf-notebook" data-active={active}>
      {clues && clues.length > 0 && (
        <details className="cf-nb__clues" open>
          <summary>Your clues ({clues.length})</summary>
          <ul>
            {clues.map((c) => (
              <li key={c.id}>{c.isNew ? <mark>{c.text}</mark> : c.text}</li>
            ))}
          </ul>
        </details>
      )}

      <div className="cf-seg cf-nb__tabs" role="group" aria-label="Notebook columns">
        {groups.map((g) => (
          <button
            key={g.name}
            type="button"
            className="cf-seg__btn"
            aria-pressed={active === g.name}
            onClick={() => setActive(g.name as typeof active)}
          >
            {g.name}
          </button>
        ))}
      </div>

      <div className="cf-nb__scroll">
        <table onMouseLeave={() => setCross(null)}>
          <thead>
            <tr className="cf-nb__group">
              <th className="cf-nb__corner" rowSpan={2}>
                <span className="cf-sr">Suspect</span>
              </th>
              {groups.map((g) => (
                <th key={g.name} colSpan={g.values.length} scope="colgroup" data-g={g.name}>
                  {g.name}
                </th>
              ))}
            </tr>
            <tr className="cf-nb__col">
              {groups.map((g) =>
                g.values.map((v) => (
                  <th key={g.name + v} scope="col" data-g={g.name} className={clsx(cross?.col === v && "is-cross")}>
                    <span>{v}</span>
                  </th>
                )),
              )}
            </tr>
          </thead>
          <tbody>
            {suspects.map((s) => (
              <tr key={s.id}>
                <th scope="row" className={clsx("cf-nb__name", cross?.row === s.id && "is-cross")}>
                  {s.name}
                </th>
                {groups.map((g) => (
                  <Fragment key={g.name}>
                    {g.values.map((v, i) => {
                      const key = `${s.name}|${v}`;
                      const manual = marks[key] ?? "";
                      const isAuto = !manual && auto.has(key);
                      const shown: Mark = manual || (isAuto ? "no" : "");
                      const here = () => setCross({ row: s.id, col: v });
                      return (
                        <td
                          key={key}
                          data-g={g.name}
                          className={clsx(
                            "cf-nb__cell",
                            i === 0 && "cf-nb__first",
                            (cross?.row === s.id || cross?.col === v) && "is-cross",
                          )}
                        >
                          <button
                            type="button"
                            className={clsx("cf-nb__btn", shown === "yes" && "is-yes", isAuto && "is-auto")}
                            aria-label={`${s.name}, ${v}: ${WORD[shown]}${isAuto ? " (automatic)" : ""}`}
                            onClick={() => tap(key)}
                            onFocus={here}
                            onPointerDown={here}
                            onBlur={() => setCross(null)}
                          >
                            {GLYPH[shown]}
                          </button>
                        </td>
                      );
                    })}
                  </Fragment>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="cf-nb__foot">
        <p className="cf-nb__legend">
          Tap a box: ✗ ruled out, ✓ confirmed. A ✓ rules out the rest of its row and column for you. Only you can see
          your notebook.
        </p>
        <Button variant="quiet" onClick={undoLast} disabled={undo.length === 0}>
          Undo
        </Button>
      </div>
    </div>
  );
}
