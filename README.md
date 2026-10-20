# scholtzap/.github

Default pull request template and the reusable `pr-gate` workflow for `scholtzap/*` and `3BO-Track/*`.

This repository is public so a personal account can share the reusable workflow, and so GitHub applies the template to personal repositories that do not have their own.

## What pr-gate checks

The job `pr-gate` fails the pull request when any of these are true:

- the first non-empty line of the description does not start with `Done when:`
- no `Task:` line contains a board Task ID (`PROJECT-TASK`)
- a line contains `- [ ]` without `follow-up: #<number>` on that same line

The placeholder example `e.g. 3BO-OFFLINE-CLASS` does not count as a Task ID.

## Caller

Each repository has `.github/workflows/pr-gate.yml` which calls this workflow:

```yaml
jobs:
  pr-gate:
    uses: scholtzap/.github/.github/workflows/pr-gate.yml@main
```

## Rulesets

The check name on a pull request is `pr-gate / pr-gate` (caller job / called job). Pass that to the ruleset script:

```bash
bash scripts/apply-rulesets.sh --pr-gate-context "pr-gate / pr-gate"
```

The script skips archived repositories and repositories with no pull_request CI job. Private repositories on the GitHub Free plan cannot use rulesets; the script records that and continues. Re-run it after GitHub Pro (user) and Team (3BO-Track) are enabled.

Agents merge with `gh pr merge --auto --squash`.
