# 05 — Backlog

Statuts : ⬜ à faire · 🟨 en cours · ✅ livré (tests verts, doc à jour)

Les lots 0 à 5 ont été livrés en une seule fois le 10/11/2026 (cf. journal). Les prochaines évolutions reprennent la méthode par petits incréments.

## Lot 0 — Socle technique
| | Tâche |
|---|---|
| ✅ | Projet `uv`, FastAPI, structure de dossiers, ruff, pytest |
| ✅ | Config (`pydantic-settings`), base SQLite, `PRAGMA foreign_keys` |
| ✅ | Modèles SQLAlchemy + première migration Alembic (cf. 03-modele-donnees) |
| ✅ | Fixtures de test : base en mémoire, membres Alice/Bob/Chloé, un admin |
| ✅ | Layout Jinja2 de base + HTMX + protection CSRF |
| ✅ | Commande `create-admin` |
| ✅ | Design : tokens, composants, mode sombre (skill `design-site`) |

## Lot 1 — Authentification et administration des comptes
| | US | Titre |
|---|---|---|
| ✅ | US-04 | Se connecter en tant qu'admin |
| ✅ | US-05 | Créer un compte membre |
| ✅ | US-06 | Modifier ou désactiver un compte |
| ✅ | US-07 | Réinitialiser un mot de passe / débloquer un compte |
| ✅ | US-01 | Se connecter en tant que membre |
| ✅ | US-03 | Blocage après 5 échecs |
| ✅ | US-02 | Se déconnecter |
| ✅ | US-26 | Supprimer un compte membre |

## Lot 2 — Listes de cadeaux (cœur de l'appli)
| | US | Titre |
|---|---|---|
| ✅ | US-10 | Consulter la liste des personnes |
| ✅ | US-11 | Ajouter un cadeau à ma liste |
| ✅ | US-13 | Consulter la liste de cadeaux d'une personne |
| ✅ | US-12 | Suggérer un cadeau pour quelqu'un |
| ✅ | US-15 | Consulter le détail d'un cadeau |
| ✅ | US-14 | Rechercher et trier les cadeaux |
| ✅ | US-16 | Modifier un cadeau |
| ✅ | US-17 | Supprimer un cadeau |

## Lot 3 — Coordination
| | US | Titre |
|---|---|---|
| ✅ | US-18 | Réserver / annuler une réservation |
| ✅ | US-19 | Marquer acheté / annuler l'achat |
| ✅ | US-20 | Consulter les commentaires d'un cadeau |
| ✅ | US-21 | Écrire un commentaire |
| ✅ | US-22 | Modifier / supprimer mon commentaire |

## Lot 4 — Profil
| | US | Titre |
|---|---|---|
| ✅ | US-23 | Changer ma photo de profil |
| ✅ | US-24 | Changer mon mot de passe |
| ✅ | US-25 | Voir mes réservations |

## Lot 5 — Administration des cadeaux
| | US | Titre |
|---|---|---|
| ✅ | US-08 | Supprimer un cadeau (admin) |
| ✅ | US-09 | Clôturer l'année |

## Lot 6 — Mise en production
| | Tâche |
|---|---|
| 🟨 | Dockerfile écrit, **non testé** ; reste le choix du PaaS et le volume persistant |
| ⬜ | Variables d'environnement (`NOEL_SECRET_KEY`, `NOEL_SECURE_COOKIES=true`), HTTPS |
| ⬜ | Sauvegarde de la base et des images |
| ⬜ | Création des comptes de la famille |

## Idées pour la suite
| | Idée |
|---|---|
| ⬜ | Aperçu de l'image avant envoi dans le formulaire cadeau |
| ⬜ | Réservation et achat sans rechargement de page (HTMX) |
| ⬜ | Page admin pour consulter les années archivées |
