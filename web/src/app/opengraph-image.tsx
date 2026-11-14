import { ImageResponse } from "next/og";

// The preview card when someone pastes a Casefile link into a chat.
// Colors are the design tokens (CSS variables don't work inside images).
const C = {
  folder: "#e9d7a9",
  folderDeep: "#d6bf85",
  card: "#fdfcf7",
  ink: "#1d1b19",
  inkMuted: "#4f473d",
  stamp: "#2e4a9a",
  string: "#b4232a",
  ruleBlue: "#a9c1dc",
};

export const alt = "Casefile: crack a case with your friends, five minutes a day";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default function OpenGraphImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          background: C.folder,
          padding: 64,
          gap: 56,
          alignItems: "center",
        }}
      >
        {/* Left: the pitch */}
        <div style={{ display: "flex", flexDirection: "column", flex: 1, gap: 24 }}>
          <div style={{ fontSize: 28, fontWeight: 700, letterSpacing: 4, color: C.inkMuted }}>CASEFILE</div>
          <div style={{ fontSize: 76, fontWeight: 800, lineHeight: 1, color: C.ink, textTransform: "uppercase" }}>
            Your group chat went quiet.
          </div>
          <div style={{ fontSize: 30, color: C.ink }}>Crack a case together, five minutes a day.</div>
        </div>

        {/* Right: a clue card pinned to the folder, with a stamp */}
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            width: 380,
            background: C.card,
            borderRadius: 6,
            padding: 32,
            gap: 16,
            position: "relative",
            border: `3px solid ${C.folderDeep}`,
          }}
        >
          <div
            style={{
              position: "absolute",
              top: -14,
              left: 176,
              width: 28,
              height: 28,
              borderRadius: 999,
              background: C.string,
              border: `3px solid ${C.ink}`,
            }}
          />
          <div
            style={{
              fontSize: 20,
              fontWeight: 700,
              letterSpacing: 2,
              color: C.inkMuted,
              borderBottom: `3px solid ${C.ruleBlue}`,
              paddingBottom: 12,
            }}
          >
            EXHIBIT 1 · DAY 1
          </div>
          <div style={{ fontSize: 30, color: C.ink, lineHeight: 1.3 }}>Jordan was not seen at 7:00 PM.</div>
          <div style={{ display: "flex", fontSize: 22, color: C.inkMuted }}>Possible worlds left</div>
          <div style={{ display: "flex", fontSize: 56, fontWeight: 800, color: C.ink }}>1,728,000</div>
          <div
            style={{
              display: "flex",
              alignSelf: "flex-start",
              border: `5px solid ${C.stamp}`,
              color: C.stamp,
              fontSize: 28,
              fontWeight: 800,
              letterSpacing: 3,
              padding: "6px 14px",
              transform: "rotate(-4deg)",
            }}
          >
            NEW TODAY
          </div>
        </div>
      </div>
    ),
    size,
  );
}
