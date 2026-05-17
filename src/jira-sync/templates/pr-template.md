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
