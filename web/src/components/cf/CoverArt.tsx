/**
 * The Casefile cover from design/components/Cover: a cork slab, an index card
 * laid across it, a tilted stamp and one red string between two pins.
 * Decorative only (aria-hidden); colors come from the tokens via CSS classes.
 */
export function CoverArt({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="500 -16 480 290" aria-hidden="true" focusable="false">
      <rect className="cv-cork" x="680" y="-8" width="288" height="248" rx="3" />
      <rect className="cv-card" x="520" y="64" width="264" height="168" rx="3" />
      <line className="cv-head" x1="520" y1="100" x2="784" y2="100" />
      <line className="cv-rule" x1="520" y1="124" x2="784" y2="124" />
      <line className="cv-rule" x1="520" y1="148" x2="784" y2="148" />
      <line className="cv-rule" x1="520" y1="172" x2="784" y2="172" />
      <line className="cv-rule" x1="520" y1="196" x2="784" y2="196" />
      <line className="cv-rule" x1="520" y1="220" x2="784" y2="220" />
      <rect className="cv-stamp" x="808" y="160" width="96" height="96" rx="3" transform="rotate(-4 856 208)" />
      <path className="cv-string" d="M652 64 Q 766 104 880 40" />
      <circle className="cv-pin" cx="652" cy="64" r="8" />
      <circle className="cv-pin" cx="880" cy="40" r="8" />
    </svg>
  );
}
