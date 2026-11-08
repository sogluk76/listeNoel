---
description: Met la documentation à jour en fin d'incrément (tests verts uniquement)
---

1. Lance `uv run pytest -q`. **Si un test échoue, arrête-toi** : la doc ne se met à jour qu'avec des tests verts.
2. Mets à jour, seulement si c'est nécessaire :
   - `docs/05-backlog.md` : statut des stories et tâches
   - `docs/07-journal.md` : nouvelle entrée au format indiqué en tête du fichier
   - `docs/02-regles-metier.md` : règle ajoutée, précisée ou modifiée (avec Lukas)
   - `docs/03-modele-donnees.md` : si une migration a changé le schéma (Mermaid + DDL)
   - `docs/04-architecture.md` : si la structure ou une dépendance a changé
   - `docs/06-points-ouverts.md` : cocher les points tranchés et reporter la décision dans les règles
   - la user story si un critère d'acceptation a été précisé
3. Affiche la liste des fichiers de doc modifiés, avec une ligne par changement.
