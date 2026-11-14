# User stories — Messages privés

Les messages privés sont une messagerie entre membres, **sans lien avec les cadeaux** : la matrice RG-30 ne s'y applique pas. L'admin n'y a aucun accès (RG-46).

Tout passe par `app/services/messages.py`, qui vérifie que le membre est participant de la conversation (RG-47).

---

## US-29 — Écrire à un membre

**En tant que** membre
**Je veux** envoyer un message privé à un autre membre depuis une pop-up
**Afin de** discuter sans quitter la page où je suis

### Analyse fonctionnelle

Une bulle « Messages » flotte en bas à droite de toutes les pages membre (RG-55). Un clic ouvre la pop-up sur la liste de mes conversations : avatar, nom, aperçu du dernier message et ancienneté (« 7 min », « 3 h », « 2 j », « 1 sem. »). Le bouton « Nouveau message » liste les autres membres actifs ; en choisir un ouvre la conversation à deux, unique pour la paire (RG-46). Sur téléphone, la pop-up prend tout l'écran. Elle reste ouverte au même endroit quand on change de page, jusqu'à ce qu'on la ferme avec la croix.

Un message fait 1 à 1 000 caractères (RG-48). Sur ordinateur, Entrée envoie et Maj+Entrée va à la ligne. La conversation affichée se rafraîchit toutes les 5 secondes.

Sans JavaScript, la bulle mène à la même messagerie en pleine page (`/messages`).

### Critères d'acceptation
- Ouvrir la conversation avec Bob, puis Bob avec moi, donne la même conversation.
- On ne peut écrire ni à soi-même, ni à l'admin, ni à un compte désactivé (404).
- Un message vide ou de plus de 1 000 caractères est refusé ; le texte est échappé à l'affichage.
- La liste montre mes conversations de la plus récente à la plus ancienne ; une conversation à deux encore vide n'y figure pas.
- **Un membre qui n'est pas participant ne lit rien** : conversation, fil, message, photo répondent 404, y compris par URL directe.
- L'admin reçoit 403 et n'a ni bulle ni message dans le panel ; un visiteur est renvoyé à la connexion.
- Chaque vue existe en fragment (pop-up) et en pleine page.

---

## US-30 — Être prévenu d'un nouveau message

**En tant que** membre
**Je veux** voir sur la bulle et sur la cloche que j'ai reçu des messages
**Afin de** ne pas les rater

### Analyse fonctionnelle

La bulle affiche le nombre de messages non lus. La cloche compte une notification par conversation non lue, et la page « Notifications » affiche pour chacune une ligne (« Bob t'a envoyé 3 messages », « 2 nouveaux messages dans « Cadeau Mamie » ») qui ouvre la conversation (RG-50). La bulle et la cloche se rafraîchissent toutes les 20 secondes.

### Critères d'acceptation
- Deux messages de la même personne : bulle « 2 », cloche « 1 ».
- Mes propres messages ne comptent pas.
- Ouvrir la page « Notifications » ne marque pas les conversations comme lues.
- Afficher la conversation (ou la garder ouverte pendant qu'un message arrive) la marque lue, et seulement elle.
- Un fil qui n'a pas changé ne renvoie rien au rafraîchissement.

---

## US-31 — Modifier / supprimer mon message

**En tant que** membre
**Je veux** corriger ou retirer un message que j'ai envoyé
**Afin de** rattraper une erreur

### Critères d'acceptation
- Je modifie le texte de mes messages ; ils affichent « (modifié) » (RG-49).
- Je ne peux ni modifier ni supprimer le message d'un autre (403), et aucun lien ne me le propose.
- Un message supprimé disparaît pour tout le monde, sans trace, avec sa photo.
- Après la suppression du dernier message, le suivant est bien compté comme non lu.

---

## US-32 — Savoir si mon message a été vu

### Critères d'acceptation
- « Vu » apparaît sous mon dernier message quand l'autre a affiché la conversation (RG-51).
- Il n'apparaît pas chez celui qui lit, et disparaît dès que l'autre répond.
- Dans un groupe : « Vu par Bob », avec les prénoms de ceux qui ont lu.

---

## US-33 — Voir si quelqu'un est en ligne

### Critères d'acceptation
- L'en-tête d'une conversation à deux affiche « En ligne » (activité depuis moins de 2 minutes) ou « En ligne il y a 7 min » / « 3 h » / « 2 j » / « 2 sem. » (RG-52).
- Rien n'est affiché pour quelqu'un qui ne s'est jamais connecté ; « Compte désactivé » pour un compte désactivé.
- Utiliser le site met à jour ma présence, au plus une fois par minute.

---

## US-34 — Envoyer une photo

### Critères d'acceptation
- Un message peut contenir une photo seule, ou une photo avec du texte (RG-48).
- Mêmes limites que les images de cadeaux : JPEG, PNG ou WebP, 5 Mo ; un fichier invalide est refusé.
- La photo est stockée hors du dossier public et **servie aux seuls participants** (404 pour les autres, RG-47).
- Supprimer le message supprime le fichier.

---

## US-35 — Discuter à plusieurs dans un groupe

**En tant que** membre
**Je veux** créer une conversation à plusieurs avec un nom
**Afin d'** organiser un cadeau commun

### Critères d'acceptation
- Un groupe demande un nom (1 à 60 caractères) et au moins un autre membre actif (RG-53).
- Tous les participants voient le groupe et ses messages, avec le prénom de l'auteur.
- Tout participant peut ajouter quelqu'un, qui voit tout l'historique sans rien de non lu.
- Seul le créateur renomme le groupe et retire un participant (403 pour les autres).
- Un participant retiré ou parti n'a plus aucun accès (404).
- Si le créateur part, le plus ancien participant devient créateur ; le groupe disparaît avec son dernier participant.
- Les réglages de groupe n'existent pas pour une conversation à deux (404).

---

## Comptes désactivés et supprimés (RG-54)

- Compte désactivé : la conversation à deux reste lisible, l'envoi est refusé, il n'est plus proposé dans « Nouveau message ». Les groupes continuent.
- Compte supprimé (US-26) : ses messages et ses conversations à deux disparaissent avec leurs photos ; il est retiré des groupes, dont le plus ancien participant devient créateur si besoin.
