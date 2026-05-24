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

### Step 4: Execute Tasks

**Independent tasks (no dependencies):**
- Dispatch in parallel using sub-agents
- Each sub-agent gets: full task description, affected files, coding standards
- Each sub-agent follows TDD: write failing test → implement → verify → commit

**Dependent tasks (sequential dependencies):**
- Execute in dependency order
- Each task: TDD cycle → code review → commit
- Wait for dependencies to complete before starting

**Per-task quality gates:**
- TDD: test first, verify it fails, implement, verify it passes
- Code review: self-review the diff before committing
- Commit with descriptive message referencing T-xxx and R-xxx

### Step 5: Track Progress

Update `devflow/tasks.md` status fields as tasks complete:
- `pending` → `in_progress` → `done`

Report progress after each task.

## Handoff

After all tasks complete:

> "Implementation complete. All T-xxx tasks done. Next: /devflow:verify to run through the test case checklist and verify against requirements."

## Smart Rollback Awareness

- If user identifies an issue: determine if it's a task-level bug (re-run that task) or a design-level issue (suggest going back to `/devflow:blueprint`)
- If tasks.md needs updating: modify it and flag affected completed tasks for re-work
