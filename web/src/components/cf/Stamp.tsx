import clsx from "clsx";
import type { ReactNode } from "react";

interface Props {
  children: ReactNode; // one or two words, never a sentence
  tone?: "stamp" | "muted" | "ink" | "red"; // red only for "Guilty"
  straight?: boolean; // no tilt, for stamps inside a line of text
  big?: boolean; // the final "Solved"
  thunk?: boolean; // lands with a 180ms thunk (Reveal)
  className?: string;
}

/** A rubber-stamp label that shows a state in one or two words. */
export function Stamp({ children, tone = "stamp", straight, big, thunk, className }: Props) {
  return (
    <span
      className={clsx(
        "cf-stamp",
        tone !== "stamp" && `cf-stamp--${tone}`,
        straight && "cf-stamp--straight",
        big && "cf-stamp--big",
        thunk && "cf-stamp--thunk",
        className,
      )}
    >
      {children}
    </span>
  );
}
