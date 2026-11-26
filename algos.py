"""Algorithmes de détection disponibles sur le site : couleurs, textes et références."""

ALGOS = {
    "wille_vivt": dict(
        label="Wille vIVT", color="#00e5ff", ring85=True,
        name={"fr": "cyan", "en": "cyan"},
        ref={"fr": "Détection AR : Wille et al. (2021), JGR Atmospheres, doi:10.1029/2020JD033788 · "
                   "vIVT vers le pôle > 98e percentile mensuel ERA5, ≥ 20° de latitude, 37,5–85°S",
             "en": "AR detection: Wille et al. (2021), JGR Atmospheres, doi:10.1029/2020JD033788 · "
                   "poleward vIVT > monthly ERA5 98th percentile, ≥ 20° latitude, 37.5–85°S"},
    ),
    "wille_iwv": dict(
        label="Wille IWV", color="#76ff03", ring85=True,
        name={"fr": "vert", "en": "green"},
        ref={"fr": "Détection AR : Wille et al. (2019), Nature Geoscience, doi:10.1038/s41561-019-0460-1 · "
                   "IWV > 98e percentile mensuel ERA5, ≥ 20° de latitude, 37,5–85°S",
             "en": "AR detection: Wille et al. (2019), Nature Geoscience, doi:10.1038/s41561-019-0460-1 · "
                   "IWV > monthly ERA5 98th percentile, ≥ 20° latitude, 37.5–85°S"},
    ),
    "dark": dict(
        label="DARK", color="#ff2bd6", ring85=False,
        name={"fr": "rose", "en": "pink"},
        ref={"fr": "Détection AR : DARK, Buffet et al. (2026), Weather Clim. Dynam., doi:10.5194/wcd-7-1189-2026 · "
                   "IVT > 98e percentile ERA5 (15 j), axe courbe ≥ 2000 km, 15–90°S",
             "en": "AR detection: DARK, Buffet et al. (2026), Weather Clim. Dynam., doi:10.5194/wcd-7-1189-2026 · "
                   "IVT > ERA5 98th percentile (15 d), curved axis ≥ 2000 km, 15–90°S"},
    ),
}
ORDER = ["wille_vivt", "wille_iwv", "dark"]


def legend_line(algo: str, lang: str) -> str:
    a = ALGOS[algo]
    if lang == "fr":
        s = f"Contour {a['name']['fr']} : rivière atmosphérique ({a['label']})"
        return s + (" · pointillés : limite de détection 85°S" if a["ring85"] else "")
    s = f"{a['name']['en'].capitalize()} contour: atmospheric river ({a['label']})"
    return s + (" · dashed: 85°S detection limit" if a["ring85"] else "")
