# Liste de Noël

Site web familial de listes de cadeaux de Noël, qui remplace l'application Power Apps existante.

Chaque membre de la famille tient sa liste de cadeaux, consulte celle des autres, suggère des idées pour quelqu'un d'autre, réserve ou marque comme acheté un cadeau, et en discute dans les commentaires. Tout ça sans que la personne concernée voie les surprises qu'on lui prépare.

## Documentation

| Document | Contenu |
|---|---|
| [docs/01-vision.md](docs/01-vision.md) | Objectif, utilisateurs, périmètre |
| [docs/02-regles-metier.md](docs/02-regles-metier.md) | Règles fonctionnelles, dont la matrice de confidentialité |
| [docs/03-modele-donnees.md](docs/03-modele-donnees.md) | Schéma de la base (Mermaid + SQL) |
| [docs/04-architecture.md](docs/04-architecture.md) | Stack, arborescence, sécurité, déploiement |
| [docs/05-backlog.md](docs/05-backlog.md) | Lots d'incréments, statut des user stories |
| [docs/06-points-ouverts.md](docs/06-points-ouverts.md) | Questions encore à trancher |
| [docs/07-journal.md](docs/07-journal.md) | Journal des incréments livrés |
| [docs/user-stories/](docs/user-stories/) | User stories par thème |

## Démarrage rapide (une fois le socle codé)

```bash
uv sync
uv run alembic upgrade head
uv run python -m app.cli create-admin   # crée le compte admin
uv run uvicorn app.main:app --reload
uv run pytest
```

## Travailler avec Claude Code

Les consignes sont dans [CLAUDE.md](CLAUDE.md) et le dossier [.claude/](.claude/). Commandes disponibles :

- `/story US-11` : implémente une user story par petits incréments
- `/diff-summary` : résume le diff en cours avant validation
- `/update-docs` : met la documentation à jour une fois les tests au vert
