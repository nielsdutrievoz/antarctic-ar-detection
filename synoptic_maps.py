#!/usr/bin/env python
"""Cartes synoptiques Antarctique (ECMWF HRES open data) avec rivières atmosphériques.

Pour chaque échéance du dernier run déterministe 00/12 UTC : IVT en couleur, vecteurs IVT,
isobares (MSLP), contours des AR détectées (méthode de Wille, vIVT) et sites configurés.
Écrit les PNG dans <site>/maps/ et un manifeste JSON lu par la page web.

    python synoptic_maps.py                    # dernier run
    python synoptic_maps.py --date 2026-11-25 --time 0
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import xarray as xr

import arcore
import maprender
import opendata

PARAMS_PL = ("q", "u", "v")
PARAMS_SFC = ("sp", "msl")


# --------------------------------------------------------------------------- données
def plot_grid(cfg):
    s = cfg["site"]
    res = float(cfg["detection"]["grid_res"])
    lat = np.round(np.arange(s["plot_lat_north"], -90 - res / 2, -res), 6)
    lon = np.round(np.arange(0.0, 360.0, res), 6)
    return lat, lon


def load_step(cfg, base, step, lat, lon, levels):
    lev = {str(l) for l in levels}

    def wanted(e):
        if e["param"] in PARAMS_SFC:
            return True
        return e["param"] in PARAMS_PL and e.get("levelist") in lev

    f, idx = {}, None
    for e, msg in opendata.fetch(cfg["site"]["source"], base, step, wanted,
                                 int(cfg["forecast"].get("download_workers", 8)), stream="oper"):
        vals, slat, slon = opendata.decode(msg)
        if idx is None:
            idx = (arcore._match(slat, lat), arcore._match(np.mod(slon, 360.0), lon))
        f[(e["param"], int(e.get("levelist", 0)))] = vals[idx[0]][:, idx[1]].astype(np.float32)
    q = np.stack([f[("q", l)] for l in levels])
    u = np.stack([f[("u", l)] for l in levels])
    v = np.stack([f[("v", l)] for l in levels])
    sp = f[("sp", 0)]
    return dict(uivt=arcore.vivt_from_levels(q, u, sp, levels),
                vivt=arcore.vivt_from_levels(q, v, sp, levels),
                msl=f[("msl", 0)] / 100.0, sp=sp)


# --------------------------------------------------------------------------- main
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", default=str(Path(__file__).with_name("config.yaml")))
    ap.add_argument("--date", help="date du run (AAAA-MM-JJ) ; défaut : dernier disponible")
    ap.add_argument("--time", type=int, choices=[0, 12], default=0)
    ap.add_argument("--max-step", type=int, help="remplace site.max_step_h (tests)")
    args = ap.parse_args(argv)

    cfg = arcore.load_config(args.config)
    sc, det = cfg["site"], cfg["detection"]
    max_step = args.max_step if args.max_step is not None else int(sc["max_step_h"])
    steps = list(range(0, max_step + 1, int(sc["step_interval_h"])))
    if args.date:
        base = dt.datetime.strptime(args.date, "%Y-%m-%d").replace(hour=args.time)
    else:
        base = opendata.latest(sc["source"], max_step, stream="oper")

    out_dir = arcore.cfg_path(cfg, sc["output_dir"])
    maps = out_dir / "maps"
    if maps.exists():
        shutil.rmtree(maps)
    maps.mkdir(parents=True)
    tmp = arcore.cfg_path(cfg, cfg["forecast"]["work_dir"])
    tmp.mkdir(parents=True, exist_ok=True)

    lat, lon = plot_grid(cfg)
    dlat, dlon = arcore.target_grid(det)
    ilat = arcore._match(lat, dlat)
    thr_file = arcore.cfg_path(cfg, cfg["climatology"]["output"])
    thresholds = None
    if thr_file.exists():
        thresholds = xr.load_dataset(thr_file)
        if thresholds.attrs.get("variable", "vivt") != "vivt":
            print(f"{thr_file.name} n'est pas un fichier de seuils vIVT : détection désactivée.")
            thresholds = None
    else:
        print(f"Seuils absents ({thr_file}) : cartes sans détection d'AR.")
    levels = [int(x) for x in cfg["forecast"]["levels"]]
    site_masks = {s["name"]: arcore.site_mask(s, dlat, dlon) for s in cfg["sites"]}

    print(f"Run HRES {base:%Y-%m-%d %HZ}, {len(steps)} échéances", flush=True)
    frames, futures = [], []
    with ProcessPoolExecutor(max_workers=int(sc.get("render_workers", 4))) as pool:
        for step in steps:
            t0 = time.time()
            vt = base + dt.timedelta(hours=step)
            fl = load_step(cfg, base, step, lat, lon, levels)
            extra, ar_sites = {}, []
            if thresholds is not None:
                pol = arcore.poleward(fl["vivt"][ilat])
                thr = thresholds["threshold"].sel(month=vt.month).values
                ar = arcore.detect_ar(pol, thr, dlat, det["min_lat_extent"])
                extra = dict(ar=ar, ar_lat=dlat, ar_lon=dlon)
                ar_sites = [n for n, m in site_masks.items() if ar[m].any()]
            npz = tmp / f"frame_{step:03d}.npz"
            np.savez(npz, lat=lat, lon=lon, **fl, **extra)
            fname = f"syn_{step:03d}.png"
            fr_, en_ = (maprender.fmt_time(base, l, weekday=False) for l in ("fr", "en"))
            job = dict(npz=str(npz), dpi=int(sc.get("dpi", 110)),
                       outputs={l: str(maps / l / fname) for l in maprender.LANGS},
                       subtitles={"fr": f"ECMWF HRES · run {fr_} · +{step} h · valide {maprender.fmt_time(vt, 'fr')}",
                                  "en": f"ECMWF HRES · run {en_} · +{step} h · valid {maprender.fmt_time(vt, 'en')}"},
                       credit="ECMWF open data, CC-BY-4.0",
                       lat_north=float(sc["plot_lat_north"]), quiver_every=int(sc.get("quiver_every", 8)),
                       sites=cfg["sites"], has_thr=thresholds is not None)
            futures.append(pool.submit(maprender.render, job))
            frames.append(dict(step=step, valid=vt.strftime("%Y-%m-%dT%H:%MZ"), file=fname,
                               ar_sites=ar_sites))
            print(f"  +{step:3d}h {vt:%d/%m %HZ} ({time.time() - t0:4.1f}s)"
                  + (f"  AR : {', '.join(ar_sites)}" if ar_sites else ""), flush=True)
        for f in futures:
            f.result()

    # animation GIF de toute la prévision, une par langue
    gifs = {}
    for lang in maprender.LANGS:
        name = f"ar_forecast_{base:%Y%m%d%H}_{lang}.gif"
        maprender.make_gif([str(maps / lang / fr["file"]) for fr in frames], str(maps / lang / name), width=720)
        gifs[lang] = f"maps/{lang}/{name}"
        print(f"GIF {lang} : {(maps / lang / name).stat().st_size / 1e6:.1f} Mo")

    manifest = dict(
        run=base.strftime("%Y-%m-%dT%HZ"),
        generated=dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
        model="ECMWF IFS HRES 0.25° (open data)",
        period=f"{cfg['climatology']['first_year']}-{cfg['climatology']['last_year']}",
        detection=thresholds is not None,
        sites=[dict(name=s["name"], lat=s["lat"], lon=s["lon"]) for s in cfg["sites"]],
        frames=frames,
        gif=gifs,
    )
    (out_dir / "data").mkdir(exist_ok=True)
    (out_dir / "data" / "manifest.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False))
    print(f"{len(frames)} cartes dans {maps}")


if __name__ == "__main__":
    main()
