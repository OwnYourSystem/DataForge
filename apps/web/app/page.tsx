"use client";

import { useEffect, useState } from "react";
import Workbench from "./workbench";

const LESSON_ID = "lab-001";
const USER_KEY = "dataforge.devUser";

export default function Home() {
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

  if (!ready) return null;

  if (!user) {
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

  return (
    <Workbench
      user={user}
      lessonId={LESSON_ID}
      onSignOut={() => {
        try {
          window.localStorage.removeItem(USER_KEY);
        } catch {
          // Nothing to remove.
        }
        setUser(null);
      }}
    />
  );
}
