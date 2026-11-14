"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { Button } from "@/components/cf/Button";
import { createCase, errorText } from "@/lib/api";
import { localPath, saveCase } from "@/lib/storage";

// The tested demo case: same seed = same case every time.
const DEMO = {
  theme: "lake-house",
  players: ["Alex", "Blake", "Casey", "Drew"],
  demo: true,
  seed: 7,
};

/** "Try a demo case": one person plays every seat of a ready-made case. */
export function TryDemo() {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function start() {
    setBusy(true);
    setError(null);
    try {
      const out = await createCase(DEMO);
      // Remember the host token and every invite, so DemoBar can switch seats.
      saveCase({ case_id: out.case_id, host_token: out.host_token, invites: out.invites, demo: true });
      router.push(localPath(out.invites[0].url));
    } catch (err) {
      setError(errorText(err));
      setBusy(false);
    }
  }

  return (
    <>
      <Button block onClick={start} disabled={busy}>
        {busy ? "Writing your case file…" : "Try a demo case"}
      </Button>
      {error && (
        <p className="cf-error" role="alert">
          {error}
        </p>
      )}
    </>
  );
}
