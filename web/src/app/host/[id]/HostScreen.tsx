"use client";

import { useParams, useSearchParams } from "next/navigation";
import { useState } from "react";
import { Button } from "@/components/cf/Button";
import { PlayerInvite } from "@/components/cf/PlayerInvite";
import { RevealBoard } from "@/components/cf/RevealBoard";
import { Stamp } from "@/components/cf/Stamp";
import { PaperLoader } from "@/components/cf/States";
import { advanceDay, askHint, errorText, isStatus } from "@/lib/api";
import type { HostOut, PlayerRow } from "@/lib/types";
import { useHost, useReveal } from "@/lib/useCase";

/** What the host sees under each QR code. */
function playerStatus(p: PlayerRow, phase: HostOut["phase"]): string {
  if (!p.joined) return "Hasn't joined yet";
  if (phase !== "play") return p.voted ? "Voted" : "Hasn't voted yet";
  return p.opened_today ? "Opened today's clue" : "Hasn't opened today's clue";
}

export function HostScreen() {
  const { id } = useParams<{ id: string }>();
  const token = useSearchParams().get("token");
  const { data: host, error, mutate } = useHost(id, token);
  const reveal = useReveal(id, host?.phase === "reveal");
  const [busy, setBusy] = useState(false);
  const [note, setNote] = useState<string | null>(null);

  async function nextDay() {
    if (!token) return;
    setBusy(true);
    setNote(null);
    try {
      const fresh = await advanceDay(id, token);
      await mutate(fresh, { revalidate: false });
    } catch (err) {
      if (isStatus(err, 409)) await mutate();
      else setNote(errorText(err));
    } finally {
      setBusy(false);
    }
  }

  async function hint() {
    if (!token) return;
    setBusy(true);
    setNote(null);
    try {
      const { shared } = await askHint(id, token);
      setNote(`Hint: ${shared.from}'s clue is now open for everyone.`);
    } catch (err) {
      setNote(isStatus(err, 409) ? "No hints yet." : errorText(err));
    } finally {
      setBusy(false);
    }
  }

  // ---- Errors and loading ----
  if (!token || (error && !host)) {
    const message = token ? errorText(error) : "This link doesn't work. Ask the host for a new one.";
    return (
      <main className="cf-cork min-h-dvh">
        <div className="mx-auto max-w-[480px]">
          <p className="cf-error">{message}</p>
        </div>
      </main>
    );
  }
  if (!host) {
    return (
      <main className="cf-cork min-h-dvh">
        <div className="mx-auto max-w-[480px]">
          <PaperLoader />
        </div>
      </main>
    );
  }

  const joined = host.players.filter((p) => p.joined).length;
  const opened = host.players.filter((p) => p.opened_today).length;
  const total = host.players.length;
  const where =
    host.phase === "play" ? `Day ${host.day} of ${host.days_total}` : host.phase === "vote" ? "Voting" : "Reveal";
  const nextLabel =
    host.phase === "vote" ? "Show the reveal" : host.day >= host.days_total ? "Open voting" : "Next day";

  return (
    <main className="cf-cork min-h-dvh">
      <div className="mx-auto grid max-w-[1200px] gap-6">
        <header className="cf-host__head">
          <div className="cf-note cf-host__case">
            <span className="cf-label">
              Case file · {where}
              {host.demo && " · Demo"}
            </span>
            <h1 className="cf-heading">{host.title}</h1>
            {/* Big enough to read from the back of the room on a projector. */}
            <div className="cf-host__count">
              <p className="cf-host__num" aria-live="polite">
                {host.phase === "play" ? `${joined} of ${total} joined` : `${host.votes_count} of ${total} voted`}
              </p>
              {host.phase === "play" && joined === total && <Stamp>All in</Stamp>}
              {host.phase !== "play" && host.votes_count === total && <Stamp>All voted</Stamp>}
            </div>
            {host.phase === "play" && (
              <p className="cf-caption">
                {opened} of {total} opened today&apos;s clue
              </p>
            )}
          </div>
          {host.phase !== "reveal" && (
            <div className="cf-note cf-host__actions">
              <div className="flex flex-wrap gap-2">
                <Button small disabled={busy || host.phase !== "play"} onClick={hint}>
                  Hint
                </Button>
                {host.demo && (
                  <Button variant="primary" small disabled={busy} onClick={nextDay}>
                    {nextLabel}
                  </Button>
                )}
              </div>
              {note && (
                <p className="cf-caption" role="status">
                  {note}
                </p>
              )}
            </div>
          )}
        </header>

        {host.phase === "reveal" ? (
          reveal.data ? (
            <RevealBoard reveal={reveal.data} suspects={host.suspects} />
          ) : reveal.error ? (
            <p className="cf-error">{errorText(reveal.error)}</p>
          ) : (
            <PaperLoader label="Pinning the clues to the board…" />
          )
        ) : (
          <div className="cf-invites cf-invites--host">
            {host.players.map((p) => (
              <PlayerInvite
                key={p.idx}
                name={p.name}
                url={p.url ?? ""}
                joined={p.joined}
                ai={p.is_ai}
                status={playerStatus(p, host.phase)}
              />
            ))}
          </div>
        )}
      </div>
    </main>
  );
}
