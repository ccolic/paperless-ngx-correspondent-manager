# AGENTS.md - AI Assistant Onboarding Manual
*Last updated 2025-06-10*

> **purpose** – This file is the onboarding manual for every AI assistant (Claude, Cursor, GPT, etc.) and every human who edits this repository.

---

## 1. Non-negotiable golden rules

| #:  | AI *may* do                                                                                                                                                                       | AI *must NOT* do                                                                                                                                     |
| --- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| G-0 | Whenever unsure about something that's related to the project, ask the developer for clarification before making changes.                                                         | ❌ Write changes or use tools when you are not sure about something project specific, or if you don't have context for a particular feature/decision. |
| G-2 | Add/update **`AIDEV-NOTE:` anchor comments** near non-trivial edited code.                                                                                                        | ❌ Delete or mangle existing `AIDEV-` comments.                                                                                                       |
| G-3 | Follow lint/style configs (`pyproject.toml`, `.ruff.toml`, `.pre-commit-config.yaml`). Use the project's configured linter, if available, instead of manually re-formatting code. | ❌ Re-format code to any other style.                                                                                                                 |
| G-5 | Stay within the current task context. Inform the dev if it'd be better to start afresh.                                                                                           | ❌ Continue work from a prior prompt after "new task" – start a fresh session.                                                                        |

---

## 2. Coding standards

*   **Formatting**: Standard `ruff` linter and formatter rules.
*   **Typing**: Strict (Pydantic v2 models preferred); `from __future__ import annotations`.
*   **Naming**: `snake_case` (functions/variables), `PascalCase` (classes), `SCREAMING_SNAKE` (constants).
*   **Documentation**: Google-style docstrings for public functions/classes.
*   **Testing**: Separate test files matching source file patterns.
*   **Virtualenv**: Always run `pyenv activate` before running any commands to ensure the correct Python environment is used.

---

## 3. Anchor comments

Add specially formatted comments throughout the codebase, where appropriate, for yourself as inline knowledge that can be easily `grep`ped for.

### Guidelines:

- Use `AIDEV-NOTE:`, `AIDEV-TODO:`, or `AIDEV-QUESTION:` (all-caps prefix) for comments aimed at AI and developers.
- Keep them concise (≤ 120 chars).
- **Important:** Before scanning files, always first try to **locate existing anchors** `AIDEV-*` in relevant subdirectories.
- **Update relevant anchors** when modifying associated code.
- **Do not remove `AIDEV-NOTE`s** without explicit human instruction.
- Make sure to add relevant anchor comments, whenever a file or piece of code is:
  * too long, or
  * too complex, or
  * very important, or
  * confusing, or
  * could have a bug unrelated to the task you are currently working on.

Example:
```python
# AIDEV-NOTE: perf-hot-path; avoid extra allocations (see ADR-24)
async def render_feed(...):
    ...
```

---

## 4. Commit discipline

*   **Granular commits**: One logical change per commit.
*   **Tag AI-generated commits**: e.g., `feat: optimise feed query [AI]`.
*   **Clear commit messages**: Explain the *why*; link to issues/ADRs if architectural.
