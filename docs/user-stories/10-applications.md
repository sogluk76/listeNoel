# User stories — Menu des applications et listes de courses

Le site s'appelle « La Famille » et réunit plusieurs applications : la liste de Noël et les listes de courses (RG-58).

---

## US-38 — Choisir une application dans le menu

**En tant que** membre
**Je veux** arriver sur un menu après la connexion
**Afin de** choisir l'application que je veux utiliser

### Analyse fonctionnelle

Après la connexion, le membre arrive sur `/`, qui le salue (« Bonjour Alice ») et affiche une tuile par application : « Liste de Noël » et « Liste de courses ». La liste des personnes de la liste de Noël passe sur `/noel` ; les adresses `/personnes/...` et `/cadeaux/...` ne changent pas. Le logo « La Famille » de l'en-tête ramène au menu. La cloche, la bulle « Messages », le profil et le thème restent communs à toutes les pages.

### Critères d'acceptation
- La connexion redirige vers le menu, qui affiche une tuile par application.
- La liste des personnes est sur `/noel`, avec un lien « Menu » ; le retour depuis la liste d'une personne mène à `/noel`.
- La cloche et la bulle « Messages » sont présentes sur le menu.
- Un visiteur non connecté est renvoyé à la connexion ; l'admin reçoit une erreur 403.

---

## US-39 — Créer et gérer des listes de courses

**En tant que** membre
**Je veux** créer des listes de courses nommées, partagées avec la famille
**Afin d'** organiser les achats à plusieurs (repas du 24, courses de la semaine…)

### Analyse fonctionnelle

La page `/courses` liste toutes les listes, la plus récemment modifiée d'abord, avec le nombre d'articles restant à acheter, et propose un champ pour en créer une (RG-59). Toutes les listes sont visibles et modifiables par tous les membres : chacun peut renommer une liste ou la supprimer, après confirmation, avec ses articles (PO-20).

### Critères d'acceptation
- Le nom est obligatoire, 60 caractères au plus ; les espaces superflus sont retirés.
- Une liste créée par Alice est visible par Bob, avec « Créée par Alice ».
- Tout membre peut renommer et supprimer une liste ; la suppression emporte ses articles.
- Une liste inconnue répond 404 ; l'admin reçoit 403 ; le contenu est échappé.

---

## US-40 — Ajouter des articles

**En tant que** membre
**Je veux** ajouter un article avec une quantité facultative
**Afin de** ne rien oublier

### Analyse fonctionnelle

Sur la page d'une liste, un formulaire permet d'ajouter un article : un nom (100 caractères au plus) et une quantité libre (« 2 kg », 30 caractères au plus) (RG-60). Les articles à acheter sont affichés dans l'ordre d'ajout, avec « Ajouté par … ». L'ajout se fait sans recharger la page, et fonctionne aussi sans JavaScript.

### Critères d'acceptation
- Un article vide ou trop long est refusé avec un message sous le champ, et la saisie est conservée.
- La quantité est facultative.
- L'article affiche son auteur.

---

## US-41 — Cocher et retirer des articles

**En tant que** membre
**Je veux** cocher ce que j'ai pris et nettoyer la liste
**Afin de** savoir ce qu'il reste à acheter

### Analyse fonctionnelle

Chaque article a un rond à cocher. Un article coché descend dans « Dans le panier », le dernier coché en premier, avec « Pris par … » (PO-22) ; on peut le décocher. Un bouton retire d'un coup tous les articles cochés, et chaque article peut être supprimé seul. Quand tout est coché, la liste affiche « Tout est dans le panier ! ».

### Critères d'acceptation
- Cocher retient qui a pris l'article ; décocher l'efface.
- Le compteur de la page des listes ne compte que les articles restant à acheter.
- « Retirer les articles cochés » supprime les cochés et garde les autres.
- Un article d'une autre liste répond 404, sans rien modifier.
- Si le compte d'un membre est supprimé, ses listes et ses articles restent, affichés « un ancien membre » (RG-61, PO-21).
