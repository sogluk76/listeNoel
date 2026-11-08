# User stories — Commentaires

---

## US-20 — Consulter les commentaires d'un cadeau

**En tant que** membre connecté
**Je veux** lire la discussion sur un cadeau d'un autre membre
**Afin de** me coordonner avec la famille

### Analyse fonctionnelle

L'icône commentaire d'un cadeau, avec son badge, ouvre le fil de discussion de ce cadeau (RG-31). Chaque message affiche la photo ou le placeholder de son auteur, son prénom, la date et l'heure, et le texte. Mes messages sont à droite, ceux des autres à gauche, par ordre chronologique (RG-32). Le fil se met à jour automatiquement toutes les 20 secondes (RG-34) sans perdre ce que je suis en train d'écrire. Le destinataire du cadeau n'a **jamais** accès à ce fil (RG-30).

### Critères d'acceptation
- Le destinataire qui ouvre l'URL du fil reçoit une erreur 403, y compris sur l'URL de rafraîchissement HTMX.
- Les messages sont triés du plus ancien au plus récent.
- Un message écrit par un autre membre apparaît en 20 secondes maximum sans recharger la page.
- Le rafraîchissement n'efface pas le texte en cours de saisie.
- Un auteur sans photo est affiché avec un placeholder.
- Le contenu des messages est échappé (pas d'injection HTML).

---

## US-21 — Écrire un commentaire

**En tant que** membre connecté
**Je veux** écrire un message sur un cadeau
**Afin de** discuter de ce cadeau avec les autres

### Analyse fonctionnelle

En bas du fil, un champ de saisie et un bouton d'envoi permettent d'ajouter un message. Les messages vides ou composés uniquement d'espaces sont refusés, et la longueur est limitée à 1 000 caractères (RG-33). Après envoi, le message apparaît immédiatement dans le fil et le champ est vidé.

| Champ | Saisie | Obligatoire |
|---|---|---|
| Message | Texte, 1 à 1 000 caractères, emojis acceptés | Oui |

### Critères d'acceptation
- Un message vide ou fait d'espaces est refusé.
- Un message de plus de 1 000 caractères est refusé.
- Les emojis sont enregistrés et affichés correctement.
- Le destinataire ne peut pas écrire sur le fil de son propre cadeau (403).
- Le badge du cadeau est incrémenté.

---

## US-22 — Modifier / supprimer mon commentaire

**En tant qu'** auteur d'un commentaire
**Je veux** modifier ou supprimer mon message
**Afin de** corriger une erreur ou retirer un message

### Analyse fonctionnelle

Sur mes propres messages uniquement, une action « Modifier » rend le texte éditable directement dans le fil, et une action « Supprimer » le supprime après confirmation (RG-35). Un message modifié affiche la mention « (modifié) ». Les mêmes règles de validation qu'à la création s'appliquent.

| Champ | Saisie | Obligatoire |
|---|---|---|
| Message | Texte, 1 à 1 000 caractères | Oui |

### Critères d'acceptation
- Les actions ne sont visibles que sur mes messages.
- Modifier ou supprimer le message d'un autre renvoie une erreur 403.
- Un message modifié affiche « (modifié) ».
- Un message supprimé disparaît du fil et du badge.
