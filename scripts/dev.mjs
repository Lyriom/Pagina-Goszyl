import { spawn, spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";

const projectRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const isWindows = process.platform === "win32";
const npm = isWindows ? "npm.cmd" : "npm";
const port = process.env.PORT || "8000";
const environment = { ...process.env };
const devVenv = path.join(projectRoot, ".venv-dev");
const python = path.join(devVenv, isWindows ? "Scripts/python.exe" : "bin/python");
const requirementsPath = path.join(projectRoot, "requirements.txt");
const requirementsStamp = path.join(devVenv, ".requirements.sha256");
const tailwindCli = path.join(
  projectRoot,
  "node_modules",
  "tailwindcss",
  "lib",
  "cli.js",
);

function run(command, args, options = {}) {
  return spawnSync(command, args, {
    cwd: projectRoot,
    stdio: "inherit",
    shell: isWindows,
    ...options,
  });
}

function supportsProject(command) {
  if (command.includes(path.sep) && !existsSync(command)) return false;
  return (
    spawnSync(
      command,
      ["-c", "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)"],
      { stdio: "ignore", shell: isWindows },
    ).status === 0
  );
}

if (!supportsProject(python)) {
  const basePython = ["python3.13", "python3.12", "python3.11", "python3", "python"]
    .find((candidate) => supportsProject(candidate));

  if (!basePython) {
    console.error("Gozsyl requiere Python 3.11 o superior. Instálalo y vuelve a ejecutar npm run dev.");
    process.exit(1);
  }

  console.log("Preparando .venv-dev con una versión compatible de Python...");
  const result = run(basePython, ["-m", "venv", devVenv]);
  if (result.status !== 0) process.exit(result.status || 1);
}

const requirementsHash = createHash("sha256")
  .update(readFileSync(requirementsPath))
  .digest("hex");
const installedHash = existsSync(requirementsStamp)
  ? readFileSync(requirementsStamp, "utf8").trim()
  : "";

if (requirementsHash !== installedHash) {
  console.log("Sincronizando las dependencias de Python...");
  const result = run(python, ["-m", "pip", "install", "-r", "requirements.txt"]);
  if (result.status !== 0) process.exit(result.status || 1);
  writeFileSync(requirementsStamp, `${requirementsHash}\n`);
}

if (!existsSync(tailwindCli)) {
  console.log("Instalando las herramientas del frontend...");
  const result = run(npm, ["ci"]);
  if (result.status !== 0) process.exit(result.status || 1);
}

if (!existsSync(path.join(projectRoot, ".env"))) {
  const defaults = {
    APP_URL: `http://localhost:${port}`,
    ENVIRONMENT: "development",
  };
  for (const [key, value] of Object.entries(defaults)) {
    if (environment[key] === undefined) environment[key] = value;
  }
}

console.log(`Gozsyl: http://localhost:${port}\n`);

const childOptions = {
  cwd: projectRoot,
  env: environment,
  stdio: "inherit",
  detached: !isWindows,
};
const processes = [
  spawn(
    python,
    ["-m", "uvicorn", "app.main:app", "--reload", "--port", port],
    childOptions,
  ),
  spawn(
    process.execPath,
    [
      tailwindCli,
      "-i",
      "./app/static/css/source.css",
      "-o",
      "./app/static/css/site.css",
      "--watch",
      "--poll",
    ],
    childOptions,
  ),
];

const active = new Set(processes);
let stopping = false;
let finalExitCode = 0;

function terminate(child, force = false) {
  if (!child.pid) return;
  try {
    if (isWindows) {
      spawnSync("taskkill", ["/pid", String(child.pid), "/T", ...(force ? ["/F"] : [])], {
        stdio: "ignore",
        shell: true,
      });
    } else {
      process.kill(-child.pid, force ? "SIGKILL" : "SIGTERM");
    }
  } catch {
    // El proceso ya terminó.
  }
}

function stop(exitCode = 0) {
  if (stopping) return;
  stopping = true;
  finalExitCode = exitCode;
  for (const child of active) terminate(child);
  const forceTimer = setTimeout(() => {
    for (const child of active) terminate(child, true);
  }, 3000);
  forceTimer.unref();
}

for (const child of processes) {
  child.on("error", (error) => {
    console.error(`No se pudo iniciar el entorno local: ${error.message}`);
    stop(1);
  });
  child.on("exit", (code, signal) => {
    active.delete(child);
    if (!stopping) stop(code ?? (signal ? 1 : 0));
    if (stopping && active.size === 0) process.exit(finalExitCode);
  });
}

process.on("SIGINT", () => stop(0));
process.on("SIGTERM", () => stop(0));
