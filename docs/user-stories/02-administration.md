# User stories — Administration

---

## US-05 — Créer un compte membre

**En tant qu'** admin
**Je veux** créer le compte d'un membre de la famille
**Afin qu'** il puisse se connecter au site

### Analyse fonctionnelle

Depuis le panel, l'admin ouvre le formulaire « Nouveau membre ». Il saisit le prénom, un mot de passe initial (RG-10) et peut ajouter une photo de profil (RG-17 pour les contraintes d'image). Le prénom doit être unique (RG-02), sans tenir compte de la casse. Le compte est créé actif, avec le rôle `member`. L'admin transmet ensuite le mot de passe initial à la personne, qui pourra le changer (US-24).

| Champ | Saisie | Obligatoire |
|---|---|---|
| Prénom | Texte, 1 à 50 caractères | Oui |
| Mot de passe initial | Texte masqué, 8 caractères minimum | Oui |
| Confirmation | Texte masqué | Oui |
| Photo | Fichier image (JPEG, PNG, WebP, 5 Mo max) | Non |

### Critères d'acceptation
- Le compte créé apparaît dans la liste de connexion et dans la liste des personnes.
- Un prénom déjà utilisé (même avec une casse différente) est refusé avec un message clair.
- Le mot de passe est stocké haché, jamais en clair.
- Une confirmation différente du mot de passe est refusée.
- Un fichier qui n'est pas une image valide est refusé.

---

## US-06 — Modifier ou désactiver un compte

**En tant qu'** admin
**Je veux** modifier le prénom ou la photo d'un membre, ou désactiver son compte
**Afin de** tenir la liste des membres à jour

### Analyse fonctionnelle

Le panel liste tous les comptes membres avec leur prénom, leur photo, leur statut (actif / désactivé / bloqué) et leur date de création. L'admin peut modifier le prénom (toujours unique) et la photo, ou la supprimer. Il peut désactiver un compte puis le réactiver. La désactivation ne supprime aucune donnée (RG-11) : le membre ne peut plus se connecter, il disparaît des listes et ses cadeaux sont masqués. Sa session en cours est invalidée.

| Champ | Saisie | Obligatoire |
|---|---|---|
| Prénom | Texte, 1 à 50 caractères | Oui |
| Photo | Fichier image ou « supprimer la photo » | Non |
| Actif | Case à cocher | Oui |

### Critères d'acceptation
- Un prénom modifié apparaît partout (listes, commentaires, « suggéré par »).
- Un compte désactivé ne peut plus se connecter et sa session active est refusée à la requête suivante.
- Un compte désactivé n'apparaît plus dans les listes ; ses cadeaux non plus.
- Un compte réactivé retrouve toutes ses données.
- Le compte admin n'apparaît pas dans cette liste et ne peut pas être désactivé depuis le panel.

---

## US-07 — Réinitialiser un mot de passe / débloquer un compte

**En tant qu'** admin
**Je veux** définir un nouveau mot de passe pour un membre ou débloquer son compte
**Afin de** l'aider s'il a oublié son mot de passe ou s'est bloqué

### Analyse fonctionnelle

Depuis la fiche d'un membre, l'admin peut saisir un nouveau mot de passe (avec confirmation) qui remplace l'ancien. Il peut aussi cliquer sur « Débloquer », visible seulement si le compte est bloqué, ce qui remet le compteur d'échecs à zéro et lève le blocage (RG-05). Une réinitialisation débloque aussi le compte.

| Champ | Saisie | Obligatoire |
|---|---|---|
| Nouveau mot de passe | Texte masqué, 8 caractères minimum | Oui |
| Confirmation | Texte masqué | Oui |

### Critères d'acceptation
- Après réinitialisation, l'ancien mot de passe est refusé et le nouveau accepté.
- La réinitialisation lève le blocage éventuel.
- « Débloquer » n'est visible que sur un compte bloqué et permet une connexion immédiate.

---

## US-26 — Supprimer un compte membre

**En tant qu'** admin
**Je veux** supprimer définitivement le compte d'un membre
**Afin de** retirer une personne qui ne participe plus, ou un compte créé par erreur

### Analyse fonctionnelle

Depuis la fiche d'un membre, une section « Supprimer le compte » explique ce qui sera supprimé. L'admin déplie « Supprimer ce compte » puis confirme avec « Oui, supprimer <prénom> ». La suppression emporte tout ce qui se rattache au membre (RG-41). Elle est irréversible : pour une absence temporaire, on désactive le compte (US-06).

### Critères d'acceptation
- Après confirmation, le compte, sa liste, ses suggestions, ses réservations et ses commentaires sont supprimés de la base.
- Sa photo et les images des cadeaux supprimés sont supprimées du disque.
- Un cadeau qu'il avait marqué « acheté » n'est plus acheté ; les réservations et commentaires des autres membres sur les cadeaux restants sont intacts.
- Le membre supprimé n'apparaît plus nulle part et sa session en cours est refusée à la requête suivante.
- Sans confirmation, rien n'est supprimé.
- Le compte admin ne peut pas être supprimé, et seul l'admin peut supprimer un compte.
- La fiche n'affiche ni commentaires, ni réservations, ni statut d'achat.

---

## US-08 — Supprimer un cadeau (admin)

**En tant qu'** admin
**Je veux** supprimer n'importe quel cadeau
**Afin de** retirer un contenu inapproprié ou erroné

### Analyse fonctionnelle

Le panel propose une liste de tous les cadeaux non archivés, avec le nom, le destinataire, l'auteur et la date d'ajout, filtrable par destinataire. L'admin ne voit **jamais** les commentaires ni les réservations (RG-23). La suppression est définitive, entraîne celle des réservations et des commentaires associés, et demande une confirmation.

### Critères d'acceptation
- La liste admin n'affiche ni commentaires, ni réservations, ni statut d'achat.
- Après confirmation, le cadeau, ses réservations et ses commentaires sont supprimés de la base.
- L'image du cadeau est supprimée du disque.
- Sans confirmation, rien n'est supprimé.

---

## US-09 — Clôturer l'année

**En tant qu'** admin
**Je veux** clôturer l'année de Noël
**Afin de** repartir sur des listes propres l'année suivante

### Analyse fonctionnelle

Depuis le panel, l'admin lance « Clôturer l'année N » (N proposé par défaut : l'année en cours). Un récapitulatif affiche le **nombre** de cadeaux qui seront archivés, sans détail sur le statut de chacun. Après confirmation, les cadeaux achetés et les cadeaux retirés reçoivent `archived_year = N` (RG-39) et disparaissent de l'application membre (RG-40). Les autres cadeaux restent dans les listes. Le sort des réservations des cadeaux non achetés est à trancher (PO-03).

| Champ | Saisie | Obligatoire |
|---|---|---|
| Année | Nombre (par défaut : année en cours) | Oui |

### Critères d'acceptation
- Seuls les cadeaux achetés ou retirés sont archivés.
- Les cadeaux archivés n'apparaissent plus dans aucune liste membre ni dans aucun compteur.
- Les cadeaux non achetés restent visibles comme avant.
- La clôture demande une confirmation et peut être relancée sans erreur (idempotente).
