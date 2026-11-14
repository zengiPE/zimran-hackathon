import type { Metadata } from "next";
import { BrowserOnly } from "@/components/cf/BrowserOnly";
import { PaperLoader } from "@/components/cf/States";
import { HostScreen } from "./HostScreen";

export const metadata: Metadata = { title: "Host screen · Casefile" };

// Host screen for a projector: /host/{id}?token={host_token}
export default function HostPage() {
  return (
    <BrowserOnly
      fallback={
        <main className="cf-cork min-h-dvh">
          <div className="mx-auto max-w-[480px]">
            <PaperLoader />
          </div>
        </main>
      }
    >
      <HostScreen />
    </BrowserOnly>
  );
}
