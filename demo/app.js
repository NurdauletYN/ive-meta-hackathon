const $ = (id) => document.getElementById(id);
const files = new Map();
const active = new Set();
const MODELS = {
  muse: "Muse Spark",
  fake: "Offline demo",
  baseten: "Muse Spark Open",
};
const GATE_LABELS = {
  flutter_analyze: "Analyze",
  flutter_test: "Tests",
  flutter_build_web: "Web preview",
  preflight: "Store checks",
};
const CHECK_LABELS = {
  privacy_link: "Privacy policy",
  terms_link: "Terms of service",
  account_deletion: "Delete account",
  restore_purchases: "Restore purchases",
  subscription_disclosure: "Subscription disclosure",
  no_placeholders: "No placeholder copy",
  wcag_contrast: "Contrast",
  interactive_home: "Home is interactive",
  smoke_tests_pass: "Smoke tests",
  account_deletion_erases_data: "Deletion clears data",
  home_not_webview: "Home is not a WebView",
  remote_code: "No remote code",
};
let cost = 0;
let designRun = null;
let es = null;
let repairSeen = 0;

function ticker(text, cls) {
  const el = $("ticker");
  el.textContent = text;
  el.className = "ticker" + (cls ? ` ${cls}` : "");
}

function log(text, cls) {
  const li = document.createElement("li");
  if (cls) li.className = cls;
  li.textContent = text;
  $("log").prepend(li);
}

function addCost(value) {
  if (typeof value === "number" && !Number.isNaN(value)) cost += value;
  $("cost").textContent = `$${cost.toFixed(2)}`;
}

function resetSession() {
  cost = 0;
  repairSeen = 0;
  addCost(0);
  files.clear();
  $("log").innerHTML = "";
  $("files").innerHTML = "";
  $("file-view").textContent = "Select a file.";
  $("evidence").hidden = true;
  $("compare-results").hidden = true;
  $("evidence-steps").innerHTML = "";
  $("evidence-preflight").innerHTML = "";
  $("evidence-meta").textContent = "";
  $("evidence-ship").textContent = "";
}

function setScreen(el, inner) {
  el.innerHTML = "";
  el.appendChild(inner);
}

function waiting(text) {
  const p = document.createElement("p");
  p.className = "empty";
  p.textContent = text;
  return p;
}

let previewBase = null;

function splitPreview(url) {
  const raw = String(url || "");
  const hashAt = raw.indexOf("#");
  if (hashAt === -1) return { base: raw, hash: "" };
  return { base: raw.slice(0, hashAt), hash: raw.slice(hashAt) };
}

function iframe(url) {
  const frame = document.createElement("iframe");
  const parts = splitPreview(url);
  previewBase = parts.base;
  frame.src = url;
  frame.title = "app preview";
  frame.setAttribute("sandbox", "allow-scripts allow-same-origin allow-forms");
  return frame;
}

function applyTourHash(hash) {
  const next = hash || "#/onboarding";
  previewBase = previewBase || "";
  const frame = document.querySelector(".phone .screen iframe");
  if (!frame || !previewBase) return;
  frame.src = previewBase + next;
  for (const btn of document.querySelectorAll("#tour-chips [data-hash]")) {
    btn.classList.toggle("on", btn.dataset.hash === next);
  }
}

function phoneCard({ id, label, small }) {
  const wrap = document.createElement("div");
  wrap.className = "phone-wrap";
  wrap.id = id;
  const caption = document.createElement("p");
  caption.className = "phone-label";
  caption.append(document.createTextNode(label));
  const slot = document.createElement("span");
  slot.className = "badge-slot";
  caption.append(slot);
  const phone = document.createElement("div");
  phone.className = "phone" + (small ? " small" : "");
  phone.innerHTML = `<div class="island"></div><div class="screen"></div><div class="home"></div>`;
  wrap.append(caption, phone);
  return wrap;
}

function badge(ok) {
  const span = document.createElement("span");
  span.className = `badge ${ok ? "ok" : "fail"}`;
  span.textContent = ok ? "pass" : "fail";
  return span;
}

function draftBadge() {
  const span = document.createElement("span");
  span.className = "badge draft";
  span.textContent = "draft";
  return span;
}

function setStep(name) {
  const steps = document.getElementById("steps");
  if (!steps) return;
  for (const li of steps.querySelectorAll("li")) {
    li.classList.toggle("on", li.dataset.step === name);
  }
}

function setLabel(wrap, text) {
  const caption = wrap.querySelector(".phone-label");
  const slot = caption.querySelector(".badge-slot");
  caption.textContent = "";
  caption.append(document.createTextNode(text), slot);
}

function payload() {
  return {
    idea: $("idea").value,
    pilot: $("pilot").value,
    max_usd: Number($("max_usd").value),
    build_web: $("build_web").checked,
  };
}

async function api(path, opts) {
  const res = await fetch(path, opts);
  const text = await res.text();
  try {
    return JSON.parse(text);
  } catch {
    throw new Error(text.slice(0, 200));
  }
}

function connectEvents() {
  if (es) es.close();
  es = new EventSource("/api/events");
  es.onmessage = (msg) => {
    const ev = JSON.parse(msg.data);
    if (ev.run_id && active.size && !active.has(ev.run_id)) return;
    handle(ev);
  };
}

function handle(ev) {
  const type = ev.type;
  if (type === "stage") {
    const label = {
      design: "Sketching three looks…",
      prepare: "Opening the app shell…",
      spec: "Writing names and screens…",
      file_ops: "Laying out the app…",
      gate: "Running store checks…",
    }[ev.name] || ev.name;
    if (ev.status === "start") ticker(label, "busy");
    else if (ev.status === "ok") ticker(ev.app_name ? `${ev.app_name} is taking shape` : `${ev.name} ready`, "ok");
    else ticker(`${ev.name} failed`, "fail");
    log(`${ev.run_id} · ${ev.name} ${ev.status}`, ev.status === "fail" ? "fail" : "ok");
  } else if (type === "pilot_call") {
    if (ev.status === "ok") {
      addCost(ev.est_cost_usd || 0);
      log(`${ev.stage} ok`, "ok");
    } else if (ev.status === "start") {
      ticker("Talking to the model…", "busy");
    } else if (ev.status === "error") {
      ticker(ev.error || "model error", "fail");
      log(`${ev.stage} error: ${ev.error}`, "fail");
    }
  } else if (type === "guard") {
    ticker(`Blocked a protected file`, "fail");
    log(`blocked ${ev.code}: ${ev.path || ""}`, "fail");
  } else if (type === "file") {
    files.set(ev.path, ev.preview || "");
    const li = document.createElement("li");
    li.textContent = `${ev.op} ${ev.path}`;
    li.addEventListener("click", () => {
      $("file-view").textContent = files.get(ev.path) || "";
    });
    $("files").prepend(li);
  } else if (type === "preflight") {
    const status = String(ev.status || "").split(".").pop();
    appendRow($("evidence-preflight"), ev.check_id, status, ev.message || status);
    $("evidence").hidden = false;
  } else if (type === "repair") {
    repairSeen = Math.max(repairSeen, Number(ev.round) || 0);
    ticker(`Repairing (round ${ev.round})…`, "busy");
    log(`repair round ${ev.round}`, "fail");
  } else if (type === "preview") {
    showPreview(ev.run_id, ev.url, ev.mode, ev.kind);
    if (ev.kind === "skin") ticker("Draft look on the phone — still writing screens…", "busy");
    if (ev.kind === "web") ticker("Live Flutter preview on the phone", "ok");
  } else if (type === "direction") {
    showDirection(ev);
  } else if (type === "picked") {
    ticker(`Using ${ev.name}. Build the app when you’re ready.`, "ok");
    for (const wrap of document.querySelectorAll(".phone-wrap")) wrap.classList.remove("picked");
    const card = document.getElementById(`dir-${ev.n}`);
    if (card) card.classList.add("picked");
  } else if (type === "done") {
    log(`${ev.run_id} done ${ev.ok ? "ok" : "fail"}`, ev.ok ? "ok" : "fail");
    if (ev.preview) showPreview(ev.run_id, ev.preview, ev.mode, ev.kind);
    ticker(ev.ok ? "Your app is on the phone." : (ev.error || "Build failed"), ev.ok ? "ok" : "fail");
    if (ev.ok) setStep("checks");
    const wrap = document.getElementById(`phone-${ev.run_id}`);
    if (wrap) {
      const slot = wrap.querySelector(".badge-slot");
      if (slot) slot.replaceChildren(badge(!!ev.ok));
    }
    fillEvidence(ev.run_id);
    maybeFillCompare();
  } else if (type === "choice") {
    ticker(`Applying ${ev.name} colors`, "ok");
  }
}

function showPreview(runId, url, mode, kind) {
  const wrap = ensurePhone(runId, mode);
  const slot = wrap.querySelector(".badge-slot");
  if (slot) slot.replaceChildren(kind === "skin" ? draftBadge() : document.createTextNode(""));
  const hashed = kind === "web" && url && !String(url).includes("#") ? `${url}#/onboarding` : url;
  setScreen(wrap.querySelector(".screen"), iframe(hashed));
  if (kind === "web") applyTourHash("#/onboarding");
}

function ensurePhone(runId, mode) {
  let wrap = document.getElementById(`phone-${runId}`);
  if (!wrap) {
    const compare = runId.endsWith("-harness") || runId.endsWith("-bare");
    if (!compare) $("phones").innerHTML = "";
    wrap = phoneCard({
      id: `phone-${runId}`,
      label: mode || "preview",
      small: compare,
    });
    $("phones").appendChild(wrap);
  }
  return wrap;
}

function mountDirectionSlots() {
  $("phones").innerHTML = "";
  for (let i = 1; i <= 3; i += 1) {
    const card = phoneCard({ id: `dir-${i}`, label: `Look ${i}`, small: true });
    card.style.cursor = "pointer";
    card.addEventListener("click", () => pickDirection(i, card));
    $("phones").appendChild(card);
    setScreen(card.querySelector(".screen"), waiting("Designing…"));
  }
}

function mountCompare(ids) {
  $("phones").innerHTML = "";
  for (const id of ids) {
    const mode = id.endsWith("bare") ? "without harness" : "with harness";
    const card = phoneCard({ id: `phone-${id}`, label: mode, small: true });
    $("phones").appendChild(card);
    setScreen(card.querySelector(".screen"), waiting("Building…"));
  }
}

function appendRow(list, name, status, detail) {
  if (!list) return;
  let li = [...list.children].find((el) => el.dataset.row === name);
  if (!li) {
    li = document.createElement("li");
    li.dataset.row = name;
    list.appendChild(li);
  }
  const ok = status === true || status === "PASS" || status === "ok";
  const fail = status === false || status === "FAIL" || status === "fail";
  li.className = fail ? "fail" : ok ? "ok" : String(status || "WARN");
  const mark = document.createElement("span");
  mark.className = "mark";
  mark.textContent = fail ? "FAIL" : ok ? "PASS" : String(status || "WARN");
  li.replaceChildren(mark, document.createTextNode(`${name}${detail ? " — " + detail : ""}`));
}

function modelName(pilot) {
  return MODELS[pilot] || pilot || "unknown";
}

async function fillEvidence(runId) {
  const panel = $("evidence");
  panel.hidden = false;
  let job = {};
  try {
    const payload = await api("/api/job");
    const jobs = payload.jobs || [];
    job = jobs.find((j) => j.run_id === runId) || payload;
  } catch {
    job = {};
  }
  const summary = job.summary || {};
  const tokens = summary.tokens || {};
  const pilot = job.pilot || $("pilot").value;
  const repairs = summary.repair_rounds ?? repairSeen;
  const costUsd = tokens.est_cost_usd ?? cost;
  $("evidence-meta").textContent =
    `${modelName(pilot)} · $${Number(costUsd || 0).toFixed(2)} · ` +
    `${tokens.input || 0} in / ${tokens.cached || 0} cached / ${tokens.output || 0} out · ` +
    `${repairs ?? 0} repair ${Number(repairs) === 1 ? "round" : "rounds"}`;
  const steps = summary.gate_steps || [];
  const stepList = $("evidence-steps");
  if (steps.length) {
    stepList.innerHTML = "";
    for (const step of steps) {
      const name = GATE_LABELS[step.name] || step.name || "step";
      appendRow(stepList, name, step.ok, step.ok ? "ok" : "failed");
    }
  }
  const checks = summary.preflight || [];
  if (checks.length) {
    const list = $("evidence-preflight");
    list.innerHTML = "";
    for (const check of checks) {
      const status = String(check.status || "").split(".").pop();
      const id = check.id || check.check_id || "check";
      appendRow(list, CHECK_LABELS[id] || id, status, check.message || "");
    }
  }
  const shipEl = $("evidence-ship");
  shipEl.textContent = "TestFlight: not uploaded from this window";
  try {
    const res = await fetch(`/runs/${encodeURIComponent(runId)}/project/ship_report.json`);
    if (res.ok) {
      const report = await res.json();
      const blob = JSON.stringify(report);
      if (blob.includes("ASC_") || blob.includes("BEGIN PRIVATE")) {
        shipEl.textContent = "TestFlight: report present (redacted)";
      } else {
        shipEl.textContent = `TestFlight: ${report.outcome || report.ok}`;
      }
    }
  } catch {
    /* no ship report */
  }
}

function renderMarkdownTables(md, dest) {
  dest.innerHTML = "";
  const chunks = md.split(/\n{2,}/);
  for (const chunk of chunks) {
    const lines = chunk.trim().split("\n");
    if (lines.length >= 2 && lines[0].startsWith("|") && lines[1].includes("---")) {
      const table = document.createElement("table");
      lines.forEach((line, i) => {
        const cells = line.replace(/^\||\|$/g, "").split("|").map((c) => c.trim());
        if (i === 1 && cells.every((c) => /^:?-+:?$/.test(c))) return;
        const tr = document.createElement("tr");
        for (const cell of cells) {
          const el = document.createElement(i === 0 ? "th" : "td");
          el.textContent = cell;
          tr.appendChild(el);
        }
        table.appendChild(tr);
      });
      dest.appendChild(table);
    } else if (chunk.trim()) {
      const p = document.createElement("p");
      p.textContent = chunk.trim();
      dest.appendChild(p);
    }
  }
}

async function maybeFillCompare() {
  const payload = await api("/api/job").catch(() => null);
  const jobs = (payload && payload.jobs) || [];
  const compare = jobs.filter((j) => String(j.run_id || "").endsWith("-harness") || String(j.run_id || "").endsWith("-bare"));
  if (compare.length < 2) return;
  if (compare.some((j) => j.status === "running")) return;
  $("compare-results").hidden = false;
  try {
    const res = await fetch("/api/results");
    if (!res.ok) {
      $("compare-table").textContent = "results.md not found. Run harness report.";
      return;
    }
    const md = await res.text();
    renderMarkdownTables(md, $("compare-table"));
  } catch (err) {
    $("compare-table").textContent = String(err);
  }
}

async function pickDirection(index, card) {
  if (!designRun) return;
  const picked = await api("/api/pick", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ run_id: designRun, n: index }),
  });
  if (!picked.ok) {
    ticker(picked.error || "pick failed", "fail");
    return;
  }
  for (const wrap of document.querySelectorAll(".phone-wrap")) wrap.classList.remove("picked");
  card.classList.add("picked");
  const name = picked.choice?.direction?.name;
  ticker(`Using ${name || "this look"}. Build the app when you’re ready.`, "ok");
}

function showDirection(ev) {
  const wrap = document.getElementById(`dir-${ev.index}`);
  if (!wrap) return;
  setLabel(wrap, `${ev.index}. ${ev.name}`);
  if (ev.preview) setScreen(wrap.querySelector(".screen"), iframe(ev.preview));
}

async function run(kind, extra) {
  const body = { ...payload(), ...extra };
  if (kind === "design") {
    body.run_id = body.run_id || slug("d");
    designRun = body.run_id;
    active.clear();
    active.add(body.run_id);
    resetSession();
    mountDirectionSlots();
    setStep("looks");
    ticker("Sketching three looks…", "busy");
  }
  if (kind === "build") {
    body.mode = extra.mode || "harness";
    body.run_id = extra.run_id || slug(body.mode);
    if (designRun) body.choice_from = designRun;
    active.clear();
    active.add(body.run_id);
    resetSession();
    $("phones").innerHTML = "";
    const card = phoneCard({ id: `phone-${body.run_id}`, label: body.mode, small: false });
    $("phones").appendChild(card);
    setScreen(card.querySelector(".screen"), waiting("Building your app…"));
    setStep("build");
    ticker("Building the app onto the phone…", "busy");
  }
  if (kind === "compare") {
    body.run_id = extra.run_id || slug("cmp");
    if (designRun) body.choice_from = designRun;
    resetSession();
    setStep("compare");
    ticker("Building with Rocket and without it, side by side…", "busy");
  }
  const started = await api(`/api/${kind}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!started.ok) {
    ticker(started.error || "failed to start", "fail");
    log(started.error || "failed to start", "fail");
    return;
  }
  if (kind === "compare") {
    const ids = started.run_ids || [];
    active.clear();
    ids.forEach((id) => active.add(id));
    mountCompare(ids);
  }
  log(`started ${kind} ${started.run_id || (started.run_ids || []).join(",")}`);
}

function slug(prefix) {
  return `${prefix}-${Date.now().toString(36).slice(-5)}`;
}

$("btn-design").addEventListener("click", () => run("design", { run_id: slug("d") }));
$("btn-build").addEventListener("click", () => run("build", { mode: "harness" }));
$("btn-compare").addEventListener("click", () => run("compare", {}));

document.querySelectorAll("[data-hash]").forEach((btn) => {
  btn.addEventListener("click", () => applyTourHash(btn.dataset.hash));
});

async function boot() {
  connectEvents();
  const ideas = await api("/api/ideas");
  const box = $("ideas");
  for (const idea of ideas) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.textContent = idea.title;
    btn.addEventListener("click", () => {
      $("idea").value = idea.blurb;
      for (const other of box.querySelectorAll("button")) other.classList.remove("active");
      btn.classList.add("active");
    });
    box.appendChild(btn);
  }
}

boot().catch((err) => ticker(String(err), "fail"));
