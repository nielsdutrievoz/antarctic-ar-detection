#!/usr/bin/env python
"""Calcule les seuils de Wille (98e percentile mensuel local du vIVT poléward ou de l'IWV) à partir d'ERA5.

À lancer une seule fois. Nécessite un compte Copernicus CDS et le fichier ~/.cdsapirc
(https://cds.climate.copernicus.eu/how-to-api), ainsi que l'acceptation de la licence ERA5.

    python build_climatology.py --config config.yaml            # téléchargement + calcul
    python build_climatology.py --config config.yaml --skip-download
"""
from __future__ import annotations

import argparse
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import xarray as xr

import arcore

ERA5_VAR = {"vivt": "vertical_integral_of_northward_water_vapour_flux",
            "iwv": "total_column_water_vapour"}


def download(cfg: dict) -> list[Path]:
    import cdsapi

    clim, det = cfg["climatology"], cfg["detection"]
    out_dir = arcore.cfg_path(cfg, clim["download_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)
    res = float(det["grid_res"])
    variable = det.get("variable", "vivt")
    files = [out_dir / f"era5_{variable}_{y}.nc"
             for y in range(int(clim["first_year"]), int(clim["last_year"]) + 1)]

    def get_year(target: Path) -> None:
        year = int(target.stem.rsplit("_", 1)[1])
        if target.exists() and target.stat().st_size > 0:
            print(f"[{year}] déjà présent", flush=True)
            return
        print(f"[{year}] requête CDS…", flush=True)
        tmp = target.with_suffix(".part")
        cdsapi.Client(quiet=True).retrieve(
            "reanalysis-era5-single-levels",
            {
                "product_type": ["reanalysis"],
                "variable": [ERA5_VAR[variable]],
                "year": [str(year)],
                "month": [f"{m:02d}" for m in range(1, 13)],
                "day": [f"{d:02d}" for d in range(1, 32)],
                "time": clim["hours"],
                "area": [det["lat_north"], 0, det["lat_south"], 360 - res],
                "grid": [res, res],
                "data_format": "netcdf",
                "download_format": "unarchived",
            },
            str(tmp),
        )
        tmp.rename(target)
        print(f"[{year}] téléchargé ({target.stat().st_size / 1e6:.0f} Mo)", flush=True)

    # quelques requêtes en parallèle : le CDS les met en file d'attente côté serveur
    with ThreadPoolExecutor(max_workers=int(clim.get("parallel_requests", 4))) as ex:
        list(ex.map(get_year, files))
    return files


def _read(path: Path) -> xr.DataArray:
    ds = xr.open_dataset(path)
    name = [v for v in ds.data_vars if ds[v].ndim == 3][0]
    da = ds[name]
    tdim = "valid_time" if "valid_time" in da.dims else "time"
    da = da.rename({tdim: "time"})
    for extra in ("number", "expver"):
        if extra in da.coords and extra not in da.dims:
            da = da.drop_vars(extra)
    return da


def compute_thresholds(cfg: dict, files: list[Path]) -> Path:
    det, clim = cfg["detection"], cfg["climatology"]
    lat, lon = arcore.target_grid(det)
    thr = np.zeros((12, lat.size, lon.size), dtype=np.float32)
    nsamples = np.zeros(12, dtype=np.int64)
    for m in range(1, 13):
        chunks = []
        for f in files:
            da = _read(f)
            sel = da.sel(time=da["time.month"] == m)
            arr = arcore.to_target(sel.values, sel["latitude"].values, sel["longitude"].values, lat, lon)
            arr = arr.astype(np.float32)
            chunks.append(arr if det.get("variable", "vivt") == "iwv" else arcore.poleward(arr))
            da.close()
        data = np.concatenate(chunks, axis=0)
        thr[m - 1] = np.percentile(data, det["percentile"], axis=0)
        nsamples[m - 1] = data.shape[0]
        print(f"mois {m:02d} : {data.shape[0]} champs, seuil médian {np.median(thr[m-1]):.1f} kg/m/s", flush=True)

    out = arcore.cfg_path(cfg, clim["output"])
    out.parent.mkdir(parents=True, exist_ok=True)
    ds = xr.Dataset(
        {"threshold": (("month", "lat", "lon"), thr,
                       {"long_name": f"{det['percentile']}th percentile of "
                                     + ("IWV" if det.get("variable") == "iwv" else "poleward vIVT")}),
         "nsamples": (("month",), nsamples)},
        coords={"month": np.arange(1, 13), "lat": lat, "lon": lon},
        attrs={"variable": det.get("variable", "vivt"),
               "source": "ERA5 " + ERA5_VAR[det.get("variable", "vivt")],
               "period": f"{clim['first_year']}-{clim['last_year']}",
               "method": "Wille et al. (2019 IWV / 2021 vIVT), percentile per calendar month and grid point"},
    )
    ds.to_netcdf(out)
    print(f"Seuils écrits dans {out}")
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", default=str(Path(__file__).with_name("config.yaml")))
    ap.add_argument("--skip-download", action="store_true", help="utiliser les fichiers déjà téléchargés")
    ap.add_argument("--variable", choices=["vivt", "iwv"],
                    help="remplace detection.variable ; les seuils vont dans data/thresholds_<variable>.nc")
    args = ap.parse_args(argv)
    cfg = arcore.load_config(args.config)
    if args.variable:
        cfg["detection"]["variable"] = args.variable
        cfg["climatology"]["output"] = f"data/thresholds_{args.variable}.nc"
    if args.skip_download:
        clim = cfg["climatology"]
        d = arcore.cfg_path(cfg, clim["download_dir"])
        files = [d / f"era5_{cfg['detection'].get('variable', 'vivt')}_{y}.nc" for y in range(int(clim["first_year"]), int(clim["last_year"]) + 1)]
        missing = [f for f in files if not f.exists()]
        if missing:
            sys.exit(f"Fichiers manquants : {[m.name for m in missing]}")
    else:
        files = download(cfg)
    compute_thresholds(cfg, files)


if __name__ == "__main__":
    main()
