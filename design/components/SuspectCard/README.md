# SuspectCard

A suspect as a pinned polaroid.

**Provide** (a `Suspect` from the API): `name`, `role`, the initial of the name, a tilt between -4° and 4° (set `--tilt`), and a verdict: none, `is-cleared` or `is-guilty`. Put the verdict stamps in the caption; the state class shows the right one.

- A case has five suspects. In a grid: three per row on phones (3 + 2, centered), five in a row from 640px. `cf-reveal__suspects` does this.
- Use `cf-suspect--fluid` inside grids. Roles are long ("The doctor on call all weekend") and wrap.
- Cleared: the photo turns `ink-muted`, the name is struck through, a muted "Cleared" Stamp replaces the role.
- Guilty: a red "Guilty" Stamp replaces the role, the polaroid lifts (`shadow-lifted`) and its pin grows.
- For voting, use the same card as a radio button: see VotePicker.
- Never draw faces or use photos. The initial in the display face is the portrait.
