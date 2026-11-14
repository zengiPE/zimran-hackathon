"use client";

import clsx from "clsx";
import { initial, postTime } from "@/lib/format";
import type { BoardPost as Post } from "@/lib/types";
import { useNow } from "@/lib/useNow";

/** One post on the theory board. Your own posts sit on folder-deep as "You". */
export function BoardPost({ post, mine }: { post: Post; mine: boolean }) {
  const now = useNow();
  const ai = Boolean(post.is_ai);
  return (
    <article className={clsx("cf-post", mine && "cf-post--mine")}>
      <span className={clsx("cf-avatar", ai && "cf-avatar--ai")} aria-hidden="true">
        {initial(post.author)}
      </span>
      <div className="cf-post__body">
        <p className="cf-post__head">
          <span className="cf-post__name">{mine ? "You" : post.author}</span>
          {ai && <span className="cf-tag">AI teammate</span>}
          {now !== null && <span>{postTime(post.ts, now)}</span>}
        </p>
        {post.text && <p className="cf-post__text">{post.text}</p>}
        {post.fact && (
          <div className="cf-attach">
            <span className="cf-label">
              {post.fact.format ?? "Clue"} · {mine ? "your" : `${post.fact.from}'s`} clue
            </span>
            <p className="cf-fact__text">{post.fact.text}</p>
          </div>
        )}
      </div>
    </article>
  );
}

/** "Nora is typing…", "Nora and Felix are typing…", "Nora, Felix and Kai are typing…". */
function typingLine(names: string[]): string {
  if (names.length === 1) return `${names[0]} is typing…`;
  const last = names[names.length - 1];
  return `${names.slice(0, -1).join(", ")} and ${last} are typing…`;
}

interface BoardProps {
  posts: Post[]; // oldest first
  myName: string;
  typing?: string[]; // AI teammates writing right now
  children?: React.ReactNode; // e.g. the Composer when it isn't pinned
}

/** The group's theory board: heading, posts or the empty state, who is typing. */
export function Board({ posts, myName, typing = [], children }: BoardProps) {
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
      {posts.length === 0 && typing.length === 0 ? (
        <p className="cf-caption">No theories yet. Share your clue to get the group talking.</p>
      ) : (
        posts.map((p, i) => <BoardPost key={p.ts + p.author + i} post={p} mine={p.author === myName} />)
      )}
      <p className="cf-caption" aria-live="polite">
        {typing.length > 0 ? typingLine(typing) : ""}
      </p>
      {children}
    </section>
  );
}
