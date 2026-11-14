import { FileSearch, FolderPlus, Vote } from "lucide-react";
import { ButtonLink } from "@/components/cf/Button";
import { CreateCase } from "./CreateCase";
import { TryDemo } from "./TryDemo";

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

// The jury tests the product alone in a browser: tell them exactly what to press.
// Button names here must match the screens.
const JURY_PATH = [
  "Press Try a demo case, type your name, press Start the demo: you play with three AI teammates, Nora, Felix and Kai.",
  "Read Today's evidence, press Share this clue, tap boxes in Your notebook, read the board.",
  "In the dashed demo bar, press Next day twice, then Open voting.",
  "Pick a suspect, press Cast your vote and watch the reveal.",
  "Press Open the next case: the paywall takes the Stripe test card 4242 4242 4242 4242.",
];

// Landing: what Casefile is in five seconds, then the Create case form.
// Phones: one column. Laptops (1024px+): the pitch on the left, the form on the right.
export default function Home() {
  return (
    <main className="cf-desk cf-screen cf-landing min-h-dvh">
      <div className="cf-landing__intro">
        <header className="cf-stack">
          <span className="cf-label">Casefile</span>
          <h1 className="cf-hero">Your group chat went quiet.</h1>
          <p className="cf-lead">Crack a case together, five minutes a day.</p>
          <ButtonLink variant="primary" block href="#create">
            Start a case
          </ButtonLink>
          <TryDemo />
          <p className="cf-caption">
            Play a ready case now with three AI teammates. They share their clues and argue back, so you can
            try it alone.
          </p>
        </header>

        <section className="cf-judges" aria-labelledby="judges">
          <span className="cf-label">For the jury · demo mode</span>
          <h2 className="cf-heading" id="judges">
            Judging? The 3-minute path
          </h2>
          <ol className="cf-judges__list">
            {JURY_PATH.map((step) => (
              <li key={step}>{step}</li>
            ))}
          </ol>
          <p className="cf-caption">
            Playing with real friends instead? Use Create case below: the host screen shows a QR code for each
            player.
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
