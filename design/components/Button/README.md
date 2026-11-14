# Button

The control for every action: a paper key with a hard ink shadow that presses down 2px on tap.

**Provide:** a verb-first label in sentence case ("Start a case", "Share this clue", "Next day"), a `type`, and `disabled` when the action can't run yet.

**Variants**

- `cf-btn--primary` (`stamp` fill, `on-stamp` text): the one main action on a screen.
- `cf-btn--secondary` (`card` fill): every other action.
- `cf-btn--quiet` (underlined `stamp` text): small actions such as "Copy link".
- `cf-btn--block`: full width, for the main action at the bottom of a phone screen.
- `cf-btn--sm` (36px): only in the Reveal header and the Host screen.

**Rules**

- One primary button per screen.
- Keep 48px height everywhere except `cf-btn--sm`.
- A disabled button gets a caption next to it that says when it will work ("Voting opens on Day 4").
- An icon, if any, sits left of the label.
