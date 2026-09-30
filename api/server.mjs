import http from "node:http";
import { randomUUID } from "node:crypto";
import { pathToFileURL } from "node:url";
import { calculate, validateDraft, InputError, ENGINE_VERSION } from "../app/lib/corrosion.ts";
import { modelBridge } from "./model-bridge.mjs";

class HttpError extends Error {
  constructor(status, message) {
    super(message);
    this.status = status;
  }
}
const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const BODY_LIMIT = 256 * 1024;

export function configuration(env = process.env) {
  const origins = (env.ALLOWED_ORIGINS || "http://localhost:3000")
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);
  for (const origin of origins) {
    let url;
    try {
      url = new URL(origin);
    } catch {
      throw new Error("ALLOWED_ORIGINS must contain exact http(s) origins.");
    }
    if (!["http:", "https:"].includes(url.protocol) || url.origin !== origin)
      throw new Error("ALLOWED_ORIGINS must contain exact origins, without paths or wildcards.");
    if (env.NODE_ENV === "production" && url.protocol !== "https:")
      throw new Error("Production browser origins must use HTTPS.");
  }
  const config = {
    origins,
    supabaseUrl: (env.SUPABASE_URL || "").replace(/\/$/, ""),
    supabaseKey: env.SUPABASE_PUBLISHABLE_KEY || "",
    production: env.NODE_ENV === "production",
  };
  if (config.production && (!config.supabaseUrl || !config.supabaseKey))
    throw new Error("Production requires SUPABASE_URL and SUPABASE_PUBLISHABLE_KEY.");
  if (config.supabaseUrl) {
    const url = new URL(config.supabaseUrl);
    if (
      url.protocol !== "https:" &&
      !(
        url.protocol === "http:" &&
        ["localhost", "127.0.0.1"].includes(url.hostname) &&
        !config.production
      )
    )
      throw new Error("Supabase must use HTTPS in production.");
  }
  if (config.supabaseKey.startsWith("sb_secret_"))
    throw new Error("Use a publishable key, never a Supabase secret key.");
  // Legacy anon JWT keys are supported, but reject keys explicitly carrying service_role.
  if (config.supabaseKey.split(".").length === 3) {
    try {
      if (
        JSON.parse(Buffer.from(config.supabaseKey.split(".")[1], "base64url").toString()).role ===
        "service_role"
      )
        throw new Error("service_role is not allowed.");
    } catch (e) {
      if (e.message === "service_role is not allowed.") throw e;
    }
  }
  return config;
}

async function body(req) {
  if (!req.headers["content-type"]?.toLowerCase().startsWith("application/json"))
    throw new HttpError(415, "Use application/json.");
  if (Number(req.headers["content-length"]) > BODY_LIMIT)
    throw new HttpError(413, "Request exceeds 256 KB.");
  const chunks = [];
  let size = 0;
  for await (const chunk of req) {
    size += chunk.length;
    if (size > BODY_LIMIT) throw new HttpError(413, "Request exceeds 256 KB.");
    chunks.push(chunk);
  }
  try {
    return JSON.parse(Buffer.concat(chunks).toString("utf8"));
  } catch {
    throw new HttpError(400, "Malformed JSON.");
  }
}

export function createServer(config = configuration(), fetcher = fetch) {
  const model = modelBridge();
  // Per-instance protection. A shared gateway limiter is required before multi-instance scaling.
  const requests = new Map();
  const prune = setInterval(() => {
    const now = Date.now();
    for (const [key, v] of requests) if (v.reset <= now) requests.delete(key);
  }, 60000).unref();
  async function supabase(path, token, options = {}) {
    if (!config.supabaseUrl || !config.supabaseKey)
      throw new HttpError(503, "Cloud storage is not configured.");
    let response;
    try {
      response = await fetcher(config.supabaseUrl + path, {
        ...options,
        headers: {
          apikey: config.supabaseKey,
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
          ...options.headers,
        },
        signal: AbortSignal.timeout(12000),
      });
    } catch {
      throw new HttpError(503, "Supabase could not be reached. Try again.");
    }
    return response;
  }
  async function authenticated(req) {
    const match = /^Bearer ([^\s]+)$/.exec(req.headers.authorization || "");
    if (!match) throw new HttpError(401, "Sign in to access cloud assessments.");
    const response = await supabase("/auth/v1/user", match[1]);
    if (!response.ok)
      throw new HttpError(
        response.status >= 500 ? 503 : 401,
        response.status >= 500
          ? "Authentication is temporarily unavailable."
          : "Session expired or invalid. Sign in again.",
      );
    const user = await response.json();
    if (!uuid.test(user.id || "")) throw new HttpError(401, "Invalid user identity.");
    return { id: user.id, token: match[1] };
  }
  const server = http.createServer(async (req, res) => {
    const requestId = randomUUID();
    res.setHeader("X-Request-ID", requestId);
    res.setHeader("X-Content-Type-Options", "nosniff");
    res.setHeader("Cache-Control", "no-store");
    const send = (status, value) => {
      res.writeHead(status, { "Content-Type": "application/json; charset=utf-8" });
      res.end(JSON.stringify(value));
    };
    try {
      const origin = req.headers.origin;
      if (origin && !config.origins.includes(origin))
        throw new HttpError(403, "Origin is not allowed.");
      if (origin) {
        res.setHeader("Access-Control-Allow-Origin", origin);
        res.setHeader("Vary", "Origin");
      }
      if (req.method === "OPTIONS") {
        res.setHeader("Access-Control-Allow-Methods", "GET,POST,DELETE,OPTIONS");
        res.setHeader("Access-Control-Allow-Headers", "Authorization,Content-Type");
        res.setHeader("Access-Control-Max-Age", "600");
        res.writeHead(204);
        res.end();
        return;
      }
      const url = new URL(req.url, "http://api.local");
      if (req.method === "GET" && url.pathname === "/health") {
        send(200, {
          status: "ok",
          engine: ENGINE_VERSION,
          cloudConfigured: !!(config.supabaseUrl && config.supabaseKey),
        });
        return;
      }
      // Do not trust client-controlled X-Forwarded-For. Behind Render this may limit a proxy cohort.
      const key = req.socket.remoteAddress || "unknown",
        now = Date.now();
      let bucket = requests.get(key);
      if (!bucket || bucket.reset <= now) {
        if (requests.size >= 10000) throw new HttpError(503, "Service busy. Retry shortly.");
        bucket = { count: 0, reset: now + 60000 };
        requests.set(key, bucket);
      }
      if (++bucket.count > 120) {
        res.setHeader("Retry-After", String(Math.ceil((bucket.reset - now) / 1000)));
        throw new HttpError(429, "Too many requests. Retry shortly.");
      }
      if (req.method === "POST" && url.pathname === "/v1/calculate") {
        const input = await body(req);
        send(200, { result: calculate(input?.draft) });
        return;
      }
      if (url.pathname.startsWith("/v1/model/")) {
        await authenticated(req);
        let input;
        if (req.method === "GET" && url.pathname === "/v1/model/catalog")
          input = { action: "catalog" };
        else if (req.method === "GET" && url.pathname === "/v1/model/training")
          input = { action: "training" };
        else if (req.method === "POST" && url.pathname === "/v1/model/predict") {
          const payload = await body(req);
          if (
            !payload ||
            typeof payload !== "object" ||
            !(
              typeof payload.csv === "string" ||
              (Array.isArray(payload.pairs) &&
                payload.pairs.length >= 1 &&
                payload.pairs.length <= 400)
            )
          )
            throw new HttpError(422, "Supply CSV or 1–400 model pairs.");
          input = {
            action: "predict",
            pairs: payload.pairs,
            csv: payload.csv,
            run: payload.run || "1",
          };
        } else throw new HttpError(404, "Route not found.");
        try {
          send(200, await model.request(input));
        } catch (e) {
          throw new HttpError(e.status || 503, e.message);
        }
        return;
      }
      if (url.pathname === "/v1/assessments" || url.pathname.startsWith("/v1/assessments/")) {
        const user = await authenticated(req);
        if (req.method === "GET" && url.pathname === "/v1/assessments") {
          const cursor = url.searchParams.get("before");
          let position;
          if (cursor)
            try {
              position = JSON.parse(Buffer.from(cursor, "base64url").toString());
              if (
                !uuid.test(position.id) ||
                typeof position.created_at !== "string" ||
                !/^\d{4}-\d{2}-\d{2}T[\d:.]+(?:Z|\+00:00)$/.test(position.created_at) ||
                !Number.isFinite(Date.parse(position.created_at))
              )
                throw new Error();
            } catch {
              throw new HttpError(400, "Invalid pagination cursor.");
            }
          const query = new URLSearchParams({
            select: "id,created_at,name,method,engine_version",
            user_id: `eq.${user.id}`,
            order: "created_at.desc,id.desc",
            limit: "51",
          });
          if (position)
            query.set(
              "or",
              `(created_at.lt.${position.created_at},and(created_at.eq.${position.created_at},id.lt.${position.id}))`,
            );
          const response = await supabase("/rest/v1/assessments?" + query, user.token);
          if (!response.ok)
            throw new HttpError(
              502,
              "Could not list assessments. Check the database migration and policies.",
            );
          const rows = await response.json();
          const hasMore = rows.length > 50;
          send(200, {
            assessments: rows.slice(0, 50),
            nextCursor: hasMore
              ? Buffer.from(
                  JSON.stringify({ created_at: rows[49].created_at, id: rows[49].id }),
                ).toString("base64url")
              : null,
          });
          return;
        }
        if (req.method === "POST" && url.pathname === "/v1/assessments") {
          const input = await body(req);
          const draft = validateDraft(input?.draft);
          const result = calculate(draft);
          if (input.id !== undefined && !uuid.test(input.id))
            throw new HttpError(400, "Invalid assessment ID.");
          const id = input.id || randomUUID();
          // Immutable insertion. Client IDs make retries safe; no upsert can overwrite evidence.
          const row = {
            id,
            user_id: user.id,
            name: draft.name,
            method: draft.method,
            draft,
            result,
            engine_version: ENGINE_VERSION,
            status: "unreviewed",
          };
          const response = await supabase("/rest/v1/assessments", user.token, {
            method: "POST",
            headers: { Prefer: "return=representation" },
            body: JSON.stringify(row),
          });
          if (response.status === 409)
            throw new HttpError(
              409,
              "This assessment ID is already saved. Refresh the cloud list.",
            );
          if (!response.ok)
            throw new HttpError(
              502,
              "Assessment could not be saved. Check the database migration and policies.",
            );
          const [saved] = await response.json();
          send(201, { assessment: saved });
          return;
        }
        const id = url.pathname.slice("/v1/assessments/".length);
        if (!uuid.test(id)) throw new HttpError(404, "Assessment not found.");
        const query = new URLSearchParams({
          id: `eq.${id}`,
          user_id: `eq.${user.id}`,
          select: "*",
        });
        if (req.method === "GET" || req.method === "DELETE") {
          const response = await supabase("/rest/v1/assessments?" + query, user.token, {
            method: req.method,
            headers: { Prefer: "return=representation" },
          });
          if (!response.ok) throw new HttpError(502, "Could not access assessment.");
          const [row] = await response.json();
          if (!row) throw new HttpError(404, "Assessment not found.");
          send(200, req.method === "DELETE" ? { deleted: id } : { assessment: row });
          return;
        }
      }
      throw new HttpError(404, "Route not found.");
    } catch (error) {
      const status =
        error instanceof InputError ? 422 : error instanceof HttpError ? error.status : 500;
      // Never log tokens, request bodies, raw Supabase responses, or measurement data.
      if (status === 500)
        console.error(JSON.stringify({ requestId, status, event: "unexpected_error" }));
      if (!res.headersSent)
        send(status, {
          error: status === 500 ? "Unexpected server error." : error.message,
          ...(error instanceof InputError ? { field: error.field } : {}),
          requestId,
        });
      else res.end();
    }
  });
  server.requestTimeout = 20000;
  server.headersTimeout = 15000;
  server.maxHeadersCount = 50;
  server.on("close", () => {
    clearInterval(prune);
    model.close();
  });
  return server;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const server = createServer();
  const port = Number(process.env.PORT || 8000);
  server.listen(port, "0.0.0.0", () => console.log(`MAST API listening on port ${port}`));
  for (const signal of ["SIGINT", "SIGTERM"])
    process.on(signal, () => {
      server.close(() => process.exit(0));
      setTimeout(() => process.exit(1), 10000).unref();
    });
}
