# Runbook — on-call for one person

Working draft. Nothing is built, so nothing here has been executed. It is written now
because the operations checklist is right that runbooks get written the first time an alert
fires, and the first time is the worst time to be writing one.

**The operating assumption is honest:** one person, business hours Eastern, best effort
outside them, until there are enough customers and enough people to promise more. Say that
on the status page. Do not imply 24/7 coverage that does not exist.

## 0. The three questions, in order

Before touching anything:

1. **Is anything being written into a customer's systems that a human did not confirm?**
   If yes, stop that first. Nothing else on this page outranks it.
2. **Is customer content leaking anywhere it should not be** — a log, an error report, a
   support ticket, a screenshot? If yes, contain it before diagnosing.
3. **Is money being spent at a rate that is not survivable?** If yes, hit the global spend
   cap and then diagnose.

Everything else is a degraded service, which is uncomfortable rather than dangerous.

## 1. Alerts that should exist

Two tiers. Page means the phone makes a noise that overrides silent mode. Ticket means it
waits for morning. The single greatest risk to a one-person on-call is alert fatigue, so the
ticket list is deliberately longer than the page list.

### Page

| Alert | Condition | Why it pages |
|---|---|---|
| Service down | Health check failing for 2 consecutive minutes | Customers cannot confirm |
| Database unreachable | Connection failures from app or workers | Everything stops |
| Authentication broken | Login error rate above baseline for 5 minutes | Nobody can get in, and it looks like a breach until proven otherwise |
| 5xx rate above baseline | Sustained 5 minutes | Something shipped or something broke |
| Unconfirmed write detected | Any task write attempted without a confirmation id | A violation of the product's central promise. This should be impossible; if it fires, it is the most serious alert in the system |
| Inference spend over the daily global cap | Meter crosses 100% | Existential cost risk |
| Confirmed items stuck | Any confirmation queued for a tracker write for over 30 minutes | The customer confirmed and nothing happened, which is the worst kind of silent failure |
| Retention sweep failed twice | Two consecutive scheduled runs failed | A retention promise is being broken while the service looks healthy |
| Security signals | Secret detected in a push, unexpected production access, MFA disabled on an operator account | Containment cannot wait |

### Ticket

| Alert | Condition |
|---|---|
| Inference spend at 50% and 80% of daily cap | Trend warning, not an emergency |
| One workspace's budget cap reached | Affects one customer; email them, do not wake up |
| Model provider elevated error rate | Drafting queues; the rest works |
| Tracker or Slack 429 rate elevated | Backoff is doing its job |
| A single OAuth token expired or revoked | Customer action needed, not ours |
| Dead-letter queue non-empty | Inspect in the morning |
| Detection acceptance rate down more than 10 points week on week for a workspace | Quality regression, needs analysis and not adrenaline |
| Nightly live contract test failed | A provider changed something; fix during the day |
| Backup restore test overdue | Monthly obligation |
| Certificate expiring within 14 days | Should be automatic; alert on the failure of automation |

**What must not page:** a single failed job, one customer's expired token, a slow request, a
one-off provider timeout. All of those are normal.

## 2. Model provider is down or degraded

**Symptoms:** elevated errors or latency from the provider abstraction; the detection queue
depth growing; drafts per hour falling toward zero.

**What is still working:** ingest, the confirm queue, tracker writes, the web app, billing.
Only new drafting stops. Say this precisely, because "our AI provider is degraded, task
drafting is queued, everything else works" is a much better sentence than "we are
experiencing issues".

**Procedure**

1. Confirm it is them, not us: check the provider status page and the error classes on the
   meter. Timeouts and 5xx are theirs; 400s and schema failures are ours.
2. Verify the circuit breaker opened. If detection workers are still hammering a dead
   provider, pause the detection queue manually.
3. Confirm nothing is being dropped. Messages must be held, not discarded. Queue depth
   should be rising; if it is flat while ingest continues, work is being lost, and that is a
   bigger incident than the outage.
4. If the outage looks longer than about 30 minutes, post to the status page with a
   next-update time, and keep it.
5. If a second provider is configured, flip the tier mapping to it for the `cheap` tier
   first, in a canary workspace, then broadly. This is exactly the drill in
   [ADR 0004](adr/0004-model-provider-strategy.md); if it has never been rehearsed, an
   outage is a bad time to find out.
6. On recovery, let the backlog drain at normal concurrency. Do not raise concurrency to
   catch up: the backlog is now a large, sudden bill, and the budget caps will start firing.
7. Watch the spend curve during the drain. A day's held messages processed in an hour looks
   exactly like a runaway loop.

**Do not:** disable confirmation to "let things through", lower the confidence threshold to
produce more drafts, or silently drop the backlog.

## 3. Tracker API is returning 429

**Symptoms:** confirmed items sitting in `queued`; 429 counters rising on one connection.

**Procedure**

1. Identify whether it is one workspace or all. One workspace is usually a replay or a bulk
   confirmation; all workspaces means a shared limit or a provider incident.
2. Confirm backoff is honouring `Retry-After`. If retries are tighter than instructed, that
   is our bug and it is making the situation worse.
3. Reduce the write queue concurrency for that connection. Confirmations are durable; the
   customer sees "creating…" rather than an error.
4. If items have been queued more than 30 minutes, tell the affected workspace before they
   ask. A confirmed task that has not appeared is the thing that erodes trust fastest.
5. After recovery, verify no duplicates were created: count tasks per confirmation id. It
   must be one. If it is not, jump to section 5.
6. Record the trigger. Repeated 429s from ordinary use mean the pacing defaults are wrong,
   which is a code change and not an incident.

## 4. Costs spike

**Symptoms:** meter alerts at 50%, 80%, or the hard stop; cost per action rising against
baseline.

**Procedure**

1. Look at the meter grouped by workspace, purpose and model. The shape of the spike names
   the cause almost immediately.

| Shape | Likely cause | Action |
|---|---|---|
| One workspace, `replay` purpose | A large historical replay, working as designed | Confirm it is bounded, let it finish, check the tier is correct |
| One workspace, `detect` purpose, sustained | A very busy workspace, or too many channels selected | Talk to the customer about channel selection; check tier pricing covers it |
| All workspaces, sudden step change | A model or tier mapping changed, or a prompt got much longer | Compare to the last deploy and the last prompt version change; revert |
| Same content processed repeatedly | Caching or idempotency broken | This is a bug, not a usage pattern. Pause detection and fix |
| `draft` purpose far exceeding candidate count | The cascade is escalating too often, or retries are looping | Check retry budgets and confidence thresholds |

2. If the cause is not obvious within 15 minutes, use the global spend cap. Stopping
   drafting is recoverable; an unpayable invoice is not.
3. Notify affected workspaces if the cap stopped their drafting. Say what stopped, what
   still works, and when it resumes.
4. Afterwards, write down what the meter should have shown that would have caught this
   sooner, and add that alert.

## 5. A customer reports a wrong assignment or a wrong task

This is the reputational failure mode, so the response is disproportionate on purpose.

**Procedure**

1. **Apologise and fix their reality first.** Their tracker, their client. Offer to remove
   or reassign the task; do not do it silently on their behalf without asking, because Seros
   does not edit what it did not create.
2. **Reconstruct exactly what happened** from ids, not memory: the draft, the confirmation
   (who, when, which surface, edited or not), the prompt version, the model, and the roster
   entry used for the suggestion. Every one of those is on a row by design.
3. **Establish which of three things it was**, because the fixes are completely different:

| Kind | Evidence | Fix |
|---|---|---|
| Model error | A human confirmed a bad suggestion | A quality problem. Add the thread to the golden set as a labelled negative. Say plainly that a person confirmed it, without blaming them |
| Product error | The suggestion was reasonable but the UI made the wrong choice easy — a bad default, an unclear owner field, a bulk confirm | The most common real cause and the most fixable. Change the interface |
| System error | A write with no confirmation, or a write to the wrong workspace or project | Stop. This is an incident, not a bug. Freeze writes, check for other occurrences, follow the incident process, and tell the customer what happened without waiting to be asked |

4. **Check the blast radius.** Same prompt version, same roster mapping, same channel
   mapping: how many other tasks share the cause? Answer before the customer asks.
5. **Record it.** A wrong-assignment log with cause categories, reviewed monthly, is how
   routing quality gets better. It is also the data that eventually justifies the v1 work.
6. **Never** respond by turning off a safety control or by promising a model improvement
   with a date. Promise a change to the product, which is under your control.

## 6. Safe rollback

Three kinds of rollback, in increasing cost.

### 6.1 Roll back a prompt

Cheapest and most common. Prompt version is a per-workspace flag
([TESTING-STRATEGY.md](TESTING-STRATEGY.md)), so:

1. Flip the affected workspaces back to the previous prompt version. No deploy.
2. Nothing already drafted changes. Existing drafts keep the version that made them, which
   is correct: they should be judged by what produced them.
3. Record the reason and the metric that triggered it. A rollback without a recorded metric
   becomes a rumour about a bad prompt.

### 6.2 Roll back code

1. Stop the workers first, then redeploy the previous build, then start the workers. Doing
   it in the other order runs the old workers against the new schema for a few seconds,
   which is where the corruption is.
2. Check for schema changes. If the deploy included a migration, the rollback is only safe
   if migrations were written to be backward compatible — expand, deploy, contract later,
   never a destructive change in the same release as the code that needs it. **If a
   migration is not reversible, do not roll back the database. Roll forward with a fix.**
3. Verify: health check, one end-to-end confirm into a sandbox, queue depths draining, error
   rate returning to baseline.
4. Reconcile side effects. A rollback does not undo writes into customer systems, and it
   must not attempt to. Any task created stays created.

### 6.3 Restore data

Last resort, and the one that must have been rehearsed.

1. Never restore over the primary. Restore to a scratch environment, verify, then move only
   what is needed.
2. Point-in-time recovery to just before the damage. Confirm the timestamp against the audit
   log rather than against memory.
3. Expect to lose whatever happened after that point, and know what it was before deciding.
4. Tell affected customers what was lost. Silence here is how a recoverable incident becomes
   a churn event.
5. Record the elapsed time. That number is the honest RTO, and it belongs in
   [SECURITY-CONTROLS.md](SECURITY-CONTROLS.md) rather than an optimistic guess.

## 7. Escalation and communication

| Situation | Action |
|---|---|
| Customer-visible degradation over 30 minutes | Status page entry with a next-update time, and honour the time |
| Any customer data exposed to the wrong party | Incident process. Preserve evidence, do not delete anything, notify within the window the DPA commits to |
| Unconfirmed write, any number | Freeze the write path for everyone. Investigate before resuming. This is worth downtime |
| A provider changed behaviour and broke an integration | Status page, name the component, refresh fixtures, ship a fix |
| Anything over 30 minutes of degradation | Public postmortem within 5 business days, plain language, no blame, what changed to prevent it |

## 8. Weekly and monthly operations

| Cadence | Task |
|---|---|
| Weekly | Review the metrics sheet; scan dead-letter queues; check cost per action against the baseline; review the wrong-assignment log |
| Weekly | Confirm the retention sweep ran every day and processed what it should have |
| Monthly | **Restore a backup to a scratch environment and record the date and elapsed time.** The most-skipped item on the list and the one that ends companies |
| Monthly | Review the on-call log: what paged, what should not have, what should have and did not |
| Quarterly | Access review; MFA inventory; dependency and secret scan review; subprocessor register review; rehearse the provider exit test |

## 9. Open questions

1. Which alerting tool, and is the page reliable enough to be trusted while asleep? An alert
   that does not wake anyone is worse than no alert, because it creates false confidence.
2. What is the honest published expectation for response time outside business hours? Write
   it before the first customer asks, not after the first incident.
3. Who is the second contact if the founder is unreachable for a week? This is a
   business-continuity question with a customer-facing answer, and it is currently blank.
4. What is the fastest safe way to freeze all writes across all workspaces? It should be one
   documented action, not an improvised deploy.
