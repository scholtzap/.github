# Architecture Overview
This document serves as a critical, living template designed to equip agents with a rapid and comprehensive understanding of the codebase's architecture, enabling efficient navigation and effective contribution from day one. Update this document as the codebase evolves.

## 1. Project Structure
This section provides a high-level overview of the project's directory and file structure, categorised by architectural layer or major functional area. It is essential for quickly navigating the codebase, locating relevant files, and understanding the overall organization and separation of concerns.

```
[scholtzap/.github]/
├── .github/
│   ├── PULL_REQUEST_TEMPLATE.md   # default PR template for repos without their own
│   └── workflows/
│       ├── pr-gate.yml            # reusable workflow_call gate
│       ├── pr-gate-caller.yml     # caller used by this repo's own PRs
│       └── ci.yml                 # trivial required check named ci
├── scripts/
│   ├── apply-rulesets.sh          # entry point
│   └── apply-rulesets.py          # gh api ruleset + auto-merge rollout
├── AGENTS.md
├── ARCHITECTURE.md
├── MISTAKES.md
├── WISHLIST.md
└── README.md
```

Ecosystem: behaviour in `AGENTS.md`; failures in `MISTAKES.md`; gaps in `WISHLIST.md`. No graphify graph and no `docs/plans/` queue.

## 2. High-Level System Diagram
Provide a simple block diagram (e.g., a C4 Model Level 1: System Context diagram, or a basic component diagram) or a clear text-based description of the major components and their interactions. Focus on how data flows, services communicate, and key architectural boundaries.

```
[PR in scholtzap/* or 3BO-Track/*]
        |
        v
[caller .github/workflows/pr-gate.yml]
        |
        v
[scholtzap/.github reusable workflow] -- reads github.event.pull_request.body
        |
        v
[check context pr-gate] --> [branch ruleset on the trunk] --> [squash auto-merge]
```

Org repositories do not inherit a personal account's default community health files, so `3BO-Track/.github` carries the same PR template.

## 3. Core Components
(List and briefly describe the main components of the system. For each, include its primary responsibility and key technologies used.)

### 3.1. Frontend

N/A — this repo has no frontend.

### 3.2. Backend Services

#### 3.2.1. pr-gate

Name: pr-gate

Description: Reusable GitHub Actions workflow. Fails when the PR description has no finish line, no board Task ID, or an unticked test-plan line without a follow-up issue.

Technologies: GitHub Actions, Python 3 on the runner

Deployment: GitHub-hosted `ubuntu-latest`, called via `workflow_call`

#### 3.2.2. ruleset rollout

Name: apply-rulesets

Description: Sets a trunk ruleset (PR required, squash only, no force-push, no delete) and turns on auto-merge. Requires the discovered CI job names plus the pr-gate check.

Technologies: `gh api`

Deployment: run locally; not a service

## 4. Data Stores

N/A — this repo stores no application data. GitHub is the system of record for workflows and rulesets.

### 4.1. N/A

Name: N/A

Type: N/A

Purpose: N/A

Key Schemas/Collections: N/A

### 4.2. N/A

Name: N/A

Type: N/A

Purpose: N/A

## 5. External Integrations / APIs

Service Name 1: GitHub REST (`gh api`)

Purpose: Read workflows, write rulesets, enable auto-merge and squash-only merges.

Integration Method: REST via the `gh` CLI. No secrets are stored in this repo.

## 6. Deployment & Infrastructure

Cloud Provider: GitHub

Key Services Used: Actions, repository rulesets, community health files

CI/CD Pipeline: `.github/workflows/ci.yml` (job name `ci`) and `.github/workflows/pr-gate-caller.yml`

Monitoring & Logging: GitHub Actions logs. No separate monitor.

## 7. Security Considerations

Authentication: `gh` user token on the operator machine. The workflow itself requests no secrets.

Authorization: Rulesets apply to admins as well (no bypass actor).

Data Encryption: GitHub in transit. The workflow reads only the pull request body.

Key Security Tools/Practices: Public repo on purpose so the reusable workflow can be called from other private repositories. Do not commit credentials here.

## 8. Development & Testing Environment

Local Setup Instructions: `gh auth status`, then `bash scripts/apply-rulesets.sh --dry-run`

Testing Frameworks: The proof is a throwaway pull request. `ci` echoes a line. `pr-gate` is exercised by editing the PR body.

Code Quality Tools: N/A

## 9. Future Considerations / Roadmap

Private-repository rulesets stay off until GitHub Pro (user) and Team (`3BO-Track`) are enabled. See `WISHLIST.md`. Re-run the ruleset script after that; do not make private repos public to unlock the feature.

## 10. Project Identification

Project Name: scholtzap/.github

Repository URL: https://github.com/scholtzap/.github

Primary Contact/Team: scholtzap

Date of Last Update: 2026-10-20

## 11. Glossary / Acronyms

pr-gate: The required status check that validates the PR description.

Task ID: Agent Projects Board id matching `PROJECT-TASK`.

merge-gate: The ruleset name this repo's script creates on each trunk.
