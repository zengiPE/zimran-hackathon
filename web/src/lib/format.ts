// Small text helpers shared by the components.

/** First letter of a name, for avatars and polaroids. */
export const initial = (name: string) => name.trim().charAt(0).toUpperCase() || "?";

/** "a flashlight" → "flashlight" (Notebook column headers). */
export const dropArticle = (item: string) => item.replace(/^(a|an|the)\s+/i, "");

/** "9:41 AM" for today, "Sat 9:41 AM" for earlier days. */
export function postTime(iso: string, now: number): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  const time = d.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" });
  const sameDay = new Date(now).toDateString() === d.toDateString();
  if (sameDay) return time;
  return `${d.toLocaleDateString("en-US", { weekday: "short" })} ${time}`;
}

/** Time left until `iso`: "6 h 12 min", "4 min", or null when it has passed. */
export function timeLeft(iso: string, now: number): string | null {
  const ms = new Date(iso).getTime() - now;
  if (Number.isNaN(ms) || ms <= 0) return null;
  const totalMin = Math.max(1, Math.ceil(ms / 60000));
  const h = Math.floor(totalMin / 60);
  const m = totalMin % 60;
  return h > 0 ? `${h} h ${m} min` : `${m} min`;
}

/** 1728000 → "1,728,000". */
export const formatNumber = (n: number) => n.toLocaleString("en-US");

/** 1200 cents → "$12", 799 → "$7.99". */
export function formatPrice(cents: number): string {
  const dollars = cents / 100;
  return `$${Number.isInteger(dollars) ? dollars : dollars.toFixed(2)}`;
}

/** Splits the case intro into paragraphs on blank lines. */
export const paragraphs = (text: string) =>
  text
    .split(/\n\s*\n/)
    .map((p) => p.trim())
    .filter(Boolean);
