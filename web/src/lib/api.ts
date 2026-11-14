// One function per API endpoint. The browser calls relative /api/... paths,
// and next.config.ts proxies them to the FastAPI backend.

import type {
  BoardPost,
  CheckoutOut,
  Clue,
  CreateCaseIn,
  CreateCaseOut,
  HostOut,
  MeOut,
  NextCaseOut,
  PaymentOut,
  Plan,
  RevealOut,
  Theme,
  VoteOut,
} from "./types";

/** An error from the API: the HTTP status plus the `detail` text. */
export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

/** Turns the `{detail}` body into one readable line. 422 sends a list. */
function readDetail(body: unknown): string {
  if (body && typeof body === "object" && "detail" in body) {
    const detail = (body as { detail: unknown }).detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail) && detail.length > 0) {
      const first = detail[0] as { msg?: string };
      if (first?.msg) return first.msg;
    }
  }
  return "Something went wrong. Try again.";
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(path, {
      ...init,
      headers: { "content-type": "application/json", ...init?.headers },
      cache: "no-store",
    });
  } catch {
    throw new ApiError(0, "No connection. Check your internet and try again.");
  }
  const body = await res.json().catch(() => null);
  if (!res.ok) throw new ApiError(res.status, readDetail(body));
  return body as T;
}

const post = <T>(path: string, data: unknown) =>
  request<T>(path, { method: "POST", body: JSON.stringify(data) });

const q = encodeURIComponent;

// ---- Cases ----
export const getThemes = () => request<Theme[]>("/api/themes");
export const createCase = (data: CreateCaseIn) => post<CreateCaseOut>("/api/cases", data);
export const getMe = (id: string, token: string) =>
  request<MeOut>(`/api/cases/${q(id)}/me?token=${q(token)}`);
export const getHost = (id: string, token: string) =>
  request<HostOut>(`/api/cases/${q(id)}/host?token=${q(token)}`);
/** A board post: text, an attached clue of yours (factId), or both. */
export const postBoard = (id: string, token: string, text: string, factId?: string) =>
  post<BoardPost>(`/api/cases/${q(id)}/board`, factId ? { token, text, fact_id: factId } : { token, text });
export const castVote = (id: string, token: string, suspect: number) =>
  post<VoteOut>(`/api/cases/${q(id)}/vote`, { token, suspect });
export const advanceDay = (id: string, hostToken: string) =>
  post<HostOut>(`/api/cases/${q(id)}/advance`, { host_token: hostToken });
export const askHint = (id: string, hostToken: string) =>
  post<{ shared: Clue }>(`/api/cases/${q(id)}/hint`, { host_token: hostToken });
export const getReveal = (id: string) => request<RevealOut>(`/api/cases/${q(id)}/reveal`);
/**
 * After the reveal: open the crew's next case (same seats, new mystery).
 * Pass a player token or the host token. 402 = someone has to pay first.
 */
export const openNextCase = (id: string, auth: { token: string } | { host_token: string }) =>
  post<NextCaseOut>(`/api/cases/${q(id)}/next`, auth);

// ---- Payments ----
export const getPlans = () => request<Plan[]>("/api/plans");
export const startCheckout = (caseId: string, plan: Plan["key"]) =>
  post<CheckoutOut>("/api/checkout", { case_id: caseId, plan });
export const getCheckout = (sessionId: string) =>
  request<PaymentOut>(`/api/checkout/${q(sessionId)}`);
export const getPayment = (caseId: string) =>
  request<PaymentOut>(`/api/cases/${q(caseId)}/payment`);

/**
 * The message a player sees for an error. 403 and 404 get fixed copy,
 * 503 is for payments, everything else shows the API's own text.
 */
export function errorText(err: unknown): string {
  if (err instanceof ApiError) {
    if (err.status === 403) return "This link doesn't work. Ask the host for a new one.";
    if (err.status === 404) return "We couldn't find this case.";
    if (err.status === 503) return "Payments are off in this demo.";
    return err.message;
  }
  return "Something went wrong. Try again.";
}

export const isStatus = (err: unknown, status: number) =>
  err instanceof ApiError && err.status === status;
