# Keywords Sync

Use this folder to generate `dev/config/keywords.md` from task source files.

---

## 1. Files

- `keywords-template.md`
  - output shape contract
  - parser-safe format
  - reusable across projects that use same keyword groups

- `prompt.md`
  - prompt for AI tool
  - tells AI how to fill template from task data

---

## 2. Inputs

Use these repo inputs:

- `dev/tasks/*/raw.md`
- `dev/tasks/*/task.json`

Template:

- `.local/keywords-sync/keywords-template.md`

Output target:

- `dev/config/keywords.md`

---

## 3. How to use

1. Open `prompt.md`
2. Give AI these files:
   - `prompt.md`
   - `keywords-template.md`
   - task files under `dev/tasks`
3. Ask AI to generate final `dev/config/keywords.md`
4. Save generated result into `dev/config/keywords.md`
5. Run index sync after update

---

## 4. Notes

- Keep exact markdown structure from template.
- Keep exact group values from template.
- Use kebab-case canonical keywords.
- Use inline lists only.
- Keep aliases precise.
- `related` values must point to real canonical keywords in same file.
- Better fewer strong keywords than many weak keywords.
