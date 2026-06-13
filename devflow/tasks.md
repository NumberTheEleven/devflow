# 任务拆解

> 生成时间: 2026-06-13
> 来源: /devflow — 编码实现阶段
> 基于: devflow/design.md, devflow/requirements.md

## T-001: 翻译 clarify Skill

**状态:** 已完成
**覆盖:** R-002（翻译 clarify Skill）
**依赖:** 无
**复杂度:** 低
**涉及文件:**
- `skills/clarify/_SKILL.md` — 全文中文化

**描述:** 将 clarify Skill 的说明文字、章节标题、流程描述、示例输出翻译成中文。保留 frontmatter 字段名、工具名、代码片段、文件路径为英文。

---

## T-002: 翻译 breakdown Skill

**状态:** 已完成
**覆盖:** R-003（翻译 breakdown Skill）
**依赖:** 无
**复杂度:** 低
**涉及文件:**
- `skills/breakdown/_SKILL.md` — 全文中文化

**描述:** 将 breakdown Skill 的说明文字、章节标题、流程描述、输出模板示例翻译成中文。保留工具名、代码片段、文件路径为英文。

---

## T-003: 翻译 blueprint Skill

**状态:** 已完成
**覆盖:** R-004（翻译 blueprint Skill）
**依赖:** 无
**复杂度:** 低
**涉及文件:**
- `skills/blueprint/_SKILL.md` — 全文中文化

**描述:** 将 blueprint Skill 的说明文字、章节标题、流程描述、Handoff 文案翻译成中文。保留 Mermaid 语法、工具名、文件路径为英文。

---

## T-004: 翻译 discover Skill

**状态:** 已完成
**覆盖:** R-005（翻译 discover Skill）
**依赖:** 无
**复杂度:** 中
**涉及文件:**
- `skills/discover/_SKILL.md` — 全文中文化

**描述:** 将 discover Skill 的说明文字、章节标题、流程描述、优化分类标签翻译成中文。为 Performance / Architecture / Maintainability 等分类提供中文对应。保留工具名、代码片段、文件路径为英文。

---

## T-005: 翻译 implement Skill

**状态:** 已完成
**覆盖:** R-006（翻译 implement Skill）
**依赖:** 无
**复杂度:** 中
**涉及文件:**
- `skills/implement/_SKILL.md` — 全文中文化

**描述:** 将 implement Skill 的说明文字、章节标题、流程描述、Production-Grade Baseline 段落翻译成中文。保留代码片段、工具名、文件路径为英文。

---

## T-006: 翻译 verify Skill

**状态:** 已完成
**覆盖:** R-007（翻译 verify Skill）
**依赖:** 无
**复杂度:** 高
**涉及文件:**
- `skills/verify/_SKILL.md` — 全文中文化

**描述:** 将 verify Skill 的说明文字、章节标题、L1/L2/L3 流程描述、输出报告模板翻译成中文。路由关键词表保持中文。保留 Playwright API、工具名、文件路径为英文。

---

## T-007: 更新 devflow 入口 Skill

**状态:** 已完成
**覆盖:** R-008（更新 devflow 入口 Skill）
**依赖:** 无
**复杂度:** 低
**涉及文件:**
- `skills/devflow/SKILL.md` — 补齐剩余英文段落的中文翻译

**描述:** `skills/devflow/SKILL.md` 主体已是中文，检查并补齐剩余英文说明文字。保留 JSON 示例、文件路径、工具名为英文。

---

## T-008: 统一校对与术语一致性检查

**状态:** 已完成
**覆盖:** R-009（统一校对与术语一致性检查）
**依赖:** T-001, T-002, T-003, T-004, T-005, T-006, T-007
**复杂度:** 中
**涉及文件:**
- `skills/*/_SKILL.md`
- `skills/devflow/SKILL.md`
- `devflow/design.md` — 术语对照表

**描述:** 对照设计文档中的术语对照表，检查所有 Skill 文件的术语翻译一致性、章节风格统一性、输出模板格式统一性。修复不一致之处。已统一 argument-hint 为中文、Handoff 章节为"交接"、智能回滚章节为"智能回滚意识"。

---

## T-009: 验证 Skill 执行不中断

**状态:** 已完成
**覆盖:** R-010（验证 Skill 执行不中断）
**依赖:** T-001, T-002, T-003, T-004, T-005, T-006, T-007
**复杂度:** 低
**涉及文件:**
- `skills/*/_SKILL.md`
- `skills/devflow/SKILL.md`

**描述:** 检查所有 Skill 文件的 frontmatter 格式、`allowed-tools` 列表、代码片段、文件路径是否保持原样。确认 Markdown 结构未因翻译破坏。Python 脚本验证通过。

---

*由 DevFlow 追踪。请勿手动编辑。*
