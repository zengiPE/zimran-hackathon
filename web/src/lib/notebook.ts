// Notebook logic without React, so it can be tested on its own (notebook.test.ts).

export type Mark = "" | "no" | "yes";

/** Manual marks only, keyed by cellKey(). This exact shape is what localStorage keeps. */
export type Marks = Record<string, Mark>;

export interface Group {
  name: string; // "Room", "Time", "Item"
  values: string[]; // column headers
}

export const cellKey = (suspect: string, value: string) => `${suspect}|${value}`;

/**
 * Automatic ✗ marks: for every manual ✓ of suspect S in column X of group G,
 * the other boxes of S in G and the other boxes of column X are ruled out.
 * Returns the keys of those boxes. Manual marks are not removed from the set;
 * the caller lets a manual mark win over an automatic one.
 */
export function deriveAutoMarks(marks: Marks, suspects: string[], groups: Group[]): Set<string> {
  const auto = new Set<string>();
  for (const g of groups) {
    for (const s of suspects) {
      for (const x of g.values) {
        if (marks[cellKey(s, x)] !== "yes") continue;
        for (const v of g.values) if (v !== x) auto.add(cellKey(s, v)); // rest of the row in this group
        for (const o of suspects) if (o !== s) auto.add(cellKey(o, x)); // rest of the column
      }
    }
  }
  return auto;
}
