import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";
import readline from "node:readline";

export function modelBridge() {
  let worker = null,
    pending = null;
  const queue = [];
  function failAll(error) {
    if (pending) {
      clearTimeout(pending.timer);
      pending.reject(error);
      pending = null;
    }
    for (const item of queue) item.reject(error);
    queue.length = 0;
  }
  function boot() {
    if (worker) return;
    const child = spawn(
      process.env.PYTHON_BIN || "python",
      [fileURLToPath(new URL("./model-worker.py", import.meta.url))],
      {
        stdio: ["pipe", "pipe", "ignore"],
        windowsHide: true,
        env: { ...process.env, PYTHONUNBUFFERED: "1", OMP_NUM_THREADS: "1" },
      },
    );
    worker = child;
    child.stdin.on("error", () => {});
    const lines = readline.createInterface({ input: child.stdout });
    lines.on("line", (line) => {
      if (child !== worker || !pending) return;
      const item = pending;
      pending = null;
      clearTimeout(item.timer);
      try {
        const result = JSON.parse(line);
        if (result.ok) item.resolve(result.data);
        else item.reject(Object.assign(new Error(result.error), { status: result.status }));
      } catch {
        item.reject(Object.assign(new Error("Invalid model response."), { status: 503 }));
      }
      pump();
    });
    const fail = () => {
      if (child !== worker) return;
      worker = null;
      failAll(Object.assign(new Error("Python model worker is unavailable."), { status: 503 }));
    };
    child.on("error", fail);
    child.on("exit", fail);
  }
  function pump() {
    if (pending || !queue.length) return;
    boot();
    pending = queue.shift();
    pending.timer = setTimeout(() => {
      const child = worker;
      worker = null;
      child?.kill();
      failAll(Object.assign(new Error("Model request timed out. Retry shortly."), { status: 503 }));
    }, 45000);
    worker.stdin.write(JSON.stringify(pending.input) + "\n");
  }
  return {
    request(input) {
      if (queue.length >= 8)
        return Promise.reject(
          Object.assign(new Error("Model busy. Retry shortly."), { status: 503 }),
        );
      return new Promise((resolve, reject) => {
        queue.push({ input, resolve, reject });
        pump();
      });
    },
    close() {
      const child = worker;
      worker = null;
      child?.kill();
      failAll(new Error("Server stopped."));
    },
  };
}
