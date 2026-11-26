"""Rendu des cartes polaires sud : un fond (IVT, MSLP, sites, textes) et un calque transparent
par algorithme de détection (contour AR + référence de l'algorithme).

Fond et calques ont exactement la même taille et la même géométrie : le site les superpose
et compose l'image téléchargée. Une carte est dessinée une seule fois ; seuls les textes
changent entre les langues. Les PNG sont réduits à 256 couleurs.
"""
from __future__ import annotations

import datetime as dt
import io
import warnings
from pathlib import Path

import numpy as np

from algos import ALGOS, legend_line

LANGS = ("fr", "en")
TEXT = {
    "fr": dict(title="IVT, pression au niveau de la mer et rivières atmosphériques",
               isobars="Isobares 4 hPa, masquées si p$_s$ < 800 hPa"),
    "en": dict(title="IVT, mean sea-level pressure and atmospheric rivers",
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


def _save(fig, dpi, out, transparent=False):
    from PIL import Image

    buf = io.BytesIO()
    fig.savefig(buf, dpi=dpi, format="png", transparent=transparent)
    buf.seek(0)
    img = Image.open(buf)
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    if transparent:
        img.convert("RGBA").quantize(colors=64, method=Image.Quantize.FASTOCTREE).save(out, optimize=True)
    else:
        img.convert("RGB").quantize(colors=256, method=Image.Quantize.MEDIANCUT).save(out, optimize=True)


def render(job: dict) -> list[str]:
    """Dessine le fond et les calques d'une carte, dans chaque langue.

    job : npz (lat, lon, uivt, vivt, msl [hPa], sp [Pa] ; masques AR <algo> et <algo>_lat/<algo>_lon),
          base {lang: png}, layers {algo: {lang: png}}, subtitles {lang: texte}, credit, sites,
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
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    from cartopy.util import add_cyclic_point

    d = np.load(job["npz"])
    lat, lon = d["lat"], d["lon"]
    ivt = np.hypot(d["uivt"], d["vivt"])
    dpi = int(job.get("dpi", 150))

    fig = plt.figure(figsize=(8, 8.6), dpi=dpi)
    ax = fig.add_axes([0.02, 0.15, 0.96, 0.79], projection=ccrs.SouthPolarStereo())
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
    # et hors du cadre : sinon les étiquettes des isobares débordent du cercle
    msl = np.where((d["sp"] < 80000.0) | (lat[:, None] > job["lat_north"]), np.nan, d["msl"])
    msl_c, _ = add_cyclic_point(msl, coord=lon)
    cs = ax.contour(X, Y, msl_c, levels=np.arange(920, 1060, 4), colors="#1f1f1f",
                    linewidths=0.6, transform=pc)
    ax.clabel(cs, cs.levels[::2], fontsize=6, fmt="%d", inline_spacing=2)

    # vecteurs IVT là où le transport est significatif
    step = int(job.get("quiver_every", 8))
    sl = (slice(None, None, step), slice(None, None, step))
    show = (ivt[sl] >= 250) & (lat[sl[0]][:, None] <= job["lat_north"])
    if show.any():
        lon2, lat2 = np.meshgrid(lon[sl[1]], lat[sl[0]])
        ax.quiver(lon2[show], lat2[show], d["uivt"][sl][show], d["vivt"][sl][show], transform=pc,
                  scale=12000, width=0.0018, color="#202020", alpha=0.75)

    halo = [patheffects.withStroke(linewidth=3, foreground="white")]
    for s in job["sites"]:
        ax.plot(s["lon"], s["lat"], marker="o", ms=6.5, mfc="white", mec="#0f1e2e", mew=1.6,
                transform=pc, zorder=10)
        ax.text(s["lon"], s["lat"], "  " + s["name"], fontsize=9, fontweight="bold", transform=pc,
                ha="left", va="center", color="#0f1e2e", path_effects=halo, zorder=11)

    gl = ax.gridlines(pc, linewidth=0.3, color="#888888", alpha=0.6, linestyle="--")
    gl.ylocator = matplotlib.ticker.FixedLocator([-80, -70, -60, -50, -40, -30])

    cax = fig.add_axes([0.15, 0.104, 0.7, 0.016])
    cb = fig.colorbar(cf, cax=cax, orientation="horizontal", ticks=levels)
    cb.set_label("IVT (kg m$^{-1}$ s$^{-1}$)", fontsize=8)
    cb.ax.tick_params(labelsize=7)

    t_title = fig.text(0.03, 0.965, "", fontsize=10.5, weight="bold")
    t_sub = fig.text(0.03, 0.945, "", fontsize=8.5, color="#333333")
    t_note = fig.text(0.03, 0.010, "", fontsize=6.5, color="#444444")
    written = []
    for lang, out in job["base"].items():
        t_title.set_text(TEXT[lang]["title"])
        t_sub.set_text(job["subtitles"][lang])
        t_note.set_text(" · ".join([TEXT[lang]["isobars"], job["credit"]]))
        _save(fig, dpi, out)
        written.append(out)

    # ---- calques : on masque tout le fond, on garde la géométrie des axes
    for a in list(ax.get_children()) + [cax, t_title, t_sub, t_note]:
        if a is not ax.patch:
            a.set_visible(False)
    for sp in ax.spines.values():
        sp.set_visible(False)
    gl.xlines = gl.ylines = False
    ax.patch.set_visible(False)
    fig.patch.set_alpha(0)

    def contour(mask, mlat, mlon, color):
        """Contour fermé : le masque est bordé de zéros pour se refermer aux bords du domaine."""
        m = mask.astype(float)
        dl = mlat[1] - mlat[0]
        m = np.vstack([np.zeros((1, m.shape[1])), m, np.zeros((1, m.shape[1]))])
        ml = np.concatenate([[mlat[0] - dl], mlat, [mlat[-1] + dl]])
        mc, lc = add_cyclic_point(m, coord=mlon)
        XM, YM = np.meshgrid(lc, ml)
        c = ax.contour(XM, YM, mc, levels=[0.5], colors=color, linewidths=2.4, transform=pc, zorder=9)
        c.set(path_effects=[patheffects.withStroke(linewidth=4.8, foreground="#0f1e2e")])
        return c

    for algo, outs in job["layers"].items():
        a = ALGOS[algo]
        drawn = []
        if algo in d.files and d[algo].any():
            drawn.append(contour(d[algo], d[f"{algo}_lat"], d[f"{algo}_lon"], a["color"]))
        if a["ring85"]:
            ring = np.linspace(0, 360, 361)
            drawn += ax.plot(ring, np.full_like(ring, -85.0), transform=pc, color="#3a3a3a", lw=0.9,
                             ls=(0, (4, 3)), zorder=7)
        t_ref = fig.text(0.03, 0.042, "", fontsize=6.5, color="#222222")
        t_leg = fig.text(0.03, 0.026, "", fontsize=6.5, color="#444444")
        drawn += [t_ref, t_leg]
        for lang, out in outs.items():
            t_ref.set_text(a["ref"][lang])
            t_leg.set_text(legend_line(algo, lang))
            _save(fig, dpi, out, transparent=True)
            written.append(out)
        for art in drawn:
            art.remove()

    plt.close(fig)
    Path(job["npz"]).unlink()
    return written


def make_gif(frames: list[tuple[str, str | None]], out: str, width: int = 640, ms: int = 450,
             colors: int = 128) -> None:
    """Animation GIF à partir de couples (fond, calque) superposés, réduits à `width` pixels.

    Une palette commune, tirée de six images réparties sur l'animation, et sans tramage : les
    zones identiques d'une image à l'autre le restent, ce qui divise la taille par deux environ.
    """
    from PIL import Image

    rgb = []
    for base, layer in frames:
        im = Image.open(base).convert("RGBA")
        if layer:
            im = Image.alpha_composite(im, Image.open(layer).convert("RGBA"))
        im = im.convert("RGB")
        h = round(im.height * width / im.width)
        rgb.append(im.resize((width, h), Image.LANCZOS))
    pick = sorted({round(i * (len(rgb) - 1) / 5) for i in range(6)})
    W, H = rgb[0].size
    mosaic = Image.new("RGB", (W * len(pick), H))
    for k, i in enumerate(pick):
        mosaic.paste(rgb[i], (k * W, 0))
    pal = mosaic.quantize(colors=colors, method=Image.Quantize.MEDIANCUT)
    imgs = [im.quantize(palette=pal, dither=Image.Dither.NONE) for im in rgb]
    durations = [ms] * len(imgs)
    durations[-1] = ms * 4                     # pause sur la dernière image
    imgs[0].save(out, save_all=True, append_images=imgs[1:], duration=durations, loop=0, optimize=True)
