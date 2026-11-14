import type { Metadata } from "next";
import { BrowserOnly } from "@/components/cf/BrowserOnly";
import { PaperLoader, Screen } from "@/components/cf/States";
import { Kit } from "./Kit";

export const metadata: Metadata = { title: "Component kit · Casefile" };

// Visual test: every Casefile component in every state, on real demo data.
export default function KitPage() {
  return (
    <BrowserOnly
      fallback={
        <Screen>
          <PaperLoader />
        </Screen>
      }
    >
      <Kit />
    </BrowserOnly>
  );
}
