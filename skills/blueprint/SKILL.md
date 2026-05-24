---
name: blueprint
description: Create the solution blueprint from a requirements checklist. Produces business process flowcharts (Mermaid), spec boundaries with Non-Goals, and a numbered test case checklist (TC-001...).
argument-hint: [design-notes]
allowed-tools: [Read, Write, Glob, Bash, WebSearch, TaskCreate]
---

# /devflow:blueprint — Solution Blueprint

## When to Use

Requirements are locked in `devflow/requirements.md`. You need to create:
1. Business process flowchart (non-technical readable)
2. Specification boundaries and standards
3. Numbered test case checklist

You can also start here directly if you already have requirements and a design in mind.

## Process

### Step 1: Load Requirements

Read `devflow/requirements.md`. If it doesn't exist, ask the user to run `/devflow:breakdown` first, or describe the requirements now.

### Step 2: Business Process Flowchart (FIRST)

**Why first:** The business flow must be confirmed before defining specs. If the flow doesn't match user expectations, everything else is wasted.

Create a Mermaid flowchart describing the business process:

- Use user-facing language, not technical jargon
- Show actors, actions, decisions, and outcomes
- Keep it at a level non-technical stakeholders can understand
- Use swimlanes if multiple actors/roles are involved

Present the flowchart and ask:

> "Does this business flow match your understanding? Any steps missing or incorrect?"

Iterate until the user confirms.

### Step 3: Spec Boundaries & Standards (SECOND)

Based on the confirmed flowchart:

- **In Scope:** What this implementation covers
- **Out of Scope (Non-Goals):** What is explicitly excluded — equally important
- **Technical Standards:** Coding conventions, architecture constraints, technology choices
- **Design Decisions:** Key choices with rationale and alternatives considered
- **Risks & Mitigations:** What could go wrong and how to handle it

### Step 4: Test Case Checklist (THIRD)

For each requirement in `devflow/requirements.md`, define test cases:

- Each test case gets a unique ID (TC-001, TC-002, ...)
- Each maps back to a requirement ID (R-xxx)
- Type: unit / integration / e2e / manual
- Clear steps and expected results
- Status field for tracking during verification

### Step 5: Persist Both Files

Write `devflow/design.md` using the design template format.
Write `devflow/test-cases.md` using the test cases template format.

Verify both files were written correctly.

## Handoff

> "Blueprint complete. devflow/design.md and devflow/test-cases.md saved. Next: /devflow:implement to break down into development tasks and start coding."

## Smart Rollback Awareness

If user says the design or test cases need changes:
- Update the relevant file(s)
- If design changes affect downstream (tasks or code), flag for re-validation
- Suggest re-running `/devflow:implement` for affected tasks
