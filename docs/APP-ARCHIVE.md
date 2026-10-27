# Archived application implementation

The separate `Seros-LLC/app` repository was the implementation of the paused Slack-to-tracker
product. It has been retired and deleted after the essential implementation record was moved
here. The product specification remains in this repository; it does not describe a deployed
service.

## Preserved implementation facts

- TypeScript on Node.js, with Express, Drizzle ORM, SQLite locally, and a Postgres-shaped
  production path.
- Server-rendered HTML with no client framework.
- `WorkspaceScope` structurally enforced tenant access, with a tenancy check in CI.
- A schema-level confirmation gate: a tracker task required a human `Confirmation` id.
- Provider access isolated under `src/provider/`, with metering and budget checks before model
  calls.
- Slack channel selection was an explicit allowlist; unselected channels were not persisted.
- The repository carried a 217-example synthetic detection evaluation and offline tests.

These facts are implementation evidence from the retired repository, not a claim that the
product is currently running or supported.

## Verification before retirement

The final local verification run completed successfully on the retired implementation:

- TypeScript typecheck: passed.
- Tenant-scope check: passed.
- Test suite: 247 tests, 234 passed, 13 skipped because `SEROS_PG_TEST_URL` was not set, and
  0 failed.

The Postgres-only tests were not run because no disposable Postgres URL was available.

The full historical product brief is preserved in [docs/APP-PRODUCT-BRIEF.md](APP-PRODUCT-BRIEF.md).

The current company positioning is AI and agentic consulting. The application was paused, not
sold, and not deployed; its implementation repository is no longer a public deliverable.

## Assets not copied

- The application icons are duplicates of assets already maintained by the website repository.
- `seros-hero.png` is duplicated by the website and remains there as the canonical brand art.
- The application `og-image.jpg` was unused by application source and carried superseded
  product positioning, so it was not migrated.

Do not recreate the deleted application repository from this summary. Use the architecture,
data model, ADRs, and testing strategy in this repository as the authoritative specification.
