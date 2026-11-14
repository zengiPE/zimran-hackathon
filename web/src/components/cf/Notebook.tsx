"use client";

import clsx from "clsx";
import { Fragment, useState } from "react";
import { dropArticle } from "@/lib/format";
import type { Labels, Suspect } from "@/lib/types";

type Mark = "" | "no" | "yes";
type Marks = Record<string, Mark>; // key: "Priya|Sunroom"

const GLYPH: Record<Mark, string> = { "": "", no: "✗", yes: "✓" };
const WORD: Record<Mark, string> = { "": "blank", no: "ruled out", yes: "confirmed" };
const NEXT: Record<Mark, Mark> = { "": "no", no: "yes", yes: "" };

interface Props {
  suspects: Suspect[];
  labels: Labels;
  storageKey: string; // "notebook:{case_id}:{token}"
}

function load(key: string): Marks {
  try {
    const raw = window.localStorage.getItem(key);
    return raw ? (JSON.parse(raw) as Marks) : {};
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
 * The player's private logic grid. Marks live only in this browser.
 * Render it inside <BrowserOnly>: it reads localStorage on the first render.
 */
export function Notebook({ suspects, labels, storageKey }: Props) {
  const [marks, setMarks] = useState<Marks>(() => load(storageKey));

  const groups = [
    { name: "Room", values: labels.room },
    { name: "Time", values: labels.time },
    { name: "Item", values: labels.item.map(dropArticle) },
  ];

  function tap(key: string) {
    setMarks((prev) => {
      const next = { ...prev, [key]: NEXT[prev[key] ?? ""] };
      save(storageKey, next);
      return next;
    });
  }

  return (
    <div className="cf-notebook">
      <table>
        <thead>
          <tr className="cf-nb__group">
            <th className="cf-nb__corner" rowSpan={2}>
              <span className="cf-sr">Suspect</span>
            </th>
            {groups.map((g) => (
              <th key={g.name} colSpan={g.values.length} scope="colgroup">
                {g.name}
              </th>
            ))}
          </tr>
          <tr className="cf-nb__col">
            {groups.map((g) =>
              g.values.map((v) => (
                <th key={g.name + v} scope="col">
                  <span>{v}</span>
                </th>
              )),
            )}
          </tr>
        </thead>
        <tbody>
          {suspects.map((s) => (
            <tr key={s.id}>
              <th scope="row" className="cf-nb__name">
                {s.name}
              </th>
              {groups.map((g) => (
                <Fragment key={g.name}>
                  {g.values.map((v, i) => {
                    const key = `${s.name}|${v}`;
                    const mark = marks[key] ?? "";
                    return (
                      <td key={key} className={clsx("cf-nb__cell", i === 0 && "cf-nb__first")}>
                        <button
                          type="button"
                          className={clsx("cf-nb__btn", mark === "yes" && "is-yes")}
                          aria-label={`${s.name}, ${v}: ${WORD[mark]}`}
                          onClick={() => tap(key)}
                        >
                          {GLYPH[mark]}
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
      <p className="cf-nb__legend">Tap a box: ✗ ruled out, ✓ confirmed. Only you can see your notebook.</p>
    </div>
  );
}
