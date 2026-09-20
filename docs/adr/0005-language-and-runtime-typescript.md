# 5. Language and runtime: TypeScript on Node

## Status

**Accepted. 2026-08-18.** Supersedes [ADR 0003](0003-language-and-runtime.md), which remains
readable as the statement of the question and the method.

## Context

ADR 0003 refused to choose, listed three families, and named the evidence that would decide
it: a timeboxed spike of the same vertical slice in at most two candidates, an evaluation
harness written in each, a deliberate 2am breakage test, an honest familiarity score, and a
contractor price check. It set a deadline — *decide before the first line of application
code* — and warned that the alternative was deciding by accident.

Two spikes were built, and are committed alongside this ADR at
[`spikes/python`](../../spikes/python) and [`spikes/typescript`](../../spikes/typescript).
Both implement the same slice: a signature-verified webhook, persistence, a real queue, one
model call behind an abstraction with a schema-validated response, a server-rendered confirm
queue, and an idempotent write to a fake tracker.

## Decision

**TypeScript on Node**, with Drizzle over SQLite in development and a Postgres-shaped schema,
server-rendered pages, and no client framework.

## Evidence, including the parts that do not flatter the decision

**What the spikes showed.** The TypeScript spike expressed the two constraints ADR 0003 said
were disqualifying if unmet, and expressed them *structurally* rather than by convention: a
`WorkspaceScope` that cannot be constructed without a workspace, injects `workspace_id` into
every query itself and exposes no raw handle; and a branded `ConfirmationProof` type that the
tracker writer demands, so "no write without a human confirmation" is checked by the compiler
rather than by a reviewer's attention. The Python spike enforced the same rules with managers
and foreign keys — correct, and checked at runtime rather than before it runs.

**Honest note on how the comparison was conducted.** The Python spike's own `MEASUREMENTS.md`
was never written, so the line-count and time comparison ADR 0003 asked for does not exist.
The two spikes were compared by reading their source. That is weaker evidence than the ADR
demanded, and it is recorded here rather than dressed up.

**The evaluation-harness test — the one ADR 0003 called decisive.** It was answered after the
decision rather than before, by building the harness for real: `evals/detection.ts` in the
application repository scores a 217-example golden set and prints a precision/recall sweep
across ten thresholds. It found a genuine defect and changed a prompt on the strength of it —
detection precision moved from 81.0% to 100.0% at 95.8% recall, because the sweep proved no
threshold could rescue a confidently wrong answer. Writing that harness in TypeScript was
unremarkable, which is the only claim being made for it.

**The 2am test.** Answered in production shape rather than in the spike: a deliberate provider
outage, a timeout, and a schema-violating response are each metered as themselves, logged as
an error class with no body, and answered by queueing rather than by inventing a draft. There
are tests for all three.

**Items 4 and 5 were not done.** No familiarity score was recorded before the spikes, and no
contractor was asked to price a second tracker integration. Both were skipped, and neither is
retrospectively invented here. If the hiring-pool question ever becomes real, item 5 is still
worth doing.

## Consequences

- The three advance consequences ADR 0003 attached to any choice are met: the provider
  abstraction exists from the first model call (`src/provider/`), tenant scoping is a
  structural constraint rather than a convention (and a build-failing check now enforces that
  no module reaches around it), and this ADR supersedes 0003 with its evidence attached.
- The application lives in [`Seros-LLC/app`](https://github.com/Seros-LLC/app),
  private, and not yet in this repository. Merging it here is a separate decision, because it
  changes what this repository is: today it is the specification, and the specification has
  been usefully independent of the thing it specifies.
- **The reversal cost is unchanged and low.** ADR 0003's own observation holds: the durable
  assets are the prompts, the golden set, the routing data and the integration knowledge, and
  all four are portable. The golden set is JSON, and the prompts are one small versioned file.
- ADR 0004 remains **proposed**. No vendor model is chosen. The application runs a local
  Qwen 7b through the abstraction, with an ordered transport chain so that when a hosted model
  is chosen it goes in front and the local one becomes the fallback behind it.

## What would make this wrong

If the evaluation and prompt-iteration work turns out to want a notebook and a scientific
stack — the argument ADR 0003 made for Option A, and the strongest argument against this
decision — the harness is small, offline, and reads a JSON corpus. Rewriting it in Python
while leaving the application alone is a day's work and would not be an admission of anything.
