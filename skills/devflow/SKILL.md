---
name: devflow
description: DevFlow v2.1 — AI 开发规范流程，单一入口，按阶段推进完整开发流程
argument-hint: [模糊需求描述]
allowed-tools: [Read, Write, Glob, Grep, Bash, Edit, Agent, TaskCreate, WebSearch, WebFetch, LSP, Skill]
---

# /devflow — DevFlow v2.1

## 流程总览

```
用户输入: /devflow 模糊需求
    ↓
Phase 1: 需求澄清 (clarify) — 纯对话，不产生文件
    ↓
Phase 2: 需求拆解 (breakdown) → R-xxx 清单
    ↓ checkpoint
Phase 3: 方案蓝图 (blueprint) → 流程图 + 设计规格 + TC-xxx
    ↓ checkpoint
Phase 4: 编码实现 (implement) → T-xxx 任务 + 架构图 + 代码
    ↓ checkpoint
Phase 5: 测试验证 (verify) → L1烟雾 + L2交互 + L3手工，证据驱动 + 智能回退
    ↓
全部通过 → 流程完成
```

**核心原则：**
- 唯一入口：`/devflow`，没有子命令
- clarify 阶段不产生任何文件写入
- clarify 确认后创建 `devflow/` 状态目录，后续文件改动在主仓库中进行
- 每阶段自动推进，checkpoint 提供"继续"和"跳转"两个选项
- 流程全部通过后：确保所有更改已提交，标记完成

---

## Step 0: 入口检测

收到 `/devflow` 请求后，首先判断当前环境：

### 0.1 检测是否有活跃会话

检查项目根目录下 `devflow/state.json` 是否存在：

- **存在且 `phase` 不是 `"completed"`：** 说明有未完成的 DevFlow 会话。
  - 输出："检测到已有 DevFlow 会话（feature: `<feature>`，当前阶段：`<phase>`），从该阶段恢复。"
  - 跳转到对应阶段继续执行

- **不存在或 `phase` 为 `"completed"`：**
  - 如果没有传入需求描述，询问用户要做什么
  - 如果传入了需求描述，进入 Phase 1（需求澄清）

### 0.2 管理命令识别

如果用户输入的是管理命令而非需求描述，走对应分支：

- `/devflow list` → 列出 devflow/ 目录下的历史会话
- `/devflow cleanup` → 清理指定会话的 devflow/ 状态文件

---

## Step 0.M: 会话管理

### /devflow list — 列出所有 DevFlow 会话

读取 `devflow/` 目录下的 `state.json`（如果存在），输出：

```
DevFlow 会话列表：

| Feature 名称 | 当前阶段 | 创建时间 | 状态 |
|-------------|---------|---------|------|
| user-auth   | implement | 2026-06-08 14:30 | 进行中 |
| payment     | completed | 2026-06-09 10:00 | 已完成 |
```

### /devflow cleanup — 清理已完成的会话

1. 先运行 list 逻辑，展示所有会话
2. 询问用户选择要清理的会话（可按编号或名称选择）
3. 确认后删除 `devflow/state.json` 及关联的跟踪文件（requirements.md, design.md, tasks.md, test-cases.md, verification-log.md）
4. 输出清理结果

---

## Phase 1: 需求澄清

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

- **Y（默认）：** 进入 Phase 1.3（提炼 feature 名称 + 初始化会话）
- **跳转到 方案蓝图 / 编码实现 / 测试验证：** 跳过中间阶段

如果用户不回复，自然暂停。下次 `/devflow` 时通过 Step 0 检测恢复。

### 1.3 提炼 Feature 名称

从确认的需求中提炼一个简短的 feature 名称：
- 使用英文小写 + 连字符（如 `user-auth`、`payment-flow`、`fix-login-timeout`）
- 4 个词以内，描述性强
- 向用户确认："基于需求，feature 名称建议为 `xxx`，可以吗？"

### 1.4 初始化会话

Feature 名称确认后，在项目根目录创建 `devflow/` 目录并写入状态文件 `devflow/state.json`：

```json
{
  "feature": "<feature-name>",
  "phase": "breakdown",
  "created_at": "<ISO timestamp>",
  "version": "2.1",
  "requirements_confirmed": true
}
```

### 1.5 进入下一阶段

会话初始化后，输出：

> "会话就绪：`<feature-name>`。开始需求拆解..."

自动进入 Phase 2。

---

## Phase 2: 需求拆解

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
- **不回复：** 自然暂停。更新 `devflow/state.json` 的 `phase` 为 `"blueprint"`。

---

## Phase 3: 方案蓝图

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

**参考：** 原 verify skill 核心逻辑，升级为三层验证架构

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

> "全部验证通过（深度 100%，证据覆盖率 100%）。DevFlow 流程完成。"

进入 Phase 6（流程完成）。

**深度不足但有通过项：**

> "验证深度 [X]%，[N] 条 TC 未执行或无证据。不建议标记为完成。"

不进入完成。更新 `devflow/state.json` 记录待验证项。

**有失败项：**

> "验证未通过。X 项失败，Y 项待确认。建议回退到 [具体阶段] 修复。"

不进入完成。更新 `devflow/state.json` 记录待修复项。

---

## Phase 6: 流程完成

### 6.1 确认

> "DevFlow 流程全部完成。是否结束会话？[Y] 确认完成 / [保留会话]"

### 6.2 预完成提交（兜底保护）

**目的：** 防止存在未提交文件（如下载的数据、临时配置等），会话结束后丢失。

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

   **情况 A — 无任何未提交变更：** 直接进入 6.3 标记完成。

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

### 6.3 标记完成

提交确认完成后，更新 `devflow/state.json`：

```json
{
  "phase": "completed",
  "completed_at": "<ISO timestamp>"
}
```

输出："DevFlow v2.1 流程完成。跟踪文件保存在 devflow/ 目录。"

### 6.4 保留会话

如果用户选择保留会话，状态文件标记 `phase: "completed"`，用户后续可通过 `/devflow cleanup` 手动清理。

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

**无显式"暂停"选项。** 用户不回复就是暂停。下次 `/devflow` 时通过 Step 0 检测恢复。

---

## 状态持久化格式

`devflow/state.json`：

```json
{
  "feature": "user-auth",
  "phase": "implement",
  "created_at": "2026-06-09T14:30:00+08:00",
  "version": "2.1",
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

## 错误处理

| 场景 | 处理 |
|------|------|
| 阶段执行报错 | 显示错误详情，不跳过阶段，询问是否重试 |
| 状态文件损坏 | 提示用户，从 clarify 重新开始或手动指定阶段 |
| git 仓库不干净 | 提示用户先清理工作区再开始 |

---

## 参考

- 各阶段内部模板位于 `skills/*/references/` 目录
- 原 6 个 skill 文件保留在 `skills/` 目录中供高级用户参考，但不再作为独立命令暴露

---

*DevFlow v2.1 — 单一入口，按阶段推进，闭环管理。*
