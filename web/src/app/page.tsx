"use client";

import { useEffect, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Health = { status: string; service: string };

export default function Home() {
  const [health, setHealth] = useState<Health | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${API_URL}/api/health`)
      .then((r) => r.json())
      .then(setHealth)
      .catch((e) => setError(String(e)));
  }, []);

  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-4 p-8">
      <h1 className="text-3xl font-semibold">Zimran Hackathon</h1>
      <p className="text-zinc-500">
        API:{" "}
        {health ? (
          <span className="text-green-600">{health.status}</span>
        ) : error ? (
          <span className="text-red-600">недоступен</span>
        ) : (
          "проверяю…"
        )}
      </p>
    </main>
  );
}
