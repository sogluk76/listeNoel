# 06 — Points ouverts

Pour livrer le site en une fois, les propositions ci-dessous ont été **appliquées par défaut**. Elles restent à confirmer par Lukas : chaque changement d'avis se fait en modifiant la règle dans `02-regles-metier.md`, le code et les tests.

Légende : 🟡 appliqué par défaut, à confirmer · ☐ encore ouvert · ☑ confirmé

| # | Sujet | Choix appliqué | Où c'est codé |
|---|---|---|---|
| 🟡 PO-01 | Durée du blocage après 5 échecs | 15 minutes | `settings.lock_minutes` |
| ☐ PO-02 | Choix du PaaS (Render, Railway, Fly.io) et coût du volume persistant | À comparer au lot 6 | — |
| 🟡 PO-03 | Clôture de l'année : réservations des cadeaux non achetés | Elles sont conservées | `services/admin.py` |
| 🟡 PO-04 | Cadeau retiré : commentaires encore possibles ? | Oui, mais plus de réservation ni d'achat | `services/reservations.py` |
| 🟡 PO-05 | Un cadeau acheté peut-il être modifié par son auteur ? | Oui (l'auteur ne sait pas qu'il est acheté) | `services/gifts.py` |
| 🟡 PO-06 | Compteur RG-13 : exclure les cadeaux achetés ? | Non, ils sont comptés | `services/visibility.py` |
| 🟡 PO-07 | Contenu de l'écran de détail (non vu dans Power Apps) | Image, nom, prix, lien, destinataire, suggéré par, date, boutons | `templates/gift_detail.html` |
| ☐ PO-08 | Sauvegarde : fréquence et destination | À définir au lot 6 | — |
| 🟡 PO-09 | Règles de mot de passe | 8 caractères minimum, sans autre contrainte | `settings.password_min_length` |

## Choix faits pendant le développement, à valider aussi

| # | Sujet | Choix appliqué |
|---|---|---|
| 🟡 PO-10 | Modification d'un commentaire | Sur une petite page dédiée, et non directement dans le fil, pour que le rafraîchissement automatique n'efface pas la saisie |
| 🟡 PO-11 | Réservation / achat | Rechargement de la page de détail après chaque action (pas encore en HTMX) |
| 🟡 PO-12 | Suppression d'un cadeau par l'admin | La confirmation se fait en dépliant « Supprimer » puis « Oui, supprimer » |
| 🟡 PO-13 | « Mes réservations » : total par destinataire | Les cadeaux retirés ne sont pas comptés dans le total |
| 🟡 PO-14 | Direction artistique | Version sobre de la palette du skill `design-site` (crème, vert sapin, touches canneberge et or), sans décor festif |
