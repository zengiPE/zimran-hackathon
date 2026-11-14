import type { Crew } from "@/lib/types";
import { Stamp } from "./Stamp";

/** The crew's record under the verdict: the "come back next week" hook. */
export function CrewRecord({ crew }: { crew: Crew }) {
  const { case_number, cases_played, cases_solved, streak, members } = crew;
  if (cases_played === 0) return null;

  return (
    <div className="cf-crew">
      <div className="cf-crew__head">
        <span className="cf-label">Your crew&apos;s record</span>
        {streak >= 2 && (
          <Stamp straight tone="stamp">
            {streak} in a row
          </Stamp>
        )}
      </div>
      <p className="m-0">
        Case #{case_number} · {cases_solved} of {cases_played} solved
        {streak === 1 && " · on a streak"}
      </p>
      <ul className="cf-votes" aria-label="Crew record">
        {members.map((m) => (
          <li key={m.name}>
            <span>
              <b>{m.name}</b> {m.is_ai && <span className="cf-tag">AI teammate</span>}
            </span>
            <span className="cf-caption">
              {m.correct} of {m.played} right
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
