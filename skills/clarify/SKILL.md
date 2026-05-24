---
name: clarify
description: Expand and align on a vague requirement through structured dialogue. Explore user intent, constraints, and success criteria. Propose alternative approaches with trade-offs.
argument-hint: <rough-idea>
allowed-tools: [Read, Glob, Grep, Bash, WebSearch, TaskCreate]
---

# /devflow:clarify — Requirements Clarification

## When to Use

You have a rough idea or vague requirement. It might come from:
- A `/devflow:discover` optimization item you selected
- A feature idea you want to explore
- A problem statement that needs refinement

## Process

### Step 1: Restate the Idea

Restate what you understand in 1-2 sentences. Ask for confirmation before proceeding.

### Step 2: Explore Through Dialogue

Ask questions ONE AT A TIME. Each question should deepen understanding:

**Key dimensions to explore:**
- **Purpose:** What problem does this solve? Who benefits?
- **Constraints:** Any technical, time, or resource constraints?
- **Success criteria:** How will we know this is done and done well?
- **Scope:** What's in scope? What's explicitly NOT in scope?
- **Users:** Who are the end users? What's their workflow?
- **Existing code:** Any relevant parts of the codebase to be aware of?

**Dialogue rules:**
- One question per turn
- Prefer multiple choice when options are clear
- Open-ended is fine when exploring
- After 3-4 questions, summarize what you've learned and confirm

### Step 3: Propose 2-3 Approaches

Once the requirement is clear enough, propose 2-3 approaches:

```markdown
## Approaches

### Approach A: [Name]
**How:** [1-2 sentences]
**Pros:** ...
**Cons:** ...

### Approach B: [Name]
**How:** [1-2 sentences]
**Pros:** ...
**Cons:** ...

### Recommendation
[Which approach and why]
```

Lead with your recommended approach and explain why.

### Step 4: Converge to Clear Requirements

After the user selects an approach, produce a clear requirements summary:

```markdown
## Clarified Requirements

**Goal:** [One sentence]

**What:**
- Requirement 1
- Requirement 2
- ...

**What NOT to do:**
- Non-goal 1
- Non-goal 2

**Success Criteria:**
- Criterion 1
- Criterion 2

**Constraints:**
- Constraint 1
```

## Handoff

Once requirements are clear and user confirms, suggest:
- `/devflow:breakdown` — to break these requirements into a numbered, trackable checklist

Do NOT automatically invoke breakdown. Wait for the user to confirm.
