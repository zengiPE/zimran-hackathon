// Types copied from docs/api-contract.md. Keep them in sync with the API.

export type Phase = "play" | "vote" | "reveal";

export interface Theme {
  id: string;
  title: string;
  tagline: string;
}

export interface Suspect {
  id: number;
  name: string;
  role: string;
}

export interface Labels {
  room: string[]; // "Sunroom", "Porch"…
  time: string[]; // in time order: "7:00 PM", "7:30 PM"…
  item: string[]; // with the article: "a flashlight"
}

export interface Clue {
  id: string; // "d1p0" = day 1, player 0
  day: number;
  text: string; // the exact fact, shown in the Fact strip
  story: string | null; // themed text, shown big
  format: string | null; // "Text message", "Photo caption"…
  fact: Record<string, string | number>; // not for the UI
  from: string; // the player who got this clue
}

export interface BoardPost {
  author: string;
  text: string; // can be "" when a clue is attached
  ts: string;
  is_ai?: boolean; // an AI teammate's post (AI friends API)
  fact?: Clue | null; // attached clue ("Share this clue")
}

export interface PlayerRow {
  idx: number;
  name: string;
  is_ai?: boolean; // an AI teammate's seat
  joined: boolean;
  opened_today: boolean;
  voted: boolean;
  token?: string; // only in /host
  url?: string; // only in /host
}

interface CaseCommon {
  case_id: string;
  title: string;
  intro: string; // paragraphs split by "\n\n"
  demo: boolean;
  day: number;
  days_total: number;
  phase: Phase;
  next_unlock_at: string; // ISO time of the next day (not used in demo)
  suspects: Suspect[];
  labels: Labels;
}

export interface CreateCaseIn {
  theme?: string;
  players?: (string | { name: string; ai?: boolean })[]; // 3–6 seats; not needed with solo
  solo?: { me: string }; // you + 3 AI teammates, 3 days, demo on
  demo?: boolean;
  days?: number; // 2–5
  seed?: number; // same seed = same case (for the demo)
}

export interface Invite {
  idx: number;
  name: string;
  token: string;
  url: string;
  ai?: boolean; // an AI teammate's seat
}

export interface CreateCaseOut {
  case_id: string;
  host_token: string;
  host_url: string;
  days: number;
  invites: Invite[];
}

export interface MeOut extends CaseCommon {
  me: { idx: number; name: string; is_ai?: boolean };
  my_clues: Clue[];
  shared_clues: Clue[];
  board: BoardPost[]; // last 100, oldest first
  typing?: string[]; // AI teammates writing a reply right now (AI friends API)
  players: PlayerRow[];
  my_vote: number | null; // suspect id
}

export interface HostOut extends CaseCommon {
  players: PlayerRow[]; // with token and url
  votes_count: number;
}

export interface ChainStep {
  clue_id: string;
  day: number;
  player: number;
  from: string;
  text: string;
  eliminated: string[]; // suspects this clue cleared
  remaining: string[];
  worlds_left: number;
}

export interface RevealOut {
  case_id: string;
  title: string;
  intro: string;
  culprit: Suspect;
  truth: { suspect: string; room: string; time: string; item: string }[];
  chain: ChainStep[];
  votes: { player: string; suspect: string; correct: boolean }[];
  stats: {
    worlds_total: number;
    worlds_public: number;
    worlds_left: number;
    candidates_by_day: number[];
    seed: number;
  };
}

export interface VoteOut {
  ok: boolean;
  phase: Phase;
}

export interface Plan {
  key: "case" | "monthly";
  name: string;
  description: string;
  amount_cents: number;
  interval: string | null;
}

export interface CheckoutOut {
  url: string;
  session_id: string;
}

export interface PaymentOut {
  case_id: string;
  paid: boolean;
  plan: string | null;
  status: string | null;
}
