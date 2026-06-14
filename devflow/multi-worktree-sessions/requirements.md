# 需求清单

> 生成时间: 2026-06-14
> 来源: /devflow — 需求拆解阶段
> Feature: multi-worktree-sessions

## R-001: 强制 worktree 隔离

**优先级:** P0
**状态:** 待开始
**描述:** 从 v2.3 开始，DevFlow 会话必须在独立 git worktree 中运行。用户在主仓库运行 `/devflow` 时，自动创建 worktree 并把会话放进去。
**依赖:** 无
**验收标准:**
- [ ] 主仓库运行 `/devflow` 时，在 clarify 确认 feature 名称后自动创建 worktree
- [ ] 后续所有阶段产生的文件都位于 worktree 内，不污染主仓库
- [ ] skill 流程明确说明"当前在 worktree 中运行"

---

## R-002: worktree 目录命名规范

**优先级:** P0
**状态:** 待开始
**描述:** 统一定义 worktree 目录命名规则为 `.claude/worktrees/devflow-<feature>`。
**依赖:** R-001
**验收标准:**
- [ ] skill 文档中明确定义命名规则
- [ ] 实际创建的 worktree 路径符合规则
- [ ] feature 名称含非法字符时有处理策略

---

## R-003: 目标分支自动识别

**优先级:** P0
**状态:** 待开始
**描述:** 自动检测目标分支为 `master` 或 `main`，暂不支持其他分支。
**依赖:** 无
**验收标准:**
- [ ] 能正确识别 `master` 和 `main`
- [ ] 两者都不存在时给出明确错误提示
- [ ] 同时存在时优先使用 `main`（或按约定）

---

## R-004: feature 分支与 worktree 同名

**优先级:** P0
**状态:** 待开始
**描述:** 每个 DevFlow 会话对应一个与 feature 同名的 git 分支，worktree 也使用该分支。
**依赖:** R-001, R-002
**验收标准:**
- [ ] 自动创建的 feature 分支名称与 feature 名称一致
- [ ] worktree 检出到该分支
- [ ] 同名分支/ worktree 已存在时按 R-012 处理

---

## R-005: 多会话状态文件隔离

**优先级:** P0
**状态:** 待开始
**描述:** 所有 DevFlow 文件（state.json、requirements.md、design.md、tasks.md、test-cases.md、verification-log.md）按 feature 隔离在 `devflow/<feature>/` 子目录下，全部随 feature 分支提交到远端。
**依赖:** R-001
**验收标准:**
- [ ] 每个 feature 有独立的 `devflow/<feature>/` 目录
- [ ] 状态读写逻辑以当前 feature 子目录为基准
- [ ] 主仓库保留已完成的 feature 子目录作为历史记录
- [ ] 合并验证时能从目标分支读取其他 feature 的 test-cases.md 等文件

---

## R-006: 移除 list/cleanup 管理命令

**优先级:** P1
**状态:** 待开始
**描述:** 不再提供 `/devflow list` 和 `/devflow cleanup`，保持 `/devflow` 单一入口。
**依赖:** 无
**验收标准:**
- [ ] skill 文档中删除 list/cleanup 相关描述
- [ ] 入口检测逻辑不再识别 list/cleanup
- [ ] 用户仍可通过文件系统查看/清理 worktree

---

## R-007: Phase 6 合并验证前置检查

**优先级:** P0
**状态:** 待开始
**描述:** 在 Phase 6 完成前，使用 `git merge-base` 获取当前 feature 与目标分支的基准 commit，并检查目标分支自基准 commit 以来是否有新的 merge commit。
**依赖:** R-003
**验收标准:**
- [ ] 能正确计算基准 commit
- [ ] 能识别目标分支上基准 commit 之后的所有 merge commit
- [ ] 无新 merge commit 时允许跳过合并验证
- [ ] 有新 merge commit 时强制进入合并验证流程

---

## R-008: 合并验证执行与冲突检测

**优先级:** P0
**状态:** 待开始
**描述:** 在 worktree 内执行 `git merge <target-branch>`，只允许 merge，不允许 rebase；发现代码冲突时必须停止并提示用户人工解决，不允许自动覆盖。
**依赖:** R-007
**验收标准:**
- [ ] 合并验证只使用 `git merge`，不使用 `rebase`
- [ ] 发现冲突时流程停止并清晰展示冲突文件
- [ ] 未解决冲突前不允许进入后续步骤
- [ ] 解决冲突后需用户确认才能继续

---

## R-009: 冲突解决后当前 feature 重验证

**优先级:** P0
**状态:** 待开始
**描述:** 合并完成后，重新验证当前 feature 的测试用例和验收规格，确保合并后的代码仍然满足需求。
**依赖:** R-008
**验收标准:**
- [ ] 合并后自动触发当前 feature 的 TC 重跑
- [ ] 所有 TC 通过后才允许进入提交/完成
- [ ] 失败时停止并提示修复

---

## R-010: 时间窗口内涉及 feat 验证

**优先级:** P0
**状态:** 待开始
**描述:** 从当前 feature 的基准 commit 到目标分支最新 commit 之间，目标分支上的每个 merge commit 都视为涉及冲突的 feat；在合并前验证这些 feat 的测试用例和验收规格，以捕获语义冲突。
**依赖:** R-007
**验收标准:**
- [ ] 能列出时间窗口内目标分支上的所有 merge commit
- [ ] 能从 merge commit 识别对应 feat（通过 commit message 中的分支名）
- [ ] 对每个涉及 feat 重跑其测试用例和验收规格
- [ ] 涉及 feat 存在但无 DevFlow 跟踪文件时，给出明确提示

---

## R-011: 会话完成后自动清理 worktree

**优先级:** P1
**状态:** 待开始
**描述:** Phase 6 提交完成后，自动移除对应 worktree，释放空间。
**依赖:** R-001
**验收标准:**
- [ ] 提交成功后自动执行 `git worktree remove`
- [ ] 清理前确认无未提交变更
- [ ] 清理失败时给出明确提示

---

## R-012: 同名 feature 冲突处理

**优先级:** P1
**状态:** 待开始
**描述:** 如果已存在同名 worktree 或 feature 分支，报错并提示用户更换 feature 名称。
**依赖:** R-002, R-004
**验收标准:**
- [ ] 创建前检查 branch 和 worktree 是否已存在
- [ ] 存在时给出清晰错误信息
- [ ] 不覆盖、不删除已有 worktree/分支

---

*由 DevFlow 追踪。请勿手动编辑。*
