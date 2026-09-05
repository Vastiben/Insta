# Retouche photo "Insta" — recherche technique pour aller au-delà de contraste/saturation/netteté/vignette

Contexte : `retouch.py` actuel (Pillow) applique `ImageEnhance.Contrast(1.18)`, `Color(1.15)`, `Brightness(1.03)`, `Sharpness(1.3)` + une vignette radiale mélangée à 35%. Verdict de Bastien : "ça ne rend pas la photo plus Insta". Photo test : selfie grand-angle dans une Porsche, lui au volant, bras tatoué, habitacle chargé (rétroviseur, tableau de bord, ceinture) autour du sujet.

**Diagnostic de départ** : ces 4 réglages Pillow sont tous des opérations *globales, uniformes sur toute l'image*. Une photo "Insta" qui a l'air pro se distingue par (a) un cadrage qui isole le sujet du bruit visuel, (b) un traitement de la couleur *différencié par zone tonale* (pas une seule valeur appliquée à tous les pixels), et (c) des opérations locales (masque de netteté à rayon large, dodge & burn) plutôt que globales. Les 4 sections ci-dessous couvrent ça dans l'ordre demandé, plus une section 5 sur les techniques additionnelles directement pertinentes pour *cette* photo précise.

---

## 1. Recadrage / composition

### Ratios recommandés par Meta aujourd'hui

Note d'accès : les domaines officiels `developers.facebook.com`, `www.facebook.com/business/*` et `help.instagram.com` sont bloqués par le proxy réseau de cet environnement (egress filtré) — impossible de les fetcher directement. Les chiffres ci-dessous viennent d'agrégateurs spécialisés (Buffer, Sprout Social, Hootsuite, Later — sources techniques régulièrement mises à jour et qui citent elles-mêmes le Meta Business Help Center et le guide publicitaire Meta) recoupés entre eux ; ils convergent tous vers les mêmes valeurs, ce qui est un bon signe de fiabilité malgré l'absence de fetch direct.

- **Plage acceptée en upload** : de **1.91:1** (paysage) à **4:5** (portrait), 1:1 (carré) au milieu. C'est la plage que Meta a affichée dans ses specs ads officielles ("All feed photo dimensions are now supported, ranging from 1.91:1 to 4:5.") — source : page officielle Meta Business Help *Awareness Image Ad Specs on Instagram Feed*, https://www.facebook.com/business/ads-guide/update/image/instagram-feed (non fetchable ici, contenu repris et confirmé par plusieurs agrégateurs, ex. https://buffer.com/resources/instagram-image-size/ et https://blog.hootsuite.com/social-media-image-sizes-guide/).
- **Format qui occupe le plus d'espace à l'écran et qu'on recommande par défaut en 2026** : **4:5 portrait**, soit **1080 × 1350 px**. C'est le format qui maximise la surface occupée dans le feed mobile (l'appli recadre/compresse tout le reste vers ses propres bornes d'affichage). Sources concordantes : https://buffer.com/resources/instagram-image-size/, https://influencermarketinghub.com/instagram-image-sizes/.
- **Carré 1:1** : 1080 × 1080 px — toujours supporté, mais occupe moins de surface verticale à l'écran qu'un 4:5, donc moins de "poids" dans le scroll.
- **Stories / Reels** : 9:16, 1080 × 1920 px (plein écran vertical).
- Éviter les formats intermédiaires que l'app doit recadrer automatiquement (ex. 3:2 issu direct d'un appareil photo) — laisser Instagram deviner le recadrage donne un résultat aléatoire ; toujours recadrer soi-même avant export.

**Implémentation Pillow** : ne jamais exporter au ratio natif du capteur (souvent 4:3 ou 3:2, encore pire en grand-angle où le ratio est large). Calculer le crop-box cible en connaissant `w, h = img.size`, choisir le ratio cible (4:5 recommandé), puis :

```python
def crop_to_ratio(img, target_ratio=4/5, focus=(0.5, 0.42)):
    """focus = position relative (x, y) du point d'intérêt (ex: visage) dans l'image source,
    utilisée pour ne pas couper le sujet quand on resserre le cadre."""
    w, h = img.size
    src_ratio = w / h
    if src_ratio > target_ratio:  # image trop large -> couper en largeur
        new_w = int(h * target_ratio)
        cx = int(w * focus[0])
        left = max(0, min(w - new_w, cx - new_w // 2))
        box = (left, 0, left + new_w, h)
    else:  # image trop haute -> couper en hauteur
        new_h = int(w / target_ratio)
        cy = int(h * focus[1])
        top = max(0, min(h - new_h, cy - new_h // 2))
        box = (0, top, w, top + new_h)
    return img.crop(box)
```

### Règles de composition, appliquées à une photo d'habitacle chargée

- **Règle des tiers** : placer les yeux/le visage sur la ligne des tiers supérieure, pas au centre. Une grille 3×3 ; les points d'intersection sont les zones de plus forte "tension visuelle". Référence technique : https://digital-photography-school.com/rule-of-thirds/ et https://www.adobe.com/creativecloud/photography/technique/rule-of-thirds.html.
- **Fill the frame ("remplir le cadre")** : le principe directement applicable ici — un plan large d'habitacle dilue le sujet dans un fouillis d'éléments (rétro, ceinture, tableau de bord). Resserrer le crop pour que le visage + une portion du volant + le bras tatoué occupent 60-80% du cadre au lieu de 30-40% supprime mécaniquement la plupart du bruit périphérique sans retouche de contenu. Source : https://artisticomposition.com/compositions/fill-the-frame.
- **Éliminer les éléments parasites en bord de cadre** : un rétroviseur ou une ceinture coupés à moitié en bord d'image attirent l'œil (contraste de bord + ligne franche = signal visuel fort) plus qu'un même élément soit totalement inclus, soit totalement exclu. Règle actionnable pour le crop automatique : préférer un ratio de crop qui *exclut entièrement* les objets d'habitacle en haut/bas plutôt qu'un ratio qui les coupe à mi-hauteur. Source : https://digital-photography-school.com/rule-of-thirds/ (section sur les distractions de bord), recoupé par https://proedu.com/blogs/photography-fundamentals/what-is-the-rule-of-thirds-in-photography-a-guide-to-perfect-composition.
- **Cas spécifique grand-angle + selfie** : un objectif large-angle proche du visage introduit une distorsion de perspective (nez/bras proches de la caméra artificiellement agrandis) en plus de la distorsion optique en barrel sur les bords. Recadrer serré vers le centre optique réduit à la fois le fouillis *et* la distorsion la plus visible (les bords, où la distorsion barrel est maximale, sont ceux qu'on coupe). Voir section 5 pour la correction algorithmique.

---

## 2. Color grading au-delà du contraste global

### Le problème technique avec `ImageEnhance.Contrast`

`ImageEnhance.Contrast` de Pillow interpole simplement chaque pixel vers/depuis la luminance moyenne de l'image entière (`enhance(factor)` = `mean + (pixel - mean) * factor`, appliqué identiquement aux trois canaux). C'est une opération **linéaire, globale, canal-par-canal identique** : elle ne distingue pas les ombres des hautes lumières et ne peut pas créer de séparation colorée entre zones tonales. Résultat : l'image "punche" un peu plus, mais garde exactement le même équilibre colorimétrique — d'où le verdict "pas plus Insta". Confirmation technique : "The Contrast slider in the Basic panel is a blunt instrument that applies a fixed, global adjustment" — https://www.lightroomqueen.com/community/threads/using-basic-tone-vs-tone-curve-to-adjust-photos (repris sur community.adobe.com), recoupé par la doc conceptuelle Lightroom sur les tone curves : https://toddmarsh.com/lightroom-tone-curve-guide/ et https://frameandfocal.com/photography-tips/4-steps-improve-photos-use-tone-curves.

### Courbe tonale (tone curve) — le vrai mécanisme

Une courbe tonale mappe **chaque valeur d'entrée 0-255 vers une valeur de sortie**, via une fonction non-linéaire définie par des points de contrôle (souvent une spline). L'exemple classique, la **courbe en S** : point ancré au milieu (ne bouge pas — préserve l'exposition globale), point remonté dans les hautes lumières (¾ vers le haut-droit), point abaissé dans les ombres (¼ vers le bas-gauche). Ça crée du contraste *perçu* sans toucher la luminosité moyenne, contrairement à `ImageEnhance.Contrast` qui, lui, décale mécaniquement tout autour de la moyenne globale sans notion de "point d'ancrage" par zone. Source : https://toddmarsh.com/lightroom-tone-curve-guide/ (section S-curve), recoupée par https://scientiaserida.substack.com/p/tone-curve.

Différence clé avec les sliders Highlights/Shadows classiques : ceux-ci appliquent un **masque de luminance** (l'effet s'atténue progressivement vers l'autre extrémité du spectre tonal), alors qu'une courbe pure n'a pas de masque et crée des compromis entre zones adjacentes si on n'espace pas suffisamment les points de contrôle. Source : forum Lightroom Queen, cité plus haut.

**Implémentation Pillow/numpy** — construire une LUT (lookup table) de 256 valeurs par interpolation entre points de contrôle, puis l'appliquer par canal :

```python
import numpy as np
from PIL import Image

def build_curve_lut(points):
    """points: liste de (x_in, y_out) triée, x et y dans [0,255].
    Ex courbe en S douce : [(0,0), (64,50), (128,128), (192,205), (255,255)]"""
    xs, ys = zip(*points)
    x_full = np.arange(256)
    lut = np.interp(x_full, xs, ys)  # interpolation linéaire par morceaux
    return np.clip(lut, 0, 255).astype(np.uint8)

def apply_curve(img, lut, channels=(0, 1, 2)):
    arr = np.array(img)
    for c in channels:
        arr[..., c] = lut[arr[..., c]]
    return Image.fromarray(arr)
```

Pour une vraie courbe lisse (pas linéaire par segments), remplacer `np.interp` par une interpolation spline cubique : `scipy.interpolate.CubicSpline(xs, ys)(x_full)`. Pour rester sans dépendance scipy, un polynôme de degré 2-3 ajusté aux points (`np.polyfit`) fonctionne aussi bien pour une courbe en S à 3-5 points.

**Highlights/midtones/shadows séparément (avec masque de luminance)**, l'approche pro plutôt que la courbe brute : calculer une carte de luminance, en dériver 3 masques (ombres/tons moyens/hautes lumières) qui se chevauchent en douceur, et appliquer un ajustement différent à chaque zone :

```python
def luminance_masks(arr):
    # arr: float array HxWx3 dans [0,255]
    lum = (0.299*arr[...,0] + 0.587*arr[...,1] + 0.114*arr[...,2]) / 255.0
    shadow_mask    = np.clip(1.0 - lum / 0.5, 0, 1)          # fort à L=0, nul à L=0.5+
    highlight_mask = np.clip((lum - 0.5) / 0.5, 0, 1)         # nul à L=0.5-, fort à L=1
    midtone_mask   = 1.0 - shadow_mask - highlight_mask
    return shadow_mask, midtone_mask, highlight_mask
```

### Balance des blancs

L'algorithme technique le plus simple et robuste sans détection de visage : **gray world** — hypothèse que la moyenne de tous les pixels d'une scène "normale" devrait être neutre (gris). On recale chaque canal RGB pour que sa moyenne rejoigne une valeur cible commune.

- Mécanisme : `output_channel = input_channel * (target / mean(channel))`, avec `target` = la luminance moyenne globale (ou 128 en implémentation fixe). Source : https://mattmaulion.medium.com/white-balancing-an-enhancement-technique-in-image-processing-8dd773c69f6, recoupé par la doc OpenCV `cv::xphoto::GrayworldWB` (https://docs.opencv.org/3.4/d7/d71/classcv_1_1xphoto_1_1GrayworldWB.html) et par un tutoriel PIL/numpy dédié : https://codeandlife.com/2019/08/17/correcting-image-white-balance-with-python-pil-and-numpy/.
- **Attention pour cette photo précise** : un habitacle de voiture (cuir/plastique souvent brun-noir-gris + peau + tatouage bleu/noir) n'est *pas* une scène "gray world" idéale — gray-world pur pourrait sur-corriger. Pratique recommandée : utiliser gray-world comme point de départ mais limiter la correction (mélanger 100% gray-world avec l'image d'origine à ~40-60%) plutôt que l'appliquer brute.

```python
def gray_world_wb(arr, strength=0.5):
    arr = arr.astype(np.float64)
    means = arr.reshape(-1, 3).mean(axis=0)
    target = means.mean()
    scale = target / np.clip(means, 1, None)
    corrected = arr * scale
    out = arr * (1 - strength) + corrected * strength
    return np.clip(out, 0, 255).astype(np.uint8)
```
(OpenCV propose aussi directement `cv2.xphoto.createGrayworldWB()` si le module `opencv-contrib-python` est installé — évite de réinventer le seuillage sur la saturation que fait l'implémentation native.)

### Split-toning / color grading (teals & oranges)

Mécanisme : teinter les ombres vers une teinte (typiquement cyan/teal, complémentaire de la peau) et les hautes lumières vers une autre (orange/ambre, dans la gamme des tons chair), en laissant les tons moyens quasi neutres. Ça fonctionne parce que la peau humaine est presque toujours dans la plage orange-jaune, et que teinter le *reste* de l'image (fond, ombres) vers le complémentaire (bleu-vert) crée une séparation chromatique sujet/fond — exactement utile ici pour détacher le visage/bras du fouillis gris-noir de l'habitacle. Source technique : https://beverlyboy.com/filmmaking/what-is-teal-orange-look/ et https://exposure.software/tutorial/complementary-color-grading/, sur le mécanisme visuel ; explication du "pourquoi ça marche avec la peau" : https://www.diyphotography.net/cinematic-color-grading-skin-tone/.

Mécanisme RGB par canal (comment un logiciel de grading fait ça en interne) : "In RGB mode, the Red, Green and Blue channels each have their own curve. Lifting the Blue channel curve in the shadows adds blue to dark areas. Pulling it down in the highlights adds yellow (the complement of blue) to bright areas." — https://amateurphotographer.com/technique/photo_editing/how-to-do-colour-grading/.

**Implémentation Pillow/numpy** — en réutilisant les masques de luminance de la section précédente, ajouter une teinte constante pondérée par masque plutôt que de bouger une courbe canal par canal :

```python
def split_tone(arr, shadow_rgb=(0, 15, 25), highlight_rgb=(25, 12, -8), shadow_mask=None, highlight_mask=None):
    """shadow_rgb / highlight_rgb : offsets additifs (peuvent être négatifs) par canal, à faible amplitude (-30..30).
    Ex: shadow_rgb teal (peu de rouge, un peu de vert, un peu plus de bleu),
        highlight_rgb ambre (plus de rouge, un peu de vert, moins de bleu)."""
    arr = arr.astype(np.float64)
    for c, (so, ho) in enumerate(zip(shadow_rgb, highlight_rgb)):
        arr[..., c] += shadow_mask * so + highlight_mask * ho
    return np.clip(arr, 0, 255).astype(np.uint8)
```

### LUT (lookup table) — remapping plus arbitraire qu'une courbe

Une LUT 3D (souvent 17³ ou 33³ points dans l'espace RGB) permet un remapping couleur *non-séparable par canal* — utile pour reproduire un look figé (type "Kodak Portra", "teal-orange cinéma") de façon cohérente. Mécanisme : "LUTs take Input Values ... then apply a transformation ... resulting in Output Values" — https://www.shutterevolve.com/color-grading-and-luts-explained/, et sur l'implémentation Python : https://jackchou00.com/en/posts/apply-lut-in-python/ (benchmark trilinéaire/tétraédrique numpy vs scipy vs PIL). Pour du code, appliquer une LUT `.cube` en Python : `pillow-lut` (`pillow_lut.load_cube_file`) ou une interpolation trilinéaire numpy manuelle si on veut zéro dépendance externe. Moins prioritaire que courbe + split-tone pour un premier passage — une LUT sert surtout à *reproduire un style existant*, pas à en construire un depuis zéro.

---

## 3. Résolution et export

Même remarque d'accès que section 1 : impossible de fetcher `developers.facebook.com` ou `help.instagram.com` directement dans cet environnement (proxy egress bloqué) ; chiffres recoupés entre plusieurs sources spécialisées qui citent le Meta Business Help Center et le guide ads Meta.

- **Largeur recommandée** : exporter à **1080 px** de large (Instagram redimensionne de toute façon à cette largeur en interne pour le feed). Uploader plus grand (ex. 4000px) n'apporte rien de plus — Instagram downscale, avec sa propre ré-compression, donc autant contrôler le downscale soi-même en amont avec un algorithme de qualité (Lanczos) plutôt que de laisser Instagram le faire.
- **Hauteur selon le ratio choisi** : 1080×1350 (4:5), 1080×1080 (1:1), 1080×608 environ pour 1.91:1 (à ne pas confondre avec l'ancien 1080×566 parfois cité, qui correspond à un ratio plus large — utiliser 1.91:1 = 1080/1.91 ≈ 566, donc l'un ou l'autre selon la source, les deux circulent ; dans le doute rester en 4:5 qui est le format recommandé par défaut).
- **Compression Instagram** : Instagram réencode systématiquement en JPEG avec sa propre chaîne de compression après upload, quelle que soit la qualité d'origine (estimation communément citée : équivalent JPEG qualité ~70-75%, contre 90-100% en export natif). Donc : ne pas exporter à une qualité JPEG Pillow trop basse en amont (le double encodage JPEG→JPEG accumule les artefacts de blocs 8×8) ; exporter en `quality=90-95` maximum en interne (le script actuel utilise déjà `quality=95`, c'est cohérent) et laisser Instagram faire son seul et unique passage de recompression.
- **Format de fichier** : JPEG plutôt que PNG à l'upload — PNG est reconverti en JPEG côté Instagram de toute façon, avec un risque de dérive de couleur au moment de la conversion forcée si l'app applique un profil colorimétrique différent. Rester en JPEG contrôlé en amont évite cette conversion invisible.
- **Espace colorimétrique** : convertir/embarquer en sRGB avant export (`img.convert("RGB")` suffit tant que la source n'est pas en Adobe RGB/P3 — sinon utiliser `ImageCms` pour une conversion de profil explicite). Un JPEG en Adobe RGB affiché par un navigateur/app sans gestion de profil (fréquent côté web) paraît désaturé.
- **Ordre des opérations recommandé dans le script** : 1) toutes les opérations de retouche à pleine résolution native du fichier source (plus de marge pour les masques de luminance, le sharpening, le split-tone) → 2) crop au ratio cible → 3) resize final vers 1080px de large en `Image.LANCZOS` → 4) `save(..., quality=92, subsampling=0)` (désactiver le sous-échantillonnage chroma 4:2:0 pour préserver la netteté des contours colorés, surtout utile si un split-tone a été appliqué avant).

Sources générales recoupées (agrégateurs spécialisés, contenu cohérent entre eux et avec les specs ads Meta) : https://buffer.com/resources/instagram-image-size/, https://blog.hootsuite.com/social-media-image-sizes-guide/, https://instasize.com/learn/how-to-avoid-instagram-compression, https://influencermarketinghub.com/instagram-image-sizes/.

---

## 4. Pièges qui trahissent une retouche amateur

### Sur-saturation

**Pourquoi ça se voit techniquement** : `ImageEnhance.Color` (comme le slider "Saturation" générique) multiplie l'écart de chaque pixel à sa version en niveaux de gris, *uniformément sur les 3 canaux et sur toute l'image*. Un canal qui approche déjà 255 (ex. le rouge dans une peau bien exposée) **clippe** — il est écrêté à 255 et perd toute variation/texture dans cette zone, ce qui aplati visuellement la peau ou crée une teinte cartoonesque. Détection technique : un pic serré contre le bord droit de l'histogramme R, G ou B isolément (pas juste la luminance) = clipping de saturation. Source : https://new.clippingfly.com/how-to-avoid-oversaturated-colors-in-professional-edits/ et fil Adobe community cité en recherche (community.adobe.com, discussion "color sat clipping indicator").

**Actionnable en code** : au lieu d'augmenter la saturation globalement, (a) plafonner le facteur à ~1.10-1.15 max sur `ImageEnhance.Color`, (b) vérifier le clipping après coup en HSV — `cv2.cvtColor(arr, cv2.COLOR_RGB2HSV)`, compter le % de pixels avec S proche de 255, et réduire le facteur si ce % dépasse un seuil (ex. 2%) ; (c) préférer une saturation *pondérée par luminance* qui épargne les tons chair déjà saturés (skin tones) — détecter la plage teinte 5-35° (orange/rouge peau) en HSV et y appliquer un facteur de saturation réduit par rapport au reste de l'image.

### Vignette trop appuyée

**Pourquoi ça se voit** : une vignette qui assombrit trop fort ou avec un rayon/mid-point trop serré crée une transition visible (bord net entre zone sombre et zone claire) au lieu d'un dégradé imperceptible — l'œil détecte les *discontinuités de gradient* bien plus facilement qu'un niveau de luminosité absolu. Le script actuel utilise déjà un flou gaussien important (`GaussianBlur(w*0.15)`) donc la transition est correctement adoucie ; le risque reste l'*amplitude* (le blend à 0.35 est raisonnable, ne pas monter au-delà de ~0.4-0.5) et le fait qu'une vignette *circulaire centrée* sur une image déjà recadrée serré tombe souvent sur le sujet lui-même plutôt que sur le fond. Source : https://fstoppers.com/lightroom/how-use-vignettes-improve-your-photos-692134 ("harsh vignette screams amateur, start at 20% opacity").

**Actionnable en code** : centrer l'ellipse de la vignette non pas sur le centre géométrique de l'image mais sur le point focal réel du sujet (le même `focus` que pour le crop en section 1), et réduire l'opacité si le crop est déjà serré (moins de fond à assombrir = moins besoin de vignette forte).

### Sur-netteté (halos autour des contours)

**Pourquoi ça se voit techniquement** : un unsharp mask fonctionne en soustrayant une version floutée de l'image à l'originale (détection de contours = filtre passe-haut), puis en ajoutant ce résultat amplifié à l'image d'origine. À trop fort `amount`/`radius`, ça crée un **overshoot** : une ligne claire ("white line") du côté clair de chaque contour et une ligne sombre ("black line") du côté sombre — les "halos" caractéristiques d'un sharpening excessif. Les 3 paramètres : `radius` (largeur du halo — trop grand = halo visible à l'œil nu au lieu de rester sous le seuil de perception), `amount` (intensité — trop fort = overshoot), `threshold` (en dessous duquel un contraste local n'est pas traité comme un contour — trop bas = amplifie aussi le bruit/le grain de peau). Source : https://www.researchgate.net/publication/231608978 et détail des 3 paramètres cité dans la recherche (DPReview forums, Adobe unsharp masking doc).

`ImageEnhance.Sharpness` de Pillow est une version simplifiée/opaque de ce mécanisme (pas de contrôle séparé radius/threshold) — c'est une des raisons pour lesquelles le rendu peut sembler "générique" : impossible de doser finement où le halo apparaît. Remplacer par un unsharp mask maison en 2 temps :

```python
import cv2
import numpy as np

def unsharp_mask(arr, radius=1.5, amount=0.6, threshold=3):
    arr_f = arr.astype(np.float32)
    blurred = cv2.GaussianBlur(arr_f, (0, 0), radius)
    diff = arr_f - blurred
    mask = np.abs(diff) >= threshold          # ne sharpen que les vrais contours, pas le bruit/grain
    sharpened = arr_f + diff * amount
    out = np.where(mask, sharpened, arr_f)
    return np.clip(out, 0, 255).astype(np.uint8)
```

Réglages de départ raisonnables pour un portrait avec peau visible (contours du visage/tatouage à renforcer, grain de peau à épargner) : `radius=1.2-1.8`, `amount=0.5-0.8`, `threshold=2-4`. Au-delà de `amount≈1.0` sur un portrait, les halos deviennent visibles autour des contours forts (contour du visage contre le fond sombre de l'habitacle, contour du tatouage) — sources techniques citées ci-dessus (radius/amount/threshold DPReview, Adobe unsharp masking).

### Mauvais recadrage

Couvert en détail section 1. Le symptôme technique le plus reconnaissable d'un recadrage amateur : un élément fort (bord de rétroviseur, angle de ceinture, montant de portière) coupé exactement en bord de cadre — l'œil interprète une ligne dure qui s'arrête net au bord comme une erreur de composition, alors que la même ligne totalement absente du cadre ne se remarque pas. Vérification actionnable : après calcul du crop-box, inspecter une bande de ~5% de large sur chaque bord pour un gradient de contraste élevé (Sobel/Canny) qui indiquerait un objet tranché — ajuster le crop de quelques pixels si détecté.

---

## 5. Techniques additionnelles pertinentes pour cette photo précise

Hors du périmètre strict des 4 points demandés, mais directement utile vu le contexte (grand-angle, habitacle chargé) :

- **Correction de distorsion grand-angle** : un objectif large en gros plan sur un visage l'étire radialement depuis le centre optique (barrel distortion + perspective proche). `cv2.undistort()` nécessite les coefficients de calibration de l'objectif (pas toujours disponibles pour un iPhone) ; à défaut, une correction approximative par remapping radial inverse (`cv2.fisheye.undistortImage` ou une fonction de correction radiale simple type `k1` négatif) peut réduire l'effet sans calibration précise. Sources : https://learnopencv.com/understanding-lens-distortion/, https://answers.opencv.org/question/45715/correct-barrel-distortion-without-reference-images/. Impact concret : réduit la déformation du bras tatoué et du visage en bord de cadre, qui est un signe fort de "selfie amateur au grand-angle".
- **Contraste local / clarté (technique "HiRaLoAm")** : un *deuxième* unsharp mask, mais avec un rayon large (30-100px) et une faible intensité (5-20%), au lieu du rayon petit/intensité forte utilisé pour la netteté des contours — ça ajoute du "punch" perçu sur les tons moyens (visage, cuir du volant) sans créer de halos fins. C'est un des ingrédients qui distingue une photo "avec du grain/de la texture" (look pro) d'une photo juste contrastée globalement. Source : https://www.cambridgeincolour.com/tutorials/local-contrast-enhancement.htm (contenu confirmé par https://geraldbakker.nl/psnumbers/sharpen-3.html — "Unsharp Mask 3 - High radius low amount").
- **Dodge & burn ciblé sujet/fond** : plutôt qu'une vignette radiale symétrique, assombrir sélectivement les zones d'habitacle identifiées comme fond (au-delà d'un rayon autour du point focal) et légèrement éclaircir le visage/bras — recrée la même intention qu'une vignette (guider l'œil vers le sujet) mais de façon asymétrique et adaptée au contenu réel de l'image plutôt qu'à sa seule géométrie. Implémentable avec le même `shadow_mask`/`highlight_mask` par luminance de la section 2, combiné à un masque de distance radiale au point focal.

---

## Résumé actionnable — ordre d'implémentation suggéré dans `retouch.py`

1. Crop au ratio 4:5 centré sur le visage (`crop_to_ratio`, section 1) — le changement qui aura le plus d'impact visuel immédiat, avant même de toucher à la couleur.
2. Balance des blancs gray-world atténuée (`gray_world_wb`, strength ~0.4-0.5, section 2).
3. Courbe tonale en S légère (`build_curve_lut` + `apply_curve`, section 2) à la place de/en complément de `ImageEnhance.Contrast`.
4. Split-tone teal ombres / ambre hautes lumières (`split_tone`, section 2) via les masques de luminance.
5. Saturation plafonnée + vérification de clipping HSV (section 4) à la place de `ImageEnhance.Color(1.15)` telle quelle.
6. Unsharp mask maison à deux passes : netteté fine (radius~1.5, amount~0.6) + contraste local large rayon (radius~50, amount~0.1) — remplace `ImageEnhance.Sharpness`.
7. Vignette recentrée sur le point focal réel, opacité réduite si le crop est déjà serré.
8. Export : resize Lanczos vers 1080px de large, `quality=92, subsampling=0`.

## Sources principales citées

- Meta / specs Instagram (via agrégateurs recoupés, domaines Meta directs non fetchables dans cet environnement) : https://buffer.com/resources/instagram-image-size/, https://blog.hootsuite.com/social-media-image-sizes-guide/, https://influencermarketinghub.com/instagram-image-sizes/, https://instasize.com/learn/how-to-avoid-instagram-compression
- Composition : https://digital-photography-school.com/rule-of-thirds/, https://artisticomposition.com/compositions/fill-the-frame, https://www.adobe.com/creativecloud/photography/technique/rule-of-thirds.html
- Courbes tonales / contraste : https://toddmarsh.com/lightroom-tone-curve-guide/, https://www.lightroomqueen.com/community/threads/using-basic-tone-vs-tone-curve-to-adjust-photos, https://frameandfocal.com/photography-tips/4-steps-improve-photos-use-tone-curves
- Balance des blancs / gray world : https://mattmaulion.medium.com/white-balancing-an-enhancement-technique-in-image-processing-8dd773c69f6, https://codeandlife.com/2019/08/17/correcting-image-white-balance-with-python-pil-and-numpy/, https://docs.opencv.org/3.4/d7/d71/classcv_1_1xphoto_1_1GrayworldWB.html
- Split-toning / teal-orange : https://beverlyboy.com/filmmaking/what-is-teal-orange-look/, https://amateurphotographer.com/technique/photo_editing/how-to-do-colour-grading/, https://www.diyphotography.net/cinematic-color-grading-skin-tone/
- LUT : https://www.shutterevolve.com/color-grading-and-luts-explained/, https://jackchou00.com/en/posts/apply-lut-in-python/
- Sur-saturation / clipping : https://new.clippingfly.com/how-to-avoid-oversaturated-colors-in-professional-edits/
- Vignette : https://fstoppers.com/lightroom/how-use-vignettes-improve-your-photos-692134
- Unsharp mask / halos : https://www.researchgate.net/publication/231608978_Unsharp_Masking_Countershading_and_Halos_Enhancements_or_Artifacts, exemples de code : https://github.com/soroushj/python-opencv-numpy-example/blob/master/unsharpmask.py
- Contraste local (clarity) : https://www.cambridgeincolour.com/tutorials/local-contrast-enhancement.htm, https://geraldbakker.nl/psnumbers/sharpen-3.html
- Distorsion grand-angle : https://learnopencv.com/understanding-lens-distortion/, https://answers.opencv.org/question/45715/correct-barrel-distortion-without-reference-images/
- Dodge & burn : https://photographylife.com/mastering-dodge-and-burn-in-photography
