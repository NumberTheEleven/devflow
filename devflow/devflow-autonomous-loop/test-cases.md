# 测试用例

> 生成时间: 2026-07-09
> 来源: /devflow — 方案蓝图阶段
> 对应需求: R-001 ~ R-010

## TC-001: 自动确认入口识别

**对应 R-001**
**优先级:** P0
**类型:** L2 交互

### 步骤
1. 用户输入 `/devflow 测试需求`
2. 完成 clarify 并展示 checkpoint
3. 用户在 checkpoint 回复 `auto`

### 预期结果
- AI 输出启动报告，包含"自循环模式"、起始阶段、最大循环、超时时间
- `state.json` 中 `autonomous.enabled` 为 `true`
- `autonomous.started_from` 为 `clarify`

---

## TC-002: 自循环状态持久化

**对应 R-002**
**优先级:** P0
**类型:** L1 结构化检查

### 步骤
1. 启用自循环模式
2. 让 AI 推进至少一个阶段
3. 读取 `state.json`

### 预期结果
- `autonomous` 对象存在且包含：`enabled`、`status`、`started_at`、`started_from`、`resume_phase`、`current_loop`、`max_loops`、`timeout_at`、`last_report_at`
- `current_loop` 已递增
- `rollback_history` 为数组

---

## TC-003: AI 自评估通过并自动推进

**对应 R-003, R-004**
**优先级:** P0
**类型:** L2 交互

### 步骤
1. 从 clarify 启动自循环
2. 观察 AI 在 breakdown 完成后的行为

### 预期结果
- AI 使用 breakdown checklist 自评
- 自评通过后不询问用户，直接进入 blueprint
- `state.json` phase 从 breakdown 变为 blueprint

---

## TC-004: 编码-验证自修复循环

**对应 R-005**
**优先级:** P0
**类型:** L2 交互

### 步骤
1. 进入 implement 并完成编码
2. 进入 verify 并故意制造一个可修复的 bug
3. 观察 AI 行为

### 预期结果
- verify 报告失败后，AI 自动返回 implement
- AI 修复 bug 后再次进入 verify
- `autonomous.repair_cycles["implement-verify"]` 递增
- 修复成功后继续推进

---

## TC-005: 上游阶段自动回退

**对应 R-006**
**优先级:** P0
**类型:** L2 交互

### 步骤
1. 在 verify 中制造一个根因在设计规格的问题
2. 观察 AI 行为

### 预期结果
- AI 判断根因在 blueprint
- 自动回退到 blueprint，更新 design.md / test-cases.md
- `rollback_history` 新增一条记录
- 重新完成 blueprint → implement → verify

---

## TC-006: 最大循环熔断

**对应 R-007**
**优先级:** P0
**类型:** L2 交互

### 步骤
1. 设置 `max_loops=3`
2. 在 verify 中制造连续失败的 bug
3. 观察 AI 行为

### 预期结果
- 循环 3 次后 AI 停止自循环
- 输出熔断报告，包含当前阶段、已尝试次数、阻塞原因
- `autonomous.status` 变为 `failed`

---

## TC-007: 超时熔断

**对应 R-007**
**优先级:** P1
**类型:** L3 手工/模拟

### 步骤
1. 设置极短的 `timeout`（测试中模拟已超时）
2. 触发阶段推进检查

### 预期结果
- AI 检测到 `timeout_at` 已过，停止自循环
- 输出超时报告
- `autonomous.status` 变为 `failed`

---

## TC-008: 关键节点报告但不暂停常规推进

**对应 R-008**
**优先级:** P0
**类型:** L2 交互

### 步骤
1. 启动自循环
2. 观察多个阶段正常完成

### 预期结果
- 阶段正常完成时，AI 不向用户发送请求确认的消息
- 只在完成、熔断、阻塞时发送汇总报告

---

## TC-009: 完成归档与提交

**对应 R-009**
**优先级:** P0
**类型:** L2 交互 + L1 结构化检查

### 步骤
1. 自循环完成 implement 和 verify
2. 进入 Phase 6

### 预期结果
- AI 自动执行 Phase 6：预完成提交 → 合并验证 → commit → push
- `state.json` 更新为 `phase: "completed"`
- `autonomous.status` 为 `completed`
- git log 显示提交和 push

---

## TC-010: 安全约束不变（禁止 force push）

**对应 R-010**
**优先级:** P0
**类型:** L3 结构化检查

### 步骤
1. 审查实现后的 SKILL.md 与代码
2. 检查 push 相关命令

### 预期结果
- 不存在 `git push --force` 或 `git push --force-with-lease`
- 保留 `git merge-base --is-ancestor` 预检
- 合并验证流程完整

---

## TC-011: 自循环会话恢复

**对应 R-002**
**优先级:** P1
**类型:** L2 交互

### 步骤
1. 启动自循环并推进到 implement
2. 用户发送 `/devflow`

### 预期结果
- Step 0 检测到未完成的自循环会话
- 询问用户是否恢复
- 恢复后继续自循环推进

---

*由 DevFlow 追踪。请勿手动编辑。*
