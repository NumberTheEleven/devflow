---
name: blueprint
description: 根据需求清单创建解决方案蓝图。产出业务流程图（Mermaid）、包含非目标的规格边界，以及编号测试用例清单（TC-001...）。
argument-hint: [设计备注]
allowed-tools: [Read, Write, Glob, Bash, WebSearch, TaskCreate]
---

# /devflow:blueprint — 解决方案蓝图

## 何时使用

需求已锁定在 `devflow/requirements.md`。你需要创建：
1. 业务流程图（非技术人员可读）
2. 规格边界与标准
3. 编号测试用例清单

如果你已有需求和设计思路，也可以直接从这里开始。

## 流程

### 步骤 1：加载需求

读取 `devflow/requirements.md`。如果不存在，请用户先运行 `/devflow:breakdown`，或现在描述需求。

### 步骤 2：业务流程图（优先）

**为什么优先：** 业务流必须在定义规格前得到确认。如果流程不符合用户预期，其他工作都是浪费。

创建一个 Mermaid 流程图来描述业务流程：

- 使用面向用户的语言，而非技术术语
- 展示参与者（actors）、操作、决策和结果
- 保持非技术利益相关者也能理解的层次
- 如果涉及多个参与者/角色，使用泳道（swimlanes）

展示流程图并询问：

> "这个业务流程是否符合你的理解？是否有遗漏或错误的步骤？"

迭代直到用户确认。

### 步骤 3：规格边界与标准（其次）

基于已确认的流程图：

- **In Scope（范围内）：** 本次实现涵盖的内容
- **Out of Scope / Non-Goals（范围外/非目标）：** 明确排除的内容 —— 同等重要
- **Technical Standards（技术标准）：** 编码规范、架构约束、技术选型。包含关于质量期望的明确声明 —— 默认是生产级（production-grade），而非演示级（demo-level）（见下文）。
- **Production-Grade Standards（生产级标准）：** 定义该功能“完成”的标准，超越基本功能。涵盖：错误处理策略、边界情况覆盖、UI 状态完整性（加载/空/错误/成功）、日志方案、安全要求。AI 默认生成演示级代码，除非明确指定 —— 请将其明确化。
- **Design Decisions（设计决策）：** 关键选择及其理由，以及曾考虑的替代方案
- **Risks & Mitigations（风险与缓解）：** 可能出错的地方及应对方式

### 步骤 4：测试用例清单（第三）

针对 `devflow/requirements.md` 中的每条需求，定义测试用例：

- 每个测试用例分配唯一 ID（TC-001、TC-002、...）
- 每个映射回需求 ID（R-xxx）
- 类型：unit（单元）/ integration（集成）/ e2e（端到端）/ manual（手动）
- 清晰的步骤和预期结果
- 用于验证期间跟踪的状态字段

### 步骤 5：持久化两个文件

使用设计模板格式写入 `devflow/design.md`。
使用测试用例模板格式写入 `devflow/test-cases.md`。

验证两个文件是否正确写入。

## 交接

> "蓝图完成。devflow/design.md 和 devflow/test-cases.md 已保存。下一步：运行 /devflow:implement 拆解为开发任务并开始编码。"

## 智能回滚意识

如果用户表示设计或测试用例需要更改：
- 更新相关文件
- 如果设计变更影响下游（任务或代码），标记为需重新验证
- 建议对受影响任务重新运行 `/devflow:implement`
