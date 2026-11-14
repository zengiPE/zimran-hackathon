import { FileSearch, FolderPlus, Vote } from "lucide-react";
import { ButtonLink } from "@/components/cf/Button";
import { CoverArt } from "@/components/cf/CoverArt";
import { SuspectCard } from "@/components/cf/SuspectCard";
import type { Suspect } from "@/lib/types";
import { CreateCase } from "./CreateCase";
import { TryDemo } from "./TryDemo";

// The hook: the demo case itself (The Lake House Weekend, seed 7), so visitors
// land inside a story the way Murdle opens on a mystery, not on a product pitch.
const SUSPECTS: Suspect[] = [
  { id: 0, name: "Priya", role: "The doctor on call all weekend" },
  { id: 1, name: "Jordan", role: "The ex-roommate who never grew up" },
  { id: 2, name: "Leo", role: "The guy who brought his guitar" },
  { id: 3, name: "Maya", role: "The planner who booked the cabin" },
  { id: 4, name: "Sam", role: "The newcomer, someone's plus-one" },
];

const STEPS = [
  {
    icon: FolderPlus,
    title: "Start a case",
    text: "Pick a story and add 3 to 6 friends. Everyone gets a private link.",
  },
  {
    icon: FileSearch,
    title: "One clue a day",
    text: "Each of you gets a different clue. Nobody can solve it alone, so talk it out on the board.",
  },
  {
    icon: Vote,
    title: "Vote, then the reveal",
    text: "After the last day, vote. Then watch the possible worlds melt down to one.",
  },
];

// First-case walkthrough for anyone new (the jury included). Button names must match the screens.
const FIRST_CASE = [
  "Press Take the case, type your name, press Start the demo. Three AI teammates join you: Nora, Felix and Kai.",
  "Read your clue. Nobody else has it, so press Share this clue.",
  "Open Your notebook and rule suspects out. Tap a name in a clue to jump to its row.",
  "In the dashed demo bar, press Next day twice, then Open voting.",
  "Cast your vote and watch the reveal. Then Open the next case: Stripe test card 4242 4242 4242 4242.",
];

// Phones: one column. Laptops (1024px+): the case and pitch on the left, Create case on the right.
export default function Home() {
  return (
    <main className="cf-desk cf-screen cf-landing min-h-dvh">
      <div className="cf-landing__intro">
        <section className="cf-case cf-hook" aria-labelledby="hook-title">
          <span className="cf-case__tab">Case file · free demo</span>
          <div className="cf-case__body cf-hook__body">
            <p className="cf-case__theme">The Lake House Weekend</p>
            <h1 className="cf-case__title" id="hook-title">
              Who broke the record player?
            </h1>
            <p className="cf-hook__story">
              Five college friends rented a cabin on Lake Wendell for their first reunion in years. Saturday night
              was supposed to be easy: grill, cards, too much rosé.
            </p>
            <p className="cf-hook__story">
              By Sunday the owner&apos;s prized 1970s record player lay smashed in the Sunroom. The clock stopped
              when it fell: 7:00 PM. One of these five was in the Sunroom at 7:00 PM.
            </p>
            <div className="cf-reveal__suspects cf-hook__suspects">
              {SUSPECTS.map((s) => (
                <SuspectCard key={s.id} suspect={s} />
              ))}
            </div>
            <TryDemo />
            <p className="cf-caption">You play with three AI teammates. About five minutes, no sign-up.</p>
          </div>
        </section>

        <section className="cf-stack cf-pitch" aria-labelledby="pitch-title">
          <CoverArt className="cf-pitch__art" />
          <h2 className="cf-hero" id="pitch-title">
            Your group chat went quiet.
          </h2>
          <p className="cf-lead">Crack a case together, five minutes a day.</p>
          <ButtonLink block href="#create">
            Start a case with friends
          </ButtonLink>
        </section>

        <section className="cf-judges" aria-labelledby="first-case">
          <span className="cf-label">Demo mode · about 3 minutes</span>
          <h2 className="cf-heading" id="first-case">
            New here? Your first case
          </h2>
          <ol className="cf-judges__list">
            {FIRST_CASE.map((step) => (
              <li key={step}>{step}</li>
            ))}
          </ol>
          <p className="cf-caption">
            Playing with real friends? Use Create case: the host screen shows a QR code for each player.
          </p>
        </section>

        <section className="cf-stack" aria-labelledby="how">
          <h2 className="cf-heading" id="how">
            How it works
          </h2>
          <ol className="cf-steps">
            {STEPS.map((s, i) => (
              <li key={s.title} className="cf-note">
                <span className="cf-label">Step {i + 1}</span>
                <p className="cf-steps__title">
                  <s.icon size={20} strokeWidth={1.75} aria-hidden="true" />
                  {s.title}
                </p>
                <p className="cf-caption">{s.text}</p>
              </li>
            ))}
          </ol>
        </section>
      </div>

      <div className="cf-landing__form">
        <CreateCase />
      </div>
    </main>
  );
}
