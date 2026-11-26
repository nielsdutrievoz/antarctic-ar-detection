"use strict";

/* ------------------------------------------------------------------ textes */
const I18N = {
  fr: {
    title: "Rivières atmosphériques en Antarctique",
    doc_title: "Rivières atmosphériques Antarctique | Niels Dutrievoz",
    back: "← Site principal",
    home: "/fr/",
    eyebrow: "Outil de suivi · prévision ECMWF",
    lead: "Situation synoptique autour de l'Antarctique et rivières atmosphériques prévues pour les cinq prochains jours, mise à jour quatre fois par jour, et retour sur des événements passés.",
    event_label: "Événement",
    sites_label: "Stations",
    legend_label: "Légende",
    footer: "Niels Dutrievoz · Données ECMWF (CC-BY-4.0) et Copernicus ERA5 · <a href=\"https://github.com/nielsdutrievoz/antarctic-ar-detection\">Code source</a>",
    tab_forecast: "Prévision",
    tab_events: "Événements passés",
    tab_method: "Méthode",
    refs_label: "Références",
    method_more: "Méthode détaillée, références et catalogue →",
    download_image: "Télécharger l'image",
    download_gif: "Télécharger l'animation (GIF)",
    sites_title: "AR aux sites",
    sites_help: "Case colorée : l'algorithme choisi détecte un AR à moins de 100 km du site. Clique sur une case pour afficher la carte.",
    algo_label: "Algorithme",
    legend_title: "Lecture des cartes",
    legend_ivt: "<b>Couleurs</b> : transport intégré de vapeur d'eau (IVT), kg m<sup>-1</sup> s<sup>-1</sup>. Flèches là où IVT ≥ 250.",
    legend_msl: "<b>Traits noirs</b> : pression au niveau de la mer, tous les 4 hPa (masquée sur le haut plateau).",
    legend_ar: {
      wille_vivt: "<b>Contour cyan</b> : AR détecté par le transport de vapeur vers le pôle (Wille et al. 2021). Le cercle pointillé marque la limite sud de la détection (85°S).",
      wille_iwv: "<b>Contour vert</b> : AR détecté par la vapeur d'eau totale, quel que soit le sens du transport (Wille et al. 2019). Le cercle pointillé marque la limite sud de la détection (85°S).",
      dark: "<b>Contour rose</b> : AR détecté par DARK (Buffet et al. 2026) : IVT total, axe courbe d'au moins 2000 km, jusqu'au pôle.",
      none: "Aucun algorithme de détection disponible pour le moment.",
    },
    method_title: "Méthode",
    method_text: "Prévisions : ECMWF IFS déterministe (HRES, 0.25°), données ouvertes ECMWF (CC-BY-4.0). Événements passés : réanalyse ERA5 (Copernicus). Trois algorithmes au choix : Wille vIVT (2021), Wille IWV (2019) et DARK (Buffet et al. 2026). Produit expérimental, sans garantie.",
    detection_on: (p) => `Seuils : 98e percentile ERA5 ${p}.`,
    detection_off: "Seuils climatologiques ERA5 pas encore calculés : les AR ne sont pas encore détectées.",
    no_data: "Aucune carte disponible pour le moment.",
    run_info: (model, run, gen) => `${model} · run du ${run} · mis à jour ${gen}`,
    event_info: "Réanalyse ERA5, toutes les 6 h",
    no_events: "Les animations des événements passés sont en préparation.",
    no_ar: "pas d'AR",
    ar_from: (s) => `AR dès ${s}`,
    ar: "AR",
    play: "Lecture", pause: "Pause", prev: "Précédente", next: "Suivante",
    map_alt: "Carte : IVT, pression au niveau de la mer et rivières atmosphériques",
    reference: "Référence :",
  },
  en: {
    title: "Atmospheric rivers in Antarctica",
    doc_title: "Antarctic atmospheric rivers | Niels Dutrievoz",
    back: "← Main site",
    home: "/",
    eyebrow: "Monitoring tool · ECMWF forecast",
    lead: "Synoptic situation around Antarctica and atmospheric rivers forecast for the next five days, updated four times a day, plus a look back at past events.",
    event_label: "Event",
    sites_label: "Stations",
    legend_label: "Legend",
    footer: "Niels Dutrievoz · Data: ECMWF (CC-BY-4.0) and Copernicus ERA5 · <a href=\"https://github.com/nielsdutrievoz/antarctic-ar-detection\">Source code</a>",
    tab_forecast: "Forecast",
    tab_events: "Past events",
    tab_method: "Method",
    refs_label: "References",
    method_more: "Detailed method, references and catalogue →",
    download_image: "Download image",
    download_gif: "Download animation (GIF)",
    sites_title: "ARs at sites",
    sites_help: "Coloured cell: the selected algorithm detects an AR within 100 km of the site. Click a cell to show that map.",
    algo_label: "Algorithm",
    legend_title: "Reading the maps",
    legend_ivt: "<b>Colours</b>: integrated water vapour transport (IVT), kg m<sup>-1</sup> s<sup>-1</sup>. Arrows where IVT ≥ 250.",
    legend_msl: "<b>Black lines</b>: mean sea-level pressure every 4 hPa (masked over the high plateau).",
    legend_ar: {
      wille_vivt: "<b>Cyan contour</b>: AR detected from poleward vapour transport (Wille et al. 2021). The dashed circle marks the southern detection limit (85°S).",
      wille_iwv: "<b>Green contour</b>: AR detected from total water vapour, whatever the transport direction (Wille et al. 2019). The dashed circle marks the southern detection limit (85°S).",
      dark: "<b>Pink contour</b>: AR detected by DARK (Buffet et al. 2026): total IVT, curved axis of at least 2000 km, up to the pole.",
      none: "No detection algorithm available yet.",
    },
    method_title: "Method",
    method_text: "Forecasts: ECMWF IFS deterministic (HRES, 0.25°), ECMWF open data (CC-BY-4.0). Past events: ERA5 reanalysis (Copernicus). Three algorithms to choose from: Wille vIVT (2021), Wille IWV (2019) and DARK (Buffet et al. 2026). Experimental product, no warranty.",
    detection_on: (p) => `Thresholds: ERA5 98th percentile ${p}.`,
    detection_off: "ERA5 climatological thresholds not computed yet: ARs are not detected yet.",
    no_data: "No maps available at the moment.",
    run_info: (model, run, gen) => `${model} · run ${run} · updated ${gen}`,
    event_info: "ERA5 reanalysis, every 6 h",
    no_events: "Past-event animations are being prepared.",
    no_ar: "no AR",
    ar_from: (s) => `AR from ${s}`,
    ar: "AR",
    play: "Play", pause: "Pause", prev: "Previous", next: "Next",
    map_alt: "Map: IVT, mean sea-level pressure and atmospheric rivers",
    reference: "Reference:",
  },
};

/* ------------------------------------------------------------------ état */
const $ = (id) => document.getElementById(id);
const state = { lang: "fr", tab: "forecast", eventId: null, current: 0, timer: null, algo: null };
const ALGOS = {
  wille_vivt: { label: "Wille vIVT", color: "#00b8d4" },
  wille_iwv: { label: "Wille IWV", color: "#64dd17" },
  dark: { label: "DARK", color: "#ff2bd6" },
};
let forecast = null;          // manifest.json
let events = [];              // events/events.json
let view = { frames: [], sites: [] };   // ce que le visualiseur affiche

const parseZ = (s) => new Date(s.replace(/Z$/, "") + (s.length <= 14 ? ":00:00Z" : ":00Z"));
const fmtDate = (d, withYear = false) => new Intl.DateTimeFormat(state.lang === "fr" ? "fr-CH" : "en-GB", {
  weekday: "short", day: "2-digit", month: withYear ? "short" : "2-digit",
  ...(withYear ? { year: "numeric" } : {}), hour: "2-digit", minute: "2-digit", timeZone: "UTC",
}).format(d) + " UTC";
const t = (k) => I18N[state.lang][k];

/* ------------------------------------------------------------------ démarrage */
async function init() {
  readUrl();
  [forecast, events] = await Promise.all([
    getJson("data/manifest.json"), getJson("events/events.json").then((e) => e || []),
  ]);
  document.querySelectorAll("[data-lang]").forEach((b) => (b.onclick = () => { state.lang = b.dataset.lang; save(); render(); }));
  document.querySelectorAll("[data-tab]").forEach((b) => (b.onclick = () => { state.tab = b.dataset.tab; state.current = 0; stop(); save(); render(); }));
  $("slider").addEventListener("input", () => show(+$("slider").value));
  $("prev").onclick = () => show(state.current - 1);
  $("next").onclick = () => show(state.current + 1);
  $("play").onclick = toggle;
  $("dl-image").onclick = downloadImage;
  document.querySelectorAll("[data-goto]").forEach((a) => (a.onclick = (e) => {
    e.preventDefault(); state.tab = a.dataset.goto; stop(); save(); render(); window.scrollTo({ top: 0, behavior: "smooth" });
  }));
  document.addEventListener("keydown", (e) => {
    if (["INPUT", "SELECT", "TEXTAREA"].includes(e.target.tagName) && e.target.type !== "range") return;
    if (e.key === "ArrowLeft") { show(state.current - 1); e.preventDefault(); }
    if (e.key === "ArrowRight") { show(state.current + 1); e.preventDefault(); }
    if (e.key === " " && e.target.tagName !== "BUTTON") { toggle(); e.preventDefault(); }
  });
  window.addEventListener("hashchange", () => { readUrl(); render(); });
  render();
}

async function getJson(url) {
  try {
    const r = await fetch(`${url}?t=${Date.now()}`, { cache: "no-store" });
    return r.ok ? await r.json() : null;
  } catch { return null; }
}

/* URL : ?lang=en#events/2018-12-concordia  (langue mémorisée aussi localement) */
function readUrl() {
  const q = new URLSearchParams(location.search).get("lang");
  let stored = null;
  try { stored = localStorage.getItem("ar-lang"); } catch { /* navigation privée */ }
  const nav = (navigator.language || "fr").toLowerCase().startsWith("fr") ? "fr" : "en";
  state.lang = ["fr", "en"].includes(q) ? q : (stored || nav);
  const qa = new URLSearchParams(location.search).get("algo");
  let storedAlgo = null;
  try { storedAlgo = localStorage.getItem("ar-algo"); } catch { /* ignore */ }
  state.algo = qa in ALGOS ? qa : (storedAlgo in ALGOS ? storedAlgo : state.algo);
  const [tab, id] = location.hash.replace(/^#/, "").split("/");
  state.tab = ["events", "method"].includes(tab) ? tab : "forecast";
  if (id) state.eventId = decodeURIComponent(id);
}

function save() {
  try { localStorage.setItem("ar-lang", state.lang); if (state.algo) localStorage.setItem("ar-algo", state.algo); } catch { /* ignore */ }
  const url = new URL(location.href);
  url.searchParams.set("lang", state.lang);
  if (state.algo) url.searchParams.set("algo", state.algo);
  url.hash = state.tab === "events" && state.eventId ? `events/${state.eventId}` : state.tab;
  history.replaceState(null, "", url);
}

/* ------------------------------------------------------------------ rendu */
function render() {
  const L = I18N[state.lang];
  document.documentElement.lang = state.lang;
  document.title = L.doc_title;
  document.querySelectorAll("[data-i18n]").forEach((el) => (el.textContent = L[el.dataset.i18n]));
  document.querySelectorAll("[data-i18n-html]").forEach((el) => (el.innerHTML = L[el.dataset.i18nHtml]));
  document.querySelectorAll("[data-lang]").forEach((b) => b.setAttribute("aria-pressed", b.dataset.lang === state.lang));
  document.querySelectorAll("[data-tab]").forEach((b) => b.setAttribute("aria-selected", b.dataset.tab === state.tab));
  $("prev").setAttribute("aria-label", L.prev);
  $("next").setAttribute("aria-label", L.next);
  $("map").alt = L.map_alt;
  $("home-link").href = L.home;
  $("back-link").href = L.home;
  $("method").textContent = forecast && (forecast.algorithms || []).length ? L.detection_on(forecast.period) : (forecast ? L.detection_off : "");

  document.querySelectorAll("[data-only]").forEach((el) => (el.hidden = el.dataset.only !== state.lang));
  const isMethod = state.tab === "method";
  $("maps-page").hidden = isMethod;
  $("method-page").hidden = !isMethod;
  if (isMethod) { stop(); return; }
  if (state.tab === "forecast") renderForecast(); else renderEvents();
  setPlayLabel();
}

function renderForecast() {
  $("event-picker").hidden = true;
  $("event-about").hidden = true;
  if (!forecast) { $("info").textContent = t("no_data"); view = { frames: [], sites: [] }; return clearViewer(); }
  const algo = pickAlgo(forecast.algorithms || []);
  const gif = forecast.gif && (forecast.gif[algo || "base"] || {})[state.lang];
  setGif(gif);
  $("info").textContent = t("run_info")(forecast.model, fmtDate(parseZ(forecast.run), true), forecast.generated.replace("T", " "));
  view = {
    sites: forecast.sites,
    frames: forecast.frames.map((f) => ({
      url: `maps/${state.lang}/${f.file}`,
      layer: algo ? `maps/${state.lang}/${algo}/${f.file}` : null,
      label: `+${f.step} h · ${fmtDate(parseZ(f.valid))}`,
      short: `+${f.step} h`,
      ar_sites: (f.ar || {})[algo] || [],
      dlname: `antarctic_ar_${forecast.run.replace(/[-:TZ]/g, "")}_${String(f.step).padStart(3, "0")}h_${algo || "base"}_${state.lang}.png`,
    })),
  };
  setupViewer();
}

function renderEvents() {
  $("event-picker").hidden = false;
  $("info").textContent = t("event_info");
  const picker = $("event-picker");
  picker.innerHTML = "";
  if (!events.length) { $("info").textContent = t("no_events"); $("event-about").hidden = true; setGif(null); $("algo-picker").innerHTML = ""; view = { frames: [], sites: [] }; return clearViewer(); }
  if (!events.some((e) => e.id === state.eventId)) state.eventId = events[0].id;
  for (const e of events) {
    const b = document.createElement("button");
    b.className = "event-card";
    b.setAttribute("aria-pressed", e.id === state.eventId);
    b.textContent = e.title[state.lang];
    b.onclick = () => { state.eventId = e.id; state.current = 0; stop(); save(); render(); };
    picker.appendChild(b);
  }
  const ev = events.find((e) => e.id === state.eventId);
  $("event-about").hidden = false;
  $("event-title").textContent = ev.title[state.lang];
  $("event-desc").textContent = ev.description[state.lang];
  const ref = ev.reference;
  $("event-ref").innerHTML = "";
  if (ref && ref.text) {
    $("event-ref").append(`${t("reference")} `);
    if (ref.url) {
      const a = document.createElement("a");
      a.href = ref.url; a.textContent = ref.text; a.rel = "noopener"; a.target = "_blank";
      $("event-ref").appendChild(a);
    } else $("event-ref").append(ref.text);
  }
  const algo = pickAlgo(ev.algorithms || []);
  setGif(algo && ev.gif[algo] ? `events/${ev.gif[algo][state.lang]}` : null);
  view = {
    sites: forecast ? forecast.sites : [],
    frames: ev.frames.map((f) => ({
      url: `events/${ev.id}/${state.lang}/${f.file}`,
      layer: algo ? `events/${ev.id}/${state.lang}/${algo}/${f.file}` : null,
      label: fmtDate(parseZ(f.time), true),
      short: fmtDate(parseZ(f.time)).replace(/ UTC$/, ""),
      ar_sites: (f.ar || {})[algo] || [],
      dlname: `antarctic_ar_${ev.id}_${f.file.replace(".png", "")}_${algo || "base"}_${state.lang}.png`,
    })),
  };
  setupViewer();
}

/* choix de l'algorithme parmi ceux disponibles pour ce jeu de cartes */
function pickAlgo(available) {
  if (!available.includes(state.algo)) state.algo = available[0] || null;
  const box = $("algo-picker");
  box.innerHTML = "";
  if (available.length) {
    const lab = document.createElement("span");
    lab.className = "algo-label";
    lab.textContent = t("algo_label");
    box.appendChild(lab);
  }
  for (const a of available) {
    const b = document.createElement("button");
    b.className = "algo";
    b.setAttribute("aria-pressed", a === state.algo);
    b.style.setProperty("--dot", ALGOS[a].color);
    b.textContent = ALGOS[a].label;
    b.onclick = () => { state.algo = a; save(); render(); };
    box.appendChild(b);
  }
  $("legend-ar").innerHTML = t("legend_ar")[state.algo || "none"];
  return state.algo;
}

function setGif(href) {
  $("dl-gif").hidden = !href;
  if (href) { $("dl-gif").href = href; $("dl-gif").setAttribute("download", href.split("/").pop()); }
}

/* image téléchargée = fond + calque de l'algorithme, composés dans un canvas */
async function downloadImage(e) {
  e.preventDefault();
  const f = view.frames[state.current];
  if (!f) return;
  const load = (u) => fetch(u).then((r) => r.blob()).then((b) => createImageBitmap(b));
  const [base, layer] = await Promise.all([load(f.url), f.layer ? load(f.layer) : null]);
  const c = document.createElement("canvas");
  c.width = base.width; c.height = base.height;
  const ctx = c.getContext("2d");
  ctx.drawImage(base, 0, 0);
  if (layer) ctx.drawImage(layer, 0, 0);
  c.toBlob((blob) => {
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = f.dlname;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 5000);
  }, "image/png");
}

function clearViewer() {
  $("map").removeAttribute("src");
  $("layer").hidden = true;
  $("label").textContent = "";
  $("sites").innerHTML = "";
  $("dl-image").removeAttribute("href");
}

function setupViewer() {
  const n = view.frames.length;
  $("slider").max = Math.max(0, n - 1);
  state.current = Math.min(state.current, n - 1);
  view.frames.forEach((f) => { for (const u of [f.url, f.layer]) if (u) { const im = new Image(); im.src = u; } });   // préchargement
  buildSites();
  show(state.current);
}

function buildSites() {
  const box = $("sites");
  box.innerHTML = "";
  const frames = view.frames;
  for (const s of view.sites) {
    const color = state.algo ? ALGOS[state.algo].color : "var(--ar)";
    const hits = frames.filter((f) => f.ar_sites.includes(s.name));
    const div = document.createElement("div");
    div.className = "site";
    const head = document.createElement("div");
    head.className = "site-name";
    const name = document.createElement("span");
    name.textContent = s.name;
    const status = document.createElement("span");
    if (hits.length) { status.className = "badge"; status.textContent = t("ar_from")(hits[0].short); }
    else { status.className = "muted small"; status.textContent = t("no_ar"); }
    head.append(name, status);
    const strip = document.createElement("div");
    strip.className = "strip";
    frames.forEach((f, i) => {
      const b = document.createElement("button");
      const ar = f.ar_sites.includes(s.name);
      if (ar) { b.classList.add("ar"); b.style.background = color; }
      b.title = `${f.label}${ar ? " · " + t("ar") : ""}`;
      b.setAttribute("aria-label", b.title);
      b.dataset.i = i;
      b.onclick = () => show(i);
      strip.appendChild(b);
    });
    const axis = document.createElement("div");
    axis.className = "axis";
    if (frames.length) axis.innerHTML = `<span>${frames[0].short}</span><span>${frames[frames.length - 1].short}</span>`;
    div.append(head, strip, axis);
    box.appendChild(div);
  }
}

function show(i) {
  const n = view.frames.length;
  if (!n) return;
  state.current = (i + n) % n;
  const f = view.frames[state.current];
  $("map").src = f.url;
  $("layer").hidden = !f.layer;
  if (f.layer) $("layer").src = f.layer;
  $("slider").value = state.current;
  $("label").textContent = f.label;
  $("dl-image").href = f.url;
  document.querySelectorAll(".strip button").forEach((b) => b.classList.toggle("current", +b.dataset.i === state.current));
}

function toggle() { state.timer ? stop() : start(); }
function start() { state.timer = setInterval(() => show(state.current + 1), 700); setPlayLabel(); }
function stop() { clearInterval(state.timer); state.timer = null; setPlayLabel(); }
function setPlayLabel() {
  $("play").textContent = state.timer ? "❚❚" : "▶";
  $("play").setAttribute("aria-label", state.timer ? t("pause") : t("play"));
}

init();
