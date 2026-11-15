"use client";

import { useEffect, useMemo, useState } from "react";
import type { SupabaseClient } from "@supabase/supabase-js";
import { devIdentity, getSupabase, supabaseIdentity, type Identity } from "./auth";
import Workbench from "./workbench";

const LESSON_ID = "lab-001";
const USER_KEY = "dataforge.devUser";

export default function Home() {
  // The sign-in mode comes from the page config, which exists in the browser only.
  const [client, setClient] = useState<SupabaseClient | null | undefined>(undefined);
  useEffect(() => setClient(getSupabase()), []);
  if (client === undefined) return null;
  return client ? <SupabaseHome client={client} /> : <DevHome />;
}

function SupabaseHome({ client }: { client: SupabaseClient }) {
  const [email, setEmail] = useState<string | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    // Fires one time at the start with the stored session, then on each change.
    const { data } = client.auth.onAuthStateChange((_event, session) => {
      setEmail(session?.user.email ?? (session ? "Signed in" : null));
      setReady(true);
    });
    return () => data.subscription.unsubscribe();
  }, [client]);

  const identity = useMemo<Identity | null>(
    () => (email ? supabaseIdentity(client, email) : null),
    [client, email],
  );

  if (!ready) return null;
  if (!identity) return <EmailSignIn client={client} />;
  return <Workbench identity={identity} lessonId={LESSON_ID} />;
}

function EmailSignIn({ client }: { client: SupabaseClient }) {
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [state, setState] = useState<"idle" | "sending" | "sent" | "checking">("idle");
  const [error, setError] = useState<string | null>(null);
  const validEmail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  const validCode = /^[0-9]{6,8}$/.test(code);

  const send = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!validEmail || state === "sending") return;
    setState("sending");
    setError(null);
    const { error: failure } = await client.auth.signInWithOtp({
      email,
      options: { emailRedirectTo: window.location.origin },
    });
    if (failure) {
      setError(
        failure.status === 429
          ? "Too many sign-in emails. Wait some minutes, then try again."
          : "The sign-in email was not sent. Try again.",
      );
      setState("idle");
      return;
    }
    setCode("");
    setState("sent");
  };

  const verify = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!validCode || state === "checking") return;
    setState("checking");
    setError(null);
    const { error: failure } = await client.auth.verifyOtp({ email, token: code, type: "email" });
    if (failure) {
      setError("The code is not correct, or it is too old. Check the code or get a new one.");
      setState("sent");
    }
    // On success, the session change shows the workbench.
  };

  if (state === "sent" || state === "checking") {
    return (
      <main className="signin">
        <form onSubmit={verify}>
          <h1>Type your code</h1>
          <p>
            We sent a sign-in code to <strong>{email}</strong>. Type the code here. You can read
            the email on a different device.
          </p>
          {error ? (
            <p className="error" role="alert">
              {error}
            </p>
          ) : null}
          <label htmlFor="code">Sign-in code</label>
          <input
            id="code"
            className="code-input"
            value={code}
            onChange={(event) => setCode(event.target.value.replace(/[^0-9]/g, "").slice(0, 8))}
            inputMode="numeric"
            autoComplete="one-time-code"
            placeholder="123456"
            autoFocus
          />
          <button type="submit" className="primary" disabled={!validCode || state === "checking"}>
            {state === "checking" ? "Checking…" : "Sign in"}
          </button>
          <button
            type="button"
            onClick={() => {
              setError(null);
              setState("idle");
            }}
          >
            Use a different email
          </button>
        </form>
      </main>
    );
  }

  return (
    <main className="signin">
      <form onSubmit={send}>
        <h1>DataForge</h1>
        <p>Type your email. We send you a code to sign in. No password.</p>
        {error ? (
          <p className="error" role="alert">
            {error}
          </p>
        ) : null}
        <label htmlFor="email">Email</label>
        <input
          id="email"
          type="email"
          value={email}
          onChange={(event) => setEmail(event.target.value.trim())}
          placeholder="you@example.com"
          autoFocus
          autoComplete="email"
        />
        <button type="submit" className="primary" disabled={!validEmail || state === "sending"}>
          {state === "sending" ? "Sending…" : "Send sign-in code"}
        </button>
      </form>
    </main>
  );
}

function DevHome() {
  const [user, setUser] = useState<string | null>(null);
  const [ready, setReady] = useState(false);
  const [name, setName] = useState("");

  useEffect(() => {
    try {
      setUser(window.localStorage.getItem(USER_KEY));
    } catch {
      // Storage is not available. The learner signs in again.
    }
    setReady(true);
  }, []);

  const identity = useMemo<Identity | null>(
    () =>
      user
        ? devIdentity(user, () => {
            try {
              window.localStorage.removeItem(USER_KEY);
            } catch {
              // Nothing to remove.
            }
            setUser(null);
          })
        : null,
    [user],
  );

  if (!ready) return null;
  if (identity) return <Workbench identity={identity} lessonId={LESSON_ID} />;

  const valid = /^[A-Za-z0-9_.@-]{1,64}$/.test(name);
  return (
    <main className="signin">
      <form
        onSubmit={(event) => {
          event.preventDefault();
          if (!valid) return;
          try {
            window.localStorage.setItem(USER_KEY, name);
          } catch {
            // Continue without storage.
          }
          setUser(name);
        }}
      >
        <h1>DataForge</h1>
        <p>Development sign-in. Type a name to start the lab.</p>
        <label htmlFor="name">Name</label>
        <input
          id="name"
          value={name}
          onChange={(event) => setName(event.target.value.trim())}
          placeholder="alice"
          autoFocus
          autoComplete="off"
        />
        <button type="submit" className="primary" disabled={!valid}>
          Start
        </button>
      </form>
    </main>
  );
}
