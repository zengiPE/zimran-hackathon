# BoardPost

The group's theory board: posts with author, time and text, followed by the composer.

**Provide** (`board` from `/me`): `{author, text, ts}` in time order, oldest at the top, up to 100.

- Your own posts (`author === me.name`) use `cf-post--mine`: `folder-deep`, no shadow, author shown as "You". Everyone else's sit on `card`.
- Avatar: the author's initial. Time: `ts` as "9:41 AM" today, "Sat 9:41 AM" earlier.
- React key: `ts + author + index` (posts have no id).
- Composer: one text input (1–280 characters, with a "12 / 280" counter) and "Post". After posting, show the post at once without waiting for the next poll. On 409 or 403, show the error under the input.
- New posts fade in over 160ms.
- Empty state: "No theories yet. Share your clue to get the group talking."

**Later, when AI teammates land in the API:** an AI author gets a dashed avatar (`cf-avatar--ai`) and an "AI teammate" tag (`cf-tag`); a post that shares a clue shows it as a `cf-attach` block with the exhibit and the fact; "Priya is typing…" as a caption under the last post.
