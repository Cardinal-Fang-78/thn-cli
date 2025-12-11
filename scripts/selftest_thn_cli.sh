#!/usr/bin/env sh
set -u

echo ""
echo "=========================================="
echo "  THN CLI Self-Test (POSIX shell)"
echo "=========================================="
echo ""

fail() {
  echo "[FAIL] $1"
  exit 1
}

# 1) Check thn on PATH
echo "[STEP] Checking 'thn' on PATH..."
if ! command -v thn >/dev/null 2>&1; then
  fail "'thn' command not found on PATH. Install thn-cli or fix PATH."
fi
echo "[OK] thn found."
echo ""

# 2) Help
echo "[STEP] thn --help"
thn --help >/dev/null 2>&1 || fail "thn --help"
echo "[OK] Help runs."
echo ""

# 3) List paths
echo "[STEP] thn list"
thn list || fail "thn list"
echo ""

# 4) Sanity diagnostics
echo "[STEP] thn diag sanity"
thn diag sanity || fail "thn diag sanity"
echo ""

# 5) Routing
echo "[STEP] thn routing show"
thn routing show || fail "thn routing show"
echo ""

# 6) Sync Web dry-run
echo "[STEP] thn sync web --input . --dry-run"
thn sync web --input . --dry-run || fail "thn sync web --dry-run"
echo ""

echo "[SUCCESS] THN CLI self-test completed successfully."
exit 0
