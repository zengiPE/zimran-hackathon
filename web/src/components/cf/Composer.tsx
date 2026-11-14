"use client";

import clsx from "clsx";
import { useId, useState, type FormEvent } from "react";
import { errorText } from "@/lib/api";
import { Button } from "./Button";

const MAX = 280;

interface Props {
  onPost: (text: string) => Promise<void>; // throw to show an error
  pinned?: boolean; // stick to the bottom of the screen
  disabled?: boolean;
}

/** One text field (1–280 characters) with a counter and a "Post" button. */
export function Composer({ onPost, pinned, disabled }: Props) {
  const id = useId();
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const trimmed = text.trim();

  async function submit(e: FormEvent) {
    e.preventDefault();
    if (!trimmed || busy) return;
    setBusy(true);
    setError(null);
    try {
      await onPost(trimmed);
      setText("");
    } catch (err) {
      setError(errorText(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className={clsx("cf-composer", pinned && "cf-composer--bar")} onSubmit={submit}>
      <label className="cf-sr" htmlFor={id}>
        Write a theory
      </label>
      <input
        className="cf-input"
        id={id}
        type="text"
        maxLength={MAX}
        placeholder="Write a theory"
        value={text}
        onChange={(e) => setText(e.target.value)}
        disabled={disabled}
        aria-describedby={error ? `${id}-error` : undefined}
        autoComplete="off"
      />
      <span className="cf-caption">
        {text.length} / {MAX}
      </span>
      <Button variant="primary" type="submit" disabled={disabled || busy || !trimmed}>
        {busy ? "Posting…" : "Post"}
      </Button>
      {error && (
        <p className="cf-error basis-full" id={`${id}-error`} role="alert">
          {error}
        </p>
      )}
    </form>
  );
}
