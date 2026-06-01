# DevFlow — AI 开发规范流程插件 设计规格

## Overview

DevFlow 是一个 Claude Code 插件（Skills + Commands），为 AI 辅助开发提供结构化的全流程规范。覆盖从项目探索到测试验证的完整生命周期，核心差异化：三态需求入口、全链路编号追踪、智能回退+增量重做。

**发布目标：** Claude Code Marketplace + Eleven Marketplace

---

## 命令体系（6 个命令，4 大阶段）

### Phase 1: Requirements 需求管理

| 命令 | 触发场景 | 内部流程 | 输出 |
|------|---------|---------|------|
| `/devflow:discover` | 用户无明确需求 | ① 扫描项目结构与代码 ② 识别可优化点（性能/架构/可维护性/功能缺口） ③ 生成优先级建议列表 | 优化机会列表 → 可触发 clarify |
| `/devflow:clarify` | 用户有模糊想法 / 从 discover 选中优化点 | ① 逐轮对话展开需求（目的/约束/成功标准） ② 提出 2-3 方案对比（trade-off + 推荐） ③ 收敛为清晰需求描述 | 清晰需求描述 → 可触发 breakdown |
| `/devflow:breakdown` | 用户有清晰需求（可直接进入） | ① 拆解为编号子需求（R-001, R-002...） ② 标注优先级 P0/P1/P2 和依赖关系 ③ 用户确认清单 | 📄 `requirements.md` 落盘 |

### Phase 2: Design 方案设计

| 命令 | 依赖 | 内部流程 | 输出 |
|------|------|---------|------|
| `/devflow:blueprint` | 需求清单（可直接进入） | ① **业务流程图** — 非技术人员可读，先确认用户世界的流程 ② **规格边界与规范标准** — 基于流程图定义实现范围、Non-Goals ③ **测试用例清单** — TC-001, TC-002... 带编号追踪 | 📄 `design.md` + 📄 `test-cases.md` 落盘 |

**设计依据：** 业务流程图先于规格边界（参考 Google PRD-before-Design 标准 + ByteDance 方案设计含流程图实践）。流程图是需求与方案的接口级产物，先确认再定范围，避免返工。

### Phase 3: Implementation 编码实现

| 命令 | 依赖 | 内部流程 | 输出 |
|------|------|---------|------|
| `/devflow:implement` | 蓝图就绪（可直接进入） | ① **任务拆解** — T-001, T-002... 标注影响模块/文件、依赖关系、预估复杂度 ② **技术架构文档** — 选择合适图表（UML/泳道图/状态机图） ③ **编码执行** — 无依赖任务 → 并行 Sub-agent + TDD；有依赖任务 → 顺序执行 | 📄 `tasks.md` 落盘 + 代码提交 |

### Phase 4: Verification 测试验证

| 命令 | 依赖 | 内部流程 | 输出 |
|------|------|---------|------|
| `/devflow:verify` | 编码完成（可直接进入） | ① 逐项验证 TC-xxx 测试用例 ② 逐项核对 R-xxx 需求清单 ③ 失败项 → 智能定位归属阶段 → 自动回退 ④ 全绿 → 验证报告 + 闭环 | 验证报告 / 回退到对应阶段 |

---

## 关键机制

### 灵活入口
用户可从任意阶段跳入。例如：已有 PRD → 直接 `/devflow:breakdown`；已有设计文档 → 直接 `/devflow:implement`。

### 智能回退
用户在任何阶段提出问题时，AI 自动识别反馈归属的阶段并回退：
- "需求不对" → 回退到 clarify/breakdown
- "设计有问题" → 回退到 blueprint
- "实现逻辑有缺陷" → 回退到 implement
- 不需要用户手动指定回退到哪个阶段

### 增量重做
回退后只重做受影响的链条。已验证通过的功能点、测试用例不重复执行。

### 阶段收尾询问
每个阶段完成时，AI 主动询问：
1. 进入下一阶段 → 触发对应命令
2. 对当前阶段有疑问 → 用户描述问题，AI 自动定位回退
3. 暂不需要继续

---

## 落盘文件结构

```
devflow/
├── requirements.md    # R-001 ~ R-xxx 需求清单 + 优先级 + 状态
├── design.md          # 设计规格 + 业务流程图
├── tasks.md           # T-001 ~ T-xxx 任务拆解 + 影响范围 + 状态
└── test-cases.md      # TC-001 ~ TC-xxx 测试用例 + 状态
```

**状态持久化策略：** 混合模式 — 核心清单（需求/设计/任务/测试）落盘为结构化 markdown 文件，跨会话可恢复；执行细节靠会话上下文传递。

---

## 技术实现

| 维度 | 方案 |
|------|------|
| 插件类型 | Claude Code Plugin（Skills + Commands） |
| 命令格式 | `/devflow:<command>` |
| 文件格式 | 每个命令 = 一个 Skill Markdown 文件 |
| 发布目标 | Claude Code Marketplace + Eleven Marketplace |
| 依赖 | 零外部依赖（纯 Markdown 指令） |
| 兼容性 | Claude Code（主力），可扩展到其他支持 Skill 的 harness |

---

## 与行业实践的对齐

DevFlow 对齐了以下行业共识：
- **PRD before Design**（Google 标准）— 业务流程图先于规格边界
- **方案对比+推荐**（Google Design Doc Alternatives 章节）
- **Non-Goals 边界**（Google Design Doc 标准）
- **设计含流程图+伪代码**（ByteDance 方案设计四部曲）
- **Sub-agent 嵌套执行**（Alibaba R2C Agent 模式）
- **TDD + 代码审查**（Superpowers 铁律 + 字节跳动质量门禁）
- **编号化任务追踪**（Windsurf 80%规划20%执行理念）

DevFlow 独有的差异化：
- 三态需求入口（无想法→模糊→清晰）覆盖从零到一完整光谱
- 全链路编号追踪（R-xxx → T-xxx → TC-xxx）
- 智能回退 + 增量重做（业界唯一）

---

## 调研参考

- Google: Design Docs at Google
- ByteDance: 一站式研发平台 Bits + DevMind 度量体系
- Alibaba: R2C (Requirement to Code) Agent + 100+ AI 编码规则
- Microsoft: Agentic DevOps 6-phase lifecycle
- Meta: Vibe Coding + dual repo (prototypes/product)
- Superpowers: brainstorm → write-plan → subagent-driven-dev
- OpenSpec: propose → apply → archive + delta specs
- GitHub Spec Kit: specify → plan → tasks → implement
- AWS Kiro: Spec-Driven / Vibe / Design-First 三模式
- BMAD-METHOD: 12+ role-specific agents + three-track system
- Gangsta Agents: 6-stage hierarchical pipeline + adversarial debate
- Cursor: RIPER-5 protocol + .cursor/rules MDC
- Windsurf: PRD → app_flow → db_schema → tech_stack → implementation_plan
- Aider: Repo Map + Architect/Editor two-pass + auto-commit
- Cline/Roo Code: multi-mode system + Memory Bank + MCP
