# DevFlow — AI Development Workflow

DevFlow is a structured AI-driven development workflow skill for Claude Code. It guides feature development through 6 phases: clarify, breakdown, blueprint, implement, verify, and completion. Supports git worktree, feature branch, and main branch isolation modes.

## Session Recovery (Important)

**At the start of every session in this repository**, check for incomplete DevFlow sessions:

1. Scan `devflow/*/state.json` for any file where `phase` is not `"completed"`
2. If incomplete sessions are found, **proactively inform the user** and offer to reconnect:
   > "我发现有一个未完成的 DevFlow 会话：**<feature>**（阶段：<phase>，模式：<mode>）。要切换进去继续吗？"
3. If the user agrees, **immediately call `EnterWorktree`** (for worktree mode) or `git checkout` (for feat/main mode) to reconnect them — do NOT just tell them to run `/devflow`
4. For **worktree-mode** sessions: call `EnterWorktree path="<isolation.path>"`
5. For **feat-branch / main-branch** sessions: run `git checkout <branch>` and stay in the current directory
6. Once reconnected, read `devflow/<feature>/state.json` to resume at the correct phase

This check is also performed automatically by the `SessionStart` hook in `.claude/settings.json`.

## Project Structure

- `skills/devflow/` — DevFlow skill entry point (loaded by plugin)
- `internal/skills/` — Phase implementations (clarify, breakdown, blueprint, implement, verify)
- `devflow/<feature>/` — Per-feature session tracking files (state.json, requirements.md, design.md, etc.)
- `.claude/hooks/` — Session hooks (devflow-session-check.py)
