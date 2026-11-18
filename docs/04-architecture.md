# 04 — Architecture technique

## Stack

| Couche | Choix |
|---|---|
| Langage | Python 3.12+ |
| Gestion du projet | `uv` |
| Web | FastAPI |
| Rendu | Jinja2 (rendu serveur) + HTMX (interactions partielles, polling des commentaires et des messages privés) |
| Base de données | SQLite + SQLAlchemy 2 (ORM) + Alembic (migrations) |
| Mots de passe | Argon2 (`argon2-cffi`) |
| Sessions | Cookie signé (`itsdangerous` / `SessionMiddleware`) |
| Interface | CSS maison à base de tokens, polices Fraunces et Nunito Sans auto-hébergées, HTMX 2 servi en local |
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
├── .env.example
├── app/
│   ├── main.py              # création de l'app, middlewares, routers, pages d'erreur
│   ├── config.py            # settings (variables d'env préfixées NOEL_)
│   ├── db.py                # engine, session, PRAGMA foreign_keys, migrations au démarrage
│   ├── models.py            # modèles SQLAlchemy
│   ├── errors.py            # NotAuthenticated, Forbidden, NotFound, Invalid
│   ├── security.py          # hachage, session, CSRF, dépendances current_member / current_admin
│   ├── web.py               # rendu des templates, filtres (dates, prix), redirections
│   ├── cli.py               # create-admin
│   ├── services/            # règles métier, sans HTTP
│   │   ├── visibility.py    # ⚠️ matrice RG-30 : seul endroit qui décide de ce qui est visible
│   │   ├── gifts.py
│   │   ├── reservations.py
│   │   ├── comments.py
│   │   ├── notifications.py # mentions @Prénom, nouveaux cadeaux, notifications (RG-42 à RG-45, RG-57)
│   │   ├── shopping.py      # listes de courses partagées (RG-59 à RG-61)
│   │   ├── messages.py      # ⚠️ messages privés : seul endroit qui décide de qui lit une conversation (RG-46 à RG-55)
│   │   ├── users.py
│   │   ├── admin.py         # liste des cadeaux côté admin, clôture de l'année
│   │   ├── images.py
│   │   └── text.py
│   ├── routers/
│   │   ├── auth.py          # /login, /logout
│   │   ├── people.py        # / (menu des applications, RG-58), /noel (liste des personnes)
│   │   ├── gifts.py         # /personnes/{id}, /cadeaux/...
│   │   ├── shopping.py      # /courses/... (listes de courses)
│   │   ├── comments.py      # /cadeaux/{id}/commentaires, /commentaires/{id}/...
│   │   ├── notifications.py # /notifications
│   │   ├── messages.py      # /messages/... (pop-up et pleine page)
│   │   ├── profile.py       # /profil
│   │   └── admin.py         # /admin/...
│   ├── templates/           # pages, fragments HTMX (_*.html), macros.html, admin/, messages/, shopping/
│   └── static/              # css/ (tokens, base, components), fonts/, js/ (htmx.min.js, mentions.js, messages.js)
├── migrations/              # Alembic
├── data/                    # base SQLite et clé de session (hors git)
├── media/                   # images envoyées (hors git, volume persistant en prod)
├── media_private/           # photos des messages privés, jamais servies en statique (hors git, volume persistant)
└── tests/
    ├── conftest.py          # base SQLite en mémoire, fixtures membres / admin
    ├── test_visibility.py   # tests de la matrice de confidentialité
    └── ...
```

## Principes

1. **Les services portent les règles métier**, les routers ne font que HTTP + templates. Les services sont testables sans serveur.
2. **Toute lecture de cadeaux/commentaires/réservations côté membre passe par `services/visibility.py`.** Aucune requête directe dans un router. De même, toute lecture de conversations, de messages privés ou de leurs photos passe par `services/messages.py`, qui vérifie que le membre est participant (RG-47).
3. **Contrôle d'accès par dépendances FastAPI** : `current_member` (403 si admin ou non connecté) et `current_admin` (403 si membre).
4. **Pas de JavaScript maison** au-delà de HTMX, sauf besoin justifié et validé. Seule exception à ce jour : `static/js/mentions.js` (aide à la saisie des mentions, US-27, et envoi avec Entrée sur ordinateur, RG-33), chargé uniquement sur les pages de commentaires. Deuxième exception : `static/js/messages.js` (pop-up des messages privés, RG-55), chargé sur les pages membre. Il ouvre et ferme la pop-up, la rouvre au même endroit après un changement de page, garde le fil calé en bas et envoie avec Entrée. Sans lui, la messagerie fonctionne en pleine page sur `/messages`.

## Sécurité

- Mots de passe hachés en Argon2, jamais journalisés.
- Cookie de session `HttpOnly`, `SameSite=Lax`, `Secure` en production, durée 30 jours.
- Protection CSRF sur tous les formulaires POST (jeton en session + champ caché / en-tête HTMX).
- Blocage après 5 échecs (RG-05).
- Upload : type vérifié par Pillow (pas seulement par l'extension), taille plafonnée, nom de fichier généré (UUID), servi depuis `media/`.
- Photos des messages privés : stockées dans `media_private/`, hors du dossier statique, et servies par une route qui vérifie que le membre est participant de la conversation (RG-47).
- Liens cadeaux : schéma `http`/`https` uniquement, `rel="noopener noreferrer"`.
- Échappement automatique Jinja2 activé (commentaires, noms de cadeaux).
- Secrets (`SECRET_KEY`, chemin de la BDD) en variables d'environnement, fichier `.env` hors git.

## Déploiement (à préciser)

- Image Docker unique : `uvicorn app.main:app`.
- Les migrations (`alembic upgrade head`) sont appliquées automatiquement au démarrage de l'application.
- Variables à définir chez l'hébergeur : `NOEL_SECRET_KEY`, `NOEL_SECURE_COOKIES=true`. Le `Dockerfile` place la base, les images et les photos privées (`NOEL_PRIVATE_MEDIA_DIR`) dans `/data`.
- **Volume persistant obligatoire** monté sur `/data` (base et images), sinon la base et les images sont perdues à chaque redéploiement sur un PaaS.
- Premier déploiement : `python -m app.cli create-admin` pour créer le compte admin.
- Sauvegarde : copie régulière du fichier SQLite et des dossiers `media/` et `media_private/` (à définir).
