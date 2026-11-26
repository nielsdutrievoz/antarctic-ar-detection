#!/usr/bin/env python
"""Animations d'événements AR passés à partir de la réanalyse ERA5.

Pour chaque événement de la section `events` de config.yaml : téléchargement ERA5
(IVT est/nord, MSLP, pression de surface, 6-horaire, 0.5°), détection de Wille avec
les mêmes seuils que les prévisions, cartes FR/EN, GIF animé, et manifeste
site/events/events.json. Les fichiers produits sont versionnés avec le site.

    python events.py                     # tous les événements
    python events.py --only 2018-12-concordia
    python events.py --download-only     # ERA5 seulement (sans seuils)
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import xarray as xr

import arcore
import maprender
from detectors import Detectors

VARS = {
    "uivt": "vertical_integral_of_eastward_water_vapour_flux",
    "vivt": "vertical_integral_of_northward_water_vapour_flux",
    "msl": "mean_sea_level_pressure",
    "sp": "surface_pressure",
    "iwv": "total_column_water_vapour",
}


def download(cfg: dict, ev: dict) -> Path:
    """ERA5 de l'événement (6-horaire, 0.5°) sur le domaine des données (site.data_lat_north → pôle)."""
    import cdsapi

    out = arcore.cfg_path(cfg, "data/events") / f"era5_{ev['id']}.nc"
    north = float(cfg["site"].get("data_lat_north", -15.0))
    if out.exists():
        ds = _open(out)
        if set(VARS) <= set(ds.data_vars) and float(ds["latitude"].max()) >= north - 1e-6:
            return out
        out.unlink()                      # ancien fichier (domaine ou variables incomplets)
    out.parent.mkdir(parents=True, exist_ok=True)
    days = [ev["start"] + dt.timedelta(days=i) for i in range((ev["end"] - ev["start"]).days + 1)]
    res = float(cfg["detection"]["grid_res"])
    parts = []
    for ym in sorted({(d.year, d.month) for d in days}):
        part = out.with_name(f"{out.stem}_{ym[0]}{ym[1]:02d}.nc")
        print(f"[{ev['id']}] requête CDS {ym[0]}-{ym[1]:02d}…", flush=True)
        cdsapi.Client(quiet=True).retrieve(
            "reanalysis-era5-single-levels",
            {"product_type": ["reanalysis"], "variable": list(VARS.values()),
             "year": [str(ym[0])], "month": [f"{ym[1]:02d}"],
             "day": [f"{d.day:02d}" for d in days if (d.year, d.month) == ym],
             "time": ["00:00", "06:00", "12:00", "18:00"], "area": [north, 0, -90, 360 - res],
             "grid": [res, res], "data_format": "netcdf", "download_format": "unarchived"},
            str(part))
        parts.append(part)
    ds = xr.concat([_open(p) for p in parts], dim="time").sortby("time")
    ds.to_netcdf(out)
    for p in parts:
        p.unlink()
    return out


def _open(path: Path) -> xr.Dataset:
    ds = xr.load_dataset(path)
    if "valid_time" in ds.dims:
        ds = ds.rename({"valid_time": "time"})
    drop = [c for c in ("number", "expver") if c in ds.coords]
    ds = ds.drop_vars(drop)
    # noms courts ERA5 -> noms internes
    short = {"viwve": "uivt", "viwvn": "vivt", "msl": "msl", "sp": "sp", "tcwv": "iwv"}
    ds = ds.rename({k: v for k, v in short.items() if k in ds and k != v})
    return ds.sortby("latitude", ascending=False)


def build(cfg: dict, ev: dict, out_root: Path, workers: int) -> dict:
    ds = _open(download(cfg, ev))
    lat, lon = ds["latitude"].values, np.mod(ds["longitude"].values, 360.0)
    det = Detectors(cfg, lat, lon)
    algos = det.available

    ev_dir = out_root / ev["id"]
    if ev_dir.exists():
        shutil.rmtree(ev_dir)
    tmp = arcore.cfg_path(cfg, cfg["forecast"]["work_dir"])
    tmp.mkdir(parents=True, exist_ok=True)

    frames, jobs = [], []
    for i, t in enumerate(ds["time"].values):
        t = dt.datetime.fromtimestamp(int(t.astype("datetime64[s]").astype(int)), dt.timezone.utc).replace(tzinfo=None)
        f = {k: ds[k].isel(time=i).values.astype(np.float32) for k in VARS}
        f["msl"] = f["msl"] / 100.0
        masks = det.run(t, f)
        hits = det.sites_hit(masks)
        npz = tmp / f"ev_{ev['id']}_{i:03d}.npz"
        np.savez(npz, lat=lat, lon=lon, uivt=f["uivt"], vivt=f["vivt"], msl=f["msl"], sp=f["sp"],
                 **det.npz_fields(masks))
        fname = f"{t:%Y%m%d_%H}.png"
        jobs.append(dict(
            npz=str(npz), dpi=int(cfg["site"].get("dpi", 150)),
            base={l: str(ev_dir / l / fname) for l in maprender.LANGS},
            layers={a: {l: str(ev_dir / l / a / fname) for l in maprender.LANGS} for a in algos},
            subtitles={l: f"ERA5 · {maprender.fmt_time(t, l)}" for l in maprender.LANGS},
            credit="ERA5, Copernicus Climate Change Service",
            lat_north=float(cfg["site"]["plot_lat_north"]),
            quiver_every=int(cfg["site"].get("quiver_every", 8)),
            sites=cfg["sites"]))
        frames.append(dict(time=t.strftime("%Y-%m-%dT%H:%MZ"), file=fname, ar=hits))
        print(f"  {t:%Y-%m-%d %HZ}  " + "  ".join(f"{a}: {', '.join(h) or '-'}" for a, h in hits.items()), flush=True)

    with ProcessPoolExecutor(max_workers=workers) as pool:
        list(pool.map(maprender.render, jobs))

    gifs = {}
    for a in algos:
        for l in maprender.LANGS:
            gif = ev_dir / f"{ev['id']}_{a}_{l}.gif"
            maprender.make_gif([(str(ev_dir / l / fr["file"]), str(ev_dir / l / a / fr["file"])) for fr in frames],
                               str(gif), width=600)
            gifs.setdefault(a, {})[l] = f"{ev['id']}/{gif.name}"
        print(f"  GIF {a} : {gif.stat().st_size / 1e6:.1f} Mo", flush=True)

    return dict(id=ev["id"], start=str(ev["start"]), end=str(ev["end"]), title=ev["title"],
                description=ev["description"], reference=ev.get("reference"),
                algorithms=algos, frames=frames, gif=gifs)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", default=str(Path(__file__).with_name("config.yaml")))
    ap.add_argument("--only", help="identifiant d'un seul événement")
    ap.add_argument("--download-only", action="store_true")
    args = ap.parse_args(argv)
    cfg = arcore.load_config(args.config)
    events = [e for e in cfg["events"] if not args.only or e["id"] == args.only]

    if args.download_only:
        for ev in events:
            print(download(cfg, ev))
        return


    out_root = arcore.cfg_path(cfg, cfg["site"]["output_dir"]) / "events"
    out_root.mkdir(parents=True, exist_ok=True)
    manifest_file = out_root / "events.json"
    old = {e["id"]: e for e in json.loads(manifest_file.read_text())} if manifest_file.exists() else {}
    for ev in events:
        print(f"Événement {ev['id']} ({ev['start']} → {ev['end']})", flush=True)
        old[ev["id"]] = build(cfg, ev, out_root, int(cfg["site"].get("render_workers", 4)))
    order = [e["id"] for e in cfg["events"]]
    manifest = [old[i] for i in order if i in old]
    manifest_file.write_text(json.dumps(manifest, indent=1, ensure_ascii=False))
    print(f"Manifeste : {manifest_file}")


if __name__ == "__main__":
    main()
