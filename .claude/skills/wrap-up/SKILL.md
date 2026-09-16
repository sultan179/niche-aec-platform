---
name: wrap-up
description: Session handoff for the Niche AEC project. Updates docs/state.md, docs/decisions.md, and docs/evidence/, then commits docs. Use when Sultan says "wrap up" or "change" as a standalone command.
---

# Wrap-up (session handoff)

Goal: the next session, possibly on a different model, can continue from the repo files alone.

1. **Review this session.** List the new facts (with sources), approved decisions, evidence, open questions, risks, finished work, and the next actions.
2. **Update `docs/state.md`.**
   - Replace outdated lines instead of appending. Keep the file under about 80 lines.
   - Update the `Updated:` date.
   - Keep these sections: phase and objective, known facts, validated decisions, open questions, active risks, evidence collected, next decision gate, next actions.
3. **Update `docs/decisions.md`** only for decisions Sultan explicitly approved. Use the next D-number and the format ID · date · status · evidence · options · chosen · why · rejected · plan impact.
4. **Add new evidence** to `docs/evidence/` (for example `ifc-test-results.md`). Label each item FACT or HYPOTHESIS.
5. **Don't touch `docs/plan.md`.** If it needs a change, list the proposal for Sultan instead.
6. **Check for confidential files:** run `git status`, and make sure nothing from `data/` or any `*.ifc` / `*.rvt` file is staged.
7. **Commit the docs only:** `git add docs && git commit -m "handoff: <YYYY-MM-DD> <one-line summary>"`.
8. **Report to Sultan in 2–3 lines:** what changed, the next action, and any decision waiting on him.
