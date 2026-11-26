"""Fonctions communes : configuration, grille, intégration du vIVT, détection Wille.

Détection (Wille et al. 2021 ; code v2.4 vIVT Antarctique, Zenodo 10.5281/zenodo.7990215) :
  1. vIVT poléward = -vIVT (transport vers le sud compté positif), valeurs < 0 mises à 0.
  2. Seuil = 98e percentile mensuel local de cette quantité (climatologie).
  3. Pixels > seuil entre 37.5°S et 85°S.
  4. On garde les objets contigus dont l'extension méridienne dépasse 20°.

Le point 4 est ici implémenté par étiquetage de composantes connexes (8-connexité,
périodique en longitude), plus simple que les découpages successifs du script
original mais fondé sur le même critère. Les catalogues peuvent donc différer
légèrement de ceux de Wille.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import yaml
from scipy import ndimage

G = 9.80665
EARTH_RADIUS_KM = 6371.0


# --------------------------------------------------------------------------- config
def load_config(path: str | Path) -> dict:
    path = Path(path).resolve()
    with open(path) as f:
        cfg = yaml.safe_load(f)
    cfg["_base"] = path.parent
    return cfg


def cfg_path(cfg: dict, rel: str) -> Path:
    p = Path(rel)
    return p if p.is_absolute() else cfg["_base"] / p


# --------------------------------------------------------------------------- grille
def target_grid(det: dict) -> tuple[np.ndarray, np.ndarray]:
    """Latitudes (nord -> sud) et longitudes 0..360 de la grille de détection."""
    res = float(det["grid_res"])
    lat = np.round(np.arange(det["lat_north"], det["lat_south"] - res / 2, -res), 6)
    lon = np.round(np.arange(0.0, 360.0, res), 6)
    return lat, lon


def to_target(field: np.ndarray, src_lat: np.ndarray, src_lon: np.ndarray,
              lat: np.ndarray, lon: np.ndarray) -> np.ndarray:
    """Extrait les points de la grille cible d'une grille régulière plus fine (sous-échantillonnage).

    Les deux dernières dimensions de `field` sont (lat, lon). src_lon peut être en -180..180.
    """
    src_lon360 = np.mod(src_lon, 360.0)
    ilat = _match(src_lat, lat)
    ilon = _match(src_lon360, lon)
    return field[..., ilat, :][..., ilon]


def _match(src: np.ndarray, dst: np.ndarray) -> np.ndarray:
    idx = np.array([int(np.argmin(np.abs(src - d))) for d in dst])
    err = np.abs(src[idx] - dst).max()
    if err > 1e-3:
        raise ValueError(f"La grille source ne contient pas la grille cible (écart {err:.3f}°)")
    return idx


# --------------------------------------------------------------------------- vIVT
def vivt_from_levels(q: np.ndarray, v: np.ndarray, sp: np.ndarray, levels_hpa) -> np.ndarray:
    """vIVT (kg m-1 s-1) = (1/g) ∫ q v dp sur la colonne au-dessus du sol.

    q, v : (..., nlev, ny, nx) ; sp : (..., ny, nx) en Pa ; levels en hPa, ordre quelconque.
    Méthode des couches : chaque niveau représente la couche comprise entre les
    mi-niveaux voisins ; les niveaux sous la surface sont ignorés et la couche du
    plus bas niveau au-dessus du sol descend jusqu'à la pression de surface.
    """
    p = np.asarray(levels_hpa, dtype=float) * 100.0
    order = np.argsort(p)[::-1]                    # du bas (haute pression) vers le haut
    p = p[order]
    q = np.take(q, order, axis=-3)
    v = np.take(v, order, axis=-3)
    nlev = p.size
    upper = np.empty(nlev)
    upper[:-1] = 0.5 * (p[:-1] + p[1:])
    upper[-1] = p[-1] - 0.5 * (p[-2] - p[-1])      # demi-couche au-dessus du dernier niveau

    total = np.zeros(q.shape[:-3] + q.shape[-2:], dtype=np.float64)
    for k in range(nlev):
        if k == 0:
            lo = sp                                # niveau le plus bas : jusqu'au sol
        else:
            mid = 0.5 * (p[k - 1] + p[k])
            # si le niveau inférieur est sous terre, cette couche descend jusqu'au sol
            lo = np.where(p[k - 1] > sp, sp, mid)
        dp = np.clip(np.minimum(lo, sp) - upper[k], 0.0, None)
        dp = np.where(p[k] > sp, 0.0, dp)          # niveau sous terre
        total += q[..., k, :, :] * v[..., k, :, :] * dp
    return (total / G).astype(np.float32)


def poleward(vivt: np.ndarray) -> np.ndarray:
    """Transport vers le pôle Sud compté positif, le reste à 0 (comme Wille)."""
    return np.clip(-vivt, 0.0, None)


# --------------------------------------------------------------------------- détection
_STRUCT = np.ones((3, 3), dtype=bool)


def detect_ar(field: np.ndarray, threshold: np.ndarray, lat: np.ndarray,
              min_lat_extent: float) -> np.ndarray:
    """Masque AR booléen (ny, nx) pour un champ poléward 2-D et son seuil 2-D."""
    exceed = field > threshold
    if not exceed.any():
        return np.zeros_like(exceed)
    labels, n = ndimage.label(exceed, structure=_STRUCT)
    # périodicité en longitude : fusion des objets qui touchent les bords 0° et 360°
    if n:
        left, right = labels[:, 0], labels[:, -1]
        parent = np.arange(n + 1)

        def find(a):
            while parent[a] != a:
                parent[a] = parent[parent[a]]
                a = parent[a]
            return a

        ny = labels.shape[0]
        for j in range(ny):
            for dj in (-1, 0, 1):
                jj = j + dj
                if 0 <= jj < ny and left[j] and right[jj]:
                    ra, rb = find(left[j]), find(right[jj])
                    if ra != rb:
                        parent[max(ra, rb)] = min(ra, rb)
        roots = np.array([find(i) for i in range(n + 1)])
        labels = roots[labels]
    ids = np.unique(labels[labels > 0])
    mask = np.zeros_like(exceed)
    lat2d = np.broadcast_to(lat[:, None], labels.shape)
    for i in ids:
        sel = labels == i
        lats = lat2d[sel]
        if lats.max() - lats.min() >= min_lat_extent:
            mask |= sel
    return mask


# --------------------------------------------------------------------------- sites
def site_mask(site: dict, lat: np.ndarray, lon: np.ndarray) -> np.ndarray:
    """Pixels de la grille associés au site (point le plus proche, ou disque de rayon radius_km)."""
    lat2, lon2 = np.meshgrid(lat, lon, indexing="ij")
    d = haversine_km(site["lat"], site["lon"], lat2, lon2)
    r = float(site.get("radius_km", 0) or 0)
    mask = d <= r if r > 0 else np.zeros_like(d, dtype=bool)
    if not mask.any():
        mask = d == d.min()
    return mask


def haversine_km(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(np.radians, (lat1, lon1, lat2, lon2))
    a = np.sin((lat2 - lat1) / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    return 2 * EARTH_RADIUS_KM * np.arcsin(np.sqrt(a))
