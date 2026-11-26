"use strict";

const $ = (id) => document.getElementById(id);
const fmt = new Intl.DateTimeFormat("fr-CH", {
  weekday: "short", day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit", timeZone: "UTC",
});
const parseZ = (s) => new Date(s.replace(/Z$/, "") + (s.length <= 14 ? ":00:00Z" : ":00Z"));

let frames = [];
let current = 0;
let timer = null;

async function init() {
  let m;
  try {
    const r = await fetch(`data/manifest.json?t=${Date.now()}`, { cache: "no-store" });
    if (!r.ok) throw new Error(r.status);
    m = await r.json();
  } catch (e) {
    $("run").textContent = "Aucune carte disponible pour le moment.";
    return;
  }
  frames = m.frames;
  const run = parseZ(m.run);
  $("run").textContent = `${m.model} · run du ${fmt.format(run)} UTC · mis à jour ${m.generated.replace("T", " ")}`;
  $("method").textContent = m.detection
    ? `Détection : ${m.detection}.`
    : "Seuils climatologiques ERA5 pas encore calculés : les AR ne sont pas encore détectées.";

  const slider = $("slider");
  slider.max = frames.length - 1;
  slider.addEventListener("input", () => show(+slider.value));
  $("prev").onclick = () => show(current - 1);
  $("next").onclick = () => show(current + 1);
  $("play").onclick = toggle;
  document.addEventListener("keydown", (e) => {
    if (e.target.tagName === "INPUT" && e.target.type !== "range") return;
    if (e.key === "ArrowLeft") { show(current - 1); e.preventDefault(); }
    if (e.key === "ArrowRight") { show(current + 1); e.preventDefault(); }
    if (e.key === " ") { toggle(); e.preventDefault(); }
  });

  buildSites(m.sites);
  // précharge les images pour une animation fluide
  frames.forEach((f) => { const img = new Image(); img.src = f.file; });
  show(0);
}

function buildSites(sites) {
  const box = $("sites");
  box.innerHTML = "";
  for (const s of sites) {
    const hits = frames.filter((f) => f.ar_sites.includes(s.name));
    const div = document.createElement("div");
    div.className = "site";
    const first = hits.length ? `AR dès +${hits[0].step} h` : "pas d'AR";
    div.innerHTML = `<div class="site-name"><span>${escapeHtml(s.name)}</span>` +
      (hits.length ? `<span class="badge">${first}</span>` : `<span class="muted small">${first}</span>`) +
      `</div>`;
    const strip = document.createElement("div");
    strip.className = "strip";
    frames.forEach((f, i) => {
      const b = document.createElement("button");
      const ar = f.ar_sites.includes(s.name);
      if (ar) b.classList.add("ar");
      b.title = `+${f.step} h · ${fmt.format(parseZ(f.valid))} UTC${ar ? " · AR" : ""}`;
      b.setAttribute("aria-label", b.title);
      b.dataset.i = i;
      b.onclick = () => show(i);
      strip.appendChild(b);
    });
    div.appendChild(strip);
    const axis = document.createElement("div");
    axis.className = "axis";
    axis.innerHTML = `<span>+0 h</span><span>+${frames[frames.length - 1].step} h</span>`;
    div.appendChild(axis);
    box.appendChild(div);
  }
}

function show(i) {
  if (!frames.length) return;
  current = (i + frames.length) % frames.length;
  const f = frames[current];
  $("map").src = f.file;
  $("slider").value = current;
  $("label").textContent = `+${f.step} h · ${fmt.format(parseZ(f.valid))} UTC`;
  document.querySelectorAll(".strip button").forEach((b) => b.classList.toggle("current", +b.dataset.i === current));
}

function toggle() {
  if (timer) {
    clearInterval(timer); timer = null;
    $("play").textContent = "▶"; $("play").setAttribute("aria-label", "Lecture");
  } else {
    timer = setInterval(() => show(current + 1), 700);
    $("play").textContent = "❚❚"; $("play").setAttribute("aria-label", "Pause");
  }
}

function escapeHtml(s) {
  return s.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

init();
