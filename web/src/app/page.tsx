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

// Landing: what Casefile is in five seconds, then the Create case form.
export default function Home() {
  return (
    <main className="cf-desk cf-screen min-h-dvh">
      <header className="cf-stack">
        <span className="cf-label">Casefile</span>
        <h1 className="cf-hero">Your group chat went quiet.</h1>
        <p className="cf-lead">Crack a case together, five minutes a day.</p>
        <ButtonLink variant="primary" block href="#create">
          Start a case
        </ButtonLink>
        <TryDemo />
        <p className="cf-caption">The demo is a ready case for four. You play every seat and move the days yourself.</p>
      </header>

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

      <CreateCase />
    </main>
  );
}
