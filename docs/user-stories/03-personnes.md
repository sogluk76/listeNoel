# User stories — Liste des personnes

---

## US-10 — Consulter la liste des personnes

**En tant que** membre connecté
**Je veux** voir la liste des membres de la famille avec leur nombre de cadeaux
**Afin de** choisir la liste que je veux consulter

### Analyse fonctionnelle

C'est l'écran d'accueil de la liste de Noël (`/noel`), ouvert depuis le menu (US-38). Il affiche tous les membres actifs, moi compris, par ordre alphabétique (RG-12), chacun avec sa photo ou son placeholder, son prénom et, entre parenthèses, le nombre de cadeaux **que je peux voir** sur sa liste (RG-13). Sur ma propre ligne, le compteur n'inclut donc pas les suggestions qu'on m'a faites. Cliquer sur une personne ouvre sa liste de cadeaux (US-13).

L'écran propose aussi un bouton « + » qui ouvre le formulaire d'ajout de cadeau (US-11) et un accès au profil.

### Critères d'acceptation
- Tous les membres actifs sont listés par ordre alphabétique ; ni l'admin ni les comptes désactivés n'y figurent.
- Pour Alice qui regarde : sa ligne compte ses cadeaux personnels, sans les suggestions qu'on lui a faites ; la ligne de Bob compte les cadeaux personnels de Bob **et** les suggestions pour Bob.
- Les cadeaux retirés et archivés ne sont jamais comptés.
- Un clic sur une personne ouvre sa liste.
- Le bouton « + » ouvre le formulaire d'ajout.
