"use client";

import { useState } from "react";
import { readJSON, writeJSON } from "@/lib/storage";
import { Button } from "./Button";

const KEY = "casefile:tips-seen"; // ids of tips this browser has dismissed

/**
 * A first-visit tip next to the thing it explains. Dashed like DemoBar (it's about
 * the app, not the case). "Got it" hides it for good in this browser.
 */
export function CoachMark({ id, children }: { id: string; children: React.ReactNode }) {
  const [hidden, setHidden] = useState(() => (readJSON<string[]>(KEY) ?? []).includes(id));
  if (hidden) return null;

  function dismiss() {
    const seen = readJSON<string[]>(KEY) ?? [];
    writeJSON(KEY, [...new Set([...seen, id])]);
    setHidden(true);
  }

  return (
    <aside className="cf-tip" aria-label="Tip">
      <p className="m-0">{children}</p>
      <Button variant="quiet" onClick={dismiss}>
        Got it
      </Button>
    </aside>
  );
}
