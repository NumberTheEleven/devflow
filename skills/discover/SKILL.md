---
name: discover
description: Scan the current project for optimization opportunities when you have no specific requirement in mind. Discover improvement areas in performance, architecture, maintainability, or feature gaps.
argument-hint: [project-path]
allowed-tools: [Read, Glob, Grep, Bash, TaskCreate]
---

# /devflow:discover — Project Discovery

## When to Use

You have NO specific requirement or task in mind. You want to find out what could be improved in the current project. This skill scans the codebase and generates a prioritized list of optimization opportunities.

**This skill is invoked directly by the user.** Do NOT auto-trigger.

## Process

### Step 1: Understand the Project

If `[project-path]` is provided, scope all scanning to that directory. Otherwise use the current working directory.

Read key project files to understand structure:
- `package.json` / `pyproject.toml` / `go.mod` / `Cargo.toml` / `build.gradle` (whichever exists)
- `README.md` or `CONTRIBUTING.md`
- Top-level directory structure

### Step 2: Scan for Opportunities

Run these analyses:

**Code Quality:**
- Find large files (>500 lines) using Glob to locate source files, then check line counts
- Find files with high complexity: look for deeply nested `if`/`for`/`while` blocks, functions exceeding ~50 lines, excessive branching

**Architecture:**
- Identify circular dependencies or tightly coupled modules
- Check for missing separation of concerns (e.g., business logic in UI files)
- Look for duplicated code patterns across files

**Maintainability:**
- Missing tests: compare `src/` files against `test/` or `__tests__/` files
- Missing or outdated documentation
- TODO/FIXME/HACK comments: use the Grep tool to search for `TODO|FIXME|HACK` across source files
- Deprecated API usage

**Performance:**
- N+1 query patterns
- Missing caching layers
- Synchronous operations that could be parallelized

**Security:**
- Hardcoded secrets, tokens, or credentials in source files
- Outdated dependencies with known CVEs (check dependency files)
- Unsafe input handling or missing sanitization

**Feature Gaps:**
- Missing error handling or edge case coverage
- Missing input validation
- Missing logging/observability

### Step 3: Generate Prioritized Report

Format the output as a structured report:

```markdown
## Project Optimization Opportunities

### Critical (P0)
- [ ] **[Category]** Description of issue. Affected files: `path/file.ts`. Suggested fix: ...

### High (P1)
- [ ] ...

### Medium (P2)
- [ ] ...

### Low (P3)
- [ ] ...
```

Each item must include:
- Priority (P0-P3)
- Category (Performance / Architecture / Maintainability / Feature Gap / Security)
- Clear description of the problem
- Specific file paths affected
- Concrete suggested approach to fix

### Step 4: Ask User to Choose

After presenting the report, ask the user to select one or more items to pursue. Then suggest:

> "Choose an item to work on. I recommend starting from the P0 items. Once selected, we'll use /devflow:clarify to expand on the requirement."

## Handoff

When the user selects an item, suggest:
- `/devflow:clarify` — to expand the selected optimization into a clear requirement

Do NOT automatically invoke clarify. Wait for the user to confirm.
