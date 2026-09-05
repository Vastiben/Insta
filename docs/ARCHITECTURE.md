# Architecture — `insta-post`

## Vue d'ensemble

```mermaid
flowchart TD
    A["Bastien envoie une photo\n+ mentionne Insta"] --> B["Skill insta-post\nse déclenche"]
    B --> C["Alfred regarde la photo\n(sujet, point focal, orientation)"]
    C --> D["Charge presets/styles.json\n(3 presets actifs)"]

    D --> E1["Preset 1\nÉpuré / lumineux"]
    D --> E2["Preset 2\nCinéma teal-orange"]
    D --> E3["Preset 3\nNoir & contrasté"]

    E1 --> F1["agent photo-stylist\n(Haiku, Bash)"]
    E2 --> F2["agent photo-stylist\n(Haiku, Bash)"]
    E3 --> F3["agent photo-stylist\n(Haiku, Bash)"]

    E1 --> G1["agent music-curator\n(Sonnet, Spotify search)"]
    E2 --> G2["agent music-curator\n(Sonnet, Spotify search)"]
    E3 --> G3["agent music-curator\n(Sonnet, Spotify search)"]

    F1 --> H["3 propositions\ncomplètes"]
    F2 --> H
    F3 --> H
    G1 --> H
    G2 --> H
    G3 --> H

    H --> I["Présentées à Bastien\n(SendUserFile x3)"]
    I --> J{"Bastien choisit\nou demande un ajustement"}

    B --> K["data/state.json\nphotos_processed += 1"]
    K --> L{"photos_processed -\nlast_research_at_count\n>= research_interval ?"}
    L -- non --> M["rien de plus"]
    L -- oui --> N["agent style-researcher\n(Sonnet, WebSearch, tâche de fond)"]
    N --> O["docs/style-options.md\nnouvelle section ajoutée"]
    O --> P["Alfred propose une promotion\nen preset actif si pertinent\n(validation Bastien)"]
    P -.->|"si validé"| D

    style F1 fill:#2d5a4a,color:#fff
    style F2 fill:#2d5a4a,color:#fff
    style F3 fill:#2d5a4a,color:#fff
    style G1 fill:#4a3a5a,color:#fff
    style G2 fill:#4a3a5a,color:#fff
    style G3 fill:#4a3a5a,color:#fff
    style N fill:#5a4a2d,color:#fff
```

## Composants

| Composant | Type | Modèle | Rôle |
|---|---|---|---|
| `insta-post` | Skill | — (orchestre dans la conversation principale) | Point d'entrée. Regarde la photo, choisit le point focal, lance les agents en parallèle, présente le résultat. |
| `photo-stylist` | Agent | Haiku | Exécute `scripts/retouch.py` pour un preset donné. Mécanique, déterministe, aucun jugement créatif. |
| `music-curator` | Agent | Sonnet | Cherche 1-2 morceaux Spotify adaptés au mood du preset + au contenu réel de la photo. Demande un peu de jugement (fit), reste sur Sonnet. |
| `style-researcher` | Agent | Sonnet | Recherche web périodique (tous les 10 photos) de nouvelles techniques, documentées dans `docs/style-options.md`. Ne touche jamais aux presets actifs. |

## Pourquoi cette découpe (agents vs skill)

- **Ce qui reste dans la skill (conversation principale)** : tout ce qui a
  besoin de *voir* la photo (choix du point focal, appréciation de la
  composition) — un sous-agent lancé via `Task`/`Agent` ne reçoit pas
  forcément l'image de la conversation, donc ce jugement visuel reste dans
  la session qui a effectivement reçu la photo de Bastien.
- **Ce qui part en agent Haiku (`photo-stylist`)** : une fois le preset et
  le point focal fixés, l'exécution est 100% déterministe (même script,
  mêmes paramètres → même résultat) — la politique de choix de modèle
  d'Alfred réserve ce type de tâche à Haiku.
- **Ce qui part en agent Sonnet (`music-curator`, `style-researcher`)** :
  les deux demandent un vrai jugement (est-ce que CE morceau va avec CETTE
  photo ; est-ce que CETTE technique trouvée en ligne est pertinente et
  différente de ce qui est déjà catalogué) — pas mécanique, donc pas Haiku,
  mais pas non plus un besoin de raisonnement assez difficile pour justifier
  Opus.
- **Parallélisation** : les 3 presets sont indépendants — `photo-stylist`
  et `music-curator` sont lancés 3x chacun en parallèle plutôt qu'en
  séquence, pour que les 3 propositions arrivent en même temps plutôt que
  d'attendre 6 exécutions à la suite.

## Données persistées vs volatiles

- **Persisté (commité)** : `presets/styles.json` (presets actifs),
  `docs/style-options.md` (catalogue complet), `data/state.json` (compteur
  de photos / cadence de recherche), `docs/research/*` (recherches web
  complètes archivées).
- **Volatile (jamais commité)** : les photos sources et les images
  retouchées produites — envoyées directement à Bastien
  (`SendUserFile`), jamais stockées dans le repo (ce sont des photos
  personnelles, pas de la documentation de projet).

## Historique de conception

Conçu le 2026-09-05 après une première itération manuelle (un seul script
`retouch.py` non paramétré, un seul style, testé sur une photo — voir
`docs/research/photo-retouching-methods.md` pour le diagnostic qui a motivé
le passage à plusieurs styles distincts plutôt qu'un réglage global unique).
Bastien a demandé explicitement : trois propositions par photo (cadrage +
retouche + musique), une recherche web périodique pour enrichir le
catalogue de techniques (tous les 10 photos), et une architecture
documentée avec agents/skills — ce document répond à cette dernière
demande.
