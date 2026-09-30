import { test } from "node:test";
import assert from "node:assert/strict";
import { createServer, configuration } from "../server.mjs";
import { example, calculate } from "../../app/lib/corrosion.ts";
const user = "11111111-1111-4111-8111-111111111111";
const id = "22222222-2222-4222-8222-222222222222";
const config = {
  origins: ["http://localhost:3000"],
  supabaseUrl: "https://example.supabase.co",
  supabaseKey: "sb_publishable_test",
};
async function setup(t, fetcher) {
  const server = createServer(config, fetcher);
  await new Promise((r) => server.listen(0, "127.0.0.1", r));
  t.after(
    () =>
      new Promise((r) => {
        server.close(r);
        server.closeAllConnections();
      }),
  );
  return `http://127.0.0.1:${server.address().port}`;
}
const json = (value, status = 200) => new Response(JSON.stringify(value), { status });
test("health, physics, malformed body and CORS", async (t) => {
  const url = await setup(t, () => {
    throw new Error("No upstream expected");
  });
  assert.equal((await fetch(url + "/health")).status, 200);
  const r = await fetch(url + "/v1/calculate", {
    method: "POST",
    headers: { "Content-Type": "application/json", Origin: "http://localhost:3000" },
    body: JSON.stringify({ draft: example }),
  });
  assert.equal(r.status, 200);
  assert.equal(r.headers.get("access-control-allow-origin"), "http://localhost:3000");
  assert.equal((await r.json()).result.rate, calculate(example).rate);
  assert.equal(
    (
      await fetch(url + "/v1/calculate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: "{",
      })
    ).status,
    400,
  );
  assert.equal(
    (await fetch(url + "/health", { headers: { Origin: "https://attacker.example" } })).status,
    403,
  );
  assert.equal(
    (
      await fetch(url + "/v1/calculate", {
        method: "OPTIONS",
        headers: { Origin: "http://localhost:3000" },
      })
    ).status,
    204,
  );
});
test("anonymous and expired sessions cannot access cloud or model", async (t) => {
  const url = await setup(t, async () => json({}, 401));
  for (const path of ["/v1/assessments", "/v1/model/catalog"]) {
    assert.equal((await fetch(url + path)).status, 401);
    assert.equal(
      (await fetch(url + path, { headers: { Authorization: "Bearer invalid" } })).status,
      401,
    );
  }
});
test("save derives owner from verified identity and ignores supplied results", async (t) => {
  let inserted;
  const url = await setup(t, async (path, options) => {
    assert.equal(options.headers.Authorization, "Bearer valid");
    assert.equal(options.headers.apikey, config.supabaseKey);
    if (path.endsWith("/auth/v1/user")) return json({ id: user });
    inserted = JSON.parse(options.body);
    return json([inserted], 201);
  });
  const response = await fetch(url + "/v1/assessments", {
    method: "POST",
    headers: { Authorization: "Bearer valid", "Content-Type": "application/json" },
    body: JSON.stringify({ id, draft: example, user_id: "attacker", result: { rate: 0 } }),
  });
  assert.equal(response.status, 201);
  assert.equal(inserted.user_id, user);
  assert.equal(inserted.result.rate, calculate(example).rate);
  assert.equal(inserted.id, id);
});
test("detail and deletion include verified owner filter and hide absent rows", async (t) => {
  const urls = [];
  const url = await setup(t, async (path) => {
    urls.push(path);
    return path.endsWith("/auth/v1/user") ? json({ id: user }) : json([]);
  });
  for (const method of ["GET", "DELETE"])
    assert.equal(
      (
        await fetch(url + "/v1/assessments/" + id, {
          method,
          headers: { Authorization: "Bearer valid" },
        })
      ).status,
      404,
    );
  assert.ok(
    urls
      .filter((x) => x.includes("/rest/"))
      .every((x) => new URL(x).searchParams.get("user_id") === `eq.${user}`),
  );
});
test("list pagination preserves timestamp ties and owner scope", async (t) => {
  let query;
  const rows = Array.from({ length: 51 }, (_, i) => ({
    id: `22222222-2222-4222-8222-${String(i).padStart(12, "0")}`,
    created_at: "2026-09-30T01:00:00.123456+00:00",
  }));
  const url = await setup(t, async (path) => {
    if (path.endsWith("/auth/v1/user")) return json({ id: user });
    query = new URL(path).searchParams;
    return json(rows);
  });
  const response = await fetch(url + "/v1/assessments", {
    headers: { Authorization: "Bearer valid" },
  });
  const data = await response.json();
  assert.equal(data.assessments.length, 50);
  assert.ok(data.nextCursor);
  assert.equal(
    (
      await fetch(url + "/v1/assessments?before=" + data.nextCursor, {
        headers: { Authorization: "Bearer valid" },
      })
    ).status,
    200,
  );
  assert.match(query.get("or"), /id.lt/);
  assert.equal(
    (
      await fetch(url + "/v1/assessments?before=bad", {
        headers: { Authorization: "Bearer valid" },
      })
    ).status,
    400,
  );
});
test("input size, type and physics boundaries are enforced", async (t) => {
  const url = await setup(t, async () => json({ id: user }));
  for (const [body, status] of [
    [JSON.stringify({ draft: { ...example, mechanism: "pitting" } }), 422],
    ["x".repeat(270000), 413],
  ]) {
    assert.equal(
      (
        await fetch(url + "/v1/calculate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body,
        })
      ).status,
      status,
    );
  }
  assert.equal((await fetch(url + "/v1/calculate", { method: "POST", body: "{}" })).status, 415);
});
test("production configuration rejects wildcard origins and privileged keys", () => {
  assert.throws(() => configuration({ NODE_ENV: "production" }));
  assert.throws(() => configuration({ ALLOWED_ORIGINS: "*" }));
  assert.throws(() => configuration({ SUPABASE_PUBLISHABLE_KEY: "sb_secret_bad" }));
  assert.throws(() =>
    configuration({
      SUPABASE_PUBLISHABLE_KEY:
        "x." + Buffer.from(JSON.stringify({ role: "service_role" })).toString("base64url") + ".x",
    }),
  );
});
