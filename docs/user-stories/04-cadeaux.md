# User stories — Cadeaux

---

## US-11 — Ajouter un cadeau à ma liste

**En tant que** membre connecté
**Je veux** ajouter un cadeau à ma propre liste
**Afin que** les autres sachent ce qui me ferait plaisir

### Analyse fonctionnelle

Le formulaire s'ouvre depuis le bouton « + » de la liste des personnes. Par défaut, l'interrupteur « Suggérer pour quelqu'un d'autre » est sur Non et le champ « Pour qui ? » affiche mon prénom sans pouvoir être modifié (RG-18). Je saisis au minimum le nom du cadeau, et si je veux un prix, un lien et une image (RG-14 à RG-17). La validation enregistre le cadeau avec moi comme auteur et destinataire, puis m'amène sur ma liste. L'annulation revient à l'écran précédent sans rien enregistrer.

| Champ | Saisie | Obligatoire |
|---|---|---|
| Cadeau | Texte, 1 à 150 caractères | Oui |
| Suggérer pour quelqu'un d'autre | Interrupteur Oui/Non (Non par défaut) | Oui |
| Prix | Montant en euros (≥ 0, 2 décimales) | Non |
| Lien | URL http(s) | Non |
| Image | Fichier image (JPEG, PNG, WebP, 5 Mo max) | Non |
| Pour qui ? | Mon prénom, non modifiable | Oui |

### Critères d'acceptation
- Un cadeau avec seulement un nom est accepté.
- Un nom vide ou composé d'espaces est refusé.
- Un prix négatif, avec plus de 2 décimales ou non numérique est refusé. La virgule et le point sont acceptés comme séparateur décimal.
- Un lien sans `http://` ou `https://` est refusé.
- Le cadeau créé a l'auteur = le destinataire = moi.
- Même en forgeant la requête, un destinataire différent de moi est ignoré ou refusé quand « Suggérer » est sur Non.

---

## US-12 — Suggérer un cadeau pour quelqu'un

**En tant que** membre connecté
**Je veux** suggérer une idée de cadeau pour un autre membre
**Afin de** partager une idée avec les autres sans que la personne concernée le sache

### Analyse fonctionnelle

Dans le même formulaire que US-11, je passe l'interrupteur « Suggérer pour quelqu'un d'autre » sur Oui. Le champ « Pour qui ? » devient une liste des **autres** membres actifs, sans moi (RG-19), et une mention « Idée de : <mon prénom> » apparaît. Une fois enregistrée, la suggestion apparaît dans la liste du destinataire pour tous les membres **sauf lui** (RG-20, RG-30), avec la mention « Suggéré par <mon prénom> ».

| Champ | Saisie | Obligatoire |
|---|---|---|
| Cadeau | Texte, 1 à 150 caractères | Oui |
| Suggérer pour quelqu'un d'autre | Interrupteur sur Oui | Oui |
| Prix | Montant en euros | Non |
| Lien | URL http(s) | Non |
| Image | Fichier image | Non |
| Pour qui ? | Liste des autres membres actifs | Oui |
| Idée de | Mon prénom, affiché en lecture seule | — |

### Critères d'acceptation
- La liste « Pour qui ? » ne contient ni moi, ni l'admin, ni les comptes désactivés.
- La suggestion est enregistrée avec l'auteur = moi et le destinataire = la personne choisie.
- Le destinataire ne voit la suggestion ni dans sa liste, ni dans son compteur, ni via l'URL directe du cadeau (403 ou 404).
- Les autres membres voient la suggestion avec « Suggéré par <moi> ».
- Si on bascule l'interrupteur de Oui à Non, « Pour qui ? » revient à mon prénom.

---

## US-13 — Consulter la liste de cadeaux d'une personne

**En tant que** membre connecté
**Je veux** voir la liste de cadeaux d'une personne
**Afin de** savoir ce qui lui ferait plaisir

### Analyse fonctionnelle

En cliquant sur une personne depuis la liste des personnes, j'arrive sur sa liste. Le titre affiche son prénom. Chaque cadeau est présenté avec son image (si elle existe), son nom et son prix, et donne accès au détail (US-15).

Ce que j'y vois dépend de la matrice de confidentialité (RG-30) :
- **sur ma propre liste**, je ne vois que mes cadeaux personnels, sans icône commentaire, sans statut, sans suggestion ;
- **sur la liste d'un autre**, je vois ses cadeaux personnels et les suggestions faites pour lui (« Suggéré par X »), le statut (disponible / réservé / acheté / retiré) et l'icône commentaire avec le nombre de messages.

L'écran propose aussi la recherche et le tri (US-14) et un bouton retour vers la liste des personnes.

### Critères d'acceptation
- Pour Alice sur sa propre liste : aucune suggestion, aucune icône commentaire, aucun statut, aucun nom de réservant.
- Pour Alice sur la liste de Bob : cadeaux personnels de Bob + suggestions pour Bob, avec statut, réservants et badge de commentaires.
- Le HTML renvoyé à Alice sur sa liste ne contient aucune donnée cachée (pas de commentaire ni de réservation dans le code source).
- Les cadeaux archivés n'apparaissent jamais.
- Un cadeau retiré apparaît chez les autres marqué « Retiré par X », jamais chez son auteur.
- Une personne inexistante ou désactivée renvoie une erreur 404.

---

## US-14 — Rechercher et trier les cadeaux

**En tant que** membre connecté
**Je veux** rechercher un cadeau par son nom et trier la liste
**Afin de** m'y retrouver dans une longue liste

### Analyse fonctionnelle

Une barre de recherche filtre la liste en direct (HTMX, avec un délai court après la frappe) sur le nom du cadeau, sans tenir compte de la casse ni des accents (RG-24). Un sélecteur permet de trier par nom, par prix ou par statut, en ordre croissant ou décroissant (RG-25). Le tri par statut n'est pas proposé sur ma propre liste. Les cadeaux sans prix sont placés en fin de liste quand on trie par prix. Le filtre et le tri s'appliquent après la règle de visibilité : ils ne peuvent jamais faire apparaître un cadeau caché.

| Champ | Saisie | Obligatoire |
|---|---|---|
| Recherche | Texte libre | Non |
| Tri | Nom / Prix / Statut | Non (nom par défaut) |
| Sens | Croissant / Décroissant | Non (croissant par défaut) |

### Critères d'acceptation
- « velo » trouve « Vélo électrique ».
- Le tri par prix croissant met les cadeaux sans prix à la fin.
- Le tri par statut est absent de ma propre liste, et un paramètre `tri=statut` forgé y est ignoré.
- Une recherche ne fait jamais apparaître de suggestion sur ma propre liste.

---

## US-15 — Consulter le détail d'un cadeau

**En tant que** membre connecté
**Je veux** voir le détail d'un cadeau
**Afin d'** accéder à son lien et à toutes ses informations

### Analyse fonctionnelle

Le détail affiche l'image en grand, le nom, le prix, le lien cliquable (nouvel onglet) et la date d'ajout. Pour les autres que le destinataire, il affiche aussi « Suggéré par X » si c'est une suggestion, le statut, la liste des réservants et les boutons de réservation et d'achat (US-18, US-19), ainsi qu'un accès aux commentaires (US-20). Les boutons Modifier et Supprimer ne sont visibles que pour l'auteur (RG-21). Le contenu exact de l'écran Power Apps reste à confirmer (PO-07).

### Critères d'acceptation
- Le lien s'ouvre dans un nouvel onglet avec `rel="noopener noreferrer"`.
- Modifier/Supprimer ne sont visibles que pour l'auteur.
- Le destinataire qui ouvre le détail de son propre cadeau ne voit ni statut, ni réservants, ni accès aux commentaires.
- Le destinataire qui ouvre par URL le détail d'une suggestion faite pour lui reçoit une erreur 404.

---

## US-16 — Modifier un cadeau

**En tant qu'** auteur d'un cadeau
**Je veux** modifier ses informations
**Afin de** corriger une erreur ou mettre à jour le prix ou le lien

### Analyse fonctionnelle

Depuis le détail, l'auteur ouvre le formulaire pré-rempli (mêmes champs qu'US-11/US-12). Il peut modifier le nom, le prix, le lien et l'image (remplacer ou supprimer). Le destinataire n'est pas modifiable : pour changer de destinataire, il faut supprimer le cadeau et en créer un autre. La modification d'un cadeau déjà acheté est à trancher (PO-05).

### Critères d'acceptation
- Seul l'auteur peut modifier ; tout autre membre reçoit une erreur 403, y compris par requête forgée.
- Les mêmes validations qu'à la création s'appliquent.
- Remplacer l'image supprime l'ancienne du disque.
- Le destinataire n'est pas modifiable.
- Un cadeau retiré ou archivé n'est plus modifiable.

---

## US-17 — Supprimer un cadeau

**En tant qu'** auteur d'un cadeau
**Je veux** supprimer un cadeau
**Afin de** le retirer d'une liste

### Analyse fonctionnelle

Depuis le détail, l'auteur clique sur Supprimer et confirme. Si le cadeau n'a ni réservation, ni achat, ni commentaire, il est supprimé définitivement, image comprise. Sinon, il est **retiré** (suppression douce, RG-22) : il disparaît de la vue de l'auteur, les autres le voient marqué « Retiré par <auteur> » et il n'est plus réservable. Le message de confirmation est le même dans les deux cas, pour ne rien révéler au destinataire.

### Critères d'acceptation
- Seul l'auteur peut supprimer ; tout autre membre reçoit une erreur 403.
- Cadeau sans activité : la ligne est supprimée de la base et l'image du disque.
- Cadeau avec réservation, achat ou commentaire : `removed_at` est renseigné et les données sont conservées.
- Après suppression, l'auteur voit le même message et le même écran dans les deux cas.
- Un cadeau retiré n'est plus réservable ni achetable.
