---
name: breakdown
description: Break down clear requirements into a numbered, trackable checklist. Each requirement gets an ID (R-001, R-002...), priority, dependencies, and acceptance criteria. Output is persisted to devflow/requirements.md.
argument-hint: [requirements-description]
---

# /devflow:breakdown — Requirements Breakdown

## When to Use

You have clear requirements — either from `/devflow:clarify` output, or you already have a well-defined PRD or requirements document. You can also start directly from this command if you already know what you want.

## Process

### Step 1: Load Existing State

Check if `devflow/requirements.md` exists. If it does, read it — we may be updating an existing breakdown.

### Step 2: Decompose Requirements

Break down the requirement into discrete, verifiable sub-requirements:

- Each sub-requirement = one numbered item (R-001, R-002, ...)
- Each gets a clear title and one-sentence description
- Assign priority: **P0** (must have), **P1** (should have), **P2** (nice to have)
- Mark dependencies: which other requirements must be completed first
- Each must have measurable acceptance criteria (checkbox format)

**Production-quality requirements:** By default, include requirements that prevent demo-level gaps. Unless the user explicitly says otherwise, add:
- Error handling for all external dependencies (API calls, file I/O, user input)
- Complete UI state coverage: loading, empty, error, success, and edge cases
- Input validation and sanitization
- Basic logging for key operations
- These can be P1/P2 if the core functionality is P0, but they MUST appear in the checklist rather than being silently omitted

### Step 3: Present for Confirmation

Show the complete numbered list to the user:

```
## Requirements Checklist

R-001 | P0 | [Title] | depends: none
  Description: ...
  Accept: - [ ] criterion 1
          - [ ] criterion 2

R-002 | P1 | [Title] | depends: R-001
  ...
```

Ask user to confirm the breakdown, adjust priorities, or add/remove items.

### Step 4: Persist to File

Write to `devflow/requirements.md`:

- Create `devflow/` directory if it doesn't exist
- Use the template from `skills/breakdown/references/requirements-template.md`
- Fill in actual requirement data
- Set all statuses to `pending`

The file MUST follow the template format exactly — it will be read by downstream skills (`/devflow:blueprint`, `/devflow:verify`).

### Step 5: Confirm Persistence

Read back `devflow/requirements.md` to confirm it was written correctly. Show a summary to the user:

> "Requirements checklist saved to `devflow/requirements.md` with N items (R-001 to R-xxx)."

## Handoff

Ask the user:

> "Requirements locked. Next: /devflow:blueprint to create the solution design, business flow diagrams, and test cases. Or do you need to adjust anything?"

## Smart Rollback Awareness

If the user says anything like "requirement X is wrong" or "we need to change R-003":
- Update `devflow/requirements.md` with the change
- If any downstream files exist (`design.md`, `tasks.md`, `test-cases.md`), flag that affected items in those files may need re-validation
- Do NOT automatically modify downstream files — let the user re-run the relevant commands
