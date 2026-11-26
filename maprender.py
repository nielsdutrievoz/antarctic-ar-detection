"""Rendu des cartes polaires sud (IVT, MSLP, contours AR, sites) en français et en anglais.

Une carte est dessinée une seule fois ; seuls les textes changent entre les langues.
Les PNG sont réduits à une palette de 256 couleurs (2 à 3 fois plus légers).
"""
from __future__ import annotations

import datetime as dt
import io
import warnings
from pathlib import Path

import numpy as np

LANGS = ("fr", "en")
TEXT = {
    "fr": dict(title="IVT, pression au niveau de la mer et rivières atmosphériques",
               ar="Contour magenta : rivière atmosphérique",
               algo="Détection AR : Wille et al. (2021), JGR Atmospheres, doi:10.1029/2020JD033788 · vIVT > 98e percentile mensuel ERA5, ≥ 20° de latitude",
               no_ar="Seuils ERA5 non disponibles : pas de détection d'AR",
               isobars="Isobares 4 hPa, masquées si p$_s$ < 800 hPa"),
    "en": dict(title="IVT, mean sea-level pressure and atmospheric rivers",
               ar="Magenta contour: atmospheric river",
               algo="AR detection: Wille et al. (2021), JGR Atmospheres, doi:10.1029/2020JD033788 · vIVT > monthly ERA5 98th percentile, ≥ 20° latitude",
               no_ar="ERA5 thresholds not available: no AR detection",
               isobars="Isobars every 4 hPa, masked where p$_s$ < 800 hPa"),
}
DAYS = {"fr": ["lun.", "mar.", "mer.", "jeu.", "ven.", "sam.", "dim."],
        "en": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]}
MONTHS_EN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def fmt_time(t: dt.datetime, lang: str, weekday: bool = True) -> str:
    """Date-heure UTC lisible, sans dépendre de la locale du système."""
    wd = DAYS[lang][t.weekday()] + " " if weekday else ""
    if lang == "fr":
        return f"{wd}{t:%d/%m/%Y %H} UTC"
    return f"{wd}{t.day} {MONTHS_EN[t.month - 1]} {t.year} {t:%H} UTC"


def render(job: dict) -> list[str]:
    """Dessine une carte et l'enregistre dans chaque langue.

    job : npz (champs lat, lon, uivt, vivt, msl [hPa], sp [Pa], et facultativement ar, ar_lat, ar_lon),
          outputs {lang: chemin png}, subtitles {lang: texte}, credit, sites, has_thr,
          lat_north, dpi, quiver_every.
    Exécuté dans un processus séparé (matplotlib n'est pas thread-safe).
    """
    warnings.filterwarnings("ignore")
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.patheffects as patheffects
    import matplotlib.path as mpath
    import matplotlib.pyplot as plt
    from matplotlib.colors import BoundaryNorm, ListedColormap
    from PIL import Image
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    from cartopy.util import add_cyclic_point

    d = np.load(job["npz"])
    lat, lon = d["lat"], d["lon"]
    ivt = np.hypot(d["uivt"], d["vivt"])
    dpi = int(job.get("dpi", 150))

    fig = plt.figure(figsize=(8, 8.6), dpi=dpi)
    ax = fig.add_axes([0.02, 0.135, 0.96, 0.805], projection=ccrs.SouthPolarStereo())
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
    cf = ax.contourf(X, Y, ivt_c, levels=levels, cmap=cmap, norm=norm, extend="max", transform=pc)

    ax.add_feature(cfeature.OCEAN.with_scale("110m"), facecolor="#eef3f7", zorder=0)
    ax.add_feature(cfeature.LAND.with_scale("50m"), facecolor="#ffffff", zorder=0)
    ax.coastlines("50m", linewidth=0.6, color="#3a3a3a")

    # isobares (masquées sur le haut plateau, où la réduction au niveau de la mer n'a pas de sens)
    msl = np.where(d["sp"] < 80000.0, np.nan, d["msl"])
    msl_c, _ = add_cyclic_point(msl, coord=lon)
    cs = ax.contour(X, Y, msl_c, levels=np.arange(920, 1060, 4), colors="#1f1f1f",
                    linewidths=0.6, transform=pc)
    ax.clabel(cs, cs.levels[::2], fontsize=6, fmt="%d", inline_spacing=2)

    # vecteurs IVT là où le transport est significatif
    step = int(job.get("quiver_every", 8))
    sl = (slice(None, None, step), slice(None, None, step))
    show = ivt[sl] >= 250
    if show.any():
        lon2, lat2 = np.meshgrid(lon[sl[1]], lat[sl[0]])
        ax.quiver(lon2[show], lat2[show], d["uivt"][sl][show], d["vivt"][sl][show], transform=pc,
                  scale=12000, width=0.0018, color="#202020", alpha=0.75)

    if "ar" in d.files and d["ar"].any():
        ar_c, lon_ar = add_cyclic_point(d["ar"].astype(float), coord=d["ar_lon"])
        XA, YA = np.meshgrid(lon_ar, d["ar_lat"])
        ax.contour(XA, YA, ar_c, levels=[0.5], colors="#d4006a", linewidths=2.0, transform=pc)

    halo = [patheffects.withStroke(linewidth=3, foreground="white")]
    for s in job["sites"]:
        ax.plot(s["lon"], s["lat"], marker="o", ms=6, mfc="#00a0b0", mec="#0f1e2e", mew=1.0,
                transform=pc, zorder=10)
        ax.text(s["lon"], s["lat"], "  " + s["name"], fontsize=9, fontweight="bold", transform=pc,
                ha="left", va="center", color="#0f1e2e", path_effects=halo, zorder=11)

    gl = ax.gridlines(pc, linewidth=0.3, color="#888888", alpha=0.6, linestyle="--")
    gl.ylocator = matplotlib.ticker.FixedLocator([-80, -70, -60, -50, -40, -30])

    cax = fig.add_axes([0.15, 0.088, 0.7, 0.016])
    cb = fig.colorbar(cf, cax=cax, orientation="horizontal", ticks=levels)
    cb.set_label("IVT (kg m$^{-1}$ s$^{-1}$)", fontsize=8)
    cb.ax.tick_params(labelsize=7)

    t_title = fig.text(0.03, 0.965, "", fontsize=10.5, weight="bold")
    t_sub = fig.text(0.03, 0.945, "", fontsize=8.5, color="#333333")
    t_algo = fig.text(0.03, 0.026, "", fontsize=6.5, color="#222222")
    t_note = fig.text(0.03, 0.010, "", fontsize=6.5, color="#444444")
    written = []
    for lang, out in job["outputs"].items():
        tx = TEXT[lang]
        t_title.set_text(tx["title"])
        t_sub.set_text(job["subtitles"][lang])
        t_algo.set_text(tx["algo"] if job["has_thr"] else tx["no_ar"])
        t_note.set_text(" · ".join(([tx["ar"]] if job["has_thr"] else []) + [tx["isobars"], job["credit"]]))
        buf = io.BytesIO()
        fig.savefig(buf, dpi=dpi, format="png")
        buf.seek(0)
        img = Image.open(buf).convert("RGB").quantize(colors=256, method=Image.Quantize.MEDIANCUT)
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        img.save(out, optimize=True)
        written.append(out)
    plt.close(fig)
    Path(job["npz"]).unlink()
    return written


def make_gif(frames: list[str], out: str, width: int = 640, ms: int = 450) -> None:
    """Animation GIF à partir des PNG (réduits à `width` pixels de large)."""
    from PIL import Image

    imgs = []
    for f in frames:
        im = Image.open(f).convert("RGB")
        h = round(im.height * width / im.width)
        imgs.append(im.resize((width, h), Image.LANCZOS).quantize(colors=256, method=Image.Quantize.MEDIANCUT))
    durations = [ms] * len(imgs)
    durations[-1] = ms * 4                     # pause sur la dernière image
    imgs[0].save(out, save_all=True, append_images=imgs[1:], duration=durations, loop=0, optimize=True)
