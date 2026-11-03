const $ = (id) => document.getElementById(id);
const files = new Map();
let cost = 0;
let designRun = null;
let es = null;

function log(text, cls) {
  const li = document.createElement("li");
  if (cls) li.className = cls;
  li.textContent = text;
  $("log").prepend(li);
}

function addCost(value) {
  if (typeof value === "number" && !Number.isNaN(value)) cost += value;
  $("cost").textContent = `$${cost.toFixed(4)}`;
}

function setScreen(el, inner) {
  el.innerHTML = "";
  el.appendChild(inner);
}

function iframe(url) {
  const frame = document.createElement("iframe");
  frame.src = url;
  frame.title = "app preview";
  frame.setAttribute("sandbox", "allow-scripts allow-same-origin allow-forms");
  return frame;
}

function swatch(color, label) {
  const d = document.createElement("div");
  d.className = "swatch";
  d.style.background = color || "#333";
  d.innerHTML = `<span>${label || ""}</span>`;
  return d;
}

function phoneCard({ id, label, small }) {
  const wrap = document.createElement("div");
  wrap.className = "phone-wrap";
  wrap.id = id;
  wrap.innerHTML = `
    <p class="phone-label">${label}<span class="badge-slot"></span></p>
    <div class="phone${small ? " small" : ""}">
      <div class="island"></div>
      <div class="screen"></div>
      <div class="home"></div>
    </div>`;
  return wrap;
}

function badge(ok) {
  const span = document.createElement("span");
  span.className = `badge ${ok ? "ok" : "fail"}`;
  span.textContent = ok ? "pass" : "fail";
  return span;
}

function showMainEmpty(text) {
  $("phones").innerHTML = "";
  const card = phoneCard({ id: "phone-main", label: "preview", small: false });
  $("phones").appendChild(card);
  setScreen(card.querySelector(".screen"), (() => {
    const p = document.createElement("p");
    p.className = "empty";
    p.textContent = text;
    return p;
  })());
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
    handle(ev);
  };
}

function handle(ev) {
  const type = ev.type;
  if (type === "stage") {
    log(`${ev.run_id} · ${ev.name} ${ev.status}`, ev.status === "fail" ? "fail" : "ok");
  } else if (type === "pilot_call") {
    if (ev.status === "ok") {
      addCost(ev.est_cost_usd || 0);
      log(`${ev.stage} · ${ev.latency_ms}ms · $${Number(ev.est_cost_usd || 0).toFixed(4)} in ${ev.input_tokens} / cache ${ev.cached_tokens}`, "ok");
    } else if (ev.status === "start") {
      log(`${ev.stage} · calling ${ev.model}…`);
    } else if (ev.status === "error") {
      log(`${ev.stage} error: ${ev.error}`, "fail");
    }
  } else if (type === "guard") {
    log(`blocked ${ev.code}: ${ev.path || ""} ${ev.message || ""}`, "fail");
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
    li.className = ev.status;
    li.textContent = `${ev.check_id} · ${ev.status}`;
  } else if (type === "repair") {
    log(`repair round ${ev.round}`, "fail");
  } else if (type === "preview") {
    showPreview(ev.run_id, ev.url, ev.mode);
  } else if (type === "direction") {
    showDirection(ev);
  } else if (type === "picked") {
    log(`picked ${ev.name}`, "ok");
  } else if (type === "done") {
    log(`${ev.run_id} done ${ev.ok ? "ok" : "fail"}`, ev.ok ? "ok" : "fail");
    if (ev.preview) showPreview(ev.run_id, ev.preview, ev.mode);
    else if (ev.kind !== "design") {
      showStatus(
        ev.run_id,
        ev.ok ? "built — turn on web preview for the live phone" : (ev.error || "failed"),
        ev.mode,
        ev.ok,
      );
    }
  } else if (type === "choice") {
    log(`tokens from ${ev.name}`, "ok");
  }
}

function showStatus(runId, text, mode, ok) {
  const wrap = ensurePhone(runId, mode);
  const slot = wrap.querySelector(".badge-slot");
  if (slot) slot.replaceChildren(badge(!!ok));
  const p = document.createElement("p");
  p.className = "empty";
  p.textContent = text;
  setScreen(wrap.querySelector(".screen"), p);
}

function ensurePhone(runId, mode) {
  let wrap = document.getElementById(`phone-${runId}`);
  if (!wrap) {
    const compare = runId.endsWith("-harness") || runId.endsWith("-bare");
    if (!compare) $("phones").innerHTML = "";
    wrap = phoneCard({
      id: `phone-${runId}`,
      label: mode || runId,
      small: compare,
    });
    $("phones").appendChild(wrap);
  }
  return wrap;
}

function showPreview(runId, url, mode) {
  const wrap = ensurePhone(runId, mode);
  const slot = wrap.querySelector(".badge-slot");
  if (slot) slot.replaceChildren();
  setScreen(wrap.querySelector(".screen"), iframe(url));
}

function showDirection(ev) {
  let wrap = document.getElementById(`dir-${ev.index}`);
  if (!wrap) {
    if (ev.index === 1) $("phones").innerHTML = "";
    wrap = phoneCard({ id: `dir-${ev.index}`, label: `${ev.index}. ${ev.name}`, small: true });
    wrap.style.cursor = "pointer";
    wrap.addEventListener("click", async () => {
      if (!designRun) return;
      const picked = await api("/api/pick", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ run_id: designRun, n: ev.index }),
      });
      if (!picked.ok) {
        log(picked.error || "pick failed", "fail");
        return;
      }
      log(`using ${picked.choice?.direction?.name || ev.name} for the next build`, "ok");
    });
    $("phones").appendChild(wrap);
  }
  wrap.querySelector(".phone-label").childNodes[0].textContent = `${ev.index}. ${ev.name}`;
  if (ev.preview) {
    setScreen(wrap.querySelector(".screen"), iframe(ev.preview));
  } else {
    setScreen(wrap.querySelector(".screen"), swatch(ev.primary, ev.name));
  }
}

async function run(kind, extra) {
  const body = { ...payload(), ...extra };
  if (kind === "design") {
    body.run_id = body.run_id || slug("design");
    designRun = body.run_id;
  }
  if (kind === "build") {
    body.mode = extra.mode || "harness";
    body.run_id = extra.run_id || slug(body.mode);
    if (designRun) body.choice_from = designRun;
  }
  if (kind === "compare") {
    body.run_id = extra.run_id || slug("cmp");
    $("phones").innerHTML = "";
    if (designRun) body.choice_from = designRun;
  }
  const started = await api(`/api/${kind}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!started.ok) {
    log(started.error || "failed to start", "fail");
    return;
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

boot().catch((err) => log(String(err), "fail"));
