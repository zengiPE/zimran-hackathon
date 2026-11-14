import type { Metadata } from "next";
import { BrowserOnly } from "@/components/cf/BrowserOnly";
import { PaperSkeleton, Screen } from "@/components/cf/States";
import { PlayerScreen } from "./PlayerScreen";

export const metadata: Metadata = { title: "Your case · Casefile" };

// Player screen: /play/{id}?token={player token}
export default function PlayPage() {
  return (
    <BrowserOnly
      fallback={
        <Screen>
          <PaperSkeleton blocks={4} />
        </Screen>
      }
    >
      <PlayerScreen />
    </BrowserOnly>
  );
}
