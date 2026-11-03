const $ = (id) => document.getElementById(id);
const files = new Map();
const active = new Set();
let cost = 0;
let designRun = null;
let es = null;

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
  addCost(0);
  files.clear();
  $("log").innerHTML = "";
  $("preflight").innerHTML = "";
  $("files").innerHTML = "";
  $("file-view").textContent = "Select a file.";
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

function iframe(url) {
  const frame = document.createElement("iframe");
  frame.src = url;
  frame.title = "app preview";
  frame.setAttribute("sandbox", "allow-scripts allow-same-origin allow-forms");
  return frame;
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
      design: "Designing three looks…",
      prepare: "Preparing the app shell…",
      spec: "Writing the spec…",
      file_ops: "Writing screens…",
      gate: "Checking the app…",
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
    let li = document.querySelector(`[data-check="${ev.check_id}"]`);
    if (!li) {
      li = document.createElement("li");
      li.dataset.check = ev.check_id;
      $("preflight").appendChild(li);
    }
    const status = String(ev.status || "").split(".").pop();
    li.className = status;
    li.textContent = `${ev.check_id} · ${status}`;
  } else if (type === "repair") {
    ticker(`Repairing (round ${ev.round})…`, "busy");
    log(`repair round ${ev.round}`, "fail");
  } else if (type === "preview") {
    showPreview(ev.run_id, ev.url, ev.mode);
    if (ev.kind === "skin") ticker("Preview of the look — writing screens…", "busy");
    if (ev.kind === "web") ticker("Live Flutter preview", "ok");
  } else if (type === "direction") {
    showDirection(ev);
  } else if (type === "picked") {
    ticker(`Using ${ev.name}. Hit Build.`, "ok");
    for (const wrap of document.querySelectorAll(".phone-wrap")) wrap.classList.remove("picked");
    const card = document.getElementById(`dir-${ev.n}`);
    if (card) card.classList.add("picked");
  } else if (type === "done") {
    log(`${ev.run_id} done ${ev.ok ? "ok" : "fail"}`, ev.ok ? "ok" : "fail");
    if (ev.preview) showPreview(ev.run_id, ev.preview, ev.mode);
    ticker(ev.ok ? "Ready" : (ev.error || "Failed"), ev.ok ? "ok" : "fail");
    const wrap = document.getElementById(`phone-${ev.run_id}`);
    if (wrap) {
      const slot = wrap.querySelector(".badge-slot");
      if (slot) slot.replaceChildren(badge(!!ev.ok));
    }
  } else if (type === "choice") {
    ticker(`Applying ${ev.name} colors`, "ok");
  }
}

function showPreview(runId, url, mode) {
  const wrap = ensurePhone(runId, mode);
  setScreen(wrap.querySelector(".screen"), iframe(url));
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
    const mode = id.endsWith("bare") ? "bare" : "harness";
    const card = phoneCard({ id: `phone-${id}`, label: mode, small: true });
    $("phones").appendChild(card);
    setScreen(card.querySelector(".screen"), waiting("Building…"));
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
  ticker(`Using ${name || "this look"}. Hit Build.`, "ok");
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
    ticker("Designing three looks…", "busy");
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
    ticker("Building…", "busy");
  }
  if (kind === "compare") {
    body.run_id = extra.run_id || slug("cmp");
    if (designRun) body.choice_from = designRun;
    resetSession();
    ticker("Building harness and bare side by side…", "busy");
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
