import re

from config import (
    DOWNLOAD_PATH,
    DOWNLOAD_PATH_REL,
    EPIC_LINK_FIELD,
    EPIC_NAME_FIELD,
    JIRA_PROJECT_KEY,
    JIRA_URL,
    SPRINT_FIELD,
    STORY_POINTS_FIELD,
    TEMPLATE_PATHS,
)

TASK_KEY_RE_TEMPLATE = r"\b{project_key}-\d+\b"


def _task_repo_path(
    task_key: str, filename: str, download_path_rel: str = DOWNLOAD_PATH_REL
) -> str:
    return f"{download_path_rel}/{task_key}/{filename}"


_BUILTIN_TEMPLATE = """\
# [KEY] — [TITLE]

- **Status:** [STATUS]
- **Type:** [ISSUETYPE]
- **Priority:** [PRIORITY]
- **Estimated:** [ESTIMATED]
- **Spent:** [SPENT]
- **Assignee:** [ASSIGNEE]
- **Reporter:** [REPORTER]
- **Components:** [COMPONENTS]
- **Labels:** [LABELS]
- **Fix Versions:** [FIX_VERSIONS]
- **Created:** [CREATED]
- **Updated:** [UPDATED]
- **Due Date:** [DUE_DATE]
- **Resolution:** [RESOLUTION]
- **Resolved At:** [RESOLUTION_DATE]
- **URL:** [URL]

---

## Hierarchy

- **Epic:** [EPIC]
- **Sprint:** [SPRINT]
- **Parent:** [PARENT]
- **Story Points:** [STORY_POINTS]
- **Subtasks:**
[SUBTASKS]

---

## Related Tasks

[RELATED_TASKS]

---

## Attachments

[ATTACHMENTS]

---

## Technical Signals

[TECH_SIGNALS]

---

## Acceptance Clues

[ACCEPTANCE_CLUES]

---

## Description

[DESCRIPTION]

---

## Comments

[COMMENTS]
"""


def load_template() -> str:
    for path in TEMPLATE_PATHS:
        if path.exists():
            with path.open("r", encoding="utf-8") as f:
                return f.read()
    return _BUILTIN_TEMPLATE


def _normalize_jira_text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "\n".join(
            part for part in (_normalize_jira_text(v) for v in value) if part
        )
    if isinstance(value, dict):
        text = value.get("text")
        if isinstance(text, str) and text.strip():
            return text
        parts = []
        for key in ("content", "body", "attrs"):
            if key in value:
                nested = _normalize_jira_text(value.get(key))
                if nested:
                    parts.append(nested)
        return "\n".join(parts)
    return str(value)


def _text(v, default="None"):
    s = _normalize_jira_text(v).strip()
    return s if s else default


def _join_names(items):
    if not items:
        return "None"
    names = [x.get("name", "").strip() for x in items if isinstance(x, dict)]
    names = [x for x in names if x]
    return ", ".join(names) if names else "None"


def _split_names(value: str) -> list[str]:
    if not value or value == "None":
        return []
    return [part.strip() for part in value.split(",") if part.strip()]


def _format_seconds(seconds):
    if seconds in (None, ""):
        return "None"
    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    if hours and minutes:
        return f"{hours}h {minutes}m"
    if hours:
        return f"{hours}h"
    return f"{minutes}m"


def _extract_timetracking(fields):
    tt = fields.get("timetracking") or {}
    est_seconds = tt.get("originalEstimateSeconds")
    spent_seconds = tt.get("timeSpentSeconds")
    return {
        "estimated": _format_seconds(est_seconds),
        "spent": _format_seconds(spent_seconds),
        "estimated_seconds": est_seconds,
        "spent_seconds": spent_seconds,
    }


def _extract_sprint(fields):
    sprint_field = fields.get(SPRINT_FIELD) or fields.get("sprint")
    if not sprint_field:
        return "None"
    if isinstance(sprint_field, list):
        if not sprint_field:
            return "None"
        latest = sprint_field[-1]
        if isinstance(latest, dict):
            return latest.get("name", "None")
        return _text(latest)
    if isinstance(sprint_field, dict):
        return sprint_field.get("name", "None")
    return _text(sprint_field)


def _build_epic(fields):
    parent = fields.get("parent")
    if parent:
        ptype = ((parent.get("fields") or {}).get("issuetype") or {}).get("name", "")
        if ptype.lower() == "epic":
            key = str(parent.get("key") or "").strip()
            summary = str(((parent.get("fields") or {}).get("summary") or "")).strip()
            if key:
                return {
                    "key": key,
                    "summary": summary,
                    "url": f"{JIRA_URL}/browse/{key}",
                }
    epic_key = str(fields.get(EPIC_LINK_FIELD) or "").strip()
    epic_name = str(fields.get(EPIC_NAME_FIELD) or "").strip()
    if epic_key:
        return {
            "key": epic_key,
            "summary": epic_name,
            "url": f"{JIRA_URL}/browse/{epic_key}",
        }
    return None


def _extract_epic(fields):
    epic = _build_epic(fields)
    if not epic:
        return "None"
    summary = str(epic.get("summary") or "").strip()
    return f"{epic['key']} — {summary}" if summary else str(epic["key"])


def _build_parent(fields):
    parent = fields.get("parent")
    if not parent:
        return None
    ptype = ((parent.get("fields") or {}).get("issuetype") or {}).get("name", "")
    if ptype.lower() == "epic":
        return None
    key = str(parent.get("key") or "").strip()
    summary = str(((parent.get("fields") or {}).get("summary") or "")).strip()
    if not key:
        return None
    return {
        "key": key,
        "summary": summary,
        "issue_type": str(ptype or "").strip() or None,
        "url": f"{JIRA_URL}/browse/{key}",
    }


def _extract_parent(fields):
    parent = _build_parent(fields)
    if not parent:
        return "None"
    issue_type = str(parent.get("issue_type") or "").strip()
    if issue_type:
        return f"{parent['key']} — {parent['summary']} ({issue_type})"
    return f"{parent['key']} — {parent['summary']}"


def _build_subtasks(fields):
    subtasks = fields.get("subtasks") or []
    items = []
    for s in subtasks:
        key = str(s.get("key") or "").strip()
        if not key:
            continue
        subtask_fields = s.get("fields") or {}
        items.append(
            {
                "key": key,
                "summary": str(subtask_fields.get("summary") or "").strip(),
                "status": str(
                    ((subtask_fields.get("status") or {}).get("name") or "")
                ).strip(),
                "issue_type": str(
                    ((subtask_fields.get("issuetype") or {}).get("name") or "")
                ).strip()
                or None,
                "url": f"{JIRA_URL}/browse/{key}",
            }
        )
    return items


def _extract_subtasks(fields):
    subtasks = _build_subtasks(fields)
    if not subtasks:
        return "- None"
    lines = []
    for subtask in subtasks:
        lines.append(f"- {subtask['key']}: {subtask['summary']} [{subtask['status']}]")
    return "\n".join(lines)


def _extract_related_tasks(fields):
    links = fields.get("issuelinks") or []
    if not links:
        return "_(none)_"
    lines = []
    for link in links:
        link_type = link.get("type") or {}
        if "inwardIssue" in link:
            issue = link.get("inwardIssue")
            direction = link_type.get("inward") or link_type.get("name") or "related"
        elif "outwardIssue" in link:
            issue = link.get("outwardIssue")
            direction = link_type.get("outward") or link_type.get("name") or "related"
        else:
            continue
        if not isinstance(issue, dict):
            continue
        key = issue.get("key", "")
        summary = ((issue.get("fields") or {}).get("summary") or "").strip()
        status = (
            ((issue.get("fields") or {}).get("status") or {}).get("name") or ""
        ).strip()
        lines.append(f"- **{direction}** {key}: {summary} [{status}]")
    return "\n".join(lines) if lines else "_(none)_"


def _build_attachments(fields):
    atts = fields.get("attachment") or []
    items = []
    for attachment in atts:
        filename = str(attachment.get("filename") or "").strip()
        content = str(attachment.get("content") or "").strip()
        if not filename and not content:
            continue
        author = (
            (attachment.get("author") or {})
            if isinstance(attachment.get("author"), dict)
            else {}
        )
        items.append(
            {
                "filename": filename or None,
                "url": content or None,
                "mime_type": str(attachment.get("mimeType") or "").strip() or None,
                "size": attachment.get("size"),
                "created": str(attachment.get("created") or "")[:10] or None,
                "author": {
                    "display_name": str(author.get("displayName") or "").strip()
                    or None,
                    "account_id": str(author.get("accountId") or "").strip() or None,
                },
            }
        )
    return items


def _extract_attachments(fields):
    attachments = _build_attachments(fields)
    if not attachments:
        return "_(none)_"
    lines = []
    for attachment in attachments:
        filename = str(attachment.get("filename") or "")
        content = str(attachment.get("url") or "")
        size = attachment.get("size")
        size_txt = f" ({size} bytes)" if size is not None else ""
        if content:
            lines.append(f"- [{filename}]({content}){size_txt}")
        else:
            lines.append(f"- {filename}{size_txt}")
    return "\n".join(lines)


def _collect_text_blob(issue):
    fields = issue.get("fields") or {}
    rendered = issue.get("renderedFields") or {}
    parts = [
        _text((fields.get("summary") or ""), default=""),
        _text(
            (rendered.get("description") or fields.get("description") or ""), default=""
        ),
    ]
    raw_comments = (fields.get("comment") or {}).get("comments", [])
    rendered_comments = (rendered.get("comment") or {}).get("comments", [])
    for i, c in enumerate(raw_comments):
        rendered_body = (
            rendered_comments[i].get("body", "") if i < len(rendered_comments) else ""
        )
        parts.append(_text(rendered_body or c.get("body", ""), default=""))
    return "\n".join([p for p in parts if p]).lower()


def _extract_tech_signals(issue):
    blob = _collect_text_blob(issue)
    groups = {
        "API": ["api", "endpoint", "swagger", "graphql", "rest"],
        "Backend": ["backend", "service", "controller", "repository", "job", "worker"],
        "Frontend": [
            "frontend",
            "ui",
            "ux",
            "component",
            "page",
            "screen",
            "react",
            "angular",
            ".net",
            "blazor",
        ],
        "Database": [
            "sql",
            "database",
            "db",
            "migration",
            "query",
            "table",
            "stored procedure",
        ],
        "Testing": ["unit test", "integration test", "automation", "test case", "qa"],
        "Performance": ["performance", "slow", "latency", "optimize", "memory", "cpu"],
        "Security": [
            "auth",
            "oauth",
            "permission",
            "security",
            "xss",
            "csrf",
            "encryption",
        ],
    }
    hits = [name for name, kws in groups.items() if any(k in blob for k in kws)]
    if not hits:
        return "- None"
    return "\n".join(f"- {h}" for h in hits)


def _extract_acceptance_clues(issue):
    fields = issue.get("fields") or {}
    rendered = issue.get("renderedFields") or {}
    parts = [
        _normalize_jira_text(
            rendered.get("description") or fields.get("description") or ""
        )
    ]
    raw_comments = (fields.get("comment") or {}).get("comments") or []
    rendered_comments = (rendered.get("comment") or {}).get("comments") or []
    for i, c in enumerate(raw_comments[:10]):
        rendered_body = (
            rendered_comments[i].get("body", "") if i < len(rendered_comments) else ""
        )
        parts.append(_normalize_jira_text(rendered_body or c.get("body") or ""))
    text = "\n".join(p for p in parts if p)
    lines = []
    for raw in re.split(r"\n+", text):
        s = re.sub(r"<[^>]+>", " ", raw).strip(" -•\t")
        s_low = s.lower()
        if not s:
            continue
        if any(
            token in s_low
            for token in [
                "accept",
                "should",
                "must",
                "expected",
                "verify",
                "test",
                "given",
                "when",
                "then",
            ]
        ):
            if s not in lines:
                lines.append(s)
        if len(lines) >= 12:
            break
    if not lines:
        return "- None"
    return "\n".join(f"- {x}" for x in lines)


def _html_to_text(value: str) -> str:
    text = re.sub(r"<br\s*/?>", "\n", value, flags=re.IGNORECASE)
    text = re.sub(r"</p\s*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<li\b[^>]*>", "- ", text, flags=re.IGNORECASE)
    text = re.sub(r"</li\s*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("&nbsp;", " ").replace("&amp;", "&")
    text = re.sub(r"\r\n?", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _extract_comments(issue):
    fields = issue.get("fields") or {}
    rendered = issue.get("renderedFields") or {}
    raw_comments = (fields.get("comment") or {}).get("comments") or []
    rendered_comments = (rendered.get("comment") or {}).get("comments") or []
    if not raw_comments:
        return "_(no comments)_"
    lines = []
    for i, c in enumerate(raw_comments):
        author = ((c.get("author") or {}).get("displayName") or "Unknown").strip()
        created = (c.get("created") or "")[:10]
        body = ""
        if i < len(rendered_comments):
            body = rendered_comments[i].get("body", "")
        if not body:
            body = c.get("body") or ""
        body = _normalize_jira_text(body).strip() or "_(empty comment)_"
        lines.append(f"**{author}** ({created}):\n{body}")
    return "\n\n---\n\n".join(lines)


def render_raw_md(issue: dict[str, object]) -> str:
    fields = issue.get("fields") or {}
    rendered = issue.get("renderedFields") or {}
    key = issue.get("key", "")
    summary = _text(fields.get("summary"), "(no summary)")
    status = _text(((fields.get("status") or {}).get("name")))
    issuetype = _text(((fields.get("issuetype") or {}).get("name")))
    priority = _text(((fields.get("priority") or {}).get("name")))
    assignee = _text(((fields.get("assignee") or {}).get("displayName")))
    reporter = _text(((fields.get("reporter") or {}).get("displayName")))
    components = _join_names(fields.get("components") or [])
    labels = (
        ", ".join(fields.get("labels") or [])
        if (fields.get("labels") or [])
        else "None"
    )
    fix_versions = _join_names(fields.get("fixVersions") or [])
    created = _text(str(fields.get("created") or "")[:10])
    updated = _text(str(fields.get("updated") or "")[:10])
    due_date = _text(fields.get("duedate"))
    resolution = _text(((fields.get("resolution") or {}).get("name")))
    resolution_date = _text(str(fields.get("resolutiondate") or "")[:10])
    story_points = fields.get(STORY_POINTS_FIELD)
    story_points = "None" if story_points in (None, "") else str(story_points)
    description = (
        rendered.get("description") or fields.get("description") or "_(no description)_"
    )
    tt = _extract_timetracking(fields)
    template = load_template()
    return (
        template.replace("[KEY]", key)
        .replace("[TITLE]", summary)
        .replace("[STATUS]", status)
        .replace("[ISSUETYPE]", issuetype)
        .replace("[PRIORITY]", priority)
        .replace("[ESTIMATED]", str(tt["estimated"]))
        .replace("[SPENT]", str(tt["spent"]))
        .replace("[ASSIGNEE]", assignee)
        .replace("[REPORTER]", reporter)
        .replace("[COMPONENTS]", components)
        .replace("[LABELS]", labels)
        .replace("[FIX_VERSIONS]", fix_versions)
        .replace("[CREATED]", created)
        .replace("[UPDATED]", updated)
        .replace("[DUE_DATE]", due_date)
        .replace("[RESOLUTION]", resolution)
        .replace("[RESOLUTION_DATE]", resolution_date)
        .replace("[URL]", f"{JIRA_URL}/browse/{key}")
        .replace("[EPIC]", _extract_epic(fields))
        .replace("[SPRINT]", _extract_sprint(fields))
        .replace("[PARENT]", _extract_parent(fields))
        .replace("[STORY_POINTS]", story_points)
        .replace("[SUBTASKS]", _extract_subtasks(fields))
        .replace("[RELATED_TASKS]", _extract_related_tasks(fields))
        .replace("[ATTACHMENTS]", _extract_attachments(fields))
        .replace("[TECH_SIGNALS]", _extract_tech_signals(issue))
        .replace("[ACCEPTANCE_CLUES]", _extract_acceptance_clues(issue))
        .replace("[DESCRIPTION]", str(description))
        .replace("[COMMENTS]", _extract_comments(issue))
    )


def build_task_relationships(
    issue: dict[str, object], download_path_rel: str = DOWNLOAD_PATH_REL
) -> dict[str, object]:
    fields = issue.get("fields") or {}
    rendered = issue.get("renderedFields") or {}
    key = str(issue.get("key", ""))
    project_key = key.partition("-")[0] or JIRA_PROJECT_KEY
    task_key_re = re.compile(
        TASK_KEY_RE_TEMPLATE.format(project_key=re.escape(project_key))
    )
    summary = _text(fields.get("summary"), "")
    tt = _extract_timetracking(fields)

    related = []
    seen = set()

    def add_relation(
        task_key,
        relation_type,
        source,
        summary_text="",
        status_text="",
        issue_type_text="",
    ):
        if not task_key or task_key == key:
            return
        uniq = (task_key, relation_type, source)
        if uniq in seen:
            return
        seen.add(uniq)
        related.append(
            {
                "key": task_key,
                "relation_type": relation_type,
                "source": source,
                "summary": summary_text or "",
                "status": status_text or None,
                "issue_type": issue_type_text or None,
                "url": f"{JIRA_URL}/browse/{task_key}",
            }
        )

    for link in fields.get("issuelinks") or []:
        link_type = link.get("type") or {}
        if "inwardIssue" in link:
            issue2 = link.get("inwardIssue")
            rel = link_type.get("inward") or link_type.get("name") or "related"
        elif "outwardIssue" in link:
            issue2 = link.get("outwardIssue")
            rel = link_type.get("outward") or link_type.get("name") or "related"
        else:
            continue
        if not isinstance(issue2, dict):
            continue
        issue2_fields = issue2.get("fields") or {}
        add_relation(
            issue2.get("key"),
            rel,
            "issue_link",
            (issue2_fields.get("summary") or ""),
            ((issue2_fields.get("status") or {}).get("name") or ""),
            ((issue2_fields.get("issuetype") or {}).get("name") or ""),
        )

    parent = fields.get("parent") or {}
    if parent.get("key"):
        ptype = (
            ((parent.get("fields") or {}).get("issuetype") or {}).get("name") or ""
        ).lower()
        relation = "epic" if ptype == "epic" else "parent"
        parent_fields = parent.get("fields") or {}
        add_relation(
            parent.get("key"),
            relation,
            "parent_field",
            (parent_fields.get("summary") or ""),
            ((parent_fields.get("status") or {}).get("name") or ""),
            ((parent_fields.get("issuetype") or {}).get("name") or ""),
        )

    epic_key = fields.get(EPIC_LINK_FIELD)
    if epic_key:
        add_relation(
            str(epic_key),
            "epic",
            "epic_link_field",
            _text(fields.get(EPIC_NAME_FIELD), ""),
            issue_type_text="Epic",
        )

    desc = _normalize_jira_text(
        rendered.get("description") or fields.get("description") or ""
    )
    for mentioned in sorted(set(task_key_re.findall(desc))):
        add_relation(mentioned, "mentioned", "description")

    comments = (fields.get("comment") or {}).get("comments") or []
    rendered_comments = (rendered.get("comment") or {}).get("comments") or []
    for i, c in enumerate(comments):
        rendered_body = (
            rendered_comments[i].get("body", "") if i < len(rendered_comments) else ""
        )
        body = _normalize_jira_text(rendered_body or c.get("body") or "")
        for mentioned in sorted(set(task_key_re.findall(body))):
            add_relation(mentioned, "mentioned", "comment")

    return {
        "task_key": key,
        "task_summary": summary,
        "task_path": _task_repo_path(key, "raw.md", download_path_rel),
        "estimated": tt["estimated"],
        "spent": tt["spent"],
        "estimated_seconds": tt["estimated_seconds"],
        "spent_seconds": tt["spent_seconds"],
        "related_tasks": related,
    }


def build_task_json_record(
    issue: dict[str, object], download_path_rel: str = DOWNLOAD_PATH_REL
) -> dict[str, object]:
    fields = issue.get("fields") or {}
    rendered = issue.get("renderedFields") or {}
    key = str(issue.get("key", ""))
    summary = _text(fields.get("summary"), "")
    tt = _extract_timetracking(fields)
    description_html = _normalize_jira_text(
        rendered.get("description") or fields.get("description") or ""
    ).strip()
    description_text = _html_to_text(description_html)
    epic_text = _extract_epic(fields)
    sprint_name = _extract_sprint(fields)
    parent_text = _extract_parent(fields)
    related_record = build_task_relationships(issue, download_path_rel)

    comments = []
    comment_texts = []
    raw_comments = (fields.get("comment") or {}).get("comments") or []
    rendered_comments = (rendered.get("comment") or {}).get("comments") or []
    for i, comment in enumerate(raw_comments):
        rendered_body = (
            rendered_comments[i].get("body", "") if i < len(rendered_comments) else ""
        )
        body_html = _normalize_jira_text(
            rendered_body or comment.get("body") or ""
        ).strip()
        body_text = _html_to_text(body_html)
        comments.append(
            {
                "author": _text(
                    ((comment.get("author") or {}).get("displayName")), "Unknown"
                ),
                "created": str(comment.get("created") or "")[:10] or None,
                "body": body_html,
                "body_text": body_text,
            }
        )
        if body_text:
            comment_texts.append(body_text)

    related_tasks = related_record["related_tasks"]
    component_names = _split_names(_join_names(fields.get("components") or []))
    epic = _build_epic(fields)
    parent = _build_parent(fields)
    subtasks = _build_subtasks(fields)
    attachments = _build_attachments(fields)
    labels = [
        str(label) for label in (fields.get("labels") or []) if str(label).strip()
    ]

    return {
        "task_key": key,
        "task_summary": summary,
        "status": _text(((fields.get("status") or {}).get("name"))),
        "issue_type": _text(((fields.get("issuetype") or {}).get("name"))),
        "priority": _text(((fields.get("priority") or {}).get("name"))),
        "estimated": tt["estimated"],
        "spent": tt["spent"],
        "estimated_seconds": tt["estimated_seconds"],
        "spent_seconds": tt["spent_seconds"],
        "assignee": _text(((fields.get("assignee") or {}).get("displayName"))),
        "reporter": _text(((fields.get("reporter") or {}).get("displayName"))),
        "components": component_names,
        "labels": labels,
        "fix_versions": _split_names(_join_names(fields.get("fixVersions") or [])),
        "created": str(fields.get("created") or "")[:10] or None,
        "updated": str(fields.get("updated") or "")[:10] or None,
        "due_date": fields.get("duedate") or None,
        "resolution": _text(((fields.get("resolution") or {}).get("name")), "None"),
        "resolution_date": str(fields.get("resolutiondate") or "")[:10] or None,
        "url": f"{JIRA_URL}/browse/{key}",
        "epic": epic,
        "epic_text": None if epic_text == "None" else epic_text,
        "sprint": None if sprint_name == "None" else sprint_name,
        "parent": parent,
        "parent_text": None if parent_text == "None" else parent_text,
        "subtasks": subtasks,
        "story_points": None
        if fields.get(STORY_POINTS_FIELD) in (None, "")
        else fields.get(STORY_POINTS_FIELD),
        "description": description_html,
        "description_text": description_text,
        "comments": comments,
        "related_tasks": related_tasks,
        "attachments": attachments,
        "paths": {
            "raw": _task_repo_path(key, "raw.md", download_path_rel),
            "task_json": _task_repo_path(key, "task.json", download_path_rel),
        },
    }
