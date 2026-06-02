# Test Cases Checklist

> Generated: 2026-06-02
> Source: /devflow:blueprint
> Linked Requirements: devflow/requirements.md

## TC-001: verify 两阶段流程结构验证

**Status:** done
**Covers:** R-001 (重构 verify 主流程为自动化验证管道)
**Type:** manual
**Steps:**
1. 在包含前端项目的仓库中执行 /devflow:verify
2. 观察执行流程是否分为 Phase 1 (自动扫描) 和 Phase 2 (人工核对)
3. 检查 Phase 1 完成后是否汇总报告再进入 Phase 2
**Expected Result:** verify 执行首先进行 Playwright 自动扫描（console/network/health/snapshot），完成后汇总发现，然后进入人工 TC 核对阶段

---

## TC-002: 自动化检查项到 TC 的映射

**Status:** done
**Covers:** R-001 (重构 verify 主流程为自动化验证管道)
**Type:** manual
**Steps:**
1. 执行 verify Phase 1
2. 检查每个自动化发现（console error / 4xx / 白屏）是否关联到对应的 TC-xxx
3. 验证报告中是否有 "Covered by Phase 1 auto-scan" 标记
**Expected Result:** 每个自动化检查项都映射到一个 TC，自动化覆盖的 TC 无需再人工核对

---

## TC-003: Playwright MCP 可用性检查

**Status:** done
**Covers:** R-001 (重构 verify 主流程为自动化验证管道)
**Type:** manual
**Steps:**
1. 在没有 Playwright MCP 的环境中执行 verify
2. 观察 skill 是否检测到 MCP 不可用
3. 观察是否降级为全人工模式并提示用户
**Expected Result:** Skill 检测到 Playwright MCP 不可用时，输出警告 "Playwright MCP not available, falling back to manual verification" 并跳过 Phase 1

---

## TC-004: 单页面控制台错误捕获

**Status:** done
**Covers:** R-002 (控制台错误零容忍检查)
**Type:** e2e
**Steps:**
1. 使用 browser_navigate 导航到一个页面
2. 使用 browser_console_messages 捕获控制台消息
3. 检查是否有 console.error 级别的消息
4. 有 error 则标记对应 TC 失败
**Expected Result:** 所有 console.error 被捕获并报告，页面 URL + 错误内容清晰展示

---

## TC-005: console.error allowlist 机制

**Status:** done
**Covers:** R-002 (控制台错误零容忍检查)
**Type:** e2e
**Steps:**
1. 导航到一个有 favicon.ico 404 错误的页面
2. 确认 allowlist 中默认包含 "favicon.ico 404"
3. 该错误不应导致 TC 失败
4. 引入一个业务相关的 console.error，确认该错误导致 TC 失败
**Expected Result:** allowlist 中的错误被豁免（跳过），不在其中的错误标记为失败

---

## TC-006: 网络请求 4xx/5xx 捕获

**Status:** done
**Covers:** R-003 (网络请求健康检查)
**Type:** e2e
**Steps:**
1. 导航到一个包含异常 API 请求的页面（如 500 或 404 的 API 响应）
2. 使用 browser_network_requests 获取所有请求
3. 检查是否有 HTTP 状态码 >= 400 的请求
4. 验证异常请求的 URL、状态码、触发页面被记录
**Expected Result:** 所有 4xx/5xx 请求被捕获并关联到具体页面，报告中列出 URL + 状态码

---

## TC-007: 正常请求不误报

**Status:** done
**Covers:** R-003 (网络请求健康检查)
**Type:** e2e
**Steps:**
1. 导航到一个所有 API 请求都正常的页面（全部 2xx/3xx）
2. 运行网络请求检查
3. 确认没有误报的异常
**Expected Result:** 正常请求（2xx/3xx）不产生异常报告

---

## TC-008: 路由页面自动发现

**Status:** done
**Covers:** R-004 (全页面运行时健康扫描)
**Type:** e2e
**Steps:**
1. 在一个多页面前端项目中执行 verify
2. 观察 Phase 1 是否自动发现所有路由页面
3. 检查发现的页面列表是否完整
**Expected Result:** Skill 自动从路由配置或页面目录中发现所有需要测试的页面，列出完整 URL 列表

---

## TC-009: 页面滚动触发懒加载

**Status:** done
**Covers:** R-004 (全页面运行时健康扫描)
**Type:** e2e
**Steps:**
1. 导航到一个包含懒加载组件的页面（如无限滚动列表）
2. 使用 browser_scroll 滚动页面到底部
3. 检查懒加载内容是否正确触发和渲染
4. 检查是否有因滚动触发的 JS 错误
**Expected Result:** 滚动操作正确触发懒加载，无 JS 崩溃，新内容正确渲染到 DOM 中

---

## TC-010: 白屏/崩溃检测

**Status:** done
**Covers:** R-004 (全页面运行时健康扫描)
**Type:** e2e
**Steps:**
1. 导航到一个已知正常渲染的页面
2. 检查 DOM 结构中有有效内容（非空 body、非纯空白）
3. 验证未产生 "page crash" 相关信息
4. （如果要测试失败场景）导航到会白屏的页面，验证被标记为失败
**Expected Result:** 正常渲染页面通过检查；白屏页面（空 DOM / 无可见内容）被标记为失败

---

## TC-011: 页面超时处理

**Status:** done
**Covers:** R-004 (全页面运行时健康扫描)
**Type:** e2e
**Steps:**
1. 导航到一个响应极慢或无限挂起的页面
2. 等待 15 秒超时
3. 检查该页面被记录为超时警告而非致命失败
**Expected Result:** 超时页面标记为 Warning（非 Failure），报告提示 "Page X timed out after 15s" 并继续扫描其他页面

---

## TC-012: browser_snapshot 语义结构断言

**Status:** done
**Covers:** R-005 (结构化 DOM 快照断言)
**Type:** e2e
**Steps:**
1. 导航到关键页面（如首页、登录页）
2. 使用 browser_snapshot 获取语义化 DOM 结构
3. 验证核心交互元素存在（如提交按钮、搜索框、导航链接）
4. 检查报告是否展示通过/失败的元素列表
**Expected Result:** snapshot 返回结构化数据，包含元素的 role、label、state 信息；核心元素的存在性断言通过

---

## TC-013: snapshot 容忍 UI 微调

**Status:** done
**Covers:** R-005 (结构化 DOM 快照断言)
**Type:** e2e
**Steps:**
1. 对一个页面做微小 CSS 调整（颜色、间距），不改变 DOM 结构
2. 再次运行 browser_snapshot 断言
3. 确认之前通过的元素断言依然通过（不因视觉微调假阳性）
**Expected Result:** 仅 CSS 变化的页面不产生 snapshot 断言失败

---

## TC-014: Phase 2 人工核对保留

**Status:** done
**Covers:** R-006 (保留人工 TC-xxx 核对)
**Type:** manual
**Steps:**
1. 完成 Phase 1 自动扫描
2. 观察 Phase 2 是否展示剩余的 TC-xxx（未被自动化覆盖的）
3. 逐条人工验证 TC-xxx
4. 标记通过/失败
**Expected Result:** Phase 2 仅展示自动化未覆盖的 TC，人工核对结果与 Phase 1 结果共同汇总到最终报告

---

## TC-015: 自动化覆盖 TC 不再人工重复

**Status:** done
**Covers:** R-006 (保留人工 TC-xxx 核对)
**Type:** manual
**Steps:**
1. Phase 1 自动检查已覆盖的 TC（如 console 检查覆盖了 TC-xxx）
2. Phase 2 中这些 TC 应标记为 "auto-checked" 并默认跳过
3. 验证用户不需要重新人工核对已自动验证的项
**Expected Result:** 自动化已覆盖的 TC 在 Phase 2 中默认跳过，避免重复劳动

---

## TC-016: 验证报告自动化汇总

**Status:** done
**Covers:** R-007 (验证报告增强)
**Type:** manual
**Steps:**
1. 完成 Phase 1 + Phase 2
2. 查看生成的验证报告
3. 确认报告包含：console 检查通过/失败数、network 异常数、health scan 结果、snapshot 断言结果
4. 确认报告有自动 vs 人工通过率统计
**Expected Result:** 报告按类别分组展示，包含统计数据（通过率），每个失败项指向具体 TC 和修复建议

---

## TC-017: 失败项修复建议

**Status:** done
**Covers:** R-007 (验证报告增强)
**Type:** manual
**Steps:**
1. 引入一个 console.error 的 TC 失败
2. 查看报告中该失败项的展示
3. 确认包含：具体 TC-xxx、失败原因、建议的修复方向（回退到哪个 DevFlow 阶段）
**Expected Result:** 每个失败项包含：所属 TC、失败描述、关联页面/请求 URL、建议的回退阶段（/implement / /blueprint / /breakdown）

---

*Tracked by DevFlow. Do not edit manually.*
