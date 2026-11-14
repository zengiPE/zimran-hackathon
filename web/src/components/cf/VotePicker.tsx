"use client";

import { useId, useState, type FormEvent } from "react";
import { errorText } from "@/lib/api";
import { initial } from "@/lib/format";
import type { Suspect } from "@/lib/types";
import { Button } from "./Button";

interface Props {
  question: string; // "Who broke the record player?"
  suspects: Suspect[];
  myVote: number | null;
  votedCount: number;
  playersCount: number;
  onVote: (suspectId: number) => Promise<void>; // throw to show an error
}

/** Five suspect polaroids as radio buttons and one "Cast your vote" button. */
export function VotePicker({ question, suspects, myVote, votedCount, playersCount, onVote }: Props) {
  const name = useId();
  const [picked, setPicked] = useState<number | null>(myVote);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const votedFor = suspects.find((s) => s.id === myVote)?.name;
  const changed = picked !== null && picked !== myVote;

  async function submit(e: FormEvent) {
    e.preventDefault();
    if (picked === null || busy) return;
    setBusy(true);
    setError(null);
    try {
      await onVote(picked);
    } catch (err) {
      setError(errorText(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="cf-stack" onSubmit={submit}>
      <fieldset className="cf-vote">
        <legend className="cf-heading">{question}</legend>
        <div className="cf-vote__grid">
          {suspects.map((s) => (
            <label key={s.id} className="cf-suspect cf-suspect--fluid cf-suspect--pick">
              <input
                className="cf-sr"
                type="radio"
                name={name}
                value={s.id}
                aria-label={`${s.name}, ${s.role}`}
                checked={picked === s.id}
                onChange={() => setPicked(s.id)}
              />
              <span className="cf-pin" aria-hidden="true" />
              <span className="cf-suspect__photo" aria-hidden="true">
                {initial(s.name)}
              </span>
              <span className="cf-suspect__caption">
                <span className="cf-suspect__name">{s.name}</span>{" "}
                <span className="cf-suspect__role">{s.role}</span>{" "}
                <span className="cf-stamp cf-suspect__verdict cf-verdict--vote">Your vote</span>
              </span>
            </label>
          ))}
        </div>
      </fieldset>
      <Button variant="primary" block type="submit" disabled={busy || picked === null || !changed}>
        {busy ? "Sending…" : myVote === null ? "Cast your vote" : "Change your vote"}
      </Button>
      {error && (
        <p className="cf-error" role="alert">
          {error}
        </p>
      )}
      <p className="cf-caption" aria-live="polite">
        {votedFor
          ? `You voted for ${votedFor}. You can change it until the reveal.`
          : "You can change your vote until the reveal."}{" "}
        {votedCount} of {playersCount} have voted.
      </p>
    </form>
  );
}
