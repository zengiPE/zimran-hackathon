import clsx from "clsx";
import type { CSSProperties, Ref } from "react";
import { initial } from "@/lib/format";
import type { Suspect } from "@/lib/types";

export type Verdict = "none" | "cleared" | "guilty";

// Fixed tilts between -4° and 4°, picked by suspect id so they never jump.
const TILTS = [-3, 2, -1, 3, -2, 1];

interface Props {
  suspect: Suspect;
  verdict?: Verdict;
  fluid?: boolean; // fill a grid cell
  thunk?: boolean; // stamps land with a thunk (Reveal)
  pinRef?: Ref<HTMLSpanElement>; // RevealBoard measures the pin for its strings
}

/** A suspect as a pinned polaroid. The initial is the portrait. */
export function SuspectCard({ suspect, verdict = "none", fluid = true, thunk, pinRef }: Props) {
  const tilt = TILTS[suspect.id % TILTS.length];
  return (
    <figure
      className={clsx(
        "cf-suspect",
        fluid && "cf-suspect--fluid",
        verdict === "cleared" && "is-cleared",
        verdict === "guilty" && "is-guilty",
      )}
      style={{ "--tilt": `${tilt}deg` } as CSSProperties}
    >
      <span className="cf-pin" aria-hidden="true" ref={pinRef} />
      <div className="cf-suspect__photo" aria-hidden="true">
        {initial(suspect.name)}
      </div>
      <figcaption>
        <p className="cf-suspect__name">{suspect.name}</p>
        <p className="cf-suspect__role">{suspect.role}</p>
        <span
          className={clsx("cf-stamp cf-stamp--muted cf-suspect__verdict cf-verdict--cleared", thunk && "cf-stamp--thunk")}
        >
          Cleared
        </span>
        <span
          className={clsx("cf-stamp cf-stamp--red cf-suspect__verdict cf-verdict--guilty", thunk && "cf-stamp--thunk")}
        >
          Guilty
        </span>
      </figcaption>
    </figure>
  );
}
