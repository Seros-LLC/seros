# 4. Model provider strategy

## Status

**Proposed. Not accepted.** No provider is chosen and none is named here as chosen. What is
proposed is the *shape* of the dependency: an abstraction from the first call, a cheap-first
cascade, and a tested ability to leave.

## Context

Inference is the largest variable cost in the product and the only dependency that can
change price, quality, availability and terms without notice. The business plan's gross
margin depends on cost per action; the security page and the DPA name model providers as
subprocessors; the "not doing" list rules out training a model. So the company rents
inference and must stay able to change landlord.

Four risks, all of which have been observed across the industry generally, and none of which
require predicting any specific vendor's behaviour:

| Risk | Effect if unmitigated |
|---|---|
| **Price changes** | Gross margin moves without a product change. If the code is welded to one provider, the only response is a price rise to customers |
| **Quality changes** | A model version is deprecated or silently updated; detection precision moves and the acceptance-rate metric drops with no code change on our side |
| **Availability** | A provider outage stops drafting entirely. With one provider, that is a full feature outage |
| **Terms and compliance** | Data handling, retention, training terms, regional availability and subprocessor disclosure obligations change. A customer's security review may exclude a specific vendor outright |

There is also a customer-facing reality: enterprise-ish buyers in the ICP ask which model
provider is used and whether their data trains it. Being able to answer precisely — and to
change the answer if a customer's policy requires it — is a sales asset, not just hygiene.

Against all of that: premature abstraction is a real cost. A layer that tries to unify
every provider feature becomes a worse SDK, and building it for a hypothetical migration is
waste. The proposal below therefore abstracts the narrowest possible surface: the three
calls in [ARCHITECTURE.md](../ARCHITECTURE.md) section 5, and nothing else.

## Decision (proposed)

**1. A provider abstraction exists from the first model call.** All model access goes
through one internal interface. No provider SDK type appears anywhere else in the codebase.
The interface is deliberately small:

| Operation | Inputs | Outputs |
|---|---|---|
| `complete` | prompt version id, rendered messages, response schema, model tier, max input tokens, max output tokens, timeout, workspace id, purpose | validated structured object, token counts, model id, latency, outcome |

Notably absent: streaming, tool calling, assistants, files, embeddings, provider-specific
parameters. If v1 needs one of them, it is added to the interface deliberately, for all
implementations, or the feature does not ship.

**2. Model tiers are named by role, not by vendor.** The codebase refers to `cheap`,
`standard` and, if needed, `careful`. The mapping from tier to a concrete model lives in
configuration, versioned, with a price per token, and is changeable without a deploy.
Prompts reference tiers; nothing else does.

**3. Cheap-model-first cascade.** Detection pass A runs on the `cheap` tier over batched
messages. Only survivors reach the `standard` tier for drafting. Escalation to a more
capable tier happens on explicit conditions — low confidence, schema validation failure,
or an evaluation-driven rule — never by default. The cascade is a cost decision and a
quality decision at once, and both are measured on the golden set before it changes.

**4. Every call is metered and budget-checked inside the abstraction.** The budget check
happens before the network call. `ActionMeter` rows are written for every outcome including
`budget_blocked` and `provider_error`. This is rule 3 from the repository README, and the
abstraction is where it becomes structural rather than a habit.

**5. Prompts are versioned artefacts, not strings in code.** Each prompt has an id and a
version; the version is recorded on every candidate, draft and meter row. Changing a prompt
is a reviewable change with an offline evaluation attached
([TESTING-STRATEGY.md](../TESTING-STRATEGY.md)).

**6. No provider is named as chosen in this repository.** The concrete choice is made when
the first spike runs, is recorded in the subprocessor list because customers are entitled
to know, and is expected to change at least once.

**7. No customer content on training-permitted terms.** A provider may only be used under
terms that exclude customer content from training. This is a promise in the messaging and
on the security page. A provider whose terms do not allow that is not a candidate,
whatever it costs or scores.

**8. Data minimisation before the boundary.** What crosses to a provider is the minimum
window of text needed, with author identities pseudonymised where the task does not require
real names. This is the engineering answer to `[[TOM_MINIMISATION]]`; see
[SECURITY-CONTROLS.md](../SECURITY-CONTROLS.md).

**9. Failure behaviour is defined at the abstraction, not at the call site.** Timeout,
bounded retry with jitter, schema validation, dead-letter on repeated invalid output, and a
circuit breaker that pauses the detection queue rather than hammering a degraded provider.
On outage, drafting queues; confirmation and tracker writes keep working
([RUNBOOK.md](../RUNBOOK.md)).

## The exit test

The abstraction is worth nothing if it has never been exercised. So the design is
falsifiable:

> **Can a second provider be added, evaluated on the golden set, and promoted to serve the
> `cheap` tier in production, by one person, in one working day?**

Run it deliberately, at least once before the first paying customer and at least twice a
year after. The run must include:

1. Implement the interface for the second provider. If this takes more than half a day,
   the interface has leaked.
2. Score the golden set on both providers and compare precision, recall and cost per
   thousand messages.
3. Flip the tier mapping in configuration, in a canary workspace first, with no deploy.
4. Confirm the meter attributes cost correctly to the new provider and that budget caps
   still stop calls.
5. Confirm the subprocessor list and the customer-facing notification path are updated,
   because a provider change is a subprocessor change with contractual notice obligations.

Failing the exit test is a finding to fix, not an argument to abandon the abstraction.

## Consequences

**Good**

- Price, quality or terms changes become a configuration change plus an evaluation run.
- Outages degrade one feature instead of stopping the product, and the status page can say
  something true and specific.
- Cost attribution per workspace, per purpose and per model exists from day one, so the
  cost-per-action metric is measured rather than assumed.
- A customer security review can be answered precisely, and an unacceptable-vendor
  objection has an answer that does not require a rewrite.

**Costs**

- Provider-specific capabilities are unavailable by default. Some of them are genuinely
  useful, and choosing not to use them costs quality or effort somewhere else.
- A thin abstraction still has to be maintained, and there is a standing temptation to
  widen it until it is a bad SDK. The interface table above is the guard.
- Running the exit test costs real days that produce no visible feature.
- Multiple providers mean multiple subprocessor entries, multiple sets of terms to track,
  and more surface for the vendor-management control.

**Neutral**

- This ADR says nothing about which model is best. That is an evaluation question with a
  measurable answer, re-asked every time the golden set is run, and it belongs in the
  evaluation record rather than in an architecture decision.
