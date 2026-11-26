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
import time
import warnings
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import xarray as xr

import arcore
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


# --------------------------------------------------------------------------- rendu
def render(job):
    """Dessine une carte. Exécuté dans un processus séparé (matplotlib n'est pas thread-safe)."""
    warnings.filterwarnings("ignore")
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.path as mpath
    import matplotlib.pyplot as plt
    from matplotlib.colors import BoundaryNorm, ListedColormap
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    from cartopy.util import add_cyclic_point

    d = np.load(job["npz"])
    lat, lon = d["lat"], d["lon"]
    ivt = np.hypot(d["uivt"], d["vivt"])

    fig = plt.figure(figsize=(8, 8.6), dpi=job["dpi"])
    ax = fig.add_axes([0.02, 0.125, 0.96, 0.815], projection=ccrs.SouthPolarStereo())
    ax.set_extent([-180, 180, -90, job["lat_north"]], ccrs.PlateCarree())
    theta = np.linspace(0, 2 * np.pi, 200)
    circle = mpath.Path(np.vstack([np.sin(theta), np.cos(theta)]).T * 0.5 + 0.5)
    ax.set_boundary(circle, transform=ax.transAxes)
    pc = ccrs.PlateCarree()

    levels = [100, 150, 200, 250, 300, 400, 500, 600, 750, 1000, 1500]
    colors = ["#fff7bc", "#fee391", "#fec44f", "#fe9929", "#ec7014", "#cc4c02",
              "#a63603", "#8c2d04", "#6a1b5a", "#4a1486"]
    cmap = ListedColormap(colors)
    cmap.set_over("#2d004b")
    norm = BoundaryNorm(levels, cmap.N)
    ivt_c, lon_c = add_cyclic_point(ivt, coord=lon)
    X, Y = np.meshgrid(lon_c, lat)
    cf = ax.contourf(X, Y, ivt_c, levels=levels, cmap=cmap, norm=norm, extend="max",
                     transform=pc)

    ax.add_feature(cfeature.OCEAN.with_scale("110m"), facecolor="#eef3f7", zorder=0)
    ax.add_feature(cfeature.LAND.with_scale("50m"), facecolor="#ffffff", zorder=0)
    ax.coastlines("50m", linewidth=0.6, color="#3a3a3a")

    # isobares (masquées sur le haut plateau, où la réduction au niveau de la mer n'a pas de sens)
    msl = np.where(d["sp"] < job["msl_mask_pa"], np.nan, d["msl"])
    msl_c, _ = add_cyclic_point(msl, coord=lon)
    cs = ax.contour(X, Y, msl_c, levels=np.arange(920, 1060, 4), colors="#1f1f1f",
                    linewidths=0.6, transform=pc)
    ax.clabel(cs, cs.levels[::2], fontsize=6, fmt="%d", inline_spacing=2)

    # vecteurs IVT là où le transport est significatif
    step = job["quiver_every"]
    sl = (slice(None, None, step), slice(None, None, step))
    uu, vv = d["uivt"][sl], d["vivt"][sl]
    show = ivt[sl] >= 250
    if show.any():
        lon2, lat2 = np.meshgrid(lon[sl[1]], lat[sl[0]])
        ax.quiver(lon2[show], lat2[show], uu[show], vv[show], transform=pc, scale=12000,
                  width=0.0018, color="#202020", alpha=0.75)

    # contours AR
    if "ar" in d.files and d["ar"].any():
        ar_c, lon_ar = add_cyclic_point(d["ar"].astype(float), coord=d["ar_lon"])
        XA, YA = np.meshgrid(lon_ar, d["ar_lat"])
        ax.contour(XA, YA, ar_c, levels=[0.5], colors="#d4006a", linewidths=2.0,
                   transform=pc)

    for s in job["sites"]:
        ax.plot(s["lon"], s["lat"], marker="o", ms=4.5, mfc="#00a0b0", mec="k", mew=0.6, transform=pc)
        ax.text(s["lon"], s["lat"], " " + s["name"], fontsize=7, transform=pc,
                ha="left", va="center", color="#003a40")

    gl = ax.gridlines(pc, linewidth=0.3, color="#888888", alpha=0.6, linestyle="--")
    gl.ylocator = matplotlib.ticker.FixedLocator([-80, -70, -60, -50, -40, -30])

    fig.text(0.03, 0.965, "IVT, pression au niveau de la mer et rivières atmosphériques",
             fontsize=10.5, weight="bold")
    fig.text(0.03, 0.945, job["subtitle"], fontsize=8.5, color="#333333")
    cax = fig.add_axes([0.15, 0.075, 0.7, 0.016])
    cb = fig.colorbar(cf, cax=cax, orientation="horizontal", ticks=levels)
    cb.set_label("IVT (kg m$^{-1}$ s$^{-1}$)", fontsize=8)
    cb.ax.tick_params(labelsize=7)
    note = ("Contour magenta : AR (Wille et al. 2021)" if job["has_thr"]
            else "Seuils ERA5 non disponibles : pas de détection d'AR")
    fig.text(0.03, 0.012, note + " · Isobares 4 hPa, masquées si p$_s$ < 800 hPa · ECMWF open data, CC-BY-4.0",
             fontsize=6.5, color="#444444")
    fig.savefig(job["out"], dpi=job["dpi"], pil_kwargs={"optimize": True})
    plt.close(fig)
    Path(job["npz"]).unlink()
    return job["out"]


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
    maps.mkdir(parents=True, exist_ok=True)
    for old in maps.glob("*.png"):
        old.unlink()
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
            job = dict(npz=str(npz), out=str(maps / fname), dpi=int(sc.get("dpi", 110)),
                       lat_north=float(sc["plot_lat_north"]), msl_mask_pa=80000.0,
                       quiver_every=int(sc.get("quiver_every", 8)), sites=cfg["sites"],
                       has_thr=thresholds is not None,
                       subtitle=(f"ECMWF HRES · run {base:%d/%m/%Y %H} UTC · +{step} h · "
                                 f"valide {vt:%a %d/%m %H} UTC"))
            futures.append(pool.submit(render, job))
            frames.append(dict(step=step, valid=vt.strftime("%Y-%m-%dT%H:%MZ"), file=f"maps/{fname}",
                               ar_sites=ar_sites))
            print(f"  +{step:3d}h {vt:%d/%m %HZ} ({time.time() - t0:4.1f}s)"
                  + (f"  AR : {', '.join(ar_sites)}" if ar_sites else ""), flush=True)
        for f in futures:
            f.result()

    manifest = dict(
        run=base.strftime("%Y-%m-%dT%HZ"),
        generated=dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
        model="ECMWF IFS HRES 0.25° (open data)",
        detection=("Wille et al. (2021), vIVT > 98e percentile mensuel ERA5 "
                   f"{cfg['climatology']['first_year']}-{cfg['climatology']['last_year']}, ≥ 20° de latitude")
        if thresholds is not None else None,
        sites=[dict(name=s["name"], lat=s["lat"], lon=s["lon"]) for s in cfg["sites"]],
        frames=frames,
    )
    (out_dir / "data").mkdir(exist_ok=True)
    (out_dir / "data" / "manifest.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False))
    print(f"{len(frames)} cartes dans {maps}")


if __name__ == "__main__":
    main()
