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

## 2026-11-14 — US-29 à US-35 — messages privés, livrés en une fois
- Fait : à la demande de Lukas (« en one shot »), en dérogation ponctuelle à la méthode par petits incréments. Conversations à deux et groupes, pop-up en bas à droite (bulle « Messages », plein écran sur téléphone), non-lus sur la bulle et dans la cloche, modification et suppression de ses messages, « Vu », « En ligne », photos privées. La suppression d'un compte emporte ses messages.
- Fichiers : `app/models.py`, `migrations/versions/0003_messages_prives.py`, `app/services/messages.py` (nouveau), `app/routers/messages.py` (nouveau), `app/static/js/messages.js` (nouveau), templates `messages/` (nouveau), `_bell_count.html` (nouveau), `base.html`, `macros.html`, `notifications.html`, `app/web.py`, `app/security.py`, `app/config.py`, `app/main.py`, `app/services/images.py`, `app/services/admin.py`, `app/routers/notifications.py`, CSS `components.css`, `Dockerfile`, `.env.example`, `.gitignore`, `tests/test_messages.py` (nouveau), `tests/conftest.py`.
- Tests : 29 ajoutés, total 153 verts. Migration vérifiée sur une base vide (`upgrade`, `alembic check`, aller-retour `downgrade` / `upgrade`). Pop-up vérifiée dans Chrome sans interface sur une base d'essai : 41 vérifications (ouverture, envoi avec Entrée, réception d'un message en direct, fil calé en bas, réouverture après changement de page, cloche mise à jour sans recharger, modification, suppression, groupe, réglages, téléphone 375 px, mode sombre, pleine page), hors suite pytest.
- Décisions validées par Lukas : groupes dès la première version ; HTMX + petit JavaScript maison (`messages.js`, deuxième exception) ; une ligne par conversation dans la cloche ; modifier / supprimer, « Vu », photos et « En ligne » inclus ; admin sans aucun accès ; pas de temps réel (5 s et 20 s) ; plein écran sur téléphone ; règles des groupes (RG-53) ; suppression sans trace ; photos servies aux seuls participants ; compte désactivé lisible mais fermé ; messages conservés à la clôture ; présence visible par tous. Nouvelles règles RG-46 à RG-55, RG-41 et RG-45 complétées.
- Décisions appliquées par défaut, à confirmer : PO-15 à PO-19.
- Non fait : envoi réel d'une photo depuis le navigateur et rendu sur un vrai téléphone non vérifiés à la main (l'envoi de photo est couvert par pytest). `Dockerfile` toujours non testé. Les photos privées demandent le même volume persistant que les images (`NOEL_PRIVATE_MEDIA_DIR`).

## 2026-11-14 — US-34 — aperçu de la photo jointe
- Fait : quand on choisit une photo dans un message privé, un bandeau au-dessus de la zone de saisie montre la miniature, le nom du fichier et une croix pour la retirer. Il disparaît après l'envoi.
- Fichiers : `app/templates/messages/_conversation.html`, `app/static/js/messages.js`, CSS `components.css`.
- Tests : aucun ajouté côté serveur, total 153 verts. Vérifié dans Chrome sans interface avec une vraie image (6 vérifications : aperçu, retrait, envoi, téléphone 375 px), hors suite pytest.
- Décisions validées : demande de Lukas.

## 2026-11-14 — US-36 — choix du thème dans le profil
- Fait : section « Apparence » du profil avec sept thèmes (Automatique, Clair, Sombre, Neige, Canneberge, Pain d'épices, Minuit), enregistrés sur le compte et appliqués à toutes les pages membre. Les tokens de couleur sont réorganisés par thème ; le rendu par défaut ne change pas.
- Fichiers : `app/models.py`, `migrations/versions/0004_theme.py`, `app/services/users.py`, `app/routers/profile.py`, templates `base.html` et `profile.html`, CSS `tokens.css` et `components.css`, `tests/test_profile.py`, skill `design-site`.
- Tests : 5 ajoutés, total 158 verts. Migration vérifiée sur une base vide (aller-retour). Contrastes des quatre nouvelles palettes calculés (19 couples texte / fond chacune, tous ≥ 4,5:1). Vérifié dans Chrome sans interface : 13 vérifications (application au clic pour chaque thème, thème clair forcé sur appareil sombre, pop-up des messages, téléphone 375 px), hors suite pytest. Ce passage a révélé un défaut corrigé avant livraison : la page ne se rechargeait pas après le clic.
- Décisions validées : demande de Lukas, qui a laissé le choix des thèmes libre (nouvelle règle RG-56).
- À savoir : dans le thème Sombre d'origine, trois couples de couleurs sont sous 4,5:1 sur le fond `--c-surface-2` (vert et rouge d'accent, 3,9 à 4,4). Ils existaient avant ce changement et n'ont pas été modifiés.

## 2026-11-18 — US-37 — notification d'un nouveau cadeau
- Fait : à la création d'un cadeau, chaque membre actif qui peut le voir est notifié, sauf l'auteur et, pour une suggestion, son destinataire. Les notifications sont listées avec les mentions, mènent à la fiche du cadeau et sont marquées lues à son ouverture. La table `notifications` reçoit `gift_id` (migration `0005`), `comment_id` devient facultatif.
- Fichiers : `app/models.py`, `migrations/versions/0005_notifications_cadeaux.py`, `app/services/notifications.py`, `app/services/gifts.py`, `app/services/visibility.py`, `app/routers/gifts.py`, `app/routers/comments.py`, `app/templates/notifications.html`, `tests/test_notifications.py`, `tests/test_visibility.py`.
- Tests : 9 ajoutés, total 167 verts. Migration vérifiée sur une base vide (aller-retour `downgrade` / `upgrade`).
- Décisions validées par Lukas : tous les membres sauf l'auteur (et le destinataire d'une suggestion), une notification par cadeau, lue via la page ou la fiche, table existante étendue. Nouvelle règle RG-57.

## 2026-11-18 — US-38 — menu des applications
- Fait : le site devient « La Famille ». Après la connexion, on arrive sur un menu (`/`) avec une tuile par application ; la liste des personnes passe sur `/noel`. Le logo ramène au menu, l'en-tête (cloche, messages, profil, thème) est commun.
- Fichiers : `app/routers/people.py`, templates `menu.html` (nouveau), `people.html`, `base.html`, `login.html`, `gift_list.html`, `gift_form.html`, `profile.html`, `macros.html` et titres de toutes les pages, CSS `components.css` (composant `app-tile`), `app/main.py`, `app/cli.py`, `tests/test_menu.py` (nouveau), `tests/test_admin.py`, `tests/test_auth.py`, `tests/test_profile.py`, `tests/test_visibility.py`.
- Tests : 5 ajoutés, total 172 verts.
- Décisions validées par Lukas : menu sur `/`, Noël sur `/noel`, en-tête commun, nom « La Famille ». Nouvelle règle RG-58.

## 2026-11-18 — US-39 à US-41 — listes de courses
- Fait : listes de courses nommées et partagées par tous les membres, articles avec quantité facultative, cocher / décocher (« Pris par … »), suppression d'un article, « Retirer les articles cochés ». Actions en HTMX sans rechargement, avec repli sans JavaScript. Les listes d'un compte supprimé restent.
- Fichiers : `app/models.py`, `migrations/versions/0006_listes_de_courses.py`, `app/services/shopping.py` (nouveau), `app/routers/shopping.py` (nouveau), `app/services/admin.py`, `app/main.py`, `app/routers/people.py`, templates `shopping/` (nouveau), `macros.html` (icônes panier, coche, corbeille), CSS `components.css`, `tests/test_shopping.py` (nouveau).
- Tests : 25 ajoutés, total 197 verts. Migration vérifiée sur une base vide (aller-retour, `alembic check`).
- Décisions validées par Lukas : plusieurs listes partagées, article = nom + quantité, cocher, pas de notification. Nouvelles règles RG-59 à RG-61, RG-41 complétée.
- Décisions appliquées par défaut, à confirmer : PO-20 à PO-22.
- Non fait : rendu des écrans non vérifié dans un navigateur (375 px, mode sombre). Au passage, `uv` a été installé sur le poste (winget).
