# Task Breakdown

> Generated: 2026-06-02
> Source: /devflow:implement
> Based on: devflow/design.md, devflow/requirements.md

## T-001: 更新 frontmatter + Step 1 主流程入口

**Status:** done
**Covers:** R-001 (重构 verify 主流程为自动化验证管道)
**Dependencies:** none
**Complexity:** low
**Estimated Files/Modules:**
- `skills/verify/SKILL.md` — 更新 allowed-tools，重写 Step 1（加载+MCP可用性检查+URL获取）

**Description:** 更新 YAML frontmatter 添加 Playwright MCP 工具；重写 Step 1 为加载所有跟踪文件、检查 Playwright MCP 可用性、询问应用 URL

---

## T-002: Phase 1 Playwright 自动扫描

**Status:** done
**Covers:** R-002, R-003, R-004, R-005
**Dependencies:** T-001
**Complexity:** medium
**Estimated Files/Modules:**
- `skills/verify/SKILL.md` — Steps 2-7：路由发现、console 检查、network 检查、health scan、DOM snapshot、Phase 1 汇总

**Description:** 编写 Phase 1 五项检查的完整指令：Step 2 路由发现、Step 3 控制台错误零容忍、Step 4 网络请求健康检查、Step 5 运行时健康扫描（含白屏/崩溃检测+滚动）、Step 6 DOM 快照断言、Step 7 汇总 Phase 1 结果

---

## T-003: Phase 2 人工核对

**Status:** done
**Covers:** R-006 (保留人工 TC-xxx 核对)
**Dependencies:** T-002
**Complexity:** low
**Estimated Files/Modules:**
- `skills/verify/SKILL.md` — Step 8：人工业务逻辑验证流程

**Description:** 重写人工核对流程，自动跳过 Phase 1 已覆盖的 TC，仅展示需要人工判断的业务逻辑 TC

---

## T-004: 验证报告 + Smart Rollback

**Status:** done
**Covers:** R-007 (验证报告增强)
**Dependencies:** T-002
**Complexity:** low
**Estimated Files/Modules:**
- `skills/verify/SKILL.md` — Steps 9-11：报告模板、Smart Rollback 增强、Playwright MCP 工具参考表

**Description:** 增强验证报告模板（自动+人工分组统计）、更新 Smart Rollback 路由表（新增 console/network/health/snapshot 失败类别）、添加 Playwright MCP 工具参考表

---
*Tracked by DevFlow. Do not edit manually.*
