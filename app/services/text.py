"""Petits utilitaires de texte."""

import unicodedata


def fold(value: str) -> str:
    """Forme de comparaison : sans accents ni casse (« Vélo » -> « velo »)."""
    decomposed = unicodedata.normalize("NFKD", value)
    return "".join(c for c in decomposed if not unicodedata.combining(c)).casefold().strip()


def initials(name: str) -> str:
    parts = [p for p in name.replace("-", " ").split() if p]
    if not parts:
        return "?"
    if len(parts) == 1:
        return parts[0][:1].upper()
    return (parts[0][:1] + parts[1][:1]).upper()


def color_index(name: str, count: int = 6) -> int:
    """Indice de couleur stable (1..count) pour le placeholder d'avatar."""
    return sum(ord(c) for c in fold(name)) % count + 1
