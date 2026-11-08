# 01 — Vision du projet

## Objectif

Remplacer l'application Power Apps « Liste Noel » par un site web accessible depuis n'importe quel navigateur, sur mobile en priorité, sans licence Microsoft.

Le design est entièrement refait : ce document et les suivants ne décrivent que le **fonctionnel**.

## Utilisateurs

| Profil | Description | Accès |
|---|---|---|
| **Membre** | Une personne de la famille (moins de 15 personnes) | Toute l'application, sauf le panel admin |
| **Admin** | Un compte technique distinct, qui n'est pas un membre de la famille | **Uniquement** le panel admin (`/admin`) |

L'admin n'a pas de liste de cadeaux, n'apparaît dans aucune liste de personnes et ne voit ni les commentaires ni les réservations.

## Principe central : la surprise

Un membre ne doit **jamais** pouvoir découvrir, sur sa propre liste :
- les cadeaux que d'autres lui ont suggérés,
- les commentaires,
- les réservations et achats.

Toute fonctionnalité est conçue et testée en priorité contre ce principe.

## Périmètre

### Repris de l'application Power Apps
- Connexion par choix du prénom + mot de passe, avec photo de profil
- Liste des personnes, avec le nombre de cadeaux de chacune
- Ajout d'un cadeau pour soi ou suggestion pour quelqu'un d'autre
- Liste de cadeaux d'une personne : recherche, tri, détail
- Commentaires par cadeau

### Nouveautés
- Réservation « je m'en occupe » (plusieurs personnes possibles) et statut « acheté »
- Écran profil : photo, mot de passe, déconnexion, mes réservations
- Panel admin : comptes, mots de passe, modération des cadeaux, clôture de l'année
- Suppression « douce » d'un cadeau déjà réservé ou acheté
- Rafraîchissement automatique des commentaires
- Photo de remplacement (placeholder) quand un membre n'a pas de photo

### Hors périmètre
- Reprise des données Power Apps : les comptes seront recréés à la main par l'admin, les listes repartent de zéro
- Notifications (mail, push)
- Plusieurs familles ou groupes séparés
- Plusieurs événements (anniversaires…) : uniquement Noël, avec archivage annuel
