// The vote question and verdict line per case. The API sends only the title,
// so we match on it. Unknown cases fall back to a neutral wording.

const COPY: Record<string, { deed: string; question: string }> = {
  "The Lake House Weekend": {
    deed: "broke the record player",
    question: "Who broke the record player?",
  },
  "The Office Holiday Party": {
    deed: "crushed the gingerbread headquarters",
    question: "Who crushed the gingerbread headquarters?",
  },
};

export function caseCopy(title: string) {
  return COPY[title] ?? { deed: "did it", question: "Who did it?" };
}
