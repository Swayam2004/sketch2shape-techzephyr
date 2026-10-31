@AGENTS.md

## Claude Code specifics

- Invoke the `unslop` skill before you write any document, README section, report fact, commit message, PR description or reply to the human. No exceptions, and that includes short chat replies. See "Writing rules" in `AGENTS.md`.
- Other skills for this repo live in `.claude/skills/` and load automatically. Useful ones are `diagnosing-bugs`, `tdd`, `research`, `code-review`, `domain-modeling` and `resolving-merge-conflicts`.
- Be concise. Show code, not paragraphs about the code. When you change something, explain why.
- Update `STATUS.md` before you end a session.
- Research output goes to `docs/research/` as Markdown with source URLs. Label claims verified, reported or unknown.
- Your own memory or personal global settings may differ from this file. This file wins for work in this repo.
