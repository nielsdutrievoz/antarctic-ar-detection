#!/usr/bin/env python
"""Seuils de l'algorithme DARK (Buffet et al. 2026) : 98e percentile de l'IVT total,
fenêtre glissante de 15 jours, par point de grille, de 15°S au pôle Sud.

Différence avec le code original : le seuil est calculé pour 73 pentades (fenêtre de 15 jours
centrée sur chaque pentade) au lieu des 366 jours de l'année, pour que le fichier reste léger
(~15 Mo) ; chaque date utilise la pentade la plus proche.

    python build_climatology_dark.py                  # téléchargement ERA5 + calcul
    python build_climatology_dark.py --skip-download
"""
from __future__ import annotations

import argparse
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import xarray as xr

import arcore

VARS = ["vertical_integral_of_eastward_water_vapour_flux",
        "vertical_integral_of_northward_water_vapour_flux"]
NORTH, SOUTH = -15.0, -90.0
WINDOW_D = 15
N_PENTADS = 73


def leap_doy(t: np.ndarray) -> np.ndarray:
    """Jour de l'année « bissextile » 1..366 (comme le code DARK : 1er mars = 61 tous les ans)."""
    t = t.astype("datetime64[D]")
    years = t.astype("datetime64[Y]").astype(int) + 1970
    doy = (t - t.astype("datetime64[Y]")).astype(int) + 1
    leap = (years % 4 == 0) & ((years % 100 != 0) | (years % 400 == 0))
    return np.where(~leap & (doy >= 60), doy + 1, doy)


def pentad_centres() -> np.ndarray:
    return np.round(np.linspace(1, 366, N_PENTADS, endpoint=False) + 366 / N_PENTADS / 2).astype(int)


def download(cfg: dict, years: list[int], workers: int) -> list[Path]:
    import cdsapi

    res = float(cfg["detection"]["grid_res"])
    out_dir = arcore.cfg_path(cfg, cfg["climatology"]["download_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)
    files = [out_dir / f"era5_ivt_{y}.nc" for y in years]

    def get_year(target: Path) -> None:
        year = int(target.stem.rsplit("_", 1)[1])
        if target.exists() and target.stat().st_size > 0:
            print(f"[{year}] déjà présent", flush=True)
            return
        print(f"[{year}] requête CDS…", flush=True)
        tmp = target.with_suffix(".part")
        cdsapi.Client(quiet=True).retrieve(
            "reanalysis-era5-single-levels",
            {"product_type": ["reanalysis"], "variable": VARS, "year": [str(year)],
             "month": [f"{m:02d}" for m in range(1, 13)], "day": [f"{d:02d}" for d in range(1, 32)],
             "time": cfg["climatology"]["hours"], "area": [NORTH, 0, SOUTH, 360 - res],
             "grid": [res, res], "data_format": "netcdf", "download_format": "unarchived"},
            str(tmp))
        tmp.rename(target)
        print(f"[{year}] téléchargé ({target.stat().st_size / 1e6:.0f} Mo)", flush=True)

    with ThreadPoolExecutor(max_workers=workers) as ex:
        list(ex.map(get_year, files))
    return files


def to_cache(f: Path, cache: Path) -> tuple[Path, Path, np.ndarray, np.ndarray]:
    """IVT total d'une année en float16 sur disque (memmap), pour lire ensuite par bandes de latitude."""
    out = cache / (f.stem + ".ivt.npy")
    tfile = cache / (f.stem + ".doy.npy")
    ds = xr.open_dataset(f)
    lat = ds["latitude"].values
    lon = np.mod(ds["longitude"].values, 360.0)
    if not out.exists():
        tdim = "valid_time" if "valid_time" in ds.dims else "time"
        ivt = np.hypot(ds["viwve"].values, ds["viwvn"].values).astype(np.float16)
        np.save(out, ivt)
        np.save(tfile, leap_doy(ds[tdim].values))
    ds.close()
    return out, tfile, lat, lon


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", default=str(Path(__file__).with_name("config.yaml")))
    ap.add_argument("--skip-download", action="store_true")
    ap.add_argument("--workers", type=int, default=3, help="requêtes CDS en parallèle")
    ap.add_argument("--band", type=int, default=8, help="lignes de latitude traitées à la fois")
    args = ap.parse_args(argv)
    cfg = arcore.load_config(args.config)
    clim = cfg["climatology"]
    years = list(range(int(clim["first_year"]), int(clim["last_year"]) + 1))
    out_dir = arcore.cfg_path(cfg, clim["download_dir"])
    files = [out_dir / f"era5_ivt_{y}.nc" for y in years]
    if args.skip_download:
        missing = [f.name for f in files if not f.exists()]
        if missing:
            sys.exit(f"Fichiers manquants : {missing}")
    else:
        files = download(cfg, years, args.workers)

    cache = out_dir / "ivt_cache"
    cache.mkdir(exist_ok=True)
    entries = []
    for f in files:
        entries.append(to_cache(f, cache))
        print(f"cache {f.name}", flush=True)
    lat, lon = entries[0][2], entries[0][3]
    order = np.argsort(lon)
    doys = np.concatenate([np.load(e[1]) for e in entries])
    centres = pentad_centres()
    half = WINDOW_D // 2
    windows = []
    for c in centres:
        w = ((np.arange(c - half, c + half + 1) - 1) % 366) + 1
        windows.append(np.isin(doys, w))

    thr = np.zeros((N_PENTADS, lat.size, lon.size), dtype=np.float32)
    mm = [np.load(e[0], mmap_mode="r") for e in entries]
    for r0 in range(0, lat.size, args.band):
        r1 = min(lat.size, r0 + args.band)
        band = np.concatenate([m[:, r0:r1, :] for m in mm], axis=0).astype(np.float32)
        for p, sel in enumerate(windows):
            thr[p, r0:r1] = np.percentile(band[sel], 98, axis=0)
        print(f"latitudes {lat[r0]:.1f} → {lat[r1 - 1]:.1f} : ok", flush=True)

    out = arcore.cfg_path(cfg, clim.get("output_dark", "data/thresholds_dark.nc"))
    xr.Dataset(
        {"threshold": (("pentad", "lat", "lon"), thr[:, :, order],
                       {"long_name": "98th percentile of total IVT, 15-day rolling window", "units": "kg m-1 s-1"})},
        coords={"pentad": np.arange(N_PENTADS), "doy_centre": ("pentad", centres), "lat": lat, "lon": lon[order]},
        attrs={"variable": "ivt", "method": "DARK (Buffet et al. 2026), 15-day window centred on each pentad",
               "source": "ERA5 vertical integrals of eastward/northward water vapour flux",
               "period": f"{years[0]}-{years[-1]}"},
    ).to_netcdf(out, encoding={"threshold": {"dtype": "int16", "scale_factor": 0.1, "_FillValue": -1,
                                             "zlib": True, "complevel": 5}})
    print(f"Seuils DARK écrits dans {out} ({out.stat().st_size / 1e6:.1f} Mo)")


if __name__ == "__main__":
    main()
