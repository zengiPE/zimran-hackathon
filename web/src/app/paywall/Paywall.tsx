"use client";

import { useSearchParams } from "next/navigation";
import { useState, type FormEvent } from "react";
import useSWR from "swr";
import { Button, ButtonLink } from "@/components/cf/Button";
import { Stamp } from "@/components/cf/Stamp";
import { ErrorNote, PaperLoader, PaperSkeleton, Screen } from "@/components/cf/States";
import { errorText, getCheckout, getPayment, getPlans, isStatus, startCheckout } from "@/lib/api";
import { formatPrice } from "@/lib/format";
import type { Plan } from "@/lib/types";


export function Paywall() {
  const params = useSearchParams();
  const caseId = params.get("case_id");
  const checkout = params.get("checkout"); // "success" | "canceled" | null
  const sessionId = params.get("session_id");

  const plans = useSWR("plans", getPlans, { revalidateOnFocus: false });
  // Already paid? (e.g. the page is opened again later)
  const payment = useSWR(caseId ? ["payment", caseId] : null, ([, id]: [string, string]) => getPayment(id), {
    revalidateOnFocus: false,
  });
  // Back from Stripe: confirm the session (works even if the webhook is late).
  // Keep asking every 3 s until it is paid.
  const confirm = useSWR(
    checkout === "success" && sessionId ? ["checkout", sessionId] : null,
    ([, sid]: [string, string]) => getCheckout(sid),
    {
      revalidateOnFocus: false,
      shouldRetryOnError: false,
      refreshInterval: (data) => (data?.paid ? 0 : 3000),
    },
  );

  const [plan, setPlan] = useState<Plan["key"]>("case");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [paymentsOff, setPaymentsOff] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    if (!caseId || busy) return;
    setBusy(true);
    setError(null);
    try {
      const { url } = await startCheckout(caseId, plan);
      window.location.href = url; // off to Stripe Checkout
    } catch (err) {
      setBusy(false);
      if (isStatus(err, 503)) setPaymentsOff(true);
      else setError(errorText(err));
    }
  }

  // ---- No case in the link ----
  if (!caseId) {
    return (
      <Screen>
        <ErrorNote action={<ButtonLink href="/">Start a case</ButtonLink>}>We couldn&apos;t find this case.</ErrorNote>
      </Screen>
    );
  }

  const paid = confirm.data?.paid || payment.data?.paid;
  const confirmOff = isStatus(confirm.error, 503);

  // ---- Paid ----
  if (paid) {
    return (
      <Screen>
        <header className="cf-stack">
          <span className="cf-label">Case file · Next case</span>
          <h1 className="cf-hero">You&apos;re in.</h1>
        </header>
        <div className="cf-verdict">
          <Stamp big>Paid</Stamp>
          <p className="m-0">Thanks! Your group&apos;s next case is unlocked. Start it whenever everyone is ready.</p>
          <ButtonLink variant="primary" href="/#create">
            Start the next case
          </ButtonLink>
        </div>
      </Screen>
    );
  }

  // ---- Back from Stripe, payment not confirmed yet ----
  if (checkout === "success" && !confirm.error && !confirmOff) {
    return (
      <Screen>
        <PaperLoader label="Confirming your payment…" />
      </Screen>
    );
  }

  return (
    <Screen>
      <header className="cf-stack">
        <span className="cf-label">Case file · Next case</span>
        <h1 className="cf-hero">Open the next case</h1>
        <p className="cf-lead">The first case was on us. Keep the group chat busy with a new one.</p>
      </header>

      {checkout === "canceled" && (
        <p className="cf-error" role="status">
          Checkout canceled. Nothing was charged. Pick a plan when you&apos;re ready.
        </p>
      )}
      {checkout === "success" && confirm.error && !confirmOff && (
        <p className="cf-error" role="alert">
          {errorText(confirm.error)}
        </p>
      )}

      <form className="cf-stack" onSubmit={submit}>
        <fieldset className="cf-fieldset">
          <legend className="cf-label">Pick a plan</legend>
          {plans.error && <p className="cf-error">{errorText(plans.error)}</p>}
          {!plans.data && !plans.error && <PaperSkeleton blocks={2} />}
          {plans.data?.map((p) => (
            <label key={p.key} className="cf-choice">
              <input
                className="cf-sr"
                type="radio"
                name="plan"
                value={p.key}
                checked={plan === p.key}
                onChange={() => setPlan(p.key)}
              />
              <span className="cf-choice__row">
                <span className="cf-choice__title">{p.name}</span>
                <span className="cf-choice__price">
                  {formatPrice(p.amount_cents)}
                  {p.interval && <span className="cf-caption"> / {p.interval}</span>}
                </span>
              </span>
              <span className="cf-caption">{p.description}</span>
            </label>
          ))}
        </fieldset>

        {paymentsOff || confirmOff ? (
          <ErrorNote>Payments are off in this demo.</ErrorNote>
        ) : (
          <>
            {error && (
              <p className="cf-error" role="alert">
                {error}
              </p>
            )}
            <Button variant="primary" block type="submit" disabled={busy || !plans.data}>
              {busy ? "Opening checkout…" : "Open the next case"}
            </Button>
            <p className="cf-caption">Secure checkout by Stripe. Test mode: no real card is charged.</p>
          </>
        )}
      </form>
    </Screen>
  );
}
