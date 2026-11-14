import type { NextConfig } from "next";

// Where the FastAPI backend lives. Locally: uvicorn on :8000; on Vercel: the api project's URL.
const API_URL = (process.env.API_URL ?? "http://localhost:8000").replace(/\/$/, "");

const nextConfig: NextConfig = {
  // Proxy /api/* to the backend so the browser stays same-origin (no CORS).
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${API_URL}/api/:path*` }];
  },
  cacheComponents: true,
  partialPrefetching: true,
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;
