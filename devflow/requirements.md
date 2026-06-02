# Requirements Checklist

> Generated: 2026-06-02
> Source: /devflow:breakdown

## R-001: 重构 verify 主流程为自动化验证管道

**Priority:** P0
**Status:** done
**Description:** 将 verify 从"人工逐条核对清单"改为"先自动扫描 → 再人工核对"的两阶段管道
**Depends On:** none
**Acceptance Criteria:**
- [ ] verify 流程明确分为 Phase 1 自动扫描 + Phase 2 人工核对
- [ ] Phase 1 完成后汇总所有自动化发现，再进入 Phase 2
- [ ] 每个自动化检查项映射到对应的 TC-xxx

---

## R-002: 控制台错误零容忍检查

**Priority:** P0
**Status:** done
**Description:** 使用 browser_console_messages 捕获所有页面 console.error，任何错误即标记对应 TC 失败
**Depends On:** R-001
**Acceptance Criteria:**
- [ ] 每个页面导航后自动采集 console 消息
- [ ] console.error 级别的消息标记为测试失败
- [ ] 提供可配置的 allowlist（允许特定已知无害错误）

---

## R-003: 网络请求健康检查

**Priority:** P0
**Status:** done
**Description:** 使用 browser_network_requests 监控所有 HTTP 请求，捕获 4xx/5xx 响应
**Depends On:** R-001
**Acceptance Criteria:**
- [ ] 自动记录所有 HTTP 请求的状态码
- [ ] 4xx/5xx 响应标记为异常并关联到对应 TC
- [ ] 报告中列出异常请求的 URL、状态码、触发页面

---

## R-004: 全页面运行时健康扫描

**Priority:** P0
**Status:** done
**Description:** 遍历所有路由页面，每页滚动触发 lazy load，检查页面崩溃、白屏、JS 运行时错误
**Depends On:** R-001
**Acceptance Criteria:**
- [ ] 自动发现所有需要测试的路由页面
- [ ] 每个页面执行滚动操作触发懒加载
- [ ] 捕获页面崩溃或白屏（通过 DOM 结构判断）
- [ ] 超时或无响应的页面标记为失败

---

## R-005: 结构化 DOM 快照断言

**Priority:** P1
**Status:** done
**Description:** 使用 browser_snapshot 获取语义化页面结构，验证关键 UI 元素（按钮、表单、导航）存在且可交互
**Depends On:** R-001
**Acceptance Criteria:**
- [ ] 关键页面生成 browser_snapshot 并进行断言
- [ ] 验证核心交互元素存在（提交按钮、搜索框、导航链接等）
- [ ] 替代纯文本断言，减少假阳性

---

## R-006: 保留人工 TC-xxx 核对

**Priority:** P1
**Status:** done
**Description:** Phase 1 自动扫描完成后，保留人工逐条核对 TC-xxx 的 Phase 2，覆盖自动化无法验证的业务逻辑
**Depends On:** none
**Acceptance Criteria:**
- [ ] 保留原 verify 人工核对流程作为 Phase 2
- [ ] Phase 2 仅处理自动化未覆盖的 TC-xxx
- [ ] 人工核对与自动化结果汇总到同一报告

---

## R-007: 验证报告增强

**Priority:** P2
**Status:** done
**Description:** 报告包含自动化检查的详细结果，按类别分组展示通过/失败/跳过的统计
**Depends On:** R-002, R-003, R-004, R-005
**Acceptance Criteria:**
- [ ] 报告增加自动化检查汇总（console / network / health / snapshot）
- [ ] 每个失败的检查项指向具体 TC 和修复建议
- [ ] 通过率按类别统计（自动 vs 人工）

---

*Tracked by DevFlow. Do not edit manually.*
