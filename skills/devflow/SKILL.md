---
name: devflow
description: DevFlow v2.4 — AI 开发规范流程，单一入口，按阶段推进完整开发流程。支持完整副本会话隔离与强制合并验证，防止多 feature 并行开发时的冲突与语义回归。
argument-hint: [模糊需求描述]
allowed-tools: [Read, Write, Glob, Grep, Bash, Edit, Agent, TaskCreate, WebSearch, WebFetch, LSP, Skill]
---

# /devflow — DevFlow v2.4

## 流程总览

```
用户输入: /devflow 模糊需求
    ↓
Step 0: 入口检测 → 判断当前是否在开发环境副本 / 是否有活跃会话
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
Phase 6: 流程完成 → 合并验证 + 提交 + 开发环境清理
```

**核心原则：**
- 唯一入口：`/devflow`，没有子命令
- clarify 阶段不产生任何文件写入
- clarify 确认后创建完整仓库副本作为开发环境，所有后续文件改动在该副本中进行
- 每个 feature 的 DevFlow 文件隔离在 `devflow/<feature>/` 目录下，随 feature 分支提交
- **每个阶段结束时必须获得用户显式确认（"确认"/"Yes"/"Y"），才能进入下一阶段**
- **用户未明确确认时，一律视为需要修改；修正后必须重新展示完整结果并再次等待确认**
- checkpoint 只提供"确认"一个明确选项；不确认就是需要修改
- **任何阶段发现前置文档无法指导当前工作，必须主动提出回退到上游阶段重新确认**
- **流程节点回退是正常场景，在遇到阻塞时主动提出，不允许自行假设继续**
- 流程全部通过后：必须经用户人工验收，确认所有更改已提交，再标记完成

---

## Step 0: 入口检测

收到 `/devflow` 请求后，首先判断当前环境：

### 0.1 检测当前是否在开发环境副本中

检查当前目录是否在 `.claude/worktrees/devflow-*` 下，并存在 `devflow/<feature>/state.json`：

- **当前在开发环境副本中：**
  - 说明用户进入了某个 feature 的开发环境继续工作
  - 读取 `devflow/<feature>/state.json` 恢复会话
  - 如果 state 不存在或损坏，提示用户并建议从 clarify 重新开始

- **当前在主仓库（非副本）：**
  - 视为启动新会话
  - 继续 0.2 检查是否有旧版活跃会话

### 0.2 检测是否有活跃会话

检查主仓库根目录下是否存在未完成的旧版 `devflow/state.json`：

- **存在且 `phase` 不是 `"completed"`：** 说明有未完成的旧版 DevFlow 会话。
  - 输出："检测到主仓库存在未完成的旧版 DevFlow 会话（feature: `<feature>`，当前阶段：`<phase>`）。v2.4 起会话需要在开发环境副本中运行，请先完成或手动清理该会话后再开始新会话。"
  - 不创建新开发环境，等待用户处理

- **不存在或 `phase` 为 `"completed"`：**
  - 如果没有传入需求描述，询问用户要做什么
  - 如果传入了需求描述，进入 Phase 1（需求澄清）

### 0.3 管理命令说明

v2.4 起不再提供 `/devflow list` 和 `/devflow cleanup` 管理命令。`/devflow` 保持唯一入口。

- 如需查看会话，直接查看 `devflow/<feature>/` 目录或 `.claude/worktrees/` 目录
- 如需清理开发环境副本，直接删除对应目录即可

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

- **用户回复 "确认" / "Yes" / "Y"：** 进入 Phase 1.3（提炼 feature 名称 + 初始化会话）
- **其他任何回复（包括"需要修改"、指出问题、部分肯定、沉默等）：** 一律视为需要修改。针对用户反馈修正后，**重新输出完整的需求总结**，再次等待确认
- **不回复：** 自然暂停。下次 `/devflow` 时通过 Step 0 检测恢复。

### 1.3 提炼 Feature 名称

从确认的需求中提炼一个简短的 feature 名称：
- 使用英文小写 + 连字符（如 `user-auth`、`payment-flow`、`fix-login-timeout`）
- 4 个词以内，描述性强
- 向用户确认："基于需求，feature 名称建议为 `xxx`，可以吗？"

### 1.4 初始化会话

Feature 名称确认后，执行以下步骤：

1. **自动识别目标分支：** 检查 `master` 和 `main`，按以下优先级：
   - 仅存在 `main` → 使用 `main`
   - 仅存在 `master` → 使用 `master`
   - 同时存在 → 默认使用 `main`
   - 都不存在 → 报错并停止

2. **检查冲突：** 检查是否已存在同名 branch 或开发环境目录：
   ```bash
   git branch --list <feature>
   ls -d .claude/worktrees/devflow-<feature> 2>/dev/null  # Unix
   # 或 Test-Path .claude/worktrees/devflow-<feature>      # Windows
   ```
   - 如果存在，报错："feature 名称 `<feature>` 已存在（branch 或开发环境），请更换名称。"
   - 不存在则继续

3. **创建 feature branch：**
   ```bash
   git checkout -b <feature>
   ```

4. **创建开发环境副本（完整复制）：**

   a. **切回目标分支：**
   ```bash
   git checkout <target-branch>
   ```

   b. **完整复制主仓库到开发环境：**
      ```bash
      rsync -av --exclude='.claude/worktrees' <repo-root>/ .claude/worktrees/devflow-<feature>/
      ```
      将当前仓库的**全部内容**（包括 node_modules、.env、本地数据等 gitignore 文件）
      复制到开发环境目录，确保开发环境与主仓库具有相同的运行时环境。
      
      **排除项：**
      - `.claude/worktrees/` — 避免嵌套复制其他开发环境

      **跨平台策略（AI agent 自动选择可用工具）：**
      - 优先 `rsync -av --exclude='.claude/worktrees' <src>/ <dst>/`
      - Windows 备选 `robocopy <src> <dst> /E /XD .claude`
      - 通用备选：手动逐目录复制（跳过 .claude/worktrees/）

   c. **在副本中切换到 feature 分支：**
      ```bash
      cd .claude/worktrees/devflow-<feature>
      git checkout <feature>
      ```

   > 复制完成后，开发环境即处于**可运行状态**——所有依赖、配置、本地数据
   > 均已在副本中就绪，无需额外初始化即可启动完整服务进行验收。

5. **初始化状态目录和文件：** 在开发环境副本内创建 `devflow/<feature>/` 目录，写入 `state.json`：

   ```json
   {
     "feature": "<feature-name>",
     "phase": "breakdown",
     "created_at": "<ISO timestamp>",
     "version": "2.4",
     "requirements_confirmed": true,
     "open_questions": ["<待澄清项>"],
     "checkpoints": {
       "clarify": "done",
       "breakdown": "in_progress",
       "blueprint": "pending",
       "implement": "pending",
       "verify": "pending"
     }
   }
   ```

6. **提示用户：**
   > "会话 `<feature>` 已在开发环境副本 `.claude/worktrees/devflow-<feature>` 中准备就绪。所有文件（含 node_modules、本地配置等）已完整复制，可立即启动服务。后续所有文件操作将在该副本内进行。"

### 1.5 进入下一阶段

会话初始化后，自动进入 Phase 2（需求拆解）。

---

## Phase 2: 需求拆解

**参考：** 原 breakdown skill 核心逻辑

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

### 6.1 确认

> "DevFlow 流程已通过人工验收。是否结束会话并提交？回复 **确认 / Yes / Y** 完成并提交；否则请说明。"

### 6.2 合并验证

确认完成后，**必须先执行**合并验证：

#### 6.2.1 识别目标分支

自动识别目标分支（`master` 或 `main`），规则同 Phase 1.4。

#### 6.2.2 计算基准 commit

```bash
git merge-base <target-branch> <feature-branch>
```

#### 6.2.3 检查目标分支新变更

列出目标分支自基准 commit 以来的所有 merge commit：

```bash
git log --merges --first-parent <base-commit>..<target-branch>
```

- **无新 merge commit：** 跳过 6.2.4 ~ 6.2.6，直接进入 6.3 预完成提交。
- **有新 merge commit：** 进入 6.2.4 涉及 feat 验证。

#### 6.2.4 涉及 feat 验证

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

#### 6.2.5 执行 merge

在开发环境副本内执行：

```bash
git merge <target-branch>
```

**只允许 merge，不允许 rebase。**

- **无冲突：** 继续 6.2.6
- **有冲突：**
  > "检测到合并冲突，请人工解决以下文件后再继续：
  > - `<conflict-file-1>`
  > - `<conflict-file-2>`
  > 
  > 不允许自动覆盖合并。解决后回复 **确认 / Yes / Y** 继续。"
  
  用户确认解决后，继续 6.2.6。

#### 6.2.6 当前 feature 重验证

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

### 6.4 提交到目标分支

将当前 feature 分支合并（或提交）到目标分支。由于 6.2 已经执行过 merge，此处执行：

```bash
git checkout <target-branch>
git merge <feature-branch>
```

或直接使用：

```bash
git push origin <feature-branch>  # 如果目标分支在远端
```

具体方式根据项目 workflow 选择，但必须在目标分支上生成 merge commit。

### 6.5 自动清理开发环境副本

提交成功后，自动删除开发环境副本：

```bash
rm -rf .claude/worktrees/devflow-<feature>
```

清理前确认副本内无未提交变更。清理失败时给出明确提示。

### 6.6 标记完成

更新 `devflow/<feature>/state.json`：

```json
{
  "phase": "completed",
  "completed_at": "<ISO timestamp>"
}
```

输出："DevFlow v2.4 流程完成。跟踪文件保存在 devflow/<feature>/ 目录。"

### 6.7 保留会话

如果用户选择保留会话，状态文件标记 `phase: "completed"`，开发环境副本可以保留或手动清理。

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
| clarify → breakdown | 用户明确回复"确认"/"Yes"/"Y"；feature 名称确认；开发环境副本创建成功 |
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
  "created_at": "2026-06-09T14:30:00+08:00",
  "version": "2.3",
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
- 恢复时读取 `phase`，跳转到对应阶段入口

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
| 开发环境副本清理失败 | 给出明确提示，由用户手动处理 |

---

## 参考

- 各阶段内部模板位于 `skills/*/references/` 目录
- 原 6 个 skill 文件保留在 `skills/` 目录中供高级用户参考，但不再作为独立命令暴露
- Git 文档：`git help`

---

*DevFlow v2.4 — 单一入口，完整副本隔离，合并验证，闭环管理。*
