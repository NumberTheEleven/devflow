# 测试用例清单

> 生成时间: 2026-06-14
> 来源: /devflow — 方案蓝图阶段
> 关联需求: devflow/multi-worktree-sessions/requirements.md
> Feature: multi-worktree-sessions

## TC-001: 主仓库运行 /devflow 自动创建 worktree

**状态:** 待开始
**覆盖:** R-001, R-002, R-004
**类型:** 端到端 / 手工
**步骤:**
1. 确保当前在主仓库，且无进行中的 DevFlow 会话
2. 运行 `/devflow 测试功能`
3. 完成 clarify 并确认 feature 名称为 `test-feature`
4. 检查文件系统

**预期结果:** 主仓库出现 `.claude/worktrees/devflow-test-feature/` 目录；该目录检出 `test-feature` 分支；worktree 内存在 `devflow/test-feature/state.json`。

---

## TC-002: 目标分支 master/main 自动识别

**状态:** 待开始
**覆盖:** R-003
**类型:** 集成 / 手工
**步骤:**
1. 在仅有 `master` 分支的仓库运行 `/devflow`
2. 在仅有 `main` 分支的仓库运行 `/devflow`
3. 在同时有 `master` 和 `main` 的仓库运行 `/devflow`

**预期结果:** 正确识别目标分支；无目标分支时给出明确错误；同时存在时按约定选择。

---

## TC-003: 同名 feature 冲突提示

**状态:** 待开始
**覆盖:** R-012
**类型:** 集成 / 手工
**步骤:**
1. 已存在 `existing-feature` 分支和对应 worktree
2. 在主仓库运行 `/devflow` 并尝试确认 feature 名称为 `existing-feature`

**预期结果:** 流程停止并提示：feature 名称已存在，请更换名称；不覆盖已有分支或 worktree。

---

## TC-004: 无新 merge commit 时跳过合并验证

**状态:** 待开始
**覆盖:** R-007
**类型:** 集成 / 手工
**步骤:**
1. 创建 feature 分支后，目标分支无新 merge commit
2. 推进到 Phase 6

**预期结果:** Phase 6 直接执行提交，不触发合并验证流程。

---

## TC-005: 有新 merge commit 时触发合并验证

**状态:** 待开始
**覆盖:** R-007, R-010
**类型:** 集成 / 手工
**步骤:**
1. 创建 feature 分支后，向目标分支合并一个其他 feature
2. 推进当前 feature 到 Phase 6

**预期结果:** Phase 6 检测到新 merge commit，列出涉及 feat，进入合并验证流程。

---

## TC-006: merge 冲突时流程停止

**状态:** 待开始
**覆盖:** R-008
**类型:** 集成 / 手工
**步骤:**
1. 当前 feature 修改了文件 A
2. 目标分支上的新 merge commit 也修改了文件 A 的同一位置
3. 推进到 Phase 6 并执行 merge

**预期结果:** merge 失败，流程停止，清晰展示冲突文件；不允许自动覆盖；未解决前无法继续。

---

## TC-007: 冲突解决后重跑当前 feature TC

**状态:** 待开始
**覆盖:** R-009
**类型:** 集成 / 手工
**步骤:**
1. 在 TC-006 的基础上人工解决冲突
2. 告知 DevFlow 冲突已解决
3. 继续 Phase 6

**预期结果:** DevFlow 自动重跑当前 feature 的测试用例；全部通过后进入提交；失败则停止。

---

## TC-008: 时间窗口内涉及 feat 验证

**状态:** 待开始
**覆盖:** R-010
**类型:** 集成 / 手工
**步骤:**
1. feature A 开发期间，feature B 和 feature C 合并到目标分支
2. 推进 feature A 到 Phase 6

**预期结果:** DevFlow 识别出 feature B 和 feature C 为涉及 feat；从目标分支读取 `devflow/feature-B/test-cases.md` 和 `devflow/feature-C/test-cases.md` 进行验证；存在但无跟踪文件时给出提示。

---

## TC-009: 会话完成后自动清理 worktree

**状态:** 待开始
**覆盖:** R-011
**类型:** 端到端 / 手工
**步骤:**
1. 推进 feature 到 Phase 6
2. 通过合并验证和人工验收
3. 提交到目标分支

**预期结果:** 提交成功后，自动执行 `git worktree remove .claude/worktrees/devflow-<feature>`；目录被删除。

---

## TC-010: list/cleanup 命令不再被识别

**状态:** 待开始
**覆盖:** R-006
**类型:** 单元 / 手工
**步骤:**
1. 在主仓库运行 `/devflow list`
2. 在主仓库运行 `/devflow cleanup`

**预期结果:** 两个命令均不被识别为管理命令；按普通需求描述处理或给出明确提示。

---

*由 DevFlow 追踪。请勿手动编辑。*
