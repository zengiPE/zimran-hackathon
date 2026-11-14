"use client";

import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";
import useSWR from "swr";
import { Button } from "@/components/cf/Button";
import { ErrorNote, PaperLoader } from "@/components/cf/States";
import { createCase, errorText, getThemes, isStatus } from "@/lib/api";
import { localPath, saveCase } from "@/lib/storage";

const MIN_PLAYERS = 3;
const MAX_PLAYERS = 6;

/** The Create case form: theme, 3–6 names, demo mode. */
export function CreateCase() {
  const router = useRouter();
  const themes = useSWR("themes", getThemes, { revalidateOnFocus: false });
  const [theme, setTheme] = useState("lake-house");
  const [names, setNames] = useState<string[]>(["", "", "", ""]);
  const [demo, setDemo] = useState(true);
  const [busy, setBusy] = useState(false);
  const [namesError, setNamesError] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  const setName = (i: number, value: string) =>
    setNames((prev) => prev.map((n, j) => (j === i ? value : n)));
  const addName = () => setNames((prev) => [...prev, ""]);
  const removeName = (i: number) => setNames((prev) => prev.filter((_, j) => j !== i));

  async function submit(e: FormEvent) {
    e.preventDefault();
    setNamesError(null);
    setFormError(null);

    const players = names.map((n) => n.trim()).filter(Boolean);
    if (players.length < MIN_PLAYERS) {
      setNamesError(`Add at least ${MIN_PLAYERS} names. You can't solve this one alone.`);
      return;
    }
    const lower = players.map((n) => n.toLowerCase());
    if (new Set(lower).size !== lower.length) {
      setNamesError("Two friends have the same name. Add an initial to tell them apart.");
      return;
    }

    setBusy(true);
    try {
      const out = await createCase({ theme, players, demo });
      saveCase({ case_id: out.case_id, host_token: out.host_token, invites: out.invites, demo });
      router.push(localPath(out.host_url));
    } catch (err) {
      setBusy(false);
      // 422 is about the form (names or theme): show it under the names.
      if (isStatus(err, 422)) setNamesError(errorText(err));
      else setFormError(errorText(err));
    }
  }

  if (busy) {
    return (
      <section id="create" className="cf-stack">
        <h2 className="cf-heading">Create case</h2>
        <PaperLoader label="Writing your case file…" />
      </section>
    );
  }

  return (
    <form id="create" className="cf-stack scroll-mt-6" onSubmit={submit} noValidate>
      <h2 className="cf-heading">Create case</h2>

      <fieldset className="cf-fieldset">
        <legend className="cf-label">Pick a story</legend>
        {themes.error && <p className="cf-error">{errorText(themes.error)}</p>}
        {!themes.data && !themes.error && <div className="cf-skeleton" aria-hidden="true" />}
        {themes.data?.map((t) => (
          <label key={t.id} className="cf-choice">
            <input
              className="cf-sr"
              type="radio"
              name="theme"
              value={t.id}
              checked={theme === t.id}
              onChange={() => setTheme(t.id)}
            />
            <span className="cf-choice__title">{t.title}</span>
            <span className="cf-caption">{t.tagline}</span>
          </label>
        ))}
      </fieldset>

      <fieldset className="cf-fieldset" aria-describedby={namesError ? "names-error" : undefined}>
        <legend className="cf-label">Your friends (3 to 6)</legend>
        {names.map((n, i) => (
          <div key={i} className="flex gap-2">
            <label className="cf-sr" htmlFor={`name-${i}`}>
              Friend {i + 1}
            </label>
            <input
              id={`name-${i}`}
              className="cf-input flex-1"
              type="text"
              placeholder={`Friend ${i + 1}`}
              value={n}
              maxLength={24}
              autoComplete="off"
              onChange={(e) => setName(i, e.target.value)}
            />
            {names.length > MIN_PLAYERS && (
              <Button variant="quiet" onClick={() => removeName(i)} aria-label={`Remove friend ${i + 1}`}>
                Remove
              </Button>
            )}
          </div>
        ))}
        {names.length < MAX_PLAYERS && (
          <Button variant="quiet" className="justify-self-start" onClick={addName}>
            Add a friend
          </Button>
        )}
        {namesError && (
          <p className="cf-error" id="names-error" role="alert">
            {namesError}
          </p>
        )}
      </fieldset>

      <label className="cf-toggle">
        <input type="checkbox" checked={demo} onChange={(e) => setDemo(e.target.checked)} />
        <span>
          <span className="cf-toggle__title">Demo mode</span>
          <span className="cf-caption block">
            The host moves the days with a button instead of waiting 24 hours.
          </span>
        </span>
      </label>

      {formError && <ErrorNote>{formError}</ErrorNote>}

      <Button variant="primary" block type="submit">
        Create case
      </Button>
    </form>
  );
}
