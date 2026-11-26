#!/usr/bin/env python
"""Détecte les AR dans la dernière prévision d'ensemble ECMWF (open data) et envoie une alerte email.

    python run_forecast.py                     # dernier run, alerte si besoin
    python run_forecast.py --dry-run           # affiche le rapport, n'envoie rien
    python run_forecast.py --test-email        # envoie un email de test et s'arrête
    python run_forecast.py --date 2026-11-24 --time 0 --force
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import smtplib
import subprocess
import sys
from email.message import EmailMessage
from pathlib import Path

import time

import numpy as np
import xarray as xr

import arcore
import opendata


# --------------------------------------------------------------------------- prévision
def _members_fields(root, base, step, params, levels, lat, lon, workers):
    """{(param, member, level): champ sur la grille cible} pour une échéance."""
    lev = {str(l) for l in levels}

    def wanted(e):
        if e.get("type") != "pf" or e["param"] not in params:
            return False
        return e.get("levtype") == "sfc" if e["param"] in ("sp", "tcwv") else e.get("levelist") in lev

    out, idx = {}, None
    for e, msg in opendata.fetch(root, base, step, wanted, workers):
        vals, src_lat, src_lon = opendata.decode(msg)
        if idx is None:
            idx = (arcore._match(src_lat, lat), arcore._match(np.mod(src_lon, 360.0), lon))
        out[(e["param"], int(e["number"]), int(e.get("levelist", 0)))] = vals[idx[0]][:, idx[1]].astype(np.float32)
    return out


def detection_field(fields, variable, levels):
    """Champ utilisé pour la détection, (membre, ny, nx), et liste des membres."""
    if variable == "iwv":
        members = sorted({k[1] for k in fields if k[0] == "tcwv"})
        return np.stack([fields[("tcwv", m, 0)] for m in members]), members
    members = sorted({k[1] for k in fields if k[0] == "sp"})
    q = np.stack([np.stack([fields[("q", m, l)] for l in levels]) for m in members])
    v = np.stack([np.stack([fields[("v", m, l)] for l in levels]) for m in members])
    sp = np.stack([fields[("sp", m, 0)] for m in members])
    return arcore.poleward(arcore.vivt_from_levels(q, v, sp, levels)), members


def process_run(cfg: dict, base: dt.datetime, thresholds: xr.Dataset) -> dict:
    det, fc = cfg["detection"], cfg["forecast"]
    variable = det.get("variable", "vivt")
    lat, lon = thresholds["lat"].values, thresholds["lon"].values
    levels = [int(x) for x in fc["levels"]]
    params = {"tcwv"} if variable == "iwv" else {"q", "v", "sp"}
    steps = list(range(0, int(fc["max_step_h"]) + 1, int(fc["step_interval_h"])))
    work = arcore.cfg_path(cfg, fc["work_dir"])
    work.mkdir(parents=True, exist_ok=True)

    site_masks = {s["name"]: arcore.site_mask(s, lat, lon) for s in cfg["sites"]}
    prob = np.zeros((len(steps), lat.size, lon.size), dtype=np.float32)
    site_prob = {n: np.zeros(len(steps)) for n in site_masks}
    site_val = {n: np.full(len(steps), np.nan) for n in site_masks}
    site_thr = {n: np.full(len(steps), np.nan) for n in site_masks}
    valid, members = [], []
    print(f"Run ENS {base:%Y-%m-%d %HZ}, variable {variable}, {len(steps)} échéances", flush=True)

    for i, step in enumerate(steps):
        t0 = time.time()
        vt = base + dt.timedelta(hours=step)
        valid.append(vt)
        fields = _members_fields(fc["source"], base, step, params, levels, lat, lon,
                                 int(fc.get("download_workers", 8)))
        val, members = detection_field(fields, variable, levels)
        del fields
        thr = thresholds["threshold"].sel(month=vt.month).values
        masks = np.stack([arcore.detect_ar(val[k], thr, lat, det["min_lat_extent"]) for k in range(len(members))])
        prob[i] = masks.mean(axis=0)
        for n, sm in site_masks.items():
            site_prob[n][i] = masks[:, sm].any(axis=1).mean()
            site_val[n][i] = np.median(val[:, sm].max(axis=1))
            site_thr[n][i] = thr[sm].max()
        print(f"  +{step:3d}h {vt:%d/%m %HZ} ({time.time() - t0:4.0f}s)  " +
              "  ".join(f"{n}: {100 * site_prob[n][i]:3.0f}%" for n in site_masks), flush=True)

    out = work / f"ar_prob_{base:%Y%m%d%H}.nc"
    xr.Dataset(
        {"ar_probability": (("time", "lat", "lon"), prob)},
        coords={"time": np.array(valid, dtype="datetime64[ns]"), "lat": lat, "lon": lon},
        attrs={"run": base.isoformat(), "members": len(members), "variable": variable},
    ).to_netcdf(out, encoding={"ar_probability": {"zlib": True, "complevel": 4}})
    return dict(base=base, steps=steps, valid=valid, members=len(members), variable=variable,
                site_prob=site_prob, site_val=site_val, site_thr=site_thr, prob_file=out)


# --------------------------------------------------------------------------- alerte
def evaluate(cfg: dict, res: dict, state: dict) -> list[dict]:
    al = cfg["alert"]
    thr, ncons = float(al["probability_threshold"]), int(al["min_consecutive_steps"])
    alerts = []
    for site in cfg["sites"]:
        n = site["name"]
        p = res["site_prob"][n]
        above = p >= thr
        run_len, best, first = 0, 0, None
        for i, a in enumerate(above):
            run_len = run_len + 1 if a else 0
            if run_len > best:
                best = run_len
            if run_len >= ncons and first is None:
                first = i - run_len + 1
        triggered = first is not None
        prev = state.get("sites", {}).get(n, {})
        pmax = float(p.max())
        send = triggered and (not prev.get("alerted")
                               or pmax >= prev.get("max_prob", 0) + float(al["update_if_prob_increase"]))
        state.setdefault("sites", {})[n] = {
            "alerted": triggered,
            "max_prob": max(pmax, prev.get("max_prob", 0)) if (triggered and prev.get("alerted")) else pmax,
            "run": res["base"].isoformat(),
        }
        alerts.append(dict(site=site, triggered=triggered, send=send, first=first, pmax=pmax,
                           update=bool(prev.get("alerted"))))
    return alerts


def report(cfg: dict, res: dict, a: dict) -> tuple[str, str]:
    n = a["site"]["name"]
    p, viv, thr = res["site_prob"][n], res["site_val"][n], res["site_thr"][n]
    vname, unit = ("IWV", "kg m-2") if res["variable"] == "iwv" else ("vIVT", "kg m-1 s-1")
    i_max = int(np.argmax(p))
    first_vt = res["valid"][a["first"]]
    subject = (f"[AR {'mise à jour' if a['update'] else 'alerte'}] {n} : "
               f"{100 * a['pmax']:.0f}% le {res['valid'][i_max]:%d/%m %HZ} "
               f"(début {first_vt:%d/%m %HZ})")
    lines = [
        f"Rivière atmosphérique prévue à {n} ({a['site']['lat']:.2f}, {a['site']['lon']:.2f}, "
        f"rayon {a['site'].get('radius_km', 0)} km).",
        f"Prévision ECMWF ENS du {res['base']:%Y-%m-%d %HZ}, {res['members']} membres, "
        f"détection Wille ({vname} > {cfg['detection']['percentile']}e percentile mensuel, "
        f"extension >= {cfg['detection']['min_lat_extent']:.0f}° lat).",
        f"Seuil d'alerte : {100 * cfg['alert']['probability_threshold']:.0f}% des membres.",
        "",
        f"{'Échéance (UTC)':<17}{'+h':>5}{'P(AR)':>8}{'membres':>9}{vname + ' méd.':>11}{'seuil':>8}",
    ]
    for i, vt in enumerate(res["valid"]):
        flag = " <" if p[i] >= cfg["alert"]["probability_threshold"] else ""
        lines.append(f"{vt:%Y-%m-%d %H:%M}{res['steps'][i]:>5}{100 * p[i]:>7.0f}%"
                     f"{round(p[i] * res['members']):>6}/{res['members']}"
                     f"{viv[i]:>11.0f}{thr[i]:>8.0f}{flag}")
    lines += ["", f"{vname} méd. = médiane d'ensemble du {vname} max dans le rayon ({unit}).",
              f"Carte de probabilité : {res['prob_file']}"]
    return subject, "\n".join(lines)


def smtp_password(email_cfg: dict) -> str | None:
    if os.environ.get("AR_SMTP_PASSWORD"):
        return os.environ["AR_SMTP_PASSWORD"]
    if not email_cfg.get("username"):
        return None
    try:
        return subprocess.run(["security", "find-generic-password", "-s", "ar-alert-smtp",
                               "-a", email_cfg["username"], "-w"],
                              capture_output=True, text=True, check=True).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        sys.exit("Mot de passe SMTP introuvable (AR_SMTP_PASSWORD ou trousseau 'ar-alert-smtp').")


def send_email(cfg: dict, subject: str, body: str) -> None:
    e = cfg["email"]
    if not e.get("to") or not e.get("from"):
        sys.exit("Configurer email.from et email.to dans config.yaml.")
    msg = EmailMessage()
    msg["Subject"], msg["From"], msg["To"] = subject, e["from"], ", ".join(e["to"])
    msg.set_content(body)
    with smtplib.SMTP(e["smtp_host"], int(e["smtp_port"]), timeout=60) as s:
        if e.get("starttls", True):
            s.starttls()
        if e.get("username"):
            s.login(e["username"], smtp_password(e))
        s.send_message(msg)
    print(f"Email envoyé à {', '.join(e['to'])} : {subject}")


# --------------------------------------------------------------------------- main
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", default=str(Path(__file__).with_name("config.yaml")))
    ap.add_argument("--date", help="date du run (AAAA-MM-JJ) ; défaut : dernier disponible")
    ap.add_argument("--time", type=int, choices=[0, 6, 12, 18], help="heure du run (UTC)")
    ap.add_argument("--force", action="store_true", help="retraiter un run déjà traité")
    ap.add_argument("--dry-run", action="store_true", help="n'envoie pas d'email, n'écrit pas l'état")
    ap.add_argument("--test-email", action="store_true", help="envoie un email de test puis s'arrête")
    args = ap.parse_args(argv)

    cfg = arcore.load_config(args.config)
    if args.test_email:
        send_email(cfg, "[AR] test", "Test du système d'alerte AR : la configuration email fonctionne.")
        return

    thr_file = arcore.cfg_path(cfg, cfg["climatology"]["output"])
    if not thr_file.exists():
        sys.exit(f"Seuils absents ({thr_file}). Lancer d'abord build_climatology.py.")
    thresholds = xr.load_dataset(thr_file)
    var_cfg, var_thr = cfg["detection"].get("variable", "vivt"), thresholds.attrs.get("variable", "vivt")
    if var_cfg != var_thr:
        sys.exit(f"Les seuils de {thr_file.name} sont pour '{var_thr}', la config demande '{var_cfg}'.")

    if args.date:
        base = dt.datetime.strptime(args.date, "%Y-%m-%d").replace(hour=args.time or 0)
    else:
        base = opendata.latest(cfg["forecast"]["source"], int(cfg["forecast"]["max_step_h"]))

    state_file = arcore.cfg_path(cfg, cfg["alert"]["state_file"])
    state = json.loads(state_file.read_text()) if state_file.exists() else {}
    if state.get("last_run") == base.isoformat() and not args.force:
        print(f"Run {base:%Y-%m-%d %HZ} déjà traité.")
        return

    res = process_run(cfg, base, thresholds)
    alerts = evaluate(cfg, res, state)
    for a in alerts:
        status = "ALERTE" if a["triggered"] else "rien"
        print(f"{a['site']['name']}: P max = {100 * a['pmax']:.0f}% -> {status}"
              + (" (email)" if a["send"] else ""))
        if a["triggered"] and (a["send"] or args.dry_run):
            subject, body = report(cfg, res, a)
            if args.dry_run or not cfg["email"].get("enabled", True):
                print("\n" + subject + "\n" + body + "\n")
            else:
                send_email(cfg, subject, body)

    if not args.dry_run:
        state["last_run"] = base.isoformat()
        state_file.parent.mkdir(parents=True, exist_ok=True)
        state_file.write_text(json.dumps(state, indent=2))


if __name__ == "__main__":
    main()
