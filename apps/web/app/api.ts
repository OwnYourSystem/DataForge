import type { Identity } from "./auth";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type Check = { id: string; title: string; weight: number; passed: boolean; critical: boolean };
export type Assessment = { passed: boolean; score: number; checks: Check[] };
export type Execution = {
  id: string;
  status: "queued" | "running" | "succeeded" | "failed" | "timed_out";
  logs: string;
  assessment: Assessment | null;
  compute_seconds: number | null;
};
export type Lesson = {
  id: string;
  title: string;
  instructions: string;
  editable_files: string[];
  operations: { id: string; title: string }[];
};
export type ProjectFile = { path: string; content: string };
export type Project = { id: string; best_score: number; completed_at: string | null };

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

export async function api<T>(identity: Identity, path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(await identity.headers()), ...init.headers },
  });
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      if (typeof body.detail === "string") detail = body.detail;
    } catch {
      // The body is not JSON. Keep the status text.
    }
    throw new ApiError(response.status, detail);
  }
  return response.json() as Promise<T>;
}
