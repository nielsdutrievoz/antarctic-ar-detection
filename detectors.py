"""Fait tourner les algorithmes de détection disponibles (selon les seuils présents) sur un pas de temps.

Champs attendus sur la grille « données » (0.5°, de site.data_lat_north au pôle) :
uivt, vivt (kg m-1 s-1) et iwv (kg m-2).
"""
from __future__ import annotations

import datetime as dt

import numpy as np
import xarray as xr

import arcore
import dark
from algos import ORDER


class Detectors:
    def __init__(self, cfg: dict, lat: np.ndarray, lon: np.ndarray):
        det, clim = cfg["detection"], cfg["climatology"]
        self.min_lat_extent = float(det["min_lat_extent"])
        self.lat, self.lon = lat, lon
        # grille de Wille (37.5–85°S), sous-ensemble de la grille des données
        self.wlat, self.wlon = arcore.target_grid(det)
        self.wi = arcore._match(lat, self.wlat)
        self.thr = {}
        for algo, key, default in (("wille_vivt", "output", "data/thresholds_vivt.nc"),
                                   ("wille_iwv", "output_iwv", "data/thresholds_iwv.nc"),
                                   ("dark", "output_dark", "data/thresholds_dark.nc")):
            f = arcore.cfg_path(cfg, clim.get(key, default))
            if f.exists():
                self.thr[algo] = xr.load_dataset(f)
        if "dark" in self.thr:
            t = self.thr["dark"]
            self.di = arcore._match(lat, t["lat"].values)       # lignes de la grille DARK dans les données
            self.dark_lat = t["lat"].values
            self.centres = t["doy_centre"].values
        self.site_masks = {
            algo: {s["name"]: arcore.site_mask(s, *self.grid(algo)) for s in cfg["sites"]}
            for algo in self.available
        }

    @property
    def available(self) -> list[str]:
        return [a for a in ORDER if a in self.thr]

    def grid(self, algo):
        return (self.dark_lat, self.lon) if algo == "dark" else (self.wlat, self.wlon)

    def run(self, t: dt.datetime, f: dict) -> dict:
        """{algo: masque} pour le pas de temps t."""
        out = {}
        if "wille_vivt" in self.thr:
            thr = self.thr["wille_vivt"]["threshold"].sel(month=t.month).values
            out["wille_vivt"] = arcore.detect_ar(arcore.poleward(f["vivt"][self.wi]), thr,
                                                 self.wlat, self.min_lat_extent)
        if "wille_iwv" in self.thr:
            thr = self.thr["wille_iwv"]["threshold"].sel(month=t.month).values
            out["wille_iwv"] = arcore.detect_ar(f["iwv"][self.wi], thr, self.wlat, self.min_lat_extent)
        if "dark" in self.thr:
            p = dark.pentad_index(t, self.centres)
            thr = self.thr["dark"]["threshold"].isel(pentad=p).values
            ivt = np.hypot(f["uivt"], f["vivt"])[self.di]
            out["dark"] = dark.detect_dark(ivt, thr, self.dark_lat, self.lon)
        return out

    def npz_fields(self, masks: dict) -> dict:
        """Masques et leurs grilles, sous la forme attendue par maprender."""
        d = {}
        for algo, m in masks.items():
            mlat, mlon = self.grid(algo)
            d[algo], d[f"{algo}_lat"], d[f"{algo}_lon"] = m, mlat, mlon
        return d

    def sites_hit(self, masks: dict) -> dict:
        return {algo: [n for n, sm in self.site_masks[algo].items() if m[sm].any()] for algo, m in masks.items()}
