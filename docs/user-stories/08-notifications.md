# User stories — Notifications

Les notifications s'affichent **sur le site uniquement** (cloche dans l'en-tête). Il n'y a ni mail ni notification sur le téléphone.

---

## US-27 — Mentionner quelqu'un dans un commentaire

**En tant que** membre
**Je veux** écrire `@Prénom` dans un commentaire
**Afin d'** attirer l'attention de cette personne sur la discussion

### Analyse fonctionnelle

Dans le fil d'un cadeau, un `@` suivi du prénom d'un membre est une mention (RG-42). Le prénom est reconnu sans tenir compte des majuscules ni des accents, et s'affiche en surbrillance dans le message. Chaque membre mentionné reçoit une notification, sauf l'auteur du message lui-même. Le destinataire du cadeau ne peut pas être mentionné : son prénom reste du texte simple et il ne reçoit rien (RG-43).

Si le message est modifié, les notifications suivent : une mention ajoutée notifie, une mention retirée retire la notification. Supprimer le message supprime ses notifications (RG-44).

### Critères d'acceptation
- `@bob` et `@BOB` mentionnent Bob ; `@chloe` mentionne Chloé.
- `@Bobby` ne mentionne pas Bob ; une adresse mail (`truc@bob.fr`) ne mentionne personne.
- Mentionner trois fois la même personne dans un message ne crée qu'une notification.
- On ne reçoit pas de notification pour s'être mentionné soi-même.
- Un membre désactivé n'est pas notifié.
- **Le destinataire du cadeau n'est jamais notifié** et rien ne change sur ses écrans.
- La mention est mise en valeur dans le fil ; le reste du message reste échappé.
- Modifier ou supprimer le message met les notifications à jour.

### Aide à la saisie

Dans la zone de saisie d'un commentaire (nouveau message ou modification), taper `@` ouvre une liste des prénoms que l'on peut mentionner. Elle se filtre au fil de la frappe, sans tenir compte des majuscules ni des accents. On choisit avec un clic, ou au clavier (flèches, puis Entrée ou Tab ; Échap referme). La liste ne propose ni moi-même, ni le destinataire du cadeau, ni un compte désactivé.

Dans le fil, le prénom de l'auteur d'un message est cliquable : il insère `@Prénom` dans la zone de saisie. Mon propre prénom et celui d'un compte désactivé ne le sont pas.

C'est le seul JavaScript maison du site (`app/static/js/mentions.js`), validé par Lukas. Sans lui, taper `@Prénom` à la main fonctionne toujours : la reconnaissance se fait côté serveur.

- La liste proposée exclut le viewer, le destinataire du cadeau et les comptes désactivés.
- Choisir un prénom remplace ce qui a été tapé après le `@` par `@Prénom` suivi d'une espace.
- Le clic sur un auteur fonctionne encore après le rafraîchissement automatique du fil.

---

## US-28 — Voir mes notifications

**En tant que** membre
**Je veux** voir une cloche avec le nombre de mentions que je n'ai pas encore lues
**Afin de** ne pas rater une discussion qui me concerne

### Analyse fonctionnelle

L'en-tête de toutes les pages membre affiche une cloche. Une pastille indique le nombre de notifications non lues ; elle est absente s'il n'y en a pas. La cloche ouvre la page « Notifications », qui liste les mentions de la plus récente à la plus ancienne : qui m'a mentionné, sur quel cadeau et pour qui, un extrait du message et la date. Chaque ligne mène au message dans le fil. Ouvrir la page marque toutes les notifications comme lues (RG-45) ; celles qui étaient nouvelles portent encore l'étiquette « Nouveau » à cet affichage. Ouvrir directement les commentaires d'un cadeau marque aussi comme lues les notifications de ce fil.

Le compteur est calculé au chargement de chaque page (pas de rafraîchissement automatique).

### Critères d'acceptation
- La pastille affiche le nombre de notifications non lues, sur toutes les pages membre.
- Ouvrir la page remet le compteur à zéro ; les notifications restent listées.
- Ouvrir les commentaires d'un cadeau retire du compteur les notifications de ce fil, pas celles des autres.
- Le rafraîchissement automatique du fil et la page de détail du cadeau ne marquent rien comme lu.
- Chaque ligne mène au bon message du fil.
- Un membre ne voit que ses propres notifications.
- Une notification dont le cadeau n'est plus visible (archivé, liste d'un compte désactivé) n'apparaît plus et n'est plus comptée.
- L'admin n'a ni cloche ni accès à la page (403) ; un visiteur non connecté est renvoyé à la connexion.
