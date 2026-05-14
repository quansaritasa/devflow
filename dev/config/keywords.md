# Keywords

Canonical keyword taxonomy for task indexing and related-task search.

Use canonical kebab-case terms.
Store canonical keywords only.
Use aliases for matching.
Keep terms reusable and broad enough to cover multiple tasks.

---

## 1. Product Areas

- canonical: admin-portal
  group: product-area
  aliases: [admin, admin site, admin ui]
  related: [user, branding, reviewer]

- canonical: auth-api
  group: product-area
  aliases: [auth api, authentication]
  related: [login, permissions, user-sync, auth-db]

- canonical: dispatch-api
  group: product-area
  aliases: [dispatch api, api]
  related: [dispatch, reviewer, api-endpoint]

- canonical: field-app
  group: product-area
  aliases: [field app, tablet app, dr site app, ipad]
  related: [daily-report, signature-placement, logged-out]

- canonical: forney
  group: product-area
  aliases: []
  related: []

- canonical: lims
  group: product-area
  aliases: [lims app]
  related: [dispatch, daily-report, ctr, reviewer]

- canonical: sync
  group: product-area
  aliases: [sync service]
  related: [user-sync, sync-failure, vantage-point]

---

## 2. Domain Entities

- canonical: account
  group: domain-entity
  aliases: [user account]
  related: [login, password-reset, account-restore]

- canonical: branding
  group: domain-entity
  aliases: [branding entity, brandings]
  related: [admin-portal, company, region, office]

- canonical: company
  group: domain-entity
  aliases: []
  related: [region, office, reviewer]

- canonical: cst-sample
  group: domain-entity
  aliases: []
  related: []

- canonical: ctr
  group: domain-entity
  aliases: []
  related: [daily-report, pending-validation, update-max]

- canonical: daily-report
  group: domain-entity
  aliases: [dr, daily report, dispatch report]
  related: [dispatch, technical-review, logged-out]

- canonical: dispatch
  group: domain-entity
  aliases: []
  related: [daily-report, reviewer, technical-review]

- canonical: distribution-list
  group: domain-entity
  aliases: [email list]
  related: [email-notification, approved]

- canonical: form
  group: domain-entity
  aliases: [master form]
  related: [pdf, daily-report]

- canonical: lab-sample
  group: domain-entity
  aliases: []
  related: [sampled-date]

- canonical: office
  group: domain-entity
  aliases: [office code]
  related: [region, company, reviewer]

- canonical: project
  group: domain-entity
  aliases: [project number]
  related: [dispatch, reviewer]

- canonical: region
  group: domain-entity
  aliases: [region code]
  related: [office, company, reviewer]

- canonical: reviewer
  group: domain-entity
  aliases: [technical reviewer, dispatch reviewer, review]
  related: [technical-review, reviewer-assignment, signature-placement]

- canonical: sampled-date
  group: domain-entity
  aliases: []
  related: [lab-sample]

- canonical: signature
  group: domain-entity
  aliases: [remote-signature]
  related: [signature-placement, footer-signature, technical-review]

- canonical: technician
  group: domain-entity
  aliases: [tech]
  related: [signature-placement, daily-report]

- canonical: user
  group: domain-entity
  aliases: [employee]
  related: [user-sync, permissions, account]

---

## 3. Workflow

- canonical: approved
  group: workflow
  aliases: [approval]
  related: [technical-review, distribution-list, email-notification]

- canonical: canceled
  group: workflow
  aliases: [cancelled, cancel]
  related: []

- canonical: logged-out
  group: workflow
  aliases: [logged out]
  related: [logout, daily-report, signature-placement]

- canonical: logout
  group: workflow
  aliases: [log out]
  related: [logged-out, logout-blocked]

- canonical: logout-blocked
  group: workflow
  aliases: []
  related: [logout, pending-validation, ctr]

- canonical: pending-technical-review
  group: workflow
  aliases: [pending technical review]
  related: [technical-review, reviewer]

- canonical: pending-validation
  group: workflow
  aliases: []
  related: [ctr, update-max, logged-out]

- canonical: rejected
  group: workflow
  aliases: [rejection]
  related: [technical-review, resubmit]

- canonical: resubmit
  group: workflow
  aliases: [resubmitted]
  related: [technical-review, rejected]

- canonical: submitted
  group: workflow
  aliases: []
  related: [technical-review, pending-technical-review]

- canonical: technical-review
  group: workflow
  aliases: [technical review, review flow]
  related: [reviewer, approved, rejected, resubmit]

- canonical: update-max
  group: workflow
  aliases: [update max]
  related: [ctr, pending-validation]

---

## 4. Auth and Access

- canonical: account-restore
  group: auth-access
  aliases: [restore account]
  related: [account, login]

- canonical: authorization
  group: auth-access
  aliases: [access control]
  related: [permissions, unauthorized]

- canonical: credentials
  group: auth-access
  aliases: [login info]
  related: [login, account]

- canonical: forgot-password
  group: auth-access
  aliases: [forgot password]
  related: [password-reset, login]

- canonical: login
  group: auth-access
  aliases: [sign in]
  related: [credentials, authorization, account]

- canonical: otp
  group: auth-access
  aliases: [one-time code, one time code]
  related: [login, password-reset]

- canonical: password-reset
  group: auth-access
  aliases: [reset password]
  related: [forgot-password, login, account]

- canonical: permissions
  group: auth-access
  aliases: [access rights]
  related: [authorization, super-admin, reviewer-assignment]

- canonical: reviewer-assignment
  group: auth-access
  aliases: [assign reviewer]
  related: [reviewer, technical-review, authorization]

- canonical: super-admin
  group: auth-access
  aliases: [super admin]
  related: [permissions, authorization]

- canonical: unauthorized
  group: auth-access
  aliases: [permission error]
  related: [authorization, permissions]

- canonical: user-sync
  group: auth-access
  aliases: [user sync, sync users, automatic users creation]
  related: [vantage-point, deltek, auth-api, auth-db]

---

## 5. Technical Areas

- canonical: 500-error
  group: technical
  aliases: [server error]
  related: [exception]

- canonical: api-endpoint
  group: technical
  aliases: [endpoint, api endpoint]
  related: [dispatch-api, auth-api, crud]

- canonical: backend
  group: technical
  aliases: [server]
  related: [api-endpoint, database]

- canonical: cpu-utilization
  group: technical
  aliases: [cpu, high cpu]
  related: [performance]

- canonical: crud
  group: technical
  aliases: []
  related: [api-endpoint, admin-portal]

- canonical: database
  group: technical
  aliases: [db, lims-db]
  related: [stored-procedure, performance, auth-db]

- canonical: email-notification
  group: technical
  aliases: [email, notification email]
  related: [distribution-list, approved]

- canonical: exception
  group: technical
  aliases: [error]
  related: [500-error, validation]

- canonical: file-upload
  group: technical
  aliases: [upload]
  related: [pdf]

- canonical: font-rendering
  group: technical
  aliases: []
  related: [frontend, pdf]

- canonical: frontend
  group: technical
  aliases: [ui]
  related: [reviewer-page, search-filter, table-alignment]

- canonical: migration
  group: technical
  aliases: []
  related: [github, gitlab, azure-ad]

- canonical: pdf
  group: technical
  aliases: [pdf-export]
  related: [signature-placement, footer-signature, daily-report]

- canonical: performance
  group: technical
  aliases: []
  related: [database, cpu-utilization]

- canonical: refactor
  group: technical
  aliases: []
  related: [backend, api-endpoint]

- canonical: revert
  group: technical
  aliases: []
  related: [refactor]

- canonical: security
  group: technical
  aliases: []
  related: [authorization, permissions]

- canonical: stored-procedure
  group: technical
  aliases: [stored proc, sp]
  related: [database, performance, user-sync]

- canonical: sync-failure
  group: technical
  aliases: []
  related: [sync, user-sync]

- canonical: testing
  group: technical
  aliases: [qa]
  related: [qa-dev, qa-uat, qa-production]

- canonical: validation
  group: technical
  aliases: [validation error]
  related: [exception]

---

## 6. UI and UX

- canonical: delete-confirmation
  group: ui-ux
  aliases: [confirm delete]
  related: [crud, admin-portal]

- canonical: detail-view
  group: ui-ux
  aliases: []
  related: [frontend]

- canonical: dropdown
  group: ui-ux
  aliases: []
  related: [frontend]

- canonical: footer-signature
  group: ui-ux
  aliases: []
  related: [signature, pdf]

- canonical: list-view
  group: ui-ux
  aliases: []
  related: [frontend]

- canonical: reviewer-page
  group: ui-ux
  aliases: []
  related: [reviewer, technical-review, frontend]

- canonical: search-filter
  group: ui-ux
  aliases: [search, filter]
  related: [reviewer-page, frontend]

- canonical: signature-placement
  group: ui-ux
  aliases: [signature position]
  related: [signature, pdf, technical-review]

- canonical: table-alignment
  group: ui-ux
  aliases: [ui alignment, row alignment]
  related: [frontend]

---

## 7. Integrations

- canonical: auth-db
  group: integration
  aliases: [auth database]
  related: [auth-api, user-sync, reviewer]

- canonical: azure-ad
  group: integration
  aliases: [azure active directory, aad, azure]
  related: [login, migration]

- canonical: deltek
  group: integration
  aliases: [deltek org]
  related: [vantage-point, user-sync]

- canonical: external-api
  group: integration
  aliases: [amazon-s3]
  related: [sync]

- canonical: github
  group: integration
  aliases: [git hub]
  related: [migration, gitlab, jenkins]

- canonical: gitlab
  group: integration
  aliases: []
  related: [github, jenkins]

- canonical: jenkins
  group: integration
  aliases: []
  related: [github, gitlab]

- canonical: salesforce
  group: integration
  aliases: [sales force]
  related: [sync]

- canonical: vantage-point
  group: integration
  aliases: [vp, vantagepoint, vantagepoints]
  related: [deltek, user-sync]

---

## 8. Environment and Release

- canonical: dev-environment
  group: environment
  aliases: [development environment]
  related: [qa-dev]

- canonical: hotfix
  group: environment
  aliases: []
  related: [release]

- canonical: production
  group: environment
  aliases: [prod]
  related: [qa-production]

- canonical: qa-dev
  group: environment
  aliases: [dev qa]
  related: [testing]

- canonical: qa-production
  group: environment
  aliases: [production qa]
  related: [testing, release]

- canonical: qa-uat
  group: environment
  aliases: [uat]
  related: [testing, release]

- canonical: release
  group: environment
  aliases: [release build]
  related: [qa-uat, qa-production]

- canonical: uat-environment
  group: environment
  aliases: [uat environment]
  related: [qa-uat]

---

## 9. Issue Shapes

- canonical: bug
  group: issue-shape
  aliases: []
  related: [exception, validation]

- canonical: feature
  group: issue-shape
  aliases: []
  related: []

- canonical: ui-update
  group: issue-shape
  aliases: []
  related: [frontend]

