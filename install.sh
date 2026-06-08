#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source_root="$repo_dir/skills"
skills_dir="${CODEX_HOME:-$HOME/.codex}/skills"
force=false
requested=()

for arg in "$@"; do
  if [[ "$arg" == "--force" ]]; then
    force=true
  else
    requested+=("$arg")
  fi
done

if [[ ${#requested[@]} -eq 0 ]]; then
  while IFS= read -r skill_file; do
    requested+=("$(basename "$(dirname "$skill_file")")")
  done < <(find "$source_root" -mindepth 2 -maxdepth 2 -name SKILL.md -print | sort)
fi

if [[ ${#requested[@]} -eq 0 ]]; then
  printf 'No skills found under %s\n' "$source_root" >&2
  exit 1
fi

mkdir -p "$skills_dir"

for skill_name in "${requested[@]}"; do
  source_dir="$source_root/$skill_name"
  target_dir="$skills_dir/$skill_name"

  if [[ ! -f "$source_dir/SKILL.md" ]]; then
    printf 'Skill not found: %s\n' "$skill_name" >&2
    exit 1
  fi

  if [[ -e "$target_dir" && "$force" != true ]]; then
    printf 'Skill already exists: %s\nRun %s --force %s to replace it.\n' \
      "$target_dir" "$0" "$skill_name" >&2
    exit 1
  fi

  if [[ -e "$target_dir" ]]; then
    rm -rf "$target_dir"
  fi
  cp -R "$source_dir" "$target_dir"
  printf 'Installed %s to %s\n' "$skill_name" "$target_dir"
done

printf 'Restart your agent runtime to discover the installed skills.\n'
