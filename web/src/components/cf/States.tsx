import type { ReactNode } from "react";

/** A blank index card with a line of text: shown while something loads. */
export function PaperLoader({ label = "Opening the case file…" }: { label?: string }) {
  return (
    <div className="cf-clue cf-clue--card" role="status" aria-live="polite">
      <div className="cf-clue__meta">
        <span className="cf-label">Case file</span>
      </div>
      <p className="cf-clue__text">
        {label}
        <br />
        <br />
      </p>
    </div>
  );
}

/** Grey paper shapes where the screen will be. */
export function PaperSkeleton({ blocks = 3 }: { blocks?: number }) {
  return (
    <div className="cf-stack" aria-hidden="true">
      {Array.from({ length: blocks }, (_, i) => (
        <div key={i} className="cf-skeleton" />
      ))}
    </div>
  );
}

/** An error in ink on paper (never red). */
export function ErrorNote({ children, action }: { children: ReactNode; action?: ReactNode }) {
  return (
    <div className="cf-stack" role="alert">
      <p className="cf-error">{children}</p>
      {action}
    </div>
  );
}

/** One centered column, 480px max: the frame of every game screen. */
export function Screen({ children }: { children: ReactNode }) {
  return <main className="cf-desk cf-screen min-h-dvh">{children}</main>;
}
