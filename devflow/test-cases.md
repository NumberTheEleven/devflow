# 测试用例清单

> 生成时间: 2026-06-13
> 来源: /devflow — 方案蓝图阶段
> 关联需求: devflow/requirements.md

## TC-001: 翻译规范文档已制定

**状态:** 待开始
**覆盖:** R-001（制定 Skill 中文化翻译规范）
**类型:** 手工
**步骤:**
1. 打开 `devflow/design.md`
2. 查看"范围与边界"、"技术标准"、"关键术语中英对照表"章节

**预期结果:** 文档明确列出需翻译内容、保留英文内容、术语对照表，且术语对照表中包含 Smoke Scan / Interaction Verification / Production-Grade 等关键术语

---

## TC-002: clarify Skill 自然语言已中文化

**状态:** 待开始
**覆盖:** R-002（翻译 clarify Skill）
**类型:** 手工
**步骤:**
1. 打开 `skills/clarify/_SKILL.md`
2. 检查标题、流程说明、示例输出、对话文案

**预期结果:** 所有说明文字为中文；`name`、`description`、`argument-hint`、`allowed-tools`、代码片段、文件路径保持英文；章节标题语义清晰

---

## TC-003: breakdown Skill 自然语言已中文化

**状态:** 待开始
**覆盖:** R-003（翻译 breakdown Skill）
**类型:** 手工
**步骤:**
1. 打开 `skills/breakdown/_SKILL.md`
2. 检查标题、流程说明、输出模板示例

**预期结果:** 所有说明文字为中文；输出模板示例（Requirements Checklist）使用中文；工具名和文件路径保持英文

---

## TC-004: blueprint Skill 自然语言已中文化

**状态:** 待开始
**覆盖:** R-004（翻译 blueprint Skill）
**类型:** 手工
**步骤:**
1. 打开 `skills/blueprint/_SKILL.md`
2. 检查标题、流程说明、Handoff 文案

**预期结果:** 所有说明文字为中文；Mermaid 语法、工具名、文件路径保持英文

---

## TC-005: discover Skill 自然语言已中文化

**状态:** 待开始
**覆盖:** R-005（翻译 discover Skill）
**类型:** 手工
**步骤:**
1. 打开 `skills/discover/_SKILL.md`
2. 检查标题、流程说明、优化分类标签

**预期结果:** 所有说明文字为中文；优化分类标签提供中文对应；工具名、文件路径保持英文

---

## TC-006: implement Skill 自然语言已中文化

**状态:** 待开始
**覆盖:** R-006（翻译 implement Skill）
**类型:** 手工
**步骤:**
1. 打开 `skills/implement/_SKILL.md`
2. 检查标题、流程说明、Production-Grade Baseline 段落

**预期结果:** 所有说明文字为中文；Production-Grade Baseline 等关键概念有清晰中文表达；代码片段、工具名、文件路径保持英文

---

## TC-007: verify Skill 自然语言已中文化

**状态:** 待开始
**覆盖:** R-007（翻译 verify Skill）
**类型:** 手工
**步骤:**
1. 打开 `skills/verify/_SKILL.md`
2. 检查标题、L1/L2/L3 流程说明、输出报告模板

**预期结果:** 所有说明文字为中文；路由关键词表保持中文；Playwright API、工具名、文件路径保持英文；输出报告模板使用中文

---

## TC-008: devflow 入口 Skill 自然语言已中文化

**状态:** 待开始
**覆盖:** R-008（更新 devflow 入口 Skill）
**类型:** 手工
**步骤:**
1. 打开 `skills/devflow/SKILL.md`
2. 检查是否仍有英文段落未翻译

**预期结果:** 文件内所有自然语言描述为中文；JSON 示例、文件路径、工具名保持英文

---

## TC-009: 术语一致性检查通过

**状态:** 待开始
**覆盖:** R-009（统一校对与术语一致性检查）
**类型:** 手工
**步骤:**
1. 打开所有已翻译的 Skill 文件
2. 对照 `devflow/design.md` 中的术语对照表
3. 检查同一英文术语是否使用统一中文翻译

**预期结果:** Smoke Scan、Interaction Verification、Production-Grade、Acceptance Criteria、Evidence Coverage 等关键术语在各 Skill 中翻译一致；无明显语义偏差

---

## TC-010: Skill frontmatter 和工具名未被破坏

**状态:** 待开始
**覆盖:** R-010（验证 Skill 执行不中断）
**类型:** 集成
**步骤:**
1. 打开所有 Skill 文件
2. 检查每个文件顶部的 YAML frontmatter
3. 检查 `allowed-tools` 列表
4. 检查代码片段中的工具名、文件路径、JSON 键名

**预期结果:** 所有 frontmatter 完整且格式正确；`allowed-tools` 中无中文工具名；文件路径和配置键名保持原样；Markdown 标题、列表、代码块、表格结构未破坏

---

*由 DevFlow 追踪。请勿手动编辑。*
