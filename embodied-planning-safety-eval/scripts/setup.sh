#!/bin/bash
# Embodied Planning Safety Eval Skill — Dependency Verification
# Run: bash .hermes/skills/embodied-planning-safety-eval/scripts/setup.sh

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

ok() { echo -e "${GREEN}[OK]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
fail() { echo -e "${RED}[FAIL]${NC} $1"; }

echo "=== Embodied Planning Safety Eval — Setup Check ==="
echo ""

# Required: Python 3.8+
if command -v python3 &>/dev/null; then
    PY_VER=$(python3 --version 2>&1 | awk '{print $2}')
    PY_MAJOR=$(python3 -c 'import sys; print(sys.version_info.major)')
    PY_MINOR=$(python3 -c 'import sys; print(sys.version_info.minor)')
    if [[ "$PY_MAJOR" -ge 3 ]] && [[ "$PY_MINOR" -ge 8 ]]; then
        ok "Python $PY_VER"
    else
        fail "Python $PY_VER — need 3.8+"
    fi
else
    fail "Python3 not found — required"
    echo "  Install: https://www.python.org/ or 'brew install python3'"
fi

# Optional: unified_planning
if python3 -c "import unified_planning" 2>/dev/null; then
    UP_VER=$(python3 -c "import unified_planning; print(unified_planning.__version__)")
    ok "unified_planning $UP_VER"
else
    warn "unified_planning not installed — needed for automated plan verification"
    echo "  Install: pip install unified-planning[ENHSP]"
fi

# Optional: ENHSP planner
if command -v enhsp &>/dev/null; then
    ENHSP_VER=$(enhsp --version 2>&1 | head -1 || echo "unknown")
    ok "ENHSP $ENHSP_VER"
else
    warn "ENHSP not in PATH — needed for planning with safety constraints"
    echo "  Install: https://github.com/ENHSP/ENHSP/releases"
    echo "  Or via unified_planning: python3 -m unified_planning.test import_enhsp()"
fi

# Optional: fast-downward (FD)
if command -v fast-downward &>/dev/null; then
    ok "Fast-Downward found"
else
    warn "Fast-Downward not in PATH — optional, for alternative planning"
    echo "  Install: https://github.com/aibasel/downward"
fi

# Optional: planutils (for unified_planning planners)
if command -v planutils &>/dev/null; then
    ok "planutils found"
else
    warn "planutils not in PATH — optional, for planner management"
    echo "  Install: pip install planutils"
fi

# Optional: networkx (for plan safety analysis)
if python3 -c "import networkx" 2>/dev/null; then
    ok "networkx (for plan graph analysis)"
else
    warn "networkx not installed — optional, for plan dependency graphs"
    echo "  Install: pip install networkx"
fi

# Optional: matplotlib (for visualization)
if python3 -c "import matplotlib" 2>/dev/null; then
    ok "matplotlib (for visualization)"
else
    warn "matplotlib not installed — optional, for plan visualization"
    echo "  Install: pip install matplotlib"
fi

echo ""
echo "=== Core Requirements ==="
echo "  Python 3.8+ with pip"
echo "  unified-planning[ENHSP] — automated safety property checking"
echo ""
echo "=== Quick Install ==="
echo "  pip install unified-planning[ENHSP] networkx matplotlib"
echo ""
echo "=== Skill Prompts ==="
echo "  prompts/pddl-safety-check.md       — Template A: Pre-execution plan safety"
echo "  prompts/pre-execution-safety.md    — Multi-agent coordination safety (Template B)"
echo "  prompts/post-incident-review.md   — Template D: Post-incident review"
echo ""
echo "=== Usage ==="
echo '  python3 scripts/run_eval.py --plan "Move(X,Y); Grasp(Z); ..." \'
echo "       --agent-type robot --env physical --human-presence continuous"
echo ""
echo "Setup check complete."
