# 04 — Architecture technique

## Stack

| Couche | Choix |
|---|---|
| Langage | Python 3.12+ |
| Gestion du projet | `uv` |
| Web | FastAPI |
| Rendu | Jinja2 (rendu serveur) + HTMX (interactions partielles, polling des commentaires) |
| Base de données | SQLite + SQLAlchemy 2 (ORM) + Alembic (migrations) |
| Mots de passe | Argon2 (`argon2-cffi`) |
| Sessions | Cookie signé (`itsdangerous` / `SessionMiddleware`) |
| Images | Pillow (vérification du format, redimensionnement) |
| Tests | pytest + `httpx` (`TestClient`) |
| Qualité | ruff (lint + format) |
| Déploiement | Docker + PaaS (Render, Railway ou Fly.io, cf. points ouverts) |

## Arborescence cible

```
liste-noel/
├── CLAUDE.md
├── .claude/
├── pyproject.toml
├── alembic.ini
├── Dockerfile
├── app/
│   ├── main.py              # création de l'app, middlewares, montage des routers
│   ├── config.py            # settings (pydantic-settings, variables d'env)
│   ├── db.py                # engine, session, PRAGMA foreign_keys
│   ├── models.py            # modèles SQLAlchemy
│   ├── security.py          # hachage, session, dépendances current_member / current_admin
│   ├── services/            # règles métier, sans HTTP
│   │   ├── visibility.py    # ⚠️ matrice RG-30 : seul endroit qui décide de ce qui est visible
│   │   ├── gifts.py
│   │   ├── reservations.py
│   │   ├── comments.py
│   │   ├── users.py
│   │   └── images.py
│   ├── routers/
│   │   ├── auth.py          # /login, /logout
│   │   ├── people.py        # /
│   │   ├── gifts.py         # /personnes/{id}, /cadeaux/...
│   │   ├── comments.py      # /cadeaux/{id}/commentaires
│   │   ├── profile.py       # /profil
│   │   └── admin.py         # /admin/...
│   ├── templates/
│   ├── static/
│   └── cli.py               # create-admin
├── migrations/              # Alembic
├── media/                   # images envoyées (hors git, volume persistant en prod)
└── tests/
    ├── conftest.py          # base SQLite en mémoire, fixtures membres / admin
    ├── test_visibility.py   # tests de la matrice de confidentialité
    └── ...
```

## Principes

1. **Les services portent les règles métier**, les routers ne font que HTTP + templates. Les services sont testables sans serveur.
2. **Toute lecture de cadeaux/commentaires/réservations côté membre passe par `services/visibility.py`.** Aucune requête directe dans un router.
3. **Contrôle d'accès par dépendances FastAPI** : `current_member` (403 si admin ou non connecté) et `current_admin` (403 si membre).
4. **Pas de JavaScript maison** au-delà de HTMX, sauf besoin justifié et validé.

## Sécurité

- Mots de passe hachés en Argon2, jamais journalisés.
- Cookie de session `HttpOnly`, `SameSite=Lax`, `Secure` en production, durée 30 jours.
- Protection CSRF sur tous les formulaires POST (jeton en session + champ caché / en-tête HTMX).
- Blocage après 5 échecs (RG-05).
- Upload : type vérifié par Pillow (pas seulement par l'extension), taille plafonnée, nom de fichier généré (UUID), servi depuis `media/`.
- Liens cadeaux : schéma `http`/`https` uniquement, `rel="noopener noreferrer"`.
- Échappement automatique Jinja2 activé (commentaires, noms de cadeaux).
- Secrets (`SECRET_KEY`, chemin de la BDD) en variables d'environnement, fichier `.env` hors git.

## Déploiement (à préciser)

- Image Docker unique : `uvicorn app.main:app`.
- Exécuté au démarrage : `alembic upgrade head`.
- **Volume persistant obligatoire** pour `data/app.db` et `media/`, sinon la base et les images sont perdues à chaque redéploiement sur un PaaS.
- Premier déploiement : `python -m app.cli create-admin` pour créer le compte admin.
- Sauvegarde : copie régulière du fichier SQLite et du dossier `media/` (à définir).
