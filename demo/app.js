const $ = (id) => document.getElementById(id);

async function api(path, opts) {
  const res = await fetch(path, opts);
  const text = await res.text();
  try {
    return JSON.parse(text);
  } catch {
    throw new Error(text.slice(0, 200));
  }
}

async function loadIdeas() {
  const ideas = await api("/api/ideas");
  const box = $("ideas");
  box.innerHTML = "";
  for (const idea of ideas) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.textContent = idea.title;
    btn.addEventListener("click", () => {
      $("idea").value = idea.blurb;
      $("run_id").value = idea.id;
      for (const other of box.querySelectorAll("button")) other.classList.remove("active");
      btn.classList.add("active");
    });
    box.appendChild(btn);
  }
}

async function loadRuns() {
  const runs = await api("/api/runs");
  const ul = $("runs");
  ul.innerHTML = runs.length ? "" : "<li>None yet. Run a job.</li>";
  for (const run of runs) {
    const li = document.createElement("li");
    const bits = [`<strong>${run.id}</strong>`, run.kind || "", run.mode || "", run.pilot || ""];
    if (run.ok === true) bits.push("pass");
    if (run.ok === false) bits.push("fail");
    li.innerHTML = bits.filter(Boolean).join(" · ");
    if (run.gallery) {
      li.innerHTML += ` · <a href="/runs/${run.id}/gallery.html" target="_blank" rel="noreferrer">gallery</a>`;
    }
    if (run.ok !== undefined) {
      li.innerHTML += ` · <a href="/runs/${run.id}/result.json" target="_blank" rel="noreferrer">result.json</a>`;
    }
    ul.appendChild(li);
  }
}

function renderJob(job) {
  $("status").textContent = `${job.status} ${job.kind || ""} ${job.run_id || ""}`.trim();
  $("status").className = `status ${job.status || "idle"}`;
  $("out").textContent = JSON.stringify(job, null, 2);
  const links = $("links");
  links.innerHTML = "";
  const summary = job.summary || {};
  if (summary.gallery) {
    links.innerHTML += `<a href="${summary.gallery}" target="_blank" rel="noreferrer">Open gallery</a> `;
  }
  if (summary.result) {
    links.innerHTML += `<a href="${summary.result}" target="_blank" rel="noreferrer">Open result.json</a>`;
  }
}

let pollTimer = null;
async function poll() {
  const job = await api("/api/job");
  renderJob(job);
  if (job.status !== "running") {
    $("go").disabled = false;
    clearInterval(pollTimer);
    pollTimer = null;
    await loadRuns();
  }
}

$("form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const kind = $("kind").value;
  const payload = {
    idea: $("idea").value,
    pilot: $("pilot").value,
    mode: $("mode").value,
    run_id: $("run_id").value,
    max_usd: Number($("max_usd").value),
    build_web: $("build_web").checked,
  };
  $("go").disabled = true;
  const started = await api(`/api/${kind}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  renderJob({ status: started.ok ? "running" : "error", ...started });
  if (!started.ok) {
    $("go").disabled = false;
    return;
  }
  if (pollTimer) clearInterval(pollTimer);
  pollTimer = setInterval(poll, 800);
});

loadIdeas().catch((err) => {
  $("out").textContent = String(err);
});
loadRuns().catch(() => {});
poll().catch(() => {});
