#!/usr/bin/env bash
# Hook PostToolUse : relance les tests après chaque modification d'un fichier de code.
# Exit 2 = les tests échouent : la sortie est renvoyée à Claude, qui doit corriger avant de continuer.

input=$(cat)

cd "$CLAUDE_PROJECT_DIR" || exit 0
[ -d tests ] || exit 0
command -v uv >/dev/null 2>&1 || { echo "uv introuvable : tests non lancés" >&2; exit 0; }

# On passe par le Python de uv : sous Windows, `python3` est le raccourci du Microsoft Store et ne fait rien.
file=$(printf '%s' "$input" | uv run --no-sync python -c 'import sys, json; print(json.load(sys.stdin).get("tool_input", {}).get("file_path", ""))' 2>/dev/null)

if [ -z "$file" ]; then
  echo "Hook run-tests : fichier modifié illisible, tests non lancés" >&2
  exit 0
fi

case "$file" in
  *.py|*.html|*.toml|*.ini|*.cfg) ;;
  *) exit 0 ;;
esac

out=$(uv run pytest -q -x 2>&1)
code=$?

# 5 = aucun test collecté (début de projet) : pas bloquant
if [ $code -ne 0 ] && [ $code -ne 5 ]; then
  echo "❌ Tests en échec après modification de $file :" >&2
  echo "$out" | tail -40 >&2
  exit 2
fi

echo "$out" | tail -1
exit 0
