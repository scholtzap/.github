## 2026-10-20 — GitHub Pro so private repos can use branch rulesets
**Kind:** access
**Requested by:** agent (PR merge-gate handover)
**Pain:** `POST /repos/{owner}/{repo}/rulesets` returns 403 on private repositories. The user account and the 3BO-Track org are on the Free plan. Rulesets work on public repositories only until the plan changes.
**What would help:** GitHub Pro for `scholtzap` and GitHub Team for `3BO-Track`, then `bash scripts/apply-rulesets.sh --pr-gate-context "<observed pr-gate check name>"`.
**Where it should live:** this repo, `scripts/apply-rulesets.sh`
**Status:** open

## 2026-10-20 — Cursor Settings user-rules file is not on disk
**Kind:** tooling
**Requested by:** agent (PR rules handover)
**Pain:** Cursor User Rules in the Settings UI are not a file this session could patch. The same text was added as an always-on rule at `~/.cursor/rules/pr-rules.mdc`.
**What would help:** a documented local path or CLI for Cursor User Rules, so a handover can update that store without the settings UI.
**Where it should live:** `~/.cursor/rules/pr-rules.mdc` until a settings path exists
**Status:** open
