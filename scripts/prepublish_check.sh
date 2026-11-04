#!/usr/bin/env bash
# Submission hygiene. Prints PASS/FAIL per check. Exit 1 if any fail.
set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PASS=0
FAIL=0
RESULTS=()

ok() { RESULTS+=("PASS  $1"); PASS=$((PASS + 1)); }
bad() { RESULTS+=("FAIL  $1 — $2"); FAIL=$((FAIL + 1)); }

echo "== prepublish_check =="

if command -v gitleaks >/dev/null 2>&1; then
  if gitleaks git --no-banner --redact -c "$ROOT/.gitleaks.toml" >/tmp/gitleaks-prepublish.log 2>&1; then
    ok "gitleaks (full git history)"
  else
    bad "gitleaks (full git history)" "see /tmp/gitleaks-prepublish.log"
  fi
else
  bad "gitleaks (full git history)" "gitleaks binary not on PATH"
fi

FORBIDDEN=$(git ls-files | grep -E '(^|/)\.env$|\.p8$|GoogleService-Info\.plist$|google-services\.json$|firebase_options\.dart$|revenuecat_api_key\.txt$|revenuecat_key\.dart$' || true)
if [[ -z "$FORBIDDEN" ]]; then
  ok "no .env / *.p8 / GoogleService-Info.plist / firebase_options.dart / revenuecat key files tracked"
else
  bad "tracked secret-named files" "$FORBIDDEN"
fi

if git grep -I -n -E -- '-----BEGIN [A-Z ]*PRIVATE KEY-----' >/tmp/prepublish-pem.txt 2>/dev/null; then
  bad "PEM private key in committed files" "$(head -c 200 /tmp/prepublish-pem.txt)"
else
  ok "no PEM private key blocks in committed files"
fi

python3 - <<'PY'
import re, subprocess, sys
names = ("META_API_KEY", "ASC_KEY_ID", "ASC_ISSUER_ID", "ASC_KEY_PATH", "OPENAI_COMPAT_API_KEY")
pat = re.compile(r"(?:%s)\s*=\s*([^\s#]+)" % "|".join(names))
skip = {".env.example", "scripts/prepublish_check.sh"}
hits = []
files = subprocess.check_output(["git", "ls-files"], text=True).splitlines()
for rel in files:
    if rel in skip:
        continue
    try:
        text = open(rel, encoding="utf-8", errors="ignore").read()
    except OSError:
        continue
    for match in pat.finditer(text):
        value = match.group(1).strip().strip("\"'")
        if len(value) >= 8 and not value.startswith("$"):
            hits.append(f"{rel}: {match.group(0)[:80]}")
if hits:
    print("HITS " + " | ".join(hits[:5]))
    sys.exit(1)
print("OK")
PY
if [[ $? -eq 0 ]]; then
  ok "no assigned API/ASC key values in committed files"
else
  bad "assigned API/ASC key values in committed files" "see scanner output"
fi

if uv run --extra dev pytest -q; then
  ok "tests green"
else
  bad "tests" "pytest failed"
fi

if uv run harness gate flutter_template --build-web >/tmp/prepublish-gate.json; then
  ok "harness gate flutter_template --build-web"
else
  bad "harness gate" "$(tail -c 200 /tmp/prepublish-gate.json)"
fi

python3 - <<'PY'
import pathlib, re, sys
root = pathlib.Path(".").resolve()
text = (root / "README.md").read_text(encoding="utf-8")
missing = []
for match in re.finditer(r"\[([^\]]+)\]\(([^)]+)\)", text):
    url = match.group(2).strip()
    if url.startswith("http://") or url.startswith("https://") or url.startswith("mailto:"):
        continue
    if url.startswith("#"):
        continue
    path = url.split("#", 1)[0]
    if not (root / path).exists():
        missing.append(url)
if missing:
    print("MISSING " + ", ".join(missing))
    sys.exit(1)
print("OK")
PY
if [[ $? -eq 0 ]]; then
  ok "README relative links resolve"
else
  bad "README relative links" "missing files"
fi

REMOTE=$(git remote -v)
if echo "$REMOTE" | grep -q 'github.com'; then
  ok "git remote points to GitHub"
else
  bad "git remote" "$REMOTE"
fi

# Fresh clone of this commit into a temp dir; run README reproduce steps (no sweep).
TMP=$(mktemp -d /tmp/rocket-prepublish-XXXX)
if git clone --quiet "$ROOT" "$TMP/repo"; then
  (
    cd "$TMP/repo"
    uv sync --all-extras >/tmp/prepublish-clone-sync.log 2>&1 \
      && (cd flutter_template && flutter pub get >/tmp/prepublish-clone-pub.log 2>&1) \
      && uv run pytest -q >/tmp/prepublish-clone-pytest.log 2>&1 \
      && uv run harness gate flutter_template --build-web >/tmp/prepublish-clone-gate.log 2>&1
  )
  if [[ $? -eq 0 ]]; then
    ok "fresh clone README reproduce (pytest + gate)"
  else
    bad "fresh clone README reproduce" "logs under /tmp/prepublish-clone-*.log"
  fi
else
  bad "fresh clone" "git clone failed"
fi
rm -rf "$TMP"

echo
echo "----"
for line in "${RESULTS[@]}"; do echo "$line"; done
echo "----"
echo "passed=$PASS failed=$FAIL"
if [[ "$FAIL" -gt 0 ]]; then
  exit 1
fi
exit 0
