# 任务拆解

> 生成时间: 2026-06-09
> 来源: /devflow:implement
> 基于: devflow/design.md, devflow/requirements.md

## T-001: 创建 `/devflow` 主入口 skill

**状态:** 已完成
**覆盖:** R-001（`/devflow` 单一入口命令）
**依赖:** 无
**复杂度:** 高
**涉及文件:**
- `skills/devflow/SKILL.md` — 新建，主编排逻辑
- `.claude-plugin/plugin.json` — 更新命令注册

**描述:** 创建唯一的 `/devflow` 入口 skill，接受模糊需求描述，负责全流程编排。plugin.json 只暴露这一个命令。

---

## T-002: 重构 clarify 为内部阶段

**状态:** 已完成
**覆盖:** R-001, R-002
**依赖:** T-001
**复杂度:** 中
**涉及文件:**
- `skills/devflow/SKILL.md` — 内嵌 clarify 阶段逻辑

**描述:** 将 clarify 逻辑整合到主入口流程。增加约束：不产生文件写入。阶段结束时提炼 feature 名称，然后创建 worktree。

---

## T-003: 重构 breakdown/blueprint/implement/verify 为内部阶段

**状态:** 已完成
**覆盖:** R-001, R-003
**依赖:** T-001
**复杂度:** 中
**涉及文件:**
- `skills/devflow/SKILL.md` — 内嵌各阶段逻辑

**描述:** 将剩余 4 个阶段作为内部流程节点。核心逻辑保持不变。通过 checkpoint 自动推进。

---

## T-004: Worktree 生命周期集成

**状态:** 已完成
**覆盖:** R-002, R-004
**依赖:** T-002
**复杂度:** 中
**涉及文件:**
- `skills/devflow/SKILL.md` — 内嵌 worktree 管理逻辑

**描述:** 集成 `EnterWorktree` 创建/检测/清理。clarify 确认后创建，verify 通过后自动合并+清理。遵循 using-git-worktrees skill 的检测流程。

---

## T-005: Checkpoint 机制

**状态:** 已完成
**覆盖:** R-003
**依赖:** T-001
**复杂度:** 低
**涉及文件:**
- `skills/devflow/SKILL.md` — checkpoint 逻辑

**描述:** 每阶段结束后提供 checkpoint（Y 继续 / 跳转到指定阶段）。无显式暂停选项，用户不回复即自然暂停。

---

## T-006: Worktree 管理命令（list/cleanup）

**状态:** 已完成
**覆盖:** R-005, R-006
**依赖:** T-004
**复杂度:** 中
**涉及文件:**
- `skills/devflow/SKILL.md` — list/cleanup 子逻辑

**描述:** `/devflow list` 列出所有未完成 worktree；`/devflow cleanup` 手动清理，清理前确认。

---

## T-007: 阶段状态持久化与恢复

**状态:** 已完成
**覆盖:** R-007
**依赖:** T-004, T-005
**复杂度:** 低
**涉及文件:**
- `skills/devflow/SKILL.md` — 状态读写逻辑

**描述:** 在 worktree 的 `devflow/` 目录记录当前阶段。重新进入时检测已有 worktree，自动恢复到暂停阶段。

---

## T-008: 模板中文化

**状态:** 已完成
**覆盖:** R-009
**依赖:** T-003
**复杂度:** 低
**涉及文件:**
- `skills/breakdown/references/requirements-template.md` — 字段中文化
- `skills/blueprint/references/design-template.md` — 字段中文化
- `skills/blueprint/references/test-cases-template.md` — 字段中文化
- `skills/implement/references/tasks-template.md` — 字段中文化
- `skills/devflow/SKILL.md` — 运行时输出中文化

**描述:** 所有模板字段名、状态值、运行时输出统一为中文。文件名保持英文。

---

## T-009: README 与文档更新

**状态:** 已完成
**覆盖:** R-008
**依赖:** T-001
**复杂度:** 低
**涉及文件:**
- `README.md` — 更新为 v2.0 用法

**描述:** 更新 README，说明 `/devflow` 单一入口用法、worktree 自动管理、checkpoint 机制。

---

*由 DevFlow 追踪。请勿手动编辑。*
