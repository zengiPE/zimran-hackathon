"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { errorText, isStatus, openNextCase } from "@/lib/api";
import { localPath } from "@/lib/storage";
import type { NextAccess, NextCaseOut } from "@/lib/types";
import { Button, ButtonLink } from "./Button";

type Auth = { token: string } | { host_token: string };

interface Props {
  caseId: string;
  auth: Auth; // a player token, or the host token on the host screen
  caseNumber: number; // this case's number in the crew
  access?: NextAccess; // undefined on an older API: fall back to the paywall link
  nextUrl?: string | null; // someone already opened the next case: your link into it
  onOpened?: (out: NextCaseOut) => void; // e.g. remember the demo seats
}

/** Paywall link that carries the token, so the paywall can open the next case after paying. */
function paywallHref(caseId: string, auth: Auth) {
  const q = new URLSearchParams({ case_id: caseId });
  if ("token" in auth) q.set("token", auth.token);
  else q.set("host_token", auth.host_token);
  return `/paywall?${q}`;
}

/** "Open the next case": same crew, new mystery. Goes to the paywall when the crew must pay. */
export function NextCase({ caseId, auth, caseNumber, access, nextUrl, onOpened }: Props) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const next = caseNumber + 1;
  const paywall = paywallHref(caseId, auth);

  // Someone in the crew already opened it: everyone just joins.
  if (nextUrl) {
    return (
      <div className="cf-stack">
        <p className="m-0">Case #{next} is open. Same crew, new mystery.</p>
        <ButtonLink variant="primary" href={localPath(nextUrl)}>
          Join case #{next}
        </ButtonLink>
      </div>
    );
  }

  if (!access || access.requires_payment) {
    return (
      <ButtonLink variant="primary" href={paywall}>
        Open the next case
      </ButtonLink>
    );
  }

  async function open() {
    setBusy(true);
    setError(null);
    try {
      const out = await openNextCase(caseId, auth);
      onOpened?.(out);
      const url = out.you?.url ?? out.host_url;
      window.location.href = localPath(url);
    } catch (err) {
      setBusy(false);
      if (isStatus(err, 402)) router.push(paywall); // someone has to pay first
      else setError(errorText(err));
    }
  }

  return (
    <div className="cf-stack">
      <Button variant="primary" onClick={open} disabled={busy}>
        {busy ? "Writing your next case file…" : "Open the next case"}
      </Button>
      <p className="cf-caption">
        {access.paid ? "Paid. " : ""}Same crew, new mystery. Everyone gets a link in their old one.
      </p>
      {error && (
        <p className="cf-error" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}
