# Catalogue des options de retouche

Ce fichier est le catalogue **vivant** de toutes les techniques de retouche
connues, documentées au fil des recherches web. Il est plus large que
`presets/styles.json` (qui ne contient que les presets **actifs**, codés et
utilisables tels quels par `scripts/retouch.py`) : une technique peut être
documentée ici sans être encore implémentée.

**Alimentation** : la skill `insta-post` relance une recherche web tous les
`research_interval` photos traitées (`data/state.json`, 10 par défaut) pour
trouver d'autres méthodes que celles déjà cataloguées, et les ajoute ici. Ne
jamais écraser une entrée existante — seulement compléter. Une entrée qui
n'a jamais été promue en preset actif après plusieurs cycles n'est pas un
échec : certaines techniques restent pertinentes en réserve (cas d'usage
spécifique) sans être un défaut par défaut.

Format par entrée : nom, mécanisme technique, quand l'utiliser, statut
(implémentée dans un preset / documentée seulement), source.

---

## Recherche du 2026-09-05 (initiale)

Source complète : `docs/research/photo-retouching-methods.md`.

### Recadrage / composition

- **Crop 4:5 (1080×1350) centré sur le sujet** — le format qui occupe le plus
  de surface dans le feed. *Implémentée* (tous les presets actifs).
- **Règle des tiers** — visage/yeux sur la ligne des tiers supérieure plutôt
  qu'au centre géométrique. *Implémentée* (focus par défaut ~0.38 en y).
- **Fill the frame** — resserrer pour que le sujet occupe 60-80% du cadre au
  lieu de 30-40%, supprime mécaniquement le bruit périphérique. *Implémentée*
  via le focus + ratio serré.
- **Exclure entièrement les éléments parasites de bord plutôt que les couper
  à mi-hauteur** (rétroviseur, ceinture, montant de portière...) — un objet
  tranché en bord de cadre attire plus l'œil qu'un objet absent. *Documentée
  seulement* — pas encore de détection automatique des bords à risque
  (piste : Sobel/Canny sur une bande de ~5% en bord de crop-box).

### Couleur

- **Courbe tonale en S** (LUT 256 valeurs, point milieu ancré) au lieu d'un
  contraste global. *Implémentée* (tous les presets, `curve_points`).
- **Split-toning teal ombres / ambre hautes lumières** via masques de
  luminance. *Implémentée* (`split_tone` dans chaque preset — dosage
  différent par style).
- **Balance des blancs gray-world atténuée** (40-60% de mélange, pas 100%
  sur une scène non neutre). *Implémentée* (`white_balance_strength`).
- **LUT 3D (type Kodak Portra, cinéma)** pour reproduire un look figé de
  façon cohérente. *Documentée seulement* — utile pour reproduire un style
  existant plutôt que pour en construire un depuis zéro ; candidate si
  Bastien identifie un look précis à copier (ex: capture d'écran d'un post
  qu'il aime). Lib envisageable : `pillow-lut`.

### Netteté / texture

- **Unsharp mask maison à deux passes** (contours fins radius~1.5 + clarté
  grand rayon radius~50) au lieu d'un filtre de netteté générique.
  *Implémentée* (`sharpen` + `clarity` dans chaque preset).
- **Dodge & burn ciblé sujet/fond** (assombrir le fond au-delà d'un rayon
  autour du point focal, éclaircir légèrement le sujet) — variante
  asymétrique de la vignette, adaptée au contenu réel plutôt qu'à la seule
  géométrie. *Documentée seulement* — plus complexe qu'une vignette radiale,
  candidate si le retour de Bastien est "la vignette actuelle ne va pas
  assez chercher le sujet".

### Correction optique

- **Correction de distorsion grand-angle** (barrel distortion + perspective
  proche sur un selfie) — réduit la déformation des bras/visage en bord de
  cadre. *Documentée seulement* — nécessite soit les coefficients de
  calibration de l'objectif (rarement disponibles), soit une correction
  radiale approximative (`k1` négatif) à calibrer à l'œil ; à tester sur un
  prochain selfie grand-angle avant de l'ajouter à un preset.

### Export

- **1080px de large, Lanczos, JPEG quality 92, subsampling=0** —
  contrôler le downscale soi-même plutôt que de laisser Instagram le faire.
  *Implémentée* (tous les presets, fin de `scripts/retouch.py`).

---

<!-- Nouvelles entrées ajoutées ici par les recherches périodiques, une section "## Recherche du AAAA-MM-JJ" par cycle, jamais en écrasant les précédentes. -->
