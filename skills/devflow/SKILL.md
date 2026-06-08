---
name: devflow
description: DevFlow v2.0 — AI 开发规范流程，单一入口，自动 worktree 隔离，按阶段推进完整开发流程
argument-hint: [模糊需求描述]
allowed-tools: [Read, Write, Glob, Grep, Bash, Edit, Agent, TaskCreate, WebSearch, WebFetch, EnterWorktree, ExitWorktree, LSP, Skill]
---

# /devflow — DevFlow v2.0

## 流程总览

```
用户输入: /devflow 模糊需求
    ↓
Phase 1: 需求澄清 (clarify) — 在主仓库，纯对话，不产生文件
    ↓
提炼 feature 名称，创建 git worktree 隔离环境
    ↓
Phase 2: 需求拆解 (breakdown) → R-xxx 清单
    ↓ checkpoint
Phase 3: 方案蓝图 (blueprint) → 流程图 + 设计规格 + TC-xxx
    ↓ checkpoint
Phase 4: 编码实现 (implement) → T-xxx 任务 + 架构图 + 代码
    ↓ checkpoint
Phase 5: 测试验证 (verify) → 逐项核对 TC + 智能回退
    ↓
全部通过 → 自动合并 + 清理 worktree
```

**核心原则：**
- 唯一入口：`/devflow`，没有子命令
- clarify 在主仓库执行，不产生任何文件写入
- clarify 确认后才创建 worktree，后续所有文件改动在隔离环境中
- 每阶段自动推进，checkpoint 提供"继续"和"跳转"两个选项
- 流程全部通过后自动清理：合并到主分支 + 删除 worktree

---

## Step 0: 入口检测

收到 `/devflow` 请求后，首先判断当前环境：

### 0.1 检测是否已在 worktree 中

```bash
GIT_DIR=$(cd "$(git rev-parse --git-dir)" 2>/dev/null && pwd -P)
GIT_COMMON=$(cd "$(git rev-parse --git-common-dir)" 2>/dev/null && pwd -P)
```

**如果 `GIT_DIR != GIT_COMMON`（且不是 submodule）：** 已在 worktree 中。
- 检查 `devflow/` 目录是否存在状态文件
- 如果有状态记录，输出："检测到已有 DevFlow 会话在 `<feature-name>` worktree 中，当前阶段：`<phase>`，从该阶段恢复。"
- 直接跳转到对应阶段继续执行
- 如果没有状态记录，从 clarify 开始（可能是旧版本遗留的 worktree）

**如果 `GIT_DIR == GIT_COMMON`：** 在主仓库中。
- 如果没有传入需求描述，询问用户要做什么
- 如果传入了需求描述，进入 Phase 1（需求澄清）

**如果是 submodule：** 当作主仓库处理，进入 Phase 1。

### 0.2 管理命令识别

如果用户输入的是管理命令而非需求描述，走对应分支：

- `/devflow list` → Step 0.M: 列出所有未完成 worktree
- `/devflow cleanup` → Step 0.M: 手动清理 worktree

---

## Step 0.M: Worktree 管理命令

### /devflow list — 列出所有未完成 worktree

通过 `git worktree list` 获取所有 worktree，排除主仓库，对每个 worktree 尝试读取其 `devflow/` 状态文件，输出：

```
DevFlow Worktree 列表：

| Feature 名称 | 当前阶段 | 创建时间 | 路径 |
|-------------|---------|---------|------|
| user-auth   | breakdown | 2026-06-08 14:30 | .worktrees/user-auth |
| payment     | blueprint | 2026-06-09 10:00 | .worktrees/payment |
| (无状态)     | 未知     | 2026-06-07 09:00 | .worktrees/old-stuff |

共 3 个 worktree，其中 2 个有 DevFlow 状态。
```

对于没有状态文件的 worktree，标注"未知"（可能是旧版本遗留或手动创建的）。

### /devflow cleanup — 清理未完成 worktree

1. 先运行 list 逻辑，展示所有 worktree
2. 询问用户选择要清理的 worktree（可按编号或名称选择）
3. 选择后显示详情（feature 名称、阶段、创建时间、分支名、最后提交信息）
4. 提供清理选项：
   - **仅删除 worktree 目录**（保留分支）
   - **删除 worktree + 分支**（彻底清理）
   - **先合并再清理**（保留代码变更到主分支）
   - **取消**
5. 确认后执行。使用 `git worktree remove <path>` 删除 worktree，按选项处理分支。

---

## Phase 1: 需求澄清

**位置：** 主仓库（未创建 worktree）
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

### 1.2 Checkpoint

需求澄清完成后，展示 checkpoint：

> "需求澄清完成。是否继续进入需求拆解？[Y] 继续 / [跳转到 X 阶段]"

- **Y（默认）：** 进入 Phase 1.3（提炼 feature 名称 + 创建 worktree）
- **跳转到 方案蓝图 / 编码实现 / 测试验证：** 跳过中间阶段

如果用户不回复，自然暂停。下次 `/devflow` 时通过 Step 0 检测恢复。

### 1.3 提炼 Feature 名称

从确认的需求中提炼一个简短的 feature 名称：
- 使用英文小写 + 连字符（如 `user-auth`、`payment-flow`、`fix-login-timeout`）
- 4 个词以内，描述性强
- 向用户确认："基于需求，feature 名称建议为 `xxx`，可以吗？"

### 1.4 创建 Worktree

Feature 名称确认后，创建隔离环境：

```
使用 EnterWorktree 工具，name 参数为提炼的 feature 名称
```

- 遵循 using-git-worktrees skill 的实践：原生工具优先
- 如果 `EnterWorktree` 不可用或失败，降级为在主目录继续流程，并明确提示用户
- 创建成功后，在 worktree 中创建 `devflow/` 目录
- 写入初始状态文件 `devflow/state.json`：
  ```json
  {
    "feature": "<feature-name>",
    "phase": "breakdown",
    "created_at": "<ISO timestamp>",
    "requirements_confirmed": true
  }
  ```

### 1.5 进入下一阶段

Worktree 就绪后，输出：

> "Worktree 就绪：`<path>`。开始需求拆解..."

自动进入 Phase 2。

---

## Phase 2: 需求拆解

**位置：** worktree 中
**参考：** 原 breakdown skill 核心逻辑

### 2.1 流程

1. 将确认的需求拆解为离散的、可验证的子需求
2. 每个子需求编号 R-001, R-002, ...
3. 分配优先级（P0/P1/P2），标注依赖关系
4. 每个子需求附带可衡量的验收标准（checkbox 格式）
5. 展示完整清单，请用户确认
6. 确认后写入 `devflow/requirements.md`（使用 `skills/breakdown/references/requirements-template.md` 格式）

### 2.2 Checkpoint

> "需求拆解完成。共 N 项需求（R-001 ~ R-xxx），已保存到 devflow/requirements.md。继续进入方案蓝图？[Y] 继续 / [跳转到 X 阶段]"

- **Y（默认）：** 进入 Phase 3
- **跳转：** 跳到后续阶段
- **不回复：** 自然暂停。更新 `devflow/state.json` 的 `phase` 为 `"blueprint"`（表示下一步是 blueprint）。

---

## Phase 3: 方案蓝图

**位置：** worktree 中
**参考：** 原 blueprint skill 核心逻辑

### 3.1 流程

1. **业务流程图：** 用 Mermaid 绘制用户视角的流程，确认是否符合预期
2. **规格边界：** 明确范围内/范围外、技术标准、设计决策、风险缓解
3. **测试用例：** 为每个 R-xxx 编写 TC-xxx，含步骤和预期结果
4. 写入 `devflow/design.md` 和 `devflow/test-cases.md`

### 3.2 Checkpoint

> "方案蓝图完成。design.md + test-cases.md 已保存（TC-001 ~ TC-xxx）。继续进入编码实现？[Y] 继续 / [跳转到 X 阶段]"

---

## Phase 4: 编码实现

**位置：** worktree 中
**参考：** 原 implement skill 核心逻辑

### 4.1 流程

1. **任务拆解：** 拆解为 T-001, T-002, ...，标注依赖、复杂度、涉及文件
2. **技术架构图：** Mermaid 格式（数据流/泳道/状态机/ER/时序图，选合适的）
3. **执行任务：**
   - 无依赖任务并行 dispatch sub-agent
   - 有依赖任务按序执行
   - 每个 sub-agent: TDD 循环 → code review → commit
4. **进度追踪：** 更新 `devflow/tasks.md` 中各 T-xxx 的状态

### 4.2 Checkpoint

> "编码实现完成。所有 T-xxx 任务已完成。继续进入测试验证？[Y] 继续 / [跳转到 X 阶段]"

---

## Phase 5: 测试验证

**位置：** worktree 中
**参考：** 原 verify skill 核心逻辑

### 5.1 流程

1. 加载所有跟踪文件（requirements.md, design.md, tasks.md, test-cases.md）
2. 逐条验证 TC-xxx（自动化测试运行 + 手工测试核对）
3. 逐条验证 R-xxx 是否满足验收标准
4. 发现问题时：
   - 实现 bug → 建议重新执行对应 T-xxx
   - 设计问题 → 建议回退到 Phase 3
   - 需求问题 → 建议回退到 Phase 1/2
5. 生成验证报告（通过率、失败项、建议）

### 5.2 验证结果

**全部通过：**

> "所有测试用例通过，所有需求验证完毕。DevFlow 流程完成。"

进入 Phase 6（流程完成）。

**有失败项：**

> "验证未完全通过。X 项失败，Y 项待确认。建议回退到 [具体阶段] 修复。"

不进入清理。更新 `devflow/state.json` 记录待修复项。

---

## Phase 6: 流程完成与清理

### 6.1 确认

> "DevFlow 流程全部完成。是否清理 worktree 并合并到主分支？[Y] 确认清理 / [保留 worktree]"

### 6.2 自动清理

确认后，执行：

1. 确保所有更改已提交
2. 使用 `ExitWorktree` 工具，action 为 `"remove"`
3. 如果 `ExitWorktree` 不可用，手动执行：
   - 合并 feature 分支到主分支
   - `git worktree remove <path>`
   - 删除 feature 分支（已合并）
4. 输出："Worktree 已清理，分支已合并。DevFlow v2.0 闭环完成。"

### 6.3 保留

如果用户选择保留 worktree，状态文件标记 `phase: "completed"`，用户后续可手动清理。

---

## Checkpoint 机制总结

每个阶段结束时统一格式：

> "✅ [阶段名] 完成。继续？[Y] 继续 / [跳转到 X 阶段]"

| 用户输入 | 行为 |
|---------|------|
| Y / 回车 / 继续 / 好的 | 进入下一阶段 |
| 跳转到 实现 / 跳到 implement | 跳过中间阶段，进入指定阶段 |
| 跳转到 验证 | 跳到 verify |
| 暂停 / 稍后 / 不回复 | 更新状态文件，自然暂停 |

**无显式"暂停"选项。** 用户不回复就是暂停。下次 `/devflow` 时自动恢复。

---

## 状态持久化格式

`devflow/state.json`：

```json
{
  "feature": "user-auth",
  "phase": "implement",
  "created_at": "2026-06-09T14:30:00+08:00",
  "version": "2.0",
  "checkpoints": {
    "clarify": "done",
    "breakdown": "done",
    "blueprint": "done",
    "implement": "in_progress",
    "verify": "pending"
  }
}
```

- `phase` 记录当前所处阶段
- `checkpoints` 记录每个阶段的完成状态
- 恢复时读取 `phase`，跳转到对应阶段入口

---

## 错误处理与降级

| 场景 | 处理 |
|------|------|
| EnterWorktree 不可用 | 提示用户，在主目录继续流程 |
| Worktree 创建失败 | 显示错误，询问是否在主目录继续 |
| 阶段执行报错 | 显示错误详情，不跳过阶段，询问是否重试 |
| 状态文件损坏 | 提示用户，从 clarify 重新开始或手动指定阶段 |
| git 仓库不干净 | 提示用户先清理工作区再开始 |

---

## 参考

- using-git-worktrees skill：worktree 创建/检测最佳实践
- 各阶段内部模板位于 `skills/*/references/` 目录
- 原 6 个 skill 文件保留在 `skills/` 目录中供高级用户参考，但不再作为独立命令暴露

---

*DevFlow v2.0 — 单一入口，自动隔离，闭环管理。*
