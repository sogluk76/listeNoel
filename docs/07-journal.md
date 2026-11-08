# 07 — Journal des incréments

Une entrée par incrément livré (tests verts). Format :

```
## AAAA-MM-JJ — US-xx (incrément n) — titre court
- Fait : …
- Fichiers : …
- Tests : x ajoutés, total y verts
- Décisions validées : …
```

---

## 2026-11-06 — Cadrage
- Fait : analyse des écrans Power Apps, règles métier, modèle de données, user stories, configuration Claude Code.
- Décisions validées : stack FastAPI + Jinja2/HTMX + SQLite, admin = compte distinct limité au panel, réservation multiple + statut acheté, suppression douce, archivage annuel.

## 2026-11-08 — Lot 0 (incréments 1 à 6) — Socle technique
- Fait :
  - Incrément 1 : projet `uv`/FastAPI, structure de dossiers, config ruff + pytest.
  - Incrément 2 : `app/config.py` (pydantic-settings) et `app/db.py` (engine SQLite, `PRAGMA foreign_keys` activé à chaque connexion).
  - Incrément 3 : modèles SQLAlchemy (`User`, `Gift`, `Reservation`, `Comment`) conformes à `03-modele-donnees.md`, première migration Alembic (mode batch pour les futures évolutions SQLite), vérifiée en upgrade/downgrade.
  - Incrément 4 : `tests/conftest.py` avec base SQLite en mémoire et fixtures `alice`/`bob`/`chloe`/`admin`.
  - Incrément 5 : layout Jinja2 de base, HTMX vendorisé dans `app/static/js/` (pas de CDN), protection CSRF (`app/security.py` : jeton en session, vérifié via en-tête HTMX ou champ caché).
  - Incrément 6 : hachage Argon2 (`hash_password`/`verify_password`) et commande `create-admin` (`app/cli.py`).
  - Dépôt git initialisé et connecté à `https://github.com/sogluk76/listeNoel.git` (premier commit `1a9d075`).
- Fichiers : `pyproject.toml`, `app/{config,db,models,main,security,cli}.py`, `app/templates/{base,index}.html`, `app/static/js/htmx.min.js`, `migrations/` (squelette Alembic + révision initiale), `tests/{conftest,test_db,test_models,test_fixtures,test_main,test_security,test_cli}.py`.
- Tests : 28 ajoutés, 28 verts.
- Décisions validées :
  - HTMX vendorisé plutôt que chargé depuis un CDN (indépendance réseau, pas de hash d'intégrité à maintenir).
  - Mot de passe de la commande `create-admin` : 8 caractères minimum, par cohérence avec la proposition de PO-09 — **PO-09 reste néanmoins ouvert**, cette valeur n'est appliquée ici qu'à la création du compte admin technique, pas encore tranchée pour US-05/US-24.

## 2026-11-08 — US-04 (incréments 1 et 2) — Se connecter en tant qu'admin
- Fait :
  - Incrément 1 : `app/services/users.py` (`authenticate()`, message générique RG-06), dépendances `current_member`/`current_admin` dans `app/security.py` (RG-09, RG-11 : relisent toujours le rôle/statut en base, jamais mis en cache en session), `/` protégée par `current_member`.
  - Incrément 2 : router `app/routers/admin.py` (`/admin/login`, `/admin`), templates `admin/login.html` et `admin/dashboard.html` (placeholder), `app/templating.py` pour partager l'instance Jinja2 entre routers.
  - Blocage après 5 échecs (RG-05) volontairement **laissé hors scope** : aucun critère d'acceptation testable de US-04 ne le couvre, et PO-01 (durée du blocage) n'est pas tranché. Sera construit avec US-03, pour membre et admin à la fois.
- Fichiers : `app/services/users.py`, `app/security.py`, `app/main.py`, `app/db.py`, `app/templating.py`, `app/routers/admin.py`, `app/templates/admin/*.html`, `tests/conftest.py` (fixtures `client`, `login_as`, `extract_csrf_token`), `tests/test_services_users.py`, `tests/test_access.py`, `tests/test_admin_auth.py`, `tests/test_main.py`.
- Tests : 22 ajoutés, 51 verts au total.
- Décisions validées :
  - `current_member`/`current_admin` : 403 si mauvais rôle, redirection (`/login` ou `/admin/login`) si pas de session ou session invalidée — pas seulement « 403 » comme le résumait `04-architecture.md`, corrigé dans la doc.
  - Deux bugs corrigés avant mise en service : `verify_password()` ne capturait que `VerifyMismatchError` (un hash malformé faisait planter au lieu d'échouer proprement) ; les bases SQLite en mémoire perdaient leur état entre requêtes FastAPI sans `StaticPool`.

## 2026-11-08 — US-05 (incréments 1 et 2) — Créer un compte membre
- Fait :
  - Incrément 1 : `create_member()` dans `app/services/users.py` (prénom unique insensible à la casse, confirmation du mot de passe, longueur minimale), route `/admin/membres/nouveau` (GET + POST, CSRF, réservée à l'admin) et son template.
  - Incrément 2 : `app/services/images.py` (`save_profile_photo()` — validation Pillow du contenu réel, formats JPEG/PNG/WebP, 5 Mo max, redimensionnement 800 px maximum sur le plus grand côté sans recadrage), champ photo optionnel branché sur le formulaire.
  - `create_admin()` déplacé de `app/cli.py` vers `app/services/users.py` pour partager sa validation avec `create_member()`.
  - Fixture `_media_dir_isole` (autouse) ajoutée pour que tous les tests écrivent dans un dossier temporaire, jamais dans le vrai `media/`.
- Fichiers : `app/services/users.py`, `app/services/images.py`, `app/cli.py`, `app/routers/admin.py`, `app/templates/admin/nouveau_membre.html`, `tests/conftest.py`, `tests/test_services_users.py`, `tests/test_services_images.py`, `tests/test_admin_membres.py`, `tests/test_cli.py`.
- Tests : 26 ajoutés, 77 verts au total.
- Décisions validées :
  - **PO-09** tranché : mot de passe, 8 caractères minimum, sans autre contrainte. Reporté en RG-10.
  - **PO-10** tranché : redimensionnement des images à 800 px maximum sur le plus grand côté, ratio conservé. Reporté en RG-17 (s'applique aussi aux photos de profil de US-06/US-23).
