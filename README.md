# Insta — assistant de retouche et post Instagram

Transforme une photo brute envoyée par Bastien en **trois propositions
complètes** pour Instagram (cadrage + retouche couleur + suggestion
musicale ancrée dans ses vrais goûts Spotify), et enrichit son propre
catalogue de techniques par recherche web périodique.

Se déclenche dans Claude Code quand Bastien envoie une photo en mentionnant
Insta/Instagram (skill `insta-post`) — voir `CLAUDE.md` pour le guide de
démarrage détaillé.

## Architecture

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

Détail complet du raisonnement architecture (pourquoi cette découpe
agents/skill, données persistées vs volatiles, historique de conception) :
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Composants

| Composant | Type | Modèle | Rôle |
|---|---|---|---|
| [`insta-post`](.claude/skills/insta-post/SKILL.md) | Skill | — (orchestre dans la conversation principale) | Point d'entrée. Regarde la photo, choisit le point focal, lance les agents en parallèle, présente le résultat. |
| [`photo-stylist`](.claude/agents/photo-stylist.md) | Agent | Haiku | Exécute `scripts/retouch.py` pour un preset donné — mécanique, déterministe. |
| [`music-curator`](.claude/agents/music-curator.md) | Agent | Sonnet | Cherche des morceaux Spotify ancrés dans les goûts réels de Bastien (pas un mood générique) et adaptés au style de la photo. |
| [`style-researcher`](.claude/agents/style-researcher.md) | Agent | Sonnet | Recherche web périodique (tous les 10 photos) de nouvelles techniques, documentées dans `docs/style-options.md`. |

## Structure du repo

```
CLAUDE.md                    guide de démarrage pour une session Claude Code
docs/
  ARCHITECTURE.md            raisonnement complet de l'architecture
  style-options.md           catalogue vivant de toutes les techniques connues
  research/                  recherches web archivées (source des presets)
presets/styles.json          les 3 presets actifs (crop + couleur + mood musical)
scripts/retouch.py           script de retouche paramétré par preset
data/state.json              compteur de photos / cadence de recherche
.claude/skills/insta-post/   la skill qui orchestre tout
.claude/agents/              les 3 agents ci-dessus
```

## Principes clés

- **Les photos ne sont jamais commitées** — sources et exports sont
  volatiles, envoyés directement à Bastien.
- **`docs/style-options.md` ne s'écrase jamais**, il se complète au fil des
  recherches périodiques.
- **Promouvoir une technique en preset actif reste toujours une décision
  explicite** — jamais automatique.
- **Instagram lui-même n'est pas accessible** depuis les sessions Claude
  Code (domaines Meta bloqués) — ce repo prépare les fichiers, poster reste
  manuel.

Détail complet : [`CLAUDE.md`](CLAUDE.md).
