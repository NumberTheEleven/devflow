---
name: breakdown
description: 将明确的需求拆分为带编号的、可追踪的 checklist。每条需求分配 ID（R-001、R-002...）、优先级、依赖关系和验收标准。输出持久化到 devflow/requirements.md。
argument-hint: [需求描述]
allowed-tools: [Read, Write, Glob, Bash, TaskCreate]
---

# /devflow:breakdown — 需求拆分（Requirements Breakdown）

## 何时使用

你已拥有明确的需求 —— 无论是来自 `/devflow:clarify` 的输出，还是你已经有一份定义良好的 PRD 或需求文档。如果你已经清楚自己想要什么，也可以直接从此命令开始。

## 流程

### 步骤 1：加载现有状态

检查 `devflow/requirements.md` 是否存在。如果存在，先读取它 —— 我们可能正在更新已有的拆分结果。

### 步骤 2：分解需求

将需求拆分为离散的、可验证的子需求：

- 每个子需求 = 一个带编号的条目（R-001、R-002、...）
- 每条都有清晰的标题和一句话描述
- 分配优先级：**P0**（必须有）、**P1**（应该有）、**P2**（最好有）
- 标记依赖关系：哪些其他需求必须先完成
- 每条都必须有可衡量的验收标准（checkbox 格式）

**生产级需求：** 默认情况下，需包含防止“演示级缺口”的需求。除非用户明确说明不需要，否则请添加：
- 所有外部依赖（API 调用、文件 I/O、用户输入）的错误处理
- 完整的 UI 状态覆盖：loading、empty、error、success 及边界情况
- 输入验证与清理（sanitization）
- 关键操作的基础日志记录
- 如果核心功能是 P0，这些可以是 P1/P2，但**必须**出现在 checklist 中，而不是被静默省略

### 步骤 3：展示并确认

向用户展示完整的编号列表：

```
## 需求清单

R-001 | P0 | [标题] | depends: none
  描述：...
  验收：- [ ] 标准 1
          - [ ] 标准 2

R-002 | P1 | [标题] | depends: R-001
  ...
```

请用户确认该拆分、调整优先级，或增删条目。

### 步骤 4：持久化到文件

写入 `devflow/requirements.md`：

- 如果 `devflow/` 目录不存在，则创建它
- 使用 `skills/breakdown/references/requirements-template.md` 中的模板
- 填入实际的需求数据
- 将所有状态设置为 `pending`

该文件**必须**严格遵循模板格式 —— 下游 skill（`/devflow:blueprint`、`/devflow:verify`）会读取它。

### 步骤 5：确认持久化结果

读回 `devflow/requirements.md` 以确认写入正确。向用户展示摘要：

> “需求 checklist 已保存到 `devflow/requirements.md`，共 N 条（R-001 到 R-xxx）。”

## 交接

询问用户：

> “需求已锁定。下一步：执行 `/devflow:blueprint` 创建解决方案设计、业务流程图和测试用例。或者你需要先调整什么？”

## 智能回滚意识

如果用户说类似“需求 X 错了”或“我们需要修改 R-003”：
- 更新 `devflow/requirements.md`
- 如果下游文件已存在（`design.md`、`tasks.md`、`test-cases.md`），标记这些文件中受影响的条目可能需要重新验证
- **不要**自动修改下游文件 —— 让用户重新执行相关命令
