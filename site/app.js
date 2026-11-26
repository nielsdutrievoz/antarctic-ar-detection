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
    tab_alert: "Alerte",
    alert_eyebrow: "Alerte par e-mail",
    alert_title: "Être prévenu quand un AR approche",
    alert_intro: "Choisis un lieu et un ou plusieurs algorithmes : tu recevras un e-mail dès qu'une rivière atmosphérique y est prévue dans les cinq prochains jours, avec l'animation de la situation synoptique autour de l'Antarctique.",
    f_email: "Adresse e-mail",
    f_where: "Lieu surveillé",
    f_station: "Station",
    f_coords: "Coordonnées",
    f_lat: "Latitude (°, négative au sud)",
    f_lon: "Longitude (°E, de −180 à 180)",
    f_radius: "Un AR est signalé s'il passe à moins de 100 km du lieu choisi.",
    f_algos: "Algorithme(s)",
    f_lang: "Langue des e-mails",
    f_consent: "J'accepte que mon adresse e-mail et le lieu choisi soient conservés uniquement pour l'envoi de ces alertes. Je peux me désinscrire à tout moment via le lien présent dans chaque e-mail.",
    f_submit: "S'inscrire à l'alerte",
    alert_where: "Lieu choisi",
    alert_how: "Fonctionnement",
    alert_steps: [
      "Après l'inscription, un e-mail de confirmation t'est envoyé : l'alerte n'est active qu'une fois le lien cliqué.",
      "À chaque nouvelle prévision (00 et 12 UTC), les algorithmes choisis sont appliqués au lieu surveillé.",
      "Un e-mail est envoyé quand un nouvel AR y est prévu : date d'arrivée, algorithme(s), animation de la situation synoptique et lien vers le site.",
      "Pas de nouvel e-mail tant que le même AR reste prévu.",
      "Produit expérimental de recherche, sans garantie : ne pas utiliser pour la sécurité des opérations de terrain.",
    ],
    err_email: "Adresse e-mail invalide.",
    err_where: "Coordonnées invalides : latitude entre −90 et −40°, longitude entre −180 et 180°.",
    err_algos: "Choisis au moins un algorithme.",
    err_consent: "Merci d'accepter la conservation des données pour recevoir les alertes.",
    wille_limit: "indisponible au sud de 85°S",
    pick_label: (name, lat, lon) => `${name ? name + " · " : ""}${lat}, ${lon}`,
    sub_soon: (sum) => `Inscription prête : ${sum}. Les inscriptions ouvrent très prochainement ; rien n'a été envoyé pour le moment.`,
    sub_ok: (email) => `C'est presque fini : un e-mail de confirmation a été envoyé à ${email}. Clique sur le lien qu'il contient pour activer l'alerte.`,
    sub_fail: "L'inscription n'a pas pu être enregistrée. Réessaie plus tard.",
    link_wait: "Traitement du lien…",
    link_confirmed: (p) => `Alerte activée pour ${p}. Tu recevras un e-mail dès qu'un AR y sera prévu.`,
    link_unsubscribed: (p) => `Désinscription effectuée pour ${p}. Tu ne recevras plus d'alerte pour ce lieu.`,
    link_fail: "Ce lien n'est pas valide ou a expiré.",
    station_groups: { peninsula: "Péninsule antarctique", east: "Antarctique de l'Est", west: "Antarctique de l'Ouest et mer de Ross", plateau: "Plateau" },
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
    tab_alert: "Alert",
    alert_eyebrow: "Email alert",
    alert_title: "Get notified when an AR is coming",
    alert_intro: "Choose a location and one or more algorithms: you will receive an email as soon as an atmospheric river is forecast there within the next five days, with an animation of the synoptic situation around Antarctica.",
    f_email: "Email address",
    f_where: "Location",
    f_station: "Station",
    f_coords: "Coordinates",
    f_lat: "Latitude (°, negative south)",
    f_lon: "Longitude (°E, −180 to 180)",
    f_radius: "An AR is reported when it passes within 100 km of the chosen location.",
    f_algos: "Algorithm(s)",
    f_lang: "Email language",
    f_consent: "I agree that my email address and the chosen location are stored only to send these alerts. I can unsubscribe at any time through the link in every email.",
    f_submit: "Subscribe to the alert",
    alert_where: "Selected location",
    alert_how: "How it works",
    alert_steps: [
      "After subscribing, you receive a confirmation email: the alert is only active once you click its link.",
      "With each new forecast (00 and 12 UTC), the selected algorithms are applied at your location.",
      "An email is sent when a new AR is forecast there: arrival time, algorithm(s), synoptic animation and a link to the site.",
      "No new email while the same AR remains forecast.",
      "Experimental research product, no warranty: do not use for field-operation safety.",
    ],
    err_email: "Invalid email address.",
    err_where: "Invalid coordinates: latitude between −90 and −40°, longitude between −180 and 180°.",
    err_algos: "Choose at least one algorithm.",
    err_consent: "Please accept data storage to receive alerts.",
    wille_limit: "unavailable south of 85°S",
    pick_label: (name, lat, lon) => `${name ? name + " · " : ""}${lat}, ${lon}`,
    sub_soon: (sum) => `Subscription ready: ${sum}. Subscriptions open very soon; nothing has been sent yet.`,
    sub_ok: (email) => `Almost done: a confirmation email was sent to ${email}. Click the link inside to activate the alert.`,
    sub_fail: "The subscription could not be saved. Please try again later.",
    link_wait: "Processing the link…",
    link_confirmed: (p) => `Alert activated for ${p}. You will receive an email as soon as an AR is forecast there.`,
    link_unsubscribed: (p) => `Unsubscribed from ${p}. You will no longer receive alerts for this location.`,
    link_fail: "This link is invalid or has expired.",
    station_groups: { peninsula: "Antarctic Peninsula", east: "East Antarctica", west: "West Antarctica and Ross Sea", plateau: "Plateau" },
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
/* Onglet Alerte : masqué tant que l'envoi des e-mails n'est pas en service. */
const ALERT_ENABLED = false;
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
  setupAlert();
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
  handleAlertLink();
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
  state.tab = ["events", "method", ...(ALERT_ENABLED ? ["alert"] : [])].includes(tab) ? tab : "forecast";
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
  document.querySelectorAll("[data-i18n-list]").forEach((el) => {
    el.replaceChildren(...L[el.dataset.i18nList].map((x) => Object.assign(document.createElement("li"), { textContent: x })));
  });
  document.querySelectorAll("[data-lang]").forEach((b) => b.setAttribute("aria-pressed", b.dataset.lang === state.lang));
  document.querySelectorAll("[data-tab]").forEach((b) => b.setAttribute("aria-selected", b.dataset.tab === state.tab));
  document.querySelector('[data-tab="alert"]').hidden = !ALERT_ENABLED;
  $("prev").setAttribute("aria-label", L.prev);
  $("next").setAttribute("aria-label", L.next);
  $("map").alt = L.map_alt;
  $("home-link").href = L.home;
  $("back-link").href = L.home;
  $("method").textContent = forecast && (forecast.algorithms || []).length ? L.detection_on(forecast.period) : (forecast ? L.detection_off : "");

  document.querySelectorAll("[data-only]").forEach((el) => (el.hidden = el.dataset.only !== state.lang));
  const isMethod = state.tab === "method", isAlert = state.tab === "alert";
  $("maps-page").hidden = isMethod || isAlert;
  $("method-page").hidden = !isMethod;
  $("alert-page").hidden = !isAlert;
  if (isAlert) { stop(); renderAlert(); return; }
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

/* ------------------------------------------------------------------ alerte */
/* Projet Supabase qui enregistre les inscriptions (supabase/schema.sql). La clé « publishable »
   est publique par conception : elle ne permet que d'ajouter une inscription et d'appeler les
   fonctions de confirmation / désinscription. Tant que l'URL est vide, le formulaire valide les
   champs et affiche un récapitulatif, sans rien envoyer. */
const SUPABASE_URL = "https://fdbiyqlglprakjyrhfzh.supabase.co";
const SUPABASE_KEY = "sb_publishable_6-bj3TwUbcU-AMnJgdWFiA_RqpkgLC4";
const WILLE_SOUTH = -85;

const STATIONS = [
  ["peninsula", "Carlini", -62.24, -58.67], ["peninsula", "King Sejong", -62.22, -58.79],
  ["peninsula", "Esperanza", -63.40, -56.98], ["peninsula", "Palmer", -64.77, -64.05],
  ["peninsula", "Vernadsky", -65.25, -64.26], ["peninsula", "Rothera", -67.57, -68.13],
  ["east", "Neumayer III", -70.67, -8.27], ["east", "Princess Elisabeth", -71.95, 23.35],
  ["east", "Syowa", -69.00, 39.58], ["east", "Mawson", -67.60, 62.87],
  ["east", "Davis", -68.58, 77.97], ["east", "Zhongshan", -69.37, 76.37],
  ["east", "Casey", -66.28, 110.53], ["east", "Dumont d'Urville", -66.66, 140.00],
  ["west", "Halley VI", -75.58, -26.66], ["west", "McMurdo", -77.85, 166.67],
  ["west", "Mario Zucchelli", -74.69, 164.11], ["west", "Byrd", -80.01, -119.40],
  ["plateau", "Concordia", -75.10, 123.35], ["plateau", "Vostok", -78.46, 106.84],
  ["plateau", "Dome Fuji", -77.32, 39.70], ["plateau", "Kohnen", -75.00, 0.07],
  ["plateau", "Amundsen-Scott (South Pole)", -90.0, 0.0],
];

/* Position d'un point sur les cartes du site : stéréographique polaire sud, longitude 0 en haut,
   cercle limité à 30°S. Géométrie des PNG (8 × 8,6 in, axes [0.02, 0.15, 0.96, 0.79]). */
const MAP_GEOM = { cx: 0.5, cy: 0.4550, rx: 0.42463, ry: 0.39500, latEdge: -30 };
function mapXY(lat, lon) {
  const k = (deg) => Math.tan(((90 + deg) / 2) * Math.PI / 180);
  const r = k(lat) / k(MAP_GEOM.latEdge), a = lon * Math.PI / 180;
  return [MAP_GEOM.cx + r * MAP_GEOM.rx * Math.sin(a), MAP_GEOM.cy - r * MAP_GEOM.ry * Math.cos(a)];
}

const alertState = { mode: "station", station: "Concordia", lang: null, algos: new Set(), touched: false };

function setupAlert() {
  const form = $("alert-form");
  form.querySelectorAll('input[name="a-mode"]').forEach((r) => (r.onchange = () => { alertState.mode = r.value; updateAlert(); }));
  form.querySelectorAll('input[name="a-lang"]').forEach((r) => (r.onchange = () => { alertState.lang = r.value; }));
  $("a-station").onchange = () => { alertState.station = $("a-station").value; updateAlert(); };
  ["a-lat", "a-lon"].forEach((id) => ($(id).oninput = updateAlert));
  $("a-email").oninput = () => alertState.touched && validateAlert();
  $("a-consent").onchange = () => alertState.touched && validateAlert();
  form.onsubmit = submitAlert;
}

function renderAlert() {
  const L = I18N[state.lang];
  if (!alertState.lang) alertState.lang = state.lang;
  document.querySelectorAll('input[name="a-lang"]').forEach((r) => (r.checked = r.value === alertState.lang));
  // stations, regroupées par secteur
  const sel = $("a-station");
  sel.replaceChildren(...Object.entries(L.station_groups).map(([g, label]) => {
    const og = document.createElement("optgroup");
    og.label = label;
    STATIONS.filter((x) => x[0] === g).forEach(([, name, lat, lon]) => {
      og.append(new Option(`${name} (${Math.abs(lat).toFixed(2)}°S, ${Math.abs(lon).toFixed(2)}°${lon < 0 ? "W" : "E"})`, name));
    });
    return og;
  }));
  sel.value = alertState.station;
  // fond de carte : première échéance de la prévision en cours
  const f = forecast && forecast.frames && forecast.frames[0];
  $("pickmap").hidden = !f;
  if (f) $("pickmap-img").src = `maps/${state.lang}/${f.file}`;
  $("pickmap-img").alt = L.map_alt;
  updateAlert();
}

function alertPoint() {
  if (alertState.mode === "station") {
    const s = STATIONS.find((x) => x[1] === alertState.station);
    return s ? { name: s[1], lat: s[2], lon: s[3] } : null;
  }
  const lat = parseFloat($("a-lat").value), lon = parseFloat($("a-lon").value);
  if (!Number.isFinite(lat) || !Number.isFinite(lon) || lat < -90 || lat > -40 || lon < -180 || lon > 180) return null;
  return { name: null, lat, lon };
}

function updateAlert() {
  const L = I18N[state.lang];
  $("a-station-box").hidden = alertState.mode !== "station";
  $("a-coords-box").hidden = alertState.mode !== "coords";
  const p = alertPoint();
  // algorithmes : ceux du site ; Wille ne détecte rien au sud de 85°S
  const box = $("a-algos");
  const avail = Object.keys(ALGOS);
  if (!alertState.algos.size) alertState.algos.add(state.algo && ALGOS[state.algo] ? state.algo : avail[0]);
  box.replaceChildren(...avail.map((a) => {
    const off = a.startsWith("wille") && p && p.lat < WILLE_SOUTH;
    if (off) alertState.algos.delete(a);
    const lab = document.createElement("label");
    lab.className = off ? "disabled" : "";
    const cb = Object.assign(document.createElement("input"), { type: "checkbox", value: a, checked: alertState.algos.has(a), disabled: off });
    cb.onchange = () => { cb.checked ? alertState.algos.add(a) : alertState.algos.delete(a); alertState.touched && validateAlert(); };
    const dot = Object.assign(document.createElement("span"), { className: "dot" });
    dot.style.background = ALGOS[a].color;
    lab.append(cb, dot, document.createTextNode(ALGOS[a].label + (off ? ` (${L.wille_limit})` : "")));
    return lab;
  }));
  // repère sur la carte
  const pin = $("pin");
  pin.hidden = !p;
  if (p) {
    const [x, y] = mapXY(p.lat, p.lon);
    pin.style.left = `${x * 100}%`;
    pin.style.top = `${y * 100}%`;
    $("pick-label").textContent = L.pick_label(p.name, `${Math.abs(p.lat).toFixed(2)}°S`,
      `${Math.abs(p.lon).toFixed(2)}°${p.lon < 0 ? "W" : "E"}`);
  } else {
    $("pick-label").textContent = "";
  }
  if (alertState.touched) validateAlert();
}

function showErr(id, msg, input) {
  $(id).hidden = !msg;
  $(id).textContent = msg || "";
  if (input) input.setAttribute("aria-invalid", msg ? "true" : "false");
  return !msg;
}

function validateAlert() {
  const L = I18N[state.lang];
  const email = $("a-email").value.trim();
  const okEmail = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email);
  const ok = [
    showErr("e-email", okEmail ? "" : L.err_email, $("a-email")),
    showErr("e-where", alertPoint() ? "" : L.err_where),
    showErr("e-algos", alertState.algos.size ? "" : L.err_algos),
    showErr("e-consent", $("a-consent").checked ? "" : L.err_consent),
  ];
  return ok.every(Boolean);
}

async function submitAlert(e) {
  e.preventDefault();
  alertState.touched = true;
  const L = I18N[state.lang];
  const res = $("a-result");
  res.hidden = true;
  res.className = "notice";
  if (!validateAlert()) return;
  const p = alertPoint();
  const sub = {
    email: $("a-email").value.trim(),
    station: p.name, lat: +p.lat.toFixed(2), lon: +p.lon.toFixed(2),
    algorithms: [...alertState.algos], lang: alertState.lang,
  };
  if ($("a-website").value) return;          // champ piège : rempli seulement par les robots
  if (!SUPABASE_URL) {
    const place = p.name || `${sub.lat}, ${sub.lon}`;
    res.textContent = L.sub_soon(`${place} · ${sub.algorithms.map((a) => ALGOS[a].label).join(", ")}`);
    res.hidden = false;
    return;
  }
  const btn = $("alert-form").querySelector('button[type="submit"]');
  btn.disabled = true;
  try {
    const r = await supa("subscriptions", sub);
    // 409 : déjà inscrit à ce lieu. Même message, pour ne pas révéler qui est inscrit.
    if (!r.ok && r.status !== 409) throw new Error(r.status);
    res.textContent = L.sub_ok(sub.email);
    res.classList.add("ok");
  } catch {
    res.textContent = L.sub_fail;
  }
  btn.disabled = false;
  res.hidden = false;
}

function supa(path, body) {
  const headers = { "Content-Type": "application/json", apikey: SUPABASE_KEY, Prefer: "return=minimal" };
  if (SUPABASE_KEY.startsWith("eyJ")) headers.Authorization = `Bearer ${SUPABASE_KEY}`;   // anciennes clés « anon »
  return fetch(`${SUPABASE_URL}/rest/v1/${path}`, { method: "POST", headers, body: JSON.stringify(body) });
}

/* Liens des e-mails : ?confirm=<jeton> ou ?unsubscribe=<jeton> */
async function handleAlertLink() {
  const q = new URLSearchParams(location.search);
  const action = q.has("confirm") ? "confirm" : q.has("unsubscribe") ? "unsubscribe" : null;
  if (!action || !ALERT_ENABLED) return;
  const token = q.get(action);
  q.delete(action);
  const url = new URL(location.href);
  url.search = q.toString();
  url.hash = "alert";
  history.replaceState(null, "", url);
  state.tab = "alert";
  render();
  const L = I18N[state.lang], box = $("alert-link-msg");
  box.hidden = false;
  box.className = "notice";
  box.textContent = L.link_wait;
  try {
    if (!SUPABASE_URL || !/^[0-9a-f-]{36}$/i.test(token)) throw new Error("bad");
    const r = await supa(`rpc/${action === "confirm" ? "confirm_subscription" : "unsubscribe"}`, { p_token: token });
    if (!r.ok) throw new Error(r.status);
    const place = await r.json();
    if (!place) throw new Error("unknown");
    box.textContent = action === "confirm" ? L.link_confirmed(place) : L.link_unsubscribed(place);
    box.classList.add("ok");
  } catch {
    box.textContent = L.link_fail;
  }
}
