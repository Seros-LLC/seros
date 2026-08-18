# 1. Record architecture decisions

## Status

Accepted. 2026-08-17.

## Context

This repository will hold a product built and operated by one person, with no code in it
yet. Every structural decision made in the next six months will be made once, quickly, and
under pressure, and will then be lived with for a long time. Two failure modes follow:

1. **Decisions become invisible.** A choice made on a Tuesday becomes "how it has always
   been" by Friday. Six months later nobody can say whether the constraint that forced it
   still exists, so it is never revisited, or it is revisited from scratch every time.
2. **Decisions get made by accident.** Writing the first file in a language chooses the
   language. Calling one provider's API directly chooses a provider. The most expensive
   commitments are the ones nobody noticed making.

The second failure mode is why this repository starts with documentation and no code. The
language, runtime and model provider are open questions
([ADR 0003](0003-language-and-runtime.md), [ADR 0004](0004-model-provider-strategy.md)),
and the way to keep them open is to write down that they are open.

There is no team to communicate decisions to yet. There will be. There is also a future
version of the founder who will not remember the reasoning, and a future security reviewer
or acquirer who will ask why the system is shaped this way. All three are served by the
same artefact.

## Decision

Architecture decisions are recorded as short Markdown files in `docs/adr/`, numbered
sequentially, in the format described by Michael Nygard's original ADR pattern:
**Context, Decision, Status, Consequences.**

Rules:

- **One decision per file.** Filename is `NNNN-short-slug.md`, numbers never reused.
- **Every ADR carries a `## Status` section** whose first meaningful line is one of
  `Proposed`, `Accepted`, `Rejected`, `Deprecated`, or `Superseded by ADR-NNNN`. CI checks
  that the section exists ([.github/workflows/docs-checks.yml](../../.github/workflows/docs-checks.yml)).
- **ADRs are immutable once accepted.** A decision that changes is not edited; a new ADR
  supersedes it, and the old one gets a status line pointing forward. The record of having
  been wrong is the useful part.
- **Proposed ADRs are allowed to sit unaccepted.** An open decision recorded honestly is
  better than a decision made by default. A proposed ADR must state **what evidence would
  decide it**, so that it is a question with an answer rather than an argument.
- **Write the ADR when the decision is being made**, not after implementation. If code
  already exists, the ADR is archaeology.
- **Threshold:** anything expensive to reverse. Language, runtime, database, hosting, model
  provider strategy, tenancy model, authentication approach, product principles with
  contractual force, data retention design, public API shape. Not: library choices,
  formatting, file layout.

## Consequences

**Good**

- Open decisions stay visibly open instead of being settled by the first commit.
- A future hire, contractor or reviewer can read the history of the system in the order it
  was decided.
- Security and procurement reviews ask "why is it built this way" and there is an answer
  that is not a reconstruction.
- Writing the consequences section forces the cost of a decision to be named at the time,
  when it is still cheap to reject.

**Costs**

- Overhead on every significant decision. At one person, the temptation to skip is real;
  the mitigation is that ADRs are short, and a bad short ADR beats no ADR.
- Immutability means the directory accumulates superseded files. That is the point, but it
  makes the directory a poor index. The README's documentation table is the index.
- A proposed ADR that never gets decided becomes a decision by inertia. Each one must name
  its deciding evidence, and the roadmap review should sweep proposed ADRs.

**Neutral**

- The ADR log is internal. Nothing in it is a public commitment except where a decision is
  also published (see [ADR 0002](0002-human-confirmation-is-mandatory.md), which is in the
  terms and on the website).
