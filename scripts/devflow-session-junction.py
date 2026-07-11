#!/usr/bin/env python3
"""
DevFlow — Claude Code Project Directory Junction Manager

Ensures Claude Code sessions from a git worktree are stored in the main
repository's project directory instead of a separate worktree project directory.

Usage:
  python devflow-session-junction.py create <main-repo-path> <worktree-path>
  python devflow-session-junction.py remove <main-repo-path> <worktree-path>

How it works:
  1. Claude Code stores sessions in ~/.claude/projects/<sanitized-path>/
  2. By default, a worktree gets its OWN project directory (separate /resume list)
  3. This script replaces the worktree's project directory with a junction
     pointing to the main repo's project directory
  4. Result: all sessions — main repo AND worktree — land in the same place
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


def get_claude_projects_dir() -> Path:
    """Get the ~/.claude/projects/ directory path."""
    home = Path(os.environ.get("USERPROFILE", os.path.expanduser("~")))
    return home / ".claude" / "projects"


def sanitize_path(path: str) -> str:
    """
    Convert a filesystem path to Claude Code's project directory name.
    Claude Code replaces path separators with '--' and colons with something similar.

    Examples:
      D:\codingProjects\devflow → D--codingProjects-devflow
      D:\codingProjects\devflow\.claude\worktrees\devflow-xxx
        → D--codingProjects-devflow--claude-worktrees-devflow-xxx
    """
    # Normalize: absolute path, backslashes to forward, lowercase drive letter
    abs_path = os.path.abspath(path)
    # Replace backslashes with hyphens, colons already handled
    sanitized = abs_path.replace("\\", "-").replace(":", "")
    return sanitized


def is_junction(path: Path) -> bool:
    """Check if a path is a directory junction (Windows)."""
    if not path.exists():
        return False
    try:
        # A junction is a reparse point
        if sys.platform == "win32":
            import ctypes
            FILE_ATTRIBUTE_REPARSE_POINT = 0x0400
            attrs = ctypes.windll.kernel32.GetFileAttributesW(str(path))
            return attrs != -1 and bool(attrs & FILE_ATTRIBUTE_REPARSE_POINT)
    except Exception:
        pass
    return False


def create_junction(source: Path, target: Path) -> None:
    """Create a directory junction: source → target (source points to target)."""
    if sys.platform == "win32":
        # Use mklink /J — directory junctions work without admin privileges
        result = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(source), str(target)],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            raise OSError(f"Failed to create junction: {result.stderr.strip()}")
    else:
        # Unix: regular symlink
        source.symlink_to(target, target_is_directory=True)


def remove_junction(source: Path) -> None:
    """Remove a directory junction or symlink."""
    if sys.platform == "win32":
        # rmdir works for junctions (not del, which would follow the junction)
        subprocess.run(
            ["cmd", "/c", "rmdir", str(source)],
            capture_output=True, text=True,
        )
    else:
        source.unlink()


def create(main_repo: str, worktree: str) -> int:
    """Create a junction from worktree project dir → main repo project dir."""
    projects_dir = get_claude_projects_dir()
    main_name = sanitize_path(main_repo)
    wt_name = sanitize_path(worktree)

    main_dir = projects_dir / main_name
    wt_dir = projects_dir / wt_name

    if not main_dir.exists():
        print(f"[DevFlow] Main repo project dir does not exist yet: {main_dir}")
        print(f"[DevFlow] Junction will be created when Claude Code first writes sessions.")

    # If the worktree project dir is already a junction, nothing to do
    if is_junction(wt_dir):
        print(f"[DevFlow] Junction already exists: {wt_name} → {main_name}")
        return 0

    # If the worktree project dir exists as a real directory, migrate its
    # contents to the main repo project dir first
    if wt_dir.exists() and wt_dir.is_dir():
        print(f"[DevFlow] Migrating existing worktree sessions to main repo project...")
        main_dir.mkdir(parents=True, exist_ok=True)
        for item in wt_dir.iterdir():
            dest = main_dir / item.name
            if not dest.exists():
                shutil.move(str(item), str(dest))
                print(f"  Moved: {item.name} → {main_name}/")
            else:
                print(f"  Skipped (already exists): {item.name}")
        # Remove the now-empty real directory
        wt_dir.rmdir()
        print(f"[DevFlow] Removed real dir: {wt_name}")

    # Create the junction
    main_dir.mkdir(parents=True, exist_ok=True)
    create_junction(wt_dir, main_dir)
    print(f"[DevFlow] Junction created: {wt_name} → {main_name}")
    return 0


def remove(main_repo: str, worktree: str) -> int:
    """Remove a previously created junction."""
    projects_dir = get_claude_projects_dir()
    wt_name = sanitize_path(worktree)
    wt_dir = projects_dir / wt_name

    if is_junction(wt_dir):
        remove_junction(wt_dir)
        print(f"[DevFlow] Junction removed: {wt_name}")
    elif wt_dir.exists():
        print(f"[DevFlow] NOT removing real directory: {wt_name} (may have concurrent sessions)")
    else:
        print(f"[DevFlow] Nothing to remove: {wt_name} does not exist")
    return 0


def main() -> int:
    if len(sys.argv) != 4:
        print(f"Usage: {sys.argv[0]} create|remove <main-repo-path> <worktree-path>")
        return 1

    action = sys.argv[1]
    main_repo = sys.argv[2]
    worktree = sys.argv[3]

    if action == "create":
        return create(main_repo, worktree)
    elif action == "remove":
        return remove(main_repo, worktree)
    else:
        print(f"Unknown action: {action}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
