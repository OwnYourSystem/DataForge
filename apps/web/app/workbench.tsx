"use client";

import Editor, { loader } from "@monaco-editor/react";
import { useCallback, useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { api, ApiError, type Execution, type Lesson, type Project, type ProjectFile } from "./api";
import type { Identity } from "./auth";

type SaveState = "saved" | "saving" | "unsaved" | "error";

const SAVE_LABEL: Record<SaveState, string> = {
  saved: "Saved",
  saving: "Saving…",
  unsaved: "Not saved",
  error: "Not saved",
};

const STATUS_LABEL: Record<Execution["status"], string> = {
  queued: "In the queue…",
  running: "Running…",
  succeeded: "Run complete",
  failed: "Run failed",
  timed_out: "Stopped at the time limit",
};

export default function Workbench(props: { identity: Identity; lessonId: string }) {
  const { identity, lessonId } = props;
  const user = identity;
  const onSignOut = () => void identity.signOut();
  const [lesson, setLesson] = useState<Lesson | null>(null);
  const [project, setProject] = useState<Project | null>(null);
  const [file, setFile] = useState<ProjectFile | null>(null);
  const [saveState, setSaveState] = useState<SaveState>("saved");
  const [execution, setExecution] = useState<Execution | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [editorReady, setEditorReady] = useState(false);
  const [dark, setDark] = useState(false);
  const content = useRef("");
  const saveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Monaco comes from the app bundle, not from a CDN.
  useEffect(() => {
    let active = true;
    (window as Window & { MonacoEnvironment?: unknown }).MonacoEnvironment = {
      getWorker: () =>
        new Worker(new URL("monaco-editor/editor/editor.worker.js", import.meta.url), {
          type: "module",
        }),
    };
    import("monaco-editor").then((monaco) => {
      loader.config({ monaco });
      if (active) setEditorReady(true);
    });
    const query = window.matchMedia("(prefers-color-scheme: dark)");
    setDark(query.matches);
    const listener = (event: MediaQueryListEvent) => setDark(event.matches);
    query.addEventListener("change", listener);
    return () => {
      active = false;
      query.removeEventListener("change", listener);
    };
  }, []);

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const loadedLesson = await api<Lesson>(user, `/v1/lessons/${lessonId}`);
        const created = await api<{ id: string }>(user, "/v1/projects", {
          method: "POST",
          body: JSON.stringify({ lesson_id: lessonId }),
        });
        const [loadedProject, files] = await Promise.all([
          api<Project>(user, `/v1/projects/${created.id}`),
          api<ProjectFile[]>(user, `/v1/projects/${created.id}/files`),
        ]);
        if (!active) return;
        content.current = files[0].content;
        setLesson(loadedLesson);
        setProject(loadedProject);
        setFile(files[0]);
      } catch (cause) {
        if (active) setError(describe(cause, "The lab did not load."));
      }
    })();
    return () => {
      active = false;
    };
  }, [user, lessonId]);

  const save = useCallback(async (): Promise<boolean> => {
    if (!project || !file) return false;
    if (saveTimer.current) clearTimeout(saveTimer.current);
    setSaveState("saving");
    try {
      await api(user, `/v1/projects/${project.id}/files/${file.path}`, {
        method: "PUT",
        body: JSON.stringify({ content: content.current }),
      });
      setSaveState("saved");
      setError(null);
      return true;
    } catch (cause) {
      setSaveState("error");
      setError(describe(cause, "The file was not saved."));
      return false;
    }
  }, [user, project, file]);

  const onEdit = (value: string | undefined) => {
    content.current = value ?? "";
    setSaveState("unsaved");
    if (saveTimer.current) clearTimeout(saveTimer.current);
    saveTimer.current = setTimeout(save, 1200);
  };

  const run = async () => {
    if (!project || !lesson || busy) return;
    setBusy(true);
    setError(null);
    try {
      if (!(await save())) return;
      const queued = await api<{ id: string }>(user, `/v1/projects/${project.id}/executions`, {
        method: "POST",
        body: JSON.stringify({ operation_id: lesson.operations[0].id }),
      });
      let current = await api<Execution>(user, `/v1/executions/${queued.id}`);
      setExecution(current);
      while (current.status === "queued" || current.status === "running") {
        await new Promise((resolve) => setTimeout(resolve, 1000));
        current = await api<Execution>(user, `/v1/executions/${queued.id}`);
        setExecution(current);
      }
      setProject(await api<Project>(user, `/v1/projects/${project.id}`));
    } catch (cause) {
      setError(describe(cause, "The run did not start."));
    } finally {
      setBusy(false);
    }
  };

  if (!lesson || !project || !file) {
    return (
      <main className="signin">
        <div>
          {error ? (
            <>
              <p className="error" role="alert">
                {error}
              </p>
              <button onClick={onSignOut}>Sign out</button>
            </>
          ) : (
            <p>Loading the lab…</p>
          )}
        </div>
      </main>
    );
  }

  const assessment = execution?.assessment ?? null;
  const active = execution?.status === "queued" || execution?.status === "running";

  return (
    <div className="shell">
      <header className="topbar">
        <strong>DataForge</strong>
        <span className="lesson-title">{lesson.title}</span>
        <span className="spacer" />
        {project.completed_at ? <span className="badge pass">Completed</span> : null}
        <span className="muted">Best score: {project.best_score}</span>
        <span className="muted user">{identity.label}</span>
        <button onClick={onSignOut}>Sign out</button>
      </header>

      <section className="instructions" aria-label="Instructions">
        <ReactMarkdown remarkPlugins={[remarkGfm]}>{lesson.instructions}</ReactMarkdown>
      </section>

      <section className="work">
        <div className="filebar">
          <code>{file.path}</code>
          <span className={`muted save-${saveState}`} aria-live="polite">
            {SAVE_LABEL[saveState]}
          </span>
          <span className="spacer" />
          <button className="primary" onClick={run} disabled={busy}>
            {busy ? "Running…" : lesson.operations[0].title}
          </button>
        </div>

        <div className="editor">
          {editorReady ? (
            <Editor
              language="sql"
              theme={dark ? "vs-dark" : "light"}
              defaultValue={file.content}
              onChange={onEdit}
              options={{
                minimap: { enabled: false },
                fontSize: 14,
                scrollBeyondLastLine: false,
                automaticLayout: true,
                tabSize: 4,
              }}
            />
          ) : (
            <p className="muted pad">Loading the editor…</p>
          )}
        </div>

        <div className="results" aria-live="polite">
          {error ? (
            <p className="error" role="alert">
              {error}
            </p>
          ) : null}
          {!execution && !error ? (
            <p className="muted">Results show here after you run the model.</p>
          ) : null}
          {execution ? (
            <>
              <div className="result-head">
                <span className={`badge ${active ? "" : assessment?.passed ? "pass" : "fail"}`}>
                  {active
                    ? STATUS_LABEL[execution.status]
                    : assessment
                      ? assessment.passed
                        ? "Passed"
                        : "Not passed"
                      : STATUS_LABEL[execution.status]}
                </span>
                {assessment ? <strong>Score: {assessment.score} / 100</strong> : null}
                {execution.compute_seconds != null ? (
                  <span className="muted">{execution.compute_seconds} s compute</span>
                ) : null}
              </div>
              {assessment ? (
                <ul className="checks">
                  {assessment.checks.map((check) => (
                    <li key={check.id} className={check.passed ? "ok" : "bad"}>
                      <span className="mark" aria-hidden="true">
                        {check.passed ? "✓" : "✕"}
                      </span>
                      <span>
                        {check.title}
                        {check.critical ? <em> (critical)</em> : null}
                      </span>
                      <span className="muted">
                        {check.passed ? check.weight : 0} / {check.weight}
                      </span>
                    </li>
                  ))}
                </ul>
              ) : null}
              {execution.logs ? (
                <details open={execution.status !== "succeeded"}>
                  <summary>dbt log</summary>
                  <pre>{execution.logs}</pre>
                </details>
              ) : null}
            </>
          ) : null}
        </div>
      </section>
    </div>
  );
}

function describe(cause: unknown, fallback: string): string {
  if (cause instanceof ApiError) return cause.message;
  if (cause instanceof TypeError) return `${fallback} The API is not available.`;
  return fallback;
}
