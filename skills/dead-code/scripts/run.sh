#!/usr/bin/env bash
# run.sh — detect and report (or fix) dead/unused code across languages.
#
# Usage:
#   run.sh [--fix] [--dir <path>] [--lang <python|ts|js|rust|go|php|ruby>]
#
# Flags:
#   --fix          Apply safe auto-fixes where the tool supports it (ruff --fix,
#                  cargo clippy --fix). Files are never deleted automatically.
#   --dir <path>   Target directory (default: current working directory)
#   --lang <name>  Force a specific language check (skips auto-detection)
#
# Exit codes:
#   0   No dead code found
#   1   Dead code found (findings printed to stdout)
#   2   Setup / tool-not-found error
#   3   No supported language detected

set -euo pipefail

# ── Defaults ────────────────────────────────────────────────────────────────
FIX=0
TARGET_DIR="${PWD}"
FORCE_LANG=""

# ── Argument parsing ─────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --fix)          FIX=1; shift ;;
    --dir)          TARGET_DIR="$2"; shift 2 ;;
    --lang)         FORCE_LANG="$2"; shift 2 ;;
    --help|-h)
      sed -n '2,12p' "$0" | sed 's/^# //'
      exit 0 ;;
    *) echo "error: unknown argument: $1" >&2; exit 2 ;;
  esac
done

cd "$TARGET_DIR"

# ── Helpers ──────────────────────────────────────────────────────────────────
has() { command -v "$1" >/dev/null 2>&1; }

section() { echo; echo "══ $* ══"; }

total_findings=0
tools_used=()
tools_missing=()

add_findings() {
  local count="$1"
  total_findings=$(( total_findings + count ))
}

# ── Language detection ────────────────────────────────────────────────────────
detect_langs() {
  local langs=()
  [[ -n "$FORCE_LANG" ]] && { echo "$FORCE_LANG"; return; }

  [[ -f pyproject.toml || -f setup.py || -f setup.cfg || -f requirements.txt ]] && langs+=(python)
  [[ -f package.json ]] && langs+=(js)
  [[ -f tsconfig.json ]] && langs+=(ts)
  [[ -f Cargo.toml ]] && langs+=(rust)
  [[ -f go.mod ]] && langs+=(go)
  [[ -f composer.json ]] && langs+=(php)
  [[ -f Gemfile ]] && langs+=(ruby)

  # Fallback: scan git-tracked extensions
  if [[ ${#langs[@]} -eq 0 ]] && has git && git rev-parse --git-dir >/dev/null 2>&1; then
    local exts
    exts=$(git ls-files | grep -oE '\.[a-zA-Z]+$' | sort | uniq -c | sort -rn | head -5)
    echo "$exts" | grep -q '\.py$'   && langs+=(python)
    echo "$exts" | grep -q '\.ts$'   && langs+=(ts)
    echo "$exts" | grep -q '\.js$'   && langs+=(js)
    echo "$exts" | grep -q '\.go$'   && langs+=(go)
    echo "$exts" | grep -q '\.rs$'   && langs+=(rust)
    echo "$exts" | grep -q '\.php$'  && langs+=(php)
    echo "$exts" | grep -q '\.rb$'   && langs+=(ruby)
  fi

  printf '%s\n' "${langs[@]}"
}

mapfile -t LANGS < <(detect_langs | sort -u)

if [[ ${#LANGS[@]} -eq 0 ]]; then
  echo "error: no supported language detected in ${TARGET_DIR}" >&2
  exit 3
fi

echo "Detected language(s): ${LANGS[*]}"
echo "Target: ${TARGET_DIR}"
[[ $FIX -eq 1 ]] && echo "Mode: fix (auto-applying safe fixes)"
echo "─────────────────────────────────────────"

# ── Python ───────────────────────────────────────────────────────────────────
run_python() {
  section "Python — ruff + vulture"

  # ruff: unused imports (F401), redefined names (F811), unused variables (F841)
  local ruff_cmd=""
  if has ruff; then
    ruff_cmd="ruff"
  elif has uvx; then
    ruff_cmd="uvx ruff"
  fi

  if [[ -n "$ruff_cmd" ]]; then
    tools_used+=(ruff)
    echo "▸ ruff (F401/F811/F841)"
    local ruff_args=(check --select F401,F811,F841 --output-format=concise)
    [[ $FIX -eq 1 ]] && ruff_args+=(--fix)
    local out
    out=$($ruff_cmd "${ruff_args[@]}" . 2>&1 || true)
    if [[ -n "$out" ]]; then
      echo "$out"
      add_findings "$(echo "$out" | grep -c '\.py:' || true)"
    else
      echo "  ✓ no issues found"
    fi
  else
    tools_missing+=(ruff)
    echo "  ⚠ ruff not found — install with: pip install ruff  or  uv tool install ruff"
  fi

  # vulture: dead functions, classes, methods
  local vulture_cmd=""
  if has vulture; then
    vulture_cmd="vulture"
  elif has uvx; then
    vulture_cmd="uvx vulture"
  fi

  if [[ -n "$vulture_cmd" ]]; then
    tools_used+=(vulture)
    echo "▸ vulture (dead functions/classes, ≥80% confidence)"
    local vout
    vout=$($vulture_cmd . --min-confidence 80 2>&1 || true)
    if [[ -n "$vout" ]]; then
      echo "$vout"
      add_findings "$(echo "$vout" | grep -c '\.py:' || true)"
    else
      echo "  ✓ no issues found"
    fi
  else
    tools_missing+=(vulture)
    echo "  ⚠ vulture not found — install with: pip install vulture  or  uv tool install vulture"
  fi
}

# ── JavaScript / TypeScript ──────────────────────────────────────────────────
run_js_ts() {
  local label="JavaScript/TypeScript"
  [[ " ${LANGS[*]} " =~ " ts " ]] && label="TypeScript"
  section "$label — knip"

  if has knip || (has npx && npx knip --version >/dev/null 2>&1); then
    tools_used+=(knip)
    echo "▸ knip (unused files, exports, types, dependencies)"
    local kout
    kout=$(npx --yes knip --reporter compact 2>&1 || true)
    if [[ -n "$kout" ]]; then
      echo "$kout"
      add_findings "$(echo "$kout" | grep -vc '^$' || true)"
    else
      echo "  ✓ no issues found"
    fi
    if [[ $FIX -eq 1 ]]; then
      echo
      echo "  ℹ knip does not auto-fix — review findings above and remove manually."
    fi
  else
    tools_missing+=(knip)
    echo "  ⚠ knip not available — install with: npm install -g knip  or  npx knip"
  fi
}

# ── Rust ─────────────────────────────────────────────────────────────────────
run_rust() {
  section "Rust — cargo clippy"

  if has cargo; then
    tools_used+=(cargo-clippy)
    echo "▸ cargo clippy (-W dead_code -W unused_imports -W unused_variables)"
    local flags=(clippy -- -W dead_code -W unused_imports -W unused_variables)
    if [[ $FIX -eq 1 ]]; then
      flags=(clippy --fix --allow-dirty -- -W dead_code -W unused_imports)
    fi
    local cout
    cout=$(cargo "${flags[@]}" 2>&1 || true)
    local warnings
    warnings=$(echo "$cout" | grep -E "^warning:" | grep -v "generated [0-9]+ warning" || true)
    if [[ -n "$warnings" ]]; then
      echo "$warnings"
      add_findings "$(echo "$warnings" | wc -l)"
    else
      echo "  ✓ no issues found"
    fi
  else
    tools_missing+=(cargo)
    echo "  ⚠ cargo not found — install Rust from https://rustup.rs"
  fi
}

# ── Go ───────────────────────────────────────────────────────────────────────
run_go() {
  section "Go — staticcheck / go vet"

  if has staticcheck; then
    tools_used+=(staticcheck)
    echo "▸ staticcheck (unused code)"
    local sout
    sout=$(staticcheck ./... 2>&1 || true)
    local relevant
    relevant=$(echo "$sout" | grep -E "U[0-9]{4}|unused|declared and not used" || true)
    if [[ -n "$relevant" ]]; then
      echo "$relevant"
      add_findings "$(echo "$relevant" | wc -l)"
    else
      echo "  ✓ no issues found"
    fi
  elif has go; then
    tools_used+=(go-vet)
    echo "▸ go vet (declared but not used)"
    local gout
    gout=$(go vet ./... 2>&1 || true)
    local relevant
    relevant=$(echo "$gout" | grep -E "unused|declared and not used" || true)
    if [[ -n "$relevant" ]]; then
      echo "$relevant"
      add_findings "$(echo "$relevant" | wc -l)"
    else
      echo "  ✓ no issues found"
    fi
  else
    tools_missing+=(go)
    echo "  ⚠ go not found in PATH"
  fi
}

# ── PHP ──────────────────────────────────────────────────────────────────────
run_php() {
  section "PHP — phpstan"

  local phpstan=""
  [[ -f vendor/bin/phpstan ]] && phpstan="vendor/bin/phpstan"
  has phpstan && phpstan="phpstan"

  if [[ -n "$phpstan" ]]; then
    tools_used+=(phpstan)
    echo "▸ phpstan (unused variables, dead code)"
    local pout
    pout=$($phpstan analyse --level=5 --error-format=table 2>&1 || true)
    local relevant
    relevant=$(echo "$pout" | grep -iE "unused|dead|never used|never called" || true)
    if [[ -n "$relevant" ]]; then
      echo "$relevant"
      add_findings "$(echo "$relevant" | wc -l)"
    else
      echo "  ✓ no dead code issues found at level 5"
    fi
  else
    tools_missing+=(phpstan)
    echo "  ⚠ phpstan not found — install with: composer require --dev phpstan/phpstan"
  fi
}

# ── Ruby ─────────────────────────────────────────────────────────────────────
run_ruby() {
  section "Ruby — rubocop"

  if has rubocop; then
    tools_used+=(rubocop)
    echo "▸ rubocop (Lint/Unused*, Style/RedundantAssignment)"
    local cops="Lint/UnusedMethodArgument,Lint/UnusedBlockArgument,Style/RedundantAssignment"
    local rout
    rout=$(rubocop --only "$cops" --format progress 2>&1 || true)
    if echo "$rout" | grep -qE "^[^0].*offenses?"; then
      echo "$rout"
      add_findings "$(echo "$rout" | grep -cE "^[CW]:" || true)"
    else
      echo "  ✓ no issues found"
    fi
  else
    tools_missing+=(rubocop)
    echo "  ⚠ rubocop not found — install with: gem install rubocop"
  fi
}

# ── Dispatch ──────────────────────────────────────────────────────────────────
for lang in "${LANGS[@]}"; do
  case "$lang" in
    python) run_python ;;
    ts|js)  ;;  # handled together below
    rust)   run_rust ;;
    go)     run_go ;;
    php)    run_php ;;
    ruby)   run_ruby ;;
  esac
done

# Run JS/TS once even if both detected
if [[ " ${LANGS[*]} " =~ " ts " || " ${LANGS[*]} " =~ " js " ]]; then
  run_js_ts
fi

# ── Summary ───────────────────────────────────────────────────────────────────
echo
echo "═════════════════════════════════════════"
echo "  Dead code scan complete"
echo "  Total findings : ${total_findings}"
echo "  Tools used     : ${tools_used[*]:-none}"
[[ ${#tools_missing[@]} -gt 0 ]] && echo "  Tools missing  : ${tools_missing[*]} (install for fuller coverage)"
echo "═════════════════════════════════════════"

[[ $total_findings -gt 0 ]] && exit 1 || exit 0
