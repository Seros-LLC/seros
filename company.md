# Seros — Company Overview

## Summary

Seros is a Vercel-hosted SaaS platform that transforms selected Slack-channel commitments into human-approved task tracker items. It bridges the gap between async team communication (Slack) and structured, auditable task management.

## Mission

Turn Slack channel commitments into verified, human-reviewed tasks — with full audit trail and production-ready deployment.

## Core Product

- **Slack → Tracker pipeline**: Monitors Slack channels for commitment mentions and surfaces them as tracked tasks.
- **Human approval gate**: Every task enters a review queue before it's marked complete — no action is taken without explicit consent.
- **Vercel deployment**: The app deploys to `app.seros.dev` on Vercel, with a single-environment, zero-downtime production setup.
- **Audit trail**: All task state changes are logged and immutable, providing a compliance-ready record.

## Key Metrics (as of this write)

| Metric | Value |
|--------|-------|
| Hosting | Vercel (app.seros.dev) |
| Framework | TypeScript/Node |
| Deployment status | BLOCKED — production env vars must satisfy fail-closed boot contract |
| Integration readiness | Real (Slack, not demo flows) |
| Security posture | Single reviewable migration-backed commits; push/deploy blocked until env gates pass |

## Status

- **Production-ready**: Not yet. The codebase has a `fail-closed` boot contract that requires production environment variables to be set before any deploy can proceed.
- **Integration readiness**: Real (Slack integration, not synthetic demo flows).
- **Security work**: Single reviewable migration-backed commits; push/deploy is blocked until production env vars satisfy the fail-closed boot contract.

## Next Steps

1. Set production environment variables satisfying the fail-closed boot contract.
2. Run `npm run verify` (typecheck + tenancy check + unit tests).
3. Push and deploy to Vercel.

---

*Generated from repo context at `/home/jrdur/repos/seros/company.md`*