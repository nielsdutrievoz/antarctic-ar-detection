"""E-mails des abonnés aux alertes AR du site (inscriptions stockées dans Supabase).

  python alert_mail.py confirm               envoie l'e-mail de confirmation aux nouvelles inscriptions
  python alert_mail.py alerts                après synoptic_maps.py : alerte les abonnés quand un AR
                                             est prévu à leur lieu
  python alert_mail.py test --to ADRESSE     envoie un exemple d'alerte (sans toucher à Supabase)

Options : --dry-run écrit les messages dans data/outbox/*.eml au lieu de les envoyer et ne modifie
pas Supabase.

Secrets lus dans l'environnement (jamais dans config.yaml) :
  SMTP_PASSWORD         jeton SMTP Proton de l'adresse d'envoi
  SUPABASE_SECRET_KEY   clé secrète du projet Supabase (lecture et mise à jour des inscriptions)

La commande « confirm » n'utilise que la bibliothèque standard et PyYAML.
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
import smtplib
import sys
import urllib.parse
import urllib.request
from email.message import EmailMessage
from email.utils import formataddr, formatdate, make_msgid
from pathlib import Path

import yaml

from algos import ALGOS, ORDER

HERE = Path(__file__).resolve().parent
RESERVED_TLD = {"invalid", "test", "example", "localhost"}     # adresses de test : jamais d'envoi
OUTBOX = HERE / "data" / "outbox"


# --------------------------------------------------------------------------- outils
def load_cfg(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def place_name(sub: dict) -> str:
    if sub.get("station"):
        return sub["station"]
    return coords(sub)


def coords(sub: dict) -> str:
    lat, lon = float(sub["lat"]), float(sub["lon"])
    return f"{abs(lat):.2f}°S, {abs(lon):.2f}°{'W' if lon < 0 else 'E'}"


def site_link(mc: dict, **query) -> str:
    return mc["site_url"] + "?" + urllib.parse.urlencode(query, safe=",")


def parse_z(s: str) -> dt.datetime:
    return dt.datetime.strptime(s, "%Y-%m-%dT%H:%MZ")


def haversine_km(lat1, lon1, lat2, lon2):
    import numpy as np

    R = 6371.0088
    lat1, lon1, lat2, lon2 = map(np.deg2rad, (lat1, lon1, lat2, lon2))
    a = np.sin((lat2 - lat1) / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    return 2 * R * np.arcsin(np.sqrt(a))


# --------------------------------------------------------------------------- Supabase
class Supabase:
    def __init__(self, url: str, key: str):
        if not key:
            sys.exit("SUPABASE_SECRET_KEY manquant (secret GitHub ou variable d'environnement).")
        self.url, self.key = url.rstrip("/"), key

    def _req(self, method: str, path: str, body=None):
        headers = {"apikey": self.key, "Content-Type": "application/json", "Prefer": "return=minimal"}
        if self.key.startswith("eyJ"):                       # anciennes clés « service_role »
            headers["Authorization"] = f"Bearer {self.key}"
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(f"{self.url}/rest/v1/{path}", data=data, method=method, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read()
        return json.loads(raw) if raw else None

    def select(self, query: str) -> list[dict]:
        return self._req("GET", f"subscriptions?{query}")

    def update(self, sub_id: str, fields: dict) -> None:
        self._req("PATCH", f"subscriptions?id=eq.{sub_id}", fields)


# --------------------------------------------------------------------------- envoi
class Mailer:
    def __init__(self, mc: dict, dry_run: bool):
        self.mc, self.dry_run = mc, dry_run
        self.password = os.environ.get("SMTP_PASSWORD", "")
        self.smtp = None
        if not dry_run and not self.password:
            sys.exit("SMTP_PASSWORD manquant (secret GitHub ou variable d'environnement).")

    def new(self, lang: str, to: str, subject: str, unsubscribe: str | None) -> EmailMessage:
        m = EmailMessage()
        m["From"] = formataddr((self.mc["sender_name"][lang], self.mc["sender"]))
        m["To"] = to
        m["Subject"] = subject
        m["Date"] = formatdate(localtime=False)
        m["Message-ID"] = make_msgid(domain=self.mc["sender"].split("@")[1])
        if unsubscribe:
            m["List-Unsubscribe"] = f"<{unsubscribe}>"
        return m

    def send(self, msg: EmailMessage) -> None:
        if self.dry_run:
            OUTBOX.mkdir(parents=True, exist_ok=True)
            n = len(list(OUTBOX.glob("*.eml"))) + 1
            out = OUTBOX / f"{n:03d}.eml"
            out.write_bytes(bytes(msg))
            print(f"    (simulation) {out}")
            return
        if self.smtp is None:
            self.smtp = smtplib.SMTP(self.mc["smtp_host"], int(self.mc["smtp_port"]), timeout=60)
            self.smtp.starttls()
            self.smtp.login(self.mc["sender"], self.password)
        self.smtp.send_message(msg)

    def close(self):
        if self.smtp is not None:
            self.smtp.quit()


# --------------------------------------------------------------------------- gabarit
TXT = {
    "fr": dict(
        confirm_subject="Confirme ton alerte AR pour {place}",
        confirm_subject_n="Confirme tes alertes AR pour {n} lieux",
        confirm_title="Confirme ton alerte",
        confirm_body="Tu as demandé à être prévenu quand une rivière atmosphérique est prévue à moins de "
                     "{radius} km de ces lieux :",
        confirm_button="Activer l'alerte",
        confirm_ignore="Si tu n'es pas à l'origine de cette demande, ignore simplement cet e-mail : "
                       "aucune alerte ne sera envoyée.",
        alert_subject="Rivière atmosphérique prévue à {place} dès le {start}",
        alert_title="Rivière atmosphérique prévue à {place}",
        alert_intro="La prévision ECMWF HRES du run du {run} prévoit un AR à moins de {radius} km de "
                    "<b>{place}</b> ({coords}).",
        col_algo="Algorithme", col_start="Arrivée", col_end="Dernière échéance avec AR",
        already="déjà présent",
        end_note="Fenêtre de prévision : jusqu'au {last}. Les prévisions au-delà de 3 à 4 jours sont incertaines.",
        anim="Animation : IVT, pression au niveau de la mer et contour AR ({algo}).",
        button="Voir la prévision sur le site",
        footer="Produit expérimental de recherche, sans garantie : ne pas utiliser pour la sécurité des opérations "
               "de terrain. Tu reçois cet e-mail car tu t'es inscrit aux alertes AR pour ce lieu.",
        unsubscribe="Se désinscrire",
    ),
    "en": dict(
        confirm_subject="Confirm your AR alert for {place}",
        confirm_subject_n="Confirm your AR alerts for {n} locations",
        confirm_title="Confirm your alert",
        confirm_body="You asked to be notified when an atmospheric river is forecast within {radius} km of "
                     "these locations:",
        confirm_button="Activate the alert",
        confirm_ignore="If you did not make this request, simply ignore this email: no alert will be sent.",
        alert_subject="Atmospheric river forecast at {place} from {start}",
        alert_title="Atmospheric river forecast at {place}",
        alert_intro="The ECMWF HRES forecast from the {run} run predicts an AR within {radius} km of "
                    "<b>{place}</b> ({coords}).",
        col_algo="Algorithm", col_start="Arrival", col_end="Last step with AR",
        already="already present",
        end_note="Forecast window: until {last}. Forecasts beyond 3 to 4 days are uncertain.",
        anim="Animation: IVT, mean sea-level pressure and AR contour ({algo}).",
        button="See the forecast on the site",
        footer="Experimental research product, no warranty: do not use for field-operation safety. "
               "You receive this email because you subscribed to AR alerts for this location.",
        unsubscribe="Unsubscribe",
    ),
}

CSS_BTN = ("display:inline-block;background:#2a6f97;color:#ffffff;text-decoration:none;padding:11px 20px;"
           "border-radius:8px;font-weight:600")


def wrap_html(title: str, inner: str, footer: str) -> str:
    return f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head><body style="margin:0;background:#f4f7f9;font-family:Helvetica,Arial,sans-serif;color:#0f1e2e">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td align="center" style="padding:24px 12px">
<table role="presentation" width="560" cellpadding="0" cellspacing="0" style="max-width:560px;width:100%;background:#ffffff;border:1px solid #dde5ec;border-radius:14px">
<tr><td style="padding:22px 26px 6px"><div style="font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:#5b6b7b">Antarctic AR</div>
<h1 style="font-size:21px;font-weight:600;margin:6px 0 0">{html.escape(title)}</h1></td></tr>
<tr><td style="padding:10px 26px 22px;font-size:15px;line-height:1.5">{inner}</td></tr>
</table>
<p style="max-width:560px;font-size:12px;line-height:1.5;color:#5b6b7b;margin:14px auto 0">{footer}</p>
</td></tr></table></body></html>"""


def fmt(t: dt.datetime, lang: str) -> str:
    from maprender import fmt_time      # import local : « confirm » n'a pas besoin de numpy
    return fmt_time(t, lang)


# --------------------------------------------------------------------------- confirmation
def confirmation_message(mailer: Mailer, mc: dict, subs: list[dict]) -> EmailMessage:
    """Un seul e-mail pour toutes les inscriptions en attente d'une même adresse."""
    last = subs[-1]
    lang = last["lang"] if last["lang"] in TXT else "fr"
    T = TXT[lang]
    tokens = ",".join(x["token"] for x in subs)
    confirm = site_link(mc, lang=lang, confirm=tokens)
    unsub = site_link(mc, lang=lang, unsubscribe=tokens)
    items = []
    for x in subs:
        algos = ", ".join(ALGOS[a]["label"] for a in ORDER if a in x["algorithms"])
        name = f"<b>{html.escape(x['station'])}</b> ({coords(x)})" if x.get("station") else f"<b>{coords(x)}</b>"
        items.append((name, algos))
    body = T["confirm_body"].format(radius=mc["radius_km"])
    lst = "".join(f"<li style='margin:4px 0'>{n} · <span style='color:#5b6b7b'>{html.escape(a)}</span></li>" for n, a in items)
    inner = (f"<p>{body}</p><ul style='padding-left:20px;margin:8px 0 0'>{lst}</ul>"
             f"<p style='margin:22px 0'><a href='{html.escape(confirm)}' style='{CSS_BTN}'>"
             f"{T['confirm_button']}</a></p><p style='color:#5b6b7b;font-size:13px'>{T['confirm_ignore']}</p>")
    subject = (T["confirm_subject"].format(place=place_name(last)) if len(subs) == 1
               else T["confirm_subject_n"].format(n=len(subs)))
    msg = mailer.new(lang, last["email"], subject, unsub)
    plain = [f"- {html.unescape(n.replace('<b>', '').replace('</b>', ''))} · {a}" for n, a in items]
    text = (f"{T['confirm_title']}\n\n{body}\n" + "\n".join(plain)
            + f"\n\n{T['confirm_button']} : {confirm}\n\n{T['confirm_ignore']}\n")
    msg.set_content(text)
    footer = f"<a href='{html.escape(mc['site_url'])}' style='color:#2a6f97'>{html.escape(mc['site_url'])}</a>"
    msg.add_alternative(wrap_html(T["confirm_title"], inner, footer), subtype="html")
    return msg


def cmd_confirm(cfg: dict, args) -> None:
    mc = cfg["alert_mail"]
    db = Supabase(mc["supabase_url"], os.environ.get("SUPABASE_SECRET_KEY", ""))
    subs = db.select("select=*&confirm_sent_at=is.null&unsubscribed_at=is.null&order=created_at")
    groups: dict[str, list[dict]] = {}
    for sub in subs:
        groups.setdefault(sub["email"].lower(), []).append(sub)
    print(f"{len(subs)} inscription(s) à confirmer, {len(groups)} adresse(s)")
    now = lambda: dt.datetime.now(dt.timezone.utc).isoformat()
    mailer = Mailer(mc, args.dry_run)
    try:
        for email, group in groups.items():
            print(f"  → {len(group)} lieu(x) : {', '.join(place_name(x) for x in group)}")
            cancel = email.rsplit(".", 1)[-1] in RESERVED_TLD
            if cancel:
                print("    domaine réservé (test) : inscriptions annulées sans envoi")
            else:
                try:
                    mailer.send(confirmation_message(mailer, mc, group))
                except smtplib.SMTPRecipientsRefused:
                    print("    adresse refusée par le serveur : inscriptions annulées")
                    cancel = True
            if not args.dry_run:
                for x in group:
                    db.update(x["id"], {"unsubscribed_at": now()} if cancel else {"confirm_sent_at": now()})
    finally:
        mailer.close()


# --------------------------------------------------------------------------- alertes
class Forecast:
    """Masques AR de la dernière prévision (écrits par synoptic_maps.py)."""

    def __init__(self, cfg: dict):
        import numpy as np

        self.np = np
        path = HERE / cfg["forecast"]["work_dir"] / "ar_masks.npz"
        if not path.exists():
            sys.exit(f"{path} absent : lancer synoptic_maps.py d'abord.")
        d = np.load(path)
        self.run = dt.datetime.strptime(str(d["run"]), "%Y-%m-%dT%HZ")
        self.valid = [parse_z(str(v)) for v in d["valid"]]
        self.files = [str(f) for f in d["files"]]
        self.algos = [str(a) for a in d["algos"]]
        self.masks = {a: d[a] for a in self.algos}
        self.grid = {a: (d[f"{a}_lat"], d[f"{a}_lon"]) for a in self.algos}
        self.maps = HERE / cfg["site"]["output_dir"] / "maps"
        self._near = {}

    def hits(self, algo: str, lat: float, lon: float, radius_km: float) -> list[int]:
        """Indices des échéances où l'AR passe à moins de radius_km du point."""
        np = self.np
        key = (algo, round(lat, 2), round(lon, 2))
        if key not in self._near:
            glat, glon = self.grid[algo]
            LA, LO = np.meshgrid(glat, glon, indexing="ij")
            self._near[key] = haversine_km(lat, lon, LA, LO) <= radius_km
        near = self._near[key]
        if not near.any():
            return []
        return [i for i in range(len(self.valid)) if self.masks[algo][i][near].any()]

    def gif(self, algo: str, lang: str, i0: int, i1: int, width: int, out: Path) -> Path:
        import maprender

        frames = [(str(self.maps / lang / f), str(self.maps / lang / algo / f)) for f in self.files[i0:i1 + 1]]
        maprender.make_gif(frames, str(out), width=width)
        return out


def alert_message(mailer: Mailer, mc: dict, fc: Forecast, sub: dict, new: dict, tmpdir: Path,
                  test: bool = False) -> EmailMessage:
    """new : {algo: [indices d'échéances avec AR]} pour les AR nouvellement prévus."""
    lang = sub["lang"] if sub["lang"] in TXT else "fr"
    T = TXT[lang]
    place = place_name(sub)
    order = [a for a in ORDER if a in new]
    first = min(new[a][0] for a in order)
    start_txt = fmt(fc.valid[first], lang)
    rows = []
    for a in order:
        i0, i1 = new[a][0], new[a][-1]
        s = fmt(fc.valid[i0], lang) + (f" ({T['already']})" if i0 == 0 else "")
        rows.append((a, s, fmt(fc.valid[i1], lang)))
    # animation de l'algorithme qui voit l'AR le plus tôt, autour de l'événement
    lead = min(order, key=lambda a: new[a][0])
    step_h = (fc.valid[1] - fc.valid[0]).total_seconds() / 3600 if len(fc.valid) > 1 else 6
    m = int(round(mc.get("gif_margin_h", 24) / step_h))
    g0, g1 = max(0, new[lead][0] - m), min(len(fc.valid) - 1, new[lead][-1] + m)
    gif = fc.gif(lead, lang, g0, g1, int(mc.get("gif_width", 480)), tmpdir / f"{sub['id']}.gif")

    link = site_link(mc, lang=lang, algo=lead) + "#forecast"
    unsub = site_link(mc, lang=lang, unsubscribe=sub["token"])
    cid = make_msgid(domain=mc["sender"].split("@")[1])
    th = "text-align:left;padding:7px 8px;border-bottom:1px solid #dde5ec;font-size:13px;color:#5b6b7b"
    td = "padding:7px 8px;border-bottom:1px solid #eef2f5;font-size:14px"
    table = (f"<table role='presentation' cellpadding='0' cellspacing='0' style='border-collapse:collapse;width:100%;margin:14px 0'>"
             f"<tr><th style='{th}'>{T['col_algo']}</th><th style='{th}'>{T['col_start']}</th><th style='{th}'>{T['col_end']}</th></tr>"
             + "".join(f"<tr><td style='{td}'><span style='display:inline-block;width:10px;height:10px;border-radius:50%;"
                       f"background:{ALGOS[a]['color']};border:1px solid #0f1e2e;margin-right:6px'></span>{ALGOS[a]['label']}</td>"
                       f"<td style='{td}'><b>{s}</b></td><td style='{td}'>{e}</td></tr>" for a, s, e in rows)
             + "</table>")
    intro = T["alert_intro"].format(run=fmt(fc.run, lang), radius=mc["radius_km"], place=html.escape(place),
                                    coords=coords(sub))
    inner = (f"<p>{intro}</p>{table}"
             f"<p style='color:#5b6b7b;font-size:13px'>{T['end_note'].format(last=fmt(fc.valid[-1], lang))}</p>"
             f"<p style='margin:18px 0 6px'><img src='cid:{cid[1:-1]}' width='{int(mc.get('gif_width', 480))}' "
             f"alt='' style='max-width:100%;height:auto;border-radius:8px;display:block'></p>"
             f"<p style='color:#5b6b7b;font-size:13px;margin:4px 0 20px'>{T['anim'].format(algo=ALGOS[lead]['label'])}</p>"
             f"<p><a href='{html.escape(link)}' style='{CSS_BTN}'>{T['button']}</a></p>")
    footer = f"{html.escape(T['footer'])} <a href='{html.escape(unsub)}' style='color:#2a6f97'>{T['unsubscribe']}</a>"

    subject = T["alert_subject"].format(place=place, start=start_txt)
    msg = mailer.new(lang, sub["email"], ("[TEST] " if test else "") + subject, unsub)
    text = [T["alert_title"].format(place=place), "",
            html.unescape(intro.replace("<b>", "").replace("</b>", "")), ""]
    text += [f"- {ALGOS[a]['label']} : {s} → {e}" for a, s, e in rows]
    text += ["", T["end_note"].format(last=fmt(fc.valid[-1], lang)), "", f"{T['button']} : {link}", "",
             T["footer"], f"{T['unsubscribe']} : {unsub}"]
    msg.set_content("\n".join(text) + "\n")
    msg.add_alternative(wrap_html(T["alert_title"].format(place=place), inner, footer), subtype="html")
    msg.get_payload()[1].add_related(gif.read_bytes(), "image", "gif", cid=cid, filename=f"ar_{lead}.gif")
    return msg


def new_events(fc: Forecast, mc: dict, sub: dict) -> tuple[dict, dict]:
    """AR nouvellement prévus pour cet abonné et nouvel état de déduplication."""
    state = dict(sub.get("alert_state") or {})
    gap = dt.timedelta(hours=float(mc.get("new_event_gap_h", 24)))
    new = {}
    for a in sub["algorithms"]:
        if a not in fc.algos:
            continue
        if a.startswith("wille") and float(sub["lat"]) < -85:
            continue
        idx = fc.hits(a, float(sub["lat"]), float(sub["lon"]), float(mc["radius_km"]))
        if not idx:
            continue
        first, last = fc.valid[idx[0]], fc.valid[idx[-1]]
        prev = state.get(a, {}).get("until")
        if prev and first <= parse_z(prev) + gap:
            # même AR que celui déjà signalé : on prolonge seulement la fenêtre connue
            state[a] = {"until": max(parse_z(prev), last).strftime("%Y-%m-%dT%H:%MZ")}
            continue
        new[a] = idx
        state[a] = {"until": last.strftime("%Y-%m-%dT%H:%MZ")}
    return new, state


def cmd_alerts(cfg: dict, args) -> None:
    import tempfile

    mc = cfg["alert_mail"]
    fc = Forecast(cfg)
    print(f"Run {fc.run:%Y-%m-%d %HZ}, algorithmes : {', '.join(fc.algos)}")
    db = Supabase(mc["supabase_url"], os.environ.get("SUPABASE_SECRET_KEY", ""))
    subs = db.select("select=*&confirmed_at=not.is.null&unsubscribed_at=is.null")
    print(f"{len(subs)} abonné(s) actif(s)")
    mailer = Mailer(mc, args.dry_run)
    sent = 0
    try:
        with tempfile.TemporaryDirectory() as tmp:
            for sub in subs:
                new, state = new_events(fc, mc, sub)
                if new:
                    print(f"  → AR prévu à {place_name(sub)} : {', '.join(new)}")
                    try:
                        mailer.send(alert_message(mailer, mc, fc, sub, new, Path(tmp)))
                        sent += 1
                    except smtplib.SMTPException as e:
                        print(f"    échec de l'envoi : {e}")
                        continue                    # état inchangé : nouvel essai au prochain passage
                if state != (sub.get("alert_state") or {}) and not args.dry_run:
                    db.update(sub["id"], {"alert_state": state})
    finally:
        mailer.close()
    print(f"{sent} alerte(s) envoyée(s)")


def cmd_test(cfg: dict, args) -> None:
    """Exemple d'alerte pour vérifier l'envoi : Concordia, premier AR de la prévision ou fausse fenêtre."""
    import tempfile

    mc = cfg["alert_mail"]
    fc = Forecast(cfg)
    sub = dict(id="test", token="00000000-0000-4000-8000-000000000000", email=args.to, lang=args.lang,
               station=args.station, lat=args.lat, lon=args.lon, algorithms=list(fc.algos), alert_state={})
    new, _ = new_events(fc, mc, sub)
    if not new:                              # pas d'AR prévu : exemple fictif sur 24 h au milieu de la prévision
        mid = len(fc.valid) // 2
        new = {fc.algos[-1]: list(range(mid, min(mid + 5, len(fc.valid))))}
        print("Aucun AR prévu à ce lieu : exemple avec une fenêtre fictive.")
    mailer = Mailer(mc, args.dry_run)
    try:
        with tempfile.TemporaryDirectory() as tmp:
            mailer.send(alert_message(mailer, mc, fc, sub, new, Path(tmp), test=True))
            mailer.send(confirmation_message(mailer, mc, [sub, dict(sub, station="Vostok", lat=-78.46, lon=106.84)]))
    finally:
        mailer.close()
    print("Exemples envoyés (alerte + confirmation).")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["confirm", "alerts", "test"])
    ap.add_argument("--config", default=str(HERE / "config.yaml"))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--to", help="test : destinataire")
    ap.add_argument("--lang", default="fr", choices=["fr", "en"])
    ap.add_argument("--station", default="Concordia")
    ap.add_argument("--lat", type=float, default=-75.10)
    ap.add_argument("--lon", type=float, default=123.35)
    args = ap.parse_args(argv)
    cfg = load_cfg(args.config)
    if args.command == "test" and not args.to:
        ap.error("test : --to ADRESSE requis")
    {"confirm": cmd_confirm, "alerts": cmd_alerts, "test": cmd_test}[args.command](cfg, args)


if __name__ == "__main__":
    main()
