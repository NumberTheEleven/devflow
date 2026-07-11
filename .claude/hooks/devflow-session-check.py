#!/usr/bin/env python3
"""DevFlow Session Check — SessionStart hook for Claude Code.

Scans devflow/*/state.json for incomplete sessions.
Outputs JSON with hookSpecificOutput.additionalContext when active sessions found,
or empty {} when all sessions are complete.
"""

import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd()))


def find_active_sessions() -> list[dict]:
    """Scan devflow/*/state.json for incomplete sessions."""
    sessions = []
    devflow_dir = REPO_ROOT / "devflow"
    if not devflow_dir.is_dir():
        return sessions

    for state_file in sorted(devflow_dir.glob("*/state.json")):
        try:
            data = json.loads(state_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue

        phase = data.get("phase", "unknown")
        if phase == "completed":
            continue

        feature = data.get("feature", state_file.parent.name)
        isolation = data.get("isolation", {})
        mode = isolation.get("mode", "worktree")
        worktree_path = isolation.get("path", "unknown")

        sessions.append({
            "feature": feature,
            "mode": mode,
            "phase": phase,
            "path": worktree_path,
        })

    return sessions


def main() -> None:
    sessions = find_active_sessions()

    if not sessions:
        print("{}")
        return

    lines = []
    for s in sessions:
        lines.append(
            f"- **{s['feature']}** | mode: {s['mode']} "
            f"| phase: {s['phase']} | path: {s['path']}"
        )

    context = (
        "## DevFlow Active Sessions\n\n"
        "The following DevFlow sessions are **incomplete**. The user's Claude Code "
        "conversation history for these sessions lives in the worktree/feat-branch "
        "directory, NOT here in the main repo. The user likely cannot see or resume "
        "these sessions from Claude Code's session picker.\n\n"
        + "\n".join(lines)
        + "\n\n"
        "**Action (IMPORTANT):** Proactively tell the user about these sessions NOW. "
        "Say something like: '我发现有未完成的 DevFlow 会话，要切换进去继续吗？'\n"
        "If the user agrees, for worktree-mode: call EnterWorktree with the path above. "
        "For feat-branch/main-branch: run git checkout to the correct branch.\n"
        "This is the user's ONLY way to get back to their worktree session — "
        "Claude Code's /resume won't show sessions from other directories."
    )

    # Short visible message for the user in the UI
    session_list = ", ".join(s["feature"] for s in sessions)
    user_msg = (
        f"[DevFlow] {len(sessions)} incomplete session(s): {session_list}. "
        "Ask me to switch into the worktree."
    )

    output = {
        "systemMessage": user_msg,
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": context,
        },
    }
    print(json.dumps(output))


if __name__ == "__main__":
    main()
