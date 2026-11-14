"use client";

import { useState, type ReactNode } from "react";
import { Board } from "@/components/cf/BoardPost";
import { Button } from "@/components/cf/Button";
import { CaseHeader } from "@/components/cf/CaseHeader";
import { ClueCard } from "@/components/cf/ClueCard";
import { Composer } from "@/components/cf/Composer";
import { DemoBar } from "@/components/cf/DemoBar";
import { Drawer } from "@/components/cf/Drawer";
import { Notebook } from "@/components/cf/Notebook";
import { PlayerInvite } from "@/components/cf/PlayerInvite";
import { RevealBoard } from "@/components/cf/RevealBoard";
import { Roster } from "@/components/cf/RosterRow";
import { Stamp } from "@/components/cf/Stamp";
import { ErrorNote, PaperLoader, PaperSkeleton } from "@/components/cf/States";
import { SuspectCard } from "@/components/cf/SuspectCard";
import { VotePicker } from "@/components/cf/VotePicker";
import { ApiError } from "@/lib/api";
import { caseCopy } from "@/lib/caseCopy";
import { clues, host, me, reveal } from "@/lib/fixtures";
import { paragraphs } from "@/lib/format";
import type { BoardPost } from "@/lib/types";

const wait = (ms: number) => new Promise<void>((r) => setTimeout(r, ms));

/** A titled block of the kit. */
function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="cf-stack">
      <p className="cf-label">{title}</p>
      {children}
    </section>
  );
}

/** Board posts from today and yesterday, and a countdown 6 h 12 min away. */
function makeTimes() {
  const now = Date.now();
  const today = new Date(now).toISOString();
  const yesterday = new Date(now - 26 * 3600_000).toISOString();
  const posts: BoardPost[] = [
    { author: "Blake", text: "Mine says Jordan was not seen at 7. Crossing him off.", ts: yesterday },
    { author: "Casey", text: "Careful, we don't know WHEN Leo was on the porch. Anyone have times?", ts: today },
    { author: "Alex", text: "Leo was seen at 7:30 or 9:00. So not him in the Sunroom at 7.", ts: today },
  ];
  return { posts, in6h: new Date(now + (6 * 60 + 12) * 60_000).toISOString() };
}

export function Kit() {
  const [{ posts, in6h }] = useState(makeTimes);
  const opened = me.players.filter((p) => p.opened_today).length;
  const copy = caseCopy(me.title);

  return (
    <>
      <main className="cf-desk cf-screen">
        <h1 className="cf-heading">Component kit</h1>
        <p className="cf-caption">Every component in every state, on the real demo case (seed 7).</p>

        <Section title="Button">
          <div className="cf-row">
            <Button variant="primary">Start a case</Button>
            <Button>Share this clue</Button>
            <Button variant="quiet">Copy link</Button>
          </div>
          <div className="cf-row">
            <Button variant="primary" disabled>
              Cast your vote
            </Button>
            <span className="cf-caption">Voting opens on Day 4</span>
          </div>
          <Button variant="primary" block>
            Next day
          </Button>
        </Section>

        <Section title="Stamp">
          <div className="cf-row">
            <Stamp>Day 2</Stamp>
            <Stamp>Joined</Stamp>
            <Stamp straight>New today</Stamp>
            <Stamp tone="muted">Waiting</Stamp>
          </div>
          <div className="cf-row">
            <Stamp tone="muted">Cleared</Stamp>
            <Stamp tone="red">Guilty</Stamp>
            <Stamp big>Solved</Stamp>
          </div>
        </Section>

        <Section title="DemoBar">
          <DemoBar
            names={me.players.map((p) => p.name)}
            current="Alex"
            day={2}
            daysTotal={3}
            phase="play"
            onViewAs={() => {}}
            onNextDay={() => wait(400)}
            onHint={async () => {
              await wait(400);
              throw new ApiError(409, "No hints yet");
            }}
          />
        </Section>

        <Section title="CaseHeader · demo, day 2">
          <CaseHeader
            title={me.title}
            day={2}
            daysTotal={3}
            phase="play"
            nextUnlockAt={me.next_unlock_at}
            demo
            playersCount={4}
            openedCount={opened}
          />
        </Section>
        <Section title="CaseHeader · real days, day 1">
          <CaseHeader
            title={me.title}
            day={1}
            daysTotal={3}
            phase="play"
            nextUnlockAt={in6h}
            demo={false}
            playersCount={4}
            openedCount={3}
          />
        </Section>
        <Section title="CaseHeader · vote">
          <CaseHeader
            title={me.title}
            day={3}
            daysTotal={3}
            phase="vote"
            nextUnlockAt={in6h}
            demo
            playersCount={4}
            openedCount={4}
          />
        </Section>

        <Section title="Drawer · Case brief">
          <Drawer title="Case brief" defaultOpen bodyClassName="cf-stack">
            {paragraphs(me.intro).map((p) => (
              <p key={p} className="m-0">
                {p}
              </p>
            ))}
          </Drawer>
        </Section>

        <Section title="ClueCard · today, text message (LLM story, Fact shown)">
          <ClueCard clue={clues.messageNew} exhibit={2} isNew />
        </Section>
        <Section title="ClueCard · template story (Fact hidden, it repeats the story)">
          <ClueCard clue={clues.photoTemplate} exhibit={1} />
          <ClueCard clue={clues.receiptTemplate} exhibit={2} />
        </Section>
        <Section title="ClueCard · receipt and guestbook (LLM story)">
          <ClueCard clue={clues.receiptStory} exhibit={2} />
          <ClueCard clue={clues.guestbookStory} exhibit={3} />
        </Section>
        <Section title="ClueCard · no story">
          <ClueCard clue={clues.noStory} exhibit={1} />
        </Section>
        <Section title="ClueCard · shared">
          <ClueCard clue={clues.sharedOverheard} shared />
        </Section>

        <Section title="Notebook">
          <Notebook
            suspects={me.suspects}
            labels={me.labels}
            storageKey="notebook:kit:demo"
            clues={[
              { id: "a", text: clues.messageNew.text, isNew: true },
              { id: "b", text: clues.photoTemplate.text },
              { id: "c", text: clues.sharedOverheard.text },
            ]}
          />
        </Section>

        <Section title="Roster · play">
          <Roster players={host.players} phase="play" myIdx={0} />
        </Section>
        <Section title="Roster · vote">
          <Roster
            players={host.players.map((p, i) => ({ ...p, voted: i < 2 }))}
            phase="vote"
            myIdx={1}
          />
        </Section>

        <Section title="VotePicker · nothing picked">
          <VotePicker
            question={copy.question}
            suspects={me.suspects}
            myVote={null}
            votedCount={2}
            playersCount={4}
            onVote={() => wait(400)}
          />
        </Section>
        <Section title="VotePicker · voted for Priya">
          <VotePicker
            question={copy.question}
            suspects={me.suspects}
            myVote={0}
            votedCount={3}
            playersCount={4}
            onVote={() => wait(400)}
          />
        </Section>

        <Section title="Board · empty">
          <Board posts={[]} myName="Alex" />
        </Section>
        <Section title="Board · posts, composer that fails with 403">
          <Board posts={posts} myName="Alex">
            <Composer
              onPost={async () => {
                await wait(300);
                throw new ApiError(403, "Bad token");
              }}
            />
          </Board>
        </Section>

        <Section title="Loading and errors">
          <PaperLoader label="Writing your case file…" />
          <PaperSkeleton blocks={2} />
          <ErrorNote>This link doesn&apos;t work. Ask the host for a new one.</ErrorNote>
          <ErrorNote>We couldn&apos;t find this case.</ErrorNote>
        </Section>

        <Section title="Composer · pinned to the bottom">
          <Composer pinned onPost={() => wait(400)} />
        </Section>
      </main>

      <div className="cf-cork">
        <div className="mx-auto grid max-w-[1200px] gap-10">
          <p className="cf-label">PlayerInvite · Host screen</p>
          <div className="cf-invites">
            {host.players.map((p) => (
              <PlayerInvite key={p.idx} name={p.name} url={p.url ?? ""} joined={p.joined} />
            ))}
          </div>

          <p className="cf-label">SuspectCard · open, cleared, guilty</p>
          <div className="cf-reveal__suspects">
            {me.suspects.map((s) => (
              <SuspectCard
                key={s.id}
                suspect={s}
                verdict={s.id === 0 ? "guilty" : s.id === 1 ? "cleared" : "none"}
              />
            ))}
          </div>

          <p className="cf-label">RevealBoard · final state</p>
          <RevealBoard reveal={reveal} suspects={me.suspects} />
        </div>
      </div>
    </>
  );
}
