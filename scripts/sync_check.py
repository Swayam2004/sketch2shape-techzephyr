"""Read-only repo sync report for agents. Run at the start and end of every session.

It never changes anything. It fetches, then prints what the agent must do before new work.
"""

from __future__ import annotations

import shutil
import subprocess
import sys


def run(*args: str) -> str:
    result = subprocess.run(args, capture_output=True, text=True, check=False)
    return (result.stdout + result.stderr).strip()


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    if run("git", "rev-parse", "--is-inside-work-tree") != "true":
        print("Not inside a git repo.")
        return 1

    print("== git fetch origin")
    print(run("git", "fetch", "origin", "--prune") or "ok")

    print("\n== branch status")
    print(run("git", "status", "-sb"))

    behind = run("git", "rev-list", "--count", "HEAD..origin/main")
    dirty = run("git", "status", "--porcelain")
    conflicts = run("git", "diff", "--name-only", "--diff-filter=U")

    if behind.isdigit() and int(behind) > 0:
        print(f"\n== {behind} commit(s) on origin/main that you do not have")
        print(run("git", "log", "--oneline", "HEAD..origin/main"))
        print(run("git", "diff", "--stat", "HEAD...origin/main"))

    if shutil.which("gh"):
        print("\n== open pull requests")
        print(
            run(
                "gh", "pr", "list", "--state", "open", "--json", "number,title,author",
                "--template",
                "{{range .}}#{{.number}} {{.author.login}} {{.title}}{{\"\\n\"}}{{end}}",
            )
            or "none"
        )

    print("\n== ACTION REQUIRED")
    actions: list[str] = []
    if conflicts:
        actions.append("Merge conflicts in:\n" + conflicts + "\nResolve them first.")
    if dirty:
        actions.append("Uncommitted changes. Commit or stash them before pulling.")
    if behind.isdigit() and int(behind) > 0:
        actions.append(
            "Pull origin/main (rebase if on a feature branch), resolve conflicts, then read "
            "the new commits and STATUS.md before you start new work. If uv.lock or "
            "pyproject.toml changed, run `uv sync`."
        )
    print("\n".join(actions) if actions else "Nothing. You are up to date. Read STATUS.md and go.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
