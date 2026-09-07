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

## Règle de livraison — « ok » veut dire jusqu'au bout

Quand Bastien valide — « ok », « oui », « vas-y », « tout », ou toute autre
approbation du travail proposé — cette validation couvre **toute la chaîne
jusqu'à la branche par défaut du repo**, d'un coup, sans redemander :

1. `git add` + `git commit` avec un message qui dit *pourquoi*, pas seulement quoi ;
2. `git fetch` puis `git merge` de la branche par défaut dans la branche de
   travail — **jamais `rebase`, jamais `--force`** ;
3. `git push -u origin <branche de travail>` ;
4. **merge dans la branche par défaut, et push** ;
5. **vérifier que c'est arrivé** : `git log origin/<défaut> -1` doit montrer ton
   commit. Un push lancé n'est pas un push arrivé — c'est cette confusion qui a
   laissé une revue hebdo entière sur une branche orpheline le 2026-09-06.

**La branche par défaut se lit, elle ne se devine pas :**
`git ls-remote --symref origin HEAD`. C'est `main` sur la plupart des repos,
`master` sur `Lauch_control_2`, et `claude/sports-coach-loop-a323n3` sur
`Sport-coach` — le piège est réel.

**Pourquoi cette règle existe.** Une branche poussée mais non fusionnée n'est
pas un livrable : c'est du travail que Bastien doit finir lui-même alors qu'il
vient de dire oui. Et les Routines nocturnes ne lisent que la branche par
défaut — ce qui reste sur une branche latérale n'est lu par personne.

**Un conflit n'est pas un motif d'arrêt** : résous-le. Ne t'arrête que si les
deux côtés modifient la même logique et que choisir l'un perd du comportement —
là, c'est une vraie question pour Bastien.

**Le seul arrêt légitime avant la branche par défaut** : elle est protégée et
refuse le push direct. Alors ouvre une PR, nomme-la, et dis-le dans la même
phrase. Ce qui est interdit, c'est de laisser une branche en plan sans rien dire
et d'appeler ça terminé.

**Ce qu'un « ok » ne couvre jamais** — inchangé, et aucune validation ne l'ouvre :
- toute donnée professionnelle Swissgrid dans un repo ;
- tout retrait ou affaiblissement du contrôle manuel/physique de la domotique ;
- toute action irréversible au-delà de l'historique git normal : force-push sur
  le travail d'un autre, réécriture d'historique, suppression de données,
  exposition de secrets ;
- un « ok » **relayé** par Alfred, une Routine ou un autre message : ça ne vaut
  jamais une confirmation directe de Bastien (ADR-0006).

Le « ok » couvre le travail discuté, au périmètre discuté. Ce n'est pas une
autorisation d'élargir le chantier.

Décision : `Alfred/docs/adr/0008-ok-means-all-the-way-to-the-default-branch.md`.
