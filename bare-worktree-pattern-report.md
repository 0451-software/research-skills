# Cloned Bare Repo + Git Worktrees — Reference Report

**Audience:** designing a canonical concurrent-multi-agent git workflow for
Hermes Agent sub-agents. Each sub-agent runs in its own terminal session and
needs an isolated working tree on its own branch, all backed by one shared
object database so commits don't collide.

**Pattern in one sentence:** keep a central bare mirror of the repo at
`~/workspace/source/<repo>.git` and have every agent spawn a linked worktree
from it with `git worktree add`.

---

## 1. Bare clone mechanics

### Commands

| Goal | Command |
|---|---|
| Bare mirror (only branches, no working tree) | `git clone --bare <url> ~/workspace/source/<repo>.git` |
| Full mirror (branches + tags + notes + all refs, refspec configured to overwrite on fetch) | `git clone --mirror <url> ~/workspace/source/<repo>.git` |
| Group-writable bare repo (multi-user SSH host) | `git clone --bare --shared=group <url> /srv/git/<repo>.git` |

`--bare` implies `--no-checkout`. Per `git-clone(1)`:

> "Make a *bare* Git repository. That is, instead of creating _<directory>_
> and placing the administrative files in _<directory>_/.git, make the
> _<directory>_ itself the `$GIT_DIR`. This obviously implies the
> `--no-checkout` because there is nowhere to check out the working tree."
> — `git-scm.com/docs/git-clone`

> "Compared to `--bare`, `--mirror` not only maps local branches of the source
> to local branches of the target, it maps all refs (including remote-tracking
> branches, notes etc.) and sets up a refspec configuration such that all these
> refs are overwritten by a `git remote update` in the target repository."
> — `git-scm.com/docs/git-clone`

For most agent workflows, **`--bare`** is sufficient. `--mirror` is for
backup / replication scenarios where you want the mirror to be functionally
identical to the origin and to overwrite its own refs on every fetch.

### Where to put it

Convention is `~/workspace/source/<repo>.git/` — `.git` suffix signals it's
the database, not a checkout. The Pro Git book codifies this:

> "By convention, bare repository directory names end with the suffix `.git`."
> — `git-scm.com/book/en/v2/Git-on-the-Server-Getting-Git-on-a-Server`

For agent workflows I recommend a per-project layout that makes the bare
repo invisible at the top level:

```
~/workspace/source/<repo>/
├── .bare/         ← the actual bare repo ($GIT_DIR)
├── .git           ← file: "gitdir: ./.bare"
├── main/          ← worktree on `main` (read-only convenience checkout)
├── agent/<task>/  ← worktree per agent task, branched from main
└── ...
```

This is the layout produced by Morgan Cugerone's helper script (cited below)
and the one pnpm itself uses internally.

### Updating the bare repo (no `git pull`!)

A bare repo has no working tree, so `git pull` (which requires merging into
a working tree) **does not work**. Two valid options:

```bash
# Option A — fetch into the bare repo (recommended for daily sync)
cd ~/workspace/source/<repo>.git
git fetch --all --prune --tags
git remote update        # equivalent; honors remote.*.fetch refspecs

# Option B — from inside any linked worktree (same effect, because they share .git)
cd ~/workspace/source/<repo>/agent/<task>
git fetch origin main    # fetches into the bare database visible to all worktrees
```

### Critical: set `remote.origin.fetch` after `--bare`

`git clone --bare` does **not** create the `remote.origin.fetch` refspec.
Without it, `git fetch` silently fetches nothing. This is the #1 footgun
and the most cited gotcha in practitioner write-ups. Confirmed by Morgan
Cugerone (cited), Graphite guide, and Dev.to.

```bash
# Run ONCE in the bare repo after the initial clone:
cd ~/workspace/source/<repo>.git
git config remote.origin.fetch "+refs/heads/*:refs/remotes/origin/*"
git fetch origin
```

Verify with:

```bash
git config --get remote.origin.fetch
# → +refs/heads/*:refs/remotes/origin/*
git branch -r
# → origin/main, origin/feat-x, …
```

> "When using `git clone` with the `--bare` option … neither remote-tracking
> branches nor the related configuration variables are created. That
> basically means that when you try to `git fetch` from your remote, the
> remote branches are not downloaded."
> — Morgan Cugerone, "Workarounds to Git worktree using bare repository"

### `core.bare = false` does not apply

Don't try to "fix" the bare repo by setting `core.bare = false`. That will
leave you with a corrupt state because `.git/` files would land on top of
working-tree files. A clone created with `--bare` is structurally bare (the
$GIT_DIR *is* the directory itself, not a subfolder). If you want a working
tree, create a worktree — don't toggle `core.bare`.

### Pushing from a worktree back to origin

Pushes **just work** from any linked worktree — they use the normal
`remote.origin.url` configured on the bare repo:

```bash
cd ~/workspace/source/<repo>/agent/<task>
git push -u origin agent/<task-id>      # first push
git push                                # subsequent pushes
```

You can also `cd` directly into the bare repo dir and run `git push`, but
that's unusual and not recommended — there's no working tree so it's just
operating on refs. Stick to pushing from the worktree.

---

## 2. Worktree mechanics

### Command surface

```bash
git worktree add <path>                        # new branch from HEAD, branch name = basename(path)
git worktree add <path> -b <branch>           # explicit branch name, still from HEAD
git worktree add <path> -b <branch> main       # branch from main explicitly (recommended for agents)
git worktree add <path> <existing-branch>      # check out existing branch in new worktree
git worktree add --detach <path> <commit-ish>  # throwaway, no branch
git worktree add --lock <path> -b <branch> main  # lock immediately on create

git worktree list                # audit
git worktree list --porcelain    # script-friendly
git worktree remove <path>       # clean only; --force to override
git worktree move <path> <new>   # cannot move worktrees with submodules
git worktree lock   <path> --reason "agent in flight"
git worktree unlock <path>
git worktree prune               # cleans $GIT_DIR/worktrees/ for missing dirs
git worktree repair [<path>…]    # re-link after manual moves
```

> "A git repository can support multiple working trees, allowing you to check
> out more than one branch at a time. With `git worktree add` a new working
> tree is associated with the repository, along with additional metadata that
> differentiates that working tree from others in the same repository."
> — `git-scm.com/docs/git-worktree`

### What's shared vs. per-worktree

| State | Shared (lives in bare `.git/`) | Per-worktree (lives in `.git/worktrees/<id>/`) |
|---|---|---|
| Object database | ✅ `objects/`, `packs/` | — |
| `refs/heads/*`, `refs/tags/*` | ✅ all branches visible everywhere | — |
| `HEAD` | — | ✅ |
| `index` | — | ✅ |
| `config` | ✅ shared unless `extensions.worktreeConfig=true` | opt-in via `--worktree` |
| Worktree-specific files (`.git` gitfile, locked marker) | — | ✅ |

Confirmed by `git-worktree(1)` DETAILS and CONFIGURATION FILE sections.

### Concurrent worktrees on the same branch

**NOT supported.** Git refuses with a hard error:

```
$ git worktree add ../other-feature feature/auth
fatal: 'feature/auth' is already checked out at '/path/to/auth'
```

You either pick a different branch or pass `--detach` (creates a throwaway
at the same commit but no branch attached). This is by design and is the
core safety property for agent isolation.

### Locked worktrees

Use `git worktree lock` when an agent is mid-task and you don't want
auto-prune (e.g. on USB drive, or any other reason the worktree might
disappear from the filesystem). Locked worktrees survive `git worktree prune`
and `git gc`. The lock file lives at `$GIT_DIR/worktrees/<id>/locked` and
holds a human-readable reason:

```bash
git worktree lock --reason "engineer persona mid-implementation" ../agent/feat-auth
```

---

## 3. Branching strategy for fresh tasks

### Convention: always branch from `main`

```bash
git worktree add ../agent/<task-id> -b agent/<task-id> main
```

Why `main` and not `HEAD` of whatever the agent currently has checked out?
Because if an agent is stacked on top of an in-progress feature branch,
branching from `HEAD` means stacking the new work on someone else's WIP
commits. Branching from `main` guarantees a clean linear base. This is the
canonical pattern in every multi-agent write-up surveyed.

### Naming convention

`agent/<task-id>` is the most common convention. Options:

| Style | Example | Pros | Cons |
|---|---|---|---|
| `agent/<task-id>` | `agent/feat-oauth2` | easy to filter by agent | collisions if two personas reuse id |
| `<persona>/<task-id>` | `engineer/feat-oauth2` | explicit persona | more verbose |
| `<user-or-prefix>/<task-id>` | `hermes/feat-oauth2` | human-readable | ambiguous |

The pnpm repo uses `<branch-name>` directly (e.g. `feat/my-feature`); their
helper script converts `feat/my-feature` → directory `feat-my-feature` to
avoid the slash on disk.

### Auto-delete after PR merge (GitHub-side)

In GitHub: Settings → General → Pull Requests → "Automatically delete head
branches" → ✅. This removes the remote ref after merge; the local worktree
can then be removed with `git worktree remove`. The local bare repo keeps
the ref until you `git remote prune origin` or `git fetch --prune`.

---

## 4. Multi-agent concurrent safety

### What's safe

| Operation | Safe? | Reason |
|---|---|---|
| Multiple agents running `git fetch` simultaneously against the bare repo | ✅ | git fetch takes an internal lock; concurrent fetches serialize cleanly |
| Pushing different branches from different worktrees | ✅ | refs/heads/agent/A and refs/heads/agent/B are independent |
| Creating new worktrees from main while others are in flight | ✅ | each gets a unique path |
| Two agents editing different files in different worktrees | ✅ | working trees are independent directories |
| Two agents reading the same file from the same branch | ✅ | working trees are read-only-ish until you commit |

### What's not safe

| Operation | Why it fails / what happens |
|---|---|
| Two agents pushing the **same branch** simultaneously | git push takes the ref lock; second push blocks, may fail with `failed to push some refs` if non-fast-forward. With `--force` you clobber the other agent — never do this from an autonomous agent. |
| Same agent checking out the same branch in two worktrees | `git worktree add` refuses (see §2) |
| One agent `git fetch`ing while another is mid-commit in a different worktree | Safe — commits are atomic in git; the fetcher either sees the old state or the new commit, never a half-commit |

### Cross-worktree branch visibility

This is the key correctness property: **all worktrees share the object
database and the ref namespace**. If Agent A pushes `agent/feat-x` to
origin, Agent B running `git fetch origin` in any worktree (or in the
bare repo) sees it immediately. There is no "pull to get your sibling's
branch" step beyond the normal fetch.

> "If you do a fetch in one of your working trees, or if you rename a branch
> in the other working tree, the changes are immediately visible in all the
> working trees, as you're operating on the same underlying data."
> — Andrew Lock, "Working on two git branches at once with git worktree"

---

## 5. Bare-repo-as-shared-git-dir in the wild

### History: `git-new-workdir` → `git worktree`

Before Git 2.5 (July 2015) the canonical way was the `contrib/workdir/git-new-workdir`
shell script. It created a new working directory and symlinked `.git/objects`,
`.git/refs`, `.git/config`, etc., creating a separate `HEAD` and `index`. It
worked but was hacky, fragile, and Windows-incompatible. Replaced in Git 2.5
by the first-class `git worktree` command (Nguyễn Thái Ngọc Duy). As of 2026
`git worktree` is the standard and `git-new-workdir` is historical.

### Real-world adoptions

- **pnpm monorepo** uses a bare repo at the root with worktrees per branch
  plus `enableGlobalVirtualStore: true` so each worktree's `node_modules` is
  just symlinks into one shared pnpm content-store. They ship a
  `pnpm worktree:new <branch-or-pr-number>` script and a shell wrapper
  `wt.sh` that `cd`s into the new worktree. (`pnpm.io/git-worktrees`)
- **Claude Code** has native `--worktree <name>` / `-w <name>` flags. By
  default creates `.claude/worktrees/<name>/` on a branch
  `worktree-<name>`. (`code.claude.com/docs/en/worktrees`)
- **Gemini CLI** similarly supports `--worktree` flag, dropping sessions
  under `.gemini/worktrees/<name>/`. (Karl Weinmeister, Google Cloud)
- **Cursor** Parallel Agents feature is built directly on top of git
  worktrees.
- **Helper tools** for AI-agent worktrees: `wt` (timvw), `wt` (Vostrez
  shell function), `git-wt` (jason-dour), `agent-worktree` (nekocode,
  npm-installed), `worktree-cli` (fnebenfuehr), `git-worktree-runner`
  (CodeRabbit, integrates with Claude/Cursor/Copilot/Gemini),
  `gwq` (d-kuro, status dashboard + tmux), `agentree` (AryaLabs),
  `ccswarm` (nwiizo, multi-pool orchestration), `Crystal` (desktop
  parallel-Claude manager).

This pattern is now mainstream enough that Andrew Lock's blog post on it
is from 2022, GitHub's own engineering blog has a 2025 post titled "What
are git worktrees, and why should I use them?", and pnpm has docs on it.

---

## 6. Pitfalls & gotchas

### "Branch already checked out"

```
fatal: 'main' is already checked out at '/path/to/other-worktree'
```

Each branch can only be checked out in one worktree. Either use a different
branch name (recommended for agents — see §3) or pass `--detach` for a
throwaway.

### `.git` file path handling

A linked worktree contains a `.git` **file** (not directory) with one line:

```
gitdir: /path/to/bare-repo/.git/worktrees/<id>
```

By default the path is absolute. If you anticipate moving the bare repo
(e.g. across machines, or into a different parent directory), set
`worktree.useRelativePaths = true` (requires `extensions.relativeWorktrees`,
incompatible with old git versions) or be ready to run `git worktree repair`
after any move. Source: `git-worktree(1)`.

If you `mv` a worktree by hand, also update the `gitdir` file inside
`$GIT_DIR/worktrees/<id>/gitdir`, or just run `git worktree repair`.

### Submodules

Submodule state lives inside the bare repo's `.git/modules/<name>/`, but
the working tree of each submodule lives inside each worktree's working
tree. **Submodule + worktree support is officially incomplete and not
recommended.** Per `git-worktree(1)` BUGS section:

> "Multiple checkout in general is still experimental, and the support for
> submodules is incomplete. It is NOT recommended to make multiple
> checkouts of a superproject."

Practical mitigations: don't add new submodules from inside a worktree
(use the bare repo context), run `git submodule update --init` after
`git worktree add` (worktree add does NOT populate submodules — see
joshjhall/containers#638), and avoid creating multiple worktrees that
both touch the same superproject's submodule config.

### Hooks

`.git/hooks/` lives in the **bare repo** and is shared by all worktrees.
This is good for push-receive / post-receive hooks (CI triggers), bad for
`pre-commit` hooks that assume a specific working tree path — they fire
for commits made in any worktree. Workaround:

```bash
git config extensions.worktreeConfig true   # in the bare repo
# then in each worktree:
git config --worktree core.hooksPath "$HOME/.githooks-shared"
```

Or write hooks using `git rev-parse --show-toplevel` instead of hardcoded
paths. Source: Stack Overflow "Using Git hooks with worktree"; hidekazu-konishi.com.

### Garbage collection

The bare repo does NOT auto-garbage-collect the way a non-bare clone does,
because `git gc --auto` is triggered by porcelain commands that create
objects (`commit`, `fetch`, etc.), but a bare repo sees those from other
worktrees/agents and never from its own working tree. Run periodically:

```bash
cd ~/workspace/source/<repo>.git
git gc                                # or: git gc --prune=now --aggressive
git maintenance run --auto           # newer (Git 2.30+); bundles multiple tasks
```

`gc.worktreePruneExpire` (default `3.months.ago`) controls when stale
worktree entries (whose directory is missing) get auto-pruned during
`git gc`. Set to `now` if you want immediate cleanup, `never` to disable.

### Bisect / clean / rebase across worktrees

These commands operate on the **current worktree**'s state, not the
shared database — they don't conflict with other worktrees. But commands
that operate on the whole `.git` directory (e.g. `git fsck`, full
`git repack -a`) should be run in the bare repo context (or any single
worktree, since they all share the same database).

### `config` files

Bare repo's `.git/config` (the actual config in our `.bare/config` layout)
is shared. Per-worktree settings need `extensions.worktreeConfig=true`
in the bare repo, after which `git config --worktree <key> <value>` writes
to `.git/worktrees/<id>/config.worktree`. Per `git-worktree(1)` CONFIG
section, variables that should never be shared: `core.worktree`,
`core.bare=true`, `core.sparseCheckout`.

For agent workflows you usually don't need per-worktree config — agents
inherit the bare repo's user.name/user.email/remote config. If different
personas need different identities, set per-worktree `user.email`.

---

## 7. Migration steps for an existing setup

### Scenario A: existing `git clone` with working tree (current state)

```bash
# 1. Identify current clone
cd ~/path/to/current/clone
git remote -v               # note the origin URL
git status                  # note uncommitted work

# 2. Commit/stash any uncommitted work in the current working tree
git stash push -u -m "WIP before migration"
# (note the stash ref)

# 3. Create the bare repo alongside the existing clone
cd ~/workspace/source
git clone --bare <origin-url> <repo>.git
cd <repo>.git
git config remote.origin.fetch "+refs/heads/*:refs/remotes/origin/*"
git fetch origin

# 4. Decide what to do with the old working tree
#    Option A: convert it into a worktree on the current branch
cd ~/path/to/current/clone
git remote set-url origin ~/workspace/source/<repo>.git   # point at bare
# (this repo can stay as-is; it shares objects if you use --reference, but
#  the cleanest path is to recreate as a worktree)

#    Option B: tear it down and re-create as worktree
rm -rf ~/path/to/current/clone
cd ~/workspace/source/<repo>.git
git worktree add ~/workspace/source/<repo>/main main
# retrieve your stash from the new worktree:
git stash pop
```

### Scenario B: in-place conversion of an existing clone to bare

The git wiki pattern (cited in Stack Overflow "How to convert a normal Git
repository to a bare one"):

```bash
mv repo/.git repo.git
git --git-dir=repo.git config core.bare true
rm -rf repo
```

This works but is fiddly and you'll need to recreate working trees
afterward with `git worktree add`. The `git clone --bare` approach is
cleaner.

### `origin` remote

Same URL on both sides. After migration the bare repo's `remote.origin.url`
is the original remote URL, and each worktree inherits it. To swap the
remote URL across the whole setup:

```bash
cd ~/workspace/source/<repo>.git
git remote set-url origin <new-url>
# all worktrees see the new URL on next fetch
```

---

## 8. Sample shell helper scripts

Generic `<repo>`-prefixed helpers. Drop into `~/bin/` or `~/.local/bin/`.

### `_wt_common.sh` (shared setup)

```bash
# Source this. Defines REPO_DIR, BARE_DIR, WORKTREE_PARENT.
# Usage: source _wt_common.sh <repo-name>
REPO_NAME="$1"
WORKTREE_PARENT="${HOME}/workspace/source/${REPO_NAME}"
BARE_DIR="${WORKTREE_PARENT}/.bare"

require_bare_repo() {
  [ -d "$BARE_DIR" ] || { echo "ERROR: bare repo not found at $BARE_DIR" >&2; exit 1; }
}

default_branch() {
  ( cd "$BARE_DIR" && git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null \
    | sed 's|^origin/||' ) || echo main
}
```

### `<repo>-sync-main` — fetch latest into bare repo

```bash
#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/_wt_common.sh" "${1:?usage: <repo>-sync-main <repo-name>}"
require_bare_repo
( cd "$BARE_DIR" && git fetch --all --prune --tags )
echo "Synced $(date -Iseconds)"
```

### `<repo>-new-worktree` — create worktree branched from main

```bash
#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/_wt_common.sh" "${1:?usage: <repo>-new-worktree <repo-name> <task-name>}"
REPO_NAME="$1"; shift
TASK_NAME="${1:?usage: <repo>-new-worktree <repo-name> <task-name>}"
BASE="${2:-$(default_branch)}"

require_bare_repo
WT_DIR="${WORKTREE_PARENT}/${TASK_NAME}"
BRANCH="agent/${TASK_NAME}"

# Refuse if the directory exists
[ -e "$WT_DIR" ] && { echo "ERROR: $WT_DIR already exists" >&2; exit 1; }

( cd "$BARE_DIR" \
  && git worktree add "$WT_DIR" -b "$BRANCH" "$BASE" )

echo "Worktree ready at: $WT_DIR"
echo "Branch: $BRANCH (based on $BASE)"
echo "To use:"
echo "  cd $WT_DIR"
```

### `<repo>-list-worktrees` — table view

```bash
#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/_wt_common.sh" "${1:?usage: <repo>-list-worktrees <repo-name>}"
require_bare_repo
( cd "$BARE_DIR" && git worktree list )
```

### `<repo>-remove-worktree` — safe removal with uncommitted-check

```bash
#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/_wt_common.sh" "${1:?usage: <repo>-remove-worktree <repo-name> <task-name>}"
REPO_NAME="$1"; shift
TASK_NAME="${1:?usage: <repo>-remove-worktree <repo-name> <task-name>}"
WT_DIR="${WORKTREE_PARENT}/${TASK_NAME}"
BRANCH="agent/${TASK_NAME}"

require_bare_repo

[ -d "$WT_DIR" ] || { echo "ERROR: $WT_DIR not found" >&2; exit 1; }

if [ -n "$(git -C "$WT_DIR" status --porcelain)" ]; then
  echo "ERROR: worktree has uncommitted changes:" >&2
  git -C "$WT_DIR" status --short >&2
  echo "Re-run with --force to discard (after stashing/pushing if you care)." >&2
  [ "${2:-}" = "--force" ] || exit 1
fi

( cd "$BARE_DIR" && git worktree remove --force "$WT_DIR" )
( cd "$BARE_DIR" && git branch -D "$BRANCH" 2>/dev/null || true )
( cd "$BARE_DIR" && git worktree prune )

echo "Removed worktree $WT_DIR and branch $BRANCH"
```

---

## 9. Concrete worked example

Walking through the full lifecycle on a fictional repo `acme/api`.

```bash
# === Setup (one time per repo) ===
cd ~/workspace/source
git clone --bare git@github.com:acme/api.git api/.git
cd api/.git
git config remote.origin.fetch "+refs/heads/*:refs/remotes/origin/*"
git fetch origin
git worktree add ../main main
# → Preparing worktree (new branch 'main' …)

# === Verify ===
cd ~/workspace/source/api/.git
git worktree list
# → /Users/you/workspace/source/api/.git             (bare)
# → /Users/you/workspace/source/api/main             abcd1234 [main]

# === Engineer persona starts a task ===
~/bin/api-new-worktree api feat-oauth2
# → Worktree ready at: /Users/you/workspace/source/api/feat-oauth2
# → Branch: agent/feat-oauth2 (based on main)
cd ~/workspace/source/api/feat-oauth2
git status
# → On branch agent/feat-oauth2
# → nothing to commit, working tree clean

# === Engineer makes changes ===
echo "new oauth2 handler" > handler.py
git add handler.py
git commit -m "feat: add oauth2 handler skeleton"
git push -u origin agent/feat-oauth2
# → Branch 'agent/feat-oauth2' set up to track remote branch 'agent/feat-oauth2' from 'origin'.

# Meanwhile, Inspector persona starts a parallel review task
~/bin/api-new-worktree api review-rate-limits
cd ~/workspace/source/api/review-rate-limits
# Inspector sees clean working tree on its own branch — no overlap with engineer's WIP

# === Inspector references the engineer's branch ===
git fetch origin
git log --oneline origin/agent/feat-oauth2
# → abc1234 feat: add oauth2 handler skeleton

# === After PR is merged ===
~/bin/api-remove-worktree api feat-oauth2
# → Removed worktree /Users/you/workspace/source/api/feat-oauth2 and branch agent/feat-oauth2

# Periodic GC on the bare repo
cd ~/workspace/source/api/.git
git gc
```

Expected output throughout comes from `git-clone(1)`, `git-worktree(1)`, and
the standard porcelain behavior. No commands above are unusual.

---

## 10. Sources & verification

### Tier 1 — Official documentation (highest authority)

1. **`git-clone(1)`** — `git-scm.com/docs/git-clone`. Authoritative for
   `--bare`, `--mirror`, refspec behavior. Verified the "no remote-tracking
   branches created with --bare" wording directly.
2. **`git-worktree(1)`** — `git-scm.com/docs/git-worktree`. Authoritative
   for all worktree mechanics: shared vs per-worktree state, the `.git`
   gitfile contents, `worktree.guessRemote`, `worktree.useRelativePaths`,
   `extensions.worktreeConfig`, the "BUGS" section about submodule
   incompleteness, and `LIST OUTPUT FORMAT` (default + `--porcelain`).
3. **`git-init(1)`** — `git-scm.com/docs/git-init`. Authoritative for
   `--shared` permission modes (`umask|group|all|world|everybody|<perm>`)
   and `core.sharedRepository` semantics.
4. **`git-gc(1)`** — `git-scm.com/docs/git-gc`. Authoritative for
   `gc.auto`, `gc.worktreePruneExpire`, and the "housekeeping is required"
   heuristic that doesn't fire automatically in bare repos.
5. **Pro Git book, ch. 4.2 "Getting Git on a Server"** —
   `git-scm.com/book/en/v2/Git-on-the-Server-Getting-Git-on-a-Server`.
   Codifies the `.git` suffix convention for bare repos.
6. **Pro Git book, ch. 10.5 "The Refspec"** —
   `git-scm.com/book/en/v2/Git-Internals-The-Refspec`. Authoritative for
   `+refs/heads/*:refs/remotes/origin/*` syntax.
7. **GitHub Docs "Duplicating a repository"** —
   `docs.github.com/en/repositories/creating-and-managing-repositories/duplicating-a-repository`.
   Official guidance for `git clone --bare` + `git push --mirror`.
8. **GitHub Blog: "What are git worktrees, and why should I use them?"**
   (Cassidy Williams, GitHub) — `github.blog/ai-and-ml/github-copilot/what-are-git-worktrees-and-why-should-i-use-them/`.
   Recent, official GitHub endorsement.
9. **GitHub Blog: "Scaling Git's garbage collection"** — context on
   `git gc --prune` semantics for bare repos.
10. **Claude Code Docs: "Run parallel sessions with worktrees"** —
    `code.claude.com/docs/en/worktrees`. Authoritative for how a major
    AI agent runtime implements worktree isolation.

### Tier 2 — Established practitioner write-ups (cited above)

11. **Andrew Lock** — "Working on two git branches at once with git
    worktree" (Apr 2022, `.NET Escapades`). The clearest pros/cons
    comparison vs. multiple clones.
12. **Morgan Cugerone** — "Workarounds to Git worktree using bare
    repository and cannot fetch remote branches" (Jan 2022, updated
    2025). The canonical write-up of the `remote.origin.fetch`
    fix; provides the production-ready `git-clone-bare-for-worktrees`
    shell script.
13. **pnpm docs** — `pnpm.io/git-worktrees`. Real production monorepo
    using bare + worktrees + global virtual store; ships
    `pnpm worktree:new` and `wt.sh`.
14. **Atlassian** — `developer.atlassian.com/server/bitbucket/how-tos/using-worktree-api-to-create-commits/`.
    Bitbucket's internal WorkTree API (sparse-checkout based, but
    relevant for understanding what a "real" worktree system looks like).

### Tier 3 — Helper tools and real adoptions

15. **Gal Buki** — "Git Worktrees in a Multi-Agent workflow" (Apr 2026).
16. **Tim Van Wassenhove** — `github.com/timvw/wt`. Go-based wt helper.
17. **Mitch Vostrez** — "A tiny wt helper for git worktrees"
    (voz.dev). Shell function variant.
18. **Superset.sh** — "Git Worktrees: The Feature That Waited a Decade
    for Its Moment". History of `git-new-workdir` → `git worktree`.
19. **Karl Weinmeister** — "Run multiple coding agents safely with git
    worktrees" (Google Cloud / Medium). Local vs. global sandbox
    architectural choice.

### Things that LOOK authoritative but are wrong (do not trust)

- **Stack Overflow answer claiming `git worktree add` automatically
  fetches from origin.** It doesn't. You need to `git fetch` first or
  ensure the branch already exists locally. Several old answers confuse
  `worktree.guessRemote` with auto-fetch.
- **Tutorials claiming `--bare` clones create remote-tracking branches.**
  They do not — this is documented in `git-clone(1)` ("neither
  remote-tracking branches nor the related configuration variables are
  created"). The widespread folk belief that `--bare` is "just like a
  regular clone but no checkout" is wrong on this specific point and
  is the cause of the "fetch doesn't update anything" confusion.
- **CoreUI/SEO content on "how to convert git repo to bare"** —
  `coreui.io/answers/how-to-convert-git-repo-to-bare-repo/` and similar
  AI-generated SEO pages. These contain correct basic commands but
  confidently assert things like "use `git clone --bare` to convert" and
  then show an in-place conversion that breaks worktree relationships.
  Use the Pro Git or git-scm docs, not these.
- **Various Medium articles** that suggest you can "set
  `core.bare=false`" to convert a bare repo back to a regular one. You
  can, but only by recreating a working tree via `git checkout <branch> -f`,
  and only as a one-off — it's not a sustainable pattern. Trust the
  `git-worktree(1)` and `git-clone(1)` wording over Medium summaries.
- **`buildkite.com/docs/agent/self-hosted/configure/git-mirrors`** is
  fine but **uses `--mirror` not `--bare`**. It is *not* the canonical
  reference for the bare-plus-worktree-for-agents pattern; it's the
  mirror-for-shared-CI pattern. They're related but different.

### Bottom line for the parent agent designing the workflow

Use the **bare + worktree + per-agent branch** pattern. The reference
implementation is:

- Bare repo at `~/workspace/source/<repo>.git/` (or `~/workspace/source/<repo>/.bare/` with a `.git` gitfile for cleanliness)
- One `--shared=group` only if multi-OS-user SSH; for single-user macOS agent workflows, skip `--shared` and rely on umask
- Set `remote.origin.fetch = +refs/heads/*:refs/remotes/origin/*` ONCE after clone
- Wrap operations in the four `<repo>-{sync-main,new-worktree,list-worktrees,remove-worktree}` helpers above
- Branch convention: `agent/<task-id>` from `main` (or whatever the repo's default branch is — detect with `git symbolic-ref --short refs/remotes/origin/HEAD`)
- Auto-delete remote branches via GitHub repo settings; local cleanup with the `remove-worktree` helper
- Schedule periodic `git gc` in the bare repo (cron `0 3 * * 0 git -C ~/workspace/source/<repo>/.git gc --quiet`)
- Don't enable `--bare --mirror`; the refspec-overwrite behavior of `--mirror` will surprise you