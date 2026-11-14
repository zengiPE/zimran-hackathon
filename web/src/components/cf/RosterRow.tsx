import clsx from "clsx";
import { initial } from "@/lib/format";
import type { Phase, PlayerRow } from "@/lib/types";

/** Player status in words. First match wins. */
function status(p: PlayerRow, phase: Phase): { text: string; done: boolean } {
  if (phase !== "play" && p.voted) return { text: "Voted", done: true };
  if (phase !== "play" && p.joined) return { text: "Hasn't voted yet", done: false };
  if (p.opened_today) return { text: "Opened today's clue", done: true };
  if (p.joined) return { text: "Hasn't opened today's clue", done: false };
  return { text: "Hasn't joined yet", done: false };
}

/** One row of the in-game roster. */
export function RosterRow({ player, phase, isMe }: { player: PlayerRow; phase: Phase; isMe: boolean }) {
  const s = status(player, phase);
  return (
    <li className="cf-roster__row">
      <span className={clsx("cf-avatar", player.is_ai && "cf-avatar--ai")} aria-hidden="true">
        {initial(player.name)}
      </span>
      <span className="cf-roster__name">
        {player.name}
        {isMe && " (you)"} {player.is_ai && <span className="cf-tag">AI teammate</span>}
      </span>
      <span className={clsx("cf-roster__status", s.done && "cf-roster__status--done")}>{s.text}</span>
    </li>
  );
}

/** The roster: you first, then the rest by idx. */
export function Roster({ players, phase, myIdx }: { players: PlayerRow[]; phase: Phase; myIdx?: number }) {
  const sorted = [...players].sort((a, b) => {
    if (a.idx === myIdx) return -1;
    if (b.idx === myIdx) return 1;
    return a.idx - b.idx;
  });
  return (
    <ul className="cf-roster" aria-label="Players">
      {sorted.map((p) => (
        <RosterRow key={p.idx} player={p} phase={phase} isMe={p.idx === myIdx} />
      ))}
    </ul>
  );
}
