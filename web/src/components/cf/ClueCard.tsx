import clsx from "clsx";
import type { Clue } from "@/lib/types";
import { Button } from "./Button";
import { Stamp } from "./Stamp";
import { SuspectText } from "./SuspectText";

interface Props {
  clue: Clue;
  exhibit?: number; // position N among the player's clues
  isNew?: boolean; // today's clue
  shared?: boolean; // from shared_clues
  suspectNames?: string[]; // suspect names in the story become links to the notebook
  used?: boolean; // shared clue the player marked as already used
  onToggleUsed?: () => void; // shows "Mark as used" on shared clues
}

type Kind = "message" | "receipt" | "card";

/** Picks the paper by `format`: chat bubble, receipt or index card. */
function kindOf(format: string | null): Kind {
  const f = (format ?? "").toLowerCase();
  if (f.includes("message") || f.includes("text")) return "message";
  if (f.includes("receipt")) return "receipt";
  return "card";
}

/** A clue as a paper document, with its exact fact printed underneath. */
export function ClueCard({ clue, exhibit, isNew, shared, suspectNames, used, onToggleUsed }: Props) {
  const story = clue.story ?? clue.text;
  // Hide the Fact strip when it would just repeat the story word for word.
  const showFact = clue.story !== null && !clue.story.includes(clue.text);
  const kind = kindOf(clue.format);
  const format = clue.format ?? "Clue";

  const label = shared
    ? `${format} · ${clue.from}'s clue, opened for everyone`
    : `Exhibit ${exhibit ?? 1} · ${format}`;

  const card = (
    <article
      className={clsx("cf-clue", `cf-clue--${kind}`, isNew && "is-new", shared && "is-shared", used && "is-used")}
    >
      {isNew && kind !== "receipt" && <Stamp className="cf-clue__flag">New today</Stamp>}
      <div className="cf-clue__meta">
        <span className="cf-label">{label}</span>
        {!shared && <span className="cf-label">Day {clue.day}</span>}
        {shared && used && <span className="cf-label">Used</span>}
      </div>

      {kind === "message" && (
        <div className="cf-msg">
          <p className="cf-msg__bubble">
            <SuspectText text={story} names={suspectNames} />
          </p>
        </div>
      )}
      {kind === "receipt" && (
        <p className="cf-receipt__body">
          <SuspectText text={story} names={suspectNames} />
        </p>
      )}
      {kind === "card" && (
        <p className="cf-clue__text">
          <SuspectText text={story} names={suspectNames} />
        </p>
      )}

      {showFact && (
        <div className="cf-fact">
          <span className="cf-label">Fact</span>
          <p className="cf-fact__text">{isNew ? <mark>{clue.text}</mark> : clue.text}</p>
        </div>
      )}

      {shared && onToggleUsed && (
        <Button variant="quiet" className="justify-self-start" aria-pressed={Boolean(used)} onClick={onToggleUsed}>
          {used ? "Used, tap to undo" : "Mark as used"}
        </Button>
      )}
    </article>
  );

  // Receipts have a torn edge (a CSS mask that would also cut off the stamp),
  // so their shadow and the "New today" stamp live on a wrapper.
  if (kind !== "receipt") return card;
  return (
    <div className="cf-drop">
      {card}
      {isNew && <Stamp className="cf-clue__flag">New today</Stamp>}
    </div>
  );
}
