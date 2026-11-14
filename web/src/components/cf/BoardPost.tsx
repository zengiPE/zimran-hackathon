"use client";

import clsx from "clsx";
import { initial, postTime } from "@/lib/format";
import type { BoardPost as Post } from "@/lib/types";
import { useNow } from "@/lib/useNow";

/** One post on the theory board. Your own posts sit on folder-deep as "You". */
export function BoardPost({ post, mine }: { post: Post; mine: boolean }) {
  const now = useNow();
  return (
    <article className={clsx("cf-post", mine && "cf-post--mine")}>
      <span className="cf-avatar" aria-hidden="true">
        {initial(post.author)}
      </span>
      <div className="cf-post__body">
        <p className="cf-post__head">
          <span className="cf-post__name">{mine ? "You" : post.author}</span>
          {now !== null && <span>{postTime(post.ts, now)}</span>}
        </p>
        <p className="cf-post__text">{post.text}</p>
      </div>
    </article>
  );
}

interface BoardProps {
  posts: Post[]; // oldest first
  myName: string;
  children?: React.ReactNode; // e.g. the Composer when it isn't pinned
}

/** The group's theory board: heading, posts or the empty state. */
export function Board({ posts, myName, children }: BoardProps) {
  const now = useNow();
  const today =
    now === null ? null : posts.filter((p) => new Date(p.ts).toDateString() === new Date(now).toDateString()).length;

  return (
    <section className="cf-board" aria-labelledby="board-title">
      <div className="cf-board__head">
        <h2 className="cf-heading" id="board-title">
          The board
        </h2>
        {today !== null && today > 0 && (
          <span className="cf-caption">
            {today} {today === 1 ? "post" : "posts"} today
          </span>
        )}
      </div>
      {posts.length === 0 ? (
        <p className="cf-caption">No theories yet. Share your clue to get the group talking.</p>
      ) : (
        posts.map((p, i) => <BoardPost key={p.ts + p.author + i} post={p} mine={p.author === myName} />)
      )}
      {children}
    </section>
  );
}
