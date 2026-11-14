import type { Metadata } from "next";
import { BrowserOnly } from "@/components/cf/BrowserOnly";
import { PaperSkeleton, Screen } from "@/components/cf/States";
import { Paywall } from "./Paywall";

export const metadata: Metadata = { title: "Open the next case · Casefile" };

// /paywall?case_id=…  (Stripe comes back with &checkout=success&session_id=… or &checkout=canceled)
export default function PaywallPage() {
  return (
    <BrowserOnly
      fallback={
        <Screen>
          <PaperSkeleton blocks={3} />
        </Screen>
      }
    >
      <Paywall />
    </BrowserOnly>
  );
}
