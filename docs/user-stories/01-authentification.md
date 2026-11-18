# User stories — Authentification

---

## US-01 — Se connecter en tant que membre

**En tant que** membre de la famille
**Je veux** me connecter en choisissant mon prénom et en saisissant mon mot de passe
**Afin de** accéder aux listes de cadeaux

### Analyse fonctionnelle

L'écran de connexion est la page d'entrée du site pour tout visiteur non connecté. Il propose une liste déroulante contenant les prénoms des membres actifs, triés par ordre alphabétique. L'admin n'y figure jamais (RG-03). Quand un prénom est choisi, la photo de profil du membre s'affiche sous la liste, ou un placeholder avec ses initiales s'il n'a pas de photo (RG-04). Ce changement se fait sans recharger la page (HTMX).

Le membre saisit son mot de passe puis valide. Si le couple prénom/mot de passe est correct et que le compte n'est pas bloqué, une session de 30 jours est ouverte (RG-07) et le membre est redirigé vers la liste des personnes (US-10). Sinon, un message générique s'affiche (RG-06) et le prénom reste sélectionné.

Un membre déjà connecté qui ouvre la page de connexion est redirigé directement vers la liste des personnes.

| Champ | Saisie | Obligatoire |
|---|---|---|
| Prénom | Liste déroulante des membres actifs | Oui |
| Mot de passe | Texte masqué | Oui |

### Critères d'acceptation
- La liste déroulante ne contient que les membres actifs, triés alphabétiquement, sans l'admin.
- Changer de prénom met à jour la photo ou le placeholder.
- Une connexion correcte redirige vers la liste des personnes et ouvre une session de 30 jours.
- Un mot de passe faux affiche « Mot de passe incorrect » sans indiquer si le compte existe.
- Un compte désactivé ne peut pas se connecter.
- Un succès remet à zéro le compteur d'échecs.
- Toute page membre visitée sans session redirige vers `/login`.

---

## US-02 — Se déconnecter

**En tant que** membre connecté
**Je veux** me déconnecter
**Afin de** protéger mon compte sur un appareil partagé

### Analyse fonctionnelle

Le bouton « Se déconnecter » se trouve dans l'écran profil (US-23 à US-25). Il détruit la session et redirige vers l'écran de connexion. La déconnexion se fait en POST, protégée contre les attaques CSRF.

### Critères d'acceptation
- Après déconnexion, toute page membre redirige vers `/login`.
- Le cookie de session est supprimé.
- Un GET sur l'URL de déconnexion ne déconnecte pas.

---

## US-03 — Blocage après 5 échecs

**En tant que** membre
**Je veux** que mon compte soit bloqué temporairement après plusieurs mauvais mots de passe
**Afin de** empêcher quelqu'un de deviner mon mot de passe

### Analyse fonctionnelle

Chaque échec de connexion incrémente le compteur d'échecs du compte. Au 5ᵉ échec consécutif, le compte est bloqué pendant 15 minutes (RG-05, durée à confirmer : PO-01). Pendant le blocage, même un mot de passe correct est refusé avec le message « Compte temporairement bloqué, réessaie plus tard ». À la fin du blocage, le compteur repart de zéro. L'admin peut débloquer le compte avant la fin (US-07).

### Critères d'acceptation
- 4 échecs puis un succès : connexion acceptée, compteur remis à 0.
- 5 échecs : compte bloqué, même le bon mot de passe est refusé.
- Après expiration du blocage, le bon mot de passe est accepté.
- Le déblocage par l'admin permet une connexion immédiate.
- Le blocage d'un compte n'affecte pas les autres.

---

## US-04 — Se connecter en tant qu'admin

**En tant qu'** admin
**Je veux** me connecter sur une page dédiée
**Afin d'** accéder au panel d'administration

### Analyse fonctionnelle

La page `/admin/login` demande un identifiant et un mot de passe. Le compte admin est créé à l'installation avec la commande `create-admin`. Une fois connecté, l'admin arrive sur le tableau de bord du panel (liste des comptes). L'admin n'a accès à aucun écran membre et un membre n'a accès à aucun écran admin (RG-09). La règle de blocage RG-05 s'applique aussi à l'admin.

| Champ | Saisie | Obligatoire |
|---|---|---|
| Identifiant | Texte | Oui |
| Mot de passe | Texte masqué | Oui |

### Critères d'acceptation
- La commande `create-admin` crée un compte de rôle `admin`, et refuse d'en créer un si le prénom est déjà pris.
- Une connexion admin correcte redirige vers `/admin`.
- Un membre ne peut pas se connecter via `/admin/login`.
- Un admin connecté qui ouvre `/`, `/noel` ou `/personnes/...` reçoit une erreur 403.
- Un membre connecté qui ouvre `/admin/...` reçoit une erreur 403.
- Les pages `/admin/...` sans session admin redirigent vers `/admin/login`.
