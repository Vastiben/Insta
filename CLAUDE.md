# Insta — assistant de retouche et post Instagram de Bastien

Ce repo transforme une photo brute envoyée par Bastien en **trois
propositions complètes** pour Instagram (cadrage + retouche couleur +
suggestion musicale), et enrichit son propre catalogue de techniques par
recherche web périodique.

Bastien communique en français. Réponds en français.

## Démarrer ici

- **Comment ça marche** : `.claude/skills/insta-post/SKILL.md` — le point
  d'entrée, déclenché quand Bastien envoie une photo en mentionnant Insta.
- **Le schéma complet** (flow, agents, pourquoi cette découpe) :
  `docs/ARCHITECTURE.md`.
- **Le catalogue de techniques** (plus large que les presets actifs) :
  `docs/style-options.md`.
- **Les 3 presets actifs** utilisés par le script de retouche :
  `presets/styles.json`.
- **Le script de retouche** : `scripts/retouch.py` (Pillow/numpy/OpenCV —
  `pip install -r requirements.txt` si les dépendances manquent).

## Principes

- **Les photos ne sont jamais commitées.** Sources et exports sont
  volatiles, envoyés directement à Bastien (`SendUserFile`) — seuls les
  fichiers de suivi/catalogue le sont (`presets/`, `docs/`,
  `data/state.json`).
- **Le catalogue de techniques (`docs/style-options.md`) ne s'écrase
  jamais**, il se complète — une recherche web ajoute une section datée en
  fin de fichier, ne réécrit jamais les précédentes.
- **Promouvoir une technique documentée en preset actif est toujours une
  décision explicite** (Bastien, ou Alfred qui propose et attend
  validation) — jamais automatique, même après une recherche réussie.
- **Musique** : Spotify est connecté (`mcp__Spotify__search`). La création
  de playlist (`mcp__Spotify__create_playlist`) reste une action que
  Bastien déclenche lui-même explicitement — jamais automatique dans le
  pipeline (nécessite Premium, et c'est le genre de décision qu'il veut
  prendre en direct).
- **Instagram lui-même n'est pas accessible depuis cette session** —
  `instagram.com` et les domaines Meta sont bloqués par le proxy réseau de
  l'environnement (confirmé le 2026-09-05). Ce repo prépare les fichiers ;
  poster reste manuel, côté Bastien.

## Conventions

- Dates en `AAAA-MM-JJ`.
- Un preset actif = un objet dans `presets/styles.json`, avec un `id`
  stable (jamais renommé une fois utilisé — un historique de proposition
  pourrait y faire référence).
- `data/state.json` est la seule source de vérité sur le compteur de
  photos / la cadence de recherche — ne pas la recalculer autrement.
