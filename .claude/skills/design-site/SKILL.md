---
name: design-site
description: Direction artistique et système de design du site Liste de Noël. À utiliser AUTOMATIQUEMENT dès qu'un template Jinja2 (app/templates/) ou un fichier CSS (app/static/css/) est créé ou modifié, et quand Lukas demande de rendre le site plus beau, de styler un écran ou de revoir l'interface.
---

# Design du site Liste de Noël

Le but est d'avoir un site **vraiment beau**, chaleureux et festif sans être kitsch, pensé d'abord pour le mobile. On veut une impression de carte de vœux haut de gamme, pas de site « template ». Chaque écran livré doit être stylé dans le même incrément que son HTML. On ne laisse jamais de HTML brut « pour plus tard ».

## 1. Direction artistique

**Ambiance** : un soir d'hiver au chaud. Papier crème, vert sapin profond, rouge canneberge, touches d'or. Des formes douces et arrondies, beaucoup d'air, une typographie expressive pour les titres et sobre pour le texte.

**À éviter** : dégradés violets, look Bootstrap par défaut, emojis en guise d'icônes de structure, flocons qui tombent partout, rouge et vert saturés côte à côte, ombres grises lourdes.

### Palette (tokens dans `assets/tokens.css`)
| Token | Rôle | Valeur |
|---|---|---|
| `--c-bg` | Fond de page (papier crème) | `#FBF7F0` |
| `--c-surface` | Cartes, formulaires | `#FFFFFF` |
| `--c-ink` | Texte principal | `#1F2A24` |
| `--c-ink-soft` | Texte secondaire | `#5B6660` |
| `--c-pine` | Couleur primaire (vert sapin) | `#1E4D3A` |
| `--c-pine-soft` | Fonds verts légers | `#E4EFE8` |
| `--c-berry` | Accent, actions fortes (canneberge) | `#B3263E` |
| `--c-berry-soft` | Fonds rouges légers | `#F8E3E6` |
| `--c-gold` | Détails, badges, focus décoratif | `#C99A2E` |
| `--c-gold-soft` | Fonds dorés légers | `#F7EDD3` |
| `--c-line` | Bordures | `#E8E0D2` |

Le mode sombre (`prefers-color-scheme: dark`) est prévu dans les tokens : nuit bleu sapin `#0F1A16`, surfaces `#17241F`, texte `#EEF2EC`.

### Thèmes au choix du membre (RG-56)

Le membre choisit son thème dans son profil ; il est posé sur `<html data-theme="…">`. Sans attribut, le thème est automatique (palette ci-dessus en clair, mode sombre selon l'appareil). Chaque thème redéfinit les **mêmes tokens** dans `tokens.css` : un composant n'a donc jamais à connaître le thème. `--c-pine` est la couleur primaire du thème et `--c-berry` son accent, quelle que soit leur teinte réelle.

| Clé | Nom | Fond | Primaire | Accent |
|---|---|---|---|---|
| `clair` | Clair (base) | crème `#FBF7F0` | sapin `#1E4D3A` | canneberge `#B3263E` |
| `sombre` | Sombre (base) | `#0F1A16` | `#4E9C78` | `#E0566D` |
| `neige` | Neige | blanc `#FFFFFF` | bleu glacier `#1F5673` | `#B3263E` |
| `canneberge` | Canneberge | `#FCF5F5` | rouge `#9B1B34` | sapin `#1E4D3A` |
| `epices` | Pain d'épices | `#F9F1E7` | cannelle `#8A3B12` | `#A8233A` |
| `minuit` | Minuit | bleu nuit `#0D1220` | or `#E0B85A` | `#E8607A` |

Ajouter un thème : un bloc `[data-theme="clé"]` dans `tokens.css` avec tous les tokens de couleur, une entrée dans `THEMES` (`app/services/users.py`), et les contrastes vérifiés (4,5:1).

### Typographie
- **Titres** : `Fraunces` (serif à caractère, poids 600, légère italique possible sur les grands titres).
- **Texte et UI** : `Nunito Sans` (400, 600, 700).
- Polices **auto-hébergées** dans `app/static/fonts/` (woff2), pas d'appel à Google Fonts (vie privée, rapidité). Si les fichiers manquent, demande à Lukas de les déposer, ou propose de les récupérer avec `uv`/`pip` (`fontsource`), puis utilise la pile de secours (`Georgia, serif` / `system-ui, sans-serif`) en attendant.
- Échelle : 14 / 16 / 18 / 22 / 28 / 36 px (`--fs-sm` … `--fs-3xl`). Le texte courant fait 16 px minimum (pas de zoom forcé sur iOS).

### Formes et profondeur
- Rayons : `--r-sm: 8px`, `--r-md: 14px`, `--r-lg: 22px`, `--r-pill: 999px`.
- Ombres teintées, jamais grises : `--shadow-1` (cartes), `--shadow-2` (élément survolé / modale).
- Espacements sur une base de 4 px : `--sp-1` (4) … `--sp-8` (48).

## 2. Architecture CSS

```
app/static/css/
├── tokens.css      # variables uniquement (copie de assets/tokens.css)
├── base.css        # reset léger, typo, liens, focus, layout global
├── components.css  # composants réutilisables (section 3)
└── screens.css     # ajustements propres à un écran, à garder minimal
```

- Fichiers chargés dans cet ordre dans `templates/base.html`. Pas de build, pas de framework CSS, pas de Tailwind.
- **Aucune couleur, taille ou ombre en dur** hors de `tokens.css` : on utilise toujours `var(--…)`.
- Pas d'attribut `style=""` dans les templates.
- Nommage des classes : `composant`, `composant__element`, `composant--variante` (ex. `gift-card__price`, `pill--bought`).
- Les composants répétés deviennent des **macros Jinja2** dans `templates/components/` (`avatar`, `pill`, `button`, `field`, `empty_state`…).
- CSS moderne autorisé : nesting natif, `:has()`, `clamp()`, `color-mix()`, container queries.

## 3. Composants à fournir

| Composant | Utilisé dans | Points clés |
|---|---|---|
| `app-header` | Tous les écrans | Barre collante, titre en Fraunces, bouton retour à gauche, actions à droite (icônes SVG, 44 px de zone tactile) |
| `avatar` | Connexion, personnes, commentaires | Rond, photo en `object-fit: cover` ; **placeholder** = initiales sur une couleur déterministe tirée du prénom (6 teintes de la palette, choisies par un hash du prénom dans la macro) |
| `login-card` | Connexion | Carte centrée, avatar 96 px qui change avec un fondu (HTMX), sélecteur de prénom stylé, gros bouton primaire |
| `person-row` | Liste des personnes | Avatar + prénom + compteur en pastille dorée, chevron, ligne entière cliquable, ma ligne mise en valeur discrètement (liseré vert) |
| `gift-card` | Liste de cadeaux | Image carrée à gauche (ou illustration de cadeau SVG par défaut), nom sur 2 lignes max, prix en gras, pastille de statut, badge de commentaires |
| `pill` | Statuts | `--available` (vert doux), `--reserved` (or), `--bought` (canneberge), `--removed` (gris, texte barré) |
| `badge` | Commentaires, compteur | Pastille ronde canneberge, chiffre blanc |
| `btn` | Partout | `--primary` (sapin), `--accent` (canneberge, « Je m'en occupe »), `--ghost`, `--danger` ; hauteur 48 px, état `:disabled` et `.htmx-request` (spinner) |
| `field` | Formulaires | Label au-dessus, champ arrondi, aide et erreur sous le champ (`aria-describedby`), état erreur en canneberge |
| `switch` | « Suggérer pour quelqu'un d'autre » | Interrupteur accessible sur une `input[type=checkbox]` native, animé |
| `image-drop` | Formulaire cadeau, profil | Zone en pointillés, aperçu de l'image choisie, bouton « retirer » |
| `search-bar` + `sort-select` | Liste de cadeaux | Barre de recherche arrondie avec icône, tri en `select` compact |
| `gift-detail` | Détail | Grande image en haut (ratio 4/3), infos en carte superposée, lien produit en bouton, réservants sous forme de pile d'avatars |
| `chat` | Commentaires | Bulles : les miennes à droite sur fond `--c-pine` et texte `--c-on-accent`, celles des autres à gauche sur la surface ; avatar, prénom et heure en petit ; mention « (modifié) » ; zone de saisie collée en bas, en tenant compte de `safe-area-inset-bottom` |
| `flash` | Messages de retour | Toast en bas d'écran, disparaît seul, `role="status"` |
| `empty-state` | Listes vides | Petite illustration SVG (cadeau, sapin), phrase chaleureuse, action principale |
| `admin-*` | Panel admin | Même tokens, mais plus sobre et dense : tableaux lisibles, **aucun** élément festif, pour bien distinguer le panel de l'appli |

Les icônes sont des **SVG inline** au trait (style Lucide), réunies dans une macro `icon(name)`. Les illustrations (cadeau, sapin, étoile) sont des SVG simples faits maison avec les couleurs de la palette. Pas de dépendance externe.

## 4. Mise en page et responsive

- **Mobile d'abord** : conception à 375 px, puis amélioration à partir de 640 px et de 1024 px.
- Contenu centré, largeur max 720 px pour l'appli (1100 px pour l'admin).
- Listes de cadeaux : une colonne sur mobile, grille de cartes à partir de 640 px (`grid-template-columns: repeat(auto-fill, minmax(260px, 1fr))`).
- Zones tactiles d'au moins 44 × 44 px.

## 5. Animations

- Discrètes et utiles : fondu et léger glissement à l'apparition d'une carte, d'une bulle ou d'un toast (150 à 250 ms, `ease-out`).
- Transitions HTMX : styler `.htmx-added`, `.htmx-swapping`, `.htmx-settling`.
- Une seule touche magique : quelques flocons ou étoiles **statiques** en SVG dans le header de l'écran de connexion. Pas de neige animée en plein écran.
- Tout est désactivé sous `@media (prefers-reduced-motion: reduce)`.

## 6. Accessibilité (non négociable)

- Contraste AA minimum (4,5:1 pour le texte). Les couples de la palette ont été vérifiés (texte sur fonds, `--c-on-accent` sur `--c-pine`/`--c-berry`, blanc sur les 6 teintes d'avatar), en clair comme en sombre. Tout nouveau couple de couleurs doit être vérifié.
- `:focus-visible` toujours visible (anneau doré de 3 px avec un décalage).
- Le statut d'un cadeau n'est jamais porté par la couleur seule : la pastille contient toujours un texte.
- Images : `alt` pertinent ; `alt=""` pour une image décorative.
- `lang="fr"`, titres hiérarchisés, labels liés aux champs.

## 7. Confidentialité et style

Le style ne doit **jamais** servir à cacher une donnée sensible : pas de `display:none`, de `hidden` ni de `.sr-only` sur une suggestion, un commentaire ou une réservation pour le destinataire. Ces données ne doivent pas être envoyées du tout (RG-30, `CLAUDE.md`). Une classe CSS ne doit pas non plus révéler un statut dans le HTML du destinataire (pas de `gift-card--bought` sur sa propre liste).

## 8. Façon de travailler

1. **Première utilisation** (aucun CSS dans le projet) : propose d'abord à Lukas la direction en quelques lignes (palette, polices, 2 ou 3 exemples de composants), et attends sa validation. C'est une décision de design. Ensuite, crée `tokens.css` (depuis `assets/tokens.css`), `base.css` et les macros de base, en un incrément séparé.
2. **Ensuite, automatiquement** : chaque nouveau template est livré stylé avec les composants existants. Si un composant manque, crée-le dans `components.css` et dans une macro, plutôt que de faire du sur-mesure dans l'écran.
3. Si le serveur peut tourner, vérifie le rendu (largeurs 375 px et 1024 px, mode clair et sombre) avant de présenter l'incrément.
4. Dans le résumé du diff, ajoute une section **« Rendu »** : composants créés ou modifiés et choix visuels faits.
5. Tout changement de la palette, des polices ou de la direction se fait **avec l'accord de Lukas**, et se reporte dans ce fichier.

## Checklist avant de livrer un écran
- [ ] Aucune valeur en dur hors des tokens, aucun `style=""`
- [ ] Rendu propre à 375 px et à 1024 px
- [ ] Mode sombre lisible
- [ ] Focus visible au clavier, zones tactiles ≥ 44 px
- [ ] États prévus : vide, chargement (HTMX), erreur, désactivé
- [ ] Placeholder d'avatar et image par défaut des cadeaux gérés
- [ ] Animations coupées en `prefers-reduced-motion`
- [ ] Aucune donnée cachée envoyée au destinataire
