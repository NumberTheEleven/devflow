# DevFlow Mode Selection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Modify `skills/devflow/SKILL.md` to support three workflow startup modes: `feat-branch`, `main-branch`, and `worktree`, with mode-aware initialization, CWD guards, and Phase 6 cleanup.

**Architecture:** Keep the single `SKILL.md` document as the source of truth. Introduce `isolation.mode` as the routing key in `state.json`, and restructure Phase 1.4 and Phase 6 into three parallel sub-flows. Phase 2-5 remain mode-agnostic but use updated CWD guards that inspect `isolation.mode`.

**Tech Stack:** Markdown skill specification, git, Claude Code `EnterWorktree`/`ExitWorktree` tools.

## Global Constraints

- `isolation.mode` must be one of: `feat-branch`, `main-branch`, `worktree`
- Missing `isolation.mode` in existing state files defaults to `worktree` for backward compatibility
- `git push --force` is absolutely prohibited in all modes
- No rebase operations allowed; merge-only workflow
- All DevFlow tracking files live under `devflow/<feature>/`
- Feature name confirmation is skipped only in `main-branch` mode
- `feat-branch` mode keeps the feature branch after merge; `worktree` mode deletes it
- CWD guard for `feat-branch`/`main-branch` checks both directory and current branch

---

## Task 1: Update State File Schema Documentation

**Files:**
- Modify: `skills/devflow/SKILL.md:267-292` (state.json example in Phase 1.4.7)
- Modify: `skills/devflow/SKILL.md` (status persistence format section near end)

**Interfaces:**
- Consumes: Existing `isolation` object with `type`, `path`, `branch`, `target_branch`
- Produces: Updated `isolation` object with `mode` field added

- [ ] **Step 1: Update Phase 1.4.7 state.json example**

Replace the existing `isolation` block in the state.json example with:

```json
"isolation": {
  "mode": "worktree",
  "type": "worktree",
  "path": ".claude/worktrees/devflow-<feature>",
  "branch": "<feature>",
  "target_branch": "<target-branch>",
  "created_at": "<ISO timestamp>"
}
```

- [ ] **Step 2: Update the status persistence format section**

Near the end of `SKILL.md`, find the state.json schema block and update the `isolation` description:

```json
"isolation": {
  "mode": "worktree",
  "type": "worktree",
  "path": ".claude/worktrees/devflow-user-auth",
  "branch": "user-auth",
  "target_branch": "main",
  "created_at": "2026-06-24T14:30:00+08:00"
}
```

Add a note after the field list:

> `mode` 是路由 key，决定初始化、CWD 守卫和 Phase 6 收尾行为。旧 state.json 无 `mode` 字段时默认视为 `worktree`。

- [ ] **Step 3: Verification**

Run: `grep -n '"mode"' skills/devflow/SKILL.md`
Expected: Two occurrences, both inside `isolation` objects.

- [ ] **Step 4: Commit**

```bash
git add skills/devflow/SKILL.md
git commit -m "docs(devflow): add isolation.mode to state.json schema

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

## Task 2: Update Step 0 Entry Detection for Main-Mode Session Conflicts

**Files:**
- Modify: `skills/devflow/SKILL.md:93-104` (Step 0.4 detect active sessions)

**Interfaces:**
- Consumes: Existing Step 0 logic that checks `devflow/state.json` in main repo
- Produces: Updated Step 0.4 that also blocks new `main-branch` sessions when one is active

- [ ] **Step 1: Update Step 0.4 active session check**

After the existing paragraph about `devflow/state.json`, add a new subsection:

### 0.4.1 检查是否已有未完成的 main 模式会话

仅在判定处于主仓库时执行。遍历 `devflow/*/` 下所有 `state.json`：

```bash
# 伪代码
for dir in devflow/*/; do
  mode=$(jq -r '.isolation.mode // "worktree"' "$dir/state.json" 2>/dev/null)
  phase=$(jq -r '.phase' "$dir/state.json" 2>/dev/null)
  if [ "$mode" = "main-branch" ] && [ "$phase" != "completed" ]; then
    echo "检测到未完成的 main 模式会话（feature: <feature>，当前阶段：$phase）。同一时刻只能有一个 main 模式会话。"
    exit 1
  fi
done
```

- 存在未完成的 main 模式会话：报错并停止，提示用户完成或标记完成后开始新会话
- 不存在：继续原有 0.4 逻辑

- [ ] **Step 2: Update Step 0.3 decision table note**

Add a note after the 0.3 table:

> 判定处于主仓库时，还需检查 0.4.1，防止多个 main 模式会话同时运行。

- [ ] **Step 3: Verification**

Run: `grep -n "main 模式会话" skills/devflow/SKILL.md`
Expected: At least two occurrences (one in 0.4.1, one in the note).

- [ ] **Step 4: Commit**

```bash
git add skills/devflow/SKILL.md
git commit -m "docs(devflow): block concurrent main-branch sessions in Step 0

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

## Task 3: Add Phase 1.35 Mode Selection and Update Phase 1.3 Feature Naming

**Files:**
- Modify: `skills/devflow/SKILL.md:151-157` (Phase 1.3 feature naming)
- Modify: `skills/devflow/SKILL.md:158` (insert new Phase 1.35 before Phase 1.4)

**Interfaces:**
- Consumes: User confirmation from Phase 1.2 checkpoint
- Produces: Selected `mode` and confirmed `feature` name (where applicable)

- [ ] **Step 1: Update Phase 1.3 to be conditional**

Replace the Phase 1.3 section with:

### 1.3 提炼 Feature 名称

从确认的需求中提炼一个简短的 feature 名称：

- 使用英文小写 + 连字符（如 `user-auth`、`payment-flow`、`fix-login-timeout`）
- 4 个词以内，描述性强
- 如果用户后续选择了 `main-branch` 模式，feature 名称仅用于 `devflow/<feature>/` 目录名，不作为分支名

向用户确认："基于需求，feature 名称建议为 `xxx`，可以吗？"

- 用户确认后暂存 feature 名称，进入 Phase 1.35 模式选择
- 若用户最终选择 `main-branch` 模式，feature 名称仅用于跟踪目录

- [ ] **Step 2: Insert Phase 1.35 mode selection**

Insert a new section between Phase 1.3 and Phase 1.4:

### 1.35 选择开发模式

在需求澄清确认后、初始化会话前，展示模式选择：

> 需求已确认。请选择本次开发模式：
> 1. **worktree 分支分库开发**（推荐）：创建独立 worktree，完全隔离，适合改动大的 feature（当前 v3.0 默认）
> 2. **feat 分支开发**：在主仓库中创建 feat/* 分支直接开发，不创建 worktree，避免 worktree 环境/端口问题
> 3. **main 分支开发**：直接在 main/master 上开发，不创建分支和 worktree，适合极小改动或紧急修复
>
> 回复数字或名称选择。

- 用户选择 `worktree` 或 `feat-branch`：使用 Phase 1.3 确认的 feature 名称
- 用户选择 `main-branch`：feature 名称降级为仅用于 `devflow/<feature>/` 目录名

选择 `main-branch` 时追加风险提示：

> 你选择了 main 分支开发模式。所有改动将直接提交到 `<target-branch>` 并推送到远端。该模式不适合需要代码审查或可能破坏主干的较大改动。是否确认继续？
>
> 回复 **确认 / Yes / Y** 继续；否则返回模式选择。

- [ ] **Step 3: Update Phase 1.4 intro**

Change "Feature 名称确认后，执行以下步骤" to:

> Feature 名称确认且模式选择完成后，执行以下步骤。

- [ ] **Step 4: Verification**

Run: `grep -n "Phase 1.35" skills/devflow/SKILL.md`
Expected: One occurrence.

Run: `grep -n "选择开发模式" skills/devflow/SKILL.md`
Expected: One occurrence in Phase 1.35.

- [ ] **Step 5: Commit**

```bash
git add skills/devflow/SKILL.md
git commit -m "docs(devflow): add Phase 1.35 mode selection and conditional feature naming

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

## Task 4: Restructure Phase 1.4 into Mode-Specific Initialization Paths

**Files:**
- Modify: `skills/devflow/SKILL.md:158-303` (Phase 1.4 initialization)

**Interfaces:**
- Consumes: `mode` from Phase 1.35, `feature` name from Phase 1.3
- Produces: `state.json` with fully populated `isolation` object

- [ ] **Step 1: Rewrite Phase 1.4 intro**

Replace the current Phase 1.4 intro with:

### 1.4 初始化会话

Feature 名称确认且模式选择完成后，按所选模式初始化会话。三种模式共享前置步骤 1.4.1 和 1.4.2，之后进入各自的初始化路径。

#### 1.4.1 自动识别目标分支

检查 `master` 和 `main`，按以下优先级：

- 仅存在 `main` → 使用 `main`
- 仅存在 `master` → 使用 `master`
- 同时存在 → 默认使用 `main`
- 都不存在 → 报错并停止

#### 1.4.2 检查冲突

- **worktree / feat 模式**：检查是否已存在同名 branch 或开发环境目录
  ```bash
  git branch --list <feature>
  ls -d .claude/worktrees/devflow-<feature> 2>/dev/null
  ```
  - 存在：报错 "feature 名称 `<feature>` 已存在（branch 或开发环境），请更换名称。"
  - 不存在：继续

- **main 模式**：Step 0 已检查未完成的 main 模式会话，此处不再重复

- [ ] **Step 2: Add worktree mode initialization section**

After 1.4.2, add:

#### 1.4.3 worktree 模式初始化

执行当前 v3.0 的初始化流程：

```bash
git checkout -b <feature>
git checkout <target-branch>
git worktree add .claude/worktrees/devflow-<feature> <feature>
EnterWorktree path=".claude/worktrees/devflow-<feature>"
```

然后按 1.4.4 补充运行时环境。

`state.json` 的 `isolation`：

```json
"isolation": {
  "mode": "worktree",
  "type": "worktree",
  "path": ".claude/worktrees/devflow-<feature>",
  "branch": "<feature>",
  "target_branch": "<target-branch>"
}
```

- [ ] **Step 3: Add feat-branch mode initialization section**

After the worktree section, add:

#### 1.4.4 feat 分支模式初始化

```bash
git checkout -b <feature>
```

不创建 worktree，留在主仓库当前目录。`devflow/<feature>/` 目录创建在主仓库中。

`state.json` 的 `isolation`：

```json
"isolation": {
  "mode": "feat-branch",
  "path": ".",
  "branch": "<feature>",
  "target_branch": "<target-branch>"
}
```

- [ ] **Step 4: Add main-branch mode initialization section**

After the feat section, add:

#### 1.4.5 main 分支模式初始化

```bash
git checkout <target-branch>
```

不创建分支，不创建 worktree。`feature` 名称仅用于 `devflow/<feature>/` 目录名。

`state.json` 的 `isolation`：

```json
"isolation": {
  "mode": "main-branch",
  "path": ".",
  "branch": "<target-branch>",
  "target_branch": "<target-branch>"
}
```

- [ ] **Step 5: Add workspace cleanliness prompt for feat/main modes**

After the mode-specific sections, add:

#### 1.4.6 工作区状态提示（feat/main 模式专用）

因为 feat/main 模式直接修改主仓库工作区，初始化前检查：

```bash
git status --short
```

- **无未提交变更**：直接继续
- **存在未提交变更**：提示但不阻塞：
  > "检测到工作区存在未提交变更。若继续，这些变更将被纳入本次 DevFlow 会话的开发范围。是否继续？
  > - 回复 **继续**：开始本次会话
  > - 回复 **清理**：请先 stash / commit / 丢弃变更后再开始"

worktree 模式不需要此检查。

- [ ] **Step 6: Update runtime environment supplement section**

Change the existing 1.4.6 to 1.4.7, and update the first paragraph:

> worktree 模式下不含 gitignored 的运行时文件，需按策略菜单补充。feat/main 模式下主仓库已有运行时环境，通常无需额外补充，但可按项目情况确认。

- [ ] **Step 7: Update state file initialization section number**

Change existing 1.4.7 to 1.4.8, and ensure the `state.json` example uses the updated `isolation` block from Task 1.

- [ ] **Step 8: Update prompt section number**

Change existing 1.4.8 to 1.4.9.

- [ ] **Step 9: Verification**

Run: `grep -n "1.4.3 worktree" skills/devflow/SKILL.md`
Expected: One occurrence.

Run: `grep -n "1.4.4 feat" skills/devflow/SKILL.md`
Expected: One occurrence.

Run: `grep -n "1.4.5 main" skills/devflow/SKILL.md`
Expected: One occurrence.

Run: `grep -n "isolation.mode" skills/devflow/SKILL.md`
Expected: At least three occurrences (one per mode example).

- [ ] **Step 10: Commit**

```bash
git add skills/devflow/SKILL.md
git commit -m "docs(devflow): restructure Phase 1.4 into three mode-specific init paths

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

## Task 5: Update CWD Guards in Phase 2-5 to Be Mode-Aware

**Files:**
- Modify: `skills/devflow/SKILL.md:311-325` (Phase 2 CWD guard)
- Modify: `skills/devflow/SKILL.md:366-380` (Phase 3 CWD guard)
- Modify: `skills/devflow/SKILL.md:413-427` (Phase 4 CWD guard)
- Modify: `skills/devflow/SKILL.md:477-491` (Phase 5 CWD guard)

**Interfaces:**
- Consumes: `isolation.mode`, `isolation.path`, `isolation.branch` from `state.json`
- Produces: Updated CWD guard logic that works for all three modes

- [ ] **Step 1: Create reusable CWD guard snippet**

Replace each CWD guard block with the following (identical in all four phases):

```bash
# Unix
MODE=$(jq -r '.isolation.mode // "worktree"' devflow/<feature>/state.json 2>/dev/null)
EXPECTED=$(jq -r .isolation.path devflow/<feature>/state.json 2>/dev/null)
EXPECTED_BRANCH=$(jq -r .isolation.branch devflow/<feature>/state.json 2>/dev/null)

if [ "$MODE" = "worktree" ]; then
  [ "$(pwd -P)" = "$(cd "$EXPECTED" 2>/dev/null && pwd -P)" ] && echo "OK" || echo "WARN: 当前不在 worktree 内"
elif [ "$MODE" = "feat-branch" ] || [ "$MODE" = "main-branch" ]; then
  CURRENT_BRANCH=$(git branch --show-current 2>/dev/null)
  if [ "$(pwd -P)" = "$(cd "$EXPECTED" 2>/dev/null && pwd -P)" ] && [ "$CURRENT_BRANCH" = "$EXPECTED_BRANCH" ]; then
    echo "OK"
  else
    echo "WARN: 当前不在主仓库正确分支内（期望分支: $EXPECTED_BRANCH）"
  fi
fi

# Windows PowerShell
$state = Get-Content "devflow/<feature>/state.json" -Raw | ConvertFrom-Json
$mode = $state.isolation.mode ?? "worktree"
$expected = (Resolve-Path $state.isolation.path -ErrorAction SilentlyContinue).Path
$expectedBranch = $state.isolation.branch

if ($mode -eq "worktree") {
  if ($PWD.Path -eq $expected) { Write-Host "OK" } else { Write-Host "WARN: 当前不在 worktree 内" }
} elseif ($mode -in @("feat-branch", "main-branch")) {
  $currentBranch = git branch --show-current 2>$null
  if ($PWD.Path -eq $expected -and $currentBranch -eq $expectedBranch) {
    Write-Host "OK"
  } else {
    Write-Host "WARN: 当前不在主仓库正确分支内（期望分支: $expectedBranch）"
  }
}
```

- [ ] **Step 2: Update WARN recovery behavior in each phase**

After each CWD guard, replace the recovery bullet with:

- **worktree 模式且检测到 WARN**：尝试 `EnterWorktree path="<isolation.path>"`；如不可用，提示用户确认并执行 `cd` 恢复
- **feat 模式且检测到 WARN**：提示用户执行 `git checkout <feature>` 并 `cd <main-repo-root>`
- **main 模式且检测到 WARN**：提示用户执行 `git checkout <target-branch>` 并 `cd <main-repo-root>`

- [ ] **Step 3: Verification**

Run: `grep -n 'isolation.mode // "worktree"' skills/devflow/SKILL.md | wc -l`
Expected: 4 (one per phase guard).

Run: `grep -n "期望分支" skills/devflow/SKILL.md | wc -l`
Expected: 4.

- [ ] **Step 4: Commit**

```bash
git add skills/devflow/SKILL.md
git commit -m "docs(devflow): make Phase 2-5 CWD guards mode-aware

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

## Task 6: Restructure Phase 6 into Mode-Specific Cleanup/Merge Paths

**Files:**
- Modify: `skills/devflow/SKILL.md` Phase 6 section (around line 525 to end of Phase 6)

**Interfaces:**
- Consumes: `isolation.mode`, `isolation.branch`, `isolation.path`, `isolation.target_branch`
- Produces: Mode-specific merge/cleanup instructions and completed state

- [ ] **Step 1: Update Phase 6 intro**

After the CWD guard, add a high-level routing note:

### 6.0 模式路由

Phase 6 的收尾逻辑按 `isolation.mode` 分为三条路径：

- `worktree`：保持现有 v3.0 流程（合并验证 → 预完成提交 → 合并到 target → 删除 worktree + 分支）
- `feat-branch`：在主仓库中把 target 同步到 feat，再合并 feat 到 target，保留 feat 分支
- `main-branch`：在主仓库中同步 target 后直接 push，不创建/删除分支

- [ ] **Step 2: Add common Phase 6 preface**

After 6.0, add:

### 6.1 确认

> "DevFlow 流程已通过人工验收。是否结束会话并提交？回复 **确认 / Yes / Y** 完成并提交；否则请说明。"

### 6.2 预完成提交（兜底保护）

所有模式共享：

1. `git status --porcelain` 检查未提交变更
2. 存在超大未追踪文件（>10MB）时单独警告
3. 按现有规则自动提交或用户选择跳过

- [ ] **Step 3: Move existing worktree flow under explicit section**

Rename the existing Phase 6.2-6.5 sections to be nested under:

### 6.3 worktree 模式收尾

保持原 6.2（合并验证）、6.3（预完成提交，注意与新增 6.2 合并）、6.4（合并到 target）、6.5（清理）内容。

注意：由于新增 6.2 已包含预完成提交，worktree 模式下的原 6.3 应移除或改为引用。

- [ ] **Step 4: Add feat-branch mode cleanup section**

### 6.4 feat 分支模式收尾

```bash
# 1. 切到 target，安全同步远端
git checkout <target-branch>
git fetch origin
git merge --ff-only origin/<target-branch>   # 失败则硬停止

# 2. 切到 feat，把 target 最新内容合并进来
git checkout <feature>
git merge <target-branch>                    # 处理冲突

# 3. 重跑当前 feature 测试用例
# ...

# 4. 切回 target，把 feat 合并进去（--no-ff）
git checkout <target-branch>
git merge --no-ff <feature>

# 5. 推送前 fast-forward 预检
git merge-base --is-ancestor origin/<target-branch> HEAD || echo "REJECT"

# 6. 推送
git push origin <target-branch>

# 7. 保留 feat 分支，不删除
```

- [ ] **Step 5: Add main-branch mode cleanup section**

### 6.5 main 分支模式收尾

```bash
# 1. 切到 target，安全同步远端
git checkout <target-branch>
git fetch origin
git merge --ff-only origin/<target-branch>   # 失败则硬停止

# 2. 推送前 fast-forward 预检
git merge-base --is-ancestor origin/<target-branch> HEAD || echo "REJECT"

# 3. 推送
git push origin <target-branch>
```

注意：

- main 模式不执行 catch-up merge（已在 target 上）
- 仍需执行 `git merge --ff-only origin/<target-branch>` 安全检查
- 推送前同样做 fast-forward 预检

- [ ] **Step 6: Add cleanup summary section**

### 6.6 清理总结

- **worktree 模式**：`ExitWorktree remove` + 删除 feature 分支
- **feat 模式**：无 worktree 清理，保留 feature 分支
- **main 模式**：无 worktree 清理，无分支删除

所有模式最后更新 `state.json`：`phase: "completed"`。

- [ ] **Step 7: Verification**

Run: `grep -n "### 6.3 worktree 模式收尾" skills/devflow/SKILL.md`
Expected: One occurrence.

Run: `grep -n "### 6.4 feat 分支模式收尾" skills/devflow/SKILL.md`
Expected: One occurrence.

Run: `grep -n "### 6.5 main 分支模式收尾" skills/devflow/SKILL.md`
Expected: One occurrence.

Run: `grep -n "保留 feat 分支" skills/devflow/SKILL.md`
Expected: One occurrence in Phase 6.4.

- [ ] **Step 8: Commit**

```bash
git add skills/devflow/SKILL.md
git commit -m "docs(devflow): restructure Phase 6 into mode-specific cleanup/merge paths

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

## Task 7: Add Mode Migration Reference and Backward Compatibility Notes

**Files:**
- Modify: `skills/devflow/SKILL.md` error handling / backward compatibility section near end

**Interfaces:**
- Consumes: Three mode definitions
- Produces: Reference table for mode migration and backward compatibility statement

- [ ] **Step 1: Add backward compatibility note**

In the error handling / backward compatibility section, add:

### 旧会话兼容

- 现有 v3.0 `state.json` 若缺少 `isolation.mode` 字段，恢复时默认视为 `worktree`
- v2.4 全量副本会话（`isolation.type == "fullcopy"`）仍按原有 v2.4 兼容逻辑处理，不受本模式选择影响

- [ ] **Step 2: Add mode migration reference table**

Add a new subsection:

### 模式间迁移（按需执行）

当用户明确提出切换模式时，AI 可协助执行：

| 源模式 | 目标模式 | 操作步骤 |
|--------|----------|----------|
| main | feat | `git stash` → `git checkout -b <feature>` → `git stash pop` → 更新 `state.json` 的 `isolation.mode`/`branch`/`path` |
| feat | main | `git reset --soft HEAD~N`（N 为本次会话产生的 commit 数）→ `git stash` → `git checkout <target-branch>` → `git stash pop` → 更新 `state.json` |
| main | worktree | `git stash` → `git checkout -b <feature>` → `git worktree add .claude/worktrees/devflow-<feature> <feature>` → `EnterWorktree` → `git stash pop` → 更新 `state.json` |
| worktree | main | 在 worktree 中 `git reset --soft HEAD~N`（N 为本次会话产生的 commit 数）→ `git stash` → 切回主仓库 `git checkout <target-branch>` → `git stash pop` → 更新 `state.json` |
| feat | worktree | 在 feat 分支上 `git worktree add .claude/worktrees/devflow-<feature> <feature>` → `EnterWorktree` → 复制 `devflow/<feature>/` 跟踪文件到 worktree → 更新 `state.json` |
| worktree | feat | 切回主仓库 `git checkout <feature>` → 复制 worktree 中的 `devflow/<feature>/` 跟踪文件到主仓库 → 更新 `state.json` |

迁移不是主流程功能，仅应用户明确要求时执行。迁移后必须重新做 CWD 守卫验证。

- [ ] **Step 3: Verification**

Run: `grep -n "模式间迁移" skills/devflow/SKILL.md`
Expected: One occurrence.

Run: `grep -n "旧会话兼容" skills/devflow/SKILL.md`
Expected: One occurrence.

- [ ] **Step 4: Commit**

```bash
git add skills/devflow/SKILL.md
git commit -m "docs(devflow): add mode migration reference and backward compatibility notes

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

## Task 8: Final Consistency Review

**Files:**
- Read: `skills/devflow/SKILL.md` (full file after all edits)

**Interfaces:**
- Consumes: All modified sections
- Produces: Verified consistency across the skill document

- [ ] **Step 1: Section numbering check**

Verify that Phase 1.4 subsection numbers are sequential and consistent:
- 1.4.1 target branch identification
- 1.4.2 conflict check
- 1.4.3 worktree init
- 1.4.4 feat init
- 1.4.5 main init
- 1.4.6 workspace status prompt
- 1.4.7 runtime environment supplement
- 1.4.8 state file init
- 1.4.9 user prompt

- [ ] **Step 2: Phase 6 numbering check**

Verify Phase 6 subsection numbers are sequential:
- 6.0 mode routing
- 6.1 confirmation
- 6.2 pre-completion commit
- 6.3 worktree cleanup
- 6.4 feat cleanup
- 6.5 main cleanup
- 6.6 cleanup summary

- [ ] **Step 3: Cross-reference check**

Run: `grep -c "isolation.mode" skills/devflow/SKILL.md`
Expected: At least 7 occurrences (schema + three init examples + four CWD guards + mode routing).

Run: `grep -c "feat-branch" skills/devflow/SKILL.md`
Expected: At least 10 occurrences.

Run: `grep -c "main-branch" skills/devflow/SKILL.md`
Expected: At least 10 occurrences.

- [ ] **Step 4: Flow trace verification**

Mentally trace each mode end-to-end:
1. worktree: Phase 1.35 → 1.4.3 → Phase 2-5 CWD guard → Phase 6.3 → cleanup
2. feat: Phase 1.35 → 1.4.4 → Phase 2-5 CWD guard → Phase 6.4 → keep branch
3. main: Phase 1.35 → 1.4.5 → Phase 2-5 CWD guard → Phase 6.5 → no branch cleanup

Confirm each path has no missing steps.

- [ ] **Step 5: Commit final review notes (optional)**

If any fixes are needed, apply them and commit. If no fixes needed, no additional commit required.

---

## Plan Self-Review

### Spec Coverage

| Spec Section | Implementing Task |
|--------------|-------------------|
| `isolation.mode` abstraction | Task 1 |
| Mode selection prompt at Phase 1.35 | Task 3 |
| Conditional feature naming (skip for main) | Task 3 |
| Step 0 main-mode conflict check | Task 2 |
| Phase 1.4 three init paths | Task 4 |
| Workspace status prompt for feat/main | Task 4 |
| Mode-aware CWD guards | Task 5 |
| Phase 6 three cleanup/merge paths | Task 6 |
| Backward compatibility | Task 7 |
| Mode migration reference | Task 7 |

**No gaps identified.**

### Placeholder Scan

- No `TBD`, `TODO`, or "implement later" strings
- All code blocks contain concrete markdown/commands
- No vague instructions like "add appropriate validation"

### Type/Term Consistency

- `isolation.mode` values consistently use `feat-branch`, `main-branch`, `worktree`
- `<target-branch>` placeholder used consistently instead of hardcoded `main`
- `<feature>` placeholder used consistently for branch/directory name
- `EnterWorktree` and `ExitWorktree` tool names preserved

---

## Execution Handoff

**Plan complete and saved to `docs/superpowers/plans/2026-07-08-devflow-mode-selection.md`.**

Two execution options:

**1. Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration.

**2. Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints.

Which approach would you like to use?
