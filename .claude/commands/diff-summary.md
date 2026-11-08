---
description: Résume le diff en cours avant validation par Lukas
---

Résume les modifications de l'incrément en cours, **sans rien modifier**.

Appuie-toi sur `git diff` (et `git status` pour les fichiers non suivis). Lance `uv run pytest -q` pour avoir le résultat réel des tests.

Format attendu :

```
## Incrément : <US-xx> — <titre court>

**Fichiers**
- `chemin/fichier.py` (nouveau | modifié) : ce qui change, en une ligne

**Pourquoi**
<2-3 phrases, avec les RG-xx concernées>

**Tests**
- Ajoutés : <liste des noms de tests>
- Résultat : <x passés, y échoués>

**Points d'attention**
<décisions prises, choix à valider, limites, dette éventuelle — ou « aucun »>

**Prochain incrément proposé**
<une ligne>
```

Puis arrête-toi et attends la validation.
