# User stories — Profil

L'écran profil est accessible depuis la liste des personnes. Il regroupe : ma photo, le changement de mot de passe, mes réservations et la déconnexion (US-02).

---

## US-23 — Changer ma photo de profil

**En tant que** membre connecté
**Je veux** changer ou supprimer ma photo de profil
**Afin que** la famille me reconnaisse à la connexion et dans les commentaires

### Analyse fonctionnelle

L'écran profil affiche ma photo actuelle ou le placeholder. J'envoie une nouvelle image (mêmes contraintes que RG-17) ou je supprime la photo actuelle. La nouvelle photo est utilisée partout : écran de connexion, liste des personnes, commentaires. L'admin peut faire la même chose depuis le panel (US-06).

| Champ | Saisie | Obligatoire |
|---|---|---|
| Photo | Fichier image (JPEG, PNG, WebP, 5 Mo max) | Non |

### Critères d'acceptation
- La nouvelle photo apparaît à la connexion, dans la liste des personnes et dans les commentaires.
- L'ancienne image est supprimée du disque.
- Supprimer la photo affiche le placeholder.
- Un fichier invalide est refusé.

---

## US-24 — Changer mon mot de passe

**En tant que** membre connecté
**Je veux** changer mon mot de passe
**Afin de** remplacer le mot de passe initial donné par l'admin

### Analyse fonctionnelle

Je saisis mon mot de passe actuel, puis le nouveau deux fois (RG-37). Si le mot de passe actuel est faux ou si les deux nouveaux diffèrent, un message l'indique. En cas de succès, un message de confirmation s'affiche et ma session reste ouverte.

| Champ | Saisie | Obligatoire |
|---|---|---|
| Mot de passe actuel | Texte masqué | Oui |
| Nouveau mot de passe | Texte masqué, 8 caractères minimum | Oui |
| Confirmation | Texte masqué | Oui |

### Critères d'acceptation
- Un mot de passe actuel faux est refusé.
- Un nouveau mot de passe de moins de 8 caractères est refusé.
- Une confirmation différente est refusée.
- Après le changement, l'ancien mot de passe ne fonctionne plus et le nouveau fonctionne.

---

## US-25 — Voir mes réservations

**En tant que** membre connecté
**Je veux** voir la liste des cadeaux que j'ai réservés ou achetés
**Afin de** savoir ce qu'il me reste à acheter et pour qui

### Analyse fonctionnelle

La section « Mes réservations » liste les cadeaux non archivés sur lesquels j'ai une réservation ou que j'ai marqués achetés, regroupés par destinataire (RG-38). Chaque ligne affiche le nom du cadeau, son prix, son statut (réservé / acheté / retiré) et donne accès au détail. Un total des prix par destinataire est affiché.

### Critères d'acceptation
- Seuls mes cadeaux réservés ou achetés apparaissent.
- Les cadeaux sont regroupés par destinataire, avec un sous-total.
- Un cadeau retiré par son auteur apparaît marqué « Retiré ».
- Les cadeaux archivés n'apparaissent pas.
