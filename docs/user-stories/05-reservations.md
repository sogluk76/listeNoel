# User stories — Réservations et achat

---

## US-18 — Réserver / annuler une réservation

**En tant que** membre connecté
**Je veux** indiquer que je m'occupe d'un cadeau
**Afin que** les autres sachent qu'il est pris en charge et puissent se joindre à moi

### Analyse fonctionnelle

Sur le détail ou la liste d'un cadeau dont je ne suis pas le destinataire, un bouton « Je m'en occupe » ajoute une réservation à mon nom (RG-26). Plusieurs membres peuvent réserver le même cadeau : la mention « Réservé par Franck, Florence » est visible par tous sauf le destinataire. Tant que le cadeau n'est pas acheté, je peux annuler **ma** réservation (RG-27). Le bouton change d'état sans recharger la page (HTMX).

### Critères d'acceptation
- Le destinataire ne voit jamais le bouton ni les réservants, et une requête forgée de sa part est refusée (403).
- Deux membres différents peuvent réserver le même cadeau.
- Un membre ne peut pas réserver deux fois le même cadeau.
- Je ne peux annuler que ma propre réservation.
- Réserver ou annuler est impossible sur un cadeau acheté, retiré ou archivé.

---

## US-19 — Marquer acheté / annuler l'achat

**En tant que** réservant d'un cadeau
**Je veux** indiquer que le cadeau est acheté
**Afin d'** éviter qu'il soit offert en double

### Analyse fonctionnelle

Un réservant voit le bouton « Marquer comme acheté ». Une fois cliqué, le cadeau passe en statut acheté (RG-28) : « Acheté par <moi> » s'affiche, plus personne ne peut réserver ni annuler une réservation, mais le cadeau reste visible et les commentaires restent ouverts. Seul le membre qui l'a marqué acheté voit « Annuler l'achat » : le cadeau repasse alors en réservé, avec ses réservants (RG-29).

### Critères d'acceptation
- Seul un réservant peut marquer acheté ; un non-réservant reçoit une erreur 403.
- Après l'achat, aucune réservation ne peut être ajoutée ni annulée.
- Les commentaires restent possibles sur un cadeau acheté.
- Seul l'acheteur peut annuler l'achat, et le cadeau repasse en « réservé ».
- Le destinataire ne voit aucune trace de l'achat.
