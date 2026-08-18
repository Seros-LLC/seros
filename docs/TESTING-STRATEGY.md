# Testing strategy

Working draft. Nothing is built. This document describes how to test a system whose core
component is a language model that will not give the same answer twice, in a repository
that has not chosen a language or a test framework.

The split that makes this tractable:

| Layer | Nature | How it is tested |
|---|---|---|
| The plumbing: ingest, queues, idempotency, tenancy, confirmation, tracker writes, metering, retention | Deterministic | Ordinary automated tests. This layer must be boringly correct, and no model is involved |
| The judgement: detection, drafting, routing | Non-deterministic | Measured on a fixed evaluation set against thresholds, not asserted |

Confusing the two is the standard mistake. Asserting an exact model output makes a test that
fails on a whitespace change; asserting nothing makes a system whose quality nobody can see.
Deterministic code gets assertions. Model behaviour gets measurements and thresholds.

## 1. The deterministic layer

These must have real automated coverage before the first customer, because every one of
them is a promise made somewhere else in the pack.

| Area | What must be proven |
|---|---|
| Webhook verification | An unsigned, wrongly signed or replayed request is rejected without processing |
| Idempotency | Every table in [ARCHITECTURE.md](ARCHITECTURE.md) section 6 survives duplicate delivery: no duplicate `SourceMessage`, no duplicate `Draft`, and above all **no duplicate task in the tracker** |
| Confirmation gate | There is no code path that creates a task without a `Confirmation` row referencing a real member. This is tested by construction, and additionally by a test that attempts it and expects failure |
| Tenancy | With two workspaces populated, every read path returns only the requesting workspace's rows. Plus a static check that fails the build on a tenant-owned query with no workspace predicate |
| Authorisation | Each role can do exactly what its row in the permission matrix says, and nothing else. Viewer cannot confirm |
| Logging hygiene | A test that runs a content-classed value through the log formatter and fails if it appears in the output. Rule 2 of the README, enforced mechanically |
| Metering | Every simulated provider call produces exactly one meter row, including failures, timeouts and budget blocks |
| Budget caps | At the cap, the provider abstraction refuses before the network call, writes a `budget_blocked` row, and leaves confirmation and writes working |
| Retention | The sweeper nulls content at the workspace's configured age, writes an audit event, and leaves metadata intact |
| Deletion | Workspace deletion removes every content and identity field, retains content-free audit and billing rows, and completes within the promised window |
| Integration failures | 429, 5xx, timeout, revoked token and missing scope each produce the behaviour in [INTEGRATIONS.md](INTEGRATIONS.md), against a recorded fake, never against a live third party |

**No test may require a live model provider or a live third-party API.** The test suite runs
offline, in CI, on an aeroplane. Third-party behaviour is exercised through recorded
interactions with the contract test described in section 6.

## 2. The golden set

The golden set is the single most valuable engineering artefact this product will own
besides the code, and it should be started before the code exists.

**What it is:** a fixed corpus of chat threads with human labels saying which messages
contain a commitment, request or decision, who the owner should be, and what the task should
say.

**Composition targets** (**ASSUMPTION**, revise once real data exists):

| Slice | Share | Why |
|---|---|---|
| Clear commitments ("I'll have the deck to you by Thursday") | 25% | The base case. If these fail, nothing else matters |
| Requests to a named person | 15% | Second most common real pattern |
| Decisions with an implied action | 10% | The subtle, valuable case |
| Hard negatives: hypotheticals, jokes, past tense, quoting someone else, "we should probably…" | **30%** | The largest slice on purpose. Precision is the product constraint, and hard negatives are the only way to measure it |
| Ambiguous cases where two humans disagree | 10% | Records the ceiling. A model cannot beat human agreement, and pretending otherwise produces chasing |
| Threads that are noise end to end: standups, banter, bot output, link dumps | 10% | Proves the pre-filters work and measures the cost of empty channels |

**Size:** start at 200 labelled messages across at least 20 threads; grow to 1,000. Below
about 200 the confidence interval on a percentage is wider than any improvement being
measured, and acting on it is superstition.

**Labelling rules:**
- Two labellers on the first 100 items, disagreements recorded rather than resolved away.
  Inter-labeller agreement is the realistic ceiling for the model.
- A written label guide. "Is this a commitment?" is not self-evident, and an unwritten
  definition drifts within a week.
- Labels are versioned with the set. Re-labelling creates a new version; results are never
  compared across versions.

**Provenance and consent:** the corpus contains no customer content that was not
explicitly consented to for this purpose, in writing, by a design partner. Everything else
is either synthetic or drawn from the founder's own conversations. Every entry records its
provenance and its consent basis, and anything without one is not eligible for the set.

## 3. Anonymisation of real threads

Real threads are far more valuable than synthetic ones, because real teams write badly and
synthetic examples are too clean. They are also the most sensitive asset in the company.

Rules, all of which are non-negotiable:

1. Written consent from the design partner first, naming the purpose (evaluating and
   improving detection) and stating that the content will not be used to train any model.
2. Anonymisation is a pipeline, not a person doing find-and-replace: consistent pseudonyms
   per person within a thread, company and client names replaced with stable placeholders,
   URLs and file names replaced, numbers that could identify a deal or an amount replaced,
   dates shifted by a constant offset per thread so relative timing survives.
3. A human reads every anonymised thread before it enters the corpus. Automated redaction
   misses the sentence that names a client in passing, and that sentence is the one that
   causes the incident.
4. The corpus lives in a private repository with restricted access, separate from the
   product repository, and never in a public one.
5. A partner can withdraw. Withdrawal removes their threads from the corpus and from every
   published evaluation baseline, which means baselines are re-run rather than adjusted.
6. **Fixtures used in the ordinary test suite are synthetic**, always. The consented corpus
   is for evaluation only. Nobody should be able to leak a customer thread by opening a test
   file.

## 4. Metrics and thresholds

For detection, precision and recall are computed against the golden set at the message
level, and a per-thread capture measure is reported alongside because a thread with three
commitments and one detection is a different failure from three false positives.

| Metric | Definition | v0 gate | Why |
|---|---|---|---|
| Detection precision | Of messages flagged as candidates, the share correctly flagged | Must not regress against the established baseline | The roadmap chooses precision over recall explicitly: a noisy queue costs the account, a miss costs nothing today |
| Detection recall | Of true commitments, the share flagged | Reported, deliberately not optimised in v0 | A recall gain bought with a precision loss is a regression |
| Owner suggestion accuracy | Of drafts with a suggested owner, the share whose owner a human accepted unchanged | Reported per workspace | The v1 differentiator; instrument it from v0 or the compounding never starts |
| Abstention rate | Share of drafts with no suggested owner | Reported | An honest abstention is better than a wrong assignment. A falling abstention rate with flat accuracy is a warning |
| Cost per thousand messages | Provider spend on the evaluation run | Reported on every run | Quality changes that triple cost are not improvements |

**Acceptance thresholds are inherited from the roadmap's exit criteria, not invented here.**
The roadmap's v0 exits are: signup to first confirmed task under 30 minutes unattended,
suggestion acceptance above 60% across at least three non-founder workspaces, at least one
real invoice paid, and measured cost per action known rather than assumed.

That maps to testing as follows:

| Roadmap criterion | The testable form |
|---|---|
| Acceptance above 60% in production | Offline precision on the golden set is the leading indicator. Ship no prompt change whose offline precision is below the current production baseline |
| Signup to first confirmed task under 30 minutes | A scripted end-to-end run against sandboxes, timed, executed before every release. If it exceeds 30 minutes, the release is blocked |
| Cost per action measured | The evaluation run reports cost per thousand messages, and the meter reports the production figure. If the two disagree by more than a factor of two, something in production is not what was evaluated |
| Integration error rate under one percent (v1 criterion, measured from v0) | Error-class counters per connection, alerting per [RUNBOOK.md](RUNBOOK.md) |

**ASSUMPTION:** no absolute precision or recall number is set here, because setting one
before the first evaluation run would be inventing a benchmark. The first run establishes
the baseline; from then on the rule is that the baseline may not fall.

## 5. Prompt versioning and offline evaluation

**Prompts are versioned artefacts.** Each has an id and a semantic version, lives in a file
under version control, and is loaded rather than concatenated inline. The version is written
onto every `Candidate`, `Draft` and `ActionMeter` row it produced, so any suggestion a
customer complains about can be traced to the exact text that produced it.

**A prompt change is a code change.** It goes through a pull request. The pull request must
contain the evaluation result:

| Field | Example shape |
|---|---|
| Golden set version | The exact corpus version scored |
| Model and tier | Which tier and which model id |
| Precision, recall, abstention | Before and after, with the deltas |
| Cost per thousand messages | Before and after |
| Sample of changed decisions | The items that flipped, both directions. This is where the real review happens |

**Rules:**
- No prompt reaches production without an offline evaluation run attached.
- A change that raises recall and lowers precision is rejected by default in v0. Overriding
  that requires a written reason in the pull request.
- Evaluation runs are recorded in an append-only log with date, corpus version, prompt
  version, model, results and cost, so quality over time is a real series and not a memory.
- Fix the sampling temperature and every other decoding parameter for evaluation, and record
  them. Comparing runs with different parameters measures nothing.
- Score the same run twice on a subset to record the model's own variance. A change smaller
  than that variance is not a change.

## 6. Contract tests for third parties

Slack and the tracker change under the product without asking. Two layers:

1. **Recorded interaction tests.** Real responses captured once, scrubbed of content and
   tokens, replayed in CI. Fast, offline, deterministic. These are what the test suite runs.
2. **A scheduled live contract test.** A nightly job against sandbox accounts that performs
   the real loop: read history, create a task, set an assignee, post a reply, delete the
   test task. It asserts shapes and status codes, not content. When a provider changes an
   API, this fails at 3am on a schedule rather than in front of a customer, and the recorded
   fixtures get refreshed.

The live test never touches a customer workspace and never runs in the customer's tenancy.

## 7. Canary workspaces and release process

| Stage | What runs there | Gate to the next stage |
|---|---|---|
| Local | Full offline suite plus the evaluation run on the golden set | Suite green, no precision regression |
| CI | Same, plus documentation checks, secret scanning and dependency alerts | All green; a red build never merges |
| Founder workspace | The founder's own Slack and tracker, always on the newest build | 24 hours with no unexplained rejection spike |
| Canary workspaces | Two or three consenting design partners, flagged, updated first | 48 hours with acceptance rate within normal variance and no integration error spike |
| General | Everyone else | Monitored per the runbook |

**Every model-affecting change is flagged per workspace**, so a prompt version is a property
of a workspace, not of a deploy. This is what makes canarying a prompt possible at all, and
it is also what makes rollback a flag flip instead of a redeploy.

**Watch after any model-affecting change**, per canary workspace: acceptance rate, rejection
rate, edit rate, drafts per thousand messages, abstention rate, cost per action. A rejection
spike in a canary is a rollback, not a discussion.

## 8. What is deliberately not tested

| Not tested | Why |
|---|---|
| Exact model output strings | They will change with every provider update, and asserting them creates tests that fail for no reason and are then disabled |
| Load and performance beyond a smoke check | v0 volume is trivial and the bottleneck is a remote provider. Performance testing now would optimise the wrong thing |
| Browser matrix coverage | Server-rendered pages in modern browsers. A support ticket is cheaper than the suite |
| Third-party APIs themselves | Their correctness is not our test's business; our handling of their failures is |
| Anything requiring production data in a test environment | Explicitly forbidden by the environment separation control in [SECURITY-CONTROLS.md](SECURITY-CONTROLS.md) |

## 9. Open questions

1. Who is the second labeller for the first hundred golden-set items? Inter-labeller
   agreement needs two people, and there is currently one.
2. Do design partners consent to a corpus at all? If none do, the corpus is synthetic plus
   the founder's own data, and the evaluation ceiling is lower. Ask early; this gates the
   whole strategy.
3. Is per-workspace prompt versioning worth building in v0? It is what makes canarying real,
   and it is much harder to retrofit than to include.
4. What is the release cadence? Continuous deployment with canary flags, or a weekly train?
   The runbook's rollback procedure depends on the answer.
