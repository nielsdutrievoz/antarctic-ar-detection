"""Téléchargement parallèle de champs ECMWF ENS open data par requêtes HTTP Range.

Chaque échéance est un gros fichier GRIB2 (~4.5 Go) accompagné d'un index JSON qui
donne la position de chaque champ. On ne télécharge que les champs utiles, en
parallèle, et on les décode en mémoire, sans fichier temporaire.
"""
from __future__ import annotations

import datetime as dt
import json
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

import numpy as np

ROOTS = {
    "ecmwf": "https://data.ecmwf.int/forecasts",
    "aws": "https://ecmwf-forecasts.s3.eu-central-1.amazonaws.com",
    "azure": "https://ai4edataeuwest.blob.core.windows.net/ecmwf",
    "google": "https://storage.googleapis.com/ecmwf-open-data",
}
UA = {"User-Agent": "ar-alert/1.0"}


STREAMS = {"enfo": "ef", "oper": "fc"}   # ensemble (50 membres) / déterministe HRES


def _url(root: str, base: dt.datetime, step: int, ext: str, stream: str = "enfo") -> str:
    kind = STREAMS[stream]
    return (f"{ROOTS[root]}/{base:%Y%m%d}/{base:%H}z/ifs/0p25/{stream}/"
            f"{base:%Y%m%d%H}0000-{step}h-{stream}-{kind}.{ext}")


def _get(url: str, rng: tuple[int, int] | None = None, retries: int = 7) -> bytes:
    headers = dict(UA)
    if rng:
        headers["Range"] = f"bytes={rng[0]}-{rng[1]}"
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=120) as r:
                return r.read()
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            if isinstance(e, urllib.error.HTTPError) and e.code == 404:
                raise
            time.sleep(2 ** attempt)
    raise RuntimeError(f"Échec du téléchargement : {url}")


def index(root: str, base: dt.datetime, step: int, stream: str = "enfo") -> list[dict]:
    txt = _get(_url(root, base, step, "index", stream)).decode()
    return [json.loads(line) for line in txt.splitlines() if line.strip()]


def available(root: str, base: dt.datetime, step: int, stream: str = "enfo") -> bool:
    try:
        req = urllib.request.Request(_url(root, base, step, "index", stream), headers=UA, method="HEAD")
        with urllib.request.urlopen(req, timeout=30):
            return True
    except Exception:
        return False


def latest(root: str, max_step: int, now: dt.datetime | None = None, stream: str = "enfo") -> dt.datetime:
    """Dernier run 00/12 UTC dont l'échéance max_step est publiée."""
    now = now or dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)
    t = now.replace(minute=0, second=0, microsecond=0, hour=0 if now.hour < 12 else 12)
    for _ in range(8):
        if available(root, t, max_step, stream):
            return t
        t -= dt.timedelta(hours=12)
    raise RuntimeError(f"Aucun run récent trouvé ({stream}).")


def fetch(root: str, base: dt.datetime, step: int, wanted, workers: int = 8, stream: str = "enfo"):
    """Télécharge les champs de l'échéance pour lesquels wanted(entrée_index) est vrai.

    Renvoie une liste de (entrée_index, bytes GRIB).
    """
    entries = sorted((e for e in index(root, base, step, stream) if wanted(e)), key=lambda e: e["_offset"])
    # regroupe les champs contigus dans le fichier pour limiter le nombre de requêtes
    groups, cur = [], []
    for e in entries:
        if cur and e["_offset"] == cur[-1]["_offset"] + cur[-1]["_length"] \
                and sum(x["_length"] for x in cur) < 32e6:
            cur.append(e)
        else:
            if cur:
                groups.append(cur)
            cur = [e]
    if cur:
        groups.append(cur)
    url = _url(root, base, step, "grib2", stream)

    def job(g):
        start = g[0]["_offset"]
        data = _get(url, (start, g[-1]["_offset"] + g[-1]["_length"] - 1))
        return [(e, data[e["_offset"] - start: e["_offset"] - start + e["_length"]]) for e in g]

    with ThreadPoolExecutor(max_workers=workers) as ex:
        return [item for part in ex.map(job, groups) for item in part]


def decode(msg: bytes):
    """Décode un message GRIB : (valeurs 2-D, latitudes, longitudes)."""
    import eccodes

    gid = eccodes.codes_new_from_message(msg)
    try:
        ni, nj = eccodes.codes_get(gid, "Ni"), eccodes.codes_get(gid, "Nj")
        lat0 = eccodes.codes_get(gid, "latitudeOfFirstGridPointInDegrees")
        lon0 = eccodes.codes_get(gid, "longitudeOfFirstGridPointInDegrees")
        dlat = eccodes.codes_get(gid, "jDirectionIncrementInDegrees")
        dlon = eccodes.codes_get(gid, "iDirectionIncrementInDegrees")
        sign = 1 if eccodes.codes_get(gid, "jScansPositively") else -1
        vals = eccodes.codes_get_values(gid).reshape(nj, ni)
    finally:
        eccodes.codes_release(gid)
    return vals, lat0 + sign * dlat * np.arange(nj), lon0 + dlon * np.arange(ni)
