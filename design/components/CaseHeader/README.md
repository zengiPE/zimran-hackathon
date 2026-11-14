# CaseHeader

The top of every player screen: a folder tab, the day and player count, the case title and the day track.

**Provide** (from `GET /api/cases/{id}/me`): `title`, `day`, `days_total`, `phase`, `next_unlock_at`, `demo`, and from `players` how many opened today's clue.

- The track has `days_total + 1` segments: one per day, then "Vote". Set `--days` on `.cf-days` to that number.
- Segment states: done (`ink` fill), today (`stamp` fill, `aria-current="step"`), upcoming (outline). "Vote" is dashed until `phase` is `vote`, then it becomes today.
- The countdown counts to `next_unlock_at`: "Next clue in 6 h 12 min". In a demo case it reads "Demo: the host moves the days". In the vote phase: "Voting is open".
- Keep the title to two lines. Shorten copy rather than shrink the type.
- The case `intro` does not go here: it goes in a "Case brief" drawer right under the header.
