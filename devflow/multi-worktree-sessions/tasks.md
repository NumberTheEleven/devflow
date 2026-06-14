# 任务拆解

> 生成时间: 2026-06-14
> 来源: /devflow — 编码实现阶段
> 基于: devflow/multi-worktree-sessions/design.md, devflow/multi-worktree-sessions/requirements.md

## T-001: 更新 frontmatter 和版本标识

**状态:** 已完成
**覆盖:** R-001, R-006
**依赖:** 无
**复杂度:** 低
**涉及文件:**
- `skills/devflow/SKILL.md` — 更新 name、description、version 为 v2.3

**描述:** 将 skill 版本从 v2.2 升级到 v2.3，描述中体现多 worktree 会话和合并验证。

---

## T-002: 重写 Step 0 入口检测

**状态:** 已完成
**覆盖:** R-001, R-005, R-006
**依赖:** T-001
**复杂度:** 中
**涉及文件:**
- `skills/devflow/SKILL.md` — 重写 Step 0

**描述:** 
- 检测当前是否在 worktree 中
- 主仓库运行 `/devflow` 时视为新会话
- worktree 中运行 `/devflow` 时恢复当前 worktree 的会话
- 移除 `/devflow list` 和 `/devflow cleanup` 管理命令识别

---

## T-003: 重写 Phase 1 会话初始化

**状态:** 已完成
**覆盖:** R-001, R-002, R-003, R-004, R-012
**依赖:** T-002
**复杂度:** 中
**涉及文件:**
- `skills/devflow/SKILL.md` — 重写 Phase 1.3 ~ 1.5

**描述:**
- 确认 feature 名称后，检查 branch 和 worktree 是否已存在
- 自动识别目标分支（master/main）
- 创建 feature branch
- 创建 worktree `.claude/worktrees/devflow-<feature>`
- 在 worktree 中初始化 `devflow/<feature>/state.json`
- 提示用户后续操作在 worktree 中进行

---

## T-004: 重写 Phase 6 合并验证与完成流程

**状态:** 已完成
**覆盖:** R-007, R-008, R-009, R-010, R-011
**依赖:** T-003
**复杂度:** 高
**涉及文件:**
- `skills/devflow/SKILL.md` — 重写 Phase 6

**描述:**
- 识别目标分支
- 计算 merge-base
- 检查目标分支上是否有新 merge commit
- 无新 merge commit → 直接提交
- 有新 merge commit → 列出涉及 feat，验证其 TC
- 执行 `git merge <target-branch>`
- 冲突时停止，提示人工解决
- 冲突解决后重跑当前 feature TC
- 提交到目标分支
- 自动移除 worktree

---

## T-005: 更新状态持久化格式说明

**状态:** 已完成
**覆盖:** R-005
**依赖:** T-002
**复杂度:** 低
**涉及文件:**
- `skills/devflow/SKILL.md` — 更新"状态持久化格式"章节

**描述:** 说明所有 DevFlow 文件位于 `devflow/<feature>/` 目录下，随 feature 分支提交。

---

## T-006: 更新 README.md 版本说明

**状态:** 已完成
**覆盖:** R-001 ~ R-012
**依赖:** T-004
**复杂度:** 低
**涉及文件:**
- `README.md` — 更新版本变更日志

**描述:** 在 README 中新增 v2.3 变更说明：恢复 worktree 隔离、强制合并验证、移除 list/cleanup、devflow/<feature> 结构等。

---

## T-007: 配置 .gitignore

**状态:** 已完成
**覆盖:** R-001
**依赖:** 无
**复杂度:** 低
**涉及文件:**
- `.gitignore` — 添加 `.claude/worktrees/`

**描述:** worktree 目录本身不需要提交到代码库，但 `devflow/<feature>/` 下的文件需要随分支提交。

---

## T-008: 验证 SKILL.md 结构和自洽性

**状态:** 已完成
**覆盖:** R-001 ~ R-012
**依赖:** T-001 ~ T-007
**复杂度:** 中
**涉及文件:**
- `skills/devflow/SKILL.md`

**描述:** 检查 frontmatter、章节结构、Markdown 语法、内部引用一致性，确保 skill 可正常加载。

---

*由 DevFlow 追踪。请勿手动编辑。*
