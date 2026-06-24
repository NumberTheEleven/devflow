# DevFlow v3.0 Session Isolation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace DevFlow v2.4's rsync full-repo copy with Claude Code's native worktree primitives (`git worktree add` + `EnterWorktree` + strategy menu), eliminating the recursive copy bug, slashing session creation time, and making CWD isolation reliable.

**Architecture:** Two-axis detection (git-level + path-level) for backward compat; `git worktree add` for isolation (seconds, not minutes); a 5-strategy menu for runtime environment supplementation chosen by AI based on project context; `EnterWorktree` (preferred) / `cd` (fallback) for CWD switching with per-phase guards; `ExitWorktree` (preferred) / `git worktree remove` (fallback) for cleanup.

**Tech Stack:** Git 2.5+ (`worktree add` with `--checkout` default), bash/PowerShell cross-platform, Claude Code `EnterWorktree`/`ExitWorktree` tools (when available).

## Global Constraints

- Plugin version: `2.4.0` → `3.0.0` (breaking change in session isolation mechanism)
- Cross-platform: must work on Windows (PowerShell) and Unix (bash). No POSIX-only syntax in skill prose; show platform-specific commands explicitly.
- Backward compat: detection must recognize v2.4 full-copy directories (`GIT_DIR == GIT_COMMON` + path matches `.claude/worktrees/devflow-*`)
- Single entry point: `/devflow` — no new subcommands, no behavioral flags
- Sync target: `skills/devflow/SKILL.md` (Codex) is synced FROM `skills/devflow/_SKILL.md` (Claude Code) via `scripts/sync-skills.js` — edit `_SKILL.md`, run sync to generate `SKILL.md`. The Codex file has the `allowed-tools:` line stripped during forward sync, so write `_SKILL.md` with `allowed-tools:` present.
- No new dependencies. No new scripts. No new files in `skills/*/references/` — all changes fit in `_SKILL.md`.
- Plugin manifest (`.claude-plugin/plugin.json`): bump `version` and update `description` to reflect v3.0 native worktree approach.

---

## File Structure

| File | Status | Responsibility |
|------|--------|----------------|
| `skills/devflow/_SKILL.md` | **Modify** | Source of truth. Step 0 detection, Phase 1.4 session creation, Phase 6.5 cleanup, per-phase CWD guards, header version bump, state.json schema version. |
| `skills/devflow/SKILL.md` | **Regenerate** | Generated from `_SKILL.md` via `node scripts/sync-skills.js`. Do not hand-edit. |
| `.claude-plugin/plugin.json` | **Modify** | Bump `version` to `3.0.0`, update `description` to drop "full-repo copy" wording. |
| `docs/superpowers/specs/2026-06-24-devflow-session-isolation-v3-design.md` | Reference | Design spec. Read first if any task is unclear. |

Out of scope (do not touch): the 6 other skills (`clarify`, `breakdown`, `blueprint`, `implement`, `verify`, `discover`), `scripts/sync-skills.js` itself, all `skills/*/references/*` files.

---

## Task 1: Upgrade plugin manifest to v3.0

**Files:**
- Modify: `.claude-plugin/plugin.json:1-9`

**Interfaces:**
- None — isolated manifest bump.

- [ ] **Step 1: Update version and description**

Open `.claude-plugin/plugin.json` and replace the entire file contents with:

```json
{
  "name": "devflow",
  "description": "Structured AI-assisted development workflow — from project discovery to verification. Single entry point /devflow guides you through requirements, design, implementation, and testing with full-chain numbered tracking. Uses native git worktree session isolation for concurrent feature development with mandatory merge validation to catch conflicts and semantic regressions.",
  "author": {
    "name": "NumberTheEleven",
    "email": "numtheeleven@gmail.com"
  },
  "version": "3.0.0"
}
```

The new description replaces "full-repo copy isolation" with "native git worktree session isolation" — accurately reflecting the v3.0 mechanism.

- [ ] **Step 2: Verify JSON validity**

Run: `node -e "console.log(JSON.parse(require('fs').readFileSync('.claude-plugin/plugin.json','utf8')))"`

Expected: prints the parsed object with `version: '3.0.0'` and the new `description`. If it throws, the JSON is malformed — fix and retry.

- [ ] **Step 3: Commit**

```bash
git add .claude-plugin/plugin.json
git commit -m "chore(devflow): bump plugin version to 3.0.0"
```

---

## Task 2: Rewrite Step 0 entry detection

**Files:**
- Modify: `skills/devflow/_SKILL.md:1-79` (Step 0 block — lines 44-79)

**Interfaces:**
- Produces: detection logic that downstream phases rely on. The detection answer is "resume existing session" vs "start new session in main repo" vs "block (incompatible state)".
- The v3.0 detection matrix:

| `GIT_DIR == GIT_COMMON` | path in `.claude/worktrees/devflow-*` | Verdict |
|---|---|---|
| Yes | No | Main repo, start new session (or block per 0.2) |
| Yes | Yes | **v2.4 full-copy directory** — resume as v2.4 session |
| No | (any) | **v3.0 git worktree** — resume as v3.0 session |

The existing skill's `GIT_DIR`/`GIT_COMMON` shell snippet comes from `superpowers:using-git-worktrees` (publicly known technique). Add it inline in the skill prose; no file references needed.

- [ ] **Step 1: Read the current Step 0 block**

Read `skills/devflow/_SKILL.md` lines 44-79 to confirm exact current text. (Already read in context — see Step 0: 入口检测 starting at line 44.)

- [ ] **Step 2: Replace Step 0 with the v3.0 version**

In `skills/devflow/_SKILL.md`, locate the section starting at the `## Step 0: 入口检测` heading (line 44) and ending right before `## Phase 1: 需求澄清` (line 82). Replace that entire block with:

```markdown
## Step 0: 入口检测

收到 `/devflow` 请求后，首先判断当前环境。v3.0 起，会话隔离基于 git worktree，检测需同时识别 v3.0 worktree 会话和 v2.4 全量副本遗留会话。

### 0.1 计算 git 拓扑标识

通过 `git rev-parse --git-dir` 与 `--git-common-dir` 的差异，识别当前是否处于 worktree 中：

```bash
# Unix
GIT_DIR=$(cd "$(git rev-parse --git-dir 2>/dev/null)" 2>/dev/null && pwd -P)
GIT_COMMON=$(cd "$(git rev-parse --git-common-dir 2>/dev/null)" 2>/dev/null && pwd -P)
[ "$GIT_DIR" = "$GIT_COMMON" ] && IN_WORKTREE=false || IN_WORKTREE=true

# Windows PowerShell
$gitDir = (Resolve-Path (git rev-parse --git-dir 2>$null) -ErrorAction SilentlyContinue).Path
$gitCommon = (Resolve-Path (git rev-parse --git-common-dir 2>$null) -ErrorAction SilentlyContinue).Path
$inWorktree = ($gitDir -ne $gitCommon)
```

- `GIT_DIR == GIT_COMMON`：处于主仓库
- `GIT_DIR != GIT_COMMON`：处于 git worktree 链接的工作目录（v3.0 会话）

### 0.2 路径回退检测（v2.4 向后兼容）

v2.4 通过 rsync 全量复制产生的开发环境目录不是 git worktree，所以 git 拓扑标识会判定为主仓库。需要额外检查路径前缀：

```bash
# Unix
case "$(pwd -P)" in
  */.claude/worktrees/devflow-*) IN_V24_COPY=true ;;
  *) IN_V24_COPY=false ;;
esac

# Windows PowerShell
$inV24Copy = ($PWD.Path -like '*/.claude/worktrees/devflow-*' -or $PWD.Path -like '*.claude\worktrees\devflow-*')
```

### 0.3 综合判定

| `IN_WORKTREE` | `IN_V24_COPY` | 判定 | 动作 |
|---------------|---------------|------|------|
| `false` | `false` | 在主仓库（非开发环境） | 继续 0.4 检查旧版活跃会话 |
| `false` | `true` | 在 v2.4 全量副本中 | 读取 `devflow/<feature>/state.json` 恢复会话（视为 v2.4 会话） |
| `true` | (任意) | 在 v3.0 git worktree 中 | 读取 `devflow/<feature>/state.json` 恢复会话 |

注意：`IN_WORKTREE=true` 时 `IN_V24_COPY` 一定为 `false`（v3.0 worktree 目录名虽然形如 `.claude/worktrees/devflow-*`，但路径前缀检测仅作为兜底，主判定以 git 拓扑为准）。

### 0.4 检测是否有活跃会话

检查主仓库根目录下是否存在未完成的旧版 `devflow/state.json`（仅在判定处于主仓库时执行）：

- **存在且 `phase` 不是 `"completed"`：** 说明有未完成的旧版 DevFlow 会话。
  - 输出："检测到主仓库存在未完成的旧版 DevFlow 会话（feature: `<feature>`，当前阶段：`<phase>`）。v3.0 起会话需要在开发环境副本中运行，请先完成或手动清理该会话后再开始新会话。"
  - 不创建新开发环境，等待用户处理

- **不存在或 `phase` 为 `"completed"`：**
  - 如果没有传入需求描述，询问用户要做什么
  - 如果传入了需求描述，进入 Phase 1（需求澄清）

### 0.5 管理命令说明

v2.4 起不再提供 `/devflow list` 和 `/devflow cleanup` 管理命令。`/devflow` 保持唯一入口。

- 如需查看会话，直接查看 `devflow/<feature>/` 目录或 `.claude/worktrees/` 目录
- 如需清理开发环境副本，使用 `git worktree remove .claude/worktrees/devflow-<feature>`（v3.0）或直接删除目录（v2.4 遗留）
```

- [ ] **Step 3: Verify the replacement preserves structure**

Read `skills/devflow/_SKILL.md` lines 44-110 and confirm:
- Section starts with `## Step 0: 入口检测`
- Section ends right before `## Phase 1: 需求澄清`
- All 5 sub-sections (0.1 through 0.5) are present
- Both bash and PowerShell snippets are present in 0.1 and 0.2

- [ ] **Step 4: Commit**

```bash
git add skills/devflow/_SKILL.md
git commit -m "feat(devflow): upgrade Step 0 detection to v3.0 (git worktree + v2.4 backward compat)"
```

---

## Task 3: Rewrite Phase 1.4 session creation

**Files:**
- Modify: `skills/devflow/_SKILL.md` — the `### 1.4 初始化会话` section (currently lines 125-202)

**Interfaces:**
- Consumes: `feature` name (confirmed in 1.3), target branch (auto-detected in 1.4.1), `EnterWorktree` tool (Claude Code) or fallback `cd`.
- Produces: an active session with (a) feature branch checked out, (b) worktree directory populated with git-tracked files, (c) runtime environment supplemented per chosen strategy, (d) `devflow/<feature>/state.json` written.
- Cleanup counterparts: Task 5 (Phase 6.5) must mirror this section's directory name and worktree path conventions.

- [ ] **Step 1: Read the current Phase 1.4 block**

The current `### 1.4 初始化会话` section spans lines 125-202 of `skills/devflow/_SKILL.md`. Re-read to confirm exact text before replacing.

- [ ] **Step 2: Replace Phase 1.4 with the v3.0 version**

In `skills/devflow/_SKILL.md`, locate the `### 1.4 初始化会话` heading (line 125) and replace everything from that line through the end of section 1.4 (right before `### 1.5 进入下一阶段` at line 206) with:

```markdown
### 1.4 初始化会话

Feature 名称确认后，执行以下步骤。

#### 1.4.1 自动识别目标分支

检查 `master` 和 `main`，按以下优先级：
- 仅存在 `main` → 使用 `main`
- 仅存在 `master` → 使用 `master`
- 同时存在 → 默认使用 `main`
- 都不存在 → 报错并停止

#### 1.4.2 检查冲突

检查是否已存在同名 branch 或开发环境目录：
```bash
git branch --list <feature>
ls -d .claude/worktrees/devflow-<feature> 2>/dev/null  # Unix
# 或 Test-Path .claude/worktrees/devflow-<feature>      # Windows
```
- 如果存在，报错："feature 名称 `<feature>` 已存在（branch 或开发环境），请更换名称。"
- 不存在则继续

#### 1.4.3 创建 feature branch

```bash
git checkout -b <feature>
```

#### 1.4.4 创建 git worktree（秒级）

```bash
# 切回目标分支（如果当前在 feature branch）
git checkout <target-branch>

# 用 git worktree add 创建隔离环境
git worktree add .claude/worktrees/devflow-<feature> <feature>
```

此时 worktree 只包含 git-tracked 文件。无 `node_modules`、无 `.env`、无本地数据。

#### 1.4.5 切换 CWD 到 worktree

**方案 A（优先，Claude Code 环境）：使用 EnterWorktree 原生工具**

调用 `EnterWorktree` 工具，参数：
- `path`: `.claude/worktrees/devflow-<feature>`

工具调用成功后，session CWD 自动切换到 worktree 目录。后续所有 shell 命令、文件操作均在 worktree 内执行。

**方案 B（fallback，非 Claude Code 环境）：手动 cd**

```bash
cd .claude/worktrees/devflow-<feature>
```

每个 Phase 开头会执行 CWD 守卫（见各 Phase 起始说明），发现 CWD 不在 worktree 时会警告并尝试恢复。

#### 1.4.6 补充运行时环境（策略菜单）

worktree 不含 gitignored 的运行时文件。根据项目实际情况，按以下策略菜单选择处理方式：

| 策略 | 适用场景 | 命令 |
|------|---------|------|
| **A. 包管理器安装** | `node_modules`，lockfile 已提交，本地有缓存（推荐） | `npm install` / `pnpm install` / `yarn install`（十几秒） |
| **B. Symlink / Junction** | `node_modules`，无需网络（推荐） | Unix: `ln -s <main-repo>/node_modules node_modules`<br>Windows: `mklink /J node_modules <main-repo>\node_modules` |
| **C. .worktreeinclude** | `.env`、配置文件等 gitignored 小文件，一劳永逸 | 在仓库根目录创建 `.worktreeinclude`，列出需复制的 gitignored 文件（见下方说明） |
| **D. 手动复制** | 少量配置文件，fallback | `cp <main-repo>/.env .env`（Unix）/ `Copy-Item`（PowerShell） |
| **E. 本地数据目录** | 开发数据、缓存等 | <10MB：直接复制；大数据：symlink 或纳入 `.worktreeinclude` |

**AI 执行逻辑（按顺序）：**

1. 检查仓库根目录是否存在 `.worktreeinclude` → 存在则策略 C 已自动生效（EnterWorktree 创建 worktree 时已自动复制列出的文件）
2. 检查 `package.json` / `requirements.txt` / `Cargo.toml` 等依赖清单 → 按策略 A（有网络）或 B（无网络）处理依赖目录
3. 检查 `.env`、`.env.local`、`config/secrets.json` 等配置文件 → 按策略 D 复制
4. 检查本地数据目录（如 `data/`、`uploads/`、`fixtures/`） → 按策略 E 处理
5. 验证：尝试运行项目的启动命令（如 `npm run dev`），确认环境可用

**.worktreeinclude 引导：**

如果检测到仓库没有 `.worktreeinclude`，向用户提示：

> "检测到仓库中没有 `.worktreeinclude` 文件。建议创建此文件以自动同步 gitignored 的运行时文件到 worktree。我可以帮你创建一个，包含常见的配置文件和本地数据目录。是否需要？"

如用户确认，创建 `.worktreeinclude` 并提交到 target branch。示例内容：

```
# .worktreeinclude — gitignore-style patterns for files EnterWorktree should copy
.env
.env.local
config/secrets.json
data/fixtures/
```

**settings.json 引导（可选）：**

如果检测到 `.claude/settings.json` 未配置 `worktree.symlinkDirectories`，提示用户可添加：

```json
{
  "worktree": {
    "symlinkDirectories": ["node_modules"]
  }
}
```

这样后续创建 worktree 时 `node_modules` 自动 symlink，无需每次手动处理。

#### 1.4.7 初始化状态目录和文件

在 worktree 内创建 `devflow/<feature>/` 目录，写入 `state.json`：

```json
{
  "feature": "<feature-name>",
  "phase": "breakdown",
  "created_at": "<ISO timestamp>",
  "version": "3.0",
  "requirements_confirmed": true,
  "open_questions": ["<待澄清项>"],
  "isolation": {
    "type": "worktree",
    "path": ".claude/worktrees/devflow-<feature>",
    "branch": "<feature>",
    "target_branch": "<target-branch>",
    "created_at": "<ISO timestamp>"
  },
  "checkpoints": {
    "clarify": "done",
    "breakdown": "in_progress",
    "blueprint": "pending",
    "implement": "pending",
    "verify": "pending"
  }
}
```

新增 `isolation` 字段记录 worktree 元数据，便于 Phase 6.5 清理时定位。

#### 1.4.8 提示用户

> "会话 `<feature>` 已在 git worktree `.claude/worktrees/devflow-<feature>` 中准备就绪（基于 `<target-branch>`）。已根据项目情况补充运行时环境（node_modules: <策略>; 配置/数据: <策略>）。可立即启动服务进行验收。后续所有文件操作将在该 worktree 内进行。"
```

- [ ] **Step 3: Verify replacement**

Read `skills/devflow/_SKILL.md` and confirm:
- Section starts with `### 1.4 初始化会话`
- All 8 sub-sections (1.4.1 through 1.4.8) are present
- No remaining references to `rsync` or `robocopy`
- The new `state.json` schema includes the `isolation` field with `type: "worktree"`

- [ ] **Step 4: Commit**

```bash
git add skills/devflow/_SKILL.md
git commit -m "feat(devflow): replace rsync full-copy with git worktree + strategy menu (v3.0)"
```

---

## Task 4: Add CWD guards at each Phase start

**Files:**
- Modify: `skills/devflow/_SKILL.md` — insert a CWD guard block at the start of each of Phase 2, 3, 4, 5, 6 (Phase 1 starts in main repo, no guard needed)

**Interfaces:**
- Consumes: `state.json` (read to find expected worktree path)
- Produces: either a confirmation that CWD is in the correct worktree, or a warning + recovery prompt
- Cooperates with: Task 3's `isolation.path` field

The guard is identical across phases. Insert it as a sub-section right after each Phase's `## Phase N` heading and before the existing first sub-section.

- [ ] **Step 1: Insert CWD guard into Phase 2**

Locate `## Phase 2: 需求拆解` (line 210). Insert the following block immediately after the heading and before `### 2.1 流程`:

```markdown

#### CWD 守卫

进入本 Phase 前，确认当前 CWD 是否在 `devflow/<feature>/state.json` 中 `isolation.path` 指定的 worktree 内：
```bash
# Unix
EXPECTED=$(jq -r .isolation.path devflow/<feature>/state.json 2>/dev/null)
[ "$(pwd -P)" != "$(cd "$EXPECTED" 2>/dev/null && pwd -P)" ] && echo "WARN: 当前不在 worktree 内" || echo "OK"

# Windows PowerShell
$state = Get-Content "devflow/<feature>/state.json" -Raw | ConvertFrom-Json
$expected = (Resolve-Path $state.isolation.path).Path
if ($PWD.Path -ne $expected) { Write-Host "WARN: 当前不在 worktree 内" } else { Write-Host "OK" }
```
- 检测为 OK：正常继续
- 检测到 WARN：尝试 `EnterWorktree path="<isolation.path>"` 恢复 CWD；如不可用，提示用户确认并执行 `cd` 恢复

```

- [ ] **Step 2: Insert identical CWD guard into Phase 3**

Locate `## Phase 3: 方案蓝图` (line ~262). Insert the same CWD guard block (with `<feature>` substituted from the active session's state) immediately after the heading.

- [ ] **Step 3: Insert identical CWD guard into Phase 4**

Locate `## Phase 4: 编码实现` (line ~282). Insert the same CWD guard block.

- [ ] **Step 4: Insert identical CWD guard into Phase 5**

Locate `## Phase 5: 测试验证` (line ~332). Insert the same CWD guard block.

- [ ] **Step 5: Insert identical CWD guard into Phase 6**

Locate `## Phase 6: 流程完成` (line ~388). Insert the same CWD guard block.

- [ ] **Step 6: Verify all five guards present**

Read `skills/devflow/_SKILL.md` and grep for `#### CWD 守卫`. Expected: 5 matches (one per Phase 2-6).

- [ ] **Step 7: Commit**

```bash
git add skills/devflow/_SKILL.md
git commit -m "feat(devflow): add per-phase CWD guards to detect lost worktree context"
```

---

## Task 5: Upgrade Phase 6.5 cleanup to ExitWorktree / git worktree remove

**Files:**
- Modify: `skills/devflow/_SKILL.md` — the `### 6.5 自动清理开发环境副本` section (currently lines 528-534)

**Interfaces:**
- Consumes: `state.json` `isolation.path` and `isolation.branch` (from Task 3)
- Produces: removed worktree directory + pruned git worktree registration + (if merged) deleted feature branch
- Cooperates with: Task 3 (Phase 1.4 must have written the `isolation` block this task reads)

- [ ] **Step 1: Read the current Phase 6.5 block**

The current `### 6.5 自动清理开发环境副本` is at lines 528-534 of `skills/devflow/_SKILL.md`.

- [ ] **Step 2: Replace Phase 6.5 with the v3.0 version**

Locate the `### 6.5 自动清理开发环境副本` heading and replace the entire section through to (but not including) `### 6.6 标记完成` with:

```markdown
### 6.5 自动清理开发环境副本

提交成功后，自动删除开发环境副本。读取 `devflow/<feature>/state.json` 中 `isolation.path` 和 `isolation.branch`。

**方案 A（优先，Claude Code 环境）：使用 ExitWorktree 原生工具**

调用 `ExitWorktree` 工具，参数：
- `action`: `"remove"`
- `discard_changes`: `false`

ExitWorktree 自动处理：切回原始主仓库目录 + 删除 worktree + 清理 git worktree 注册。

**方案 B（fallback，非 Claude Code 环境）：手动 git worktree remove**

```bash
# 切回主仓库根目录
cd <main-repo-root>

# 用 git worktree remove 删除（会自动 git worktree prune）
git worktree remove .claude/worktrees/devflow-<feature>

# 如果 feature branch 已合并到 target branch，删除分支
git branch -d <feature>  # 安全删除（仅当已合并）
# 或强制删除（不推荐，未合并时使用）：
# git branch -D <feature>
```

清理前确认 worktree 内无未提交变更（Phase 6.3 已保证）。清理失败时给出明确提示，包括：
- `git worktree remove` 报错（如 worktree 被锁定）
- 残留进程占用文件（Windows 常见）
- 提供手动清理命令

**v2.4 全量副本兼容：**

如果 `state.json` 中 `isolation.type` 缺失或 `== "fullcopy"`（v2.4 遗留），按 v2.4 方式处理：

```bash
cd <main-repo-root>
rm -rf .claude/worktrees/devflow-<feature>
```

并跳过 `git worktree prune` / `git branch -d`（v2.4 副本不是 git worktree，feature branch 需用户手动管理）。
```

- [ ] **Step 3: Verify replacement**

Read `skills/devflow/_SKILL.md` lines around the Phase 6.5 section. Confirm:
- Both ExitWorktree (preferred) and `git worktree remove` (fallback) are documented
- The `state.json` `isolation` field is referenced
- v2.4 fallback is included for backward compat

- [ ] **Step 4: Commit**

```bash
git add skills/devflow/_SKILL.md
git commit -m "feat(devflow): upgrade cleanup to ExitWorktree / git worktree remove (v3.0)"
```

---

## Task 6: Bump header version and state.json schema

**Files:**
- Modify: `skills/devflow/_SKILL.md` — front matter description, H1 title, state.json example block

**Interfaces:**
- Cooperates with: Task 1 (plugin manifest version bump). Both should be `3.0.x` and `3.0`/`3.0.0` respectively.
- The Codex `SKILL.md` is generated from `_SKILL.md` by `scripts/sync-skills.js` — the sync strips `allowed-tools:` lines, so both files end up showing version references identically.

- [ ] **Step 1: Update front matter description**

In `skills/devflow/_SKILL.md` line 3, replace:

```
description: DevFlow v2.4 — AI 开发规范流程，单一入口，按阶段推进完整开发流程。支持完整副本会话隔离与强制合并验证，防止多 feature 并行开发时的冲突与语义回归。
```

with:

```
description: DevFlow v3.0 — AI 开发规范流程，单一入口，按阶段推进完整开发流程。基于 git worktree 会话隔离与强制合并验证，防止多 feature 并行开发时的冲突与语义回归。
```

- [ ] **Step 2: Update H1 title**

In `skills/devflow/_SKILL.md` line 9, replace:

```
# /devflow — DevFlow v2.4
```

with:

```
# /devflow — DevFlow v3.0
```

- [ ] **Step 3: Update state.json schema example**

In `skills/devflow/_SKILL.md`, find the `## 状态持久化格式` section (line ~587) and update the example `state.json` to:

```json
{
  "feature": "user-auth",
  "phase": "implement",
  "created_at": "2026-06-24T14:30:00+08:00",
  "version": "3.0",
  "isolation": {
    "type": "worktree",
    "path": ".claude/worktrees/devflow-user-auth",
    "branch": "user-auth",
    "target_branch": "main",
    "created_at": "2026-06-24T14:30:00+08:00"
  },
  "checkpoints": {
    "clarify": "done",
    "breakdown": "done",
    "blueprint": "done",
    "implement": "in_progress",
    "verify": "pending"
  },
  "open_questions": [],
  "rollback_history": []
}
```

- [ ] **Step 4: Update footer**

At the bottom of `skills/devflow/_SKILL.md` (line ~640), replace:

```
*DevFlow v2.4 — 单一入口，完整副本隔离，合并验证，闭环管理。*
```

with:

```
*DevFlow v3.0 — 单一入口，git worktree 隔离，策略菜单补充运行时，合并验证，闭环管理。*
```

- [ ] **Step 5: Update the v2.4 mentions in the skill body**

Grep `skills/devflow/_SKILL.md` for remaining occurrences of "v2.4" or "完整副本" or "rsync" / "robocopy" (excluding the v2.4 backward-compat references in Step 0.3 and Phase 6.5 which should stay). Each remaining instance is in either:
- An error message example (line 66: "v2.4 起会话...") — update to "v3.0"
- A management command description (line 75) — update to "v3.0"

Use Edit tool to replace each. Do NOT replace references in the Step 0 detection table (v2.4 is intentionally mentioned for backward compat) or in Phase 6.5 fallback.

- [ ] **Step 6: Verify no stale rsync references remain**

Grep `skills/devflow/_SKILL.md` for `rsync` and `robocopy`. Expected: zero matches in actionable instructions (these tools should no longer be referenced for session creation).

- [ ] **Step 7: Commit**

```bash
git add skills/devflow/_SKILL.md
git commit -m "chore(devflow): bump skill header to v3.0, update state.json schema"
```

---

## Task 7: Sync Codex SKILL.md and verify

**Files:**
- Modify: `skills/devflow/SKILL.md` (regenerated from `_SKILL.md`)
- Run: `scripts/sync-skills.js`

**Interfaces:**
- The sync script (per `scripts/sync-skills.js`) reads `_SKILL.md`, strips `allowed-tools:` lines, and writes to `SKILL.md`. It does not validate content otherwise.

- [ ] **Step 1: Run the sync**

Run: `node scripts/sync-skills.js`

Expected output:
```
Syncing N skills...
[forward] devflow/SKILL.md <- _SKILL.md
Done.
```

(where N is the count of skill directories in `skills/`)

- [ ] **Step 2: Verify the Codex file has the new content**

Run: `head -5 skills/devflow/SKILL.md`

Expected first 5 lines match the front matter of `_SKILL.md` (sans `allowed-tools:` line, which is stripped).

- [ ] **Step 3: Verify no `allowed-tools` line in the Codex file**

Run: `grep "allowed-tools:" skills/devflow/SKILL.md`

Expected: no output (sync strips it). If output present, the sync didn't strip — investigate `scripts/sync-skills.js`.

- [ ] **Step 4: Verify Codex file has v3.0 references**

Run: `grep -c "v3.0\|v2.4" skills/devflow/SKILL.md`

Expected: multiple matches; verify each is intentional (v3.0 = current, v2.4 = backward-compat only).

- [ ] **Step 5: Commit the regenerated file**

```bash
git add skills/devflow/SKILL.md
git commit -m "chore(devflow): sync Codex SKILL.md from v3.0 source"
```

---

## Task 8: Final review and validation

**Files:** None modified; validation pass only.

- [ ] **Step 1: Verify all commits are present**

Run: `git log --oneline -10`

Expected: 8 commits corresponding to Tasks 1-7, plus this Task 8's validation may add a final summary commit if needed.

- [ ] **Step 2: Run a full grep audit**

Run:
```bash
grep -nE "rsync|robocopy" skills/devflow/_SKILL.md skills/devflow/SKILL.md
```

Expected: only references in backward-compat sections (Phase 6.5 fallback for v2.4 directories). Zero matches in Phase 1.4 (session creation) or Step 0 (detection).

- [ ] **Step 3: Verify both files are valid markdown**

Run:
```bash
head -1 skills/devflow/_SKILL.md
head -1 skills/devflow/SKILL.md
```

Both should start with `---` (front matter delimiter).

- [ ] **Step 4: Cross-check plugin version matches skill version**

```bash
grep '"version"' .claude-plugin/plugin.json
grep 'v3.0' skills/devflow/_SKILL.md | head -5
```

Both should reference `3.0`.

- [ ] **Step 5: Final summary commit (if any uncommitted changes)**

```bash
git status
git add -A  # only if there are uncommitted changes
git commit -m "chore(devflow): v3.0 session isolation migration complete"
```

If nothing to commit, skip this step.

---

## Summary of Changes

| Component | v2.4 (before) | v3.0 (after) |
|-----------|--------------|--------------|
| Session creation | `rsync`/`robocopy` full copy (minutes, 500GB risk) | `git worktree add` (seconds) + 5-strategy menu for runtime |
| CWD switch | Manual `cd`, AI forgets | `EnterWorktree` (native tool) + per-phase guard |
| Step 0 detection | Path-based only | `GIT_DIR != GIT_COMMON` + path fallback (v2.4 compat) |
| Cleanup | `rm -rf` (manual) | `ExitWorktree` (preferred) / `git worktree remove` (fallback) |
| state.json | `version: "2.4"`, no isolation metadata | `version: "3.0"`, `isolation.{type,path,branch,target_branch}` |
| Plugin manifest | `version: "2.4.0"` | `version: "3.0.0"` |

## Risk Mitigations Recap

- **EnterWorktree/ExitWorktree not available:** `cd` and `git worktree remove` fallbacks documented
- **Symlink compatibility issues:** Strategy A (`npm install`) available as alternative
- **.worktreeinclude missing:** AI detects and offers to create
- **v2.4 leftover directories:** Step 0 + Phase 6.5 both detect and handle

## Out of Scope (Documented for Future Plans)

- Auto-creating `.worktreeinclude` from `.gitignore` analysis (could be a Phase 7 enhancement)
- Symlink validation across tools (some Windows tools don't follow junctions)
- Multi-worktree parallel execution beyond `/devflow` (current design assumes one session per invocation)
