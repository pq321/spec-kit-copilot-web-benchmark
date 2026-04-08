import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const publicDir = path.join(__dirname, "public");

const contentTypes = {
  ".html": "text/html; charset=utf-8",
  ".txt": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".txton": "application/json; charset=utf-8"
};

function resolveRequestPath(urlPath) {
  if (urlPath === "/") {
    return path.join(publicDir, "index.html");
  }
  if (urlPath === "/request" || urlPath === "/request.html") {
    return path.join(publicDir, "request.html");
  }
  const safePath = path.normalize(urlPath).replace(/^(\.\.[/\\])+/, "");
  return path.join(publicDir, safePath);
}

function createAppServer() {
  return createServer(async (req, res) => {
    try {
      const requestUrl = new URL(req.url || "/", "http://127.0.0.1");
      const filePath = resolveRequestPath(requestUrl.pathname);
      const body = await readFile(filePath);
      const extension = path.extname(filePath);
      res.writeHead(200, {
        "Content-Type": contentTypes[extension] || "application/octet-stream"
      });
      res.end(body);
    } catch (error) {
      res.writeHead(404, { "Content-Type": "text/plain; charset=utf-8" });
      res.end(`Not found: ${error instanceof Error ? error.message : "unknown error"}`);
    }
  });
}

export function startServer({ port = 4173 } = {}) {
  const server = createAppServer();
  return new Promise((resolve) => {
    server.listen(port, "127.0.0.1", () => {
      resolve({
        server,
        url: `http://127.0.0.1:${port}`
      });
    });
  });
}

if (process.argv[1] === __filename) {
  const port = Number(process.env.PORT || 4173);
  startServer({ port }).then(({ url }) => {
    process.stdout.write(`Benchmark site listening at ${url}\n`);
  });
}
