---
name: verify
description: Verify implementation against the test case checklist (TC-xxx) and requirements (R-xxx). Uses a three-layer approach — L1 smoke scan (console errors, network failures, page crashes, DOM structure), L2 interaction verification (real user operations via Playwright MCP), L3 structured manual verification (evidence-driven). Failed items trigger smart rollback. Verification depth scoring exposes false positives from shallow checks.
argument-hint: [verification-scope]
allowed-tools: [Read, Glob, Grep, Bash, Edit, TaskCreate, browser_navigate, browser_console_messages, browser_network_requests, browser_snapshot, browser_scroll, browser_click, browser_type, browser_wait_for, browser_fill_form, browser_select_option, browser_press_key, browser_hover]
---

# /devflow:verify — Verification

## When to Use

Implementation is complete. All development tasks in `devflow/tasks.md` are marked done. You need to systematically verify everything works as specified.

This skill uses a **three-layer verification** approach:

| Layer | What It Checks | Method | Depth |
|-------|---------------|--------|-------|
| **L1: Smoke Scan** | Infrastructure health — console errors, HTTP failures, page crashes, missing elements | Playwright automated scan of all routes | Surface — checks that pages "don't break" |
| **L2: Interaction** | Core user operations — clicking buttons, filling forms, submitting, navigating | Playwright MCP executes real user actions, records DOM changes | Functional — checks that features "actually work" |
| **L3: Manual** | Subjective judgment — visual quality, permission logic, animation feel, multi-role scenarios | Structured protocol with evidence requirements | Deep — checks what a human user would notice |

**Key principle:** L1 passing alone does NOT mean "verification complete." Only L2 actually exercises functionality. The final report includes a **verification depth score** that exposes shallow verification.

---

## Process

### Step 1: Load Context & Check Capabilities

Read all DevFlow state files:
- `devflow/requirements.md` — what we promised to build
- `devflow/design.md` — the spec and scope
- `devflow/tasks.md` — what was implemented
- `devflow/test-cases.md` — the verification checklist

**Check Playwright MCP availability:**

Determine whether Playwright MCP tools are available. Check if `browser_navigate` is in the available tool list.

- **Playwright available + target URL known:** Proceed with full L1+L2+L3 pipeline.
- **Playwright available but no target URL:** Ask the user for the base URL of the running application (e.g., `http://localhost:3000`). If the user cannot provide one, all TC routes to L3.
- **Playwright NOT available:** Output:

  > "Playwright MCP 不可用，L1 烟雾扫描和 L2 交互验证将全部降级到 L3 结构化手工验证。"

  All TCs route to L3. The verification can still complete with full evidence requirements, just slower.

**Important:** Even in full-manual mode, every TC must still meet the evidence requirements defined in L3. No "I checked it, it works" without proof.

---

### Step 2: TC Router Engine

**This is the most critical step.** Before running any verification, classify every TC into the appropriate layer. Incorrect routing causes either false positives (interaction TC routed to L1) or wasted time (simple health TC routed to L3).

#### 2.1 Routing Rules

Parse every TC in `devflow/test-cases.md`. For each TC, extract its **type** field and scan its **title + steps** for keywords.

**Keyword → Layer mapping:**

| Keywords in TC Content | Route To | Rationale |
|------------------------|----------|-----------|
| 不报错、控制台错误、网络请求、HTTP 状态码、页面加载、资源加载、白屏、崩溃、页面超时 | L1 | Static health check covers these |
| 点击、输入、填写、提交、选择、上传、删除、编辑、创建、搜索、登录、注册、跳转、导航、返回、刷新 | L2 | Requires real interaction |
| 权限、角色、动画、过渡、响应式、文案、样式、颜色、布局、流畅、视觉、美观、体验 | L3 | Requires human subjective judgment |

**TC type → default layer (when keywords are ambiguous):**

| TC Type | Default Layer | Notes |
|---------|---------------|-------|
| 单元 | L1 | Code-level: check error output |
| 集成 | L1 or L2 | Determined by keywords |
| 端到端 | L2 | Simulates user workflow |
| 手工 | L3 | Requires human judgment |

#### 2.2 Routing Priority

Apply rules in this order:

1. TC type = 端到端 AND content has interaction keywords → **L2**
2. TC type = 手工 AND content has subjective keywords → **L3**
3. TC content has L1 keywords AND NO L2/L3 keywords → **L1**
4. Default → **L3** (better to verify manually than produce false positives)

#### 2.3 Present Routing Plan

After classification, display the routing plan to the user:

```
验证计划（共 N 条 TC）：

L1 烟雾扫描（X 条）：TC-001, TC-003, TC-005, ...
L2 交互验证（Y 条）：TC-002, TC-004, TC-008, ...
L3 手工验证（Z 条）：TC-006, TC-007, TC-009, ...
```

Ask: "路由计划如上。是否需要调整？[Y] 确认执行 / [调整 TC-xxx 从 X 层到 Y 层]"

Record any user adjustments. Once confirmed, write the final routing plan to `devflow/verification-log.md` as the first section.

---

## L1: Smoke Scan

> L1 checks structural health: do pages load without errors? These checks are fast, broad, and catch runtime regressions. **L1 passing ≠ features work.** L1 only proves the page's infrastructure is healthy.

### Step 3: Discover Routes

Determine all pages to scan:

1. If the project has a route config file (e.g., `src/router/index.ts`, `pages/` directory, `app/` routes in Next.js), read it to extract the full list of routes.
2. If no explicit route config exists, check `devflow/design.md` for mentioned pages, or ask the user:
   > "需要扫描所有页面路由。应用有哪些主要路由？(如 /, /login, /dashboard, /settings)"
3. Compile the final route list. Confirm with the user if the list looks complete.

### Step 4: Console Error Check (Zero-Tolerance)

**Covers:** TC routed to L1 with error/console keywords | **Maps to:** R-001

For each route in the discovered list:

1. Navigate to the page: `browser_navigate` to `<baseURL><route>`
2. Wait 2 seconds for initial JS execution to settle
3. Use `browser_console_messages` to collect all console output
4. Filter for `console.error` level messages

**Default allowlist** (these are known-harmless and do NOT count as failures):
- `/favicon.ico` — 404
- Source map 404 errors (e.g., `*.map` — 404)
- Chrome extension errors (errors originating from `chrome-extension://` URLs)

**To customize the allowlist:** Edit the allowlist items above in this skill file. Add project-specific patterns (e.g., third-party script errors you cannot fix) with a comment explaining why.

**Judgment:**
- Any console.error NOT in the allowlist → **FAIL**. Report: page URL, error message text, and line reference if available.
- Zero console errors (or only allowlist matches) → **PASS**

**Important:** Do NOT ignore warnings (`console.warn`). Report them as informational notes but do not fail on them. Only `console.error` triggers failure.

### Step 5: Network Request Health Check

**Covers:** TC routed to L1 with network/HTTP keywords | **Maps to:** R-001

For each route in the discovered list:

1. Navigate to the page: `browser_navigate` to `<baseURL><route>`
2. Use `browser_network_requests` to retrieve all network requests made by the page
3. Filter for HTTP status codes >= 400

**Judgment:**
- Any request returning 4xx or 5xx → **FAIL**. Report: failing URL, HTTP status code, and the page that triggered it.
- All requests return 2xx/3xx → **PASS**

**Notes:**
- A single page may trigger multiple failing requests. Report each one separately.
- Distinguish between API calls (actionable failures) and static asset 404s (usually missing images/icons). Both are reported, but API 5xx carries higher severity in the final report.

### Step 6: Runtime Health Scan (Crash & White-Screen Detection)

**Covers:** TC routed to L1 with crash/white-screen keywords | **Maps to:** R-001

For each route in the discovered list:

1. Navigate to the page: `browser_navigate` to `<baseURL><route>`
2. Wait for the page to reach a stable state (loaded or network idle)
3. Use `browser_snapshot` to capture the current DOM structure
4. **White-screen check:** If the snapshot shows an empty or near-empty body (no visible text content, no interactive elements, no meaningful landmarks), flag as **potential white screen**.
5. **Crash check:** If the snapshot returns an error or if the page title/body contains crash indicators (e.g., "Application error", "Something went wrong", "Cannot read properties of"), flag as **app crash**.
6. **Scroll check:** Use `browser_scroll` to scroll down by one viewport height. Re-capture snapshot. Check that new lazy-loaded content appeared (DOM grew) or that no error was triggered by scrolling.
7. Repeat scroll 2-3 times if the page has infinite-scroll indicators (load more buttons, skeleton loaders).

**Judgment:**
- Page loads and has meaningful DOM content, no crash indicators, scroll works → **PASS**
- White screen (empty DOM) → **FAIL** with severity HIGH
- App crash (error message in DOM) → **FAIL** with severity CRITICAL
- Scroll triggers JS error → **FAIL** with severity HIGH
- Page times out (15s default) without loading → **WARNING** (not FAIL — may be environment-specific)

### Step 7: Structured DOM Snapshot Assertions

**Covers:** TC routed to L1 with element/structure keywords | **Maps to:** R-001

For key pages identified as critical (homepage, login, main dashboard, primary feature pages):

1. Navigate to the page
2. Use `browser_snapshot` to get the accessibility tree / semantic structure
3. Verify that documented core UI elements exist in the snapshot:
   - Check for elements mentioned in `devflow/design.md` or `devflow/requirements.md`
   - Common checks: navigation bar, search input, submit buttons, main content area, footer
4. Use **existence assertions** only (is the element present in the snapshot?), NOT exact text matching or CSS property checks.

**Judgment:**
- Core elements present in snapshot → **PASS**
- Key element missing from snapshot → **FAIL**. Report which element was expected and which page was checked.
- Note: minor UI text changes do NOT cause failure. This check is for structural completeness, not visual precision.

### Step 8: Aggregate L1 Results

After scanning all routes, compile the L1 summary:

```markdown
## L1: Smoke Scan Results

### Console Errors
- /page-a: PASS (0 errors)
- /page-b: FAIL — 2 console errors detected:
  - "TypeError: Cannot read property 'name' of undefined" at app.js:142
  - "Failed to load resource: 500 /api/users"

### Network Health
- /page-a: PASS (all 2xx/3xx)
- /page-b: FAIL — 1 abnormal request:
  - GET /api/users → 500 Internal Server Error

### Runtime Health
- /page-a: PASS
- /page-b: PASS
- /page-c: WARNING — page timed out after 15s

### DOM Snapshot
- / (homepage): PASS — all core elements present
- /login: PASS — login form, submit button present

**L1 Summary:** X/Y pages smoke-scan clean. Z issues found (C console errors, N network failures, H health warnings, S snapshot gaps).

> ⚠️ L1 烟雾扫描仅检查页面基础设施是否正常（不报错、不崩溃、元素存在）。不代表业务功能验证通过。业务功能验证由 L2 和 L3 完成。
```

Map each finding to a TC-xxx. L1 passing results mark their corresponding TCs as having L1 coverage. L1 failures flag TCs for attention.

---

## L2: Interaction Verification

> L2 is the critical new layer. It doesn't just check that a page loaded — it exercises real user actions and observes whether the page responds correctly. This is where most "verify passed but manually broken" issues are caught.

### Step 9: Extract L2 TC Actions

From the routing plan, take all TCs routed to L2. For each TC:

1. Parse the **步骤** field to extract action steps. Look for action verbs:
   - 点击 / click → `browser_click`
   - 输入 / 填写 / type / fill → `browser_type` or `browser_fill_form`
   - 选择 / select → `browser_select_option`
   - 等待 / wait → `browser_wait_for`
   - 导航 / 跳转 / navigate → `browser_navigate`
   - 悬停 / hover → `browser_hover`
   - 按键 / press → `browser_press_key`

2. Build an action sequence for each TC. Each action is: `{tool, target, value, description}`.

3. If a TC has more than 5 steps, split it into sub-sequences with intermediate checkpoints.

**Target resolution:** When a step says "点击提交按钮" but doesn't specify an exact selector, use `browser_snapshot` first to find a matching element (button with "提交" text or submit type), then use that element reference.

### Step 10: Execute Interaction + Record Trace

For each L2 TC:

1. **Pre-action snapshot:** Use `browser_snapshot` to capture the DOM state before the action.
2. **Execute action:** Call the appropriate Playwright tool.
3. **Wait for response:** Use `browser_wait_for` to wait for either DOM change or a short time (1-2s for instant feedback, up to 5s for async operations).
4. **Post-action snapshot:** Use `browser_snapshot` to capture the DOM state after the action.
5. **Record interaction trace:** For each action step, write to `devflow/verification-log.md`:

```markdown
#### TC-xxx Step N: [action description]

**操作:** navigate → /login
**操作前 DOM 摘要:** [semantic elements visible before: button "登录", input "email", input "password"]
**操作后 DOM 摘要:** [semantic elements visible after: same as before, page loaded]
**DOM 变化:** 无结构性变化（页面初始加载）
**结果:** ✅ 页面加载成功
```

For actions expected to change the DOM:

```markdown
#### TC-xxx Step N: [action description]

**操作:** click "提交" button (空表单)
**操作前 DOM 摘要:** form with 3 inputs, 1 submit button
**操作后 DOM 摘要:** form with 3 inputs, 1 submit button, NEW: 2x role="alert" with validation messages
**DOM 变化:** +2 alert elements (表单校验错误提示)
**结果:** ✅ 表单校验触发（验证了空表单会被拦截）
```

### Step 11: DOM Change Judgment

**Do NOT rely on exact text content** (e.g., "请输入邮箱" vs "请输入电子邮件"). Instead, judge based on **semantic DOM structure changes**:

| Expected Behavior | What to Check |
|------------------|---------------|
| Form submitted successfully | Page URL changed OR new semantic elements appeared (e.g., success message, new page heading, redirect) |
| Validation error shown | New elements with `role="alert"` or `alert` in snapshot appeared; form structure unchanged |
| Navigation happened | URL changed OR page heading in snapshot changed |
| Modal/dialog opened | New element with dialog/modal semantics appeared in snapshot |
| Content loaded/refreshed | List/table element count changed; new text nodes appeared |
| Button disabled during loading | Button element attribute changed to disabled |

**Judgment per action:**
- DOM changed in the semantically expected way → **✅ Action effective**
- DOM did NOT change when it should have → **❌ Action ineffective** (FAIL)
- DOM changed in an unexpected way (error page, redirect to wrong page) → **❌ Unexpected result** (FAIL)
- Cannot determine (ambiguous change, dynamic content) → **⚠️ Uncertain** (flag for manual review in L3)

### Step 12: Interaction Timeout & Side-Effect Guard

**Timeout handling:**
- Single action timeout: 30 seconds. If an action times out, mark as **❌ Timeout** and skip remaining steps for that TC.
- Full TC timeout: 2 minutes. If a TC's total interaction chain exceeds this, mark as **⚠️ Incomplete** and note which steps weren't executed.

**Side-effect guard — check before L2 execution:**
- If the TC involves **write operations** (创建/删除/修改/上传/提交订单/发送), do NOT auto-execute those steps. Instead:
  1. Execute read-only steps (navigation, viewing) automatically
  2. At the write step, pause and ask: "TC-xxx 包含写操作（[具体操作]）。是否继续自动执行？[Y] 执行 / [S] 跳过此步骤，手工验证 / [跳过整个 TC]"
  3. If on a non-localhost URL (production/staging), warn more strongly.
- This prevents accidental data modification in shared environments.

### Step 13: L2 Playwright Degradation

If Playwright MCP tools are NOT available:

> "Playwright MCP 不可用，L2 交互验证降级为手工引导模式。"

For each L2 TC:
1. Display the TC steps clearly
2. Guide the user: "请执行以下操作：1) 打开页面 /xxx  2) 点击 '提交' 按钮（留空表单） 3) 告诉我页面发生了什么变化"
3. After the user reports back, ask: "操作结果如何？[A] 符合预期 / [B] 不符合预期（请描述）/ [C] 跳过"
4. Record the user's report as evidence in the interaction trace

---

## L3: Structured Manual Verification

> L3 covers what automation cannot: subjective judgment, complex permission logic, multi-role scenarios, visual quality. Every L3 TC must have evidence — no evidence, no "done."

### Step 14: Evidence Requirements Matrix

Different TC types need different evidence. This is non-negotiable:

| TC Type | Minimum Evidence | Acceptable Evidence |
|---------|-----------------|---------------------|
| 端到端 (降级到L3) | User confirmation of each step result | User report + relevant DOM snapshot / console log captured by model |
| 手工 (视觉/体验) | User confirmation of visual check | User report describing what they saw |
| 手工 (权限/角色) | User confirms behavior for each role | User report per role, OR console/network logs showing auth behavior |
| 手工 (业务逻辑) | User confirms calculation/result is correct | User report with specific input/output values verified |
| 手工 (其他) | At least user confirmation | Any relevant logs or snapshots the model can capture |

**Evidence grading:**
- 🟢 **Strong evidence:** DOM snapshot + console log + network log + user confirmation
- 🟡 **Adequate evidence:** User confirmation OR one type of automated log
- 🔴 **No evidence:** TC status must be `unverified`, not `done`

### Step 15: Structured Verification Protocol

For each L3 TC:

1. **Display the TC** clearly:
   ```
   ─────────────────────────────
   TC-xxx: [标题]
   步骤:
     1. [准备步骤]
     2. [操作步骤]
     3. [验证步骤]
   预期结果: [应该发生什么]
   ─────────────────────────────
   ```

2. **Attempt automated evidence collection first:** Before asking the user, check if any evidence can be gathered automatically:
   - Can we navigate to the relevant page and capture a snapshot?
   - Can we check console/network logs?
   - Automated evidence is preferred because it's objective.

3. **Ask the user for what can't be automated:**
   - "TC-xxx 需要人工判定。请执行上述步骤后告诉我：[具体的判定问题]。"
   - For visual TCs: "请确认 [具体视觉效果] 是否符合预期？"
   - For permission TCs: "请分别用 [角色A] 和 [角色B] 登录，确认看到的内容是否不同。"

4. **Record evidence** immediately in `devflow/verification-log.md`:

```markdown
#### TC-xxx: [标题]

**层级:** L3
**证据类型:** [用户确认 / DOM snapshot / Console log / Network log]
**证据:**
- [用户报告内容，引用原文]
- [自动采集的日志/snapshot 摘要]
**证据等级:** 🟢 Strong / 🟡 Adequate
**结果:** ✅ done / ❌ fail / ⚠️ unverified / ⏭️ skipped
**备注:** [如有]
```

### Step 16: Unverified & Skipped Rules

- **No evidence → `unverified`:** A TC with zero evidence cannot be marked `done`. It stays `unverified` and counts against the depth score.
- **User skipped → `skipped` with reason:** If the user explicitly says "skip this TC," record it as `skipped` with the reason they give. Skipped TCs are NOT counted as verified.
- **TC not applicable → `n/a`:** If the TC genuinely doesn't apply to this feature (e.g., misrouted), mark as `n/a` with justification. n/a TCs are excluded from depth scoring.

---

## Verification Report

### Step 17: Aggregate All Three Layers

Combine L1, L2, and L3 results into a single evidence index:

1. Count TCs that were actually executed (had actions run or had user evidence collected) vs. TCs that were only marked based on static checks.
2. Count TCs with at least one evidence item.
3. Group by layer distribution.

### Step 18: Calculate Depth Scores

**Verification Depth Score** = (TCs with actual execution or user evidence) / (Total TCs - n/a TCs)

- Execution means: L2 had Playwright actions run OR L3 had user confirmation recorded.
- L1-only coverage does NOT count as "executed" — L1 checks infrastructure, not functionality.

**Evidence Coverage Score** = (TCs with at least one evidence item) / (Total TCs - n/a TCs)

**Layer Distribution:**
- L1 coverage: X TCs
- L2 coverage: Y TCs (Z auto-executed, W degraded to manual)
- L3 coverage: V TCs

### Step 19: Generate Unified Verification Report

Write the complete report to `devflow/verification-log.md`:

```markdown
# DevFlow 验证报告

**日期:** YYYY-MM-DD HH:MM
**应用:** <baseURL>
**Feature:** <feature-name>

---

## 验证计划

| TC | 路由 | 依据 |
|----|------|------|
| TC-001 | L1 | 关键词: "不报错" |
| TC-002 | L2 | 关键词: "点击提交" |
| TC-003 | L3 | 关键词: "权限" |
| ... | ... | ... |

路由调整: [如有用户调整，记录]

---

## L1: 烟雾扫描

| 类别 | 页面数 | 通过 | 失败 | 警告 |
|------|--------|------|------|------|
| Console Errors | N | X | Y | — |
| Network Health | N | X | Y | — |
| Runtime Health | N | X | Y | Z |
| DOM Snapshot | N | X | Y | — |

**问题清单:**
1. **/page-x — Console Error:** [error text]
   - 严重性: HIGH
   - 建议: /devflow:implement T-xxx

---

## L2: 交互验证追踪

### TC-002: [标题]
- Step 1: navigate → /login ✅ 页面加载成功
  - 操作前: [DOM摘要]
  - 操作后: [DOM摘要]
- Step 2: click "提交" (空表单) ✅ 表单校验触发
  - DOM变化: +2 alert elements
- **结果:** ✅ 通过

### TC-004: [标题]
- Step 1: navigate → /dashboard ✅
- Step 2: click "删除" button ❌ 按钮点击后无 DOM 变化
  - 操作前: [DOM摘要]
  - 操作后: [DOM摘要 — 完全一致]
  - **结果:** ❌ 失败 — 删除按钮点击无效

---

## L3: 结构化手工验证

#### TC-006: [标题]
- **证据类型:** 用户确认
- **证据:** 用户报告："用 admin 登录能看到所有菜单，用 user 登录只看到 3 个菜单"
- **证据等级:** 🟡 Adequate
- **结果:** ✅ done

#### TC-007: [标题]
- **证据:** 无
- **结果:** ⚠️ unverified — 用户未提供反馈

---

## 深度评分

| 指标 | 值 | 状态 |
|------|-----|------|
| 总 TC 数 | 10 | — |
| 验证深度 | 8/10 (80%) | ⚠️ 2 条未执行 |
| 证据覆盖率 | 9/10 (90%) | ⚠️ 1 条无证据 |
| n/a (不适用) | 0 | — |

**分层覆盖:**
- L1 覆盖: 4 条（烟雾扫描）
- L2 覆盖: 4 条（3 自动执行 + 1 手工降级）
- L3 覆盖: 2 条

**未验证项:**
- TC-007: 无证据（用户未反馈）
- TC-009: 未执行（用户跳过 — "非本期范围"）

---

## 结论

> ⚠️ **部分通过。** 8/10 TC 验证通过（80%），验证深度 80%，证据覆盖率 90%。
> 以下 TC 未完全验证：TC-007, TC-009。
> 建议：对 TC-007 收集证据后重新验证，或确认 TC-009 可推迟到后续迭代。

### 失败项详情

1. **TC-004 (L2):** 删除按钮点击无效
   - 操作: 在 /dashboard 点击 "删除" 按钮
   - 预期: 出现确认弹窗或列表项减少
   - 实际: DOM 无任何变化
   - 严重性: HIGH
   - 根因分析: 按钮可能未绑定点击事件或事件处理器有 bug
   - 建议: /devflow:implement T-xxx（修复删除按钮事件绑定）
```

---

### Step 20: Smart Rollback (When Issues Found)

When issues are found, classify and route them:

| Failure Category | Layer | Root Phase | Action |
|-----------------|-------|------------|--------|
| Console error (TypeError, ReferenceError) | L1 | implement | Bug in code — re-run specific T-xxx |
| HTTP 500 from API | L1 | implement | Backend bug — re-run affected task |
| HTTP 404 for expected endpoint | L1 | blueprint | Missing API — fix spec, re-derive tasks |
| White screen / app crash | L1 | implement | Runtime error — re-run affected task |
| Missing UI element (snapshot fail) | L1 | implement | Incomplete UI — re-run that component's task |
| Button click no response | L2 | implement | Event handler bug — re-run specific T-xxx |
| Form submit wrong behavior | L2 | implement or blueprint | Bug or spec gap — re-run task or revisit design |
| Interaction triggers wrong outcome | L2 | blueprint or breakdown | Design or requirement gap |
| Business logic wrong (L3 fail) | L3 | blueprint or breakdown | Design or requirement gap |
| Visual/animation issue (L3 fail) | L3 | implement | UI fix — re-run specific T-xxx |
| Permission logic wrong (L3 fail) | L3 | blueprint | Design gap — revisit auth spec |
| Requirement no longer valid | L3 | breakdown or clarify | Revisit requirements |

**Incremental redo principle:** Only re-do the affected chain. If R-003 changed and only T-005 and TC-008 were affected, only those need re-work. Everything else stays verified.

### Step 21: All Green — Complete

**"All green" now requires BOTH:**
1. All TCs either `done` or `n/a` (no `fail`, no `unverified`)
2. **Verification depth = 100%** (every TC was actually executed or had evidence collected)

When both conditions are met:

> "✅ 全部验证通过（深度 100%，证据覆盖率 100%）。DevFlow 循环完成。"

- All TC statuses updated to `done`
- All R statuses updated to `done`
- Suggest next: commit, push, deploy

**When depth < 100%:**

> "⚠️ 验证未完全完成。验证深度 [X]%，[N] 条 TC 未执行或无证据。是否接受当前结果？[Y] 接受，标记为完成 / [N] 继续验证未覆盖的 TC"

This prevents the old pattern of "all checks passed but features don't work" — because checks that weren't actually executed can't "pass."

---

## Handoff

After successful verification (depth = 100%, all passing):

- Suggest git commit and push for any fixes made during verification
- Suggest PR creation if applicable
- No further DevFlow commands needed for this feature

If issues remain, handoff to the identified phase for re-work.

---

## Playwright MCP Tool Reference

This skill uses the following Playwright MCP tools:

| Tool | Purpose | Used In |
|------|---------|---------|
| `browser_navigate` | Navigate to a URL | L1, L2 |
| `browser_console_messages` | Collect console output (filter for errors) | L1 |
| `browser_network_requests` | Retrieve all HTTP requests and status codes | L1 |
| `browser_snapshot` | Get accessibility tree / semantic DOM structure | L1, L2, L3 |
| `browser_scroll` | Scroll the page by pixels or viewport | L1 |
| `browser_click` | Click an element on the page | L2 |
| `browser_type` | Type text into an editable element | L2 |
| `browser_fill_form` | Fill multiple form fields at once | L2 |
| `browser_select_option` | Select an option in a dropdown | L2 |
| `browser_wait_for` | Wait for text to appear/disappear or time to pass | L2 |
| `browser_press_key` | Press a key on the keyboard | L2 |
| `browser_hover` | Hover over an element | L2 |
