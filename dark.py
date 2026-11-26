"""Détection DARK (Detecting ARs using their Kurvature), Buffet et al. (2026), WCD 7, 1189–1210.

Adaptation du code publié par V. Buffet (DARK_era5.py, v1.0, doi:10.5281/zenodo.20610709,
licence CC-BY-4.0) à un seul pas de temps :
  1. IVT total = sqrt(uIVT² + vIVT²) > 98e percentile local (fenêtre glissante de 15 jours) ;
  2. objets contigus (8-connexité, périodiques en longitude) ;
  3. suppression des objets de moins de MIN_AREA_KM2 ;
  4. axe central : squelette de l'objet → graphe → chemin le plus long et le mieux aligné
     sur l'axe principal (ACP) → prolongé jusqu'aux bords → lissé par B-spline ;
  5. AR si la longueur géodésique de cet axe est ≥ 2000 km, quelle que soit son orientation.

Écarts avec le code original : longueur calculée par la formule de haversine (le code utilise
geopy.geodesic, écart < 0,5 %) ; le module « AR-children » (suivi temporel des restes d'AR
après l'atterrissage) n'est pas inclus.
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage
from scipy.interpolate import RegularGridInterpolator, splev, splprep

# Valeur du code publié (v1.0). L'article indique 200 000 km² ; voir README.
MIN_AREA_KM2 = 20000
MIN_LENGTH_KM = 2000


def gridcell_area_km2(lat: np.ndarray, lon: np.ndarray) -> np.ndarray:
    R = 6371.0088
    dlat = np.abs(np.gradient(lat)) if lat.size > 1 else np.array([0.5])
    dlon = np.deg2rad(np.abs(np.diff(lon).mean()))
    return (np.deg2rad(dlat)[:, None] * R) * (dlon * R * np.cos(np.deg2rad(lat))[:, None]) * np.ones((1, lon.size))


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0088
    lat1, lon1, lat2, lon2 = map(np.deg2rad, [lat1, lon1, lat2, lon2])
    a = np.sin((lat2 - lat1) / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    return 2 * R * np.arcsin(np.sqrt(a))


def label_torus_lon(mask: np.ndarray):
    """Étiquetage 8-connexe, périodique en longitude."""
    lab, n = ndimage.label(mask, structure=np.ones((3, 3), int))
    if n == 0:
        return lab, 0
    parent = np.arange(n + 1)

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    left, right = lab[:, 0], lab[:, -1]
    H = lab.shape[0]
    for i in range(H):
        if left[i]:
            for j in (i - 1, i, i + 1):
                if 0 <= j < H and right[j]:
                    ra, rb = find(left[i]), find(right[j])
                    if ra != rb:
                        parent[max(ra, rb)] = min(ra, rb)
    roots = np.array([find(k) for k in range(n + 1)])
    uniq = np.unique(roots[roots > 0])
    remap = np.zeros(n + 1, dtype=int)
    remap[uniq] = np.arange(1, uniq.size + 1)
    return remap[roots][lab], uniq.size


def roll_by_largest_gap(mask: np.ndarray):
    """Décale les colonnes pour que la plus grande bande vide serve de raccord en longitude."""
    nlon = mask.shape[1]
    cols = np.unique(np.where(mask.any(axis=0))[0])
    if cols.size == 0:
        return mask, 0
    gaps = np.diff(np.r_[cols, cols[0] + nlon]) - 1
    k = int(np.argmax(gaps))
    if gaps[k] <= 0:
        return mask, 0
    seam = (cols[k] + 1 + gaps[k] // 2) % nlon
    return np.roll(mask, -seam, axis=1), -seam


def _skeleton_paths(skel: np.ndarray):
    import networkx as nx

    G = nx.Graph()
    for y, x in np.argwhere(skel):
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if (dy or dx) and 0 <= y + dy < skel.shape[0] and 0 <= x + dx < skel.shape[1] and skel[y + dy, x + dx]:
                    G.add_edge((y, x), (y + dy, x + dx))
    ends = [n for n in G.nodes if G.degree[n] == 1]
    paths = []
    for i in range(len(ends)):
        for j in range(i + 1, len(ends)):
            try:
                paths.append(nx.shortest_path(G, ends[i], ends[j]))
            except nx.NetworkXNoPath:
                pass
    return paths


def _pca_axis(mask):
    pts = np.argwhere(mask)
    if len(pts) < 2:
        return np.array([1.0, 0.0])
    _, _, vh = np.linalg.svd(pts - pts.mean(0), full_matrices=False)
    return vh[0]


def _path_score(path, axis, shape):
    c = np.array(path)
    if len(c) < 2:
        return -np.inf
    length = np.sum(np.linalg.norm(np.diff(c, axis=0), axis=1))
    u = (c[-1] - c[0]) / (np.linalg.norm(c[-1] - c[0]) + 1e-9)
    return length * abs(np.dot(u, axis)) * (np.ptp(c[:, 0]) / shape[0])


def _fallback(mask):
    ys, xs = np.where(mask.any(axis=1))[0], np.where(mask.any(axis=0))[0]
    if ys.size == 0:
        return None
    rows = np.arange(ys.min(), ys.max() + 1)
    return np.column_stack([rows, np.full_like(rows, int(round(xs.mean())))])


def _extend(path, mask, max_ext=25):
    if path is None or len(path) < 2:
        return path

    def one(p0, p1):
        v = (p0 - p1).astype(float)
        v /= np.linalg.norm(v) + 1e-9
        for i in range(1, max_ext + 1):
            yy, xx = np.round(p0 + i * v).astype(int)
            if not (0 <= yy < mask.shape[0] and 0 <= xx < mask.shape[1]):
                break
            if not mask[yy, xx]:
                return np.round(p0 + (i - 1) * v).astype(int)
        return p0

    P = np.asarray(path)
    return np.vstack([one(P[0], P[1]), P[1:-1], one(P[-1], P[-2])])


def _smooth(path, n_points=200, s=300):
    if path is None or len(path) < 3:
        return path
    try:
        tck, _ = splprep([path[:, 0].astype(float), path[:, 1].astype(float)], s=s)
        ys, xs = splev(np.linspace(0, 1, n_points), tck)
        return np.column_stack([ys, xs])
    except Exception:
        return path


def centerline_length_km(mask: np.ndarray, lat: np.ndarray, lon: np.ndarray):
    """Longueur (km) de l'axe central lissé d'un objet, et l'axe (lon, lat)."""
    from skimage.morphology import skeletonize

    rolled, shift = roll_by_largest_gap(mask)
    lon_r = np.roll(lon, shift)
    paths = _skeleton_paths(skeletonize(rolled))
    if paths:
        axis = _pca_axis(rolled)
        cl = np.array(max(paths, key=lambda p: _path_score(p, axis, rolled.shape)))
    else:
        cl = _fallback(rolled)
        if cl is None:
            return 0.0, None
    cl = _smooth(_extend(cl, rolled), n_points=200, s=300).astype(float)
    H, W = lat.size, lon_r.size
    cl[:, 0] = np.clip(cl[:, 0], 0, H - 1)
    cl[:, 1] = np.mod(cl[:, 1], W)
    iy, ix = np.arange(H), np.arange(W)
    plat = RegularGridInterpolator((iy, ix), np.tile(lat[:, None], (1, W)), bounds_error=False)(cl)
    lr = np.deg2rad(lon_r)
    psin = RegularGridInterpolator((iy, ix), np.tile(np.sin(lr)[None, :], (H, 1)), bounds_error=False)(cl)
    pcos = RegularGridInterpolator((iy, ix), np.tile(np.cos(lr)[None, :], (H, 1)), bounds_error=False)(cl)
    plon = np.rad2deg(np.arctan2(psin, pcos))
    ok = np.isfinite(plat) & np.isfinite(plon)
    plat, plon = np.clip(plat[ok], -90, 90), plon[ok]
    if plat.size < 2:
        return 0.0, None
    L = float(np.sum(haversine_km(plat[:-1], plon[:-1], plat[1:], plon[1:])))
    return L, (np.mod(plon, 360.0), plat)


def detect_dark(ivt: np.ndarray, thr: np.ndarray, lat: np.ndarray, lon: np.ndarray,
                min_area_km2: float = MIN_AREA_KM2, min_length_km: float = MIN_LENGTH_KM) -> np.ndarray:
    """Masque AR DARK (ny, nx) pour un champ d'IVT total et son seuil."""
    exceed = ivt > thr
    lab, n = label_torus_lon(exceed)
    keep = np.zeros_like(exceed)
    if n == 0:
        return keep
    area = gridcell_area_km2(lat, lon)
    sums = np.bincount(lab.ravel(), weights=area.ravel(), minlength=n + 1)
    for k in np.where(sums >= min_area_km2)[0]:
        if k == 0:
            continue
        comp = lab == k
        if comp.sum() < 30:
            continue
        rolled, shift = roll_by_largest_gap(comp)
        lon_r = np.roll(lon, shift)
        ys, xs = np.where(rolled)
        proxy = haversine_km(lat[ys.min()], lon_r[xs.min()], lat[ys.max()], lon_r[xs.max()])
        if proxy < 0.5 * min_length_km:
            continue
        L, _ = centerline_length_km(comp, lat, lon)
        if L >= min_length_km:
            keep |= comp
    return keep


def pentad_index(t, centres: np.ndarray) -> int:
    """Indice de la pentade dont le centre est le plus proche du jour (calendrier bissextile 1..366)."""
    import datetime as dt

    doy = t.timetuple().tm_yday
    leap = (t.year % 4 == 0) and (t.year % 100 != 0 or t.year % 400 == 0)
    if not leap and doy >= 60:
        doy += 1
    d = np.abs(((centres - doy + 183) % 366) - 183)
    return int(np.argmin(d))
