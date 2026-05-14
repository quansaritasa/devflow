# Keywords

Canonical keyword taxonomy for task indexing and related-task search.

Use canonical kebab-case terms.
Store canonical keywords only.
Use aliases for matching.
Keep terms reusable and broad enough to cover multiple tasks.

---

## 1. Product Areas

- canonical: <product-area-keyword>
  group: product-area
  aliases: [<alias-one>, <alias-two>]
  related: [<canonical-keyword>, <canonical-keyword>]

---

## 2. Domain Entities

- canonical: <domain-entity-keyword>
  group: domain-entity
  aliases: [<alias-one>, <alias-two>]
  related: [<canonical-keyword>, <canonical-keyword>]

---

## 3. Workflow

- canonical: <workflow-keyword>
  group: workflow
  aliases: [<alias-one>, <alias-two>]
  related: [<canonical-keyword>, <canonical-keyword>]

---

## 4. Auth and Access

- canonical: <auth-access-keyword>
  group: auth-access
  aliases: [<alias-one>, <alias-two>]
  related: [<canonical-keyword>, <canonical-keyword>]

---

## 5. Technical Areas

- canonical: <technical-keyword>
  group: technical
  aliases: [<alias-one>, <alias-two>]
  related: [<canonical-keyword>, <canonical-keyword>]

---

## 6. UI and UX

- canonical: <ui-ux-keyword>
  group: ui-ux
  aliases: [<alias-one>, <alias-two>]
  related: [<canonical-keyword>, <canonical-keyword>]

---

## 7. Integrations

- canonical: <integration-keyword>
  group: integration
  aliases: [<alias-one>, <alias-two>]
  related: [<canonical-keyword>, <canonical-keyword>]

---

## 8. Environment and Release

- canonical: <environment-keyword>
  group: environment
  aliases: [<alias-one>, <alias-two>]
  related: [<canonical-keyword>, <canonical-keyword>]

---

## 9. Issue Shapes

- canonical: <issue-shape-keyword>
  group: issue-shape
  aliases: [<alias-one>, <alias-two>]
  related: [<canonical-keyword>, <canonical-keyword>]

---

## Generator Notes

- Replace placeholders with real entries.
- Add as many entries as needed under each section.
- Remove example placeholder entries once real entries are added.
- Keep exact section order.
- Keep exact field names:
  - `canonical`
  - `group`
  - `aliases`
  - `related`
- Use canonical kebab-case terms.
- Use inline lists only, like `[a, b, c]`.
- Use `aliases: []` when none.
- Use `related: []` when none.
- `related` values must reference real canonical keywords present in the final file.
- Each canonical keyword must appear only once in the whole file.
- Avoid vague canonicals like `system`, `page`, `data`, `process`, `item`, `record`, `service`, `module`.
- Avoid overly broad aliases like `api`, `user`, `review`, `sync`, `admin`, `error` unless they are truly project-safe.
- Keep keywords reusable, stable, and broad enough to support multi-task matching.
- Allowed group values only:
  - `product-area`
  - `domain-entity`
  - `workflow`
  - `auth-access`
  - `technical`
  - `ui-ux`
  - `integration`
  - `environment`
  - `issue-shape`
