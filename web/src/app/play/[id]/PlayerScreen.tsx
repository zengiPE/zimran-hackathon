"use client";

import { useParams, useRouter, useSearchParams } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { Board } from "@/components/cf/BoardPost";
import { CaseHeader } from "@/components/cf/CaseHeader";
import { ClueCard } from "@/components/cf/ClueCard";
import { DemoBar } from "@/components/cf/DemoBar";
import { Composer } from "@/components/cf/Composer";
import { Drawer } from "@/components/cf/Drawer";
import { Notebook } from "@/components/cf/Notebook";
import { RevealBoard } from "@/components/cf/RevealBoard";
import { Roster } from "@/components/cf/RosterRow";
import { ErrorNote, PaperLoader, PaperSkeleton, Screen } from "@/components/cf/States";
import { VotePicker } from "@/components/cf/VotePicker";
import { advanceDay, askHint, castVote, errorText, isStatus, postBoard } from "@/lib/api";
import { caseCopy } from "@/lib/caseCopy";
import { paragraphs } from "@/lib/format";
import { loadCase, readJSON, writeJSON } from "@/lib/storage";
import { useMe, useReveal } from "@/lib/useCase";

export function PlayerScreen() {
  const { id } = useParams<{ id: string }>();
  const token = useSearchParams().get("token");
  const { data: me, error, mutate } = useMe(id, token);
  const reveal = useReveal(id, me?.phase === "reveal");
  const router = useRouter();

  // A demo case created in this browser: we know every seat and the host token.
  const [saved] = useState(() => loadCase(id));

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
    return (
      <main className="cf-cork min-h-dvh">
        <div className="mx-auto max-w-[960px]">
          {reveal.data ? (
            <RevealBoard reveal={reveal.data} suspects={me.suspects} />
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

  async function post(text: string) {
    try {
      const fresh = await postBoard(id, myToken, text);
      // Show the post right away, without waiting for the next poll.
      await mutate((d) => (d ? { ...d, board: [...d.board, fresh] } : d), { revalidate: false });
      // Bring the new post into view above the pinned composer.
      requestAnimationFrame(() => window.scrollTo({ top: document.body.scrollHeight, behavior: "smooth" }));
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
          names={demo.invites.map((i) => i.name)}
          current={me.me.name}
          day={me.day}
          daysTotal={me.days_total}
          phase={me.phase}
          onViewAs={viewAs}
          onNextDay={demoNextDay}
          onHint={demoHint}
        />
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
      />

      <Drawer title="Case brief" defaultOpen={briefOpen} bodyClassName="cf-stack">
        {paragraphs(me.intro).map((p) => (
          <p key={p} className="m-0">
            {p}
          </p>
        ))}
      </Drawer>

      {me.phase === "vote" ? (
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
            <div key={today.id} className="cf-fade">
              <ClueCard clue={today} exhibit={exhibit(today.id)} isNew />
            </div>
          ) : (
            <p className="cf-caption">No clue for you today. Check the board.</p>
          )}
        </section>
      )}

      {earlier.length > 0 && (
        <Drawer title={`Your earlier clues (${earlier.length})`} bodyClassName="cf-stack">
          {earlier.map((c) => (
            <ClueCard key={c.id} clue={c} exhibit={exhibit(c.id)} />
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

      <Board posts={me.board} myName={me.me.name} />
      <Composer pinned onPost={post} />
    </Screen>
  );
}
