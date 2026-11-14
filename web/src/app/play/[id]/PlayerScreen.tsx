"use client";

import { useParams, useRouter, useSearchParams } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { Board } from "@/components/cf/BoardPost";
import { CaseHeader } from "@/components/cf/CaseHeader";
import { ClueCard } from "@/components/cf/ClueCard";
import { CrewRecord } from "@/components/cf/CrewRecord";
import { DemoBar } from "@/components/cf/DemoBar";
import { Composer } from "@/components/cf/Composer";
import { Drawer } from "@/components/cf/Drawer";
import { Notebook } from "@/components/cf/Notebook";
import { NextCase } from "@/components/cf/NextCase";
import { RevealBoard } from "@/components/cf/RevealBoard";
import { ShareClue } from "@/components/cf/ShareClue";
import { Roster } from "@/components/cf/RosterRow";
import { ErrorNote, PaperLoader, PaperSkeleton, Screen } from "@/components/cf/States";
import { VotePicker } from "@/components/cf/VotePicker";
import { advanceDay, askHint, castVote, errorText, isStatus, postBoard } from "@/lib/api";
import { caseCopy } from "@/lib/caseCopy";
import { paragraphs } from "@/lib/format";
import { loadCase, readJSON, saveCase, writeJSON } from "@/lib/storage";
import type { Clue, NextCaseOut } from "@/lib/types";
import { useMe, useReveal } from "@/lib/useCase";

export function PlayerScreen() {
  const { id } = useParams<{ id: string }>();
  const token = useSearchParams().get("token");
  const { data: me, error, mutate } = useMe(id, token);
  const reveal = useReveal(id, me?.phase === "reveal");
  const router = useRouter();

  // A demo case created in this browser: we know every seat and the host token.
  const [saved] = useState(() => loadCase(id));

  // A demo case created here: remember the next case's seats too, so DemoBar keeps working.
  function rememberNext(out: NextCaseOut) {
    if (saved) saveCase({ case_id: out.case_id, host_token: out.host_token, invites: out.invites, demo: true });
  }

  // "Case brief" is open on the first visit, collapsed after.
  const briefKey = `brief-seen:${id}:${token}`;
  const [briefOpen] = useState(() => !readJSON<boolean>(briefKey));
  useEffect(() => writeJSON(briefKey, true), [briefKey]);

  // When the day changes between polls, scroll to today's evidence.
  const todayRef = useRef<HTMLElement>(null);
  const lastDay = useRef<number | null>(null);
  const day = me?.day;
  useEffect(() => {
    if (day === undefined) return;
    if (lastDay.current !== null && lastDay.current !== day) {
      todayRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    }
    lastDay.current = day;
  }, [day]);

  // The reveal starts at the top of the page, with the counter.
  const phase = me?.phase;
  useEffect(() => {
    if (phase === "reveal") window.scrollTo({ top: 0 });
  }, [phase]);

  // ---- Errors and loading ----
  if (!token) {
    return (
      <Screen>
        <ErrorNote>This link doesn&apos;t work. Ask the host for a new one.</ErrorNote>
      </Screen>
    );
  }
  if (error && !me) {
    return (
      <Screen>
        <ErrorNote>{errorText(error)}</ErrorNote>
      </Screen>
    );
  }
  if (!me) {
    return (
      <Screen>
        <PaperSkeleton blocks={4} />
      </Screen>
    );
  }

  // ---- Reveal: the cork board takes the whole screen ----
  if (me.phase === "reveal") {
    const crew = me.crew ?? reveal.data?.crew;
    return (
      <main className="cf-cork min-h-dvh">
        <div className="mx-auto max-w-[960px]">
          {reveal.data ? (
            <RevealBoard reveal={reveal.data} suspects={me.suspects}>
              {crew && <CrewRecord crew={crew} />}
              <NextCase
                caseId={id}
                auth={{ token }}
                caseNumber={crew?.case_number ?? 1}
                access={me.next_access ?? reveal.data.next_access}
                nextUrl={me.next_case?.url}
                onOpened={rememberNext}
              />
            </RevealBoard>
          ) : reveal.error ? (
            <ErrorNote>{errorText(reveal.error)}</ErrorNote>
          ) : (
            <PaperLoader label="Pinning the clues to the board…" />
          )}
        </div>
      </main>
    );
  }

  // ---- Play and vote ----
  const myToken = token;
  const clues = [...me.my_clues].sort((a, b) => a.day - b.day);
  const exhibit = (clueId: string) => clues.findIndex((c) => c.id === clueId) + 1;
  const today = clues.find((c) => c.day === me.day);
  const earlier = clues.filter((c) => c !== today).reverse(); // newest first
  const opened = me.players.filter((p) => p.opened_today).length;
  const voted = me.players.filter((p) => p.voted).length;
  // Facts for the notebook strip: your clues and shared ones, newest first.
  const notebookClues = [...me.my_clues, ...me.shared_clues]
    .sort((a, b) => b.day - a.day)
    .map((c) => ({ id: c.id, text: c.text, isNew: c.id === today?.id }));

  // AI teammates (new API): who is typing, which of your clues are already on the board.
  const aiApi = me.typing !== undefined;
  const viewingAi = Boolean(me.me.is_ai); // DemoBar switched to an AI seat: read only
  const sharedIds = new Set(
    me.board.filter((b) => b.author === me.me.name && b.fact).map((b) => (b.fact as Clue).id),
  );
  const canShare = aiApi && !viewingAi;

  async function post(text: string, factId?: string) {
    try {
      const fresh = await postBoard(id, myToken, text, factId);
      // Show the post right away, without waiting for the next poll.
      await mutate((d) => (d ? { ...d, board: [...d.board, fresh] } : d), { revalidate: false });
      // Bring the new post into view above the pinned composer.
      requestAnimationFrame(() => window.scrollTo({ top: document.body.scrollHeight, behavior: "smooth" }));
      // AI teammates start "typing" a reply right away: refresh soon to show it.
      if (aiApi) setTimeout(() => void mutate(), 600);
    } catch (err) {
      if (!isStatus(err, 409)) throw err;
      await mutate(); // 409 = wrong phase: quietly refresh /me
    }
  }

  async function vote(suspect: number) {
    try {
      await castVote(id, myToken, suspect);
      await mutate(); // if everyone voted, phase is now "reveal"
    } catch (err) {
      if (!isStatus(err, 409)) throw err;
      await mutate();
    }
  }

  // ---- Demo controls (only for a demo case created in this browser) ----
  const demo = me.demo && saved ? saved : null;

  function viewAs(name: string) {
    const seat = demo?.invites.find((i) => i.name === name);
    if (!seat || seat.token === myToken) return;
    window.scrollTo({ top: 0 });
    router.replace(`/play/${id}?token=${encodeURIComponent(seat.token)}`, { scroll: false });
  }

  async function demoNextDay() {
    if (!demo) return;
    await advanceDay(id, demo.host_token);
    await mutate();
  }

  async function demoHint() {
    if (!demo) return;
    await askHint(id, demo.host_token);
    await mutate();
  }

  return (
    <Screen>
      {demo && (
        <DemoBar
          seats={demo.invites}
          current={me.me.name}
          day={me.day}
          daysTotal={me.days_total}
          phase={me.phase}
          onViewAs={viewAs}
          onNextDay={demoNextDay}
          onHint={demoHint}
        />
      )}

      {viewingAi && (
        <p className="cf-error" role="status">
          You&apos;re looking at {me.me.name}&apos;s screen. {me.me.name} is an AI teammate: switch back to
          yourself to post or vote.
        </p>
      )}

      <CaseHeader
        title={me.title}
        day={me.day}
        daysTotal={me.days_total}
        phase={me.phase}
        nextUnlockAt={me.next_unlock_at}
        demo={me.demo}
        playersCount={me.players.length}
        openedCount={opened}
        caseNumber={me.crew?.case_number}
      />

      <Drawer title="Case brief" defaultOpen={briefOpen} bodyClassName="cf-stack">
        {paragraphs(me.intro).map((p) => (
          <p key={p} className="m-0">
            {p}
          </p>
        ))}
      </Drawer>

      {me.phase === "vote" && viewingAi ? (
        <section ref={todayRef} className="cf-stack scroll-mt-4">
          <h2 className="cf-heading">{caseCopy(me.title).question}</h2>
          <p className="m-0">
            {me.my_vote !== null
              ? `${me.me.name} voted for ${me.suspects.find((s) => s.id === me.my_vote)?.name ?? "someone"}.`
              : `${me.me.name} hasn't voted yet.`}
          </p>
        </section>
      ) : me.phase === "vote" ? (
        <section ref={todayRef} className="scroll-mt-4">
          <VotePicker
            key={myToken}
            question={caseCopy(me.title).question}
            suspects={me.suspects}
            myVote={me.my_vote}
            votedCount={voted}
            playersCount={me.players.length}
            onVote={vote}
          />
        </section>
      ) : (
        <section ref={todayRef} className="cf-stack scroll-mt-4" aria-labelledby="today">
          <h2 className="cf-heading" id="today">
            Today&apos;s evidence
          </h2>
          {today ? (
            <div key={today.id} className="cf-fade cf-stack">
              <ClueCard clue={today} exhibit={exhibit(today.id)} isNew />
              {canShare && <ShareClue shared={sharedIds.has(today.id)} onShare={() => post("", today.id)} />}
            </div>
          ) : (
            <p className="cf-caption">No clue for you today. Check the board.</p>
          )}
        </section>
      )}

      {earlier.length > 0 && (
        <Drawer title={`Your earlier clues (${earlier.length})`} bodyClassName="cf-stack">
          {earlier.map((c) => (
            <div key={c.id} className="cf-stack">
              <ClueCard clue={c} exhibit={exhibit(c.id)} />
              {canShare && <ShareClue shared={sharedIds.has(c.id)} onShare={() => post("", c.id)} />}
            </div>
          ))}
        </Drawer>
      )}

      <Drawer title="Your notebook">
        <Notebook
          key={myToken}
          suspects={me.suspects}
          labels={me.labels}
          storageKey={`notebook:${id}:${myToken}`}
          clues={notebookClues}
        />
      </Drawer>

      {me.shared_clues.length > 0 && (
        <section className="cf-stack" aria-labelledby="shared">
          <h2 className="cf-heading" id="shared">
            Opened for everyone
          </h2>
          {me.shared_clues.map((c) => (
            <ClueCard key={c.id} clue={c} shared />
          ))}
        </section>
      )}

      <Drawer title={`Players (${me.players.length})`}>
        <Roster players={me.players} phase={me.phase} myIdx={me.me.idx} />
      </Drawer>

      <Board posts={me.board} myName={me.me.name} typing={me.typing} />
      {!viewingAi && <Composer pinned onPost={(text) => post(text)} />}
    </Screen>
  );
}
