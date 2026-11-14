"use client";

import clsx from "clsx";
import { Clock, DoorOpen, Package, type LucideIcon } from "lucide-react";
import { Fragment, useCallback, useEffect, useId, useRef, useState } from "react";
import { dropArticle } from "@/lib/format";
import { cellKey, deriveAutoMarks, type Group, type Mark, type Marks } from "@/lib/notebook";
import type { Labels, Suspect } from "@/lib/types";
import { Button } from "./Button";
import { SUSPECT_EVENT, SuspectText } from "./SuspectText";

const UNDO_LIMIT = 20;
const HIGHLIGHT_MS = 1500;
const GLYPH: Record<Mark, string> = { "": "", no: "✗", yes: "✓" };
const WORD: Record<Mark, string> = { "": "blank", no: "ruled out", yes: "confirmed" };
const NEXT: Record<Mark, Mark> = { "": "no", no: "yes", yes: "" };
const GROUP_ICON: Record<string, LucideIcon> = { Room: DoorOpen, Time: Clock, Item: Package };

/** One row of the "Your clues" strip: the exact fact of one of your clues. */
export interface NotebookClue {
  id: string;
  exhibit: number; // N in "Exhibit N"
  day: number;
  text: string; // the exact fact (never the raw fact object)
  isNew?: boolean; // today's clue: highlighted
}

interface Props {
  suspects: Suspect[];
  labels: Labels;
  storageKey: string; // "notebook:{case_id}:{token}" — holds the manual marks only
  clues?: NotebookClue[]; // from my_clues, newest first
}

type GroupName = "Room" | "Time" | "Item";
type Highlight = { row: number | null; col: string | null } | null;

function load(key: string): Marks {
  try {
    const raw = window.localStorage.getItem(key);
    if (!raw) return {};
    const data = JSON.parse(raw);
    // A short-lived build saved {marks, undo}; read it, but always write plain marks.
    if (data && typeof data === "object" && "marks" in data) return data.marks as Marks;
    return data as Marks;
  } catch {
    return {};
  }
}

function save(key: string, marks: Marks) {
  try {
    window.localStorage.setItem(key, JSON.stringify(marks));
  } catch {
    // Private mode or storage full: the notebook still works until reload.
  }
}

/**
 * The player's private logic grid. Only manual marks are saved; automatic ✗ marks
 * are derived on every render. Render it inside <BrowserOnly> (reads localStorage).
 */
export function Notebook({ suspects, labels, storageKey, clues }: Props) {
  const rootRef = useRef<HTMLDivElement>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const cluesId = useId();
  const [marks, setMarks] = useState<Marks>(() => load(storageKey));
  const [undo, setUndo] = useState<{ key: string; prev: Mark }[]>([]); // memory only
  const [status, setStatus] = useState("");
  const [highlight, setHighlight] = useState<Highlight>(null);
  const timer = useRef<number | undefined>(undefined);
  // Narrow notebooks show one group at a time (tabs); wide ones show all three.
  const [active, setActive] = useState<GroupName>("Room");
  const [cluesOpen, setCluesOpen] = useState(true);

  const groups: Group[] = [
    { name: "Room", values: labels.room },
    { name: "Time", values: labels.time },
    { name: "Item", values: labels.item.map(dropArticle) },
  ];
  const names = suspects.map((s) => s.name);
  const auto = deriveAutoMarks(marks, names, groups);

  /** Light up a row and/or column; it fades after 1.5 s unless a key-focused box keeps it. */
  const flash = useCallback((h: Highlight, keep = false) => {
    window.clearTimeout(timer.current);
    timer.current = undefined;
    setHighlight(h);
    if (!keep) {
      timer.current = window.setTimeout(() => {
        timer.current = undefined;
        setHighlight(null);
      }, HIGHLIGHT_MS);
    }
  }, []);
  useEffect(() => () => window.clearTimeout(timer.current), []);

  function tap(key: string, row: number, col: string, el: HTMLElement) {
    const manual = marks[key] ?? "";
    // Tapping an automatic ✗ writes a manual ✗; after that the usual cycle.
    const next: Mark = !manual && auto.has(key) ? "no" : NEXT[manual];
    const updated = { ...marks, [key]: next };
    setMarks(updated);
    save(storageKey, updated);
    setUndo((u) => [...u, { key, prev: manual }].slice(-UNDO_LIMIT));
    setStatus("");
    flash({ row, col }, el.matches(":focus-visible"));
  }

  function undoLast() {
    const last = undo[undo.length - 1];
    if (!last) return;
    const updated = { ...marks, [last.key]: last.prev };
    setMarks(updated);
    save(storageKey, updated);
    setUndo((u) => u.slice(0, -1));
    setStatus("Undid the last mark.");
  }

  // A suspect name tapped in a clue: open this notebook and show that suspect's row.
  useEffect(() => {
    function onSuspect(e: Event) {
      const name = (e as CustomEvent<string>).detail;
      const s = suspects.find((x) => x.name === name);
      const root = rootRef.current;
      if (!s || !root) return;
      const drawer = root.closest("details");
      if (drawer && !drawer.open) drawer.open = true;
      scrollRef.current?.scrollTo({ left: 0 });
      root.scrollIntoView({ block: "center", behavior: "smooth" });
      flash({ row: s.id, col: null });
      root.querySelector<HTMLElement>(`[data-suspect="${s.id}"]`)?.focus({ preventScroll: true });
    }
    window.addEventListener(SUSPECT_EVENT, onSuspect);
    return () => window.removeEventListener(SUSPECT_EVENT, onSuspect);
  }, [suspects, flash]);

  const rowLit = (id: number) => highlight?.row === id;
  const colLit = (v: string) => highlight?.col === v;

  return (
    <div className="cf-notebook" data-active={active} ref={rootRef}>
      {clues && (
        <section className="cf-nb__clues" aria-label={`Your clues, ${clues.length}`}>
          <button
            type="button"
            className="cf-nb__clues-toggle"
            aria-expanded={cluesOpen}
            aria-controls={cluesId}
            onClick={() => setCluesOpen((o) => !o)}
          >
            Your clues ({clues.length})
          </button>
          <div id={cluesId} className="cf-nb__clues-list" hidden={!cluesOpen}>
            {clues.length === 0 ? (
              <p className="cf-caption">No clues yet.</p>
            ) : (
              <ul>
                {clues.map((c) => (
                  <li key={c.id}>
                    <span className="cf-label">
                      Exhibit {c.exhibit} · Day {c.day}
                    </span>
                    <p className="cf-fact__text">
                      {c.isNew ? (
                        <mark>
                          <SuspectText text={c.text} names={names} />
                        </mark>
                      ) : (
                        <SuspectText text={c.text} names={names} />
                      )}
                    </p>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </section>
      )}

      <div className="cf-seg cf-nb__tabs" role="group" aria-label="Notebook columns">
        {groups.map((g) => (
          <button
            key={g.name}
            type="button"
            className="cf-seg__btn"
            aria-pressed={active === g.name}
            onClick={() => setActive(g.name as GroupName)}
          >
            <GroupIcon name={g.name} />
            {g.name}
          </button>
        ))}
      </div>

      <div className="cf-nb__scroll" ref={scrollRef}>
        <table>
          <thead>
            <tr className="cf-nb__group">
              <th className="cf-nb__corner" rowSpan={2}>
                <span className="cf-sr">Suspect</span>
              </th>
              {groups.map((g) => (
                <th key={g.name} colSpan={g.values.length} scope="colgroup" data-g={g.name}>
                  <span className="cf-nb__groupname">
                    <GroupIcon name={g.name} />
                    {g.name}
                  </span>
                </th>
              ))}
            </tr>
            <tr className="cf-nb__col">
              {groups.map((g) =>
                g.values.map((v) => (
                  <th key={g.name + v} scope="col" data-g={g.name} className={clsx(colLit(v) && "is-cross")}>
                    <span>{v}</span>
                  </th>
                )),
              )}
            </tr>
          </thead>
          <tbody>
            {suspects.map((s) => (
              <tr key={s.id}>
                <th
                  scope="row"
                  tabIndex={-1}
                  data-suspect={s.id}
                  className={clsx("cf-nb__name", rowLit(s.id) && "is-cross")}
                >
                  {s.name}
                </th>
                {groups.map((g) => (
                  <Fragment key={g.name}>
                    {g.values.map((v, i) => {
                      const key = cellKey(s.name, v);
                      const manual = marks[key] ?? "";
                      const isAuto = !manual && auto.has(key);
                      const shown: Mark = manual || (isAuto ? "no" : "");
                      return (
                        <td
                          key={key}
                          data-g={g.name}
                          className={clsx(
                            "cf-nb__cell",
                            i === 0 && "cf-nb__first",
                            (rowLit(s.id) || colLit(v)) && "is-cross",
                          )}
                        >
                          <button
                            type="button"
                            className={clsx("cf-nb__btn", shown === "yes" && "is-yes", isAuto && "is-auto")}
                            aria-label={`${s.name}, ${v}: ${WORD[shown]}${isAuto ? " (automatic)" : ""}`}
                            onClick={(e) => tap(key, s.id, v, e.currentTarget)}
                            onFocus={(e) => {
                              // Keyboard focus keeps the highlight (taps on iPhone never focus).
                              if (e.currentTarget.matches(":focus-visible")) flash({ row: s.id, col: v }, true);
                            }}
                            onBlur={() => {
                              if (!timer.current) setHighlight(null);
                            }}
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
          Tap a box: ✗ ruled out, ✓ confirmed. Small ✗ marks are filled in for you. Only you can see your notebook.
        </p>
        <Button onClick={undoLast} disabled={undo.length === 0}>
          Undo
        </Button>
        <p className="cf-sr" role="status" aria-live="polite">
          {status}
        </p>
      </div>
    </div>
  );
}

/** Room, Time or Item picture next to the group's name. */
function GroupIcon({ name }: { name: string }) {
  const Icon = GROUP_ICON[name];
  return Icon ? <Icon size={16} strokeWidth={1.75} aria-hidden="true" /> : null;
}
