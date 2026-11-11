/**
 * Same-origin proxy to the API. The browser calls /api/v1/..., and this
 * server forwards the request to the API on the private network. The API
 * then needs no public address, and the browser needs no API URL.
 */
export const dynamic = "force-dynamic";

const API_URL = (process.env.API_INTERNAL_URL ?? "http://localhost:8000").replace(/\/$/, "");
const FORWARD_HEADERS = ["authorization", "content-type", "x-dev-user"];
const MAX_BODY_BYTES = 100_000;

async function forward(request: Request, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  // Only the versioned API. No other path on the API host is reachable.
  if (path[0] !== "v1" || path.some((part) => part === ".." || part === ".")) {
    return Response.json({ detail: "Not found." }, { status: 404 });
  }
  const headers = new Headers();
  for (const name of FORWARD_HEADERS) {
    const value = request.headers.get(name);
    if (value) headers.set(name, value);
  }
  let body: ArrayBuffer | undefined;
  if (request.method !== "GET" && request.method !== "HEAD") {
    body = await request.arrayBuffer();
    if (body.byteLength > MAX_BODY_BYTES) {
      return Response.json({ detail: "The request is too large." }, { status: 413 });
    }
  }
  const target = `${API_URL}/${path.map(encodeURIComponent).join("/")}${new URL(request.url).search}`;
  let upstream: Response;
  try {
    upstream = await fetch(target, { method: request.method, headers, body, cache: "no-store" });
  } catch {
    return Response.json({ detail: "The API is not available. Try again." }, { status: 502 });
  }
  const responseHeaders = new Headers({ "cache-control": "no-store" });
  const contentType = upstream.headers.get("content-type");
  if (contentType) responseHeaders.set("content-type", contentType);
  const challenge = upstream.headers.get("www-authenticate");
  if (challenge) responseHeaders.set("www-authenticate", challenge);
  return new Response(upstream.body, { status: upstream.status, headers: responseHeaders });
}

export { forward as GET, forward as POST, forward as PUT };
