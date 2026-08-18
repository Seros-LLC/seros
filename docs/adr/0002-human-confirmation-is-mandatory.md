# 2. Human confirmation is mandatory before any write

## Status

**Accepted.** 2026-08-17. This is a product principle, not an implementation preference. It
is already published on the website and stated in the terms, so changing it is a customer
communication and a contractual matter before it is an engineering one.

## Context

Seros reads a team's conversations, decides that something was committed to, drafts a task
with an owner and a date, and puts it in the tracker the team already uses. Every step
before the last one is a suggestion. The last one is an action inside a system other people
depend on, often visible to a customer's own clients.

The failure is asymmetric, and the asymmetry is the whole argument.

| Error | Cost |
|---|---|
| We miss a commitment | The team is where it was before Seros existed. The cost is the value not delivered |
| We create a wrong task, assigned to the wrong person, with a wrong date, in a shared tracker | Someone else's process is now polluted. They must find it, undo it, explain it, and decide whether to trust the tool. In a client-facing project, they may have to explain it to their client |

The roadmap makes this explicit: precision over recall, deliberately. The business plan
identifies the trust of the buyer as the scarce asset. The "not doing" list names
auto-assignment without confirmation as excluded from v0 and v1.

There is also a legal dimension. Seros is a processor acting on the customer's instruction.
A confirmation record is the evidence that a specific human authorised a specific write.
Without it, the company is asserting that an inference from a model constituted an
instruction, which is a much worse position in any dispute about a task that caused harm.

And there is a product dimension that is easy to miss: the confirmation is not friction to
be optimised away. It is the moment the customer sees the value, corrects the system, and
generates the rejection and edit data that makes routing better. The confirm loop is the
product's only compounding data asset. Removing it would remove the moat along with the
safety.

## Decision

**No write to any customer system happens without a recorded human confirmation.**

Concretely:

1. The tracker writer accepts a **confirmation id**, never a draft id. There is no function
   signature in the system that lets a caller create a task from a draft directly.
2. `Task.confirmation_id` is required and unique. A task row without one is a schema
   violation, not a logic bug.
3. A confirmation must reference a `Member` — a real, authenticated person in the
   workspace. Service accounts and system actors cannot confirm.
4. There is **no configuration flag, environment variable, feature toggle or admin override
   that disables confirmation** in v0. A flag that can be turned on will be turned on for a
   demo and then left on.
5. This includes the reply posted back into the source thread, which is also a write into a
   customer's system and is also gated by the confirmation.
6. Rejections and edits are recorded with the same weight as confirmations. They are data,
   not discards.
7. Any future narrowing of this rule (the v2 "trusted auto-confirm" idea) requires a new
   ADR superseding this one, and it inherits every constraint stated there: opt-in,
   rule-scoped, low-risk cases only, after a workspace has confirmed several hundred
   suggestions at a high acceptance rate, and never for anything posted outside the
   customer's own company.

## Consequences

**Good**

- The blast radius of a detection error is a bad row in a queue nobody accepted. That is a
  quality problem, not an incident.
- The architecture gets a single choke point that is easy to review and easy to test: one
  path to a customer's systems, one required foreign key.
- Every write is attributable to a person, with a timestamp and a surface. This answers the
  security-review question, the "who did this" support question and the audit export
  requirement in one structure.
- Edits and rejections accumulate as labelled training and evaluation data, per workspace.

**Costs**

- The product cannot claim full automation, and some prospects want exactly that. The
  answer is that the confirmation is thirty seconds and the alternative is auditing
  someone else's mistakes.
- Value is capped by confirmer attention. If the queue is noisy the customer stops
  confirming, so precision is not optional — it is the gating constraint on the whole
  product. This is why the acceptance-rate metric is a health metric, not a vanity one.
- Time-to-confirm becomes a metric that can kill an account (the roadmap's "the confirm
  queue became another inbox" risk). It must be watched.
- Bulk confirmation UI becomes necessary earlier than expected, and bulk confirm has to
  stay a real decision rather than a "select all" that quietly becomes automation.

**Neutral**

- The confirm surface has to exist in two places (web app and Slack action), because a
  confirmer who has to change context will not confirm. That is two implementations of the
  same authorisation check, which is a testing obligation.
