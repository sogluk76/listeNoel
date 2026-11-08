# 02 — Règles métier

Chaque règle a un identifiant `RG-xx` cité dans les user stories et dans les tests.

## Vocabulaire

| Terme | Définition |
|---|---|
| **Membre** | Utilisateur de la famille (rôle `member`) |
| **Admin** | Compte technique (rôle `admin`), accès au panel admin seulement |
| **Destinataire** | Personne à qui le cadeau est destiné (celle dont c'est la liste) |
| **Auteur** | Personne qui a créé le cadeau |
| **Cadeau personnel** | Cadeau dont l'auteur est le destinataire |
| **Suggestion** | Cadeau dont l'auteur n'est **pas** le destinataire |
| **Réservant** | Membre qui a cliqué « je m'en occupe » sur un cadeau |
| **Viewer** | Membre connecté qui consulte un écran |

## Comptes et connexion

- **RG-01** Seul l'admin crée les comptes. Il n'y a pas d'inscription libre.
- **RG-02** Les prénoms des membres sont uniques (ils servent d'identifiant de connexion).
- **RG-03** L'écran de connexion membre propose la liste déroulante des membres **actifs**, triée par ordre alphabétique. L'admin n'y apparaît jamais.
- **RG-04** Quand un prénom est choisi, sa photo de profil s'affiche, ou un placeholder (initiales) s'il n'en a pas.
- **RG-05** Après **5 échecs consécutifs**, le compte est bloqué **15 minutes** (durée à confirmer, cf. points ouverts). Un succès remet le compteur à zéro. L'admin peut débloquer un compte.
- **RG-06** Le message d'erreur reste générique : « Mot de passe incorrect ». En cas de blocage : « Compte temporairement bloqué, réessaie plus tard ».
- **RG-07** La session dure **30 jours**. Un bouton de déconnexion est disponible depuis le profil.
- **RG-08** L'admin se connecte sur une page séparée `/admin/login`, avec identifiant + mot de passe.
- **RG-09** Un membre n'accède jamais au panel admin, et l'admin n'accède jamais aux écrans membres. Toute tentative renvoie une erreur 403 ou une redirection vers la bonne page de connexion.
- **RG-10** Les mots de passe sont stockés **hachés** (Argon2), jamais en clair. L'admin définit le mot de passe initial et chaque membre peut ensuite changer le sien. Longueur minimale : **8 caractères**, sans autre contrainte (PO-09).
- **RG-11** Un compte désactivé ne peut plus se connecter, n'apparaît plus dans les listes de personnes et ses cadeaux sont masqués. Ses données sont conservées.

## Liste des personnes

- **RG-12** La liste affiche tous les membres actifs, **moi compris**, par ordre alphabétique.
- **RG-13** Le compteur affiché à côté de chaque prénom est le **nombre de cadeaux visibles par le viewer** sur la liste de cette personne (cf. matrice RG-30), hors cadeaux retirés et archivés.

## Cadeaux

- **RG-14** Champs : nom (obligatoire), prix, lien, image, destinataire (obligatoire). Prix, lien et image sont facultatifs.
- **RG-15** Prix : montant en euros, décimal ≥ 0 avec 2 décimales maximum, affiché au format français `39,99 €`.
- **RG-16** Lien : URL `http://` ou `https://`, ouverte dans un nouvel onglet.
- **RG-17** Image : **une seule** par cadeau, en JPEG, PNG ou WebP, 5 Mo maximum, redimensionnée à l'enregistrement à **800 px maximum sur le plus grand côté** (ratio conservé, pas de recadrage ; PO-10). Même règle pour les photos de profil (US-05, US-06, US-23).
- **RG-18** Par défaut (« Suggérer pour quelqu'un d'autre » = Non), le destinataire est le membre connecté et le champ « Pour qui ? » n'est pas modifiable.
- **RG-19** Si « Suggérer » = Oui, le champ « Pour qui ? » propose **les autres membres actifs uniquement** (pas moi), et le formulaire affiche « Idée de : <moi> ».
- **RG-20** Pour les autres membres, une suggestion affiche « Suggéré par <auteur> ». Le destinataire ne voit jamais la suggestion.
- **RG-21** Seul l'**auteur** peut modifier un cadeau. L'admin ne modifie pas les cadeaux.
- **RG-22** Suppression par l'auteur :
  - si le cadeau n'a **ni réservation, ni achat, ni commentaire**, il est supprimé définitivement ;
  - sinon, c'est une **suppression douce** : le cadeau disparaît de la vue de l'auteur, et les autres membres le voient marqué « Retiré par <auteur> ». Il n'est plus réservable.
- **RG-23** L'admin peut supprimer **définitivement** n'importe quel cadeau depuis le panel, avec ses réservations et commentaires, après confirmation. Le panel affiche le nom, le destinataire, l'auteur et la date, **jamais** les commentaires ni les réservations.
- **RG-24** Recherche : sur le nom du cadeau, insensible à la casse et aux accents.
- **RG-25** Tri : par nom, par prix ou par statut (pour les autres que le destinataire), croissant ou décroissant. Tri par défaut : nom croissant. Les cadeaux sans prix sont placés en fin de liste.

## Réservations et achat

- **RG-26** Un membre peut réserver (« je m'en occupe ») un cadeau dont il n'est **pas** le destinataire. **Plusieurs** membres peuvent réserver le même cadeau, et la liste des réservants est visible par tous sauf le destinataire.
- **RG-27** Un réservant peut annuler sa propre réservation tant que le cadeau n'est pas acheté.
- **RG-28** Un **réservant** peut passer le cadeau en « acheté ». Le cadeau est alors **bloqué** : plus de nouvelle réservation ni d'annulation de réservation. Il reste visible avec la mention « Acheté par <membre> », et on peut toujours écrire des commentaires.
- **RG-29** Seul le membre qui a marqué le cadeau « acheté » peut annuler l'achat. Le cadeau repasse alors en « réservé », avec ses réservants.

## Matrice de confidentialité

- **RG-30** Ce que voit le viewer V sur la liste de la personne D :

| Élément | V = D (ma liste) | V ≠ D (liste d'un autre) |
|---|---|---|
| Cadeaux personnels de D | ✅ | ✅ |
| Suggestions pour D | ❌ | ✅ avec « Suggéré par X » |
| Cadeaux retirés par leur auteur | ❌ (si V est l'auteur) | ✅ marqués « Retiré » |
| Réservations / statut acheté | ❌ | ✅ |
| Icône commentaires + badge | ❌ | ✅ |
| Écran commentaires (y compris par URL directe) | ❌ 403 | ✅ |
| Tri par statut | ❌ | ✅ |

> ⚠️ La règle s'applique **côté serveur** (requêtes et contrôles d'accès), pas seulement à l'affichage. Une URL tapée à la main ne doit rien révéler. Elle doit être couverte par des tests dédiés.

## Commentaires

- **RG-31** Les commentaires sont rattachés à **un cadeau**. On y accède depuis l'icône commentaire du cadeau. Le badge affiche le nombre de commentaires.
- **RG-32** Un message affiche l'auteur, sa photo (ou le placeholder), la date et l'heure (`07/12/2025 17:00`) et le texte. Mes messages sont alignés à droite, ceux des autres à gauche. Ordre chronologique, du plus ancien au plus récent.
- **RG-33** Les messages vides ou composés uniquement d'espaces sont refusés. Les emojis sont acceptés. Longueur maximale : 1 000 caractères.
- **RG-34** Le fil se rafraîchit automatiquement toutes les **20 secondes**.
- **RG-35** Chacun peut **modifier** et **supprimer** ses propres messages. Un message modifié affiche « (modifié) ».

## Profil

- **RG-36** Chaque membre peut changer sa photo. L'admin peut aussi changer la photo d'un membre.
- **RG-37** Pour changer son mot de passe, le membre saisit l'ancien, puis le nouveau deux fois (8 caractères minimum).
- **RG-38** « Mes réservations » liste les cadeaux que j'ai réservés ou achetés, regroupés par destinataire, avec leur statut.

## Clôture de l'année

- **RG-39** L'admin clôture l'année N : les cadeaux **achetés** et les cadeaux **retirés** sont archivés (année N), avec leurs commentaires. Les autres cadeaux restent dans les listes.
- **RG-40** Les cadeaux archivés n'apparaissent plus nulle part dans l'application membre et ne comptent plus dans les compteurs.
