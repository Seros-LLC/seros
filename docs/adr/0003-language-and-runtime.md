# 3. Language and runtime

## Status

**Proposed. Not accepted.** No language, runtime, framework or hosting target has been
chosen. This ADR exists so that the choice is made deliberately, with evidence, rather than
by whoever writes the first file. Nothing in this repository may assume an answer.

## Context

The decision has to be made by one person who will build, operate and support the result
alone for at least a year, and who may later need to hand parts of it to a contractor or a
first hire. That constrains the decision more than any technical property does.

The system's actual demands are modest and specific:

| Demand | What it needs |
|---|---|
| Slack webhooks and OAuth | An ordinary HTTP server with signature verification |
| A confirm queue UI | Server-rendered pages are sufficient; there is no rich client requirement in v0 |
| Background workers | Reliable queues, retries, scheduled jobs, dead-lettering |
| Model calls | HTTP clients, streaming optional, structured output validation, tight timeouts |
| A relational store | Transactions, unique constraints, JSON columns, row-level security preferred |
| Evaluation harness | Running a golden set offline, scoring precision and recall, comparing prompt versions |
| One-person operability | Small deployment surface, boring failure behaviour, good stack traces |

Nothing here needs unusual performance. The expensive part of a request is a remote model
call, so raw language throughput is close to irrelevant. What matters is iteration speed,
how quickly one person can debug production at 2am, the maturity of the model and
integration tooling, and whether a future hire is plausible.

The counter-pressure: the founder ships an iOS app under a separate company, so there is
existing competence somewhere in that direction. Familiarity is a legitimate input to this
decision and should be weighed openly rather than pretended away.

## Options

### Option A — a dynamic, batteries-included web stack

*The family of choices where a mature framework provides routing, ORM, migrations, admin,
background jobs and templating out of the box.*

| Dimension | Assessment |
|---|---|
| Iteration speed | Highest. Whole features exist as framework conventions; less code to write and to own |
| Hiring pool | Large, and cheap to hire from at contractor level |
| LLM tooling maturity | Strongest in this family, particularly for evaluation harnesses, structured output validation and notebook-style iteration on prompts |
| Hosting cost | Low to moderate. More instances for the same load, but v0 load is trivial and the model bill dominates the compute bill |
| Operational risk | Runtime type errors reach production more easily. Mitigation is tests and gradual typing, which costs discipline |
| Fit to this system | Very good. The work is glue, HTTP, queues and prompts, which is what these stacks are for |

### Option B — a statically typed, single-language front and back stack

*The family where the same language runs the server and any browser code, with types across
the boundary.*

| Dimension | Assessment |
|---|---|
| Iteration speed | High once set up; slower at the start because more is assembled by hand |
| Hiring pool | Very large, especially for anyone who can also touch the UI |
| LLM tooling maturity | Good and improving; provider SDKs are first class, evaluation tooling is thinner than Option A |
| Hosting cost | Low. Efficient enough at this scale that it is not a differentiator |
| Operational risk | Compile-time checks catch a real class of integration bugs, which matters when one person reviews their own code |
| Fit to this system | Good. The risk is assembling a bespoke framework out of parts and then owning all of it |

### Option C — a compiled, statically typed backend with a minimal server-rendered UI

*The family chosen for operational simplicity: one binary, low memory, explicit errors.*

| Dimension | Assessment |
|---|---|
| Iteration speed | Lowest of the three for product work. More ceremony per feature, less magic |
| Hiring pool | Smaller, and more expensive per hour, though the average candidate is stronger on operations |
| LLM tooling maturity | Thinnest. Provider SDKs exist; evaluation and prompt-iteration tooling would largely be built here |
| Hosting cost | Lowest, and the deployment story is genuinely simple |
| Operational risk | Best. Predictable, few runtime surprises, excellent long-running worker behaviour |
| Fit to this system | Fine, but optimises for a constraint (efficiency) that this product does not have, at the cost of the one it does (iteration speed) |

### Summary

| | A: dynamic batteries-included | B: typed one-language | C: compiled backend |
|---|---|---|---|
| Time to first confirmed task | Fastest | Middle | Slowest |
| LLM and eval tooling | Strongest | Adequate | Weakest |
| Contractor availability | High | Highest | Lower |
| Ops burden for one person | Middle | Middle | Lowest |
| Risk of building a bespoke framework | Low | High | Middle |
| Cost of being wrong | Moderate; the expensive parts are prompts, integrations and data, which port | Moderate | Moderate |

Worth stating: **the durable assets of this product are not in the language.** The prompts,
the golden set, the routing data, the integration knowledge and the customer relationships
all survive a rewrite. That lowers the stakes of this decision and is an argument against
agonising over it.

## Decision

None yet. Deliberately open.

**What evidence would decide it:**

1. **A timeboxed spike, two days per candidate, maximum two candidates.** Build the same
   vertical slice in each: receive a Slack event with signature verification, persist it,
   enqueue a job, call one model provider with a validated structured response, render a
   one-row confirm queue, write to a tracker sandbox with an idempotency key. Whichever
   produces a working slice with less unfamiliar code wins on iteration speed, measured in
   hours and lines, not opinion.
2. **The evaluation harness test.** Write a scorer for the golden set described in
   [TESTING-STRATEGY.md](../TESTING-STRATEGY.md) in each candidate. If one candidate makes
   offline evaluation obviously easier, that is decisive, because evaluation is a weekly
   activity for the life of the product and everything else is a one-time cost.
3. **The 2am test.** Deliberately break the slice: a bad token, a provider timeout, a
   malformed model response. Which stack tells the truth fastest, from a phone?
4. **Honest familiarity score.** Rate current fluency per candidate out of five, before the
   spikes, and write it down. A stack the founder is fluent in should win any near-tie; at
   one person, months of fluency beat a marginal technical property.
5. **Contractor sanity check.** Ask two contractors what they would charge to add a second
   tracker integration in each candidate. If the answers differ by more than a factor of
   two, that is a hiring-pool signal worth having.

**Deadline:** decide before the first line of application code. If the spikes are not done,
the decision is still open, and the correct action is to do the spikes, not to start
building in whatever was used for the spike that felt best.

## Consequences

Recorded once a decision is made. Whatever is chosen, three consequences apply in advance:

- The provider abstraction in [ADR 0004](0004-model-provider-strategy.md) must exist in the
  chosen stack from the first model call, since it is the boundary that keeps the model
  decision reversible.
- The tenant-scoping requirement in [ARCHITECTURE.md](../ARCHITECTURE.md) section 8 must be
  expressible as a structural constraint in the chosen data layer, not as a convention.
  If a candidate cannot do that, it loses.
- The choice is recorded here as a superseding ADR, with the spike measurements attached,
  so that the next person can see whether the reasoning still holds.
