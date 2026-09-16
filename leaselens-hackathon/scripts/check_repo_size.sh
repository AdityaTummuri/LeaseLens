#!/bin/bash
# LeaseLens Repository Size Audit
# Verifies the repo stays under the 10MB hackathon limit.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
MAX_SIZE_KB=10240  # 10MB in KB

echo "═══════════════════════════════════════════════"
echo "  LeaseLens Repository Size Audit"
echo "═══════════════════════════════════════════════"
echo ""

# Check if .gitignore excludes critical dirs
echo "📋 .gitignore validation:"
for pattern in node_modules venv .env dist "*.pdf"; do
    if grep -q "$pattern" "$REPO_ROOT/.gitignore" 2>/dev/null || grep -q "$pattern" "$REPO_ROOT/../.gitignore" 2>/dev/null; then
        echo "   ✅ $pattern excluded"
    else
        echo "   ❌ WARNING: $pattern NOT in .gitignore!"
    fi
done
echo ""

# Measure tracked files (what would be in the repo)
echo "📦 Repository content analysis:"
cd "$REPO_ROOT"

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    # If git is initialized, measure tracked + untracked (respecting .gitignore)
    TOTAL_SIZE=$(git ls-files -z --others --cached --exclude-standard | \
                 xargs -0 du -sk 2>/dev/null | \
                 awk '{total+=$1} END {print total}')
    echo "   Git-tracked content: ${TOTAL_SIZE:-0}KB"
else
    # Fallback: measure everything except ignored dirs
    TOTAL_SIZE=$(du -sk --exclude=node_modules --exclude=venv --exclude=.venv \
                        --exclude=dist --exclude=.git --exclude=.env \
                        "$REPO_ROOT" 2>/dev/null | awk '{print $1}')
    echo "   Project content (excl. ignored): ${TOTAL_SIZE:-0}KB"
fi

echo ""

# Size by directory
echo "📊 Size breakdown by directory:"
for dir in backend frontend scripts; do
    if [ -d "$REPO_ROOT/$dir" ]; then
        DIR_SIZE=$(du -sk "$REPO_ROOT/$dir" --exclude=node_modules \
                   --exclude=venv --exclude=dist 2>/dev/null | awk '{print $1}')
        echo "   $dir/: ${DIR_SIZE}KB"
    fi
done
echo ""

# Frontend build size (if built)
if [ -d "$REPO_ROOT/frontend/dist" ]; then
    DIST_SIZE=$(du -sk "$REPO_ROOT/frontend/dist" | awk '{print $1}')
    echo "🏗️  Frontend build output: ${DIST_SIZE}KB"
    echo "   (This is excluded from git via .gitignore)"
    echo ""
fi

# Verdict
echo "═══════════════════════════════════════════════"
if [ "${TOTAL_SIZE:-0}" -lt "$MAX_SIZE_KB" ]; then
    echo "✅ PASS: Repository is ${TOTAL_SIZE:-0}KB / ${MAX_SIZE_KB}KB ($(( MAX_SIZE_KB - ${TOTAL_SIZE:-0} ))KB headroom)"
else
    echo "❌ FAIL: Repository is ${TOTAL_SIZE:-0}KB / ${MAX_SIZE_KB}KB ($(( ${TOTAL_SIZE:-0} - MAX_SIZE_KB ))KB over limit!)"
    exit 1
fi
echo "═══════════════════════════════════════════════"
