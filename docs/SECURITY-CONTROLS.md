# Security controls — the engineering backlog behind the legal pack

Working draft. **Every control on this page is `Not implemented`, because no code exists.**
That is the honest status and it is the point of the document.

The company's DPA annex and security page contain placeholder tokens of the form
`[[TOM_*]]` — technical and organisational measures that are promised to customers but not
yet described. Each token is a sentence a customer's security reviewer will read. This file
maps every one of them to the concrete engineering control that would make it true, where
that control would live, and what it depends on.

Filling a `[[TOM_*]]` token in the legal pack with words that are not backed by a row on
this page marked `Implemented` is a misrepresentation. That is the rule this document
exists to enforce.

## How to read the status column

| Status | Meaning | Requirement |
|---|---|---|
| `Not implemented` | Nothing exists | The legal placeholder must not be filled |
| `Partial` | Some of the control exists; the gap is named in the notes | The placeholder may be filled only with language that describes what actually exists |
| `Implemented` | The control exists and is verifiable | **The row must link to the file, workflow or runbook section that implements it.** CI fails otherwise |

CI enforcement lives in
[.github/workflows/docs-checks.yml](../.github/workflows/docs-checks.yml). It identifies a control
row as any table row containing a `[[TOM_*]]` token, reads its status cell, and fails the
build on any row marked `Implemented` that carries no relative link to an existing file.
It also fails on a control row with no recognised status cell. A promise without an
artefact does not merge.

## 1. Encryption and key management

| Token | What the legal pack promises | Engineering control | Status | Where it lives | Depends on |
|---|---|---|---|---|---|
| `[[TOM_TLS]]` | TLS 1.2 or higher for all external connections | TLS terminated at the platform edge, TLS 1.2 minimum with 1.3 preferred, HSTS with a long max-age, HTTP redirected not served, modern cipher suites only, and a scheduled external check that records the negotiated version | `Not implemented` | Infrastructure configuration; verified by an external scan recorded in the ops log | Hosting choice |
| `[[TOM_ENCRYPTION_AT_REST]]` | Encryption at rest for databases, object storage and backups | Provider-managed volume and bucket encryption on every store including backups and snapshots, plus application-level encryption for the `SECRET` fields in [DATA-MODEL.md](DATA-MODEL.md) so a database compromise does not yield usable OAuth tokens | `Not implemented` | Infrastructure configuration; secret field encryption in the data layer | Hosting choice, ADR 0003 |
| `[[TOM_KEY_MANAGEMENT]]` | Keys managed and rotated, not stored in source control | A managed key service holds the master key; per-workspace data keys are wrapped by it; rotation is a scheduled job with a documented procedure; no key material in the repository, in environment files committed anywhere, or in logs; secret scanning in CI as the backstop | `Not implemented` | Key service configuration, a rotation runbook entry, and the secret-scan job in CI | Hosting choice |

## 2. Access control

| Token | What the legal pack promises | Engineering control | Status | Where it lives | Depends on |
|---|---|---|---|---|---|
| `[[TOM_RBAC]]` | Role-based access control and least privilege for staff | Four customer-facing roles (`owner`, `admin`, `confirmer`, `viewer`) enforced on every workspace-scoped operation; internally, no standing production access — operator access is break-glass, time-boxed, justified, and written to the audit log as `operator.accessed`; no bulk export of customer content by any operator path | `Not implemented` | Authorisation layer, admin console, audit log | Data model |
| `[[TOM_MFA]]` | MFA on production and administrative systems | Hardware-key or TOTP MFA required on every account that can reach production: hosting, database, key service, source control, payment provider, model providers, DNS, email. No shared accounts. An inventory of these accounts with their MFA state, reviewed quarterly | `Not implemented` | An operator security inventory in the ops repository | Nothing; this one is available today |
| `[[TOM_CUSTOMER_SSO]]` | Customer-side SSO, provisioning and role management | v0: email-based authentication with roles and admin-managed invitations. SSO and SCIM are explicitly v2 on the roadmap. The security page must say that plainly rather than implying SSO exists | `Not implemented` | Authentication layer | Roadmap v2 |
| `[[TOM_CREDENTIALS]]` | Session management and credential storage | A memory-hard password hashing function with per-user salts and current parameters, if passwords exist at all; server-side sessions with rotation on privilege change, absolute and idle expiry, secure and HTTP-only cookies, CSRF protection on every state-changing request; tokens for integrations never rendered to a browser | `Not implemented` | Authentication layer | ADR 0003 |

## 3. Tenancy, environments and development

| Token | What the legal pack promises | Engineering control | Status | Where it lives | Depends on |
|---|---|---|---|---|---|
| `[[TOM_TENANT_ISOLATION]]` | Logical tenant separation in a multi-tenant architecture | The five-part strategy in [ARCHITECTURE.md](ARCHITECTURE.md) section 8: workspace id in every tenant-owned key, a scoped accessor that cannot build an unscoped query, database row-level security as a second line, cross-tenant reads confined to two audited code paths, and a build-failing test that detects any unscoped tenant query | `Not implemented` | Data access layer, database policies, test suite | ADR 0003 |
| `[[TOM_ENV_SEPARATION]]` | Production is separate from development and test, and production data is not copied into them | Separate projects, credentials and networks per environment; no path by which a developer machine can read production; development and test seeded exclusively from the anonymised fixture corpus in [TESTING-STRATEGY.md](TESTING-STRATEGY.md); a documented refusal to "just restore prod into staging to reproduce a bug" | `Not implemented` | Infrastructure configuration, seed tooling | Hosting choice |
| `[[TOM_CHANGE_MANAGEMENT]]` | Change management, code review, separation of duties | Protected `main`; no direct pushes; every change through a pull request with required review even when the author is the only engineer; CI green before merge; conventional commits; deployment from `main` only; a release log recording what shipped and when | `Not implemented` | Repository settings and CI workflows | Nothing; available today |
| `[[TOM_SECURE_SDLC]]` | Input validation and secure development practices | Schema validation on every external input including webhooks and model responses; parameterised queries only; output encoding in the UI; a dependency policy that prefers fewer dependencies; a short secure-coding checklist in the pull request template covering authorisation, tenancy scoping, logging of content, and idempotency | `Not implemented` | Pull request template, CI, code conventions | ADR 0003 |

## 4. Availability and resilience

| Token | What the legal pack promises | Engineering control | Status | Where it lives | Depends on |
|---|---|---|---|---|---|
| `[[TOM_BACKUP_RPO_RTO]]` | Backups, tested restore procedure, recovery objectives | Automated daily backups plus point-in-time recovery, retained per the `[[BACKUP_RETENTION_DAYS]]` value in the legal pack, stored in a different region from the primary; **a monthly restore into a scratch environment with the date and elapsed time recorded**; stated RPO and RTO published only after a restore has actually been timed | `Not implemented` | Hosting configuration, a restore runbook entry, the restore log | Hosting choice |
| `[[TOM_REDUNDANCY]]` | Redundancy and failover in the hosting environment | Managed database with automated failover; stateless application instances behind a load balancer with more than one instance; object storage with versioning; queues that survive a worker restart without losing work. Deliberately unpromised: multi-region active-active, which one person cannot operate | `Not implemented` | Hosting configuration | Hosting choice |
| `[[TOM_BCDR]]` | Business continuity and disaster recovery plan | A written plan covering total hosting-region loss, source-control loss, payment-provider loss and founder unavailability, including where credentials are held for someone else to recover the business; reviewed twice a year; the founder-unavailability section is the one most likely to be skipped and the one that matters most to a customer | `Not implemented` | A continuity document in the ops repository | Nothing; available today |

## 5. Testing, monitoring and vulnerability management

| Token | What the legal pack promises | Engineering control | Status | Where it lives | Depends on |
|---|---|---|---|---|---|
| `[[TOM_VULN_SCANNING]]` | Vulnerability scanning and dependency monitoring | Automated dependency alerts with a stated remediation window by severity; a lockfile committed; container base images rebuilt on a schedule rather than pinned forever; secret scanning on every push and on the full history; static analysis in CI | `Not implemented` | CI workflows and repository security settings | ADR 0003 |
| `[[TOM_PENTEST]]` | Penetration testing cadence | Honest position for v0: no third-party penetration test has been performed, and the security page says so. Trigger for the first test is the earlier of the first customer who requires one and the first enterprise-shaped deal; scope would be the web app, the OAuth flows and tenant isolation, with findings tracked to closure | `Not implemented` | A commissioned engagement; findings tracked as issues | Budget, first enterprise deal |
| `[[TOM_LOGGING]]` | Logging, alerting and monitoring | Structured logs with an **allowlist** of fields so customer content cannot be logged by accident; a request id on every entry; retention per `[[RETENTION_SECURITY_LOGS]]`; the audit log described in [DATA-MODEL.md](DATA-MODEL.md); alerting per [RUNBOOK.md](RUNBOOK.md) including authentication failures, integration error rates, 5xx rates and inference spend thresholds; a test that fails if a content-classed field reaches a log formatter | `Not implemented` | Logging layer, alert configuration, test suite | ADR 0003 |

## 6. Data handling

| Token | What the legal pack promises | Engineering control | Status | Where it lives | Depends on |
|---|---|---|---|---|---|
| `[[TOM_MINIMISATION]]` | Only the data needed for a feature is sent to model providers | Pre-filters drop bot, join, leave, emoji-only and link-only messages before any model call; prompts carry a bounded context window rather than whole threads; author identities are pseudonymised unless the task requires the real name; attachments and file contents are never fetched or sent in v0; the provider abstraction is the only egress point and it records what purpose each call served | `Not implemented` | Detection pipeline, provider abstraction | ADR 0004 |
| `[[TOM_RETENTION_AUTOMATION]]` | Retention and deletion automation | The scheduled sweeper described in [DATA-MODEL.md](DATA-MODEL.md), per table and per workspace policy, writing a `retention.swept` audit event with counts; a per-workspace retention setting between 7 and 90 days; content nulled in place with `content_purged_at` set; an alert if a sweep does not run or finds rows past their window | `Not implemented` | A scheduled worker | Data model |
| `[[TOM_SECURE_DELETION]]` | Secure deletion and media sanitisation | Deletion on disconnect within 24 hours for that source's content; whole-workspace deletion within the `[[DELETION_SLA_DAYS]]` window, executed in dependency order, with a completion record the customer can be shown; backups age out rather than being surgically edited, and the privacy policy must say so; media sanitisation is inherited from the hosting provider and is described as inherited, not as ours | `Not implemented` | A deletion job plus a runbook entry | Data model |

## 7. People, vendors and incidents

| Token | What the legal pack promises | Engineering control | Status | Where it lives | Depends on |
|---|---|---|---|---|---|
| `[[TOM_PERSONNEL]]` | Background checks and confidentiality agreements | Today the company is one person, and the security page should say that rather than implying an HR function. The control to build before the first contractor: a signed confidentiality and IP agreement, a background check where lawful and proportionate, an access checklist at start, and a revocation checklist at end with a target of same day | `Not implemented` | An onboarding and offboarding checklist in the ops repository | First hire or contractor |
| `[[TOM_TRAINING]]` | Security awareness training | Annual training for anyone with production access, recorded with a date. For a solo founder this is a short self-administered review against a written checklist — phishing, credential handling, device encryption, screen lock, incident reporting. Small, but a reviewer will ask and "none" is a poor answer | `Not implemented` | A training record in the ops repository | Nothing; available today |
| `[[TOM_VENDOR_MANAGEMENT]]` | Subprocessor due diligence, contracts, periodic review | A subprocessor register listing purpose, data categories, region, DPA status and review date; a DPA with every subprocessor that touches customer content; an annual review; the customer notice period from the legal pack honoured on any change; a rule that no vendor touches customer content before it is on the register | `Not implemented` | The subprocessor register in the legal pack, plus a review calendar entry | Vendor choices |
| `[[TOM_INCIDENT_RESPONSE]]` | Documented process, roles, and customer notification path | A written plan with severity levels, the single decision-maker named, a customer notification path meeting the `[[BREACH_NOTICE_HOURS]]` commitment, a communications template, an evidence-preservation step, and a required post-incident note. Rehearsed once, on paper, before launch: a plan first read during an incident is not a plan. See [RUNBOOK.md](RUNBOOK.md) | `Not implemented` | An incident response document plus the runbook | Nothing; available today |
| `[[TOM_PHYSICAL]]` | Physical security | Inherited entirely from the hosting provider's data centres, and described as inherited with the provider's own attestations referenced. Locally: full-disk encryption, screen lock, no production credentials on any device without them | `Not implemented` | Hosting provider documentation, plus a device baseline note | Hosting choice |

## 8. Sequencing

Ordered by what a customer's security reviewer notices first, weighted by what is cheap to
do before there is any code.

| Order | Controls | Why now | Cost |
|---|---|---|---|
| 1 | `[[TOM_MFA]]`, `[[TOM_CHANGE_MANAGEMENT]]`, secret scanning under `[[TOM_VULN_SCANNING]]` | Available today, no code required, and they prevent the mistakes that end small companies | Hours |
| 2 | `[[TOM_TENANT_ISOLATION]]`, `[[TOM_LOGGING]]`, `[[TOM_MINIMISATION]]` | Structural. Retrofitting any of the three means touching every query, every log line and every prompt | Design cost only, if decided before the first line |
| 3 | `[[TOM_ENCRYPTION_AT_REST]]`, `[[TOM_KEY_MANAGEMENT]]`, `[[TOM_CREDENTIALS]]` | Required before any real customer token is stored | Days |
| 4 | `[[TOM_RETENTION_AUTOMATION]]`, `[[TOM_SECURE_DELETION]]` | The privacy policy is unenforceable without them, and they are the first thing a data-protection question tests | Days |
| 5 | `[[TOM_BACKUP_RPO_RTO]]`, `[[TOM_REDUNDANCY]]`, `[[TOM_INCIDENT_RESPONSE]]`, `[[TOM_BCDR]]` | Needed before the first paying customer depends on the service | Days, plus a recurring monthly restore test |
| 6 | `[[TOM_PENTEST]]`, `[[TOM_PERSONNEL]]`, `[[TOM_CUSTOMER_SSO]]` | Triggered by a customer or a hire, not by a calendar | Money, or a hire |

## 9. What this document is not

- It is not a claim of compliance. The company holds no certification and the security page
  says so.
- It is not a substitute for the legal pack. When a control here and a sentence in the DPA
  disagree, the DPA is the promise and this page is the bug.
- It is not fixed. Every row gains a link and a status change as the control is built, and
  every status change is a pull request that a reviewer can check.
