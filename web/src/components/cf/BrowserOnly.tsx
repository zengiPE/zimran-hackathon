"use client";

import { Suspense, use, type ReactNode } from "react";
import { browser } from "react-dom";

function Gate({ children }: { children: ReactNode }) {
  // Suspends during prerender, so everything below renders only in the browser
  // and may read localStorage, the clock and the URL right away.
  use(browser("Game screens read the link token and localStorage."));
  return children;
}

/** Renders `children` only in the browser; `fallback` is what the server sends. */
export function BrowserOnly({ children, fallback }: { children: ReactNode; fallback: ReactNode }) {
  return (
    <Suspense fallback={fallback}>
      <Gate>{children}</Gate>
    </Suspense>
  );
}
