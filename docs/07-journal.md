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
