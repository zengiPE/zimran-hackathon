"use client";

import { useState } from "react";
import { errorText } from "@/lib/api";
import { Button } from "./Button";

interface Props {
  shared: boolean; // already on the board
  onShare: () => Promise<void>; // throw to show an error
}

/** "Share this clue": pins your clue to the board so the group (and AI teammates) can use it. */
export function ShareClue({ shared, onShare }: Props) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (shared) return <p className="cf-caption">Shared on the board.</p>;

  async function share() {
    setBusy(true);
    setError(null);
    try {
      await onShare();
    } catch (err) {
      setError(errorText(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="cf-stack">
      <Button variant="quiet" className="justify-self-start self-start" onClick={share} disabled={busy}>
        {busy ? "Sharing…" : "Share this clue"}
      </Button>
      {error && (
        <p className="cf-error" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}
