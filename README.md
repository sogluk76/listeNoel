# Liste de Noël

Site web familial de listes de cadeaux de Noël, qui remplace l'application Power Apps existante.

Chaque membre de la famille tient sa liste de cadeaux, consulte celle des autres, suggère des idées pour quelqu'un d'autre, réserve ou marque comme acheté un cadeau, et en discute dans les commentaires. Tout ça sans que la personne concernée voie les surprises qu'on lui prépare.

## Lancer le site

Il faut [uv](https://docs.astral.sh/uv/) (qui installe Python tout seul si besoin).

```bash
uv sync                                  # installe les dépendances
uv run python -m app.cli create-admin    # crée le compte admin (une seule fois)
uv run uvicorn app.main:app --reload     # démarre le site
```

Ensuite :

1. Ouvre <http://localhost:8000/admin/login> et connecte-toi avec le compte admin.
2. Crée les comptes de la famille (« Nouveau membre »).
3. Chaque personne se connecte sur <http://localhost:8000> avec son prénom et son mot de passe.

La base (`data/app.db`) est créée et mise à jour automatiquement au démarrage. Les images envoyées vont dans `media/`. Ces deux dossiers sont à sauvegarder.

Pour y accéder depuis un téléphone sur le même Wi-Fi : `uv run uvicorn app.main:app --host 0.0.0.0`, puis `http://<adresse-ip-du-pc>:8000`.

## Tests

```bash
uv run pytest -q       # 100 tests, dont ceux de la confidentialité (tests/test_visibility.py)
uv run ruff check .
```

## Configuration

Les réglages passent par des variables d'environnement préfixées `NOEL_`, ou par un fichier `.env` (modèle : `.env.example`).

| Variable | Rôle | Défaut |
|---|---|---|
| `NOEL_SECRET_KEY` | Clé de signature des sessions. **À définir en production.** | générée dans `data/secret_key` |
| `NOEL_SECURE_COOKIES` | `true` en production (HTTPS) | `false` |
| `NOEL_DATABASE_URL` | Emplacement de la base SQLite | `sqlite:///data/app.db` |
| `NOEL_MEDIA_DIR` | Dossier des images | `media/` |

## Mise en ligne

Un `Dockerfile` est fourni (non testé sur un hébergeur pour l'instant). L'hébergeur doit fournir un **volume persistant** monté sur `/data`, sinon la base et les images sont perdues à chaque redéploiement. Voir [docs/04-architecture.md](docs/04-architecture.md).

## Documentation

| Document | Contenu |
|---|---|
| [docs/01-vision.md](docs/01-vision.md) | Objectif, utilisateurs, périmètre |
| [docs/02-regles-metier.md](docs/02-regles-metier.md) | Règles fonctionnelles, dont la matrice de confidentialité |
| [docs/03-modele-donnees.md](docs/03-modele-donnees.md) | Schéma de la base (Mermaid + SQL) |
| [docs/04-architecture.md](docs/04-architecture.md) | Stack, arborescence, sécurité, déploiement |
| [docs/05-backlog.md](docs/05-backlog.md) | Lots d'incréments, statut des user stories |
| [docs/06-points-ouverts.md](docs/06-points-ouverts.md) | Choix appliqués par défaut, à confirmer |
| [docs/07-journal.md](docs/07-journal.md) | Journal des incréments livrés |
| [docs/user-stories/](docs/user-stories/) | User stories par thème |

## Travailler avec Claude Code

Les consignes sont dans [CLAUDE.md](CLAUDE.md) et le dossier [.claude/](.claude/). Commandes disponibles :

- `/story US-11` : implémente une user story par petits incréments
- `/diff-summary` : résume le diff en cours avant validation
- `/update-docs` : met la documentation à jour une fois les tests au vert

Le skill `design-site` (`.claude/skills/design-site/`) donne la direction artistique. Claude Code l'utilise automatiquement dès qu'il touche un template ou le CSS.
