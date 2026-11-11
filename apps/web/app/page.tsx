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
  const [state, setState] = useState<"idle" | "sending" | "sent">("idle");
  const [error, setError] = useState<string | null>(null);
  const valid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);

  const send = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!valid || state === "sending") return;
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
    setState("sent");
  };

  if (state === "sent") {
    return (
      <main className="signin">
        <div>
          <h1>Check your email</h1>
          <p>
            We sent a sign-in link to <strong>{email}</strong>. Open the link on this device to
            start the lab.
          </p>
          <button onClick={() => setState("idle")}>Use a different email</button>
        </div>
      </main>
    );
  }

  return (
    <main className="signin">
      <form onSubmit={send}>
        <h1>DataForge</h1>
        <p>Type your email. We send you a link to sign in. No password.</p>
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
        <button type="submit" className="primary" disabled={!valid || state === "sending"}>
          {state === "sending" ? "Sending…" : "Send sign-in link"}
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
