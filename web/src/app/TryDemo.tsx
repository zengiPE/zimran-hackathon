"use client";

import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";
import { Button } from "@/components/cf/Button";
import { createCase, errorText, isStatus } from "@/lib/api";
import { localPath, readJSON, saveCase, writeJSON } from "@/lib/storage";
import type { CreateCaseOut } from "@/lib/types";

const SEED = 7; // the tested demo case: same seed = same case every time
const NAME_KEY = "casefile:name";

/**
 * Solo demo: you + 3 AI teammates (Nora, Felix, Kai).
 * If the API has AI teammates off (409) or doesn't know `solo` yet (422),
 * fall back to the classic demo where one person plays all four seats.
 */
async function createDemo(me: string): Promise<CreateCaseOut> {
  try {
    return await createCase({ solo: { me }, theme: "lake-house", seed: SEED });
  } catch (err) {
    if (!isStatus(err, 409) && !isStatus(err, 422)) throw err;
    return createCase({
      theme: "lake-house",
      players: [me, "Blake", "Casey", "Drew"],
      demo: true,
      seed: SEED,
    });
  }
}

/** "Try a demo case": asks your name, then opens your screen in a ready-made case. */
export function TryDemo() {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function show() {
    setName(readJSON<string>(NAME_KEY) ?? "");
    setOpen(true);
  }

  async function start(e: FormEvent) {
    e.preventDefault();
    const me = name.trim();
    if (!me) {
      setError("Add your name so your teammates know who they're talking to.");
      return;
    }
    setBusy(true);
    setError(null);
    writeJSON(NAME_KEY, me);
    try {
      const out = await createDemo(me);
      // Remember the host token and every seat, so DemoBar can move days and switch seats.
      saveCase({ case_id: out.case_id, host_token: out.host_token, invites: out.invites, demo: true });
      router.push(localPath(out.invites[0].url));
    } catch (err) {
      setError(errorText(err));
      setBusy(false);
    }
  }

  if (!open) {
    return (
      <Button block onClick={show}>
        Try a demo case
      </Button>
    );
  }

  return (
    <form className="cf-composer" onSubmit={start} noValidate>
      <label className="cf-sr" htmlFor="demo-name">
        Your name
      </label>
      <input
        id="demo-name"
        className="cf-input"
        type="text"
        placeholder="Your name"
        value={name}
        maxLength={24}
        autoComplete="given-name"
        autoFocus
        onChange={(e) => setName(e.target.value)}
        disabled={busy}
      />
      <Button type="submit" block disabled={busy}>
        {busy ? "Writing your case file…" : "Start the demo"}
      </Button>
      {error && (
        <p className="cf-error basis-full" role="alert">
          {error}
        </p>
      )}
    </form>
  );
}
