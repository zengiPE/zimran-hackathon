"use client";

import { useState } from "react";
import { Button } from "./Button";

const CARD = "4242 4242 4242 4242";

/** Stripe test-mode card, shown next to the pay button so anyone can finish checkout. */
export function TestCard() {
  const [copied, setCopied] = useState(false);

  async function copy() {
    try {
      await navigator.clipboard.writeText(CARD.replace(/ /g, ""));
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Clipboard blocked: the number is on screen anyway.
    }
  }

  return (
    <div className="cf-testcard" role="note" aria-label="Stripe test card">
      <span className="cf-label">Stripe test mode · no real money</span>
      <div className="cf-testcard__row">
        <span className="cf-testcard__num">{CARD}</span>
        <Button variant="quiet" onClick={copy} aria-label="Copy the test card number">
          {copied ? "Copied" : "Copy"}
        </Button>
      </div>
      <p className="cf-caption">Any future date, any CVC, any ZIP.</p>
    </div>
  );
}
