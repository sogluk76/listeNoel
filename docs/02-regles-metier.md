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
- **RG-05** Après **5 échecs consécutifs**, le compte est bloqué **15 minutes** (PO-01, à confirmer). Un succès remet le compteur à zéro. L'admin peut débloquer un compte.
- **RG-06** Le message d'erreur reste générique : « Mot de passe incorrect ». En cas de blocage : « Compte temporairement bloqué, réessaie plus tard ».
- **RG-07** La session dure **30 jours**. Un bouton de déconnexion est disponible depuis le profil.
- **RG-08** L'admin se connecte sur une page séparée `/admin/login`, avec identifiant + mot de passe.
- **RG-09** Un membre n'accède jamais au panel admin, et l'admin n'accède jamais aux écrans membres. Toute tentative renvoie une erreur 403 ou une redirection vers la bonne page de connexion.
- **RG-10** Les mots de passe sont stockés **hachés** (Argon2), jamais en clair. L'admin définit le mot de passe initial et chaque membre peut ensuite changer le sien.
- **RG-11** Un compte désactivé ne peut plus se connecter, n'apparaît plus dans les listes de personnes et ses cadeaux sont masqués. Ses données sont conservées.

## Menu des applications

- **RG-58** Le site s'appelle **« La Famille »** et réunit plusieurs applications. Après la connexion, le membre arrive sur le **menu** (`/`), qui propose une tuile par application : « Liste de Noël » (`/noel`) et « Liste de courses » (`/courses`). Le logo de l'en-tête ramène au menu. La cloche, la bulle « Messages », le profil et le thème sont communs à toutes les applications. Le menu et les applications sont réservés aux membres (RG-09).

## Liste des personnes

- **RG-12** La liste (`/noel`, page d'accueil de la liste de Noël) affiche tous les membres actifs, **moi compris**, par ordre alphabétique.
- **RG-13** Le compteur affiché à côté de chaque prénom est le **nombre de cadeaux visibles par le viewer** sur la liste de cette personne (cf. matrice RG-30), hors cadeaux retirés et archivés.

## Cadeaux

- **RG-14** Champs : nom (obligatoire), prix, lien, image, destinataire (obligatoire). Prix, lien et image sont facultatifs.
- **RG-15** Prix : montant en euros, décimal ≥ 0 avec 2 décimales maximum, affiché au format français `39,99 €`.
- **RG-16** Lien : URL `http://` ou `https://`, ouverte dans un nouvel onglet.
- **RG-17** Image : **une seule** par cadeau, en JPEG, PNG ou WebP, 5 Mo maximum, redimensionnée à l'enregistrement.
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
| Mention `@D` dans le fil et notification associée (RG-43) | ❌ jamais notifié | ✅ pour les autres membres |
| Notification « nouvelle suggestion pour D » (RG-57) | ❌ jamais notifié | ✅ pour les autres membres, sauf l'auteur |

> ⚠️ La règle s'applique **côté serveur** (requêtes et contrôles d'accès), pas seulement à l'affichage. Une URL tapée à la main ne doit rien révéler. Elle doit être couverte par des tests dédiés.

## Commentaires

- **RG-31** Les commentaires sont rattachés à **un cadeau**. On y accède depuis l'icône commentaire du cadeau. Le badge affiche le nombre de commentaires.
- **RG-32** Un message affiche l'auteur, sa photo (ou le placeholder), la date et l'heure (`07/12/2025 17:00`) et le texte. Mes messages sont alignés à droite, ceux des autres à gauche. Ordre chronologique, du plus ancien au plus récent.
- **RG-33** Les messages vides ou composés uniquement d'espaces sont refusés. Les emojis sont acceptés. Longueur maximale : 1 000 caractères. Sur ordinateur, **Entrée envoie** le message et **Maj+Entrée** va à la ligne ; sur téléphone et tablette, Entrée va à la ligne et on envoie avec le bouton.
- **RG-34** Le fil se rafraîchit automatiquement toutes les **20 secondes**.
- **RG-35** Chacun peut **modifier** et **supprimer** ses propres messages. Un message modifié affiche « (modifié) ». La modification se fait sur une page dédiée (PO-10).

## Profil

- **RG-36** Chaque membre peut changer sa photo. L'admin peut aussi changer la photo d'un membre.
- **RG-37** Pour changer son mot de passe, le membre saisit l'ancien, puis le nouveau deux fois (8 caractères minimum).
- **RG-38** « Mes réservations » liste les cadeaux que j'ai réservés ou achetés, regroupés par destinataire, avec leur statut.
- **RG-56** Chaque membre choisit son **thème d'affichage** dans son profil : Automatique (clair ou sombre selon l'appareil, choix par défaut), Clair, Sombre, Neige, Canneberge, Pain d'épices ou Minuit. Le thème est enregistré sur le compte : il s'applique à toutes les pages membre et suit le membre sur tous ses appareils. Un thème inconnu est refusé. La page de connexion, les pages d'erreur et le panel admin restent en thème automatique.

## Clôture de l'année

- **RG-39** L'admin clôture l'année N : les cadeaux **achetés** et les cadeaux **retirés** sont archivés (année N), avec leurs commentaires. Les autres cadeaux restent dans les listes.
- **RG-40** Les cadeaux archivés n'apparaissent plus nulle part dans l'application membre et ne comptent plus dans les compteurs.

## Mentions et notifications

- **RG-42** Dans un commentaire, `@` suivi du prénom d'un membre actif est une **mention**. Le prénom est reconnu sans tenir compte de la casse ni des accents, et doit être complet (`@Bobby` ne mentionne pas Bob). Le `@` ne doit pas suivre une lettre ou un chiffre (une adresse mail n'est pas une mention). Chaque membre mentionné reçoit **une** notification par message, sauf l'auteur du message.
- **RG-43** Le **destinataire du cadeau n'est jamais notifié** et ne peut pas être mentionné dans le fil de son propre cadeau : son prénom y reste du texte simple. Le commentaire est accepté normalement. C'est une conséquence de RG-30 : une notification lui révélerait qu'on parle d'un de ses cadeaux.
- **RG-44** Les notifications suivent le message : modifier un message ajoute ou retire les notifications selon ses mentions, supprimer un message (ou son cadeau) les supprime.
- **RG-45** Une **cloche** dans l'en-tête des pages membre affiche le nombre de notifications non lues : les mentions, plus **une par conversation privée qui contient du non-lu** (RG-50). La page « Notifications » liste d'abord ces conversations, puis les mentions de la plus récente à la plus ancienne, et **marque toutes les mentions comme lues à l'ouverture**. Ouvrir la page de commentaires d'un cadeau marque aussi comme lues les notifications de ce fil (et seulement celles-là) ; le rafraîchissement automatique du fil ne marque rien. Une notification n'est affichée et comptée que si le membre a encore le droit de voir le fil concerné (RG-30, RG-11, RG-40). Les notifications n'existent que sur le site : pas de mail, pas de notification sur le téléphone. L'admin n'en a pas. Les nouveaux cadeaux (RG-57) sont listés et comptés avec les mentions.
- **RG-57** Quand un membre **crée un cadeau**, chaque membre actif qui peut le voir reçoit **une** notification, sauf l'auteur : pour un cadeau sur sa propre liste, tous les autres membres (« Bob a ajouté « Vélo » à sa liste ») ; pour une suggestion pour D, tout le monde sauf l'auteur **et D** (« Bob a suggéré « Vélo » pour Chloé »). D n'est jamais notifié d'une suggestion (RG-30). La ligne affiche le prix s'il y en a un et mène à la fiche du cadeau. Elle est marquée lue à l'ouverture de la page « Notifications » ou de la fiche du cadeau. Modifier un cadeau ne notifie pas. Supprimer le cadeau supprime ses notifications ; un cadeau retiré, archivé ou qui n'est plus visible n'est plus affiché ni compté. Seuls les cadeaux créés depuis la mise en place de la règle génèrent une notification.

## Messages privés

Les messages privés ne sont rattachés à aucun cadeau : la matrice RG-30 ne s'y applique pas, et on peut écrire ce qu'on veut à qui on veut.

- **RG-46** Deux membres actifs peuvent s'écrire dans une **conversation à deux**, unique pour la paire. Un membre peut aussi créer un **groupe** nommé (RG-53). On ne s'écrit pas à soi-même. **L'admin n'a aucun accès** aux messages : ni bulle, ni pages, ni rien dans le panel.
- **RG-47** Seuls les **participants** d'une conversation la lisent et y écrivent. La règle s'applique côté serveur : pour tout autre membre, la conversation, son fil, ses messages et ses photos répondent 404, y compris par une URL tapée à la main. Les photos ne sont jamais servies depuis le dossier public des images.
- **RG-48** Un message contient un texte (1 à 1 000 caractères, emojis acceptés), **une** photo (JPEG, PNG ou WebP, 5 Mo maximum, comme RG-17), ou les deux. Sur ordinateur, Entrée envoie et Maj+Entrée va à la ligne ; sur téléphone, on envoie avec le bouton.
- **RG-49** Chacun peut **modifier** le texte et **supprimer** ses propres messages. Un message modifié affiche « (modifié) ». Un message supprimé disparaît sans laisser de trace, avec sa photo.
- **RG-50** Un message est **non lu** tant que son destinataire n'a pas affiché la conversation. La bulle « Messages » affiche le nombre de messages non lus ; la cloche compte **une notification par conversation** non lue, listée dans la page « Notifications » (« Bob t'a envoyé 3 messages »). Seul l'affichage de la conversation la marque comme lue : ouvrir la page « Notifications » ne suffit pas. Ses propres messages ne comptent jamais.
- **RG-51** « **Vu** » s'affiche sous mon dernier message quand il est le dernier du fil et que l'autre l'a lu. Dans un groupe : « Vu par Bob, Chloé ».
- **RG-52** L'en-tête d'une conversation à deux affiche la présence de l'autre : « **En ligne** » s'il a utilisé le site depuis moins de 2 minutes, sinon « En ligne il y a 7 min » (min, h, j, sem.), ou rien s'il ne s'est jamais connecté. Visible par tous les membres, sans réglage pour le masquer.
- **RG-53** Groupes :
  - le créateur choisit un nom (1 à 60 caractères) et au moins un autre membre actif ;
  - tout participant peut **ajouter** un membre actif et **quitter** le groupe ;
  - seul le **créateur** peut renommer le groupe et retirer quelqu'un ;
  - un nouvel arrivant voit **tout l'historique**, sans que rien ne lui soit compté comme non lu ;
  - un membre retiré ou parti perd tout accès ; ses messages restent ;
  - si le créateur part, le plus ancien participant devient créateur ; un groupe sans participant est supprimé.
- **RG-54** Compte **désactivé** : ses conversations restent lisibles, mais on ne peut plus lui écrire à deux (les groupes continuent). Compte **supprimé** (RG-41) : ses messages et ses conversations à deux disparaissent, il est retiré des groupes. La **clôture de l'année** ne touche pas aux messages.
- **RG-55** La messagerie s'ouvre dans une **pop-up** en bas à droite de toutes les pages membre, depuis une bulle « Messages » (plein écran sur téléphone). Elle reste ouverte au même endroit quand on change de page. La conversation affichée se rafraîchit toutes les **5 secondes**, la bulle et la cloche toutes les **20 secondes**. Sans JavaScript, la bulle mène à la même messagerie en pleine page (`/messages`).

## Listes de courses

Les listes de courses ne sont rattachées à aucun cadeau : la matrice RG-30 ne s'y applique pas.

- **RG-59** Tout membre actif peut créer une **liste de courses** nommée (1 à 60 caractères, espaces superflus retirés). **Toutes les listes sont partagées** : chaque membre les voit, les renomme et les supprime (après confirmation, avec tous leurs articles) (PO-20). Elles sont triées de la plus récemment modifiée à la plus ancienne, avec le nombre d'articles restant à acheter. L'admin n'y a aucun accès (403).
- **RG-60** Un **article** a un nom (1 à 100 caractères) et une quantité libre facultative (« 2 kg », 30 caractères au plus). Tout membre peut en ajouter, **cocher** un article pris, le décocher, le supprimer, et **retirer d'un coup tous les articles cochés**. Les articles à acheter sont affichés dans l'ordre d'ajout avec « Ajouté par … » ; les articles cochés descendent dans « Dans le panier », le dernier coché en premier, avec « Pris par … » (PO-22). Les actions se font sans recharger la page (HTMX), et fonctionnent aussi sans JavaScript. Un article d'une autre liste répond 404. Les listes de courses ne génèrent aucune notification.
- **RG-61** Compte **supprimé** (RG-41) : ses listes et les articles qu'il a ajoutés ou cochés **restent**, sans auteur (« un ancien membre ») (PO-21). Compte **désactivé** : rien ne change dans les listes. La clôture de l'année ne touche pas aux listes de courses.

## Suppression d'un compte

- **RG-41** L'admin peut supprimer **définitivement** le compte d'un membre, après confirmation. Tout ce qui s'y rattache est supprimé avec lui :
  - sa liste (les cadeaux dont il est destinataire, y compris les suggestions des autres, avec leurs réservations et commentaires) ;
  - les cadeaux qu'il a créés pour d'autres (ses suggestions), avec leurs réservations et commentaires ;
  - ses réservations et ses commentaires sur les cadeaux des autres ;
  - ses notifications, et celles créées par ses commentaires ;
  - ses messages privés, ses conversations à deux (en entier) et sa place dans les groupes (RG-54) ;
  - sa photo et les images des cadeaux supprimés ;
  - les cadeaux archivés qui le concernent.

  Seule exception : ses **listes de courses** et les articles qu'il y a ajoutés **restent** à la famille, sans auteur (RG-61).

  Un cadeau qu'il avait marqué « acheté » redevient « réservé » (s'il reste des réservants) ou disponible. Le compte admin ne peut pas être supprimé depuis le panel. La fiche du membre n'affiche aucun détail sur ce qui sera supprimé (RG-23). Pour une absence temporaire, la désactivation (RG-11) reste la bonne option.
