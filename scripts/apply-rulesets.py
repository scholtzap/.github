#!/usr/bin/env python3
"""Apply main-branch merge gates for scholtzap and 3BO-Track.

Uses `gh api` only. Skips archived repos and repos whose workflows never
run on pull_request. Private repos on the free plan return 403; those rows
are reported and left unchanged.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys

OWNERS = ("scholtzap", "3BO-Track")
TRUNK_NAMES = {"main", "master", "trunk"}
RULESET_NAME = "merge-gate"


def gh(path: str, method: str | None = None, payload: dict | None = None):
    cmd = ["gh", "api"]
    if method:
        cmd.extend(["--method", method])
    cmd.append(path)
    raw = None
    if payload is not None:
        cmd.extend(["--input", "-"])
        raw = json.dumps(payload)
    result = subprocess.run(cmd, input=raw, text=True, capture_output=True)
    body = (result.stdout or "").strip()
    parsed = None
    if body:
        try:
            parsed = json.loads(body)
        except json.JSONDecodeError:
            parsed = body
    return result.returncode, parsed, (result.stderr or "").strip()


def list_repos_paginated(owner: str) -> list[dict]:
    result = subprocess.run(
        [
            "gh",
            "repo",
            "list",
            owner,
            "--limit",
            "200",
            "--json",
            "name,isArchived,isPrivate,defaultBranchRef",
        ],
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        print(result.stderr or result.stdout, file=sys.stderr)
        return []
    repos = []
    for repo in json.loads(result.stdout):
        ref = repo.get("defaultBranchRef") or {}
        repos.append(
            {
                "name": repo["name"],
                "archived": repo.get("isArchived"),
                "private": repo.get("isPrivate"),
                "default_branch": ref.get("name") or "main",
            }
        )
    return repos


def file_text(repo: str, path: str, ref: str) -> str | None:
    code, parsed, _err = gh(f"repos/{repo}/contents/{path}?ref={ref}")
    if code != 0 or not isinstance(parsed, dict) or "content" not in parsed:
        return None
    import base64

    return base64.b64decode(parsed["content"]).decode("utf-8", errors="replace")


def list_workflows(repo: str, ref: str) -> list[str]:
    code, parsed, _err = gh(f"repos/{repo}/contents/.github/workflows?ref={ref}")
    if code != 0 or not isinstance(parsed, list):
        return []
    return [item["name"] for item in parsed if item.get("name", "").endswith((".yml", ".yaml"))]


def triggers_pull_request(text: str) -> bool:
    lines = text.splitlines()
    start = None
    for index, line in enumerate(lines):
        if re.match(r"^on:\s*", line):
            start = index
            break
    if start is None:
        return False
    block = []
    for line in lines[start + 1 :]:
        if line and not line.startswith(" ") and not line.startswith("\t") and not line.startswith("#"):
            break
        block.append(line)
    header = lines[start]
    blob = header + "\n" + "\n".join(block)
    return "pull_request" in blob


def pr_job_names(text: str) -> tuple[list[str], list[str]]:
    """Return (required job contexts, notes) for a workflow file."""
    notes: list[str] = []
    if not triggers_pull_request(text):
        return [], notes
    lines = text.splitlines()
    start = None
    for index, line in enumerate(lines):
        if re.match(r"^jobs:\s*$", line):
            start = index + 1
            break
    if start is None:
        return [], notes
    jobs: list[tuple[str, list[str]]] = []
    current: tuple[str, list[str]] | None = None
    for line in lines[start:]:
        if line and not line.startswith(" ") and not line.startswith("#"):
            break
        match = re.match(r"^  ([A-Za-z0-9_-]+):\s*$", line)
        if match:
            current = (match.group(1), [])
            jobs.append(current)
            continue
        if current is not None:
            current[1].append(line)
    required: list[str] = []
    for job_id, body in jobs:
        joined = "\n".join(body)
        if re.search(r"^    uses:\s*", joined, flags=re.M):
            notes.append(f"{job_id} is a reusable-workflow caller")
            continue
        if_line = ""
        for line in body:
            match = re.match(r"^    if:\s*(.+)$", line)
            if match:
                if_line = match.group(1)
                break
        if if_line and "pull_request" not in if_line and (
            "workflow_dispatch" in if_line or "refs/tags" in if_line
        ):
            notes.append(f"skip {job_id} (does not run on pull_request)")
            continue
        if re.search(r"^    strategy:\s*$", joined, flags=re.M):
            notes.append(f"matrix job {job_id} left out of the ruleset")
            continue
        name = job_id
        for line in body:
            match = re.match(r"^    name:\s*['\"]?(.+?)['\"]?\s*$", line)
            if match:
                name = match.group(1).strip()
                break
        required.append(name)
    return required, notes


def discover(repo: str, ref: str) -> tuple[list[str], list[str]]:
    checks: list[str] = []
    notes: list[str] = []
    for name in list_workflows(repo, ref):
        text = file_text(repo, f".github/workflows/{name}", ref)
        if text is None:
            continue
        found, job_notes = pr_job_names(text)
        checks.extend(found)
        notes.extend(f"{name}: {note}" for note in job_notes)
    deduped: list[str] = []
    for check in checks:
        if check not in deduped and check != "pr-gate":
            deduped.append(check)
    return deduped, notes


def ruleset_body(branch: str, checks: list[str], context: str) -> dict:
    contexts = list(checks)
    if context not in contexts:
        contexts.append(context)
    return {
        "name": RULESET_NAME,
        "target": "branch",
        "enforcement": "active",
        "conditions": {"ref_name": {"include": [f"refs/heads/{branch}"], "exclude": []}},
        "rules": [
            {"type": "deletion"},
            {"type": "non_fast_forward"},
            {
                "type": "pull_request",
                "parameters": {
                    "required_approving_review_count": 0,
                    "dismiss_stale_reviews_on_push": False,
                    "require_code_owner_review": False,
                    "require_last_push_approval": False,
                    "required_review_thread_resolution": False,
                    "allowed_merge_methods": ["squash"],
                },
            },
            {
                "type": "required_status_checks",
                "parameters": {
                    "strict_required_status_checks_policy": False,
                    "do_not_enforce_on_create": True,
                    "required_status_checks": [{"context": item} for item in contexts],
                },
            },
        ],
    }


def apply_one(repo: dict, owner: str, context: str, dry_run: bool) -> dict:
    name = repo["name"]
    full = f"{owner}/{name}"
    row = {
        "repo": full,
        "ruleset": "no",
        "required_checks": "",
        "template": "",
        "skipped": "",
        "auto_merge": "",
    }
    if repo.get("archived"):
        row["skipped"] = "archived"
        return row
    branch = repo.get("default_branch") or "main"
    if branch not in TRUNK_NAMES:
        row["skipped"] = f"default branch is {branch}, not main/master/trunk"
        return row
    checks, notes = discover(full, branch)
    if not checks:
        row["skipped"] = "no pull_request CI job"
        if notes:
            row["skipped"] += " (" + "; ".join(notes) + ")"
        return row
    contexts = checks + ([context] if context not in checks else [])
    row["required_checks"] = ", ".join(contexts)
    if notes:
        row["skipped"] = "; ".join(notes)
    if dry_run:
        row["ruleset"] = "dry-run"
        return row
    code, parsed, err = gh(
        f"repos/{full}",
        "PATCH",
        {
            "allow_auto_merge": True,
            "allow_squash_merge": True,
            "allow_merge_commit": False,
            "allow_rebase_merge": False,
        },
    )
    if code == 0:
        row["auto_merge"] = "on"
    else:
        message = parsed.get("message") if isinstance(parsed, dict) else err
        row["auto_merge"] = f"failed: {message}"
    code, existing, err = gh(f"repos/{full}/rulesets")
    if code != 0:
        message = existing.get("message") if isinstance(existing, dict) else (err or existing)
        row["ruleset"] = "no"
        row["skipped"] = (row["skipped"] + "; " if row["skipped"] else "") + f"ruleset API: {message}"
        return row
    match = None
    if isinstance(existing, list):
        match = next((item for item in existing if item.get("name") == RULESET_NAME), None)
    body = ruleset_body(branch, checks, context)
    if match:
        code, parsed, err = gh(f"repos/{full}/rulesets/{match['id']}", "PUT", body)
        action = "updated"
    else:
        code, parsed, err = gh(f"repos/{full}/rulesets", "POST", body)
        action = "created"
    if code != 0:
        message = parsed.get("message") if isinstance(parsed, dict) else (err or parsed)
        row["ruleset"] = "no"
        row["skipped"] = (row["skipped"] + "; " if row["skipped"] else "") + f"ruleset {action} failed: {message}"
        return row
    row["ruleset"] = "yes"
    return row


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pr-gate-context", default="pr-gate")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    rows = []
    for owner in OWNERS:
        for repo in list_repos_paginated(owner):
            row = apply_one(repo, owner, args.pr_gate_context, args.dry_run)
            rows.append(row)
            print(
                f"{row['repo']}\truleset={row['ruleset']}\tchecks={row['required_checks']}\t{row['skipped']}",
                flush=True,
            )
    print("\nJSON_REPORT_START")
    print(json.dumps(rows))
    print("JSON_REPORT_END")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
