# 测试用例清单

> 生成时间: 2026-06-13
> 来源: /devflow — 方案蓝图阶段
> 关联需求: devflow/requirements.md
> Feature: verify-visual-ai-detection

## TC-001: verify Skill 中定义了 AI 视觉审查机制

**状态:** 待开始
**覆盖:** R-001（在 verify Skill 中引入 AI 视觉审查机制）
**类型:** 手工
**步骤:**
1. 打开 `skills/verify/_SKILL.md`
2. 查找“AI 视觉审查”、“视觉审查”、“Visual Review”相关章节
3. 确认其中定义了：触发条件、执行步骤、AI prompt 要求、问题分级方式

**预期结果:** 文档明确说明：仅当 TC 涉及前端/视觉/布局/样式时才启用 AI 视觉审查；AI 能识别重叠、遮挡、溢出、截断、错位、异常空白等常见问题

---

## TC-002: L1 视觉烟雾扫描流程已补充

**状态:** 待开始
**覆盖:** R-002（扩展 L1 烟雾扫描支持视觉烟雾扫描）
**类型:** 手工
**步骤:**
1. 打开 `skills/verify/_SKILL.md` 的 L1 章节
2. 查找“视觉烟雾扫描”或“Visual Smoke Scan”子步骤
3. 确认截图时机、截图范围、AI 分析输入/输出格式

**预期结果:** L1 流程中包含视觉烟雾扫描步骤；明确使用 `browser_take_screenshot`；结果汇入 verification-log.md 的“视觉问题清单”

---

## TC-003: L2 交互截图分析流程已补充

**状态:** 待开始
**覆盖:** R-003（扩展 L2 交互验证支持交互前后截图分析）
**类型:** 手工
**步骤:**
1. 打开 `skills/verify/_SKILL.md` 的 L2 章节
2. 查找“交互截图分析”或“Interaction Screenshot Analysis”子步骤
3. 确认动作前、动作后、异步稳定后三个截图时机

**预期结果:** L2 流程明确：每个关键交互动作前后截图，由 AI 分析视觉变化；异常结果可标记 fail 或降级 L3

---

## TC-004: 程序化布局断言规则已定义

**状态:** 待开始
**覆盖:** R-004（增加程序化布局断言作为 AI 视觉分析的补充）
**类型:** 手工
**步骤:**
1. 打开 `skills/verify/_SKILL.md`
2. 查找“程序化布局断言”或“Programmatic Layout Assertion”相关小节
3. 检查是否定义至少 3 种断言规则

**预期结果:** 文档中定义了可见元素重叠、元素超出可视区域、文字/内容被容器截断等断言；断言失败结果汇入“视觉问题清单”

---

## TC-005: 视觉/前端相关 TC 优先路由到 L1/L2

**状态:** 待开始
**覆盖:** R-005（调整 TC 路由规则）
**类型:** 集成
**步骤:**
1. 打开 `skills/verify/_SKILL.md` 的 TC 路由章节
2. 检查关键词 → 层级映射表
3. 验证“重叠、遮挡、覆盖、溢出、截断、布局、错位、白屏、闪烁”等词映射到 L1 或 L2
4. 验证“美观、流畅、体验、动画、权限、角色”等词仍映射到 L3

**预期结果:** 路由表中视觉/布局类关键词不再默认进入 L3；L3 仅保留主观/权限/动画类 TC

---

## TC-006: verification-log.md 模板包含视觉问题清单

**状态:** 待开始
**覆盖:** R-006（在 verification-log.md 中新增视觉问题清单章节）
**类型:** 手工
**步骤:**
1. 打开 `skills/verify/_SKILL.md` 中的验证报告模板
2. 查找“视觉问题清单”或“Visual Issue Registry”章节
3. 检查每条问题应包含的字段

**预期结果:** 报告模板中包含视觉问题清单；每条问题包含来源 TC/路由、问题描述、截图证据、严重程度、建议修复阶段

---

## TC-007: test-cases template 包含视觉相关 TC 示例

**状态:** 待开始
**覆盖:** R-007（更新 test-cases template 增加视觉 TC 示例）
**类型:** 手工
**步骤:**
1. 打开 `skills/blueprint/references/test-cases-template.md`
2. 查找新增的示例 TC（如页面加载无视觉异常、弹窗完整可见、响应式布局无重叠）
3. 检查示例中的关键词是否能命中更新后的路由规则

**预期结果:** 模板中至少包含 1 个 L1 视觉类 TC 示例和 1 个 L2 交互视觉类 TC 示例

---

## TC-008: verify Skill frontmatter 和 allowed-tools 未被破坏

**状态:** 待开始
**覆盖:** R-008（验证本次改动后 verify skill 文档自洽可用）
**类型:** 集成
**步骤:**
1. 打开 `skills/verify/_SKILL.md`
2. 检查顶部 YAML frontmatter（name、description、argument-hint、allowed-tools）
3. 确认 `allowed-tools` 中已新增 `browser_take_screenshot`
4. 检查 Markdown 标题、列表、表格、代码块结构是否完整

**预期结果:** frontmatter 完整；`allowed-tools` 包含 `browser_take_screenshot` 且所有工具名为英文；Markdown 结构未破坏；自然语言为中文

---

## TC-009: 端到端路由示例正确

**状态:** 待开始
**覆盖:** R-005、R-002、R-003（路由规则 + L1/L2 视觉流程）
**类型:** 端到端
**步骤:**
1. 构造一条示例 TC："点击提交按钮后，确认弹窗完整显示，无被导航栏遮挡"
2. 用更新后的路由规则判断其应进入 L2
3. 确认 L2 流程会执行：动作前截图 → 点击 → 动作后截图 → AI 分析

**预期结果:** 该示例 TC 被路由到 L2；L2 流程文档中包含对应的截图分析步骤

---

*由 DevFlow 追踪。请勿手动编辑。*
