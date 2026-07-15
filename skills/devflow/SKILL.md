---
name: devflow
description: DevFlow v3.6 — AI 开发规范流程，单一入口，按阶段推进完整开发流程。支持 git worktree / feat 分支 / main 分支三种开发模式，main 分支多会话协调式并行（Phase 1-4 独立并行 + Phase 5-6 全局串行排队 + git/verify/push lock）。
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
    ↓ checkpoint（显式确认 / 可切换自循环）
Phase 2: 需求拆解 (breakdown) → R-xxx 清单
    ↓ checkpoint（显式确认 / 可切换自循环）
Phase 3: 方案蓝图 (blueprint) → 流程图 + 设计规格 + TC-xxx
    ↓ checkpoint（显式确认 / 可切换自循环）
Phase 4: 编码实现 (implement) → T-xxx 任务 + 架构图 + 代码
    ↓ checkpoint（显式确认 / 可切换自循环）
Phase 5: 测试验证 (verify) → L1烟雾 + L2交互 + L3手工，证据驱动
    ↓ checkpoint（人工验收 / 自循环下自动修复）
Phase 6: 流程完成 → 合并验证 + 提交 + 按模式清理
```

**自循环模式（Autonomous / Auto）：**
- 用户在任意 checkpoint 可输入 `auto` / `autonomous` / `自循环`，将后续阶段交给 AI 自主推进
- AI 接管后，按阶段自评 checklist 自行确认并推进
- implement ↔ verify 之间形成自修复小循环；根因在上游时自动回退
- 达到超时或最大迭代时熔断暂停，向用户报告
- 最终必须完成 Phase 6 的 commit + push 才退出

**核心原则：**
- 唯一入口：`/devflow`，没有子命令
- clarify 阶段不产生任何文件写入
- clarify 确认且模式选择完成后，按所选模式初始化开发环境（worktree / feat 分支 / main 分支），所有后续文件改动在该开发环境中进行
- v2.4 遗留的全量副本目录（`GIT_DIR == GIT_COMMON` 但路径在 `.claude/worktrees/devflow-*` 下）仍可识别并恢复
- 每个 feature 的 DevFlow 文件隔离在 `devflow/<feature>/` 目录下，随 feature 分支提交
- **每个阶段结束时必须获得用户显式确认（"确认"/"Yes"/"Y"），才能进入下一阶段**
- **用户未明确确认时，一律视为需要修改；修正后必须重新展示完整结果并再次等待确认**
- checkpoint 只提供"确认"一个明确选项；不确认就是需要修改
- **任何阶段发现前置文档无法指导当前工作，必须主动提出回退到上游阶段重新确认**
- **流程节点回退是正常场景，在遇到阻塞时主动提出，不允许自行假设继续**
- 流程全部通过后：必须经用户人工验收，确认所有更改已提交，再标记完成
- **绝对禁止 `git push --force`。** 任何阶段的任何操作都不允许强制推送。目标分支提交只能通过正常 merge 流程
- **自循环模式：** 用户在 checkpoint 输入 `auto` / `autonomous` / `自循环` 后，AI 按自评 checklist 自动推进；常规推进不打扰用户，只在阻塞/完成/熔断时报告

### 编号规范

DevFlow 文档采用统一的纯十进制编号体系：

- **阶段**：`Phase X`（如 Phase 1、Phase 2）
- **步骤**：`X.Y`（如 1.1、1.2）
- **子步骤**：`X.Y.Z`（如 1.5.1、1.5.2）

禁止以下编号形式：

- 字母后缀：`1.3a`、`1.4b`
- 两位小数：`1.35`、`1.45`

---

## Step 0: 入口检测

收到 `/devflow` 请求后，首先判断当前环境。v3.0 起，会话隔离支持三种模式：git worktree 分库开发、feat 分支开发、main 分支开发，检测需同时识别 v3.0 worktree 会话、feat/main 主仓库会话和 v2.4 全量副本遗留会话。

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
| `false` | `false` | 在主仓库（非开发环境） | 继续 0.4 检查活跃会话（包括 feat/main 模式会话） |
| `false` | `true` | 在 v2.4 全量副本中 | 读取 `devflow/<feature>/state.json` 恢复会话（视为 v2.4 会话） |
| `true` | (任意) | 在 v3.0 git worktree 中 | 读取 `devflow/<feature>/state.json` 恢复会话 |

注意：`IN_WORKTREE=true` 时 `IN_V24_COPY` 一定为 `false`（v3.0 worktree 目录名虽然形如 `.claude/worktrees/devflow-*`，但路径前缀检测仅作为兜底，主判定以 git 拓扑为准）。

> 判定处于主仓库时，还需检查 0.4.1，提示已有 main 模式会话的并发风险。

### 0.4 检测是否有活跃会话

先在主仓库根目录下扫描 `devflow/*/` 中未完成的 feat/main 模式会话（仅在判定处于主仓库时执行）。扫描时同时识别是否启用了自循环模式：

```bash
# 伪代码
for dir in devflow/*/; do
  state_file="$dir/state.json"
  [ -f "$state_file" ] || continue
  mode=$(jq -r '.isolation.mode // "worktree"' "$state_file" 2>/dev/null)
  phase=$(jq -r '.phase' "$state_file" 2>/dev/null)
  autonomous=$(jq -r '.autonomous.enabled // false' "$state_file" 2>/dev/null)
  feature=$(basename "$dir")
  if [ "$phase" != "completed" ] && [ "$mode" = "feat-branch" -o "$mode" = "main-branch" ]; then
    if [ "$autonomous" = "true" ]; then
      echo "检测到未完成的自循环会话（feature: $feature，当前阶段：$phase）。是否恢复该会话？"
    else
      echo "检测到未完成的 $mode 会话（feature: $feature，当前阶段：$phase）。是否恢复该会话？"
    fi
    # 恢复会话：读取 state.json，跳转到对应 phase
  fi
done
```

- **发现一个未完成的 feat/main 模式会话：** 询问用户是否恢复该会话
  - 若 `autonomous.enabled == true`，优先提示"自循环会话"，恢复后按自循环规则继续推进
  - 用户确认恢复：读取 `devflow/<feature>/state.json`，跳转到 `phase` 对应阶段入口
  - 用户拒绝恢复：继续检查旧版 `devflow/state.json`（若为 main 模式会话，后续 0.4.1 会给出并发风险提示）

- **发现多个未完成的 feat/main 模式会话：** 列出所有未完成会话，询问用户恢复哪一个
  - 用户选择其中一个：读取对应 `state.json` 并跳转
  - 用户拒绝恢复：继续检查旧版 `devflow/state.json`（若存在 main 模式会话，后续 0.4.1 会给出并发风险提示）

- **未发现未完成的 feat/main 模式会话：** 继续检查旧版 `devflow/state.json`（见下方）。

再检查主仓库根目录下是否存在未完成的旧版 `devflow/state.json`：

- **存在且 `phase` 不是 `"completed"`：** 说明有未完成的旧版 DevFlow 会话。
  - 输出："检测到主仓库存在未完成的旧版 DevFlow 会话（feature: `<feature>`，当前阶段：`<phase>`）。v3.0 起会话需要在开发环境副本中运行，请先完成或手动清理该会话后再开始新会话。"
  - 不创建新开发环境，等待用户处理

- **不存在或 `phase` 为 `"completed"`：**
  - 如果没有传入需求描述，询问用户要做什么
  - 如果传入了需求描述，进入 Phase 1（需求澄清）

### 0.4.1 检查是否已有未完成的 main 模式会话（并发风险提示）

仅在判定处于主仓库时执行。遍历 `devflow/*/` 下所有 `state.json`，检查是否存在未完成的 main 模式会话：

```bash
# 伪代码
count=0
for dir in devflow/*/; do
  state_file="$dir/state.json"
  [ -f "$state_file" ] || continue
  mode=$(jq -r '.isolation.mode // "worktree"' "$state_file" 2>/dev/null)
  phase=$(jq -r '.phase' "$state_file" 2>/dev/null)
  if [ "$mode" = "main-branch" ] && [ "$phase" != "completed" ]; then
    feature=$(basename "$dir")
    echo "  - $feature（阶段：$phase）"
    count=$((count + 1))
  fi
done
```

- **不存在未完成的 main 模式会话：** 跳过，继续原有 0.4 逻辑
- **存在未完成的 main 模式会话：** 输出风险提示，但不阻塞：

> ⚠️ 检测到以下未完成的 main 分支会话：
> - `<feature-1>`（阶段：`<phase>`）
> - `<feature-2>`（阶段：`<phase>`）
>
> main 分支模式的所有会话共享同一个分支和工作目录，同时进行多个 main 模式会话存在以下风险：
> - **工作区冲突**：多个会话可能同时修改相同文件，导致未提交变更相互覆盖
> - **推送冲突**：一个会话完成并推送后，其他会话的 Phase 6 合并验证可能失败，需要重新同步
> - **状态不一致**：`devflow/<feature>/` 跟踪文件与实际代码状态可能脱节
>
> 建议优先恢复已有会话，或使用 feat-branch / worktree 模式以获得更好的隔离性。
>
> 是否仍要开始新的 main 模式会话？回复 **确认 / Yes / Y** 继续；回复 **No** 返回模式选择或恢复已有会话。

- 用户确认继续 → 进入 Phase 1
- 用户拒绝 → 返回询问是否恢复已有会话或选择其他模式

### 0.5 main 分支并行会话协调（v3.5 新增）

#### 0.5.1 global-registry 管理

`devflow/.global-registry.json` 是并行 main 会话的本地协调文件（已加入 .gitignore，不提交到 git）。

```json
{
  "version": 1,
  "target_branch": "master",
  "sessions": {
    "<feature-name>": {
      "phase": "implement",
      "files": ["src/auth.ts"],
      "port": 3001,
      "registered_at": "2026-07-16T10:00:00+08:00",
      "last_heartbeat": "2026-07-16T10:30:00+08:00"
    }
  }
}
```

**操作时机：**

| 时机 | 操作 |
|------|------|
| Phase 3 确认后（main 模式） | 注册本会话：files + port + heartbeat |
| Phase 4 每次 commit | 更新 heartbeat（`last_heartbeat` → 当前时间） |
| Phase 5 verify | 更新 heartbeat |
| Phase 6 完成后 | 移除本会话条目 |
| Step 0 恢复会话 | 更新 heartbeat |

**格式说明：**
- `files`：本会话声明修改的文件列表（从 design.md 提取）
- `port`：Phase 5 dev server 端口（从 3001 递增分配）
- `heartbeat`：ISO 时间戳，用于僵死检测

#### 0.5.2 僵死会话检测

Step 0 扫描活跃 main 会话时，同时检查 global-registry 中的 heartbeat：
- 如果某会话的 `last_heartbeat` 距今超过 2 小时 → 提示：
  > "⚠️ 检测到 `<feature>` 会话可能已僵死（最后更新：`<time>`）。是否从 registry 清理？清理后将释放端口 `<port>`。"
- 用户确认后，从 registry 移除该条目

#### 0.5.3 管理命令说明

v2.4 起不再提供 `/devflow list` 和 `/devflow cleanup` 管理命令。`/devflow` 保持唯一入口。

- 如需查看会话，直接查看 `devflow/<feature>/` 目录或 `.claude/worktrees/` 目录
- 如需查看并行会话协调状态，查看 `devflow/.global-registry.json`
- 如需清理开发环境副本，使用 `git worktree remove .claude/worktrees/devflow-<feature>`（v3.0）或直接删除目录（v2.4 遗留）

---

## Phase 1: 需求澄清

```
Phase 1.1-1.2: 需求澄清
    ↓ checkpoint（显式确认）
Phase 1.3: 选择开发模式
    ↓
[Phase 1.4: 提炼 feature 名称]  （仅当 mode ≠ main-branch）
    ↓
Phase 1.5: 按模式初始化会话
```

**约束：** 不调用 Write/Edit，不产生任何文件改动

### 1.1 流程

遵循原 clarify skill 的核心逻辑，并补充以下约束：

1. **复述理解：** 用 1-2 句话复述用户的需求，确认理解是否正确
2. **逐步探索：** 一次问一个问题，逐步深入。探索维度：
   - 目的：解决什么问题？谁受益？
   - 约束：技术、时间、资源限制？
   - 成功标准：怎样算完成、算做得好？
   - 范围：做什么？明确不做什么？
   - 用户：最终用户是谁？使用场景？
   - **现有代码与系统现状：** 通过代码搜索（`Glob`/`Grep`/`Read`/`Bash`）或 Playwright 截图自行查证。**严禁向用户提问现状类问题。**
3. **提出方案：** 需求足够清晰后，提出 2-3 个方案，推荐一个
4. **收敛确认：** 产出清晰的需求总结（目标、包含项、排除项、成功标准、约束、已查证现状）
5. **记录待澄清项：** 如果存在无法在 clarify 阶段说清的问题，明确记录为"待澄清项"，并在 Phase 2 中主动列出要求用户确认

**现状查证截图路径：**
- 如需在 clarify 阶段截取页面现状，统一保存到 `devflow/<feature>/screenshots/clarify/`
- 文件名格式：`clarify-<page-name>-<YYYY-MM-DD>-<HHMMSS>.png`
- 例如：`devflow/<feature>/screenshots/clarify/login-page-2026-07-09-123045.png`
- 该目录属于生成的验证证据，应加入 `.gitignore`，不提交到 git

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
> 请确认以上内容是否准确、完整。回复 **"确认" / "Yes" / "Y"** 进入需求拆解；回复 **`auto` / `autonomous` / `自循环`** 进入需求拆解并由 AI 自动推进后续阶段；否则请指出需要修改的地方。"

- **用户回复 "确认" / "Yes" / "Y"：** 进入 Phase 1.3（选择开发模式）
- **用户回复 `auto` / `autonomous` / `自循环`：** 进入 Phase 1.3，并在会话初始化后切换为自循环模式
- **其他任何回复（包括"需要修改"、指出问题、部分肯定、沉默等）：** 一律视为需要修改。针对用户反馈修正后，**重新输出完整的需求总结**，再次等待确认
- **不回复：** 自然暂停。下次 `/devflow` 时通过 Step 0 检测恢复。

### 1.3 选择开发模式

在需求澄清确认后、初始化会话前，展示模式选择：

> 需求已确认。请选择本次开发模式：
> 1. **worktree 分支分库开发**（推荐）：创建独立 worktree，完全隔离，适合改动大的 feature（当前 v3.0 默认）
> 2. **feat 分支开发**：在主仓库中创建 feature 分支直接开发，不创建 worktree，避免 worktree 环境/端口问题
> 3. **main 分支开发**：直接在 main/master 上开发，不创建分支和 worktree，适合极小改动或紧急修复
>
> 回复数字或名称选择。

- 用户选择 `worktree` 或 `feat-branch`：进入 Phase 1.4 提炼并确认 feature 名称
- 用户选择 `main-branch`：跳过 Phase 1.4，feature 名称由 AI 内部推导，仅用于 `devflow/<feature>/` 目录跟踪，不经过用户确认

选择 `main-branch` 时追加风险提示：

> 你选择了 main 分支开发模式。所有改动将直接提交到 `<target-branch>` 并推送到远端。该模式不适合需要代码审查或可能破坏主干的较大改动。
>
> 若当前存在其他未完成的 main 模式会话，请注意并发风险（共享分支和工作目录，详见 Step 0.4.1）。
>
> 是否确认继续？
>
> 回复 **确认 / Yes / Y** 继续；否则返回模式选择。

### 1.4 提炼 Feature 名称

**仅当用户选择 `feat-branch` 或 `worktree` 模式时执行。** 若用户选择 `main-branch` 模式，则跳过本阶段，feature 名称由 AI 内部推导，仅用于 `devflow/<feature>/` 目录跟踪。

从确认的需求中提炼一个简短的 feature 名称：

- 使用英文小写 + 连字符（如 `user-auth`、`payment-flow`、`fix-login-timeout`）
- 4 个词以内，描述性强
- 用于分支名（`feature` 分支名或 worktree 分支名）和 `devflow/<feature>/` 目录名

向用户确认："基于需求，feature 名称建议为 `xxx`，可以吗？"

- 用户确认后暂存 feature 名称，进入 Phase 1.5 初始化会话

### 1.5 初始化会话

Feature 名称确认且模式选择完成后，按所选模式初始化会话。三种模式共享前置步骤 1.5.1 和 1.5.2。1.5.3 为 feat 模式的工作区状态提示（worktree 和 main 模式跳过）。之后进入各自的初始化路径：1.5.4（worktree）、1.5.5（feat）、1.5.6（main）。最终通过 `state.json` 中的 `isolation.mode` 记录所选模式。

#### 1.5.1 自动识别目标分支

检查 `master` 和 `main`，按以下优先级：

- 仅存在 `main` → 使用 `main`
- 仅存在 `master` → 使用 `master`
- 同时存在 → 默认使用 `main`
- 都不存在 → 报错并停止

#### 1.5.2 检查冲突

- **worktree / feat 模式**：检查是否已存在同名 branch 或开发环境目录
  ```bash
  git branch --list <feature>
  ls -d .claude/worktrees/devflow-<feature> 2>/dev/null
  ```
  - 存在：报错 "feature 名称 `<feature>` 已存在（branch 或开发环境），请更换名称。"
  - 不存在：继续

- **main 模式**：Step 0.4.1 已提示并发风险（不阻塞），此处不再重复。main 模式无需检查 branch 冲突（不创建新分支）。

#### 1.5.3 工作区状态提示（仅 feat 模式）

因为 feat 模式直接修改主仓库工作区，初始化前检查：

```bash
git status --short
```

- **无未提交变更**：直接继续
- **存在未提交变更**：提示但不阻塞：
  > "检测到工作区存在未提交变更。若继续，这些变更将被纳入本次 DevFlow 会话的开发范围。是否继续？
  > - 回复 **继续**：开始本次会话
  > - 回复 **清理**：请先 stash / commit / 丢弃变更后再开始"

**main 模式跳过此检查。** main 模式的工作区未提交变更属于其他并行会话，本会话不对其进行任何操作或确认。worktree 模式不需要此检查。

#### 1.5.4 worktree 模式初始化

执行当前 v3.0 的初始化流程：

```bash
git checkout -b <feature> <target-branch>
git checkout <target-branch>
git worktree add .claude/worktrees/devflow-<feature> <feature>
```

**在调用 `EnterWorktree` 之前**，先创建会话 junction，将 worktree 的 `~/.claude/projects/` 会话目录重定向到主仓库（Claude Code 按 CWD 绝对路径识别项目，EnterWorktree 会将会话迁移到 worktree 的项目目录；此 junction 必须在 EnterWorktree 之前创建，才能接住迁移的会话，确保 `/resume` 双向可见）：

```bash
MAIN_REPO=$(pwd -P)
WORKTREE="$MAIN_REPO/.claude/worktrees/devflow-<feature>"

python3 - "$MAIN_REPO" "$WORKTREE" << 'PYEOF'
import os, shutil, subprocess, sys

main = sys.argv[1]
wt = sys.argv[2]

def encode(p):
    """将绝对路径转为 ~/.claude/projects/ 下的目录名（所有非字母数字字符→-）"""
    return ''.join(c if c.isalnum() else '-' for c in os.path.abspath(p))

home = os.environ.get('USERPROFILE', os.path.expanduser('~'))
proj_dir = os.path.join(home, '.claude', 'projects')
main_proj = os.path.join(proj_dir, encode(main))
wt_proj = os.path.join(proj_dir, encode(wt))

# 确保主仓库项目目录存在
os.makedirs(main_proj, exist_ok=True)

# 清理 worktree 项目路径上已有的任何内容
if os.path.exists(wt_proj):
    try:
        import ctypes
        attrs = ctypes.windll.kernel32.GetFileAttributesW(wt_proj)
        if attrs != -1 and (attrs & 0x0400):
            # 已是 junction，直接删除
            subprocess.run(['cmd', '/c', 'rmdir', wt_proj], capture_output=True)
        else:
            # 真实目录 — 迁移内容后删除
            os.makedirs(main_proj, exist_ok=True)
            for item in os.listdir(wt_proj):
                src = os.path.join(wt_proj, item)
                dst = os.path.join(main_proj, item)
                if not os.path.exists(dst):
                    shutil.move(src, dst)
            os.rmdir(wt_proj)
            print('[DevFlow] Migrated stale worktree sessions to main repo')
    except Exception:
        pass

# 创建 junction: ~/.claude/projects/<worktree> -> ~/.claude/projects/<main>
subprocess.run(['cmd', '/c', 'mklink', '/J', wt_proj, main_proj], capture_output=True)
print('[DevFlow] Session junction created — worktree sessions → main repo')
PYEOF
```

然后调用 `EnterWorktree` 进入 worktree：

```
EnterWorktree path=".claude/worktrees/devflow-<feature>"
```

> **说明：** Claude Code 按 CWD 绝对路径将 worktree 视为独立项目，会话以 JSONL 格式存储在 `~/.claude/projects/<encoded-cwd>/` 下。EnterWorktree 会将当前会话迁移到 worktree 的项目目录，导致主仓库 CLI 无法再通过 `/resume` 看到该会话。此 junction 在 EnterWorktree 之前创建，使 worktree 的会话目录指向主仓库，所有会话统一存储、双向可见。`devflow/<feature>/` 跟踪文件保持普通目录，随 feature 分支提交。

然后按 1.5.7 补充运行时环境。

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

#### 1.5.5 feat 分支模式初始化

```bash
git checkout -b <feature> <target-branch>
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

#### 1.5.6 main 分支模式初始化

```bash
git checkout <target-branch>
git fetch origin
```

不创建分支，不创建 worktree。`feature` 名称仅用于 `devflow/<feature>/` 目录名。

**记录基准 commit（v3.3 新增，v3.4 简化）：**

初始化完成后，记录远端基准信息用于 Phase 6 安全推送：

```bash
# 记录远端基准 commit
BASE_REF="origin/<target-branch>"
BASE_COMMIT=$(git rev-parse "$BASE_REF")
echo "base_ref=$BASE_REF base_commit=$BASE_COMMIT"
```

> v3.4 不再记录工作区快照。工作区的未提交变更属于其他并行会话，本会话不对其进行任何检查或操作。

在 `state.json` 中填充：

```json
"commits": {
  "base_ref": "origin/<target-branch>",
  "base_commit": "<BASE_COMMIT>",
  "session_commits": [],
  "session_files": []
},
"port": null
```

- `commits.base_ref` 和 `commits.base_commit`：记录会话初始时的远端状态，Phase 6.5 用它判断是否有其他会话在远端推送了新提交
- `commits.session_commits`：Phase 4 中每次 commit 后追加，用于追溯本会话产生的提交
- `commits.session_files`（v3.5 新增）：本会话声明修改的文件列表（从 Phase 3 design.md 提取），用于 Phase 6.2 精确提交和并行会话文件冲突检测
- `port`（v3.5 新增）：本会话在 Phase 5 verify 时绑定的 dev 端口，避免与并行会话冲突

`state.json` 的 `isolation`：

```json
"isolation": {
  "mode": "main-branch",
  "path": ".",
  "branch": "<target-branch>",
  "target_branch": "<target-branch>"
}
```

#### 1.5.7 补充运行时环境（策略菜单）

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

#### 1.5.8 初始化状态目录和文件

在当前 `isolation.path` 指定的工作目录内创建 `devflow/<feature>/` 目录，并同时创建 `devflow/<feature>/screenshots/` 子目录，用于统一存放 clarify 与 verify 阶段的 Playwright 截图证据：

```bash
mkdir -p devflow/<feature>/screenshots
```

**忽略截图目录：**
- 检查仓库根目录 `.gitignore` 是否已包含 `devflow/*/screenshots/`
- 如未包含，追加以下内容，避免将生成的截图证据提交到 git：

```gitignore
# DevFlow generated evidence
devflow/*/screenshots/
```

写入 `state.json`：

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
  },
  "autonomous": {
    "enabled": false,
    "status": "idle",
    "started_at": null,
    "started_from": null,
    "resume_phase": null,
    "current_loop": 0,
    "max_loops": 20,
    "timeout_at": null,
    "last_report_at": null,
    "repair_cycles": {},
    "rollback_history": []
  },
  "commits": {
    "base_ref": "<target-branch 的远端引用，如 origin/main>",
    "base_commit": "<会话初始时 origin/<target-branch> 的 commit hash>",
    "session_commits": [],
    "session_files": []
  },
  "port": null
}
```

新增 `isolation` 字段记录会话隔离元数据，便于后续 CWD 守卫和 Phase 6 清理时定位。
`autonomous` 字段预留自循环状态。
`commits` 字段（v3.3 新增）记录 main 分支会话的基准 commit 和会话内产生的 commit 列表。`commits.session_files`（v3.5 新增）记录本会话声明修改的文件列表，用于文件冲突检测和 Phase 6.2 精确提交。`port`（v3.5 新增）为 Phase 5 verify 分配的独立端口。v3.6 使用 `.claude/hooks/devflow-locks.sh` 中的 git lock / verify lock 保护 Phase 4-6 的并发操作，使用 global-registry 的 push_queue 串行化推送。v3.4+ 不执行任何 `git stash` 操作——在共享 main 分支上，未提交变更归创建它的会话所有，其他会话不对其进行任何移动、暂存或清理。

> **向后兼容：** 旧 state.json 缺少 `commits` 字段时，Phase 6.5 回退到原有的 `--ff-only` 硬停止行为。

**自循环初始化：**
- 若用户在 Phase 1.2 输入 `auto` / `autonomous` / `自循环`，初始化时设置 `autonomous.enabled = true`，`autonomous.status = "running"`，`autonomous.started_at` 为当前时间，`autonomous.started_from = "clarify"`，`autonomous.timeout_at = 当前时间 + 4 小时`
- 若用户在后续 checkpoint 才触发自循环，则在进入下一阶段前更新上述字段
- 若未触发自循环，`autonomous.enabled` 保持 `false`

#### 1.5.9 提示用户

> "会话 `<feature>` 已准备就绪（模式：`<isolation.mode>`；路径：`<isolation.path>`；基于 `<target-branch>`）。已根据项目情况补充运行时环境（如适用）。可立即启动服务进行验收。后续所有文件操作将在当前工作目录内进行。"
> 
> 若已启用自循环模式，追加："自循环模式已启用，AI 将自动推进后续阶段。"

### 1.6 进入下一阶段

会话初始化后，自动进入 Phase 2（需求拆解）。

**若已启用自循环：** 进入 Phase 2 后，AI 直接使用 breakdown checklist 自评并推进，不再展示 checkpoint 给用户。

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
  REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
  CURRENT_BRANCH=$(git branch --show-current 2>/dev/null)
  if [ "$(pwd -P)" = "$REPO_ROOT" ] && [ "$CURRENT_BRANCH" = "$EXPECTED_BRANCH" ]; then
    echo "OK"
  else
    echo "WARN: 当前不在主仓库根目录或分支不匹配"
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
  $repoRoot = (git rev-parse --show-toplevel 2>$null | Out-String).Trim()
  $currentBranch = git branch --show-current 2>$null
  if ($PWD.Path -eq $repoRoot -and $currentBranch -eq $expectedBranch) {
    Write-Host "OK"
  } else {
    Write-Host "WARN: 当前不在主仓库根目录或分支不匹配"
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
8. 确认后写入 `devflow/<feature>/requirements.md`（使用 `internal/skills/breakdown/references/requirements-template.md` 格式）

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
> 请确认以上需求拆解是否准确、完整。回复 **确认 / Yes / Y** 进入方案蓝图；回复 **`auto` / `autonomous` / `自循环`** 进入方案蓝图并由 AI 自动推进后续阶段；否则请指出需要修改的地方。"

- **用户回复 "确认" / "Yes" / "Y"：** 进入 Phase 3
- **用户回复 `auto` / `autonomous` / `自循环`：** 进入 Phase 3 并切换为自循环模式
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
  REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
  CURRENT_BRANCH=$(git branch --show-current 2>/dev/null)
  if [ "$(pwd -P)" = "$REPO_ROOT" ] && [ "$CURRENT_BRANCH" = "$EXPECTED_BRANCH" ]; then
    echo "OK"
  else
    echo "WARN: 当前不在主仓库根目录或分支不匹配"
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
  $repoRoot = (git rev-parse --show-toplevel 2>$null | Out-String).Trim()
  $currentBranch = git branch --show-current 2>$null
  if ($PWD.Path -eq $repoRoot -and $currentBranch -eq $expectedBranch) {
    Write-Host "OK"
  } else {
    Write-Host "WARN: 当前不在主仓库根目录或分支不匹配"
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
5. **涉及文件声明（v3.5 新增，main 模式专属）：**
   - `design.md` 中必须包含"涉及文件"章节，列出所有计划新增/修改/删除的文件路径
   - 将文件列表写入 `state.json` 的 `commits.session_files` 数组
   - 读取 `devflow/.global-registry.json`，检查其他活跃会话是否已声明相同文件
   - 如果存在文件冲突 → 弹出版本冲突警告（见 3.1.1）
   - 如果无冲突 → 向 global-registry 注册本会话（files + port + heartbeat）
6. 写入 `devflow/<feature>/design.md` 和 `devflow/<feature>/test-cases.md`

#### 3.1.1 main 模式文件冲突检测（v3.5 新增）

仅当 `isolation.mode == "main-branch"` 且 `devflow/.global-registry.json` 中存在其他活跃 main 会话时执行。

```bash
# 读取 global-registry
REGISTRY=$(cat devflow/.global-registry.json 2>/dev/null || echo '{}')
# 检查每个已注册会话的 files 与本会话声明的是否有重叠
```

**无冲突：** 注册本会话，继续。

**有冲突：**

> ⚠️ 检测到与以下并行会话的文件冲突：
> - `<other-feature>`（阶段：`<phase>`）已声明修改：`<file-path>`
>
> 并行修改同一文件可能导致 Phase 6 rebase 冲突。
>
> 建议处理方式：
> 1. **等待** — 等 `<other-feature>` 推送后再继续
> 2. **协调** — 与 `<other-feature>` 协调分工，各改各的
> 3. **接受** — 理解风险，rebase 时手动解决冲突
>
> 回复 1/2/3 选择。

#### 3.1.2 端口分配（v3.5 新增，main 模式专属）

为并行 main 会话分配独立的 dev server 端口，避免 Phase 5 verify 时端口冲突：

```bash
# 从 global-registry 查找已用端口，从 3001 开始递增分配第一个空闲端口
BASE_PORT=3001
REGISTRY=$(cat devflow/.global-registry.json 2>/dev/null || echo '{}' )
USED_PORTS=$(echo "$REGISTRY" | jq -r '[.sessions[].port // empty] | .[]')
PORT=$BASE_PORT
while echo "$USED_PORTS" | grep -q "^$PORT$"; do
  PORT=$((PORT + 1))
done
echo "分配端口: $PORT"
```

将 `port` 写入 global-registry 和 state.json。Phase 5 运行 dev server 时使用此端口。

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
> 请确认以上方案蓝图是否准确、完整。回复 **确认 / Yes / Y** 进入编码实现；回复 **`auto` / `autonomous` / `自循环`** 进入编码实现并由 AI 自动推进后续阶段；否则请指出需要修改的地方。"

- **用户回复 "确认" / "Yes" / "Y"：**
  - main 模式：执行 3.1.1 冲突检测 → 无冲突 → 向 global-registry 注册 → 进入 Phase 4
  - 其他模式：直接进入 Phase 4
- **用户回复 `auto` / `autonomous` / `自循环`：** 进入 Phase 4 并切换为自循环模式（main 模式同样执行注册流程）
- **其他任何回复：** 视为需要修改。修正后重新输出完整方案蓝图，再次等待确认
- **不回复：** 自然暂停。更新 `state.json` 的 `phase` 为 `"implement"`。
- **自循环模式下：** AI 使用 blueprint checklist 自评，通过后自动进入 Phase 4。

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
  REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
  CURRENT_BRANCH=$(git branch --show-current 2>/dev/null)
  if [ "$(pwd -P)" = "$REPO_ROOT" ] && [ "$CURRENT_BRANCH" = "$EXPECTED_BRANCH" ]; then
    echo "OK"
  else
    echo "WARN: 当前不在主仓库根目录或分支不匹配"
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
  $repoRoot = (git rev-parse --show-toplevel 2>$null | Out-String).Trim()
  $currentBranch = git branch --show-current 2>$null
  if ($PWD.Path -eq $repoRoot -and $currentBranch -eq $expectedBranch) {
    Write-Host "OK"
  } else {
    Write-Host "WARN: 当前不在主仓库根目录或分支不匹配"
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
6. **自循环执行：**
   - 若 `autonomous.enabled == true`，所有 T-xxx 完成后，AI 使用 implement checklist 自评
   - 自评通过后自动进入 Phase 5，不等待用户确认
   - 自评不通过时，自动修正并重新自评
7. **main 分支精确提交（v3.3 新增，v3.6 增强）：**
   - 仅当 `isolation.mode == "main-branch"` 时执行
   - **精确 add：** 每个 sub-agent commit 时只 add 该任务声明的涉及文件，不使用 `git add -A` / `git add -u` / `git add .`：
     ```bash
     # 只 add 本会话声明范围内的文件
     git add src/auth.ts src/utils/session.ts  # 从 tasks.md T-xxx 的"涉及文件"列获取
     ```
   - **git lock 保护（v3.6 新增）：** commit 前获取 git lock，防止并行会话的 git 操作互相损坏：
     ```bash
     source .claude/hooks/devflow-locks.sh
     acquire_git_lock "<feature>"
     git add src/auth.ts src/utils/session.ts
     git commit -m "feat: T-001 add session helper"
     release_git_lock
     ```
   - **提交追踪：** commit 后记录 hash 到 `state.json` 的 `commits.session_commits`
     ```bash
     LATEST_COMMIT=$(git rev-parse HEAD)
     jq --arg c "$LATEST_COMMIT" '.commits.session_commits += [$c]' devflow/<feature>/state.json > tmp && mv tmp devflow/<feature>/state.json
     ```
   - **文件追踪：** 将实际涉及的文件追加到 `commits.session_files`（去重）
   - **registry 心跳：** 更新 `devflow/.global-registry.json` 中本会话的 `last_heartbeat`

### 4.2 实现中回退机制

在编码实现过程中，如果发现以下任一情况：
- 按照需求拆解的任务规范无法达成需求
- 设计规格与实际实现存在不可调和的冲突
- 需求边界不清晰导致实现无法收敛
- 技术约束导致原方案不可行
- 前置文档无法指导当前工作

**人工模式下必须停止当前实现，主动提出：**
> "当前实现遇到阻塞：`<原因>`。按照需求拆解/方案蓝图无法继续推进。建议回退到 `<Phase 1/2/3>` 重新确认需求/拆解/设计。是否回退？"

只有用户确认回退后，才允许回退并重新进入上游阶段。回退后必须重新完成该阶段并再次获得用户确认，才能继续。

**自循环模式下：**
- AI 自行判断阻塞是否可自愈
- 若根因在上游阶段，自动回退并更新 `rollback_history`
- 若无法自愈，暂停并报告用户

### 4.3 用户反馈与修正

如果用户对编码实现提出任何非确认性反馈（包括任务拆解、架构图、代码方向等）：
1. 一律视为需要修改
2. 不要只回复"已修改"或只修改局部
3. **必须重新输出完整的编码实现状态**（任务清单 + 架构图 + 当前进度）
4. 明确询问："以上是修正后的完整编码实现状态，请确认是否有问题。回复 **确认 / Yes / Y** 进入测试验证；回复 **`auto` / `autonomous` / `自循环`** 进入测试验证并由 AI 自动推进后续阶段；否则请指出需要修改的地方。"
5. 只有用户明确回复确认后，才能进入 Phase 5

### 4.4 Checkpoint

> "编码实现完成。所有 T-xxx 任务已完成，tasks.md 已更新。
>
> 请确认以上编码实现是否完整、符合预期。回复 **确认 / Yes / Y** 进入测试验证；回复 **`auto` / `autonomous` / `自循环`** 进入测试验证并由 AI 自动推进后续阶段；否则请指出需要修改的地方。"

- **用户回复 "确认" / "Yes" / "Y"：** 进入 Phase 5
- **用户回复 `auto` / `autonomous` / `自循环`：** 进入 Phase 5 并切换为自循环模式
- **自循环模式下：** AI 使用 implement checklist 自评，通过后自动进入 Phase 5
- **其他任何回复：** 视为需要修改。修正后重新输出完整编码实现状态，再次等待确认
- **不回复：** 自然暂停。更新 `state.json` 的 `phase` 为 `"verify"`。

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
  REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
  CURRENT_BRANCH=$(git branch --show-current 2>/dev/null)
  if [ "$(pwd -P)" = "$REPO_ROOT" ] && [ "$CURRENT_BRANCH" = "$EXPECTED_BRANCH" ]; then
    echo "OK"
  else
    echo "WARN: 当前不在主仓库根目录或分支不匹配"
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
  $repoRoot = (git rev-parse --show-toplevel 2>$null | Out-String).Trim()
  $currentBranch = git branch --show-current 2>$null
  if ($PWD.Path -eq $repoRoot -and $currentBranch -eq $expectedBranch) {
    Write-Host "OK"
  } else {
    Write-Host "WARN: 当前不在主仓库根目录或分支不匹配"
  }
}
```
- 检测为 OK：正常继续
- **worktree 模式且检测到 WARN**：尝试 `EnterWorktree path="<isolation.path>"`；如不可用，提示用户确认并执行 `cd` 恢复
- **feat 模式且检测到 WARN**：提示用户执行 `git checkout <feature>` 并 `cd <main-repo-root>`
- **main 模式且检测到 WARN**：提示用户执行 `git checkout <target-branch>` 并 `cd <main-repo-root>`

### 5.1 流程

1. 加载所有跟踪文件（requirements.md, design.md, tasks.md, test-cases.md）
2. **确保截图目录存在：** 验证开始前，确认 `devflow/<feature>/screenshots/` 目录存在。如不存在，使用 `Bash` 创建（例如 `mkdir -p devflow/<feature>/screenshots`）
3. **main 模式端口隔离（v3.5 新增）：**
   - 仅当 `isolation.mode == "main-branch"` 时执行
   - 读取 `state.json` 中的 `port` 字段
   - 启动 dev server 时使用该端口：`npm run dev -- --port <port>`（或项目的等效命令）
   - 确保 Playwright 测试连接 `http://localhost:<port>` 而非默认端口
4. **verify lock（v3.6 新增）：**
   - main 模式下，运行任何 Playwright 验证前获取 verify lock：
     ```bash
     source .claude/hooks/devflow-locks.sh
     acquire_verify_lock "<feature>"
     ```
   - 如果其他会话正在验证，等待其完成（最多 15 分钟）
   - 验证全部完成后释放：`release_verify_lock`
   - 确保同时只有一个会话在跑 Playwright，避免共享运行时互相干扰
6. **TC 智能路由：** 按关键字和类型将每条 TC 分发到 L1/L2/L3
7. **L1 烟雾扫描：** Playwright 自动扫描所有路由（console error / network health / runtime health / DOM snapshot），检查页面基础设施是否正常
8. **L2 交互验证：** 对交互类 TC 使用 Playwright 执行真实用户操作（点击、输入、提交），记录 Interaction Trace（操作前后 DOM diff），判断功能是否真的可用
9. **L3 结构化手工验证：** 对无法自动化的 TC（权限、动画、视觉等），逐条收集证据，无证据不标记通过
10. **深度评分：** 计算验证深度（真正执行过的 TC 占比）和证据覆盖率，暴露"走过场"验证
11. 发现问题时：
   - L1 失败 → 基础设施问题，建议重新执行对应 T-xxx
   - L2 失败 → 功能 bug，建议重新执行对应 T-xxx
   - L3 失败 / 设计问题 → 建议回退到 Phase 3
   - 需求问题 → 建议回退到 Phase 1/2
12. **自循环修复循环（autonomous.enabled == true）：**
   - 验证失败时，AI 首先判断失败根因阶段
   - 根因在 implement：自动返回 Phase 4 修复，`repair_cycles["implement-verify"]` 递增
   - 根因在 blueprint/breakdown/clarify：自动回退到对应阶段，`rollback_history` 记录原因
   - 修复/回退完成后重新推进到 verify
   - 每次循环前检查 `max_loops` 与 `timeout_at`，超限则熔断暂停
13. 生成统一验证报告（verification-log.md），包含三层结果 + 交互追踪 + 深度评分
14. **释放 verify lock（v3.6 新增）：**
    - 所有验证完成（通过或失败）后，释放 verify lock：
      ```bash
      source .claude/hooks/devflow-locks.sh
      release_verify_lock
      ```
    - 释放后，等待中的其他会话可以开始验证

**Playwright 截图保存规范：**
- 所有通过 `browser_take_screenshot` 捕获的截图，必须保存到 `devflow/<feature>/screenshots/`
- L1 截图：`devflow/<feature>/screenshots/l1-<TC编号>-<page-name>-<timestamp>.png`
- L2 截图：
  - 操作前：`devflow/<feature>/screenshots/l2-<TC编号>-<step-N>-before-<timestamp>.png`
  - 操作后：`devflow/<feature>/screenshots/l2-<TC编号>-<step-N>-after-<timestamp>.png`
- L3 手工证据：如包含截图，也统一放入该目录
- 截图目录属于生成的验证证据，应加入 `.gitignore`（例如 `devflow/*/screenshots/`），不提交到 git
- 在 verification-log.md 中引用截图时，使用相对路径 `devflow/<feature>/screenshots/...`

### 5.2 验证结果

**全部通过（深度 = 100%）：**

> "自动化验证已全部通过（深度 100%，证据覆盖率 100%）。
>
> 验证报告已保存到 devflow/<feature>/verification-log.md。
>
> 请在实际环境中进行人工验收。确认验收通过后，才能进行归档和提交。
> 回复 **确认 / Yes / Y** 表示人工验收通过，进入流程完成；否则请指出问题。"

**人工模式下不自动进入 Phase 6。** 必须等待用户明确回复确认后，才允许进入 Phase 6。

**自循环模式下：**
- AI 使用 verify checklist 自评（verification-log.md 完整、深度 100%、无失败项）
- 自评通过后自动进入 Phase 6，不再询问人工验收
- 自评不通过时，按 5.1 第 9 条执行修复循环或回退

**深度不足或有失败项：**

> "验证未通过 / 验证深度不足。具体情况如下：...
>
> 请确认处理方式：
> [修复后重新验证] 返回对应阶段修复
> [回退到 blueprint/breakdown/clarify] 重新确认
> [保留会话稍后继续]"

**自循环模式下深度不足或有失败项：**
- 优先自动返回 implement 修复
- 若根因在上游，自动回退
- 若无法自愈或达到熔断条件，暂停并报告

### 5.3 人工验收 Checkpoint

验证通过后，人工模式下必须增加独立的"人工验收" checkpoint：

> "所有自动化验证已执行完毕。请进行人工验收：
> 1. 打开验证报告 devflow/<feature>/verification-log.md
> 2. 检查 L1/L2/L3 结果和证据
> 3. 在实际环境中试用关键功能
> 4. 确认无误后回复 **确认 / Yes / Y**
>
> 只有收到明确确认后，才会进入归档和提交。"

只有用户明确回复确认后，才允许进入 Phase 6。

**自循环模式下：** 跳过人工验收 checkpoint，由 AI 自评后直接推进到 Phase 6。

---

## Phase 6: 流程完成

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
  REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
  CURRENT_BRANCH=$(git branch --show-current 2>/dev/null)
  if [ "$(pwd -P)" = "$REPO_ROOT" ] && [ "$CURRENT_BRANCH" = "$EXPECTED_BRANCH" ]; then
    echo "OK"
  else
    echo "WARN: 当前不在主仓库根目录或分支不匹配"
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
  $repoRoot = (git rev-parse --show-toplevel 2>$null | Out-String).Trim()
  $currentBranch = git branch --show-current 2>$null
  if ($PWD.Path -eq $repoRoot -and $currentBranch -eq $expectedBranch) {
    Write-Host "OK"
  } else {
    Write-Host "WARN: 当前不在主仓库根目录或分支不匹配"
  }
}
```
- 检测为 OK：正常继续
- **worktree 模式且检测到 WARN**：尝试 `EnterWorktree path="<isolation.path>"`；如不可用，提示用户确认并执行 `cd` 恢复
- **feat 模式且检测到 WARN**：提示用户执行 `git checkout <feature>` 并 `cd <main-repo-root>`
- **main 模式且检测到 WARN**：提示用户执行 `git checkout <target-branch>` 并 `cd <main-repo-root>`

### 6.0 模式路由

Phase 6 的收尾逻辑按 `isolation.mode` 分为三条路径：

- `worktree`：保持现有 v3.0 流程（预完成提交 → 合并验证 → 合并到 target → 清理 worktree）
- `feat-branch`：在主仓库中把 target 同步到 feat，再合并 feat 到 target，保留 feat 分支
- `main-branch`：在主仓库中同步 target 后直接 push，不创建/删除分支

### 6.1 确认

**人工模式：**

> "DevFlow 流程已通过人工验收。是否结束会话并提交？回复 **确认 / Yes / Y** 完成并提交；否则请说明。"

**自循环模式：**
- AI 自评 Phase 6 入口条件（verify 已通过、工作区可提交）
- 自评通过后自动执行 6.2 及后续收尾流程
- 收尾完成后输出完成报告，更新 `state.json`：`phase: "completed"`、`autonomous.status: "completed"`

### 6.2 预完成提交（兜底保护）

**目的：** 防止存在未提交文件（如下载的数据、临时配置等），会话结束后丢失。

**注意：** 只有在 Phase 5 通过验收后，才执行提交。人工模式下需用户明确确认；自循环模式下由 AI 自评通过后自动执行。合并验证在后续 6.3/6.4/6.5 中按模式执行。

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

2. **根据检测结果处理（worktree / feat 模式）：**

   **情况 A — 无任何未提交变更：** 直接进入下一阶段。

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

   **main 模式特殊处理（v3.4+, v3.5 增强）：**

   main 模式的工作区未提交变更可能属于其他并行会话，本会话只提交自己产生的变更。Phase 6.2 在 main 模式下仅 commit `commits.session_files` 范围内的文件和 `devflow/<feature>/` 跟踪文件：

   ```bash
   # 读取本会话的涉及文件
   SESSION_FILES=$(jq -r '.commits.session_files[]' devflow/<feature>/state.json 2>/dev/null)
   # 精确 add
   for f in $SESSION_FILES; do
     git add "$f" 2>/dev/null || true
   done
   git add "devflow/<feature>/" 2>/dev/null || true
   # 检查是否有需要提交的变更
   git diff --cached --quiet || git commit -m "chore: pre-completion commit for <feature>"
   ```

   - **不执行** `git add -u` 或 `git add -A`（会包含其他会话的未提交变更）
   - 如果存在本会话文件范围外的未提交变更，跳过并提示："检测到其他会话的未提交变更，已跳过"
   - 如果 `devflow/<feature>/` 跟踪文件有未提交的，精确 add 这些文件后 commit

3. **提交后二次确认：**
   ```bash
   git status --porcelain
   ```
   必须干净才能标记完成（仅检查本会话相关文件）。其他会话的未提交变更忽略。

### 6.3 worktree 模式收尾

保持原 v3.0 合并验证、合并到 target、清理流程。

#### 6.3.1 合并验证

确认完成后，**必须先执行**合并验证：

#### 6.3.1.1 识别目标分支

自动识别目标分支（`master` 或 `main`），规则同 Phase 1.4。

#### 6.3.1.2 拉取远端并验证本地状态

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

- **OK：** 继续 6.3.1.3
- **WARN：** 执行 `git merge --ff-only origin/<target-branch>` 将本地目标分支同步到远端最新
  - `--ff-only` 成功 → 继续 6.3.1.3
  - `--ff-only`失败（分叉）→ **立即停止**，提示：
    > "⚠️ 本地 <target-branch> 与远端分叉，存在本地独有的提交。不允许继续，请手动处理后再运行 /devflow。"

#### 6.3.1.3 计算基准 commit

```bash
git merge-base <target-branch> <feature>
```

#### 6.3.1.4 检查目标分支新变更

列出目标分支自基准 commit 以来的所有 merge commit：

```bash
git log --merges --first-parent <base-commit>..<target-branch>
```

- **无新 merge commit：** 跳过 6.3.1.5 ~ 6.3.1.7，直接进入 6.3.3 合并 feature 到 target。
- **有新 merge commit：** 进入 6.3.1.5 涉及 feat 验证。

#### 6.3.1.5 涉及 feat 验证

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

#### 6.3.1.6 执行 catch-up merge（目标分支 → feature）

在 **worktree** 内执行。将目标分支的最新内容合并到 feature 分支，目的是让 feature 分支追上目标分支的进度，在 6.3.1.7 中重新验证兼容性。

⚠️ **merge 方向是 `<target-branch>` 合并 INTO `<feature>`，不是反过来。** 当前在 feature 分支上：

```bash
git checkout <feature>                     # 确认在 feature 分支
git merge <target-branch>                  # 将 target 合并到 feature
```

**只允许 merge，不允许 rebase。**

- **无冲突：** 继续 6.3.1.7
- **有冲突：**
  > "检测到合并冲突，请人工解决以下文件后再继续：
  > - `<conflict-file-1>`
  > - `<conflict-file-2>`
  > 
  > 不允许自动覆盖合并。解决后回复 **确认 / Yes / Y** 继续。"
  
  用户确认解决后，继续 6.3.1.7。

#### 6.3.1.7 当前 feature 重验证

merge 完成后，重新跑当前 feature 的测试用例和验收规格（`devflow/<feature>/test-cases.md`）。

- 全部通过 → 进入 6.3.3 合并 feature 到 target
- 未通过 → 停止，提示用户修复

#### 6.3.2 预完成提交（兜底保护）

> 预完成提交已在 6.2 中统一执行。worktree 模式进入 6.3.1 合并验证前应确保工作区干净；如不干净，需先处理未提交变更再继续。

#### 6.3.3 合并到目标分支（严格安全流程）

将 feature 分支合并到目标分支。这是整个流程中唯一一次变更目标分支的操作，**必须严格遵守以下步骤，每一步都有验证，禁止跳步。**

⚠️ **所有以下操作在主仓库根目录执行，不在 worktree 中。** 执行前确认 CWD 不在 `.claude/worktrees/devflow-*` 路径下。

#### 6.3.3.1 拉取远端并验证状态

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

- **OK：** 继续 6.3.3.2
- **WARN：** 执行 `git merge --ff-only origin/<target-branch>`
  - `--ff-only` 成功 → 继续 6.3.3.2
  - `--ff-only` 失败（分叉）→ **硬停止。** 输出：
    > "⛔ 本地 <target-branch> 与远端分叉。存在本地独有的提交，或本地历史与远端不一致。
    > 继续合并将导致覆盖远端提交。请手动处理后再运行 /devflow。
    > 建议：检查 `git log --oneline --graph <target-branch> origin/<target-branch>`，确认分叉原因。"

#### 6.3.3.2 确认 feature 分支可访问

```bash
# 确认 feature branch 存在且与 worktree 中的一致
git log --oneline -1 <feature>
```

读取 `devflow/<feature>/state.json` 确认 `isolation.branch` 与 `<feature>` 一致。

#### 6.3.3.3 切换到目标分支

```bash
git checkout <target-branch>
```

验证切换成功：
```bash
git branch --show-current
```
输出必须是 `<target-branch>`。不是则停止。

#### 6.3.3.4 合并 feature 分支（--no-ff 强制生成 merge commit）

```bash
git merge --no-ff <feature>
```

**只允许 `--no-ff`，不允许 fast-forward、squash、rebase。**

- **合并成功：** 继续 6.3.3.5
- **有冲突（git 返回非零退出码）：**
  > "⛔ 合并到目标分支时检测到冲突。这可能是因为 6.3.1.6 中已合并的目标分支内容与当前目标分支不一致（远端有新提交），或 feature 分支存在未预期的变更。
  > 
  > 请检查并手动解决以下冲突文件：
  > - `<conflict-file-1>`
  > - `<conflict-file-2>`
  > 
  > 解决后回复 **确认 / Yes / Y** 继续，我将验证合并结果。"

#### 6.3.3.5 合并结果验证

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
- 第二个 parent 是 `<feature>` 的最新 commit
- 当前分支是 `<target-branch>`

如果任一项不满足 → 停止，检查输出。

#### 6.3.3.6 推送前预检

在推送前最后一次确认不会覆盖远端：

```bash
# 目标分支的本地 HEAD 必须是 origin/<target-branch> 的直接后代
git merge-base --is-ancestor origin/<target-branch> HEAD && echo "OK: 推送安全（本地是远端的 fast-forward）" || echo "REJECT: 推送到远端将被拒绝或覆盖"
```

- **OK：** 继续 6.3.3.7
- **REJECT：** **硬停止。** 输出：
  > "⛔ 检测到当前本地 <target-branch> 不是远端的 fast-forward 后代。推送将被拒绝或覆盖远端。
  > 请检查 `git log --oneline --graph origin/<target-branch> HEAD`，确认原因后手动处理。"

#### 6.3.3.7 推送到远端

```bash
git push origin <target-branch>
```

⚠️ **绝对禁止 `git push --force`、`git push --force-with-lease`、或任何形式的强制推送。**

- **推送成功：** 继续 6.3.3.8
- **推送被拒绝：** **硬停止。** 输出：
  > "⛔ 推送到远端被拒绝。远端在 6.3.3.6 之后有新的提交，或存在其他冲突。
  > 请从 6.3.3.1 重新执行（重新 fetch 并验证）。"

#### 6.3.3.8 推送后远端验证

```bash
# 确认远端目标分支 HEAD 与本地一致
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/<target-branch>)
[ "$LOCAL" = "$REMOTE" ] && echo "✅ 推送成功，远端已更新" || echo "REJECT: 远端与本地不一致"
```

- **OK：** 进入 6.3.4 清理
- **不一致：** 输出：
  > "⚠️ 推送后远端与本地不一致，可能是推送未完成或远端 hook 修改了提交。请检查 `git log origin/<target-branch>`。"

#### 6.3.4 自动清理开发环境副本（worktree）

提交成功后，自动删除 worktree。读取 `devflow/<feature>/state.json` 中 `isolation.path` 和 `isolation.branch`。

**清理前先移除会话 junction：**

```bash
python3 - << 'PYEOF'
import os, subprocess, sys

def encode(p):
    """将绝对路径转为 ~/.claude/projects/ 下的目录名（所有非字母数字字符→-）"""
    return ''.join(c if c.isalnum() else '-' for c in os.path.abspath(p))

home = os.environ.get('USERPROFILE', os.path.expanduser('~'))
proj_dir = os.path.join(home, '.claude', 'projects')
wt_proj = os.path.join(proj_dir, encode(os.getcwd()))

if not os.path.exists(wt_proj):
    print('[DevFlow] No session junction to remove')
    sys.exit(0)

# Check if it's a junction
try:
    import ctypes
    attrs = ctypes.windll.kernel32.GetFileAttributesW(wt_proj)
    if attrs != -1 and (attrs & 0x0400):
        subprocess.run(['cmd', '/c', 'rmdir', wt_proj], capture_output=True)
        print('[DevFlow] Session junction removed')
    else:
        print('[DevFlow] Not a junction — leaving in place')
except Exception:
    if os.path.islink(wt_proj):
        os.unlink(wt_proj)
        print('[DevFlow] Session symlink removed')
    else:
        print('[DevFlow] Not a symlink — leaving in place')
PYEOF
```

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

清理前确认 worktree 内无未提交变更（Phase 6.2 已保证）。清理失败时给出明确提示，包括：
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

#### 6.3.5 标记完成

更新 `devflow/<feature>/state.json`：

```json
{
  "phase": "completed",
  "completed_at": "<ISO timestamp>",
  "autonomous": {
    "status": "completed",
    "completed_at": "<ISO timestamp>"
  }
}
```

输出："DevFlow v3.0 流程完成。跟踪文件保存在 devflow/<feature>/ 目录。"  
若处于自循环模式，追加输出完成报告。

#### 6.3.6 保留会话

如果用户选择保留会话，状态文件标记 `phase: "completed"`，worktree 可以保留或手动清理。

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
git merge-base --is-ancestor origin/<target-branch> HEAD && echo "OK" || echo "REJECT"
# OK：继续下一步
# REJECT：硬停止。本地 target 不是远端的 fast-forward 后代，禁止推送。

# 6. 推送
git push origin <target-branch>

# 推送后验证
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/<target-branch>)
[ "$LOCAL" = "$REMOTE" ] && echo "✅ 推送成功" || echo "⚠️ 远端与本地不一致"

# 7. 保留 feat 分支，不删除
```

### 6.5 main 分支模式收尾

main 模式不创建 feature 分支，所有提交直接在 `<target-branch>` 上。当多个 main 会话并发时，Phase 6.2 的预完成提交可能产生本地分叉。v3.3 起，Phase 6.5 支持并发安全的推送流程。

#### 6.5.1 分析本地与远端关系

```bash
# Step 1: 确认在 target 分支，拉取最新远端
git checkout <target-branch>
git fetch origin

# Step 2: 读取会话基准信息
BASE_COMMIT=$(jq -r '.commits.base_commit // empty' devflow/<feature>/state.json)
BASE_REF=$(jq -r '.commits.base_ref // "origin/<target-branch>"' devflow/<feature>/state.json)

# Step 3: 分析本地与远端的关系
LOCAL_AHEAD=$(git rev-list $BASE_REF..HEAD --count 2>/dev/null || echo 0)
REMOTE_AHEAD=$(git rev-list HEAD..$BASE_REF --count 2>/dev/null || echo 0)
```

#### 6.5.2 按场景处理

根据 `LOCAL_AHEAD` 和 `REMOTE_AHEAD` 的值：

| 场景 | LOCAL_AHEAD | REMOTE_AHEAD | 含义 | 处理 |
|------|-------------|--------------|------|------|
| A | 0 | >0 | 本地落后于远端（仅其他会话推送了） | `git merge --ff-only $BASE_REF` |
| B | >0 | 0 | 本地领先于远端（只有本会话有提交） | 正常推送 |
| C | >0 | >0 | 本地和远端分叉（**并发会话场景**） | 进入 6.5.3 rebase 流程 |
| D | 0 | 0 | 本地与远端一致（无可推送内容） | 跳过推送，直接标记完成 |

**向后兼容：** 如果 `BASE_COMMIT` 为空（旧会话未记录基准），回退到原 `--ff-only` 硬停止行为：

```bash
git merge --ff-only $BASE_REF   # 失败则硬停止，提示用户重新初始化会话
```

#### 6.5.3 并发场景：rebase 本地提交

当本地和远端分叉时（场景 C），远端有其他会话的提交，本地有本会话的提交。需要将本地提交 rebase 到远端最新提交之上：

```bash
# Step C1: 确认 session_commits 中的提交全部是本地的（未被推送过）
# 如果 session_commits 为空（旧会话），以 base_commit 为界：
#   git rebase --onto $BASE_REF $BASE_COMMIT
# 如果 session_commits 不为空，rebase 从 base_commit 之后到 HEAD 的所有提交：
git rebase --onto $BASE_REF $BASE_COMMIT
```

> ⚠️ `git rebase --onto` 只移动本地未推送的提交，不改写远端历史。
> 这符合 DevFlow 的禁止 force push 原则——force push 只在改写远端历史时发生，rebase 本地提交是安全的。

**rebase 成功：** 进入 6.5.4 重验证。

**rebase 冲突：**

> ⚠️ 检测到合并冲突。可能原因：其他会话修改了与本会话相同的文件。
>
> 冲突文件：
> - `<conflict-file-1>`
> - `<conflict-file-2>`
>
> 请手动解决冲突后执行：
> ```bash
> git add <resolved-files>
> git rebase --continue
> ```
> **不要使用 `git rebase --abort`**（会丢失本会话的提交进度）。
>
> 解决后回复 **确认 / Yes / Y** 继续。

#### 6.5.4 重验证（rebase 后）

rebase 成功后，运行快速烟雾测试验证 rebase 没有引入回归：

- 如果项目有自动化测试：运行项目测试套件
- 如果有 Playwright 测试：扫描关键路由，检查 console error / network health
- 快速通过即继续；失败则报告并暂停，等待用户决策

#### 6.5.5 推送排队（v3.6 新增）

main 模式下推送必须排队，确保同一时间只有一个会话推送，避免级联 rebase 冲突。

```bash
# 1. 加入 push queue
REGISTRY=".global-registry.json"
jq ".push_queue += [\"$FEATURE\"]" "$REGISTRY" > tmp && mv tmp "$REGISTRY"

# 2. 等待轮到自己（同时更新 registry heartbeat）
while [ "$(jq -r '.push_queue[0]' "$REGISTRY")" != "$FEATURE" ]; do
  echo "⏳ 推送队列中，前面还有: $(jq -r '.push_queue[1:-1] | join(", ")' "$REGISTRY")"
  sleep 10
  # 更新 heartbeat 防止被僵死检测误判
  jq --arg f "$FEATURE" --arg t "$(date -u +%Y-%m-%dT%H:%M:%S+08:00)" '.sessions[$f].last_heartbeat = $t' "$REGISTRY" > tmp && mv tmp "$REGISTRY"
done

# 3. 获取 git lock（确保 rebase/push 期间无并发 git 操作）
source .claude/hooks/devflow-locks.sh
acquire_git_lock "$FEATURE"

# 4. 推送前 fast-forward 预检（在 git lock 保护下）
git merge-base --is-ancestor $BASE_REF HEAD && echo "OK" || echo "REJECT"
# REJECT → 重新 fetch + rebase（在 git lock 保护下）

# 5. 推送
git push origin <target-branch>

# 6. 释放 git lock
release_git_lock

# 7. 出队
jq ".push_queue = .push_queue[1:]" "$REGISTRY" > tmp && mv tmp "$REGISTRY"
```

**推送被拒时（远端在排队期间有新提交）：**

- 人工模式：自动回到 6.5.1 重新执行（最多 3 次重试）
- 自循环模式：自动回到 6.5.1 重新执行，重试计数计入 `autonomous.current_loop`

#### 6.5.6 推送后验证

```bash
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse $BASE_REF)
[ "$LOCAL" = "$REMOTE" ] && echo "✅ 推送成功" || echo "⚠️ 远端与本地不一致"
```

注意：

- main 模式不执行 catch-up merge（已在 target 上）
- v3.3 起，并发场景使用 `git rebase --onto` 替代 `--ff-only` 硬停止
- 旧会话（无 `commits.base_commit`）回退到原 `--ff-only` 硬停止行为

### 6.6 清理总结

- **worktree 模式**：`ExitWorktree remove` + 删除 feature 分支
- **feat 模式**：无 worktree 清理，保留 feature 分支
- **main 模式**：无 worktree 清理，无分支删除，无 stash 操作。从 `devflow/.global-registry.json` 移除本会话条目，释放端口。

```bash
# main 模式完成后从 registry 移除
if [ -f devflow/.global-registry.json ]; then
  jq "del(.sessions[\"<feature>\"])" devflow/.global-registry.json > tmp && mv tmp devflow/.global-registry.json
fi
```

所有模式最后更新 `state.json`：`phase: "completed"`。

---

## Checkpoint 机制总结

每个阶段结束时统一格式：

> "✅ [阶段名] 完成。
>
> 请确认以上结果是否准确、完整。回复 **确认 / Yes / Y** 进入下一阶段；回复 **`auto` / `autonomous` / `自循环`** 进入下一阶段并由 AI 自动推进后续阶段；否则请指出需要修改的地方。"

| 用户输入 | 行为 |
|---------|------|
| 确认 / Yes / Y / y / 是的 | 进入下一阶段 |
| `auto` / `autonomous` / `自循环` | 切换为自循环模式，AI 使用自评 checklist 自动推进后续阶段 |
| 其他任何回复（包括"需要修改"、指出问题、部分肯定、沉默、跳转请求等） | **一律视为需要修改**。修正后重新输出完整结果，再次等待确认 |
| 不回复 | 自然暂停，更新状态文件 |

**checkpoint 只提供"确认"一个明确选项。** 用户不确认就是需要修改。回退、跳转等需求通过用户在"需要修改"反馈中提出，或者由 AI 在发现阻塞时主动提出。

**自循环模式下 checkpoint 的行为：**
- AI 不展示 checkpoint 给用户，而是使用对应阶段的自评 checklist 自行判断
- 自评通过后自动推进
- 自评不通过时自动修正或回退
- 仅在阻塞、熔断、完成时向用户发送汇总报告

---

## 自循环模式（Autonomous Mode）

### 触发方式

用户在任意 checkpoint 输入以下任一指令：
- `auto`
- `autonomous`
- `自循环`

### 启动报告

切换为自循环模式后，输出：

```
🤖 已启用自循环模式
- 起始阶段: <phase>
- 目标: 完成整个 DevFlow 流程并提交推送
- 最大循环: <max_loops>
- 超时时间: <timeout_at>
- 常规推进将不打扰你，遇到阻塞或完成时汇总报告。
```

### 自评 Checklist

#### Clarify
- [ ] 需求总结包含目标、包含项、排除项、成功标准、约束
- [ ] 无 open_questions
- [ ] 用户已确认（自循环起点必须是已确认状态）

#### Breakdown
- [ ] R-xxx 清单完整，编号连续
- [ ] 每条 R-xxx 含优先级、依赖、验收标准
- [ ] 无待澄清项

#### Blueprint
- [ ] design.md 包含流程图、规格边界、架构图、涉及文件
- [ ] test-cases.md 为每条 R-xxx 编写 TC-xxx
- [ ] TC 覆盖正常路径与异常路径

#### Implement
- [ ] T-xxx 全部完成
- [ ] tasks.md 已更新状态
- [ ] 代码已提交（至少一次 commit）
- [ ] 前置文档（requirements.md + design.md）足以指导实现

#### Verify
- [ ] verification-log.md 已生成
- [ ] L1/L2/L3 全部通过或已记录证据
- [ ] 深度评分 100%

#### Completed
- [ ] 工作区干净或已提交
- [ ] 合并验证通过（worktree/feat 模式）
- [ ] main 模式：rebase 成功（如进入 6.5.3 流程）
- [ ] main 模式：rebase 后重验证通过（如适用）
- [ ] fast-forward 预检通过
- [ ] push 成功且远端一致
- [ ] main 模式：stash 已清理（如适用）
- [ ] state.json phase=completed

### 熔断条件

自循环在以下任一条件满足时暂停并报告：
- `current_loop >= max_loops`
- 当前时间超过 `timeout_at`
- 连续多次在同一对阶段间循环无进展
- 遇到无法自愈的阻塞（安全边界、合并冲突、无法推断的根因等）

### 报告模板

#### 完成报告

```
✅ 自循环完成
- 结束阶段: completed
- 总循环: <current_loop>
- 最终提交: <commit-hash>
- 验证报告: devflow/<feature>/verification-log.md
```

#### 熔断/阻塞报告

```
⏸️ 自循环已暂停
- 当前阶段: <phase>
- 原因: <timeout | max_loops | unrecoverable-block>
- 已尝试: <current_loop> 次
- 建议: <action>
```

---

## 阶段间确认规则

| 从 → 到 | 人工模式必须满足的条件 | 自循环模式替代条件 |
|---------|----------------------|-------------------|
| clarify → breakdown | 用户明确回复"确认"/"Yes"/"Y"；feature 名称确认；会话初始化成功 | 用户输入 `auto` / `autonomous` / `自循环`，或此前已启用自循环；AI 自评 clarify checklist 通过 |
| breakdown → blueprint | 用户明确回复"确认"/"Yes"/"Y"；完整 R-xxx 清单已确认；所有待澄清项已解决 | AI 自评 breakdown checklist 通过 |
| blueprint → implement | 用户明确回复"确认"/"Yes"/"Y"；完整设计方案 + TC 清单已确认 | AI 自评 blueprint checklist 通过 |
| implement → verify | 用户明确回复"确认"/"Yes"/"Y"；完整 T-xxx 已完成 | AI 自评 implement checklist 通过 |
| verify → completed | 自动化验证通过 + 用户明确回复"确认"/"Yes"/"Y"完成人工验收 + 合并验证通过 | 自动化验证通过 + AI 自评 verify checklist 通过 + 合并验证通过 |

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
  "rollback_history": [],
  "autonomous": {
    "enabled": false,
    "status": "idle",
    "started_at": null,
    "started_from": null,
    "resume_phase": null,
    "current_loop": 0,
    "max_loops": 20,
    "timeout_at": null,
    "last_report_at": null,
    "repair_cycles": {},
    "rollback_history": []
  }
}
```

- `phase` 记录当前所处阶段
- `checkpoints` 记录每个阶段的完成状态
- `open_questions` 记录未澄清问题，进入下一阶段前必须清空或得到用户确认
- `rollback_history` 记录回退历史，便于追踪
- `isolation` 记录会话隔离元数据（v3.0 新增），Phase 6 按模式清理时读取
- `autonomous` 记录自循环模式状态（v3.1 新增）
  - `enabled`：是否启用自循环
  - `status`：`idle` / `running` / `paused` / `failed` / `completed`
  - `started_at` / `started_from`：启动时间与起始阶段
  - `resume_phase`：恢复后继续的阶段
  - `current_loop`：总循环计数
  - `max_loops`：最大允许循环次数
  - `timeout_at`：超时时间
  - `last_report_at`：上次报告时间
  - `repair_cycles`：记录 implement-verify 等修复循环次数
  - `rollback_history`：自循环期间的回退历史
- 恢复时读取 `phase`，跳转到对应阶段入口

> `mode` 是路由 key，决定初始化、CWD 守卫和 Phase 6 收尾行为。旧 state.json 无 `mode` 字段时默认视为 `worktree`。

---

## 错误处理

| 场景 | 处理 |
|------|------|
| 阶段执行报错 | 显示错误详情，不跳过阶段，询问是否重试。自循环模式下重试并计数，达到限制则熔断。 |
| 状态文件损坏 | 提示用户，从 clarify 重新开始或手动指定阶段 |
| git 仓库不干净 | 提示用户先清理工作区再开始 |
| 前置文档无法指导当前工作 | 主动提出回退到上游阶段重新确认。自循环模式下自动回退并记录原因。 |
| 实现中发现需求不可行 | 主动提出回退到 clarify/breakdown 重新确认。自循环模式下自动回退。 |
| 用户未明确确认 | **不推进到下一阶段**，保持当前阶段等待确认或修改（人工模式） |
| 自循环达到 max_loops | 暂停自循环，输出熔断报告，等待用户决策 |
| 自循环超时 | 暂停自循环，输出超时报告，等待用户决策 |
| 自循环遇到无法自愈阻塞 | 暂停并报告用户，等待决策 |
| 目标分支无 master/main | 报错并停止，提示用户创建目标分支 |
| feature branch 或开发环境副本已存在 | 报错并提示用户更换 feature 名称 |
| 合并验证发现冲突 | 停止流程，提示人工解决，不允许自动覆盖 |
| 本地与远端分叉（--ff-only 失败） | worktree/feat 模式：**硬停止**，提示用户手动检查。main 模式（v3.3+）：自动进入 6.5.3 rebase 流程。旧 main 会话（无 `commits.base_commit`）：**硬停止**并提示重新初始化。 |
| main 模式 rebase 冲突（6.5.3） | 列出冲突文件，提示用户手动解决。不允许 `git rebase --abort`。解决后回复确认继续。 |
| main 模式并发推送重试耗尽 | **硬停止**。报告检测到远端频繁更新（>3 次重试失败），请稍后手动完成 Phase 6.5。 |
| 推送前安全预检失败 | **硬停止**，本地不是远端的 fast-forward 后代，禁止推送 |
| git push 被远端拒绝 | **硬停止**，worktree 模式从 6.3.3.1 重新执行；feat 模式从 6.4 第 1 步重新执行；main 模式从 6.5.1 重新执行（含 3 次重试） |
| 远端验证不一致 | 提示用户检查 `git log origin/<target-branch>` |
| git push --force | **绝对禁止。** 任何情况下不允许使用 |
| worktree 清理失败 | 给出明确提示，由用户手动处理 |

### 旧会话兼容

- 现有 v3.0 `state.json` 若缺少 `isolation.mode` 字段，恢复时默认视为 `worktree`
- v2.4 全量副本会话（`isolation.type == "fullcopy"`）仍按原有 v2.4 兼容逻辑处理，不受本模式选择影响

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

---

## 参考

- 各阶段内部模板位于 `internal/skills/*/references/` 目录
- 原 6 个 skill 文件保留在 `internal/skills/` 目录中供参考，但不再作为独立命令暴露；唯一入口为 `/devflow`
- Git 文档：`git help`

---

*DevFlow v3.6 — 单一入口，多模式会话隔离（worktree / feat / main），main 分支协调式并行（Phase 1-4 独立并行 / Phase 5-6 全局串行排队 / git+verify+push lock），策略菜单补充运行时，合并验证，闭环管理。*
