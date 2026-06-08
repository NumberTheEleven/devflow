---
name: implement
description: Execute implementation from the blueprint. First breaks down into numbered development tasks (T-001...), creates technical architecture diagrams (UML/swimlane/state machine), then dispatches parallel sub-agents for independent tasks and sequential TDD for dependent ones.
argument-hint: [implementation-notes]
allowed-tools: [Read, Write, Glob, Grep, Bash, Edit, Agent, TaskCreate, WebSearch]
---

# /devflow:implement — Implementation

## When to Use

The blueprint is ready (`devflow/design.md` and `devflow/test-cases.md` exist). You need to:
1. Break down into development tasks with file scoping
2. Create technical architecture documentation
3. Execute coding with sub-agents

You can also start here directly if you have an existing design.

## Process

### Step 1: Load Context

Read all existing DevFlow files:
- `devflow/requirements.md`
- `devflow/design.md`
- `devflow/test-cases.md`

If none exist, ask user for context or suggest starting from an earlier phase.

### Step 2: Task Breakdown (FIRST — Persist)

Break the blueprint into concrete development tasks:

- Each task gets ID: T-001, T-002, ...
- Each maps to requirement(s): R-xxx
- Identify dependencies between tasks
- Estimate complexity (low/medium/high)
- List likely files/modules affected
- Mark which tasks have NO dependencies (can be parallelized)

Present the task list. Ask user to confirm scope and file targeting.

Write to `devflow/tasks.md` using the template format.

### Step 3: Technical Architecture Documentation

Create appropriate technical diagrams in Mermaid format:

- **Data flow** → flowchart or data flow diagram
- **Multi-actor processes** → swimlane diagram
- **State changes** → state machine diagram
- **Entity relationships** → ER diagram
- **API design** → sequence diagram

Choose the diagram type(s) that best represent the technical design. Include in the architecture section of the conversation.

### Step 4: Production-Grade Baseline (CRITICAL)

**Default assumption: Every implementation targets production quality.** AI tends to produce demo-level code (hardcoded data, missing error states, no edge case handling) unless explicitly told otherwise. Before dispatching ANY task, establish this baseline:

Every piece of code must satisfy:
- **Error handling:** Every async operation, API call, file I/O, and user input path has explicit error handling. Errors are surfaced to the user in human-readable form, not swallowed or console-logged.
- **Edge cases:** Null/empty/undefined states are handled explicitly. Loading, empty, error, and success states are all represented in the UI. Boundary conditions (max length, timeout, rate limit) are handled.
- **Data integrity:** No hardcoded magic values, no fake/stub data in production paths. Configuration comes from environment variables or config files. Database queries have proper constraints and indexes.
- **UI completeness:** Every interactive element has hover, focus, disabled, and active states. Forms have validation feedback. Destructive actions have confirmation. Empty states have helpful guidance, not blank screens.
- **Observability:** Key operations are logged with enough context to debug in production. Errors include stack traces or diagnostic information.
- **Security:** User input is validated and sanitized. SQL queries use parameterized statements. Sensitive data is never logged or exposed client-side. Authentication and authorization checks are in place.

**This baseline applies to ALL implementation tasks.** Even if the user says "just a quick prototype" or "simple demo," default to production quality for the parts that ARE implemented. A prototype with solid foundations is better than one that needs a full rewrite.

### Step 5: Execute Tasks

**Independent tasks (no dependencies):**
- Dispatch in parallel using sub-agents
- Each sub-agent gets: full task description, affected files, coding standards, AND the Production-Grade Baseline from Step 4
- Each sub-agent follows TDD: write failing test → implement → verify → commit

**Dependent tasks (sequential dependencies):**
- Execute in dependency order
- Each task: TDD cycle → code review → commit
- Wait for dependencies to complete before starting

**Per-task quality gates:**
- TDD: test first, verify it fails, implement, verify it passes
- Production-grade check: verify the implementation satisfies the Step 4 baseline (error handling, edge cases, UI completeness, etc.)
- Code review: self-review the diff before committing
- Commit with descriptive message referencing T-xxx and R-xxx

### Step 6: Track Progress

Update `devflow/tasks.md` status fields as tasks complete:
- `pending` → `in_progress` → `done`

Report progress after each task.

## Handoff

After all tasks complete:

> "Implementation complete. All T-xxx tasks done. Next: /devflow:verify to run through the test case checklist and verify against requirements."

## Smart Rollback Awareness

- If user identifies an issue: determine if it's a task-level bug (re-run that task) or a design-level issue (suggest going back to `/devflow:blueprint`)
- If tasks.md needs updating: modify it and flag affected completed tasks for re-work
