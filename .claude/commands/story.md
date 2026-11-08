---
description: Implémente une user story par petits incréments validés
argument-hint: US-xx
---

Implémente la user story **$ARGUMENTS**.

1. Lis la story dans `docs/user-stories/`, les règles `RG-xx` qu'elle cite dans `docs/02-regles-metier.md` et vérifie `docs/06-points-ouverts.md`.
2. Liste les questions ou ambiguïtés éventuelles. S'il y en a, **pose-les et arrête-toi là**.
3. Propose un découpage en incréments (2 à 4 en général) : pour chacun, les fichiers touchés et les tests prévus (un par critère d'acceptation minimum, plus les tests de confidentialité si la story touche cadeaux, commentaires ou réservations). Passe la story en 🟨 dans `docs/05-backlog.md`. **Attends la validation.**
4. Réalise **un seul** incrément : tests et code, puis exécute `uv run pytest -q` et `uv run ruff check .`.
5. Termine par le résumé du diff (format `/diff-summary`) et **attends le feu vert** avant l'incrément suivant.
6. Quand tous les incréments sont faits et les tests verts, lance `/update-docs` et passe la story en ✅.
