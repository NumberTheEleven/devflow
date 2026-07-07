---
name: devflow
description: DevFlow v3.0 — AI 开发规范流程，单一入口，按阶段推进完整开发流程。基于 git worktree 会话隔离与强制合并验证，防止多 feature 并行开发时的冲突与语义回归。
argument-hint: [模糊需求描述]
---

# /devflow — DevFlow v3.0

## 流程总览

```
用户输入: /devflow 模糊需求
    ↓
Step 0: 入口检测 → git 拓扑 + 路径检测，判断是否在 worktree / 是否有活跃会话
    ↓
Phase 1: 需求澄清 (clarify) — 纯对话，不产生文件
    ↓ checkpoint（显式确认）
Phase 2: 需求拆解 (breakdown) → R-xxx 清单
    ↓ checkpoint（显式确认）
Phase 3: 方案蓝图 (blueprint) → 流程图 + 设计规格 + TC-xxx
    ↓ checkpoint（显式确认）
Phase 4: 编码实现 (implement) → T-xxx 任务 + 架构图 + 代码
    ↓ checkpoint（显式确认）
Phase 5: 测试验证 (verify) → L1烟雾 + L2交互 + L3手工，证据驱动
    ↓ checkpoint（人工验收）
Phase 6: 流程完成 → 合并验证 + 提交 + worktree 清理
```

**核心原则：**
- 唯一入口：`/devflow`，没有子命令
- clarify 阶段不产生任何文件写入
- clarify 确认后创建 git worktree 作为开发环境（v3.0 起），所有后续文件改动在该 worktree 内进行
- v2.4 遗留的全量副本目录（`GIT_DIR == GIT_COMMON` 但路径在 `.claude/worktrees/devflow-*` 下）仍可识别并恢复
- 每个 feature 的 DevFlow 文件隔离在 `devflow/<feature>/` 目录下，随 feature 分支提交
- **每个阶段结束时必须获得用户显式确认（"确认"/"Yes"/"Y"），才能进入下一阶段**
- **用户未明确确认时，一律视为需要修改；修正后必须重新展示完整结果并再次等待确认**
- checkpoint 只提供"确认"一个明确选项；不确认就是需要修改
- **任何阶段发现前置文档无法指导当前工作，必须主动提出回退到上游阶段重新确认**
- **流程节点回退是正常场景，在遇到阻塞时主动提出，不允许自行假设继续**
- 流程全部通过后：必须经用户人工验收，确认所有更改已提交，再标记完成
- **绝对禁止 `git push --force`。** 任何阶段的任何操作都不允许强制推送。目标分支提交只能通过正常 merge 流程

---

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

> 判定处于主仓库时，还需检查 0.4.1，防止多个 main 模式会话同时运行。

### 0.4 检测是否有活跃会话

检查主仓库根目录下是否存在未完成的旧版 `devflow/state.json`（仅在判定处于主仓库时执行）：

- **存在且 `phase` 不是 `"completed"`：** 说明有未完成的旧版 DevFlow 会话。
  - 输出："检测到主仓库存在未完成的旧版 DevFlow 会话（feature: `<feature>`，当前阶段：`<phase>`）。v3.0 起会话需要在开发环境副本中运行，请先完成或手动清理该会话后再开始新会话。"
  - 不创建新开发环境，等待用户处理

- **不存在或 `phase` 为 `"completed"`：**
  - 如果没有传入需求描述，询问用户要做什么
  - 如果传入了需求描述，进入 Phase 1（需求澄清）

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

### 0.5 管理命令说明

v2.4 起不再提供 `/devflow list` 和 `/devflow cleanup` 管理命令。`/devflow` 保持唯一入口。

- 如需查看会话，直接查看 `devflow/<feature>/` 目录或 `.claude/worktrees/` 目录
- 如需清理开发环境副本，使用 `git worktree remove .claude/worktrees/devflow-<feature>`（v3.0）或直接删除目录（v2.4 遗留）

---

## Phase 1: 需求澄清

```
Phase 1.1-1.2: 需求澄清
    ↓ checkpoint（显式确认）
Phase 1.35: 选择开发模式
    ↓
[Phase 1.3: 提炼 feature 名称]  （仅当 mode ≠ main-branch）
    ↓
Phase 1.4: 按模式初始化会话
```

**约束：** 不调用 Write/Edit，不产生任何文件改动

### 1.1 流程

遵循原 clarify skill 的核心逻辑：

1. **复述理解：** 用 1-2 句话复述用户的需求，确认理解是否正确
2. **逐步探索：** 一次问一个问题，逐步深入。探索维度：
   - 目的：解决什么问题？谁受益？
   - 约束：技术、时间、资源限制？
   - 成功标准：怎样算完成、算做得好？
   - 范围：做什么？明确不做什么？
   - 用户：最终用户是谁？使用场景？
3. **提出方案：** 需求足够清晰后，提出 2-3 个方案，推荐一个
4. **收敛确认：** 产出清晰的需求总结（目标、包含项、排除项、成功标准、约束）
5. **记录待澄清项：** 如果存在无法在 clarify 阶段说清的问题，明确记录为"待澄清项"，并在 Phase 2 中主动列出要求用户确认

### 1.2 Checkpoint

需求澄清完成后，展示 checkpoint：

> "需求澄清完成。当前需求总结如下：
> - 目标：...
> - 包含项：...
> - 排除项：...
> - 成功标准：...
> - 约束：...
> - 待澄清项（如有）：...
>
> 请确认以上内容是否准确、完整。回复 **"确认" / "Yes" / "Y"** 进入需求拆解；否则请指出需要修改的地方。"

- **用户回复 "确认" / "Yes" / "Y"：** 进入 Phase 1.35（选择开发模式）
- **其他任何回复（包括"需要修改"、指出问题、部分肯定、沉默等）：** 一律视为需要修改。针对用户反馈修正后，**重新输出完整的需求总结**，再次等待确认
- **不回复：** 自然暂停。下次 `/devflow` 时通过 Step 0 检测恢复。

### 1.35 选择开发模式

在需求澄清确认后、初始化会话前，展示模式选择：

> 需求已确认。请选择本次开发模式：
> 1. **worktree 分支分库开发**（推荐）：创建独立 worktree，完全隔离，适合改动大的 feature（当前 v3.0 默认）
> 2. **feat 分支开发**：在主仓库中创建 feat/* 分支直接开发，不创建 worktree，避免 worktree 环境/端口问题
> 3. **main 分支开发**：直接在 main/master 上开发，不创建分支和 worktree，适合极小改动或紧急修复
>
> 回复数字或名称选择。

- 用户选择 `worktree` 或 `feat-branch`：进入 Phase 1.3 提炼并确认 feature 名称
- 用户选择 `main-branch`：跳过 Phase 1.3，feature 名称由 AI 内部推导，仅用于 `devflow/<feature>/` 目录跟踪，不经过用户确认

选择 `main-branch` 时追加风险提示：

> 你选择了 main 分支开发模式。所有改动将直接提交到 `<target-branch>` 并推送到远端。该模式不适合需要代码审查或可能破坏主干的较大改动。是否确认继续？
>
> 回复 **确认 / Yes / Y** 继续；否则返回模式选择。

### 1.3 提炼 Feature 名称

**仅当用户选择 `feat-branch` 或 `worktree` 模式时执行。** 若用户选择 `main-branch` 模式，则跳过本阶段，feature 名称由 AI 内部推导，仅用于 `devflow/<feature>/` 目录跟踪。

从确认的需求中提炼一个简短的 feature 名称：

- 使用英文小写 + 连字符（如 `user-auth`、`payment-flow`、`fix-login-timeout`）
- 4 个词以内，描述性强
- 用于分支名（`feat/<feature>` 或 worktree 分支名）和 `devflow/<feature>/` 目录名

向用户确认："基于需求，feature 名称建议为 `xxx`，可以吗？"

- 用户确认后暂存 feature 名称，进入 Phase 1.4 初始化会话

### 1.4 初始化会话

Feature 名称确认且模式选择完成后，按所选模式初始化会话。三种模式共享前置步骤 1.4.1 和 1.4.2，之后进入各自的初始化路径。最终通过 `state.json` 中的 `isolation.mode` 记录所选模式。

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

#### 1.4.3 worktree 模式初始化

执行当前 v3.0 的初始化流程：

```bash
git checkout -b <feature>
git checkout <target-branch>
git worktree add .claude/worktrees/devflow-<feature> <feature>
EnterWorktree path=".claude/worktrees/devflow-<feature>"
```

然后按 1.4.7 补充运行时环境。

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

#### 1.4.7 补充运行时环境（策略菜单）

worktree 模式下不含 gitignored 的运行时文件，需按策略菜单补充。feat/main 模式下主仓库已有运行时环境，通常无需额外补充，但可按项目情况确认。

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

#### 1.4.8 初始化状态目录和文件

在当前 `isolation.path` 指定的工作目录内创建 `devflow/<feature>/` 目录，写入 `state.json`：

```json
{
  "feature": "<feature-name>",
  "phase": "breakdown",
  "created_at": "<ISO timestamp>",
  "version": "3.0",
  "requirements_confirmed": true,
  "open_questions": ["<待澄清项>"],
  "isolation": {
    "mode": "worktree",
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

新增 `isolation` 字段记录会话隔离元数据，便于后续 CWD 守卫和 Phase 6 清理时定位。

#### 1.4.9 提示用户

> "会话 `<feature>` 已准备就绪（模式：`<isolation.mode>`；路径：`<isolation.path>`；基于 `<target-branch>`）。已根据项目情况补充运行时环境（如适用）。可立即启动服务进行验收。后续所有文件操作将在当前工作目录内进行。"

### 1.5 进入下一阶段

会话初始化后，自动进入 Phase 2（需求拆解）。

---

## Phase 2: 需求拆解

**参考：** 原 breakdown skill 核心逻辑

#### CWD 守卫

进入本 Phase 前，确认当前 CWD 是否在 `devflow/<feature>/state.json` 中 `isolation.path` 指定的工作目录内，且当前分支符合 `isolation.branch`：
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
- 检测为 OK：正常继续
- **worktree 模式且检测到 WARN**：尝试 `EnterWorktree path="<isolation.path>"`；如不可用，提示用户确认并执行 `cd` 恢复
- **feat 模式且检测到 WARN**：提示用户执行 `git checkout <feature>` 并 `cd <main-repo-root>`
- **main 模式且检测到 WARN**：提示用户执行 `git checkout <target-branch>` 并 `cd <main-repo-root>`

### 2.1 流程

1. 将确认的需求拆解为离散的、可验证的子需求
2. 每个子需求编号 R-001, R-002, ...
3. 分配优先级（P0/P1/P2），标注依赖关系
4. 每个子需求附带可衡量的验收标准（checkbox 格式）
5. **处理待澄清项：**
   - 如果 `state.json` 中存在 `open_questions`，在展示 R-xxx 清单前主动列出：
     > "以下问题在需求澄清阶段尚未明确，请确认后我才能正确拆解需求："
   - 每条待澄清项必须得到用户明确答复，回答后重新生成完整的需求拆解清单
6. **识别新增不清晰项：** 拆解过程中，如果发现需求澄清中仍无法指导拆解的内容，主动提出并标记为新的待澄清项，要求用户确认
7. 展示完整清单，请用户确认
8. 确认后写入 `devflow/<feature>/requirements.md`（使用 `skills/breakdown/references/requirements-template.md` 格式）

### 2.2 用户反馈与修正

如果用户对 R-xxx 清单提出任何非确认性反馈：
1. 一律视为需要修改
2. 不要只回复"已修改"或只修改局部
3. **必须重新输出完整的需求拆解清单**（包含所有 R-xxx、优先级、依赖、验收标准）
4. 明确询问："以上是修正后的完整需求拆解，请确认是否有问题。回复 **确认 / Yes / Y** 进入方案蓝图；否则请指出需要修改的地方。"
5. 只有用户明确回复确认后，才能进入 Phase 3

### 2.3 Checkpoint

> "需求拆解完成。共 N 项需求（R-001 ~ R-xxx），已保存到 devflow/<feature>/requirements.md。
>
> 请确认以上需求拆解是否准确、完整。回复 **确认 / Yes / Y** 进入方案蓝图；否则请指出需要修改的地方。"

- **用户回复 "确认" / "Yes" / "Y"：** 进入 Phase 3
- **其他任何回复：** 视为需要修改。修正后重新输出完整清单，再次等待确认
- **不回复：** 自然暂停。更新 `devflow/<feature>/state.json` 的 `phase` 为 `"blueprint"`。

---

## Phase 3: 方案蓝图

**参考：** 原 blueprint skill 核心逻辑

#### CWD 守卫

进入本 Phase 前，确认当前 CWD 是否在 `devflow/<feature>/state.json` 中 `isolation.path` 指定的工作目录内，且当前分支符合 `isolation.branch`：
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
- 检测为 OK：正常继续
- **worktree 模式且检测到 WARN**：尝试 `EnterWorktree path="<isolation.path>"`；如不可用，提示用户确认并执行 `cd` 恢复
- **feat 模式且检测到 WARN**：提示用户执行 `git checkout <feature>` 并 `cd <main-repo-root>`
- **main 模式且检测到 WARN**：提示用户执行 `git checkout <target-branch>` 并 `cd <main-repo-root>`

### 3.1 流程

1. **业务流程图：** 用 Mermaid 绘制用户视角的流程，确认是否符合预期
2. **规格边界：** 明确范围内/范围外、技术标准、设计决策、风险缓解
3. **测试用例：** 为每个 R-xxx 编写 TC-xxx，含步骤和预期结果
4. **前置文档可指导性检查：**
   - 在编写设计规格和测试用例前，主动检查 `requirements.md` 是否足以指导设计
   - 如果发现存在 R-xxx 无法转化为具体设计或测试用例，**主动提出回退到 Phase 1 或 Phase 2 重新确认**
5. 写入 `devflow/<feature>/design.md` 和 `devflow/<feature>/test-cases.md`

### 3.2 用户反馈与修正

如果用户对方案蓝图提出任何非确认性反馈：
1. 一律视为需要修改
2. 不要只回复"已修改"或只修改局部
3. **必须重新输出完整的方案蓝图结果**（流程图 + 规格边界 + TC 清单）
4. 明确询问："以上是修正后的完整方案蓝图，请确认是否有问题。回复 **确认 / Yes / Y** 进入编码实现；否则请指出需要修改的地方。"
5. 只有用户明确回复确认后，才能进入 Phase 4

### 3.3 Checkpoint

> "方案蓝图完成。design.md + test-cases.md 已保存（TC-001 ~ TC-xxx）。
>
> 请确认以上方案蓝图是否准确、完整。回复 **确认 / Yes / Y** 进入编码实现；否则请指出需要修改的地方。"

---

## Phase 4: 编码实现

**参考：** 原 implement skill 核心逻辑

#### CWD 守卫

进入本 Phase 前，确认当前 CWD 是否在 `devflow/<feature>/state.json` 中 `isolation.path` 指定的工作目录内，且当前分支符合 `isolation.branch`：
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
- 检测为 OK：正常继续
- **worktree 模式且检测到 WARN**：尝试 `EnterWorktree path="<isolation.path>"`；如不可用，提示用户确认并执行 `cd` 恢复
- **feat 模式且检测到 WARN**：提示用户执行 `git checkout <feature>` 并 `cd <main-repo-root>`
- **main 模式且检测到 WARN**：提示用户执行 `git checkout <target-branch>` 并 `cd <main-repo-root>`

### 4.1 流程

1. **任务拆解：** 拆解为 T-001, T-002, ...，标注依赖、复杂度、涉及文件
2. **技术架构图：** Mermaid 格式（数据流/泳道/状态机/ER/时序图，选合适的）
3. **前置文档可指导性检查：**
   - 在编码前，主动检查 `requirements.md` 和 `design.md` 是否足以指导实现
   - 如果发现按照当前 R-xxx / design 无法达成需求，或存在技术不可行、边界冲突、依赖缺失等问题，**必须主动提出回退到 Phase 1/2/3 重新确认**，不允许自行假设并继续
4. **执行任务：**
   - 无依赖任务并行 dispatch sub-agent
   - 有依赖任务按序执行
   - 每个 sub-agent: TDD 循环 → code review → commit
5. **进度追踪：** 更新 `devflow/<feature>/tasks.md` 中各 T-xxx 的状态

### 4.2 实现中回退机制

在编码实现过程中，如果发现以下任一情况：
- 按照需求拆解的任务规范无法达成需求
- 设计规格与实际实现存在不可调和的冲突
- 需求边界不清晰导致实现无法收敛
- 技术约束导致原方案不可行
- 前置文档无法指导当前工作

**必须停止当前实现，主动提出：**
> "当前实现遇到阻塞：`<原因>`。按照需求拆解/方案蓝图无法继续推进。建议回退到 `<Phase 1/2/3>` 重新确认需求/拆解/设计。是否回退？"

只有用户确认回退后，才允许回退并重新进入上游阶段。回退后必须重新完成该阶段并再次获得用户确认，才能继续。

### 4.3 用户反馈与修正

如果用户对编码实现提出任何非确认性反馈（包括任务拆解、架构图、代码方向等）：
1. 一律视为需要修改
2. 不要只回复"已修改"或只修改局部
3. **必须重新输出完整的编码实现状态**（任务清单 + 架构图 + 当前进度）
4. 明确询问："以上是修正后的完整编码实现状态，请确认是否有问题。回复 **确认 / Yes / Y** 进入测试验证；否则请指出需要修改的地方。"
5. 只有用户明确回复确认后，才能进入 Phase 5

### 4.4 Checkpoint

> "编码实现完成。所有 T-xxx 任务已完成，tasks.md 已更新。
>
> 请确认以上编码实现是否完整、符合预期。回复 **确认 / Yes / Y** 进入测试验证；否则请指出需要修改的地方。"

---

## Phase 5: 测试验证

**参考：** 原 verify skill 核心逻辑，升级为三层验证架构

#### CWD 守卫

进入本 Phase 前，确认当前 CWD 是否在 `devflow/<feature>/state.json` 中 `isolation.path` 指定的工作目录内，且当前分支符合 `isolation.branch`：
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
- 检测为 OK：正常继续
- **worktree 模式且检测到 WARN**：尝试 `EnterWorktree path="<isolation.path>"`；如不可用，提示用户确认并执行 `cd` 恢复
- **feat 模式且检测到 WARN**：提示用户执行 `git checkout <feature>` 并 `cd <main-repo-root>`
- **main 模式且检测到 WARN**：提示用户执行 `git checkout <target-branch>` 并 `cd <main-repo-root>`

### 5.1 流程

1. 加载所有跟踪文件（requirements.md, design.md, tasks.md, test-cases.md）
2. **TC 智能路由：** 按关键字和类型将每条 TC 分发到 L1/L2/L3
3. **L1 烟雾扫描：** Playwright 自动扫描所有路由（console error / network health / runtime health / DOM snapshot），检查页面基础设施是否正常
4. **L2 交互验证：** 对交互类 TC 使用 Playwright 执行真实用户操作（点击、输入、提交），记录 Interaction Trace（操作前后 DOM diff），判断功能是否真的可用
5. **L3 结构化手工验证：** 对无法自动化的 TC（权限、动画、视觉等），逐条收集证据，无证据不标记通过
6. **深度评分：** 计算验证深度（真正执行过的 TC 占比）和证据覆盖率，暴露"走过场"验证
7. 发现问题时：
   - L1 失败 → 基础设施问题，建议重新执行对应 T-xxx
   - L2 失败 → 功能 bug，建议重新执行对应 T-xxx
   - L3 失败 / 设计问题 → 建议回退到 Phase 3
   - 需求问题 → 建议回退到 Phase 1/2
8. 生成统一验证报告（verification-log.md），包含三层结果 + 交互追踪 + 深度评分

### 5.2 验证结果

**全部通过（深度 = 100%）：**

> "自动化验证已全部通过（深度 100%，证据覆盖率 100%）。
>
> 验证报告已保存到 devflow/<feature>/verification-log.md。
>
> 请在实际环境中进行人工验收。确认验收通过后，才能进行归档和提交。
> 回复 **确认 / Yes / Y** 表示人工验收通过，进入流程完成；否则请指出问题。"

**不自动进入 Phase 6。** 必须等待用户明确回复确认后，才允许进入 Phase 6。

**深度不足或有失败项：**

> "验证未通过 / 验证深度不足。具体情况如下：...
>
> 请确认处理方式：
> [修复后重新验证] 返回对应阶段修复
> [回退到 blueprint/breakdown/clarify] 重新确认
> [保留会话稍后继续]"

### 5.3 人工验收 Checkpoint

验证通过后，必须增加独立的"人工验收" checkpoint：

> "所有自动化验证已执行完毕。请进行人工验收：
> 1. 打开验证报告 devflow/<feature>/verification-log.md
> 2. 检查 L1/L2/L3 结果和证据
> 3. 在实际环境中试用关键功能
> 4. 确认无误后回复 **确认 / Yes / Y**
>
> 只有收到明确确认后，才会进入归档和提交。"

只有用户明确回复确认后，才允许进入 Phase 6。

---

## Phase 6: 流程完成

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

### 6.1 确认

> "DevFlow 流程已通过人工验收。是否结束会话并提交？回复 **确认 / Yes / Y** 完成并提交；否则请说明。"

### 6.2 合并验证

确认完成后，**必须先执行**合并验证：

#### 6.2.1 识别目标分支

自动识别目标分支（`master` 或 `main`），规则同 Phase 1.4。

#### 6.2.2 拉取远端并验证本地状态

⚠️ **合并验证的核心安全步骤。**
```bash
# 在所有涉及的工作目录（主仓库和 worktree）均拉取最新远端状态
git fetch origin
```

验证本地目标分支与远端一致：
```bash
# Unix
LOCAL=$(git rev-parse <target-branch>)
REMOTE=$(git rev-parse origin/<target-branch>)
[ "$LOCAL" = "$REMOTE" ] && echo "OK: 本地与远端一致" || echo "WARN: 本地 <target-branch> 落后于远端"

# Windows PowerShell
$local = git rev-parse <target-branch>
$remote = git rev-parse origin/<target-branch>
if ($local -eq $remote) { Write-Host "OK: 本地与远端一致" } else { Write-Host "WARN: 本地 <target-branch> 落后于远端" }
```

- **OK：** 继续 6.2.3
- **WARN：** 执行 `git merge --ff-only origin/<target-branch>` 将本地目标分支同步到远端最新
  - `--ff-only` 成功 → 继续 6.2.3
  - `--ff-only`失败（分叉）→ **立即停止**，提示：
    > "⚠️ 本地 <target-branch> 与远端分叉，存在本地独有的提交。不允许继续，请手动处理后再运行 /devflow。"

#### 6.2.3 计算基准 commit

```bash
git merge-base <target-branch> <feature-branch>
```

#### 6.2.4 检查目标分支新变更

列出目标分支自基准 commit 以来的所有 merge commit：

```bash
git log --merges --first-parent <base-commit>..<target-branch>
```

- **无新 merge commit：** 跳过 6.2.5 ~ 6.2.7，直接进入 6.3 预完成提交。
- **有新 merge commit：** 进入 6.2.5 涉及 feat 验证。

#### 6.2.5 涉及 feat 验证

对每个 merge commit，从 commit message 中识别合并的 feature 分支名（例如 `Merge branch 'user-auth' into main` → `user-auth`）。

对每个识别出的涉及 feat：
1. 检查目标分支上是否存在 `devflow/<involved-feature>/test-cases.md`
2. 如果存在，重跑其测试用例和验收规格
3. 如果不存在，给出明确提示："涉及 feat `<involved-feature>` 没有 DevFlow 跟踪文件，请人工确认是否需要验证。"

**注意：** 即使没有 git 代码冲突，只要时间窗口存在重叠，就需要验证涉及 feat 的测试用例，以捕获语义冲突。

如果涉及 feat 验证未通过：
> "涉及 feat 验证未通过。请确认：
> [修复涉及 feat] 需要上游 feature 修复后重新合并到目标分支
> [调整当前 feature 以兼容] 在当前 feature 中适配上游变更
> [人工确认可接受] 明确记录风险后继续"

#### 6.2.6 执行 catch-up merge（目标分支 → feature）

在 **worktree** 内执行。将目标分支的最新内容合并到 feature 分支，目的是让 feature 分支追上目标分支的进度，在 6.2.7 中重新验证兼容性。

⚠️ **merge 方向是 `<target-branch>` 合并 INTO `<feature>`，不是反过来。** 当前在 feature 分支上：

```bash
git checkout <feature>                     # 确认在 feature 分支
git merge <target-branch>                  # 将 target 合并到 feature
```

**只允许 merge，不允许 rebase。**

- **无冲突：** 继续 6.2.7
- **有冲突：**
  > "检测到合并冲突，请人工解决以下文件后再继续：
  > - `<conflict-file-1>`
  > - `<conflict-file-2>`
  > 
  > 不允许自动覆盖合并。解决后回复 **确认 / Yes / Y** 继续。"
  
  用户确认解决后，继续 6.2.7。

#### 6.2.7 当前 feature 重验证

merge 完成后，重新跑当前 feature 的测试用例和验收规格（`devflow/<feature>/test-cases.md`）。

- 全部通过 → 进入 6.3 预完成提交
- 未通过 → 停止，提示用户修复

### 6.3 预完成提交（兜底保护）

**目的：** 防止存在未提交文件（如下载的数据、临时配置等），会话结束后丢失。

**注意：** 只有在 Phase 5 通过人工验收且合并验证通过后，才执行提交。

确认完成后，**必须先执行**以下步骤：

1. **检测未提交变更：**
   ```bash
   git status --porcelain
   ```
   同时检查文件大小，标记超大文件：
   ```bash
   git ls-files --others --exclude-standard | while read f; do
     size=$(stat -c%s "$f" 2>/dev/null || echo 0)
     [ "$size" -gt 10485760 ] && echo "LARGE: $f ($(( size / 1048576 ))MB)"
   done
   ```

2. **根据检测结果处理：**

   **情况 A — 无任何未提交变更：** 直接进入 6.4 标记完成。

   **情况 B — 仅有已追踪文件的修改（无 untracked）：**
   - 列出变更文件
   - `git add -u && git commit -m "chore: auto-commit pending changes before DevFlow completion"`

   **情况 C — 存在未追踪文件（untracked）：**
   - 列出所有未追踪文件及其大小
   - 如果存在 **超过 10MB 的大文件**，单独列出并警告用户：
     > "⚠️ 检测到超大未追踪文件（>10MB），直接提交可能污染 git 历史。建议："
     > "  1. 移动到外部存储（如对象存储），在代码中保留下载脚本"
     > "  2. 使用 Git LFS 管理"
     > "  3. 如果确定要提交，回复'全部提交'"
   - 如果用户选择"全部提交"，或没有超大文件：
     `git add -A && git commit -m "chore: auto-commit all contents before DevFlow completion"`
   - 如果用户选择跳过某些文件，协助添加到 `.gitignore` 后再提交

   **情况 D — 用户拒绝提交：**
   - 不强制。输出警告："⚠️ 未提交文件将在会话结束后丢失，已确认跳过。"
   - 更新状态文件记录此决策。

3. **提交后二次确认：**
   ```bash
   git status --porcelain
   ```
   必须干净才能标记完成。如果不干净（用户跳过了某些文件），再次提醒并确认。

### 6.4 合并到目标分支（严格安全流程）

将 feature 分支合并到目标分支。这是整个流程中唯一一次变更目标分支的操作，**必须严格遵守以下步骤，每一步都有验证，禁止跳步。**

⚠️ **所有以下操作在主仓库根目录执行，不在 worktree 中。** 执行前确认 CWD 不在 `.claude/worktrees/devflow-*` 路径下。

#### 6.4.1 拉取远端并验证状态

```bash
# 拉取远端最新状态（只拉取，不合并）
git fetch origin
```

验证本地目标分支与远端一致：
```bash
# Unix
LOCAL=$(git rev-parse <target-branch>)
REMOTE=$(git rev-parse origin/<target-branch>)
[ "$LOCAL" = "$REMOTE" ] && echo "OK: 本地与远端一致" || echo "WARN: 本地落后于远端"

# Windows PowerShell
$local = git rev-parse <target-branch>
$remote = git rev-parse origin/<target-branch>
if ($local -eq $remote) { Write-Host "OK: 本地与远端一致" } else { Write-Host "WARN: 本地落后于远端" }
```

- **OK：** 继续 6.4.2
- **WARN：** 执行 `git merge --ff-only origin/<target-branch>`
  - `--ff-only` 成功 → 继续 6.4.2
  - `--ff-only` 失败（分叉）→ **硬停止。** 输出：
    > "⛔ 本地 <target-branch> 与远端分叉。存在本地独有的提交，或本地历史与远端不一致。
    > 继续合并将导致覆盖远端提交。请手动处理后再运行 /devflow。
    > 建议：检查 `git log --oneline --graph <target-branch> origin/<target-branch>`，确认分叉原因。"

#### 6.4.2 确认 feature 分支可访问

```bash
# 确认 feature branch 存在且与 worktree 中的一致
git log --oneline -1 <feature-branch>
```

读取 `devflow/<feature>/state.json` 确认 `isolation.branch` 与 `<feature-branch>` 一致。

#### 6.4.3 切换到目标分支

```bash
git checkout <target-branch>
```

验证切换成功：
```bash
git branch --show-current
```
输出必须是 `<target-branch>`。不是则停止。

#### 6.4.4 合并 feature 分支（--no-ff 强制生成 merge commit）

```bash
git merge --no-ff <feature-branch>
```

**只允许 `--no-ff`，不允许 fast-forward、squash、rebase。**

- **合并成功：** 继续 6.4.5
- **有冲突（git 返回非零退出码）：**
  > "⛔ 合并到目标分支时检测到冲突。这可能是因为 6.2.6 中已合并的目标分支内容与当前目标分支不一致（远端有新提交），或 feature 分支存在未预期的变更。
  > 
  > 请检查并手动解决以下冲突文件：
  > - `<conflict-file-1>`
  > - `<conflict-file-2>`
  > 
  > 解决后回复 **确认 / Yes / Y** 继续，我将验证合并结果。"

#### 6.4.5 合并结果验证

```bash
# 确认 HEAD 是 merge commit（有两个 parent）
git log --oneline -1 --merges

# 确认 merge commit 的 parent 包含目标分支和 feature 分支
git log --oneline -3 --graph

# 确认当前分支仍是目标分支
git branch --show-current
```

验证 checklist：
- HEAD 是一个 merge commit（有两个 parent）
- 第一个 parent 是合并前的 `<target-branch>` HEAD
- 第二个 parent 是 `<feature-branch>` 的最新 commit
- 当前分支是 `<target-branch>`

如果任一项不满足 → 停止，检查输出。

#### 6.4.6 推送前预检

在推送前最后一次确认不会覆盖远端：

```bash
# 目标分支的本地 HEAD 必须是 origin/<target-branch> 的直接后代
git merge-base --is-ancestor origin/<target-branch> HEAD && echo "OK: 推送安全（本地是远端的 fast-forward）" || echo "REJECT: 推送到远端将被拒绝或覆盖"
```

- **OK：** 继续 6.4.7
- **REJECT：** **硬停止。** 输出：
  > "⛔ 检测到当前本地 <target-branch> 不是远端的 fast-forward 后代。推送将被拒绝或覆盖远端。
  > 请检查 `git log --oneline --graph origin/<target-branch> HEAD`，确认原因后手动处理。"

#### 6.4.7 推送到远端

```bash
git push origin <target-branch>
```

⚠️ **绝对禁止 `git push --force`、`git push --force-with-lease`、或任何形式的强制推送。**

- **推送成功：** 继续 6.4.8
- **推送被拒绝：** **硬停止。** 输出：
  > "⛔ 推送到远端被拒绝。远端在 6.4.6 之后有新的提交，或存在其他冲突。
  > 请从 6.4.1 重新执行（重新 fetch 并验证）。"

#### 6.4.8 推送后远端验证

```bash
# 确认远端目标分支 HEAD 与本地一致
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/<target-branch>)
[ "$LOCAL" = "$REMOTE" ] && echo "✅ 推送成功，远端已更新" || echo "REJECT: 远端与本地不一致"
```

- **OK：** 进入 6.5 清理
- **不一致：** 输出：
  > "⚠️ 推送后远端与本地不一致，可能是推送未完成或远端 hook 修改了提交。请检查 `git log origin/<target-branch>`。"

### 6.5 自动清理开发环境副本（worktree）

提交成功后，自动删除 worktree。读取 `devflow/<feature>/state.json` 中 `isolation.path` 和 `isolation.branch`。

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

### 6.6 标记完成

更新 `devflow/<feature>/state.json`：

```json
{
  "phase": "completed",
  "completed_at": "<ISO timestamp>"
}
```

输出："DevFlow v3.0 流程完成。跟踪文件保存在 devflow/<feature>/ 目录。"

### 6.7 保留会话

如果用户选择保留会话，状态文件标记 `phase: "completed"`，worktree 可以保留或手动清理。

---

## Checkpoint 机制总结

每个阶段结束时统一格式：

> "✅ [阶段名] 完成。
>
> 请确认以上结果是否准确、完整。回复 **确认 / Yes / Y** 进入下一阶段；否则请指出需要修改的地方。"

| 用户输入 | 行为 |
|---------|------|
| 确认 / Yes / Y / y / 是的 | 进入下一阶段 |
| 其他任何回复（包括"需要修改"、指出问题、部分肯定、沉默、跳转请求等） | **一律视为需要修改**。修正后重新输出完整结果，再次等待确认 |
| 不回复 | 自然暂停，更新状态文件 |

**checkpoint 只提供"确认"一个明确选项。** 用户不确认就是需要修改。回退、跳转等需求通过用户在"需要修改"反馈中提出，或者由 AI 在发现阻塞时主动提出。

---

## 阶段间确认规则

| 从 → 到 | 必须满足的条件 |
|---------|---------------|
| clarify → breakdown | 用户明确回复"确认"/"Yes"/"Y"；feature 名称确认；worktree 创建成功 |
| breakdown → blueprint | 用户明确回复"确认"/"Yes"/"Y"；完整 R-xxx 清单已确认；所有待澄清项已解决 |
| blueprint → implement | 用户明确回复"确认"/"Yes"/"Y"；完整设计方案 + TC 清单已确认 |
| implement → verify | 用户明确回复"确认"/"Yes"/"Y"；完整 T-xxx 已完成 |
| verify → completed | 自动化验证通过 + 用户明确回复"确认"/"Yes"/"Y"完成人工验收 + 合并验证通过 |

---

## 状态持久化格式

`devflow/<feature>/state.json`：

```json
{
  "feature": "user-auth",
  "phase": "implement",
  "created_at": "2026-06-24T14:30:00+08:00",
  "version": "3.0",
  "isolation": {
    "mode": "worktree",
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

- `phase` 记录当前所处阶段
- `checkpoints` 记录每个阶段的完成状态
- `open_questions` 记录未澄清问题，进入下一阶段前必须清空或得到用户确认
- `rollback_history` 记录回退历史，便于追踪
- `isolation` 记录 worktree 元数据（v3.0 新增），Phase 6.5 清理时读取
- 恢复时读取 `phase`，跳转到对应阶段入口

> `mode` 是路由 key，决定初始化、CWD 守卫和 Phase 6 收尾行为。旧 state.json 无 `mode` 字段时默认视为 `worktree`。

---

## 错误处理

| 场景 | 处理 |
|------|------|
| 阶段执行报错 | 显示错误详情，不跳过阶段，询问是否重试 |
| 状态文件损坏 | 提示用户，从 clarify 重新开始或手动指定阶段 |
| git 仓库不干净 | 提示用户先清理工作区再开始 |
| 前置文档无法指导当前工作 | 主动提出回退到上游阶段重新确认 |
| 实现中发现需求不可行 | 主动提出回退到 clarify/breakdown 重新确认 |
| 用户未明确确认 | **不推进到下一阶段**，保持当前阶段等待确认或修改 |
| 目标分支无 master/main | 报错并停止，提示用户创建目标分支 |
| feature branch 或开发环境副本已存在 | 报错并提示用户更换 feature 名称 |
| 合并验证发现冲突 | 停止流程，提示人工解决，不允许自动覆盖 |
| 本地与远端分叉（--ff-only 失败） | **硬停止**，提示用户手动检查 `git log --oneline --graph` 确认分叉原因 |
| 推送前安全预检失败 | **硬停止**，本地不是远端的 fast-forward 后代，禁止推送 |
| git push 被远端拒绝 | **硬停止**，从 6.4.1 重新执行 |
| 远端验证不一致 | 提示用户检查 `git log origin/<target-branch>` |
| git push --force | **绝对禁止。** 任何情况下不允许使用 |
| worktree 清理失败 | 给出明确提示，由用户手动处理 |

---

## 参考

- 各阶段内部模板位于 `skills/*/references/` 目录
- 原 6 个 skill 文件保留在 `skills/` 目录中供高级用户参考，但不再作为独立命令暴露
- Git 文档：`git help`

---

*DevFlow v3.0 — 单一入口，git worktree 隔离，策略菜单补充运行时，合并验证，闭环管理。*
