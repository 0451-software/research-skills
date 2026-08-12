# Hermes Git Workflow Overhaul — Implementation Plan

**Goal:** Make `git clone --bare` + per-task `git worktree` the canonical Hermes
git pattern so concurrent sub-agents stop stomping each other's branches. Every
new coding task gets its own worktree branched off `main`. Shared object
database means no copy, no re-clone, zero cross-task contamination.

**Architecture:**
- Canonical layout `~/workspace/source/<owner--repo>/` with `.bare/` as the
  shared git dir and sibling dirs `main/`, `agent/<task>/` as worktrees.
- One global shell helper `~/.hermes/bin/wt` with subcommands
  `new | rm | sync | list | bootstrap | repair`. No per-repo PATH pollution.
- Branch naming: `agent/<task>` for all sub-agents.
- For `agent_owned: true` repos (hermes-config, agent-notes), `wt new ... main`
  short-circuits — just commit on `main` directly per existing rule.

**Tech stack:** Bash (helper scripts), a new `git-workflow` skill,
Mnemosyne canonical slot, SKILL/SOUL updates.

**For Hermes:** Use subagent-driven-development to implement this plan
task-by-task. Each task is 2–5 minutes; commit per task; verify per task.

Reference: `bare-worktree-pattern-report.md` (research report in same dir).

---

## Phase 0 — Guardrails and validation framework (must complete before any worktree edit)

### Task 1: Verify bare-repo state of all repos in `~/workspace/source/0451-software/`

**Objective:** Establish ground truth on what is currently a real clone vs bare vs worktree vs nothing. Three categories exist; some are partial conversions from prior sessions.

**Step 1:** For each top-level repo in `~/workspace/source/0451-software/`, capture: layout (`git clone` / bare / mixed), default branch, current HEAD, dirty status. Use a script, not interactive commands — this is the first executable run that exercises the new `wt` helper exists-or-not state.

```bash
for d in ~/workspace/source/0451-software/*/; do
  name=$(basename "$d")
  echo "=== $name ==="
  ( cd "$d" && git rev-parse --show-toplevel 2>/dev/null || echo "<not a git repo>" )
  ( cd "$d" && git rev-parse --is-bare-repository 2>/dev/null || echo "<n/a>" )
  ( cd "$d" && git status --short 2>/dev/null | head -10 || echo "<n/a>" )
done | tee /tmp/wt-pre-baseline.txt
```

**Step 2:** Read the output. Categorize each repo into: (a) needs bootstrap, (b) already bare, (c) already worktree, (d) has WIP that must be preserved, (e) is not a repo.

**Expected output:** ~15-20 repos surveyed. Some `agent-notes`, `hermes-config` flagged `agent_owned: true` per Mnemosyne canonical slot.

**Verify:** `cat /tmp/wt-pre-baseline.txt | head -80` returns sensible output. Commit nothing yet — baseline only.

**Step 3:** Document findings inline in this plan (replace this task with the actual list when run).

**Step 4:** No commit (this is a read-only baseline).

---

## Phase 1 — Bootstrap the `wt` helper

### Task 2: Create `~/.hermes/bin/` directory

**Objective:** Establish the canonical location for Hermes-owned bin scripts. This dir complements `~/bin/` (user-owned) and `~/.local/bin/` (XDG user bin).

**Files:** none — `mkdir` only.

**Step 1:** Create the directory.

```bash
mkdir -p ~/.hermes/bin
```

**Step 2:** Add `~/.hermes/bin` to PATH in `~/.zshrc` (zsh) and `~/.bashrc` if present.

```bash
for f in ~/.zshrc ~/.bashrc; do
  [ -f "$f" ] || continue
  grep -q '\.hermes/bin' "$f" 2>/dev/null || {
    echo '' >> "$f"
    echo '# Hermes Agent bin scripts' >> "$f"
    echo 'export PATH="$HOME/.hermes/bin:$PATH"' >> "$f"
  }
done
```

**Verify:** `ls -la ~/.hermes/bin/` exists; `echo $PATH | grep -q '\.hermes/bin'` succeeds after `source ~/.zshrc`.

**Step 3:** Commit-N/A (no git repo here).

---

### Task 3: Write the `wt` shell helper script

**Objective:** Create `~/.hermes/bin/wt` — the single entry point for bare-repo + worktree operations. ~120 lines of POSIX bash. Smoke-tested with `wt --help`.

**Files:**
- Create: `~/.hermes/bin/wt`
- Create: `~/.hermes/bin/wt-common.sh` (sourced by wt for shared fns)

**Step 1:** Write `~/.hermes/bin/wt-common.sh` first (shared functions).

```bash
#!/usr/bin/env bash
# wt-common.sh — shared helpers for `wt` subcommands. Sourced, not executed.
set -euo pipefail

# Resolve a repo spec like "0451-software/linkdown" or "linkdown" to its
# container dir under ~/workspace/source/. Print absolute path or exit 1.
resolve_repo_dir() {
  local spec="$1"
  case "$spec" in
    */*) echo "$HOME/workspace/source/${spec//\//\/}" ;;
    *)   echo "$HOME/workspace/source/$spec" ;;
  esac | tr -s '/'
}

# Assume the spec and validate the bare layout exists.
require_bare_layout() {
  local repo_dir="$1"
  local bare_dir="$repo_dir/.bare"
  [ -d "$bare_dir" ] || die "no bare layout at $repo_dir (run: wt bootstrap <repo>)"
}

# Print the default branch name (main|master|trunk), falling back to "main".
default_branch() {
  local bare_dir="$1"
  ( cd "$bare_dir" && \
      git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null \
        | sed 's|^origin/||' ) \
    || echo main
}

# Print number of WIP lines in a worktree.
dirty_count() {
  local wt_dir="$1"
  ( cd "$wt_dir" && git status --porcelain 2>/dev/null | wc -l | tr -d ' ' ) \
    || echo 0
}

die() { printf 'wt: %s\n' "$*" >&2; exit 1; }
note() { printf 'wt: %s\n' "$*"; }
```

**Step 2:** Write `~/.hermes/bin/wt` (the dispatcher). Subcommands: `new`, `rm`, `sync`, `list`, `bootstrap`, `repair`, `--help`.

```bash
#!/usr/bin/env bash
# wt — Hermes bare-repo + per-task worktree helper.
#
# Usage:
#   wt bootstrap <repo>          Convert a working clone (or first-time clone)
#                                  into the canonical .bare/ + main/ layout.
#   wt new <repo> <task>         Create a fresh worktree at
#                                  <repo>/agent/<task> on branch agent/<task>
#                                  based on origin/main (or default branch).
#   wt sync <repo>               Fetch origin into the bare repo so origin/main
#                                  is current. (Replaces `git pull`.)
#   wt list [repo]               List worktrees; if <repo> omitted, list all
#                                  bare repos and their worktrees.
#   wt rm <repo> <task> [--force]
#                                Remove the worktree; refuse if it has
#                                  uncommitted changes unless --force.
#                                  Also deletes the local branch.
#   wt repair [repo]             Re-link worktrees whose .git pointer file
#                                  is broken (run after mv).
#
# Repo spec: "0451-software/linkdown" or "linkdown". Expansion rules in
# wt-common.sh::resolve_repo_dir.

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$SCRIPT_DIR/wt-common.sh"

usage() {
  sed -n '2,/^$/p' "$0" | sed 's/^# \{0,1\}//'
  exit "${1:-0}"
}

[ $# -ge 1 ] || usage 1
case "$1" in
  -h|--help|help) usage 0 ;;
esac
sub="$1"; shift

case "$sub" in
  bootstrap) "$0"-impl-bootstrap "$@" ;;
  new)       "$0"-impl-new       "$@" ;;
  sync)      "$0"-impl-sync      "$@" ;;
  list)      "$0"-impl-list      "$@" ;;
  rm|remove) "$0"-impl-rm        "$@" ;;
  repair)    "$0"-impl-repair    "$@" ;;
  *) die "unknown subcommand: $sub (try: bootstrap|new|sync|list|rm|repair)" ;;
esac
```

**Step 3:** Add `wt-impl-*` subcommand handlers at the bottom of the same file (or a separate sourced file). Each implements one verb.

**`wt bootstrap <repo>`:**

```bash
# Creates .bare/, .git file, main/ worktree on origin/HEAD. Detects existing
# working clone and converts it safely.
wt-impl-bootstrap() {
  local spec="${1:?usage: wt bootstrap <repo>}"
  local repo_dir; repo_dir="$(resolve_repo_dir "$spec")"
  local bare_dir="$repo_dir/.bare"

  if [ -d "$bare_dir" ]; then
    note "already bootstrapped: $bare_dir"
    exit 0
  fi

  mkdir -p "$repo_dir"
  local origin_url=""
  if [ -d "$repo_dir/.git" ]; then
    # Existing working clone — read its remote URL, then convert.
    origin_url="$(git -C "$repo_dir" config --get remote.origin.url)"
    note "converting existing clone at $repo_dir (origin: $origin_url)"
    # Move .git aside to .bare (mv is atomic on same filesystem).
    mv "$repo_dir/.git" "$bare_dir"
    ( cd "$bare_dir" && git config core.bare true )
    ( cd "$bare_dir" && git config remote.origin.fetch "+refs/heads/*:refs/remotes/origin/*" )
    # Rewrite the .git pointer in the old location so its working tree still works.
    printf 'gitdir: ./.bare\n' > "$repo_dir/.git"
  elif [ -z "$(ls -A "$repo_dir" 2>/dev/null)" ]; then
    # Empty dir — need to clone. Caller must provide origin URL via env or we'll
    # ask. For automation, prefer wt-bootstrap <repo> <url> form.
    if [ -n "${WT_ORIGIN_URL:-}" ]; then
      origin_url="$WT_ORIGIN_URL"
    else
      die "empty dir at $repo_dir and WT_ORIGIN_URL not set; pass URL as 2nd arg"
    fi
    ( cd "$repo_dir" && git clone --bare "$origin_url" .bare )
    ( cd "$bare_dir" && git config remote.origin.fetch "+refs/heads/*:refs/remotes/origin/*" )
    printf 'gitdir: ./.bare\n' > "$repo_dir/.git"
  else
    die "$repo_dir is non-empty and not a git repo — refusing to bootstrap"
  fi

  # First-time fetch into bare
  ( cd "$bare_dir" && git fetch --all --prune --tags )

  # Detect default branch
  local base; base="$(default_branch "$bare_dir")"

  # Create main/ worktree
  if [ ! -d "$repo_dir/main" ]; then
    ( cd "$bare_dir" && git worktree add "$repo_dir/main" "$base" )
  fi

  note "bootstrapped $spec -> $repo_dir"
  note "default branch: $base"
  note "use: wt sync $spec   to refresh origin/main"
  note "     wt new  $spec <task>  to start a new agent task"
}
```

**`wt new <repo> <task>`:**

```bash
wt-impl-new() {
  local spec="${1:?usage: wt new <repo> <task>}"
  local task="${2:?usage: wt new <repo> <task>}"
  shift 2

  local repo_dir; repo_dir="$(resolve_repo_dir "$spec")"
  require_bare_layout "$repo_dir"
  local bare_dir="$repo_dir/.bare"
  local wt_dir="$repo_dir/agent/$task"
  local branch="agent/$task"
  local base; base="$(default_branch "$bare_dir")"

  # Sync main first so the new worktree sees latest
  ( cd "$bare_dir" && git fetch origin "$base" --prune )

  # Refuse if dir or branch already exists
  [ -e "$wt_dir" ] && die "worktree dir already exists: $wt_dir"
  ( cd "$bare_dir" && git show-ref --verify --quiet "refs/heads/$branch" ) \
    && die "branch $branch already exists in the bare repo"

  ( cd "$bare_dir" && git worktree add "$wt_dir" -b "$branch" "origin/$base" ) \
    || die "git worktree add failed"

  note "worktree: $wt_dir"
  note "branch:   $branch (based on origin/$base)"
  note "cd $wt_dir to begin"
}
```

**`wt sync <repo>`:**

```bash
wt-impl-sync() {
  local spec="${1:?usage: wt sync <repo>}"
  local repo_dir; repo_dir="$(resolve_repo_dir "$spec")"
  require_bare_layout "$repo_dir"
  local bare_dir="$repo_dir/.bare"
  ( cd "$bare_dir" && git fetch --all --prune --tags )
  note "synced $spec $(date -Iseconds)"
}
```

**`wt list [repo]`:**

```bash
wt-impl-list() {
  local spec="${1:-}"
  if [ -z "$spec" ]; then
    # List every bare repo under ~/workspace/source/
    for d in "$HOME/workspace/source"/*/; do
      [ -d "$d/.bare" ] || continue
      wt-impl-list "$(basename "$d")"
      echo
    done
    return
  fi
  local repo_dir; repo_dir="$(resolve_repo_dir "$spec")"
  [ -d "$repo_dir/.bare" ] || die "no bare layout at $repo_dir"
  note "$spec @ $repo_dir"
  ( cd "$repo_dir/.bare" && git worktree list --porcelain \
      | awk -v RS= -v ORS='\n\n' '1' \
      | sed 's/^/  /' )
}
```

**`wt rm <repo> <task> [--force]`:**

```bash
wt-impl-rm() {
  local spec="${1:?usage: wt rm <repo> <task> [--force]}"
  local task="${2:?usage: wt rm <repo> <task> [--force]}"
  shift 2
  local force=""
  [ "${1:-}" = "--force" ] && force=1

  local repo_dir; repo_dir="$(resolve_repo_dir "$spec")"
  require_bare_layout "$repo_dir"
  local bare_dir="$repo_dir/.bare"
  local wt_dir="$repo_dir/agent/$task"
  local branch="agent/$task"

  [ -d "$wt_dir" ] || die "worktree not found: $wt_dir"

  local dirty; dirty="$(dirty_count "$wt_dir")"
  if [ "$dirty" != "0" ] && [ -z "$force" ]; then
    die "worktree has $dirty uncommitted change(s); use --force to discard"
  fi

  ( cd "$bare_dir" && git worktree remove --force "$wt_dir" ) \
    || die "worktree remove failed"
  ( cd "$bare_dir" && git branch -D "$branch" 2>/dev/null || true )
  ( cd "$bare_dir" && git worktree prune )
  note "removed $wt_dir and branch $branch"
}
```

**`wt repair [repo]`:**

```bash
wt-impl-repair() {
  local spec="${1:-}"
  local repo_dir
  if [ -z "$spec" ]; then
    find "$HOME/workspace/source" -name .bare -type d -prune -print \
      | while read -r bare_dir; do
        wt-impl-repair "$(echo "$bare_dir" | sed "s|$HOME/workspace/source/||")"
      done
    return
  fi
  repo_dir="$(resolve_repo_dir "$spec")"
  [ -d "$repo_dir/.bare" ] || die "no bare layout at $repo_dir"
  ( cd "$repo_dir/.bare" && git worktree repair )
  note "repaired worktrees for $spec"
}
```

**Step 4:** Make both files executable; smoke-test.

```bash
chmod +x ~/.hermes/bin/wt ~/.hermes/bin/wt-common.sh
~/.hermes/bin/wt --help   # prints usage
```

**Verify:**
- `~/.hermes/bin/wt` runs without bash errors.
- `wt --help` exits 0 and lists subcommands.
- `wt bootstrap` with no args exits non-zero with usage message.
- Shell script passes `shellcheck ~/.hermes/bin/wt` (or `bash -n` if shellcheck unavailable).

**Commit:** N/A — these are not in a git repo. They'll be picked up by `~/.hermes/sync-profiles.py` if that script syncs the bin dir; otherwise they're local-only.

---

## Phase 2 — Bootstrap the most-used repos

### Task 4: Bootstrap `0451-software/hermes-config` (agent_owned: true)

**Objective:** This is the first canonical conversion. Because hermes-config is `agent_owned: true` per Mnemosyne canonical slot, we still use the bare+worktree layout — multiple sub-agents editing skill files concurrently need the same isolation. Just skip the PR-creation step on shipping.

**Files (operate on):** `~/workspace/source/0451-software/hermes-config/`

**Step 1:** Inspect current state.

```bash
cd ~/workspace/source/0451-software/hermes-config
git rev-parse --is-bare-repository
git status --short
git remote -v
git branch --show-current
```

**Step 2:** If `false` (not bare), run `wt bootstrap 0451-software/hermes-config`.

**Step 3:** If `wt bootstrap` says "no origin URL", set `WT_ORIGIN_URL` and retry. Read the remote URL first: `git config --get remote.origin.url`.

**Step 4:** After bootstrap, verify the layout.

```bash
ls -la ~/workspace/source/0451-software/hermes-config/
git -C ~/workspace/source/0451-software/hermes-config/.bare worktree list
# expect:
#   /Users/agent/workspace/source/0451-software/hermes-config/.bare   (bare)
#   /Users/agent/workspace/source/0451-software/hermes-config/main    <sha> [main]
```

**Step 5:** Smoke-test: `wt new 0451-software/hermes-config test-smoke-task`, make a no-op change, `git -C ~/workspace/source/0451-software/hermes-config/agent/test-smoke-task status`, then `wt rm 0451-software/hermes-config test-smoke-task`.

**Verify:** Test worktree created, can run `git status`, removed cleanly. `git worktree list` returns to just `.bare` + `main`.

**Commit:** Inside the bootstrap, if there were no working-copy changes, no commit needed. If the conversion required committing WIP first, that commit happens on `main` (per `agent_owned: true` rule).

---

### Task 5: Bootstrap `0451-software/agent-notes` (agent_owned: true)

**Objective:** Same as Task 4 but for agent-notes, which is the second `agent_owned: true` repo and frequently has WIP. Important: agent-notes is where the parent session tracks state — preserve uncommitted work.

**Files (operate on):** `~/workspace/source/agent-notes/`

**Step 1:** Capture any uncommitted work BEFORE bootstrap; if dirty, decide: commit on current branch first, or stash.

```bash
cd ~/workspace/source/agent-notes
git status --short
git log --oneline -5
```

**Step 2:** If clean: `wt bootstrap agent-notes`. If dirty with intent: `git add -A && git commit -m "wip: capture before bootstrap"` on the current branch first.

**Step 3:** After bootstrap, the WIP commits live on whatever branch was checked out in the old working tree. To recover them in the new `main/` worktree: `git -C ~/workspace/source/agent-notes/main cherry-pick <sha>` (or branch is already `main` if that was the branch — verify).

**Step 4:** Verify with `wt list agent-notes` and `git status --short` showing clean tree.

**Verify:** Layout is correct; WIP is either committed in the right place or stashed.

**Commit:** inside the workflow per `agent_owned: true` rule.

---

### Task 6: Bootstrap a non-agent_owned repo (e.g. `0451-software/linkdown`)

**Objective:** Prove the pattern works on a PR-driven repo. linkdown has the most documented PR workflow in our skills.

**Files (operate on):** `~/workspace/source/0451-software/linkdown/`

**Step 1:** Same as Task 4 step 1 — inspect, then `wt bootstrap 0451-software/linkdown` if not bare.

**Step 2:** Verify default branch resolves correctly (linkdown might use `main` or may have `master` historically — confirm `wt list` output).

**Step 3:** Test: `wt new 0451-software/linkdown test-linkdown-task`, write a temp file, commit, push the branch to verify remote URLs work.

```bash
wt new 0451-software/linkdown test-linkdown-task
cd ~/workspace/source/0451-software/linkdown/agent/test-linkdown-task
echo "smoke" > /tmp/wt-smoke.txt
git add -A && git commit -m "test: smoke check"
git push -u origin agent/test-linkdown-task
# expect: branch pushed to origin
```

**Step 4:** Clean up: `wt rm 0451-software/linkdown test-linkdown-task` and `git push origin --delete agent/test-linkdown-task` (per internal-repo-dev skill — orphan branches only deleted via GitHub UI normally, but a test branch is fine to push-delete).

**Verify:** Push succeeded (`git ls-remote origin agent/test-linkdown-task` shows it before delete, empty after). Worktree removed cleanly.

**Commit:** N/A — test branch deleted.

---

### Task 7: For all remaining `~/workspace/source/<owner>/<repo>/` repos that are not bootstrapped, queue them with `wt-bootstrap --dry-run` and a TODO list

**Objective:** Don't lose track of which repos still need conversion. Some are scratch (kanban workspaces, hermes-config vendor copies) and don't need conversion.

**Files:**
- Create: `~/workspace/source/WORKTREE_MIGRATION_TODO.md` (or similar)

**Step 1:** Loop through all `~/workspace/source/<owner>/<repo>/` style dirs (skipping agent-notes, hermes-config, linkdown already done). For each: check `git rev-parse --is-bare-repository`. Skip scratch dirs (`kanban/`, `hermes-config.bak/`, `.bak*`).

**Step 2:** For each remaining real repo, write a 2-line entry: `<owner/repo>` + `bootstrap status: pending | done | skip (because scratch)`. Save to `~/workspace/source/WORKTREE_MIGRATION_TODO.md`.

**Step 3:** Do NOT bootstrap them in this task — just inventory. Bootstrap each one in subsequent tasks to keep each task bite-sized.

**Verify:** File exists with sane entries. No repo overwrites happened.

**Commit:** N/A — file is outside any repo (place under `~/workspace/` or use a `git init`'d dir if you want version tracking).

---

## Phase 3 — Author the new `git-workflow` skill and update the canonical skills

### Task 8: Write `/Users/agent/.hermes/skills/git-workflow/SKILL.md`

**Objective:** Create the skill the Coder SOUL already references but doesn't exist. This becomes the single source of truth for "how an agent should set up its git workspace." Skills load when triggered; SOUL.md git-workflow section will be rewritten to point here.

**Files:**
- Create: `/Users/agent/.hermes/skills/git-workflow/SKILL.md`

**Step 1:** Write the SKILL.md frontmatter + body. Frontmatter targets the description field so the skill auto-loads when an agent says "I need to work on a repo."

```markdown
---
name: git-workflow
description: "Hermes bare-repo + per-task worktree workflow. Use when an agent starts a new coding task that touches a git repo, when picking up a Kanban task, when the orchestrator is dispatching a coder/inspector/adversarial-reviewer sub-agent, or when a sub-agent reports it needs 'a fresh checkout'. Loads the canonical layout, the `wt` helper, and the agent/<task> branch convention. Replaces the `## Git Workflow` section in every SOUL.md."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    category: git
    tags: [git, worktree, bare-repo, subagent, kanban, branch]
---
```

**Step 2:** Body: "When to Use", "Canonical Layout", "Setup (one-time per repo)", "Per-task workflow", "Sub-agent dispatch template", "Pitfalls".

**Step 3:** Cross-link: `internal-repo-dev`, `subagent-driven-development`, `kanban-codex-lane`, `kanban`, `hermes-config`.

**Step 4:** Validate YAML frontmatter parses and metadata.hermes.category is "git".

**Verify:** `cat SKILL.md | head -20` shows valid frontmatter.

**Commit:** If the SOUL.md update happens via the hermes-config sync flow (it does — see Task 12), then this skill ships through that pipeline. Otherwise commit to the worktree.

---

### Task 9: Update `internal-repo-dev/SKILL.md` Branch Convention section

**Objective:** Replace the `## Branch Convention` block (lines ~37–54) with bare+worktree pattern. Keep the `### Pre-push decision tree` and orphan-branch recipe intact — they're orthogonal.

**Files:**
- Modify: `/Users/agent/.hermes/skills/github/internal-repo-dev/SKILL.md`

**Step 1:** Find the `## Branch Convention` heading.

**Step 2:** Replace lines `## Branch Convention` through the workflow block inclusive with:

```markdown
## Branch Convention

All 0451-software repos use a **bare-repo + per-task worktree layout**.
The canonical helper is `wt` (from `~/.hermes/bin/wt`); see the
`git-workflow` skill for full mechanics. Branch prefix:

| Prefix | Use |
|--------|-----|
| `agent/<task>` | Every agent task — created by `wt new <repo> <task>` |
| `feat/` | Reserved for human-authored branches |
| `fix/` | Reserved for human-authored hotfix branches |
| `chore/`, `docs/` | Reserved for human-authored tooling/docs |

**Workflow (must do before any code change):**

```bash
# 1. Bootstrap once per repo (skipped after first run)
wt bootstrap 0451-software/<repo>

# 2. Sync origin/main so the new branch is current
wt sync 0451-software/<repo>

# 3. Create the task worktree
wt new 0451-software/<repo> <task-name>
# → creates branch agent/<task-name> off origin/main in
#   ~/workspace/source/0451-software/<repo>/agent/<task-name>/

# 4. cd in, do work, commit, push
cd ~/workspace/source/0451-software/<repo>/agent/<task-name>
git add -A && git commit -m "..."
git push -u origin agent/<task-name>
gh pr create --base main --head agent/<task-name> --title "..." --body "..."

# 5. After PR merge — clean up
wt rm 0451-software/<repo> <task-name>
```

**agent_owned exception:** for repos with the `agent_owned: true`
custom property (currently hermes-config, agent-notes), skip the PR
step. Use `wt new <repo> <task>`, commit on `agent/<task>`, then after
merge fast-forward `main` and `wt rm`. Direct push to `main` remains
disallowed by branch protection; the worktree-per-task pattern still
gives you isolation.
```

**Step 3:** Keep `### Pre-push decision tree` and beyond untouched — they reference the branch name not the layout.

**Step 4:** Verify diff scope: only the `## Branch Convention` block changes. Lines before and after preserved.

**Verify:** `diff` between original and new shows only the targeted section.

**Commit:** Inside the hermes-config worktree per `agent_owned: true` rule.

---

### Task 10: Update `subagent-driven-development/SKILL.md` worktree pitfalls

**Objective:** Replace the two existing pitfalls (`shared-worktree stomp` and `subagent's uncommitted untracked files contaminate other branches`) with the new canonical workflow. Preserve the "verification before belief" content and the 16/16 worked example.

**Files:**
- Modify: `/Users/agent/.hermes/skills/software-development/subagent-driven-development/SKILL.md`

**Step 1:** Around lines 372–377 ("Dispatch parallel subagents that touch the same files"), replace the worktree examples with explicit `wt new` invocations.

**Step 2:** Around lines 399–417 ("Dispatch protocol that actually works on this host"), update to canonical helper:

```markdown
**Dispatch protocol that works on this host (2026-08-11):**

Every parallel sub-agent now gets its own worktree via `wt new`. The
shared-worktree stomps documented in the 2026-06-15 slide-share
session were diagnosed and resolved by switching to the bare-repo +
worktree-per-task layout. The canonical command is:

```bash
# Parent: scaffold N worktrees off origin/main in parallel
for n in feat-A feat-B feat-C; do
  wt new 0451-software/<repo> "$n"
done

# Parent: dispatch sub-agents with the worktree path baked into the brief
delegate_task(tasks=[...3 tasks...])
# each sub-agent: cd ~/workspace/source/0451-software/<repo>/agent/<feat-X>
#                 do work, commit, push, PR, then wt rm
```

**Belt-and-braces brief template:**

> "Final-3 mandatory:
> 1. `git add -A && git commit -m '<type>(<scope>): <description> (<task-id>)'` if anything is unstaged
> 2. `git push -u origin agent/<task-id>` (or `git push origin agent/<task-id>` if upstream exists)
> 3. `gh pr create --base main --head agent/<task-id> --title '...' --body-file /tmp/pr-N-body.md` then report the PR URL
>
> If you hit the iteration limit before all 3 are done, push whatever you have on the branch — the orchestrator will finalize. The branch tip MUST be on `origin/agent/<task-id>` before you exit.
>
> Your workdir is `/Users/agent/workspace/source/0451-software/<repo>/agent/<task-id>` — created for you by `wt new`. Do NOT clone the repo again. Do NOT use `git checkout main` in this worktree. Do NOT touch other agents' worktrees (~/workspace/source/0451-software/<repo>/agent/<other-task>/). When done, `wt rm 0451-software/<repo> <task-id>`."
```

**Step 3:** Replace the obsolete 16-subagent shell loop (lines 491–514) with a 1-line reference: "See `subagent-batch-recipe.md` for the older shell loop — superseded by `wt new` + `delegate_task`."

**Step 4:** Verify the file still loads (frontmatter intact, no broken cross-refs).

**Verify:** `skill_view(name='subagent-driven-development')` succeeds.

**Commit:** Inside hermes-config worktree.

---

### Task 11: Update `kanban-codex-lane/SKILL.md` and `devops/kanban/SKILL.md`

**Objective:** Both skills reference worktrees but use ad-hoc `git worktree add` invocations. Replace with `wt new` / `wt rm`.

**Files:**
- Modify: `/Users/agent/.hermes/skills/autonomous-ai-agents/kanban-codex-lane/SKILL.md`
- Modify: `/Users/agent/.hermes/skills/devops/kanban/SKILL.md`

**Step 1 (kanban-codex-lane):** In the "Required Worktree and Branch Pattern" section, replace the manual `git worktree add -b "$BRANCH" "$WORKTREE" "$BASE"` block with:

```bash
wt new 0451-software/<repo> codex-${SAFE_TASK}
# → creates branch agent/<prefix>/codex-<task> at ~/workspace/source/0451-software/<repo>/agent/codex-<task>/
```

**Cleanup:** Replace `git -C "$REPO" worktree remove "$WORKTREE"` + `git -C "$REPO" branch -D "$BRANCH"` with `wt rm 0451-software/<repo> codex-<task>`.

**Step 2 (devops/kanban):** The kanban skill already routes to a `worktree:` protocol. Replace the inline `git worktree add` instruction with `wt new`. Keep the table that lists worktree as the execution surface.

**Step 3:** Verify both files still pass frontmatter validation.

**Verify:** both `skill_view` succeed.

**Commit:** Inside hermes-config worktree.

---

## Phase 4 — Update all SOUL.md git-workflow sections to point at the skill

### Task 12: Update the shared `/Users/agent/.hermes/SOUL.md` `## Git Workflow` section

**Objective:** Reduce the canonical Git Workflow section to a pointer to the new `git-workflow` skill. The long-form lives in the skill where it can be edited once and benefit every profile.

**Files:**
- Modify: `/Users/agent/.hermes/SOUL.md`

**Step 1:** Find `## Git Workflow` (line 105).

**Step 2:** Replace the entire section (lines 105–123) with:

```markdown
## Git Workflow

The canonical Hermes git workflow uses a bare-repo + per-task worktree
layout. Every coding task gets its own isolated worktree branched off
`main` via the `wt` helper. Concurrent sub-agents never step on each
other's branches. See the **`git-workflow`** skill for the full
mechanics, the canonical layout (`~/workspace/source/<owner--repo>/.bare/`),
the `wt new / rm / sync / list / bootstrap / repair` command surface, and
the `agent/<task>` branch convention.

**Hard rules that survive the skill-load:**

- Destructive git operations are forbidden. Never force-push. Never
  rewrite shared history. Never modify branch-protection rules. If a
  path requires destructive action, stop and ask G.
- For `agent_owned: true` repos (currently hermes-config, agent-notes),
  follow the same `wt new` pattern but skip the PR step — commit on
  `agent/<task>` and fast-forward into `main` after review.
- Branch prefix `agent/` is reserved for agent-created branches; do not
  reuse it for human-authored work.
```

**Step 3:** Verify nothing else references these lines (other SOUL.md files do, but each is updated separately).

**Verify:** Section is concise, all hard rules preserved, points at the skill.

**Commit:** Inside hermes-config worktree (agent_owned: true).

---

### Task 13: Update all per-profile SOUL.md `## Git Workflow` sections in lockstep

**Objective:** Each profile's SOUL.md has the same `## Git Workflow` block as the shared one (lines 105–123 in `/Users/agent/.hermes/SOUL.md`). Apply the same rewrite to each. The Coder profile has a different wording that says "this is the `git-workflow` skill, replaces local section" — make sure that reference still resolves to the now-existing skill.

**Files to modify (per profile):**
- `/Users/agent/.hermes/profiles/adversarial-reviewer/SOUL.md`
- `/Users/agent/.hermes/profiles/coder/SOUL.md`
- `/Users/agent/.hermes/profiles/erica/SOUL.md`
- `/Users/agent/.hermes/profiles/marketing/SOUL.md`
- `/Users/agent/.hermes/profiles/orchestrator/SOUL.md`
- `/Users/agent/.hermes/profiles/qa/SOUL.md`
- `/Users/agent/.hermes/profiles/researcher/SOUL.md`
- `/Users/agent/.hermes/profiles/sre/SOUL.md`

**Step 1:** List per-profile SOUL.md and check each has `## Git Workflow`.

```bash
for f in /Users/agent/.hermes/profiles/*/SOUL.md; do
  grep -l "## Git Workflow" "$f"
done
```

**Step 2:** For each file: replace `## Git Workflow` section with the same compact version as Task 12 (or keep the erica profile's "user is Erica, primary user" framing — adapt wording only where it changes semantics; preserve all hard rules).

**Step 3:** For the Coder profile specifically, remove the "git-workflow skill doesn't exist" placeholder text — the skill now exists.

**Step 4:** Run a final grep to confirm every profile has the rewritten compact section.

**Verify:** `grep -l "git-workflow" /Users/agent/.hermes/profiles/*/SOUL.md /Users/agent/.hermes/SOUL.md | wc -l` returns at least 9 (8 profiles + shared).

**Commit:** Inside hermes-config worktree.

---

## Phase 5 — Update Mnemosyne canonical facts and project-local instruction files

### Task 14: Add Mnemosyne canonical slot for the new git workflow

**Objective:** Make the canonical slot `model:workflow::git-workflow` available so every agent session loads the pattern via Mnemosyne recall instead of relying on SOUL.md text being read.

**Step 1:** Use `mnemosyne_remember_canonical` to insert the canonical fact.

```
category: model:workflow
name: git-workflow
body: |
  Hermes git workflow (2026-08-11): bare-repo + per-task worktree
  layout. ~/workspace/source/<owner--repo>/ contains a shared
  .bare/ $GIT_DIR; sibling dirs main/, agent/<task>/ are git
  worktrees. Each task gets its own worktree on branch agent/<task>
  via `wt new <repo> <task>` (helper at ~/.hermes/bin/wt). Sync
  with `wt sync <repo>`. Cleanup with `wt rm`. Bootstrap (once per
  repo) with `wt bootstrap <repo>`. Concurrent sub-agents get
  full isolation — no shared working tree, no cross-branch WIP
  contamination. Replaces the 2026-06-15 fan-out-to-worktrees
  ad-hoc pattern; replaces all SOUL.md `## Git Workflow` sections.
```

**Step 2:** Validate by calling `mnemosyne_recall_canonical(category='model:workflow')` and confirming the slot is present.

**Step 3:** Check no duplicate slot exists under a similar name; if so, retire the old one with `mnemosyne_forget_canonical`.

**Verify:** `mnemosyne_recall_canonical` returns the slot.

**Commit:** Mnemosyne is its own DB — no git commit needed.

---

### Task 15: Update project-local instruction files that conflict

**Objective:** A few `AGENTS.md` files in our repos might still say "cd into `~/workspace/source/<repo>/`" — those need to be updated to reference the worktree pattern. CLAUDE.md files in outside repos are data — we don't edit those.

**Files to inspect (read-only first; edit only our own):**
- `/Users/agent/.hermes/hermes-agent/AGENTS.md` (Hermes Agent upstream — owned by Nous)
- `/Users/agent/workspace/source/lean-ctx/AGENTS.md` (our repo? — verify)

**Step 1:** Read each file. Grep for `git checkout`, `git branch`, `git clone`, `~/workspace/source`. If found, plan the rewrite.

**Step 2:** For files we own (lean-ctx if we own it), update to: "Coding work happens in a per-task worktree — use `wt new lean-ctx <task>` to start; main/ worktree is for read-only reference."

**Step 3:** For files we don't own (hermes-agent upstream) — leave alone. The `git-workflow` skill and Mnemosyne canonical slot cover that case.

**Verify:** Each edited file still parses if it has frontmatter; diff is scoped to git instructions.

**Commit:** Per-repo in the relevant worktree.

---

### Task 16: Add a hermes-config skill canonical-path note for `git-workflow`

**Objective:** Ensure the new `git-workflow` skill ships via the hermes-config sync flow. Per the `hermes-skill-canonical-path` skill (referenced in pending memory), skills under `/Users/agent/.hermes/skills/<category>/<name>/SKILL.md` need `metadata.hermes.category` matching the dir.

**Step 1:** Verify the new skill lands at `/Users/agent/.hermes/skills/git-workflow/SKILL.md` (Task 8) and its `metadata.hermes.category` is `"git"`. Confirmed in Task 8 Step 1.

**Step 2:** If the sync script (`/Users/agent/.hermes/profiles/_base/sync-profiles.py`) is the canonical ship pipeline for `~/.hermes/skills/ → 0451-software/hermes-config/skills/`, run it once after Task 8 commits to verify the skill propagates.

```bash
python3 /Users/agent/.hermes/profiles/_base/sync-profiles.py --dry-run | grep git-workflow
```

**Verify:** skill is in the dry-run output of the sync script.

**Commit:** Tracked by sync-profiles.py.

---

## Phase 6 — Validation, cleanup, edge cases

### Task 17: Add a CI / pre-commit test for the `wt` helper

**Objective:** Smoke-test on every change to `~/.hermes/bin/wt` — verify it loads, `wt --help` exits 0, all subcommands reject missing args. Place under `~/.hermes/scripts/` or skip if no test infra.

**Files:**
- Create: `/Users/agent/.hermes/scripts/test-wt.sh`

**Step 1:** Write a 20-line bash test that:

- Sources `wt-common.sh` (mock the die/note functions to capture output)
- Calls each impl function with no args; asserts non-zero exit
- Calls `wt --help`; asserts zero exit
- Calls `wt` with no args; asserts non-zero exit and usage message
- Mocks `git` and asserts `wt new` calls `git fetch` + `git worktree add` in the right order

**Step 2:** Make executable. Run.

```bash
chmod +x /Users/agent/.hermes/scripts/test-wt.sh
/Users/agent/.hermes/scripts/test-wt.sh
```

**Verify:** all assertions pass; exit 0.

**Commit:** Inside hermes-config if scripts live there.

---

### Task 18: Migrate the SURVIVING `~/workspace/source/<owner>/<repo>` clones (per the Phase 0 baseline)

**Objective:** Walk the migration TODO file. For each "pending" repo, run `wt bootstrap`. Bite-sized: ONE repo per task in subsequent passes.

**Files:** `~/workspace/source/WORKTREE_MIGRATION_TODO.md` (from Task 7).

**Step 1:** Pick the next pending repo from the TODO list.

**Step 2:** Run `wt bootstrap`. Same pattern as Task 4/5/6.

**Step 3:** Verify the layout, list worktrees, check that the existing human-authored branches still resolve to remote heads.

**Step 4:** Update the TODO file: change `bootstrap status: pending` to `done`.

**Step 5:** Repeat per repo as separate tasks (future plan instances, or roll up multiple small repos into one task).

**Verify:** List shrinks to zero pending entries over time.

**Commit:** Per repo, per its agent_owned-or-not rule.

---

### Task 19: Update shell aliases and CronJobs that referenced the old paths

**Objective:** Audit `~/.zshrc`, `~/.bashrc`, crontab entries, and any shell scripts under `~/.hermes/scripts/` that hardcode `~/workspace/source/<repo>/` — none should exist after migration, but check.

**Files:**
- `~/.zshrc`, `~/.bashrc`
- `/Users/agent/workspace/bin/*` (5 scripts)
- `/Users/agent/.hermes/scripts/*`
- `crontab -l`

**Step 1:** Grep for `~/workspace/source/[^/]+/[^/]+/.git` or `cd /Users/agent/workspace/source/<repo>` patterns.

**Step 2:** For each match, either:
- Replace with `cd $(wt list <repo> | head -1 | awk '{print $1}')` style (ugly), or
- Replace with hardcoded worktree path `<repo>/main` or `<repo>/agent/<known-task>` (clearer), or
- Add `wt new <repo> <task>` calls where appropriate.

**Step 3:** If a script is per-repo (e.g. `pr-status`), generalize it to take a `<repo>` arg and read branch from `wt list`.

**Verify:** Each script is invocable without error; output unchanged for the canonical case.

**Commit:** N/A — these are user-shell files.

---

### Task 20: Write a CHANGELOG entry + Mnemosyne summary

**Objective:** Capture the why-it-mattered for future sessions.

**Step 1:** Update `/Users/agent/workspace/source/hermes-config/CHANGELOG.md` (or whichever Changelog the skill lives in) with a one-line `[Unreleased] > Changed: Adopt bare-repo + per-task worktree as canonical git workflow. Added ~/.hermes/bin/wt helper. Renamed branch convention to agent/<task>. See git-workflow skill.`

**Step 2:** Mnemosyne canonical slot:

```
memory: workflow-git-changed-2026-08-11
content: "Git workflow switched from `git clone` + ad-hoc `git worktree
add` to canonical bare-repo (~/workspace/source/<owner--repo>/.bare/)
+ global `wt` helper. Every coding task now runs in its own worktree
on branch agent/<task>. Eliminates 2026-06-15 shared-worktree stomp
failure mode. Schema consistent across 0451-software repos."
importance: 0.9
source: workflow-change
veracity: stated
```

**Step 3:** Verify Changelog entry doesn't conflict with similar entries from prior days; if so, merge them.

**Verify:** Mnemosyne recall returns the new memory; Changelog entry visible.

**Commit:** Inside hermes-config worktree (Changelog lives there).

---

## Verification at end of plan

After all tasks run:

```bash
# 1. Every SOUL.md and skills file references the pattern
grep -l "agent/<task>" /Users/agent/.hermes/SOUL.md /Users/agent/.hermes/profiles/*/SOUL.md
grep -rl "git-workflow" /Users/agent/.hermes/skills/ | wc -l

# 2. The wt helper works end-to-end
~/.hermes/bin/wt --help
wt list

# 3. Mnemosyne canonical slot is set
python3 -c "import mnemosyne..."  # or use the agent recall tool

# 4. All bootstrapped repos show the right layout
for d in ~/workspace/source/0451-software/*/; do
  [ -d "$d/.bare" ] && echo "✓ $(basename "$d")"
done

# 5. No `git clone` ad-hoc instructions survive in SOUL.md
grep -c "git clone\b" /Users/agent/.hermes/SOUL.md /Users/agent/.hermes/profiles/*/SOUL.md
# expect: 0 in the Git Workflow section (other git-clone usage for
# agent bootstrap is fine but should live in wt-bootstrap)

# 6. The kanban workspace and subagent guidance both point at `wt`
grep -c "wt new" /Users/agent/.hermes/skills/devops/kanban/SKILL.md \
                /Users/agent/.hermes/skills/software-development/subagent-driven-development/SKILL.md
# expect: ≥1 each
```

If any check fails, return to the relevant task and fix; otherwise the
plan is complete and the project is on the new workflow.
