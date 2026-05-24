---
name: verify
description: Verify implementation against the test case checklist (TC-xxx) and requirements (R-xxx). Runs through every item systematically. Failed items trigger smart rollback — AI identifies which phase to return to for fixes.
argument-hint: [verification-scope]
allowed-tools: [Read, Glob, Grep, Bash, Edit, TaskCreate]
---

# /devflow:verify — Verification

## When to Use

Implementation is complete. All development tasks in `devflow/tasks.md` are marked done. You need to systematically verify everything works as specified.

## Process

### Step 1: Load All Tracking Files

Read all DevFlow state files:
- `devflow/requirements.md` — what we promised to build
- `devflow/design.md` — the spec and scope
- `devflow/tasks.md` — what was implemented
- `devflow/test-cases.md` — the verification checklist

### Step 2: Verify Test Cases

Go through every test case in `devflow/test-cases.md`:

For each TC-xxx:
- Run the test if it's automated
- Manually verify if it's a manual test
- Mark status: `done` if passing, leave `pending` if not checked

For failed test cases:
- Identify which requirement (R-xxx) and task (T-xxx) it relates to
- Determine the root cause:
  - **Implementation bug** → suggest re-running the specific task in `/devflow:implement`
  - **Design issue** → suggest going back to `/devflow:blueprint` to fix the spec
  - **Requirement gap** → suggest going back to `/devflow:breakdown` or `/devflow:clarify`

### Step 3: Verify Requirements

Go through every requirement in `devflow/requirements.md`:

For each R-xxx:
- Does the implemented code actually satisfy the acceptance criteria?
- Is there test coverage (TC-xxx) that proves it works?
- Mark status: `done` if fully satisfied, leave as-is if not

### Step 4: Smart Rollback (When Issues Found)

When issues are found, classify them:

| User Feedback / Finding | Root Phase | Action |
|------------------------|------------|--------|
| "This requirement is wrong" | /clarify → /breakdown | Revisit requirements, update R-xxx |
| "The design doesn't handle X" | /blueprint | Fix spec, re-derive affected tasks |
| "This task has a bug" | /implement | Re-run specific T-xxx |
| "Test case is incorrect" | /blueprint | Update TC-xxx |

**Incremental redo principle:** Only re-do the affected chain. If R-003 changed and only T-005 and TC-008 were affected, only those need re-work. Everything else stays verified.

### Step 5: Generate Verification Report

```markdown
## DevFlow Verification Report

**Date:** YYYY-MM-DD

### Test Cases
- TC-001 ✅ | TC-002 ✅ | TC-003 ❌ (see below)
- Pass rate: X/Y (Z%)

### Requirements
- R-001 ✅ | R-002 ✅ | R-003 ✅
- Completion: X/Y (Z%)

### Issues Found
1. TC-003 failed: [description]
   - Root cause: [analysis]
   - Recommended action: /devflow:implement T-003
```

### Step 6: All Green — Complete

When everything passes:

> "All test cases pass. All requirements met. DevFlow cycle complete."

- All statuses in all files should be `done`
- Suggest next steps: commit, push, deploy, etc.
- The DevFlow cycle is now closed

## Handoff

After successful verification, the DevFlow cycle is complete. Suggest:
- Git commit and push
- PR creation if applicable
- No further DevFlow commands needed for this feature

If issues remain, the handoff is to the identified phase for re-work.
