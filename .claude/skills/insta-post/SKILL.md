---
name: insta-post
description: >-
  Génère trois propositions complètes (cadrage + retouche + musique) pour un
  post Instagram, à partir d'une photo que Bastien envoie. Utilise cette
  skill dès que Bastien upload une image ET mentionne Insta/Instagram dans
  le même message ou juste après — par exemple "voilà la photo, pour insta",
  "je veux poster ça", ou une photo suivie de "insta ?". Ne se déclenche pas
  sur une photo seule sans contexte Instagram (health-import et d'autres
  skills gèrent déjà les autres cas d'usage des images).
---

# insta-post

Pipeline qui transforme une photo brute en trois propositions prêtes à
poster, chacune avec sa propre identité (cadrage, retouche couleur,
suggestion musicale cohérente). Voir `docs/ARCHITECTURE.md` pour le schéma
complet du flow et `docs/style-options.md` pour le catalogue de techniques
dont sont tirés les presets actifs (`presets/styles.json`).

## Étapes

1. **Regarde la photo directement** (toi, pas un sous-agent — c'est la
   seule étape qui a besoin de voir l'image dans cette conversation).
   Repère : le sujet principal, sa position approximative dans le cadre
   (point focal, en fraction [0,1] de la largeur/hauteur), et si l'image
   est mal orientée (ex. selfie pris à l'envers, cas déjà rencontré).

2. **Charge `presets/styles.json`** — les 3 presets actifs. Ne les modifie
   pas ici ; c'est le rôle de l'étape 6 / du `style-researcher`.

3. **Pour chacun des 3 presets, en parallèle** : lance l'agent
   `photo-stylist` avec la photo source, le point focal repéré à l'étape 1,
   le flag de rotation si besoin, et l'id du preset. Récupère les 3 images
   produites.

4. **Pour chacun des 3 presets, en parallèle** : lance l'agent
   `music-curator` avec le `musique_mood` du preset et une description
   courte de la scène (2-3 mots) pour affiner le fit. Récupère 1-2
   suggestions par preset.

5. **Présente les 3 propositions à Bastien** — chaque proposition = image
   retouchée + suggestion(s) musicale(s) + nom du style. Pas de légende
   texte automatique ici (voir note ci-dessous) : Bastien préfère
   visiblement décider ça lui-même au cas par cas, laisse-le demander si
   besoin plutôt que d'imposer un texte à chaque fois.

6. **Met à jour `data/state.json`** : incrémente `photos_processed` de 1,
   committe. Si `photos_processed - last_research_at_count >=
   research_interval` : lance l'agent `style-researcher` en tâche de fond
   (ne bloque pas la réponse à Bastien dessus), puis une fois terminé mets
   à jour `last_research_at_count` et `last_research_date`, committe.

7. **Commit** : les images produites ne sont pas commitées dans le repo
   (fichiers volatiles, envoyés directement à Bastien via `SendUserFile`) —
   seuls les fichiers de suivi (`data/state.json`) et les mises à jour de
   catalogue (`docs/style-options.md`) le sont. Un « go » de Bastien sur une
   proposition ne déclenche pas de push supplémentaire ici — voir note.

## Notes

- **Texte/légende** : Bastien a un avis marqué sur le ton (voir historique
  de conversation — sobre, direct, pas de sur-explication). Ne génère pas
  de légende automatiquement dans chaque proposition ; propose-la seulement
  si Bastien la demande explicitement, avec 2-3 registres courts (voir
  exemples déjà donnés en conversation : minimaliste / direct-confiant /
  silencieux).
- **Musique sur une photo statique** : Instagram ne permet la musique en
  feed permanent que via un Reel (voir conversation) — le sticker musique
  Story est éphémère. Si Bastien veut le Reel, c'est une étape
  supplémentaire (clip vidéo court à partir de la photo retouchée),
  pas encore couverte par cette skill — à ajouter si le besoin se confirme.
- **Promotion d'une technique en preset actif** : reste une décision
  explicite (Bastien, ou Alfred qui la propose et attend validation) —
  jamais automatique même après une recherche `style-researcher` réussie.
