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

## 2026-11-10 — Lots 0 à 5 — livraison complète en une fois
- Fait : tout le site, à la demande de Lukas (« en one shot »), en dérogation ponctuelle à la méthode par petits incréments. Socle, authentification, panel admin, listes de cadeaux, suggestions, réservations, achat, commentaires, profil, clôture de l'année, design.
- Fichiers : `app/` (modèles, services, routers, templates, CSS), `migrations/`, `tests/`, `Dockerfile`, `.env.example`.
- Tests : 100 ajoutés, 100 verts. La matrice de confidentialité RG-30 est couverte par `tests/test_visibility.py`. Parcours vérifié à la main dans un vrai navigateur (connexion, recherche, tri, interrupteur « Suggérer », commentaires HTMX, admin, mobile et mode sombre).
- Décisions appliquées par défaut, à confirmer : PO-01, PO-03 à PO-07, PO-09 à PO-14 (cf. `06-points-ouverts.md`).
- Non fait : mise en production (lot 6). Le `Dockerfile` n'a pas été testé.

## 2026-11-10 — US-26 (incrément 1) — supprimer un compte membre
- Fait : suppression définitive d'un compte depuis sa fiche admin, avec toute sa trace (liste, suggestions, réservations, commentaires, images). Un cadeau qu'il avait marqué « acheté » redevient réservé ou disponible.
- Fichiers : `app/services/admin.py` (`delete_member`), `app/routers/admin.py`, `app/templates/admin/member_edit.html`, `tests/test_admin.py`.
- Tests : 3 ajoutés, total 103 verts.
- Décisions validées : « tout supprimer » plutôt que « seulement si le compte est vide » ou « garder ce qu'il a fait pour les autres » (nouvelle règle RG-41).

## 2026-11-10 — En-tête — retrait du raccourci « + »
- Fait : le bouton « + » de l'en-tête est retiré, à la demande de Lukas (le bouton « Ajouter un cadeau » des pages suffit).
- Fichiers : `app/templates/base.html`.
- Tests : aucun ajouté, total 103 verts.

## 2026-11-10 — US-27 (incrément 1) et US-28 — mentions et notifications
- Fait : table `notifications` et migration `0002`, détection des `@Prénom` à l'envoi et à la modification d'un commentaire, mise en valeur des mentions dans le fil, cloche avec compteur dans l'en-tête, page « Notifications » qui marque tout comme lu à l'ouverture. La suppression d'un compte emporte aussi ses notifications.
- Fichiers : `app/models.py`, `migrations/versions/0002_notifications.py`, `app/services/notifications.py` (nouveau), `app/services/visibility.py`, `app/services/comments.py`, `app/services/admin.py`, `app/routers/notifications.py` (nouveau), `app/routers/comments.py`, `app/web.py`, `app/main.py`, templates `base.html`, `_comment_thread.html`, `notifications.html` (nouveau), `macros.html`, CSS `base.css` et `components.css`, `tests/test_notifications.py` (nouveau), `tests/test_visibility.py`, `tests/test_admin.py`.
- Tests : 15 ajoutés, total 118 verts. Migration vérifiée sur une base vide (`alembic upgrade`, `alembic check`, aller-retour `downgrade` / `upgrade`).
- Décisions validées : pas de notification pour le destinataire du cadeau, le commentaire restant accepté (RG-43) ; lecture à l'ouverture de la page cloche (RG-45) ; autocomplétion et clic sur un prénom acceptés par Lukas malgré la règle « pas de JavaScript maison », à faire à l'incrément 2.
- Non fait : autocomplétion sur `@`, clic sur un prénom pour l'insérer, rafraîchissement automatique du compteur. Rendu non vérifié à l'écran.

## 2026-11-10 — US-27 (incrément 2) — aide à la saisie des mentions
- Fait : liste de prénoms quand on tape `@` dans un commentaire (nouveau message et modification), et clic sur le prénom d'un auteur du fil pour insérer `@Prénom`.
- Fichiers : `app/static/js/mentions.js` (nouveau), `app/routers/comments.py`, templates `base.html`, `comments.html`, `comment_edit.html`, `_comment_thread.html`, CSS `components.css`, `tests/test_notifications.py`.
- Tests : 4 ajoutés côté serveur, total 122 verts. Le script a été vérifié à part : 14 assertions sur sa logique avec Node, et 20 vérifications de comportement dans Chrome sans interface (frappe, clavier, clic, rechargement du fil). Ces essais ne sont pas dans la suite pytest.
- Décisions validées : JavaScript maison accepté par Lukas pour cette fonction.
- Non fait : rendu non vérifié à l'écran sur le vrai site ni sur téléphone.

## 2026-11-10 — Commentaires — Entrée pour envoyer, notifications lues à l'ouverture du fil
- Fait : sur ordinateur, Entrée envoie le message et Maj+Entrée va à la ligne (inchangé sur téléphone et sur la page de modification). Ouvrir les commentaires d'un cadeau marque comme lues les notifications de ce fil.
- Fichiers : `app/static/js/mentions.js`, `app/templates/comments.html`, `app/routers/comments.py`, `tests/test_notifications.py`.
- Tests : 2 ajoutés, total 124 verts. Entrée / Maj+Entrée vérifiés dans Chrome sans interface (7 vérifications, dont la cohabitation avec la liste de mentions), hors suite pytest.
- Décisions validées : demandes de Lukas ; règles RG-33 et RG-45 précisées.
- Non fait : comportement sur téléphone non vérifié.
