---
name: verify
description: Verify implementation against the test case checklist (TC-xxx) and requirements (R-xxx). Phase 1 runs Playwright automated health scans (console errors, network failures, page crashes, DOM structure). Phase 2 performs manual verification of remaining business-logic TCs. Failed items trigger smart rollback.
argument-hint: [verification-scope]
allowed-tools: [Read, Glob, Grep, Bash, Edit, TaskCreate, browser_navigate, browser_console_messages, browser_network_requests, browser_snapshot, browser_scroll, browser_take_screenshot]
---

# /devflow:verify — Verification

## When to Use

Implementation is complete. All development tasks in `devflow/tasks.md` are marked done. You need to systematically verify everything works as specified.

This skill runs a **two-phase pipeline**: Phase 1 uses Playwright to automatically scan for structural defects (console errors, broken requests, page crashes, missing UI elements). Phase 2 performs manual business-logic verification on the remaining TCs that automation cannot cover.

## Process

### Step 1: Load Context & Check Capabilities

Read all DevFlow state files:
- `devflow/requirements.md` — what we promised to build
- `devflow/design.md` — the spec and scope
- `devflow/tasks.md` — what was implemented
- `devflow/test-cases.md` — the verification checklist

**Check Playwright MCP availability:**

Before starting Phase 1, determine whether Playwright MCP tools are available. If `browser_navigate` is listed in available tools and the user has a running dev server or deploy preview URL, proceed with Phase 1. Otherwise, skip to Phase 2 (manual only) and output:

> "Playwright MCP not available or no target URL configured. Skipping Phase 1 automated scan. Proceeding with Phase 2 manual verification."

Ask the user for the base URL of the running application (e.g., `http://localhost:3000`) if not already known. If the user cannot provide one, skip Phase 1.

---

## Phase 1: Playwright Automated Health Scan

> Phase 1 runs structural checks that catch the most common "verify passed but broken in real use" issues. Each check maps to specific TC-xxx items. Failures here are high-signal — they indicate real runtime problems.

### Step 2: Discover Routes

Determine all pages to scan:

1. If the project has a route config file (e.g., `src/router/index.ts`, `pages/` directory, `app/` routes in Next.js), read it to extract the full list of routes.
2. If no explicit route config exists, check `devflow/design.md` for mentioned pages, or ask the user:
   > "I need to scan all pages. What are the main routes of this application? (e.g., /, /login, /dashboard, /settings)"
3. Compile the final route list. Confirm with the user if the list looks complete.

### Step 3: Console Error Check (Zero-Tolerance)

**Covers:** TC-004, TC-005 | **Maps to:** R-002

For each route in the discovered list:

1. Navigate to the page: `browser_navigate` to `<baseURL><route>`
2. Wait 2 seconds for initial JS execution to settle
3. Use `browser_console_messages` to collect all console output
4. Filter for `console.error` level messages

**Default allowlist** (these are known-harmless and do NOT count as failures):
- `/favicon.ico` — 404
- Source map 404 errors (e.g., `*.map` — 404)
- Chrome extension errors (errors originating from `chrome-extension://` URLs)

**Judgment:**
- Any console.error NOT in the allowlist → **FAIL**. Report: page URL, error message text, and line reference if available.
- Zero console errors (or only allowlist matches) → **PASS**

**Important:** Do NOT ignore warnings (`console.warn`). Report them as informational notes but do not fail on them. Only `console.error` triggers failure.

### Step 4: Network Request Health Check

**Covers:** TC-006, TC-007 | **Maps to:** R-003

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

### Step 5: Runtime Health Scan (Crash & White-Screen Detection)

**Covers:** TC-008, TC-009, TC-010, TC-011 | **Maps to:** R-004

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

### Step 6: Structured DOM Snapshot Assertions

**Covers:** TC-012, TC-013 | **Maps to:** R-005

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

### Step 7: Aggregate Phase 1 Results

After scanning all routes, compile a Phase 1 summary:

```markdown
## Phase 1: Automated Scan Results

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

**Phase 1 Summary:** X/Y pages fully passing. Z issues found (C console errors, N network failures, H health warnings, S snapshot gaps).
```

Map each finding to a TC-xxx. Automated findings automatically mark their corresponding TC as `done` (if passing) or flag it for attention (if failing).

---

## Phase 2: Manual TC Verification

### Step 8: Manual Business-Logic Verification

**Covers:** TC-014, TC-015 | **Maps to:** R-006

Now process the test cases that Phase 1 could NOT automatically verify. These are typically:
- Business logic correctness (does the calculation produce the right result?)
- User interaction flows (multi-step workflows, form submissions)
- Permission/authorization behavior
- Edge case scenarios from `devflow/test-cases.md`

For each remaining TC-xxx:

1. Display the TC: show its steps and expected result
2. Check if Phase 1 already covered it (e.g., console check covered the error-handling TC)
   - If covered by Phase 1 → mark as `done` with note "Verified by Phase 1 auto-scan"
   - If not covered → proceed with manual verification
3. For manual-only TCs:
   - If the TC is testable with available tools (can navigate, can inspect DOM, can run a command), test it now
   - If the TC requires human judgment (e.g., "the animation feels smooth"), ask the user to verify and report
4. Mark status: `done` if passing, leave `pending` if not checked or failing

**Key rule:** Do NOT ask the user to re-verify TCs that Phase 1 already covered. This avoids duplicate work.

---

## Verification Report

### Step 9: Generate Verification Report

**Covers:** TC-016, TC-017 | **Maps to:** R-007

```markdown
## DevFlow Verification Report

**Date:** YYYY-MM-DD
**Application:** <baseURL>

### Phase 1: Automated Scan

| Category | Pages Scanned | Pass | Fail | Warning |
|----------|--------------|------|------|---------|
| Console Errors | N | X | Y | — |
| Network Health | N | X | Y | — |
| Runtime Health | N | X | Y | Z |
| DOM Snapshot | N | X | Y | — |

### Phase 2: Manual Verification

- TC-xxx ✅ (auto-covered by Phase 1 console check)
- TC-xxx ✅ (manual — verified)
- TC-xxx ❌ (manual — see issue #1 below)

### Summary

| Metric | Value |
|--------|-------|
| Total TCs | X |
| Auto-verified (Phase 1) | Y |
| Manually verified (Phase 2) | Z |
| Passing | A |
| Failing | B |
| Pass Rate | A/X (XX%) |

### Issues Found

1. **TC-xxx failed:** [description of the failure]
   - **Category:** console / network / health / snapshot / business-logic
   - **Severity:** CRITICAL / HIGH / MEDIUM / LOW
   - **Evidence:** [console error text / HTTP status / snapshot diff / user report]
   - **Root cause analysis:** [what went wrong]
   - **Recommended action:** /devflow:implement T-xxx (bug fix) / /devflow:blueprint (design issue) / /devflow:breakdown (requirement gap)
```

### Step 10: Smart Rollback (When Issues Found)

When issues are found, classify and route them:

| Failure Category | Root Phase | Action |
|-----------------|------------|--------|
| Console error (TypeError, ReferenceError) | /implement | Bug in code — re-run specific T-xxx |
| HTTP 500 from API | /implement | Backend bug — re-run affected task |
| HTTP 404 for expected endpoint | /blueprint | Missing API — fix spec, re-derive tasks |
| White screen / app crash | /implement | Runtime error — re-run affected task |
| Missing UI element (snapshot fail) | /implement | Incomplete UI — re-run that component's task |
| Business logic wrong (manual TC fail) | /blueprint or /breakdown | Design or requirement gap |
| Requirement no longer valid | /breakdown or /clarify | Revisit requirements |

**Incremental redo principle:** Only re-do the affected chain. If R-003 changed and only T-005 and TC-008 were affected, only those need re-work. Everything else stays verified.

### Step 11: All Green — Complete

When everything passes:

> "All automated scans pass. All manual TCs verified. DevFlow cycle complete."

- All TC statuses updated to `done`
- All R statuses updated to `done`
- Suggest next: commit, push, deploy

## Handoff

After successful verification:

- Suggest git commit and push for any fixes made during verification
- Suggest PR creation if applicable
- No further DevFlow commands needed for this feature

If issues remain, handoff to the identified phase for re-work.

## Playwright MCP Tool Reference

This skill uses the following Playwright MCP tools. Ensure they are available before starting Phase 1:

| Tool | Purpose | Used In |
|------|---------|---------|
| `browser_navigate` | Navigate to a URL | Phase 1 all steps |
| `browser_console_messages` | Collect console output (filter for errors) | Step 3 |
| `browser_network_requests` | Retrieve all HTTP requests and status codes | Step 4 |
| `browser_snapshot` | Get accessibility tree / semantic DOM structure | Step 5, Step 6 |
| `browser_scroll` | Scroll the page by pixels or viewport | Step 5 |
| `browser_take_screenshot` | Capture visual screenshot (optional, for debugging) | On failure only |
