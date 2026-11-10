# 07 — Journal des incréments

Une entrée par incrément livré (tests verts). Format :

```
## AAAA-MM-JJ — US-xx (incrément n) — titre court
- Fait : …
- Fichiers : …
- Tests : x ajoutés, total y verts
- Décisions validées : …
```

---

## 2026-11-06 — Cadrage
- Fait : analyse des écrans Power Apps, règles métier, modèle de données, user stories, configuration Claude Code.
- Décisions validées : stack FastAPI + Jinja2/HTMX + SQLite, admin = compte distinct limité au panel, réservation multiple + statut acheté, suppression douce, archivage annuel.

## 2026-11-10 — Lots 0 à 5 — livraison complète en une fois
- Fait : tout le site, à la demande de Lukas (« en one shot »), en dérogation ponctuelle à la méthode par petits incréments. Socle, authentification, panel admin, listes de cadeaux, suggestions, réservations, achat, commentaires, profil, clôture de l'année, design.
- Fichiers : `app/` (modèles, services, routers, templates, CSS), `migrations/`, `tests/`, `Dockerfile`, `.env.example`.
- Tests : 100 ajoutés, 100 verts. La matrice de confidentialité RG-30 est couverte par `tests/test_visibility.py`. Parcours vérifié à la main dans un vrai navigateur (connexion, recherche, tri, interrupteur « Suggérer », commentaires HTMX, admin, mobile et mode sombre).
- Décisions appliquées par défaut, à confirmer : PO-01, PO-03 à PO-07, PO-09 à PO-14 (cf. `06-points-ouverts.md`).
- Non fait : mise en production (lot 6). Le `Dockerfile` n'a pas été testé.

## 2026-11-10 — US-26 (incrément 1) — supprimer un compte membre
- Fait : suppression définitive d'un compte depuis sa fiche admin, avec toute sa trace (liste, suggestions, réservations, commentaires, images). Un cadeau qu'il avait marqué « acheté » redevient réservé ou disponible.
- Fichiers : `app/services/admin.py` (`delete_member`), `app/routers/admin.py`, `app/templates/admin/member_edit.html`, `tests/test_admin.py`.
- Tests : 3 ajoutés, total 103 verts.
- Décisions validées : « tout supprimer » plutôt que « seulement si le compte est vide » ou « garder ce qu'il a fait pour les autres » (nouvelle règle RG-41).
