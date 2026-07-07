# DevFlow 模式选择设计 — feat / main / worktree 三种开发模式

**Date:** 2026-07-08
**Status:** Draft
**Context:** 在 DevFlow v3.0 的 git worktree 隔离基础上，增加流程启动时的模式选择，允许用户根据实际场景选择 feat 分支开发、main 分支开发或 worktree 分支分库开发。

---

## 问题回顾

DevFlow v3.0 默认使用 git worktree 做会话隔离，但用户反馈 worktree 流程偶尔仍有问题：

| 痛点 | 表现 |
|------|------|
| 端口/服务冲突 | 多个 worktree 同时跑 dev server 时端口占用 |
| 运行时环境缺失 | worktree 缺少 node_modules / .env / 配置文件 |
| CWD 上下文丢失 | AI 后续 turn 忘记在 worktree 内工作 |
| 合并/清理失败 | Phase 6 合并回主仓库时冲突、worktree 残留无法清理 |

这些痛点并非所有任务都会遇到。对于小改动、紧急修复或环境敏感的任务，用户希望能在主仓库直接开发，而不是强制进入 worktree。

---

## 设计目标

1. **保留 worktree 模式作为默认推荐**，不改 v3.0 主路径
2. **新增 feat 分支模式**：在主仓库创建 feat/* 分支直接开发，不创建 worktree
3. **新增 main 分支模式**：直接在 main/master 上开发，不创建分支和 worktree
4. **模式选择发生在需求澄清确认后、初始化会话前**
5. **Phase 2-5 保持 mode 无关**，Phase 6 按 mode 路由收尾
6. **向后兼容**：旧 v3.0 无 `isolation.mode` 的状态文件默认视为 worktree 模式
7. **模式迁移可行**：当用户需要时，提供任意两种模式之间的迁移方法

---

## 总体架构

### 修改后的 Phase 1 流程

```
Phase 1.2 checkpoint 用户确认需求
           ↓
Phase 1.3 提炼 feature 名称
           ↓  仅当 mode ≠ main-branch
Phase 1.35 选择开发模式（新增）
           ├─ feat-branch
           ├─ main-branch
           └─ worktree
           ↓
Phase 1.4 按 mode 初始化会话
           ↓
Phase 2-5（公共流程，不感知 mode）
```

### 核心抽象：`isolation.mode`

`devflow/<feature>/state.json` 中的 `isolation` 字段扩展为：

```json
{
  "isolation": {
    "mode": "feat-branch | main-branch | worktree",
    "path": "...",
    "branch": "...",
    "target_branch": "...",
    "created_at": "..."
  }
}
```

| 字段 | 含义 |
|------|------|
| `mode` | 路由 key，决定初始化、CWD 守卫、Phase 6 收尾行为 |
| `path` | 开发工作目录。feat/main 模式下为主仓库根目录（`.`）；worktree 模式下为 `.claude/worktrees/devflow-<feature>` |
| `branch` | 当前开发分支。feat 模式下为 feat 分支名；main 模式下为 `main`/`master`；worktree 模式下为 worktree 对应分支名 |
| `target_branch` | 最终要合并到的目标分支（`main` 或 `master`） |

---

## 模式选择 Prompt

在需求澄清确认后、初始化会话前展示：

> 需求已确认。请选择本次开发模式：
> 1. **worktree 分支分库开发**（推荐）：创建独立 worktree，完全隔离，适合改动大的 feature（当前 v3.0 默认）
> 2. **feat 分支开发**：在主仓库中创建 feat/* 分支直接开发，不创建 worktree，避免 worktree 环境/端口问题
> 3. **main 分支开发**：直接在 main/master 上开发，不创建分支和 worktree，适合极小改动或紧急修复
>
> 回复数字或名称选择。

选择 **main-branch** 时追加风险提示：

> 你选择了 main 分支开发模式。所有改动将直接提交到 `<target-branch>` 并推送到远端。该模式不适合需要代码审查或可能破坏主干的较大改动。是否确认继续？

---

## Phase 1.4：按模式初始化会话

### 公共前置：识别 target_branch

三种模式都先执行：

```bash
# 仅存在 main → main
# 仅存在 master → master
# 同时存在 → main
# 都不存在 → 报错并停止
```

### worktree 模式（保持 v3.0）

```bash
git checkout -b <feature>
git checkout <target-branch>
git worktree add .claude/worktrees/devflow-<feature> <feature>
EnterWorktree path=".claude/worktrees/devflow-<feature>"
# 运行时环境补充（策略菜单 A-E）
```

`state.json`：

```json
"isolation": {
  "mode": "worktree",
  "path": ".claude/worktrees/devflow-<feature>",
  "branch": "<feature>",
  "target_branch": "<target-branch>"
}
```

### feat 分支模式（新增）

```bash
git checkout -b <feature>
# 不创建 worktree，留在主仓库
```

`state.json`：

```json
"isolation": {
  "mode": "feat-branch",
  "path": ".",
  "branch": "<feature>",
  "target_branch": "<target-branch>"
}
```

### main 分支模式（新增）

```bash
git checkout <target-branch>
# 不创建分支，不创建 worktree
```

需要一个 **feature 标识** 仅用于跟踪文件目录，不用于分支名：

- 从需求中提炼简短标识（如 `hotfix-login`、`docs-update`）
- 仅用于 `devflow/<feature>/` 目录名

`state.json`：

```json
"isolation": {
  "mode": "main-branch",
  "path": ".",
  "branch": "<target-branch>",
  "target_branch": "<target-branch>"
}
```

### 工作区状态提示（feat/main 模式专用）

因为 feat/main 模式直接修改主仓库工作区，初始化前检查：

```bash
git status --short
```

- **无未提交变更**：直接继续
- **存在未提交变更**：提示但不阻塞：
  > 检测到工作区存在未提交变更。若继续，这些变更将被纳入本次 DevFlow 会话的开发范围。是否继续？
  > - 回复 **继续**：开始本次会话
  > - 回复 **清理**：请先 stash / commit / 丢弃变更后再开始

---

## CWD 守卫与公共流程（Phase 2-5）

### 修改后的 CWD 守卫

读取 `state.json` 后按 `isolation.mode` 判断：

```bash
MODE=$(jq -r .isolation.mode devflow/<feature>/state.json)
EXPECTED=$(jq -r .isolation.path devflow/<feature>/state.json)
EXPECTED_BRANCH=$(jq -r .isolation.branch devflow/<feature>/state.json)

if [ "$MODE" = "worktree" ]; then
  # 必须位于 worktree 目录
  [ "$(pwd -P)" = "$(cd "$EXPECTED" && pwd -P)" ] && OK || WARN
elif [ "$MODE" = "feat-branch" ] || [ "$MODE" = "main-branch" ]; then
  # 必须位于主仓库根目录，且当前分支匹配 isolation.branch
  CURRENT_BRANCH=$(git branch --show-current)
  [ "$(pwd -P)" = "$(cd "$EXPECTED" && pwd -P)" ] && [ "$CURRENT_BRANCH" = "$EXPECTED_BRANCH" ] && OK || WARN
fi
```

### WARN 恢复行为

- **worktree 模式**：尝试 `EnterWorktree path="<isolation.path>"`；失败则提示手动 `cd`
- **feat 模式**：提示 `git checkout <feature>` + `cd <main-repo-root>`
- **main 模式**：提示 `git checkout <target-branch>` + `cd <main-repo-root>`

### Phase 2-5 公共行为

需求拆解、方案蓝图、编码实现、测试验证四个阶段保持 mode 无关：

- 文件都写入 `devflow/<feature>/`
- 代码修改写入当前分支（由 CWD 守卫保证分支正确）

---

## Phase 6：按模式收尾

### 公共入口

所有模式都先执行：

1. 用户确认"是否结束会话并提交"
2. `git status --porcelain` 检查未提交变更
3. 有变更则按现有 6.3 规则自动提交（或用户选择跳过）

### worktree 模式（保持 v3.0）

完整保留现有 Phase 6 流程：

1. 6.2 合并验证（target → feature）
2. 6.3 预完成提交
3. 6.4 在主仓库把 feature merge 到 target（`--no-ff`）
4. 6.5 删除 worktree + 删除 feature 分支

### feat 分支模式（新增）

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

# 4. 切回 target，把 feat 合并进去（生成 merge commit）
git checkout <target-branch>
git merge --no-ff <feature>

# 5. 推送
git push origin <target-branch>

# 6. 保留 feat 分支
```

**为什么用 `git fetch` + `git merge --ff-only` 而不是 `git pull`？**

`git pull` 的默认行为依赖本地 git 配置：若配置过 `pull.rebase=true`，会变成 `fetch` + `rebase`。DevFlow 严格禁止 rebase，因此必须显式控制：

```bash
git fetch origin
git merge --ff-only origin/<target-branch>
```

`--ff-only` 还能在本地 main 与远端分叉时**失败并停止**，而不是默默产生合并提交。这是 v3.0 Phase 6 防止覆盖远端提交的核心安全措施。

### main 分支模式（新增）

```bash
# 1. 切到 target，安全同步远端
git checkout <target-branch>
git fetch origin
git merge --ff-only origin/<target-branch>   # 失败则硬停止

# 2. 所有改动已在 target 上，直接 push
git push origin <target-branch>
```

注意：

- main 模式**不执行 catch-up merge**（因为已经在 target 上）
- 但仍需执行 `git merge --ff-only origin/<target-branch>` 安全检查
- 推送前同样要做 fast-forward 预检

### 清理

- **worktree 模式**：`ExitWorktree remove` + 删除 feature 分支
- **feat 模式**：无 worktree 清理，保留 feature 分支
- **main 模式**：无 worktree 清理，无分支删除

所有模式最后更新 `state.json`：`phase: "completed"`。

---

## 错误处理、向后兼容与边界情况

### 旧状态文件兼容

现有 v3.0 `state.json` 中没有 `isolation.mode` 字段。恢复旧会话时：

```bash
MODE=$(jq -r '.isolation.mode // "worktree"' devflow/<feature>/state.json)
```

- 缺失 `mode` 时默认为 `worktree`，保持与现有 v3.0 行为一致
- 旧 v2.4 会话的 `isolation.type == "fullcopy"` 仍按 v2.4 兼容逻辑处理

### 多会话冲突

- **worktree 模式**：多个 feature 可并行（多个 worktree）
- **feat 模式**：多个 feature 分支可并行，但每次 `/devflow` 只处理一个 feature
- **main 模式**：同一时刻只允许一个 main 模式会话（Step 0 检查主仓库是否存在未完成的 main 模式会话）

### main 模式风险提示

选择 main 模式时追加一次确认（见"模式选择 Prompt"）。

### 分支名冲突检查（按 mode）

- **worktree / feat 模式**：检查 `git branch --list <feature>` 和 `.claude/worktrees/devflow-<feature>` 是否已存在
- **main 模式**：检查主仓库是否已有未完成的 main 模式会话（通过 `devflow/*/state.json` 中 `isolation.mode == "main-branch"` 且 `phase != "completed"`）

### 模式间迁移（按需执行，非主流程）

当用户明确要求切换模式时，AI 可协助执行：

| 源模式 | 目标模式 | 操作步骤 |
|--------|----------|----------|
| main | feat | `git stash` 保存当前改动 → `git checkout -b <feature>` → `git stash pop` → 更新 `state.json` 的 `isolation.mode` / `branch` / `path` |
| feat | main | `git reset --soft HEAD~N`（N 为本次会话产生的 commit 数，回退到工作区）→ `git stash` → `git checkout <target-branch>` → `git stash pop` → 更新 `state.json` |
| main | worktree | `git stash` → `git checkout -b <feature>` → `git worktree add .claude/worktrees/devflow-<feature> <feature>` → `EnterWorktree` → `git stash pop` → 更新 `state.json` |
| worktree | main | 在 worktree 中 `git reset --soft HEAD~N`（N 为本次会话产生的 commit 数）→ `git stash` → 切回主仓库 `git checkout <target-branch>` → `git stash pop` → 更新 `state.json` |
| feat | worktree | 在 feat 分支上 `git worktree add .claude/worktrees/devflow-<feature> <feature>` → `EnterWorktree` → 把 `devflow/<feature>/` 跟踪文件复制到 worktree 中 → 更新 `state.json` |
| worktree | feat | 切回主仓库 `git checkout <feature>` → 把 worktree 中的 `devflow/<feature>/` 跟踪文件复制到主仓库 → 更新 `state.json` |

**注意：** 模式迁移不是 `/devflow` 主流程的一等公民功能，仅当用户明确提出需求时执行。迁移后必须重新做 CWD 守卫验证。

---

## 决策记录

| 决策 | 原因 |
|------|------|
| 模式选择放在 Phase 1.2 之后 | 需求澄清不应产生文件；模式决定后才知道如何初始化会话 |
| main 模式不需要 feature 分支名 | main 模式直接在 target 上开发，无分支 |
| feat 模式保留 feature 分支 | 用户明确要求，便于后续追溯或继续迭代 |
| feat/main 模式不强制清工 | 支持主仓库上多个小任务并行 |
| 用 `fetch` + `--ff-only` 替代 `pull` | 避免 `pull.rebase` 配置导致 rebase，并保持远端一致性安全检查 |
| worktree 仍作为默认推荐 | 隔离性最好，适合大改动 |

---

## 待实现影响

本设计主要影响 `skills/devflow/SKILL.md` 中的以下内容：

- Step 0：检测未完成会话时增加 main 模式冲突检查
- Phase 1.3：新增 feature 名称只在非 main 模式下确认
- Phase 1.4 前：新增模式选择 prompt
- Phase 1.4：拆分为 worktree / feat / main 三条初始化路径
- Phase 2-5 开头：CWD 守卫按 mode 路由
- Phase 6：拆分为 worktree / feat / main 三条收尾路径
- 状态文件：`isolation` 字段增加 `mode`
