import requests

from config import (
    AUTH,
    HEADERS,
    HTTP_TIMEOUT_SECONDS,
    JIRA_FIELDS,
    JIRA_PROJECT_KEY,
    JIRA_URL,
)

SEARCH_URL = f"{JIRA_URL}/rest/api/3/search/jql"


def _parse_issue_number(issue_key: str) -> int:
    prefix, sep, suffix = str(issue_key).rpartition("-")
    if not sep or not prefix or not suffix.isdigit():
        raise ValueError(f"Unexpected Jira issue key format: {issue_key}")
    return int(suffix)


def get_max_issue_id(project_key: str) -> int:
    payload = {
        "jql": f"project = {project_key} ORDER BY id DESC",
        "maxResults": 1,
        "fields": ["summary"],
    }
    resp = requests.post(
        SEARCH_URL,
        json=payload,
        auth=AUTH,
        headers=HEADERS,
        timeout=HTTP_TIMEOUT_SECONDS,
    )
    resp.raise_for_status()
    issues = resp.json().get("issues", [])
    if not issues:
        return 0
    return _parse_issue_number(issues[0].get("key", ""))


def fetch_issue(project_key: str, issue_id: int) -> dict[str, object] | None:
    key = f"{project_key}-{issue_id}"
    url = f"{JIRA_URL}/rest/api/3/issue/{key}"
    params = {
        "fields": ",".join(JIRA_FIELDS),
        "expand": "renderedFields,names",
    }
    resp = requests.get(
        url,
        params=params,
        auth=AUTH,
        headers=HEADERS,
        timeout=HTTP_TIMEOUT_SECONDS,
    )
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return resp.json()


def should_fetch_children(issue: dict[str, object]) -> bool:
    """Only fetch children for Epics that don't already have subtasks."""
    fields = issue.get("fields") or {}
    issuetype_name = (fields.get("issuetype") or {}).get("name", "") or ""
    if issuetype_name.lower() != "epic":
        return False
    subtasks = fields.get("subtasks") or []
    if subtasks:
        return False
    return True


def fetch_children(parent_key: str) -> list[dict[str, object]]:
    """Fetch child issues via JQL parent={key}."""
    payload = {
        "jql": f"parent={parent_key}",
        "maxResults": 100,
        "fields": ["summary", "status", "issuetype"],
    }
    resp = requests.post(
        SEARCH_URL,
        json=payload,
        auth=AUTH,
        headers=HEADERS,
        timeout=HTTP_TIMEOUT_SECONDS,
    )
    resp.raise_for_status()
    return resp.json().get("issues", [])


def _fetch_field_names() -> dict[str, str]:
    """Return customfield_XXX -> display name mapping from a sample issue."""
    payload = {
        "jql": f"project = {JIRA_PROJECT_KEY} ORDER BY created DESC",
        "maxResults": 1,
        "fields": ["summary"],
    }
    resp = requests.post(
        SEARCH_URL,
        json=payload,
        auth=AUTH,
        headers=HEADERS,
        timeout=HTTP_TIMEOUT_SECONDS,
    )
    resp.raise_for_status()
    issues = resp.json().get("issues", [])
    if not issues:
        return {}

    sample_key = issues[0]["key"]
    url = f"{JIRA_URL}/rest/api/3/issue/{sample_key}"
    resp = requests.get(
        url,
        params={"fields": "*all", "expand": "names"},
        auth=AUTH,
        headers=HEADERS,
        timeout=HTTP_TIMEOUT_SECONDS,
    )
    resp.raise_for_status()
    names = resp.json().get("names") or {}

    result: dict[str, str] = {}
    for field_id, field_name in names.items():
        if field_id.startswith("customfield_"):
            result[field_id] = str(field_name)
    return result


def discover_fields(
    configured_fields: dict[str, str] | None = None, show_all: bool = False
) -> None:
    """Fetch and display custom fields from Jira for config.json setup."""
    print(f"Discovering custom fields for project '{JIRA_PROJECT_KEY}'...")
    print()

    custom_fields = _fetch_field_names()
    if not custom_fields:
        print("No issues found in project. Cannot discover fields.")
        return

    if show_all:
        print(f"All {len(custom_fields)} custom fields:")
        print()
        for field_id, field_name in sorted(custom_fields.items()):
            print(f"  {field_name}")
            print(f"  -> {field_id}")
            print()
        return

    configured = configured_fields or {}
    matched_ids: set[str] = set()

    if configured:
        print("Configured custom fields:")
        print()
        for config_key, config_value in configured.items():
            if not config_value:
                print(f'  "{config_key}": "",  # NOT SET')
                continue
            if config_value.startswith("customfield_"):
                name = custom_fields.get(config_value, "unknown")
                print(f'  "{config_key}": "{config_value}",  # {name}')
                matched_ids.add(config_value)
            else:
                found = False
                for field_id, field_name in sorted(custom_fields.items()):
                    if field_name.lower() == config_value.lower():
                        print(f'  "{config_key}": "{field_id}",  # {field_name}')
                        matched_ids.add(field_id)
                        found = True
                        break
                if not found:
                    print(f'  "{config_key}": "",  # NOT FOUND: "{config_value}"')
        print()

    unmatched = {
        fid: fname
        for fid, fname in sorted(custom_fields.items())
        if fid not in matched_ids
    }
    if unmatched:
        label = (
            "Other custom fields"
            if configured
            else f"All {len(unmatched)} custom fields"
        )
        print(f"{label}:")
        print()
        for field_id, field_name in unmatched.items():
            print(f"  # {field_name}")
            print(f"  # -> {field_id}")
            print()
