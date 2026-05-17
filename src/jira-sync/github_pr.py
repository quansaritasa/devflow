"""GitHub PR fetch for Jira tasks using gh CLI.

Matches PRs by searching headRefName for the task key,
then fetches detailed data and writes pr.md alongside raw.md.
"""

import json
import os
import re
import subprocess
from typing import Any

from config import PR_TEMPLATE_PATH


def _gh_json(args: list[str], label: str = "") -> Any:
    try:
        result = subprocess.run(
            ["gh"] + args, capture_output=True, encoding="utf-8", timeout=60
        )
        if result.returncode != 0:
            if label:
                print(f"  [gh] {label}: {result.stderr.strip()[:200]}")
            return None
        return json.loads(result.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError) as e:
        if label:
            print(f"  [gh] {label}: {e}")
        return None


def _gh_lines(args: list[str], label: str = "") -> list[dict[str, Any]]:
    try:
        result = subprocess.run(
            ["gh"] + args, capture_output=True, encoding="utf-8", timeout=60
        )
        if result.returncode != 0:
            if label:
                print(f"  [gh] {label}: {result.stderr.strip()[:200]}")
            return []
        items = []
        for line in result.stdout.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            try:
                items.append(json.loads(line))
            except json.JSONDecodeError:
                pass
        return items
    except subprocess.TimeoutExpired as e:
        if label:
            print(f"  [gh] {label}: {e}")
        return []


def _extract_key_from_ref(head_ref: str, task_key: str) -> bool:
    return task_key.lower() in head_ref.lower()


def search_prs(task_key: str, github_repo: str) -> list[dict[str, Any]]:
    args = [
        "pr",
        "list",
        "--repo",
        github_repo,
        "--state",
        "all",
        "--search",
        f'"{task_key}" in:title,body',
        "--json",
        "number,title,headRefName,state,mergedAt,createdAt,author,url",
        "--limit",
        "20",
    ]
    results = _gh_json(args, f"search PRs for {task_key}")
    if not results:
        return []
    matches = []
    for pr in results:
        head_ref = pr.get("headRefName") or ""
        title = pr.get("title") or ""
        if _extract_key_from_ref(head_ref, task_key):
            matches.append(pr)
        elif _extract_key_from_ref(title, task_key):
            matches.append(pr)
    return matches


_SKIP_FILE_PATTERNS = [
    re.compile(r"^\.claude/"),
    re.compile(r"^docs/ai-knowledge/"),
    re.compile(r"\.md$"),
    re.compile(r"^\.gitignore$"),
]


def _should_skip_file(filepath: str | None) -> bool:
    if not filepath:
        return True
    for pat in _SKIP_FILE_PATTERNS:
        if pat.search(filepath):
            return True
    return False


def fetch_pr_details(pr_number: int, github_repo: str) -> dict[str, Any] | None:
    args = [
        "pr",
        "view",
        str(pr_number),
        "--repo",
        github_repo,
        "--json",
        (
            "number,title,body,state,isDraft,author,headRefName,baseRefName,"
            "createdAt,updatedAt,closedAt,mergedAt,"
            "additions,deletions,changedFiles,"
            "commits,reviews,comments,labels,assignees,reviewRequests,url"
        ),
    ]
    return _gh_json(args, f"PR #{pr_number} details")


def fetch_pr_files(pr_number: int, github_repo: str) -> list[dict[str, Any]]:
    args = [
        "api",
        f"/repos/{github_repo}/pulls/{pr_number}/files",
        "--paginate",
        "--jq",
        ".[] | {path, patch, status, additions, deletions}",
    ]
    return _gh_lines(args, f"PR #{pr_number} files")


def fetch_pr_review_comments(pr_number: int, github_repo: str) -> list[dict[str, Any]]:
    args = [
        "api",
        f"/repos/{github_repo}/pulls/{pr_number}/comments",
        "--jq",
        ".[] | {id, user, body, path, line, position}",
    ]
    return _gh_lines(args, f"PR #{pr_number} review comments")


def _load_pr_template() -> str:
    if PR_TEMPLATE_PATH.exists():
        return PR_TEMPLATE_PATH.read_text(encoding="utf-8")
    # fallback built-in template
    return """\
# PR #{{ number }} — {{ title }}

- **Repository:** {{ repository_or_unknown }}
- **Task:** {{ task_key }}
- **State:** {{ state }}
- **Draft:** {{ draft_yes_no }}
- **Merged:** {{ merged_yes_no }}
- **Author:** {{ author_or_unknown }}
- **Base Branch:** {{ base_ref_or_unknown }}
- **Head Branch:** {{ head_ref_or_unknown }}
- **Created:** {{ created_at_or_unknown }}
- **Updated:** {{ updated_at_or_unknown }}
- **Closed:** {{ closed_at_or_not_closed }}
- **Merged At:** {{ merged_at_or_not_merged }}
- **URL:** {{ url_or_unknown }}

## Summary

{{ body_or_no_description }}

## Stats

- **Commits:** {{ stats.commits }}
- **Issue Comments:** {{ stats.comments }}
- **Review Comments:** {{ stats.review_comments }}
- **Additions:** {{ stats.additions }}
- **Deletions:** {{ stats.deletions }}
- **Changed Files:** {{ stats.changed_files }}

## Labels

{{ labels_bullets }}

## Reviewers

{{ reviewers_and_assignees_bullets }}

## Changed Files

{{ files_bullets }}

## Commits

{{ commits_bullets }}

## Reviews

{{ reviews_bullets }}

## Issue Comments

{{ issue_comments_bullets }}

## Review Comments

{{ review_comments_bullets }}
"""


def _login(user: dict[str, Any] | None) -> str:
    if not user:
        return "unknown"
    return user.get("login") or "unknown"


def _yn(value: bool | None) -> str:
    return "Yes" if value else "No"


def _dt(value: str | None, fallback: str = "n/a") -> str:
    return value or fallback


def _format_files_bullets(files: list[dict[str, Any]]) -> str:
    source = [f for f in files if not _should_skip_file(f.get("path") or "")]
    if not source:
        return "_(none)_"
    lines: list[str] = []
    for f in source:
        path = f.get("path", "?")
        status = f.get("status", "?")
        add_n = f.get("additions", 0)
        del_n = f.get("deletions", 0)
        lines.append(f"- `{path}` ({status}) +{add_n} / -{del_n}")
    return "\n".join(lines)


def _format_commits_bullets(commits: list[dict[str, Any]]) -> str:
    if not commits:
        return "_(none)_"
    lines: list[str] = []
    for c in commits:
        oid = (c.get("oid") or "")[:7]
        msg = c.get("messageHeadline") or c.get("message") or "(no message)"
        lines.append(f"- `{oid}` — {msg}")
    return "\n".join(lines)


def _format_reviews_bullets(reviews: list[dict[str, Any]]) -> str:
    if not reviews:
        return "_(none)_"
    lines: list[str] = []
    for r in reviews:
        login = _login(r.get("author"))
        state = r.get("state", "COMMENTED")
        body = (r.get("body") or "").split("\n")[0][:200]
        if state == "APPROVED":
            lines.append(f"- **@{login}:** {state}")
        elif body:
            lines.append(f"- **@{login}:** {state} — {body}")
        else:
            lines.append(f"- **@{login}:** {state}")
    return "\n".join(lines)


def _format_issue_comments_bullets(comments: list[dict[str, Any]]) -> str:
    if not comments:
        return "_(none)_"
    lines: list[str] = []
    for c in comments:
        login = _login(c.get("author"))
        created = (c.get("createdAt") or "")[:10]
        body = (c.get("body") or "").split("\n")[0][:200]
        lines.append(f"- **@{login}** ({created}): {body}")
    return "\n".join(lines)


def _format_review_comments_bullets(
    review_comments: list[dict[str, Any]],
) -> str:
    if not review_comments:
        return "_(none)_"
    lines: list[str] = []
    for c in review_comments:
        login = _login(c.get("user"))
        path = c.get("path") or "?"
        line_num = c.get("line") or c.get("position") or "?"
        body = (c.get("body") or "").split("\n")[0]
        lines.append(f"- **@{login}** (`{path}`:{line_num}): {body}")
    return "\n".join(lines)


def _format_labels_bullets(labels: list[dict[str, Any]]) -> str:
    if not labels:
        return "_(none)_"
    lines: list[str] = []
    for lab in labels:
        name = lab.get("name") or "?"
        lines.append(f"- {name}")
    return "\n".join(lines)


def _format_reviewers_bullets(
    review_requests: list[dict[str, Any]],
    assignees: list[dict[str, Any]],
) -> str:
    lines: list[str] = []
    if review_requests:
        for rr in review_requests:
            login = _login(rr.get("requestedReviewer"))
            if login != "unknown":
                lines.append(f"- @{login} (reviewer)")
    if assignees:
        for a in assignees:
            login = _login(a)
            if login != "unknown":
                lines.append(f"- @{login} (assignee)")
    return "\n".join(lines) if lines else "_(none)_"


def render_pr_md(
    pr_details: dict[str, Any],
    files: list[dict[str, Any]],
    review_comments: list[dict[str, Any]],
    task_key: str,
    github_repo: str,
) -> str:
    template = _load_pr_template()

    commits = pr_details.get("commits") or []
    comments = pr_details.get("comments") or []
    reviews = pr_details.get("reviews") or []
    labels = pr_details.get("labels") or []
    assignees = pr_details.get("assignees") or []
    review_requests = pr_details.get("reviewRequests") or []

    merged_at = pr_details.get("mergedAt")
    closed_at = pr_details.get("closedAt")

    return (
        template.replace("{{ number }}", str(pr_details.get("number", "?")))
        .replace("{{ title }}", pr_details.get("title") or "(no title)")
        .replace("{{ repository_or_unknown }}", github_repo or "unknown")
        .replace("{{ task_key }}", task_key)
        .replace("{{ state }}", (pr_details.get("state") or "unknown").upper())
        .replace("{{ draft_yes_no }}", _yn(pr_details.get("isDraft")))
        .replace("{{ merged_yes_no }}", _yn(bool(merged_at)))
        .replace("{{ author_or_unknown }}", _login(pr_details.get("author")))
        .replace(
            "{{ base_ref_or_unknown }}", pr_details.get("baseRefName") or "unknown"
        )
        .replace(
            "{{ head_ref_or_unknown }}", pr_details.get("headRefName") or "unknown"
        )
        .replace("{{ created_at_or_unknown }}", _dt(pr_details.get("createdAt")))
        .replace("{{ updated_at_or_unknown }}", _dt(pr_details.get("updatedAt")))
        .replace("{{ closed_at_or_not_closed }}", _dt(closed_at, "Not closed"))
        .replace("{{ merged_at_or_not_merged }}", _dt(merged_at, "Not merged"))
        .replace("{{ url_or_unknown }}", pr_details.get("url") or "unknown")
        .replace(
            "{{ body_or_no_description }}",
            pr_details.get("body") or "_(No description provided)_",
        )
        .replace("{{ stats.commits }}", str(len(commits)))
        .replace("{{ stats.comments }}", str(len(comments)))
        .replace("{{ stats.review_comments }}", str(len(review_comments)))
        .replace("{{ stats.additions }}", str(pr_details.get("additions", 0)))
        .replace("{{ stats.deletions }}", str(pr_details.get("deletions", 0)))
        .replace(
            "{{ stats.changed_files }}", str(pr_details.get("changedFiles", len(files)))
        )
        .replace("{{ labels_bullets }}", _format_labels_bullets(labels))
        .replace(
            "{{ reviewers_and_assignees_bullets }}",
            _format_reviewers_bullets(review_requests, assignees),
        )
        .replace("{{ files_bullets }}", _format_files_bullets(files))
        .replace("{{ commits_bullets }}", _format_commits_bullets(commits))
        .replace("{{ reviews_bullets }}", _format_reviews_bullets(reviews))
        .replace(
            "{{ issue_comments_bullets }}", _format_issue_comments_bullets(comments)
        )
        .replace(
            "{{ review_comments_bullets }}",
            _format_review_comments_bullets(review_comments),
        )
    )


_PR_HEADER_RE = re.compile(r"^# PR #(\d+) —", re.MULTILINE)


def _existing_pr_numbers(filepath: str) -> set[str]:
    if not os.path.exists(filepath):
        return set()
    try:
        with open(filepath, "r", encoding="utf-8") as fh:
            content = fh.read()
    except OSError:
        return set()
    return set(_PR_HEADER_RE.findall(content))


def fetch_and_write_pr(
    task_key: str,
    download_path: str,
    github_repo: str,
    force: bool = False,
) -> str:
    folder = os.path.join(download_path, task_key)
    pr_md_path = os.path.join(folder, "pr.md")

    prs = search_prs(task_key, github_repo)
    if not prs:
        if not os.path.exists(pr_md_path):
            print(f"    pr.md: no PR found")
        else:
            print(f"    pr.md: no new PR found (existing file kept)")
        return "no_pr"

    existing_numbers = set() if force else _existing_pr_numbers(pr_md_path)

    new_entries: list[tuple[str, str]] = []
    for pr_summary in prs:
        pr_number = pr_summary.get("number")
        if not pr_number:
            continue
        pr_number_str = str(pr_number)

        if pr_number_str in existing_numbers and not force:
            print(f"    pr.md: PR #{pr_number} already in file - skipped")
            continue

        details = fetch_pr_details(pr_number, github_repo)
        if not details:
            continue
        files = fetch_pr_files(pr_number, github_repo)
        review_comments = fetch_pr_review_comments(pr_number, github_repo)
        entry = render_pr_md(details, files, review_comments, task_key, github_repo)
        new_entries.append((pr_number_str, entry))

    new_entries.sort(key=lambda x: int(x[0]))

    if not new_entries:
        if not os.path.exists(pr_md_path):
            print(f"    pr.md: error fetching details")
            return "error"
        print(f"    pr.md: all PRs already in file - nothing to do")
        return "skipped"

    os.makedirs(folder, exist_ok=True)
    tmp_path = pr_md_path + ".tmp"

    if force or not os.path.exists(pr_md_path):
        content = "\n\n---\n\n".join(entry for _, entry in new_entries) + "\n"
        with open(tmp_path, "w", encoding="utf-8") as fh:
            fh.write(content)
        os.replace(tmp_path, pr_md_path)
        pns = ", ".join(f"#{pn}" for pn, _ in new_entries)
        print(f"    pr.md: created ({len(new_entries)} PR(s): {pns})")
        return "created"
    else:
        try:
            with open(pr_md_path, "r", encoding="utf-8") as fh:
                existing = fh.read().rstrip("\n")
        except OSError:
            existing = ""
        content = (
            existing
            + "\n\n---\n\n"
            + "\n\n---\n\n".join(entry for _, entry in new_entries)
            + "\n"
        )
        with open(tmp_path, "w", encoding="utf-8") as fh:
            fh.write(content)
        os.replace(tmp_path, pr_md_path)
        pns = ", ".join(f"#{pn}" for pn, _ in new_entries)
        print(f"    pr.md: appended ({len(new_entries)} new PR(s): {pns})")
        return "appended"
