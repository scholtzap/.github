# Agent instructions

This repo holds the shared PR template and the reusable `pr-gate` workflow. Product code does not live here.

## PR rules (Arno)

- Every task has a finish line. If I didn't give one, ask "Done when?" with 3-5 options before starting.
- Every PR description starts with "Done when: ..." and has a "Task: <ID>" line with the Agent Projects Board Task ID. If there's no board row, create one (sheet 16ApeiYY7SH4HOuzb_w8yC7z7ZbpIcqvYa2WWWuaQbgE, Tasks tab, Org = Plentify | scholtzap | Both) and put the PR URL in it.
- Tick each test-plan item only with real evidence. For anything you can't verify, open a follow-up issue and write "follow-up: #N" on that line.
- Never push to main. Open a PR, enable auto-merge (`gh pr merge --auto --squash`), and let required CI decide.
- When the PR is open, send it to the Code Review bot. If you can't reach it, leave it to auto-merge and update the board row.
- Picking up work: when asked to pick up work, take the highest-score Status=Ready row on the board for this repo, set it to In progress with your name, and follow its Done when.

## Commands

- Re-apply branch rulesets: `bash scripts/apply-rulesets.sh --pr-gate-context "<check name>"`
- Map: `ARCHITECTURE.md`
