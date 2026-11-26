# Alerte AR Antarctique

Ce système surveille un ou plusieurs sites en Antarctique et envoie un email quand
la prévision d'ensemble ECMWF annonce une rivière atmosphérique (AR) dans les
prochains jours.

## Fonctionnement

1. **Seuils** (une seule fois, `build_climatology.py`). Le script télécharge le
   vIVT d'ERA5 (`vertical_integral_of_northward_water_vapour_flux`, 6-horaire) et
   calcule pour chaque mois et chaque point le 98e percentile du transport
   poléward. C'est le seuil de Wille et al. (2021).
2. **Prévision** (à chaque run, `run_forecast.py`). Pour chaque échéance et chacun
   des 50 membres ECMWF ENS (open data, 0.25°) :
   - téléchargement de `q`, `v` sur 8 niveaux et de `sp` ;
   - calcul du vIVT au-dessus du sol, puis du transport poléward ;
   - détection de Wille : pixels au-dessus du seuil entre 37.5°S et 85°S,
     regroupés en objets contigus ; un objet est retenu si son extension
     méridienne atteint au moins 20°.
3. **Alerte**. P(AR) au site = fraction des membres où un pixel AR tombe dans le
   rayon du site. Un email part si P(AR) ≥ `probability_threshold` à au moins une
   échéance. Pour la même situation, un nouvel email ne part que si la
   probabilité maximale augmente de `update_if_prob_increase`.

Chaque run produit aussi une carte de probabilité AR,
`data/forecast/ar_prob_AAAAMMJJHH.nc`.

## Installation

```bash
conda env create -f environment.yml
```

### 1. Seuils ERA5 (une seule fois)

1. Crée un compte sur https://cds.climate.copernicus.eu.
2. Accepte la licence ERA5 sur la page du jeu de données.
3. Mets ta clé API dans `~/.cdsapirc` (voir https://cds.climate.copernicus.eu/how-to-api).
4. Lance le calcul :

```bash
conda run -n ar-alert python build_climatology.py
```

Il y a une requête CDS par année (30 au total). Selon la file d'attente du CDS, ça
prend de quelques heures à une journée. Le script reprend là où il s'est arrêté.
Une fois `data/thresholds_vivt.nc` créé, tu peux supprimer `data/era5/` (~6 Go).

### 2. Email

Remplis la section `email:` de `config.yaml`. Le mot de passe SMTP n'est jamais
écrit dans ce fichier : il est lu dans la variable `AR_SMTP_PASSWORD`, sinon dans
le trousseau macOS. Pour l'enregistrer dans le trousseau, lance cette commande
dans ton terminal (elle demande le mot de passe) :

```bash
security add-generic-password -s ar-alert-smtp -a TON_LOGIN_SMTP -w
```

Pour tester l'envoi :

```bash
conda run -n ar-alert python run_forecast.py --test-email
```

### 3. Sites et paramètres d'alerte

Les sites se règlent dans `config.yaml`, section `sites:` (nom, lat, lon, rayon en
km). Les paramètres d'alerte sont dans la section `alert:`.

Pour un essai sans envoi d'email :

```bash
conda run -n ar-alert python run_forecast.py --dry-run
```

### 4. Lancement automatique (launchd)

```bash
./install_launchd.sh "$(conda run -n ar-alert which python)"
```

La tâche tourne à 10h30 et 22h30 (heure du Mac), après la publication des runs
00 et 12 UTC. Un run déjà traité est ignoré. Le journal est dans
`data/logs/ar_alert.log`. Pour désinstaller : `./install_launchd.sh --uninstall`.

## Volume de données et durée

Le vIVT demande 17 champs globaux par membre et par échéance, soit environ 8 Mo.
Avec 50 membres, 6 h de pas et 120 h d'horizon, ça fait environ **9 Go par run**.
Pour réduire :

- `step_interval_h: 12` divise le volume par deux ;
- `max_step_h` plus court ;
- moins de niveaux dans `levels` (ex. `[1000, 925, 850, 700, 500, 300]`) ;
- `detection.variable: iwv` (méthode IWV de Wille et al. 2019, colonne d'eau
  totale) : ~0.4 Mo par membre et par échéance, soit environ 20 fois moins. Il
  faut alors recalculer les seuils avec `variable: iwv` et
  `output: data/thresholds_iwv.nc`.

## Limites connues

- **Biais entre seuils et prévision.** Les seuils viennent du vIVT ERA5 (colonne
  complète, niveaux modèle). En prévision, le vIVT est intégré sur 8 niveaux de
  pression jusqu'à 300 hPa, ce qui donne une légère sous-estimation (quelques %),
  donc un algorithme un peu conservateur. Les biais propres au modèle IFS
  s'ajoutent.
- **Détection réimplémentée.** La détection reprend le critère de Wille (≥ 20° de
  latitude) avec un étiquetage en composantes connexes, et non les découpages
  successifs du script original (`ar_alg_v2.4_vIVT_ant.py`). Les résultats peuvent
  différer légèrement.
- **Domaine limité à 85°S.** Comme chez Wille, la détection s'arrête à 85°S, et
  un site très à l'intérieur ne voit que les AR qui s'étendent jusqu'à lui.
- **Pas de membre de contrôle.** Il n'est pas publié en open data ; seuls les 50
  membres perturbés sont utilisés.

## Références

- Wille et al. (2019), *Nat. Geosci.*, doi:10.1038/s41561-019-0460-1
- Wille et al. (2021), *J. Geophys. Res. Atmos.*, doi:10.1029/2020JD033788
- Code original : https://github.com/jwille45/Antarctic-lab (Zenodo 10.5281/zenodo.7990215)

---

# Site web : situation synoptique en temps réel

`synoptic_maps.py` produit, pour le dernier run déterministe ECMWF HRES 00/12 UTC
(0 à 120 h, toutes les 6 h), des cartes polaires sud. Chaque carte montre :

- l'IVT en couleur, avec des flèches là où IVT ≥ 250 ;
- les isobares tous les 4 hPa ;
- les contours des AR détectées ;
- les sites configurés.

La page `site/` (HTML/JS statique) affiche ces cartes avec un curseur, une
lecture animée et une frise « AR à ce site » pour chaque site.

Un run complet télécharge environ 300 Mo et prend moins d'une minute.

```bash
conda run -n ar-alert python synoptic_maps.py              # génère site/maps + site/data/manifest.json
python3 -m http.server 8765 --directory site               # aperçu local : http://localhost:8765
```

## Publication sur GitHub Pages

Le workflow `.github/workflows/update-site.yml` régénère les cartes toutes les 6 h
sur les serveurs GitHub (réseau rapide) et publie `site/` sur GitHub Pages. Rien
n'est commité à chaque run.

1. Crée un dépôt **public** sur github.com (Pages et Actions sont gratuits pour un dépôt public).
2. Dans *Settings → Pages*, choisis **Source : GitHub Actions**.
3. Pousse ce dossier :

   ```bash
   git init -b main
   git add .
   git commit -m "Site AR Antarctique"
   git remote add origin https://github.com/TON_COMPTE/TON_DEPOT.git
   git push -u origin main
   ```

4. Dans *Actions → Cartes synoptiques*, clique sur **Run workflow** pour la
   première publication. Le site est ensuite à `https://TON_COMPTE.github.io/TON_DEPOT/`.

**Seuils.** Les contours AR n'apparaissent qu'une fois `data/thresholds_vivt.nc`
calculé (`build_climatology.py`) et commité. C'est le seul fichier de `data/`
suivi par git (~3 Mo).

**À savoir.** GitHub désactive les workflows planifiés d'un dépôt public après
60 jours sans activité sur le dépôt. Un commit ou un clic sur « Enable workflow »
les réactive.

## Langues, sites et événements passés

- Chaque carte est produite en français et en anglais (`site/maps/fr`, `site/maps/en`).
  La page propose un sélecteur FR/EN (lien direct : `?lang=en`) et un bouton pour
  télécharger l'image affichée.
- Les sites (Dumont d'Urville, Concordia, Neumayer III) se règlent dans `config.yaml`, section `sites:`.
- L'onglet « Événements passés » montre des animations ERA5 définies dans la section
  `events:` de `config.yaml` : décembre 2018 (Concordia, Dutrievoz et al. 2026) et
  mars 2022 (vague de chaleur en Antarctique de l'Est). Une fois les seuils calculés,
  elles se génèrent avec `python events.py`, puis `site/events/` est commité.
