import requests

from config import AUTH, HEADERS, HTTP_TIMEOUT_SECONDS, JIRA_FIELDS, JIRA_URL

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
