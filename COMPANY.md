# Seros — Company Overview

Seros, LLC is an AI and agentic consulting firm based in Georgia, USA. We advise businesses
on where AI and AI agents genuinely pay off, then design, build and run them to a fixed scope,
with a person approving every consequential step.

Services: AI strategy and readiness assessment, advisory retainer, agentic workflow
automation, AI-native custom CRM, custom builds and integrations, and care plans.

Positioning history: SaaS product → solution development (2026-09-19,
`business/PIVOT-DECISION.md`) → AI and agentic consulting (2026-09-25,
`business/DECISION-AI-CONSULTING.md`).

## What we sell

| Stage | What happens |
|---|---|
| Discovery | A paid discovery sprint produces a written specification the client owns, whether or not we build it. |
| Build | Fixed scope, agreed before work starts. No open-ended hourly drift. |
| Handover | Client owns the code, the infrastructure, and the accounts. No lock-in. |
| Maintain | Optional retainer for the system after delivery. |

Revenue is project fees and retainers, not subscription. The only publicly stated number is
the professional services rate in `website/site.json` (`PROF_SERVICES_RATE`, $150/hour).
Project prices are quoted after discovery.

## Status

- **Clients shipped:** none. The site claims no clients, logos, testimonials, or results.
- **Services motion:** live on seros.dev — services, work, engagements, and contact pages.
- **Target market:** not yet settled (industry and business size are open questions).
- **Delivery model:** not yet settled (solo, subcontracted, or hired-for). No capacity
  claim appears publicly until it is.

## The paused product

The Slack-to-tracker application in `app/` is **paused, not cancelled**. It is not
deployed, not sold, and has no sign-up. It remains public as evidence of delivery
capability, and it is referenced from /work on the site.

Its engineering invariant still holds and is the thing worth showing: no task is written to
a customer's tracker without a recorded human confirmation, enforced at the type level
rather than by convention.

Undecided: whether app.seros.dev is eventually shut down, open-sourced, or resumed.

## Repositories

| Repo | Visibility | What it is |
|---|---|---|
| `website` | public | seros.dev — marketing site and generated legal pages |
| `app` | public | The paused Slack-to-tracker application |
| `seros` | public | Product specification: architecture, data model, ADRs, security controls |
| `.github` | public | Org profile and community health files |
| `business` | private | Business plan, pricing internals, metrics, risk register |
| `legal` | private | Policies, contracts, MSA/SOW templates, formation checklist |

## Open assumptions

Tracked in `business/METRICS.md`:

- **PV1** — businesses in the founder's reachable network will pay for scoped custom builds.
- **PV2** — a paid discovery sprint is an acceptable first step for buyers.
- **PV3** — $150/hour is defensible for this market.

If PV1 is wrong, the services motion has no pipeline and the pivot buys nothing.
