---
paths:
  - "tools/**"
  - "src/**"
  - "tests/**"
---

# Coding guidelines (loads automatically when working on code)

**Tradeoff:** these guidelines favor caution over speed. For trivial tasks, use judgment.

---

## 1. Think before coding

Don't assume. Don't hide confusion. Surface tradeoffs.

Before implementing:

- State your assumptions explicitly. If you're uncertain, ask.
- If there are several interpretations, present them. Don't pick one silently.
- If a simpler approach exists, say so. Push back when it's warranted.
- If something is unclear, stop, name what's confusing, and ask.

## 2. Simplicity first

Write the minimum code that solves the problem. Nothing speculative.

- No features beyond what was asked.
- No abstractions for code used once.
- No "flexibility" or "configurability" that nobody requested.
- No error handling for impossible scenarios.
- If you wrote 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical changes

Touch only what you must, and clean up only your own mess.

When editing existing code:

- Don't "improve" nearby code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match the existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it. Don't delete it.

When your changes leave things unused:

- Remove imports, variables, and functions that **your** changes made unused.
- Don't remove dead code that was already there unless asked.

**Test:** every changed line should trace directly to the user's request.

## 4. Goal-driven execution

Define success criteria, and keep working until they are verified.

Turn tasks into goals you can check:

- "Add validation" → "Write tests for invalid inputs, then make them pass."
- "Fix the bug" → "Write a test that reproduces it, then make it pass."
- "Refactor X" → "Make sure the tests pass before and after."

For multi-step tasks, state a brief plan:

```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you work through a task on your own. Weak ones ("make it work") mean constant clarification.

---

## Precedence for this project

- The safety mechanisms in `docs/CLAUDE_INSTRUCTIONS.md` are **required features, not speculative complexity**. "Simplicity first" never removes them:
  - worksharing checks
  - Change Contract concurrency check
  - audit events
  - verification after each change
  - human approval
- "No error handling for impossible scenarios" does **not** cover external systems. Failures from Revit, SAFI, IFC, files, or the database are *possible* and must be handled.
- If these guidelines conflict with `docs/plan.md`, the plan wins. Report the conflict (Instructions §23).
