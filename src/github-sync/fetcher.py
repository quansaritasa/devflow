import os
import re
from typing import Any

import requests
from config import GITHUB_API_URL, GITHUB_REPOSITORIES, HEADERS, HTTP_TIMEOUT_SECONDS
from requests import HTTPError

TASK_KEY_RE = re.compile(r"\b[A-Z][A-Z0-9]+[-_\s]+\d+\b")


def _is_verbose() -> bool:
    return os.getenv("GITHUB_SYNC_VERBOSE", "") == "1"


def _github_get(path: str, params: dict[str, Any] | None = None) -> Any:
    url = f"{GITHUB_API_URL}{path}"
    response = requests.get(
        url,
        params=params,
        headers=HEADERS,
        timeout=HTTP_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    return response.json()


def _paginate(path: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    page = 1
    items: list[dict[str, Any]] = []
    while True:
        merged_params = {**(params or {}), "per_page": 100, "page": page}
        page_items = _github_get(path, params=merged_params)
        if not isinstance(page_items, list) or not page_items:
            break
        items.extend(item for item in page_items if isinstance(item, dict))
        if len(page_items) < 100:
            break
        page += 1
    return items


def _paginate_search(
    path: str, params: dict[str, Any] | None = None
) -> list[dict[str, Any]]:
    page = 1
    items: list[dict[str, Any]] = []
    while True:
        merged_params = {**(params or {}), "per_page": 100, "page": page}
        payload = _github_get(path, params=merged_params)
        if not isinstance(payload, dict):
            break
        page_items = payload.get("items", [])
        if not isinstance(page_items, list) or not page_items:
            break
        items.extend(item for item in page_items if isinstance(item, dict))
        if len(page_items) < 100:
            break
        page += 1
    return items


def _normalize_task_key(value: str) -> str:
    normalized = re.sub(r"[-_\s]+", "-", value.strip().upper())
    return normalized


def _extract_task_keys(*values: object) -> list[str]:
    found: set[str] = set()
    for value in values:
        if not isinstance(value, str):
            continue
        matches = TASK_KEY_RE.findall(value.upper())
        found.update(_normalize_task_key(match) for match in matches)
    return sorted(found)


def _repo_parts(repository: str) -> tuple[str, str]:
    owner, _, repo = repository.partition("/")
    if not owner or not repo:
        raise ValueError(
            f"GitHub repository must be in 'owner/repo' format: {repository}"
        )
    return owner, repo


def configured_repositories() -> list[str]:
    repositories = [repo for repo in GITHUB_REPOSITORIES if repo]
    if not repositories:
        raise ValueError(
            "No GitHub repositories configured. Set 'repositories' in config.json"
        )
    return repositories


def _format_http_error(exc: HTTPError) -> str:
    response = exc.response
    if response is None:
        return "request failed"
    status_code = response.status_code
    if status_code == 404:
        return "inaccessible (404)"
    if status_code == 401:
        return "unauthorized (401)"
    if status_code == 403:
        return "forbidden or rate-limited (403)"
    return f"HTTP {status_code}"


def _search_pull_requests_for_task(
    repository: str, normalized_task_key: str
) -> list[dict[str, Any]]:
    query_key = normalized_task_key.replace("-", " ")
    items = _paginate_search(
        "/search/issues",
        params={
            "q": f"{query_key} repo:{repository} is:pr",
            "sort": "updated",
            "order": "desc",
        },
    )
    pulls: list[dict[str, Any]] = []
    for item in items:
        task_keys = _extract_task_keys(
            item.get("title"),
            item.get("body"),
            item.get("html_url"),
        )
        if _is_verbose() and task_keys:
            print(
                f"DEBUG: repository {repository} search result #{item.get('number')} matched keys {task_keys}"
            )
        if normalized_task_key in task_keys:
            enriched_item = dict(item)
            enriched_item["repository"] = repository
            pulls.append(enriched_item)
            if _is_verbose():
                print(
                    f"DEBUG: repository {repository} matched target {normalized_task_key} on PR #{item.get('number')}"
                )
    return pulls


def find_pull_requests_for_task(task_key: str) -> list[dict[str, Any]]:
    normalized_task_key = _normalize_task_key(task_key)
    matching: list[dict[str, Any]] = []
    for repository in configured_repositories():
        try:
            pulls = _search_pull_requests_for_task(repository, normalized_task_key)
            if _is_verbose():
                print(
                    f"DEBUG: repository {repository} returned {len(pulls)} matching pull(s)"
                )
        except HTTPError as exc:
            if _is_verbose():
                print(f"DEBUG: repository {repository} {_format_http_error(exc)}")
            continue
        matching.extend(pulls)
    return matching


def filter_new_or_updated_pull_requests(
    pulls: list[dict[str, Any]],
    previous_ids: list[str],
    last_synced_at: str | None,
) -> list[dict[str, Any]]:
    previous_id_set = set(previous_ids)
    filtered: list[dict[str, Any]] = []
    for pull in pulls:
        pull_number = pull.get("number")
        pull_updated_at = pull.get("updated_at")
        repository = pull.get("repository")
        if not isinstance(pull_number, int) or not isinstance(repository, str):
            continue
        pull_id = f"{repository}#{pull_number}"
        if pull_id not in previous_id_set:
            filtered.append(pull)
            continue
        if isinstance(last_synced_at, str) and isinstance(pull_updated_at, str):
            if pull_updated_at > last_synced_at:
                filtered.append(pull)
    return filtered


def fetch_pull_request_details(repository: str, pull_number: int) -> dict[str, Any]:
    owner, repo = _repo_parts(repository)
    pull = _github_get(f"/repos/{owner}/{repo}/pulls/{pull_number}")
    comments = _paginate(f"/repos/{owner}/{repo}/issues/{pull_number}/comments")
    reviews = _paginate(f"/repos/{owner}/{repo}/pulls/{pull_number}/reviews")
    review_comments = _paginate(f"/repos/{owner}/{repo}/pulls/{pull_number}/comments")
    commits = _paginate(f"/repos/{owner}/{repo}/pulls/{pull_number}/commits")
    files = _paginate(f"/repos/{owner}/{repo}/pulls/{pull_number}/files")
    return {
        "repository": repository,
        "pull": pull,
        "issue_comments": comments,
        "reviews": reviews,
        "review_comments": review_comments,
        "commits": commits,
        "files": files,
    }
