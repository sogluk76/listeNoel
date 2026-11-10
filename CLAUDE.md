# Liste de Noël — consignes pour Claude Code

Site web familial de listes de cadeaux de Noël (moins de 15 personnes), qui remplace une application Power Apps. Lukas est le seul développeur et valide chaque changement. On échange en français, et le code visible par les utilisateurs (textes, messages d'erreur) est en français.

## Principe central : la surprise

Un membre ne doit **jamais** pouvoir découvrir, sur sa propre liste, les suggestions qu'on lui a faites, les commentaires, les réservations ou les achats. C'est la matrice **RG-30** de [docs/02-regles-metier.md](docs/02-regles-metier.md).

- La règle s'applique **côté serveur**, pas seulement à l'affichage : une URL tapée à la main ne doit rien révéler.
- Toute lecture de cadeaux, commentaires ou réservations côté membre passe par `app/services/visibility.py`. Aucune requête directe dans un router.
- Tout changement qui touche cadeaux, commentaires ou réservations s'accompagne de tests dans `tests/test_visibility.py`.
- L'admin ne voit jamais les commentaires ni les réservations (RG-23).

## Commandes

```bash
uv sync                                  # installe les dépendances
uv run pytest -q                         # tests
uv run ruff check .                      # lint
uv run ruff format .                     # formatage
uv run uvicorn app.main:app --reload     # lance le site sur http://localhost:8000
uv run python -m app.cli create-admin    # crée le compte admin
uv run alembic revision --autogenerate -m "..."   # nouvelle migration
```

Tout passe par `uv` : ne jamais appeler `python`, `python3` ou `pip` directement (sur ce poste Windows, `python3` est le raccourci du Microsoft Store et ne fonctionne pas).

## Méthode de travail

- **Petits incréments validés.** Un incrément = tests + code, puis résumé du diff, puis attente du feu vert de Lukas avant le suivant. Pas de livraison « en une fois » sauf demande explicite.
- **Poser les questions avant de coder.** En cas d'ambiguïté sur une règle, s'arrêter et demander, plutôt que choisir à la place de Lukas.
- **Un test par critère d'acceptation** au minimum. Les tests citent les `RG-xx` qu'ils couvrent.
- **La doc ne se met à jour qu'avec des tests verts** (`/update-docs`).
- Commandes : `/story US-xx`, `/diff-summary`, `/update-docs`.
- Un hook relance `uv run pytest` après chaque modification de code. S'il échoue, corriger avant de continuer.

## Architecture

Stack : Python 3.12+, FastAPI, Jinja2 + HTMX, SQLite + SQLAlchemy 2 + Alembic, Argon2, pytest, ruff. Détail et arborescence dans [docs/04-architecture.md](docs/04-architecture.md).

- **Les services portent les règles métier** (`app/services/`, sans HTTP, testables sans serveur). Les routers ne font que HTTP + templates.
- **Contrôle d'accès par dépendances FastAPI** : `current_member` et `current_admin` (`app/security.py`). Un membre n'accède jamais à `/admin`, l'admin n'accède jamais aux écrans membres (RG-09).
- **Protection CSRF** sur tous les formulaires POST.
- **Pas de JavaScript maison** au-delà de HTMX, sauf besoin justifié et validé. Seule exception : `app/static/js/mentions.js`.
- **Tout changement de schéma passe par une migration Alembic** et une mise à jour de `docs/03-modele-donnees.md`.
- Interface : charger le skill `design-site` avant de toucher un template ou le CSS.

## Documentation

| Document | À lire quand |
|---|---|
| [docs/02-regles-metier.md](docs/02-regles-metier.md) | Avant tout changement fonctionnel (règles `RG-xx`) |
| [docs/user-stories/](docs/user-stories/) | Pour implémenter une story (`US-xx`) |
| [docs/06-points-ouverts.md](docs/06-points-ouverts.md) | Choix appliqués par défaut, à confirmer par Lukas (`PO-xx`) |
| [docs/05-backlog.md](docs/05-backlog.md) | Statut des lots et des stories |
| [docs/07-journal.md](docs/07-journal.md) | Historique des incréments livrés |
| [docs/03-modele-donnees.md](docs/03-modele-donnees.md) | Schéma de la base |

Une règle qui change se modifie à trois endroits : `02-regles-metier.md`, le code et les tests.

## À ne pas faire

- Ne pas lire `.env` ni `data/` (base réelle et clé de session).
- Ne pas faire `git push`. `git add` et `git commit` seulement sur demande.
- Ne pas ajouter de dépendance sans en parler d'abord.
