# 任务拆解

> 生成时间: 2026-06-09
> 来源: /devflow — 编码实现阶段
> 基于: devflow/design.md, devflow/requirements.md

## T-001: 重写 verify skill 头部（描述、When to Use、Step 1 能力检测）

**状态:** 已完成
**覆盖:** R-006（verify skill 文档更新）
**依赖:** 无
**复杂度:** 低
**涉及文件:**
- `skills/verify/_SKILL.md` — 更新 frontmatter description、When to Use、Step 1

**描述:** 将 skill 描述从"two-phase pipeline"更新为"three-layer verification"。Step 1 的能力检测增加 Playwright 降级路径描述。

---

## T-002: 新增 TC 路由引擎（Step 2）

**状态:** 已完成
**覆盖:** R-004（TC 智能路由引擎）、R-006（verify skill 文档更新）
**依赖:** T-001
**复杂度:** 中
**涉及文件:**
- `skills/verify/_SKILL.md` — 新增 Step 2 路由引擎

**描述:** 新增完整的 TC 路由规则：关键词匹配表 → 类型推断 → 路由优先级 → 展示路由计划给用户确认 → 记录路由决策。路由规则从 design.md 引用。

---

## T-003: 重写 L1 烟雾扫描（Step 3-7）

**状态:** 已完成
**覆盖:** R-001（L1 烟雾扫描层）
**依赖:** T-002
**复杂度:** 中
**涉及文件:**
- `skills/verify/_SKILL.md` — 重写 Step 3-7

**描述:** 保留现有 4 类检查逻辑（console / network / health / DOM），调整措辞：通过时标注"L1 烟雾扫描通过"，不再暗示"验证完成"。聚合结果时标注"L1 仅检查基础设施，不代表业务功能验证通过"。

---

## T-004: 新增 L2 交互验证（Step 8-12）

**状态:** 已完成
**覆盖:** R-002（L2 交互验证层）、R-006（verify skill 文档更新）
**依赖:** T-002
**复杂度:** 高
**涉及文件:**
- `skills/verify/_SKILL.md` — 新增 Step 8-12

**描述:** 新增 L2 交互验证的完整流程：
- Step 8: 从路由计划中提取 L2 TC，解析操作步骤
- Step 9: 执行 Playwright 操作（navigate → click → type → wait → snapshot），每步记录 Interaction Trace
- Step 10: DOM 变化判断（语义标签 diff，不依赖文案）
- Step 11: 交互异常处理（超时、副作用检查）
- Step 12: Playwright 不可用时降级为手工引导

---

## T-005: 重写 L3 结构化手工验证（Step 13-15）

**状态:** 已完成
**覆盖:** R-003（L3 结构化手工验证层）
**依赖:** T-002
**复杂度:** 中
**涉及文件:**
- `skills/verify/_SKILL.md` — 重写 Step 13-15

**描述:** 升级旧 Phase 2 为 L3 结构化手工验证：
- Step 13: 证据要求矩阵（每种 TC 类型需要什么证据）
- Step 14: 逐条验证（展示 TC → 请求用户确认 → 收集证据）
- Step 15: 无证据标记规则（无证据 → unverified，跳过需原因）

---

## T-006: 新增深度评分 + 统一报告（Step 16-18）

**状态:** 已完成
**覆盖:** R-005（验证深度评分体系）、R-007（验证报告格式升级）
**依赖:** T-003, T-004, T-005
**复杂度:** 中
**涉及文件:**
- `skills/verify/_SKILL.md` — 新增 Step 16-18

**描述:**
- Step 16: 聚合三层验证结果
- Step 17: 计算深度评分（执行率、证据覆盖率、分层分布）
- Step 18: 生成统一验证报告（单一 verification-log.md 格式模板）

---

## T-007: 重写智能回退 + Handoff（Step 19-20）

**状态:** 已完成
**覆盖:** R-006（verify skill 文档更新）
**依赖:** T-006
**复杂度:** 低
**涉及文件:**
- `skills/verify/_SKILL.md` — 重写 Step 19-20

**描述:** 更新智能回退映射表，增加 L2 交互失败的回退建议。更新 Handoff 部分的"全部通过"条件（必须深度=100% 才算真正全部通过）。

---

## T-008: 更新 Playwright 工具参考表

**状态:** 已完成
**覆盖:** R-006（verify skill 文档更新）
**依赖:** T-004
**复杂度:** 低
**涉及文件:**
- `skills/verify/_SKILL.md` — 更新篇末工具参考表

**描述:** 增加 `browser_click`、`browser_type`、`browser_wait_for` 等 L2 使用的 Playwright 工具引用。

---

## T-009: 更新 devflow 主 skill Phase 5 描述

**状态:** 已完成
**覆盖:** R-006（verify skill 文档更新）
**依赖:** 无
**复杂度:** 低
**涉及文件:**
- `skills/devflow/SKILL.md` — 更新 Phase 5.1 流程描述和 5.2 验证结果

**描述:** 将 Phase 5 描述从"逐条验证 TC + 自动化/手工"更新为"L1 烟雾扫描 + L2 交互验证 + L3 结构化手工验证，证据驱动，智能回退"。

---

*由 DevFlow 追踪。请勿手动编辑。*
