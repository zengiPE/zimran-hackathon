"use client";

import { Share2 } from "lucide-react";
import { useState } from "react";
import { errorText } from "@/lib/api";
import { Button } from "./Button";

interface Props {
  shared: boolean; // already on the board
  onShare: () => Promise<void>; // throw to show an error
  prominent?: boolean; // today's clue: a full key-style button and a line that says why
  withAi?: boolean; // the case has AI teammates (they count shared clues only)
}

/** "Share this clue": pins your clue to the board so the group (and AI teammates) can use it. */
export function ShareClue({ shared, onShare, prominent, withAi }: Props) {
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
    <div className="cf-stack cf-share">
      {prominent && (
        <p className="m-0">
          Nobody else has this clue. Share it so the group{withAi ? " (and AI teammates)" : ""} can use it.
        </p>
      )}
      <Button
        variant={prominent ? "secondary" : "quiet"}
        block={prominent}
        className={prominent ? undefined : "justify-self-start self-start"}
        onClick={share}
        disabled={busy}
      >
        {prominent && <Share2 size={20} strokeWidth={1.75} aria-hidden="true" />}
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
