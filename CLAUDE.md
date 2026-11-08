# CLAUDE.md — Liste de Noël

Site familial de listes de cadeaux de Noël, qui remplace une application Power Apps. Moins de 15 utilisateurs. Toute la communication se fait **en français**.

## À lire avant toute tâche
1. `docs/02-regles-metier.md` : règles `RG-xx`, en particulier la **matrice de confidentialité RG-30**
2. La user story concernée dans `docs/user-stories/`
3. `docs/06-points-ouverts.md` : ne jamais coder une règle encore ouverte sans demander
4. `docs/03-modele-donnees.md` et `docs/04-architecture.md` si la tâche touche la base ou la structure

## Méthode de travail (obligatoire)

Lukas applique la « méthode Karpathy » : petits incréments relus, rien de généré n'est fiable tant qu'il n'a pas tourné.

1. **Questions d'abord.** Si une règle, un comportement ou un choix technique est ambigu ou absent des docs, **pose la question avant de coder**. Ne devine jamais une règle métier. Ne prends aucune décision d'architecture seul : propose 2 ou 3 options avec leurs compromis.
2. **Petits incréments.** Une user story est découpée en incréments de quelques fichiers au maximum (ex. : modèle + service + tests, puis router + template). Annonce le découpage et attends la validation avant de commencer.
3. **Tests à chaque modification.** Un hook relance `pytest` après chaque modification de fichier. Écris les tests en même temps que le code : chaque critère d'acceptation et chaque `RG-xx` touchée a au moins un test. Ne présente jamais du code comme fonctionnel sans l'avoir exécuté.
4. **Résumé du diff à chaque fin d'incrément** (commande `/diff-summary`) : fichiers touchés, ce qui change et pourquoi, tests ajoutés, résultat des tests, points d'attention. **Puis stop** : attends le feu vert de Lukas avant l'incrément suivant.
5. **Documentation à jour quand les tests sont verts** (commande `/update-docs`) : backlog, journal, règles ou modèle si ça a changé, points ouverts tranchés.
6. **Git** : pas de commit ni de push sans demande explicite.

## Règle n° 1 : la surprise

Un membre ne doit **jamais** voir, sur sa propre liste ou via une URL forgée : les suggestions qu'on lui a faites, les commentaires de ses cadeaux, les réservations et achats.

- Toute lecture de cadeaux, commentaires ou réservations côté membre passe par `app/services/visibility.py`. Pas de requête directe dans un router.
- Le filtrage se fait **côté serveur** dans la requête, jamais en masquant dans le template.
- Chaque nouvel écran ou endpoint exposant ces données ajoute un test dans `tests/test_visibility.py` qui vérifie que le destinataire ne reçoit rien, y compris les fragments HTMX.
- Les messages de retour (suppression, erreurs) ne doivent rien révéler au destinataire (ex. RG-22 : même message en suppression définitive ou douce).

## Rôles
- `member` : toute l'appli sauf `/admin`. Dépendance `current_member`.
- `admin` : compte distinct, **uniquement** `/admin`. Il n'est jamais destinataire, auteur, réservant ni commentateur. Dépendance `current_admin`.

## Stack et commandes

FastAPI · Jinja2 + HTMX · SQLite + SQLAlchemy 2 + Alembic · Argon2 · pytest · ruff · uv

```bash
uv sync                                  # dépendances
uv run uvicorn app.main:app --reload     # serveur de dev
uv run pytest -q                         # tests
uv run ruff check . && uv run ruff format .
uv run alembic revision --autogenerate -m "..."   # nouvelle migration
uv run alembic upgrade head
uv run python -m app.cli create-admin
```

## Conventions
- Code, noms de tables et de colonnes en **anglais** ; écrans, messages, docs et commits en **français**.
- Règles métier dans `app/services/`, sans dépendance HTTP ; routers minces.
- Toute modification de schéma passe par une migration Alembic, et `docs/03-modele-donnees.md` est mis à jour en même temps.
- Tests : base SQLite en mémoire, fixtures `alice`, `bob`, `chloe` (membres) et `admin`. Nommage `test_<us>_<comportement>` (ex. `test_us12_destinataire_ne_voit_pas_suggestion`).
- Dates affichées au format `07/12/2025 17:00`, prix au format `39,99 €`, fuseau Europe/Paris.
- Pas de JavaScript maison au-delà de HTMX sans validation.
- Le design sera travaillé à part : HTML sémantique simple et propre, sans framework CSS imposé tant que ce n'est pas décidé.
