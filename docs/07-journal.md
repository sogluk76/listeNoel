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

## 2026-11-08 — US-06 (incréments 1 et 2) — Modifier ou désactiver un compte
- Fait :
  - Incrément 1 : `list_members()` (tous les comptes membres, actifs ou non, admin exclu) et `update_member()` dans `app/services/users.py` (prénom unique hors soi-même, remplacement/suppression de la photo avec nettoyage de l'ancien fichier, refuse d'opérer sur un id qui n'est pas un membre — l'admin ne peut jamais être modifié/désactivé via cette fonction, même avec un id forgé) ; `delete_profile_photo()` dans `app/services/images.py`.
  - Incrément 2 : routes `GET /admin/membres` (liste) et `GET/POST /admin/membres/{id}/modifier`, templates associés. Ajout de `GET /media/{filename}` dans `app/main.py` : aucune route ne servait encore les photos uploadées depuis US-05, elles étaient stockées mais jamais consultables. Ajout du filtre Jinja `date_fr` (`app/templating.py`, convention `07/12/2025 17:00`, fuseau Europe/Paris) réutilisable par les prochaines stories affichant des dates.
- Fichiers : `app/services/users.py`, `app/services/images.py`, `app/routers/admin.py`, `app/templating.py`, `app/main.py`, `app/templates/admin/{membres,modifier_membre,dashboard}.html`, `pyproject.toml` (dépendance `tzdata`, nécessaire sur Windows pour `Europe/Paris`), `tests/{test_services_users,test_services_images,test_admin_membres,test_main,test_templating}.py`.
- Tests : 35 ajoutés, 112 verts au total.
- Décisions validées :
  - La liste admin affiche tous les comptes membres y compris désactivés/bloqués (contrairement à RG-12, propre à la liste membre) : l'admin doit pouvoir réactiver un compte.
  - Route `/media/{filename}` dédiée plutôt qu'un montage `StaticFiles` classique, pour rester compatible avec l'isolation du dossier `media/` dans les tests.
  - Deux tests du découpage initial (connexion refusée via `/login`, disparition de la liste des personnes) retirés : ces écrans relèvent de US-01/US-10/US-03, pas encore construits. RG-11 reste couvert par `test_authenticate_refuse_compte_inactif` (déjà existant) et par le test d'invalidation de session de cet incrément.

## 2026-11-08 — Réordonnancement du backlog — US-03 avant US-07
- Fait : US-07 (réinitialiser/débloquer) dépend du mécanisme de blocage RG-05, volontairement non construit en US-04 et initialement prévu pour US-03, placée après US-07 dans le backlog. Décidé avec Lukas d'intervertir l'ordre : US-03 avant US-07.
- Décisions validées : **PO-01** tranché à cette occasion : blocage de 15 minutes. Reporté en RG-05.

## 2026-11-08 — US-03 (incrément unique) — Blocage après 5 échecs
- Fait : logique de blocage ajoutée dans `authenticate()` (`app/services/users.py`) — compteur d'échecs, blocage 15 minutes au 5ᵉ échec consécutif, message RG-06 distinct (« Compte temporairement bloqué… »), remise à zéro à l'expiration du blocage ou sur succès. Aucune nouvelle route : `authenticate()` est déjà appelée par `/admin/login`, donc le blocage s'applique immédiatement à l'admin, et s'appliquera à US-01 sans code supplémentaire.
- Fichiers : `app/services/users.py`, `tests/test_services_users.py`, `tests/test_admin_auth.py`.
- Tests : 7 ajoutés, 119 verts au total.
- Décisions validées :
  - Le critère « déblocage admin → connexion immédiate » (US-07) est démontré au niveau service (remettre `failed_login_count`/`locked_until` à zéro débloque immédiatement) : c'est exactement ce que l'action « Débloquer » de US-07 appellera.

## 2026-11-08 — US-07 (incrément unique) — Réinitialiser un mot de passe / débloquer un compte
- Fait : `reset_password()` et `unlock_member()` dans `app/services/users.py` (RG-05, RG-10) ; routes `POST /admin/membres/{id}/mot-de-passe` et `POST /admin/membres/{id}/debloquer`, ajoutées sur la fiche membre existante (US-06), pas un nouvel écran. Filtre Jinja `est_bloque` (`app/templating.py`) qui vérifie l'expiration de `locked_until`, pas seulement sa présence ; corrige au passage le statut « Bloqué » de la liste admin (US-06), qui ne tenait pas compte de l'expiration.
- Fichiers : `app/services/users.py`, `app/routers/admin.py`, `app/templating.py`, `app/templates/admin/{modifier_membre,membres}.html`, `tests/{test_services_users,test_admin_membres}.py`.
- Tests : 19 ajoutés, 138 verts au total.
- Décisions validées : garde-fou id-admin (`MemberNotFoundError` → 404) appliqué aux deux nouvelles routes, même principe que US-06.

## 2026-11-08 — US-01 (incréments 1 et 2) — Se connecter en tant que membre
- Fait :
  - Incrément 1 : `list_active_members()` dans `app/services/users.py` (RG-03) ; `app/security.py` : `_user_from_session` renommée `user_from_session` (publique, réutilisée par le router) ; router `app/routers/auth.py` (`GET`/`POST /login`), template `login.html`. Branché sur `authenticate()`, déjà partagé avec l'admin (RG-05/RG-06 s'appliquent sans code supplémentaire).
  - Incrément 2 : `GET /login/photo` (fragment HTMX, RG-04) et câblage du `<select>` (`hx-get`/`hx-trigger="change"`/`hx-include="this"`), template `_photo_login.html`.
- Fichiers : `app/services/users.py`, `app/security.py`, `app/main.py`, `app/routers/auth.py`, `app/templates/{login,_photo_login}.html`, `tests/test_login.py`.
- Tests : 12 ajoutés, 150 verts au total.
- Décisions validées :
  - Connexion réussie redirige vers `/` (stub existant) plutôt que d'attendre US-10 : c'est la même route que celle-ci remplira.
  - `hx-include="this"` sur le `<select>` : sans cette restriction, htmx inclut par défaut tout le formulaire englobant dans la requête GET, ce qui aurait mis le mot de passe en clair dans l'URL (et les logs serveur).
  - `GET /login/photo` renvoie le même placeholder vide pour un prénom inconnu et pour un prénom désactivé (jamais les initiales) : aucune fuite au-delà de ce que la liste déroulante révèle déjà, qui liste publiquement tous les prénoms actifs.

## 2026-11-09 — US-02 (incrément unique) — Se déconnecter — Lot 1 terminé
- Fait : `POST /logout` dans `app/routers/auth.py` (RG-07, CSRF, réservé au rôle membre via `current_member` donc refusé à l'admin par RG-09) ; vide la session et redirige vers `/login`. Bouton « Se déconnecter » posé sur le stub `index.html` en attendant l'écran profil réel (US-23 à US-25).
  - Bug de test corrigé au passage : la fixture `login_as` (conftest.py) posait le cookie de session sans domaine explicite. httpx normalise `testserver` en `testserver.local` ; toute réponse serveur posant elle-même un cookie (ex. ajout du jeton CSRF en session) créait donc un **second** cookie `session` de domaine différent, jamais invalidé par la déconnexion — masquant toute vérification d'un état réellement déconnecté. Invisible jusqu'ici car aucun test n'enchaînait requête-après-mutation-de-session puis vérification d'un état déconnecté. Corrigé en précisant `domain="testserver.local"` à la pose du cookie.
- Fichiers : `app/routers/auth.py`, `app/templates/index.html`, `tests/test_login.py`, `tests/conftest.py`.
- Tests : 5 ajoutés, 155 verts au total.
- Décisions validées : aucune nouvelle règle métier ; `POST /logout` réutilise le contrôle d'accès déjà en place (RG-09) sans code spécifique.
- **Lot 1 — Authentification et administration des comptes — entièrement livré** (US-04, US-05, US-06, US-03, US-07, US-01, US-02).

## 2026-11-09 — PO-04, PO-05, PO-06, PO-07 tranchés avant le Lot 2
- Fait : les quatre points ouverts bloquant respectivement US-17, US-16, US-10 et US-15 ont été tranchés avec Lukas avant de démarrer le Lot 2.
- Décisions validées :
  - **PO-06** : le compteur RG-13 compte les cadeaux achetés. Reporté en RG-13.
  - **PO-05** : un cadeau acheté reste modifiable par son auteur ; les autres membres voient alors « modifié le … ». Reporté en RG-21.
  - **PO-04** : un cadeau retiré reste ouvert aux commentaires (lecture et écriture), seule la réservation est bloquée. Reporté en RG-22.
  - **PO-07** : le contenu de l'écran de détail (US-15) est confirmé tel que décrit dans son analyse fonctionnelle.

## 2026-11-09 — US-10 (incréments 1 et 2) — Consulter la liste des personnes
- Fait :
  - Incrément 1 : `app/services/visibility.py` (nouveau — cœur de RG-30), `visible_gift_count(db, viewer, person)` : cadeaux personnels toujours comptés, suggestions comptées seulement si le viewer n'est pas le destinataire, retirés/archivés jamais comptés, achetés toujours comptés (PO-06). Fixture `create_gift` (factory minimale) ajoutée à `tests/conftest.py`.
  - Incrément 2 : `app/routers/people.py` (`GET /`, remplace le stub posé en US-02), template `people.html` : membres actifs triés alphabétiquement, photo/placeholder, compteur, lien vers le formulaire d'ajout (`/cadeaux/nouveau`, US-11) et vers la liste de chaque personne (`/personnes/{id}`, US-13) — ces deux routes n'existent pas encore. `app/templates/index.html` supprimé (plus aucune référence).
- Fichiers : `app/services/visibility.py`, `app/routers/people.py`, `app/main.py`, `app/templates/people.html`, `tests/conftest.py`, `tests/test_visibility.py`, `tests/test_people.py`.
- Tests : 12 ajoutés, 167 verts au total.
- Décisions validées : aucune règle métier nouvelle ; les deux liens de `people.html` pointent vers des routes à construire aux prochaines stories (US-11, US-13).

## 2026-11-09 — US-11 (incrément unique) — Ajouter un cadeau à ma liste
- Fait : `create_gift()` dans `app/services/gifts.py` (RG-14 à RG-18) et `GET/POST /cadeaux/nouveau` dans `app/routers/gifts.py`, template `gifts/nouveau.html`. `create_gift()` ne prend aucun paramètre destinataire : tant que « Suggérer » n'existe pas (US-12), un cadeau créé ici est toujours pour son auteur par construction, ce qui neutralise une requête forgée sans code mort non testé pour la branche suggestion. Réutilise `save_profile_photo`/`delete_profile_photo` d'`app/services/images.py` tels quels (déjà génériques). Erreurs de validation en `ValueError`, cohérent avec `app/services/users.py`.
- Fichiers : `app/services/gifts.py`, `app/routers/gifts.py`, `app/templates/gifts/nouveau.html`, `app/main.py`, `tests/test_services_gifts.py`, `tests/test_gifts.py`.
- Tests : 17 ajoutés, 185 verts au total.
- Décisions validées : redirection après création vers `/` (liste des personnes) en attendant `/personnes/{id}` (US-13).
