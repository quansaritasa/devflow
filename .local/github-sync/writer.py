import json
import os
import re
from pathlib import Path
from typing import Any

try:
    from .config import PR_DOWNLOAD_PATH, PR_DOWNLOAD_PATH_REL, TEMPLATE_PATHS
except ImportError:
    from config import PR_DOWNLOAD_PATH, PR_DOWNLOAD_PATH_REL, TEMPLATE_PATHS


def _pr_repo_path(task_key: str, filename: str) -> str:
    return f"{PR_DOWNLOAD_PATH_REL}/{task_key}/{filename}"


def _text(value: object, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _value_or_default(value: object, default: str) -> str:
    text = _text(value)
    return text if text else default


def _bool_yes_no(value: object) -> str:
    return "yes" if bool(value) else "no"


def _bullet_list(items: list[str], default: str = "- None") -> str:
    normalized = [item for item in items if _text(item)]
    return "\n".join(normalized) if normalized else default


def _commit_summary(commit: dict[str, Any]) -> str:
    message = _text(commit.get("message"))
    first_line = message.splitlines()[0] if message else "(no message)"
    return (
        f"- `{commit.get('sha')}` — {first_line} "
        f"({commit.get('author') or 'Unknown'}, {commit.get('date') or 'Unknown'})"
    )


def _review_summary(review: dict[str, Any]) -> str:
    return (
        f"- **{review.get('state') or 'UNKNOWN'}** by {review.get('author') or 'Unknown'} "
        f"at {review.get('submitted_at') or 'Unknown'}\n\n"
        f"  {review.get('body') or '_(no body)_'}"
    )


def _issue_comment_summary(comment: dict[str, Any]) -> str:
    return (
        f"- **{comment.get('author') or 'Unknown'}** at {comment.get('created_at') or 'Unknown'}\n\n"
        f"  {comment.get('body') or '_(no body)_'}"
    )


def _review_comment_summary(comment: dict[str, Any]) -> str:
    return (
        f"- `{comment.get('path') or 'unknown path'}` line {comment.get('line') or '?'} "
        f"by {comment.get('author') or 'Unknown'} at {comment.get('created_at') or 'Unknown'}\n\n"
        f"  {comment.get('body') or '_(no body)_'}"
    )


def _load_template() -> str | None:
    for path in TEMPLATE_PATHS:
        try:
            return Path(path).read_text(encoding="utf-8")
        except OSError:
            continue
    return None


def build_pr_json_entry(task_key: str, details: dict[str, Any]) -> dict[str, Any]:
    pull = details.get("pull") or {}
    issue_comments = details.get("issue_comments") or []
    reviews = details.get("reviews") or []
    review_comments = details.get("review_comments") or []
    commits = details.get("commits") or []
    files = details.get("files") or []

    changed_files = []
    for file in files:
        if not isinstance(file, dict):
            continue
        changed_files.append(
            {
                "filename": file.get("filename"),
                "status": file.get("status"),
                "additions": file.get("additions"),
                "deletions": file.get("deletions"),
                "changes": file.get("changes"),
            }
        )

    commit_summaries = []
    for commit in commits:
        if not isinstance(commit, dict):
            continue
        commit_data = commit.get("commit") or {}
        author = commit_data.get("author") or {}
        commit_summaries.append(
            {
                "sha": commit.get("sha"),
                "message": _text(commit_data.get("message")),
                "author": _text(author.get("name")),
                "date": author.get("date"),
            }
        )

    repository = _text(details.get("repository"))

    return {
        "task_key": task_key,
        "repository": repository,
        "number": pull.get("number"),
        "title": _text(pull.get("title")),
        "state": _text(pull.get("state")),
        "draft": bool(pull.get("draft")),
        "merged": bool(pull.get("merged")),
        "created_at": pull.get("created_at"),
        "updated_at": pull.get("updated_at"),
        "closed_at": pull.get("closed_at"),
        "merged_at": pull.get("merged_at"),
        "author": _text((pull.get("user") or {}).get("login")),
        "assignees": [
            user.get("login")
            for user in (pull.get("assignees") or [])
            if isinstance(user, dict) and user.get("login")
        ],
        "requested_reviewers": [
            user.get("login")
            for user in (pull.get("requested_reviewers") or [])
            if isinstance(user, dict) and user.get("login")
        ],
        "labels": [
            label.get("name")
            for label in (pull.get("labels") or [])
            if isinstance(label, dict) and label.get("name")
        ],
        "head_ref": _text(((pull.get("head") or {}).get("ref"))),
        "base_ref": _text(((pull.get("base") or {}).get("ref"))),
        "url": pull.get("html_url"),
        "body": _text(pull.get("body")),
        "stats": {
            "commits": pull.get("commits"),
            "comments": pull.get("comments"),
            "review_comments": pull.get("review_comments"),
            "additions": pull.get("additions"),
            "deletions": pull.get("deletions"),
            "changed_files": pull.get("changed_files"),
        },
        "files": changed_files,
        "commits": commit_summaries,
        "issue_comments": [
            {
                "author": _text((comment.get("user") or {}).get("login")),
                "created_at": comment.get("created_at"),
                "updated_at": comment.get("updated_at"),
                "body": _text(comment.get("body")),
            }
            for comment in issue_comments
            if isinstance(comment, dict)
        ],
        "reviews": [
            {
                "author": _text((review.get("user") or {}).get("login")),
                "state": _text(review.get("state")),
                "submitted_at": review.get("submitted_at"),
                "body": _text(review.get("body")),
            }
            for review in reviews
            if isinstance(review, dict)
        ],
        "review_comments": [
            {
                "author": _text((comment.get("user") or {}).get("login")),
                "path": _text(comment.get("path")),
                "line": comment.get("line"),
                "created_at": comment.get("created_at"),
                "body": _text(comment.get("body")),
            }
            for comment in review_comments
            if isinstance(comment, dict)
        ],
        "paths": {
            "pr_md": _pr_repo_path(task_key, "pr.md"),
            "pr_json": _pr_repo_path(task_key, "pr.json"),
        },
    }


def _template_context(record: dict[str, Any]) -> dict[str, str]:
    stats = record.get("stats") or {}
    reviewer_lines = [f"- {name}" for name in record.get("requested_reviewers", [])]
    assignee_lines = [f"- assignee: {name}" for name in record.get("assignees", [])]
    file_lines = [
        f"- `{file['filename']}` ({file['status']}, +{file['additions']}/-{file['deletions']}, total {file['changes']})"
        for file in record.get("files", [])
    ]
    commit_lines = [_commit_summary(commit) for commit in record.get("commits", [])]
    review_lines = [_review_summary(review) for review in record.get("reviews", [])]
    issue_comment_lines = [
        _issue_comment_summary(comment) for comment in record.get("issue_comments", [])
    ]
    review_comment_lines = [
        _review_comment_summary(comment)
        for comment in record.get("review_comments", [])
    ]

    return {
        "task_key": _text(record.get("task_key")),
        "repository": _text(record.get("repository")),
        "repository_or_unknown": _value_or_default(record.get("repository"), "Unknown"),
        "number": _text(record.get("number")),
        "title": _text(record.get("title")),
        "state": _text(record.get("state")),
        "draft_yes_no": _bool_yes_no(record.get("draft")),
        "merged_yes_no": _bool_yes_no(record.get("merged")),
        "author_or_unknown": _value_or_default(record.get("author"), "Unknown"),
        "base_ref_or_unknown": _value_or_default(record.get("base_ref"), "Unknown"),
        "head_ref_or_unknown": _value_or_default(record.get("head_ref"), "Unknown"),
        "created_at_or_unknown": _value_or_default(record.get("created_at"), "Unknown"),
        "updated_at_or_unknown": _value_or_default(record.get("updated_at"), "Unknown"),
        "closed_at_or_not_closed": _value_or_default(
            record.get("closed_at"), "Not closed"
        ),
        "merged_at_or_not_merged": _value_or_default(
            record.get("merged_at"), "Not merged"
        ),
        "url_or_unknown": _value_or_default(record.get("url"), "Unknown"),
        "body_or_no_description": _value_or_default(
            record.get("body"), "_(no description)_"
        ),
        "labels_bullets": _bullet_list(
            [f"- {label}" for label in record.get("labels", [])]
        ),
        "reviewers_and_assignees_bullets": _bullet_list(
            reviewer_lines + assignee_lines
        ),
        "files_bullets": _bullet_list(file_lines),
        "commits_bullets": _bullet_list(commit_lines),
        "reviews_bullets": _bullet_list(review_lines),
        "issue_comments_bullets": _bullet_list(issue_comment_lines),
        "review_comments_bullets": _bullet_list(review_comment_lines),
        "stats.commits": _text(stats.get("commits"), "0"),
        "stats.comments": _text(stats.get("comments"), "0"),
        "stats.review_comments": _text(stats.get("review_comments"), "0"),
        "stats.additions": _text(stats.get("additions"), "0"),
        "stats.deletions": _text(stats.get("deletions"), "0"),
        "stats.changed_files": _text(stats.get("changed_files"), "0"),
    }


def _render_template(template: str, context: dict[str, str]) -> str:
    def replace(match: re.Match[str]) -> str:
        key = match.group(1).strip()
        return context.get(key, "")

    return re.sub(r"\{\{\s*([^{}]+?)\s*\}\}", replace, template)


def _render_pr_md_from_entry(record: dict[str, Any]) -> str:
    template = _load_template()
    if template:
        return _render_template(template, _template_context(record)).strip()

    lines = [
        f"# PR #{record['number']} — {record['title']}",
        "",
        f"- **Repository:** {record['repository'] or 'Unknown'}",
        "",
        f"- **Task:** {record['task_key']}",
        f"- **State:** {record['state']}",
        f"- **Draft:** {'yes' if record['draft'] else 'no'}",
        f"- **Merged:** {'yes' if record['merged'] else 'no'}",
        f"- **Author:** {record['author'] or 'Unknown'}",
        f"- **Base Branch:** {record['base_ref'] or 'Unknown'}",
        f"- **Head Branch:** {record['head_ref'] or 'Unknown'}",
        f"- **Created:** {record['created_at'] or 'Unknown'}",
        f"- **Updated:** {record['updated_at'] or 'Unknown'}",
        f"- **Closed:** {record['closed_at'] or 'Not closed'}",
        f"- **Merged At:** {record['merged_at'] or 'Not merged'}",
        f"- **URL:** {record['url'] or 'Unknown'}",
        "",
        "## Summary",
        "",
        record["body"] or "_(no description)_",
        "",
        "## Stats",
        "",
        f"- **Commits:** {record['stats']['commits']}",
        f"- **Issue Comments:** {record['stats']['comments']}",
        f"- **Review Comments:** {record['stats']['review_comments']}",
        f"- **Additions:** {record['stats']['additions']}",
        f"- **Deletions:** {record['stats']['deletions']}",
        f"- **Changed Files:** {record['stats']['changed_files']}",
        "",
        "## Labels",
        "",
    ]
    lines.extend([f"- {label}" for label in record["labels"]] or ["- None"])
    lines.extend(["", "## Reviewers", ""])
    reviewer_lines = [f"- {name}" for name in record["requested_reviewers"]]
    assignee_lines = [f"- assignee: {name}" for name in record["assignees"]]
    lines.extend(reviewer_lines + assignee_lines or ["- None"])
    lines.extend(["", "## Changed Files", ""])
    lines.extend(
        [
            f"- `{file['filename']}` ({file['status']}, +{file['additions']}/-{file['deletions']}, total {file['changes']})"
            for file in record["files"]
        ]
        or ["- None"]
    )
    lines.extend(["", "## Commits", ""])
    lines.extend(
        [
            f"- `{commit['sha']}` — {commit['message'].splitlines()[0] if commit['message'] else '(no message)'} ({commit['author'] or 'Unknown'}, {commit['date'] or 'Unknown'})"
            for commit in record["commits"]
        ]
        or ["- None"]
    )
    lines.extend(["", "## Reviews", ""])
    lines.extend(
        [
            f"- **{review['state'] or 'UNKNOWN'}** by {review['author'] or 'Unknown'} at {review['submitted_at'] or 'Unknown'}\n\n  {review['body'] or '_(no body)_'}"
            for review in record["reviews"]
        ]
        or ["- None"]
    )
    lines.extend(["", "## Issue Comments", ""])
    lines.extend(
        [
            f"- **{comment['author'] or 'Unknown'}** at {comment['created_at'] or 'Unknown'}\n\n  {comment['body'] or '_(no body)_'}"
            for comment in record["issue_comments"]
        ]
        or ["- None"]
    )
    lines.extend(["", "## Review Comments", ""])
    lines.extend(
        [
            f"- `{comment['path'] or 'unknown path'}` line {comment['line'] or '?'} by {comment['author'] or 'Unknown'} at {comment['created_at'] or 'Unknown'}\n\n  {comment['body'] or '_(no body)_'}"
            for comment in record["review_comments"]
        ]
        or ["- None"]
    )
    return "\n".join(lines).strip()


def _load_existing_json_entries(path: str) -> list[dict[str, Any]]:
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (json.JSONDecodeError, OSError):
        return []
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    return []


def write_pr_files(
    task_key: str,
    details_list: list[dict[str, Any]],
    overwrite: bool = False,
) -> int:
    folder = os.path.join(PR_DOWNLOAD_PATH, task_key)
    os.makedirs(folder, exist_ok=True)
    md_path = os.path.join(folder, "pr.md")
    json_path = os.path.join(folder, "pr.json")

    existing_entries = [] if overwrite else _load_existing_json_entries(json_path)
    by_number = {
        f"{entry.get('repository')}#{entry.get('number')}": entry
        for entry in existing_entries
        if isinstance(entry, dict)
        and isinstance(entry.get("repository"), str)
        and entry.get("number") is not None
    }

    for details in details_list:
        entry = build_pr_json_entry(task_key, details)
        entry_id = f"{entry.get('repository')}#{entry.get('number')}"
        by_number[entry_id] = entry

    ordered_numbers = sorted(by_number.keys())
    ordered_entries = [by_number[number] for number in ordered_numbers]

    with open(json_path, "w", encoding="utf-8") as handle:
        json.dump(ordered_entries, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

    rendered_sections = [_render_pr_md_from_entry(entry) for entry in ordered_entries]
    with open(md_path, "w", encoding="utf-8") as handle:
        handle.write("\n\n---\n\n".join(rendered_sections).strip() + "\n")

    return len(ordered_entries)
