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
  kit_usage: "Kit widgets",
  not_text_only: "Not text-only",
};
const BUILD_STEPS = ["understand", "designing", "writing", "checks", "fixing", "ready"];
let cost = 0;
let tokensIn = 0;
let tokensOut = 0;
let designRun = null;
let es = null;
let repairSeen = 0;
let lookChosen = false;
let previewBase = null;
let buildStartedAt = 0;
let stepStartedAt = 0;
let elapsedTimer = null;
let currentBuildStep = null;

function ticker(text, cls) {
  const el = $("ticker");
  el.textContent = text;
  el.className = "ticker" + (cls ? ` ${cls}` : "");
}

function log(text, cls) {
  const li = document.createElement("li");
  if (cls) li.className = cls;
  li.textContent = text;
  $("log").appendChild(li);
  li.scrollIntoView({ block: "end" });
}

function addCost(value) {
  if (typeof value === "number" && !Number.isNaN(value)) cost += value;
  $("cost").textContent = `$${cost.toFixed(2)}`;
}

function addTokens(input, output) {
  tokensIn += Number(input) || 0;
  tokensOut += Number(output) || 0;
  const el = $("token-count");
  if (el) el.textContent = `${tokensIn + tokensOut} tokens · ${tokensIn} in / ${tokensOut} out`;
}

function setUsedModel(pilot) {
  const el = $("used-model");
  if (!el) return;
  if (pilot === "baseten") el.textContent = "Built with Muse Spark Open";
  else if (pilot === "muse") el.textContent = "Built with Muse Spark";
  else if (pilot === "fake") el.textContent = "Offline demo (no API)";
  else el.textContent = "";
}

function enableBuild(on) {
  lookChosen = !!on;
  $("btn-build").disabled = !lookChosen;
}

function resetSession() {
  cost = 0;
  tokensIn = 0;
  tokensOut = 0;
  repairSeen = 0;
  addCost(0);
  addTokens(0, 0);
  files.clear();
  $("log").innerHTML = "";
  $("files").innerHTML = "";
  $("file-view").textContent = "Select a file.";
  $("evidence").hidden = true;
  $("compare-results").hidden = true;
  $("ship-panel").hidden = true;
  $("evidence-steps").innerHTML = "";
  $("evidence-preflight").innerHTML = "";
  $("evidence-meta").textContent = "";
  $("evidence-ship").textContent = "";
  $("plain-error").hidden = true;
  $("plain-error").textContent = "";
  stopElapsed();
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
  const frame = document.querySelector(".phone .screen iframe");
  if (!frame || !previewBase) return;
  frame.src = previewBase + next;
  for (const btn of document.querySelectorAll("#tour-chips [data-hash]")) {
    btn.classList.toggle("on", btn.dataset.hash === next);
  }
}

function phoneCard({ id, label, small, useLook }) {
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
  if (useLook) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "use-look";
    btn.textContent = "Use this look";
    btn.addEventListener("click", (ev) => {
      ev.stopPropagation();
      pickDirection(Number(id.replace("dir-", "")), wrap);
    });
    wrap.append(btn);
  }
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
  if (name === "ship") $("ship-panel").hidden = false;
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

function formatElapsed(ms) {
  const s = Math.max(0, Math.round(ms / 1000));
  return s < 60 ? `${s}s` : `${Math.floor(s / 60)}m ${s % 60}s`;
}

function stopElapsed() {
  if (elapsedTimer) clearInterval(elapsedTimer);
  elapsedTimer = null;
  currentBuildStep = null;
}

function setBuildStep(name, { fail } = {}) {
  const list = $("build-stepper");
  if (!list) return;
  list.hidden = false;
  $("build-stats").hidden = false;
  const order = BUILD_STEPS.indexOf(name);
  for (const li of list.querySelectorAll("li")) {
    const id = li.dataset.build;
    const idx = BUILD_STEPS.indexOf(id);
    li.classList.remove("on", "done", "fail");
    if (idx < order) li.classList.add("done");
    if (id === name) li.classList.add(fail ? "fail" : "on");
    if (id === "fixing" && name === "fixing") {
      li.querySelector(".step-name").textContent = `Fixing issues (round ${repairSeen || 1})`;
    }
  }
  currentBuildStep = name;
  stepStartedAt = Date.now();
  const activeLi = list.querySelector(`li[data-build="${name}"] [data-elapsed]`);
  if (elapsedTimer) clearInterval(elapsedTimer);
  elapsedTimer = setInterval(() => {
    if (activeLi) activeLi.textContent = formatElapsed(Date.now() - stepStartedAt);
  }, 250);
}

function skeletonPhone(on) {
  document.querySelectorAll(".phone .screen").forEach((el) => el.classList.toggle("shimmer", !!on));
}

function plainError(text) {
  const t = String(text || "");
  if (/budget/i.test(t)) return "The spend cap was reached. Raise it under Model and spend, then try again.";
  if (/timeout/i.test(t)) return "The model took too long. Try again in a moment.";
  if (/guard|protected/i.test(t)) return "The model tried to edit a locked file. That change was blocked.";
  if (/json/i.test(t) && /invalid/i.test(t)) return "The model returned a response we could not read. Retry the build.";
  return t || "Something went wrong while building.";
}

function showError(text) {
  const el = $("plain-error");
  el.hidden = false;
  el.textContent = plainError(text);
}

function handle(ev) {
  const type = ev.type;
  if (type === "stage") {
    if (ev.name === "spec" && ev.status === "start") setBuildStep("understand");
    if (ev.name === "file_ops" && ev.status === "start") setBuildStep("designing");
    if (ev.name === "gate" && ev.status === "start") setBuildStep("checks");
    const label = {
      design: "Sketching three looks…",
      prepare: "Opening the app shell…",
      spec: "Understanding your idea…",
      file_ops: "Designing the screens…",
      gate: "Running store checks…",
    }[ev.name] || ev.name;
    if (ev.status === "start") ticker(label, "busy");
    else if (ev.status === "ok") ticker(ev.app_name ? `${ev.app_name} is taking shape` : `${ev.name} ready`, "ok");
    else {
      ticker(`${ev.name} failed`, "fail");
      showError(ev.detail || ev.error || `${ev.name} failed`);
    }
    log(`${ev.run_id} · ${ev.name} ${ev.status}`, ev.status === "fail" ? "fail" : "ok");
  } else if (type === "pilot_call") {
    if (ev.status === "ok") {
      addCost(ev.est_cost_usd || 0);
      addTokens(ev.input_tokens, ev.output_tokens);
      log(`${ev.stage} ok`, "ok");
    } else if (ev.status === "start") {
      ticker("Talking to the model…", "busy");
    } else if (ev.status === "error") {
      ticker(plainError(ev.error), "fail");
      showError(ev.error);
      log(`${ev.stage} error: ${ev.error}`, "fail");
    }
  } else if (type === "guard") {
    ticker("Blocked a protected file", "fail");
    log(`blocked ${ev.code}: ${ev.path || ""}`, "fail");
  } else if (type === "file") {
    setBuildStep("writing");
    files.set(ev.path, ev.preview || "");
    const li = document.createElement("li");
    li.textContent = `${ev.op} ${ev.path}`;
    li.addEventListener("click", () => {
      $("file-view").textContent = files.get(ev.path) || "";
    });
    $("files").appendChild(li);
  } else if (type === "preflight") {
    const status = String(ev.status || "").split(".").pop();
    appendRow($("evidence-preflight"), ev.check_id, status, ev.message || status);
    $("evidence").hidden = false;
  } else if (type === "repair") {
    repairSeen = Math.max(repairSeen, Number(ev.round) || 0);
    setBuildStep("fixing");
    ticker(`Fixing issues (round ${ev.round})…`, "busy");
    log(`repair round ${ev.round}`, "fail");
  } else if (type === "preview") {
    showPreview(ev.run_id, ev.url, ev.mode, ev.kind);
    if (ev.kind === "skin") ticker("Draft look on the phone — still writing screens…", "busy");
    if (ev.kind === "web") {
      skeletonPhone(false);
      ticker("Live Flutter preview on the phone", "ok");
    }
  } else if (type === "direction") {
    showDirection(ev);
  } else if (type === "picked") {
    enableBuild(true);
    ticker(`Using ${ev.name}. Build the app when you’re ready.`, "ok");
    for (const wrap of document.querySelectorAll(".phone-wrap")) wrap.classList.remove("picked");
    const card = document.getElementById(`dir-${ev.n}`);
    if (card) card.classList.add("picked");
  } else if (type === "done") {
    log(`${ev.run_id} done ${ev.ok ? "ok" : "fail"}`, ev.ok ? "ok" : "fail");
    if (ev.preview) showPreview(ev.run_id, ev.preview, ev.mode, ev.kind);
    if (ev.ok) {
      setBuildStep("ready");
      skeletonPhone(false);
      ticker("Your app is on the phone.", "ok");
      setStep("check");
    } else {
      ticker(plainError(ev.error || "Build failed"), "fail");
      showError(ev.error || "Build failed");
      setBuildStep(currentBuildStep || "checks", { fail: true });
    }
    stopElapsed();
    const wrap = document.getElementById(`phone-${ev.run_id}`);
    if (wrap) {
      const slot = wrap.querySelector(".badge-slot");
      if (slot) slot.replaceChildren(badge(!!ev.ok));
    }
    fillEvidence(ev.run_id);
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
    const card = phoneCard({ id: `dir-${i}`, label: `Look ${i}`, small: true, useLook: true });
    $("phones").appendChild(card);
    setScreen(card.querySelector(".screen"), waiting("Designing…"));
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
  setUsedModel(pilot);
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

function isEmptySweep(md) {
  return !md || /passed 0\/0|0\/0/.test(md) || !/\|\s*(pass|quality_fail|infra_fail)/i.test(md);
}

async function showHarnessReport() {
  $("compare-results").hidden = false;
  const empty = $("compare-empty");
  const table = $("compare-table");
  empty.hidden = true;
  table.innerHTML = "";
  try {
    const res = await fetch("/api/results");
    if (!res.ok) {
      empty.hidden = false;
      empty.textContent = "No sweep results exist yet.";
      return;
    }
    const md = await res.text();
    if (isEmptySweep(md)) {
      empty.hidden = false;
      empty.textContent = "No sweep results exist yet.";
      return;
    }
    empty.hidden = true;
    renderMarkdownTables(md, table);
  } catch (err) {
    empty.hidden = false;
    empty.textContent = "No sweep results exist yet.";
    log(String(err), "fail");
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
  enableBuild(true);
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

async function useDefaultLook() {
  if (designRun) {
    const card = document.getElementById("dir-1");
    if (card) await pickDirection(1, card);
  }
  enableBuild(true);
  ticker("Using the default look. Build when you’re ready.", "ok");
  setStep("looks");
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
    if (!lookChosen) {
      ticker("Choose a look first, or use the default look.", "fail");
      return;
    }
    body.mode = extra.mode || "harness";
    body.run_id = extra.run_id || slug(body.mode);
    if (designRun) body.choice_from = designRun;
    active.clear();
    active.add(body.run_id);
    resetSession();
    setUsedModel(body.pilot);
    $("phones").innerHTML = "";
    const card = phoneCard({ id: `phone-${body.run_id}`, label: body.mode, small: false });
    $("phones").appendChild(card);
    setScreen(card.querySelector(".screen"), waiting("Building your app…"));
    skeletonPhone(true);
    $("build-stepper").hidden = false;
    $("build-stats").hidden = false;
    buildStartedAt = Date.now();
    setBuildStep("understand");
    setStep("build");
    ticker("Building the app onto the phone…", "busy");
  }
  const started = await api(`/api/${kind}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!started.ok) {
    ticker(plainError(started.error || "failed to start"), "fail");
    showError(started.error || "failed to start");
    log(started.error || "failed to start", "fail");
    skeletonPhone(false);
    return;
  }
  log(`started ${kind} ${started.run_id || (started.run_ids || []).join(",")}`);
}

function slug(prefix) {
  return `${prefix}-${Date.now().toString(36).slice(-5)}`;
}

$("btn-design").addEventListener("click", () => run("design", { run_id: slug("d") }));
$("btn-build").addEventListener("click", () => run("build", { mode: "harness" }));
$("btn-default-look").addEventListener("click", () => useDefaultLook());
$("btn-compare").addEventListener("click", () => showHarnessReport());

document.querySelectorAll("[data-hash]").forEach((btn) => {
  btn.addEventListener("click", () => applyTourHash(btn.dataset.hash));
});

document.querySelectorAll("#steps li").forEach((li) => {
  li.addEventListener("click", () => {
    const name = li.dataset.step;
    setStep(name);
    if (name === "check") $("evidence").hidden = false;
    if (name === "ship") $("ship-panel").hidden = false;
  });
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
