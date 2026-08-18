# Integrations — scopes, limits, tokens and failure behaviour

Working draft. Nothing is built. This document states exactly what Seros would ask a
customer for, why each request is necessary, what it reads, what it writes, and what stops
working if a scope is refused.

The governing principle is that the scope list is a sales document. It is read by the
person who has to approve the install, and every scope that cannot be justified in one
sentence is a reason for them to say no. So: **ask for the least that makes the v0 loop
work, and be able to explain every line.**

## 1. Slack

The Slack app is installed by a workspace admin, is granted access to an explicit list of
channels, and posts nothing publicly by default.

### 1.1 Bot token scopes requested

| Scope | Why it is needed | Read or write | If refused |
|---|---|---|---|
| `channels:history` | Read messages in the public channels the admin selected. This is the raw material for detection; without it there is no product | Read | Nothing works for public channels |
| `channels:read` | List public channels so the admin can pick which ones to include, and resolve channel names in the UI | Read | The channel picker cannot be populated; the admin would have to type ids |
| `groups:history` | Read messages in private channels the app has been explicitly invited to. Much agency and MSP client work happens in private channels | Read | Private channels cannot be used; public-only deployment still functions |
| `groups:read` | List the private channels the app is in, for the picker | Read | Private channels cannot be selected by name |
| `users:read` | Resolve user ids to display names for the roster, owner suggestions and mention handling | Read | Owner suggestion degrades to raw user ids, which is unusable for a confirmer |
| `users:read.email` | Match Slack users to Seros members and to tracker users by email. This is the only reliable automatic mapping between three systems | Read | Roster mapping falls back to manual mapping in the admin UI; assignment quality drops materially |
| `chat:write` | Post the confirmation prompt and the created-task permalink back into the source thread, and send the confirm queue notice | Write | No thread reply, no Slack-side confirm surface; the web queue still works |
| `commands` | A slash command to open the confirm queue and to check status without leaving Slack | Read (invocation) | Minor: the app is reachable only from the web app and from message actions |
| `reactions:write` | Mark a message as captured with a reaction, so the team can see at a glance what became a task | Write | Cosmetic loss; capture state is visible only in the app |
| `team:read` | Read the workspace name and id for display and for tenant binding | Read | Display degrades; tenant binding uses the id alone |

**Deliberately not requested**

| Scope | Why not |
|---|---|
| `files:read` | v0 never reads file contents. Not asking for it is a stronger privacy statement than asking and not using it |
| `im:history`, `mpim:history` | Direct messages are not read. This is the single most reassuring line in the whole scope list and it should stay true |
| `channels:join` | The app is invited, it does not add itself. Self-joining channels is exactly the behaviour that gets an app uninstalled |
| `chat:write.public` | Posting into channels the app was not invited to is the blast radius named in the roadmap's "not doing" list |
| `admin.*` | Workspace administration is never needed. Any admin scope turns a routine install into a security review |
| `users:read` on a user token | The app acts as an app, not as a person. A user token that can read as the installer is a liability |

### 1.2 What is read and what is written

**Read:** messages, thread structure, timestamps, author ids and mentions, in the selected
channels only. Channel selection is an allowlist stored on the `Connection` record; an empty
list means nothing is read, and that is the default at install.

**Written:** a reply in the source thread containing the created task link, an optional
reaction on the source message, and confirm-queue messages sent to the confirmer. Nothing
is posted to a channel that was not the source of the item, and nothing is posted at all
before a human confirmation ([ADR 0002](adr/0002-human-confirmation-is-mandatory.md)).

### 1.3 Rate limits and event handling

**ASSUMPTION:** the figures below describe the general shape of Slack's published limits and
must be verified against current documentation during the first spike, because they change.

| Concern | Design response |
|---|---|
| Per-method rate tiers | A per-connection token-bucket limiter in front of every Slack call, tuned to the slowest tier used, with the limiter shared across workers so concurrency cannot bypass it |
| `Retry-After` on 429 | Always honoured. Never retried faster than instructed. Backoff with jitter |
| Event delivery retries | Slack retries deliveries that are not acknowledged quickly, so the webhook receiver acknowledges immediately and enqueues; all downstream work is idempotent on `(channel_id, ts)` |
| Bulk history pull for replay | Runs on the maintenance queue with a conservative pace and a progress record, so a 30-day replay cannot exhaust the workspace's rate budget and stall live ingest |
| Event volume spikes | Ingest writes and enqueues only; detection is batched behind it, so a busy day becomes a longer queue rather than a cost spike or a dropped event |

### 1.4 Tokens, storage and rotation

- Bot tokens and any refresh tokens are stored encrypted with a per-workspace key
  ([DATA-MODEL.md](DATA-MODEL.md), `Connection.access_token`). They are never logged, never
  rendered to a browser, never included in an export, and never sent to a model provider.
- Where token rotation is available it is enabled, and refresh runs proactively before
  expiry rather than reactively on a 401.
- The signing secret is used to verify every inbound request, with a timestamp window to
  reject replays. An unverified request is dropped without processing.
- Rotation procedure: rotate on any suspicion, on any personnel change, and on a schedule.
  A rotation must not require a customer to reinstall the app.

### 1.5 Disconnect behaviour

1. The admin clicks disconnect in Seros, or uninstalls the app from Slack.
2. Ingest stops immediately; queued detection work for that connection is cancelled.
3. Tokens are destroyed. The `Connection` row is kept with `status = disconnected` for the
   audit trail.
4. Stored message content for that source is deleted within 24 hours.
5. Pending drafts are cancelled, not silently confirmed. Confirmed tasks already created in
   the tracker stay there, because they are the customer's data in the customer's system,
   and the disconnect screen says so explicitly.
6. An audit event and a confirmation email to the admin record what was deleted.

## 2. The tracker

**The tracker is not chosen.** The roadmap makes that choice a design-partner question, and
it is close to irreversible for six months. This section therefore specifies the integration
by capability. Each capability names the shape of the permission a tracker is expected to
expose; the exact scope strings are filled in when the tracker is chosen, and this document
is updated in the same pull request as the integration.

### 2.1 Capabilities requested

| Capability | Why it is needed | Read or write | Typical scope shape | If refused |
|---|---|---|---|---|
| Read projects and boards | The admin maps a Slack channel to a project. Without it there is nowhere to put a task | Read | `read:project` | Setup is impossible |
| Read users and their identifiers | Build the roster mapping so an owner suggestion can become a real assignee | Read | `read:user` | Tasks can be created but not assigned; the product loses most of its value |
| Read open issues, titles and status | Deduplicate against work already tracked. This is the difference between a helpful queue and a noisy one | Read | `read:issue` | Dedupe is disabled; duplicate suggestions appear and acceptance rate falls |
| Create an issue | The whole point | Write | `write:issue` | The product cannot complete its loop |
| Set assignee and due date on the issue being created | An unassigned, undated task is a note, not a delegation | Write | `write:issue` | Tasks are created unowned; the customer does the routing by hand |
| Attach a source link or reference | Traceability from a task back to the conversation that caused it | Write | `write:issue` or a comment scope | The audit trail from task to source is broken for the customer |
| Receive completion signal | Capture rate and the v1 close-the-loop reply need to know when a task is done | Read, webhook or poll | `read:issue` plus webhook registration | Completion is unknown; the capture-rate metric degrades to created-not-completed |

**Deliberately not requested**

| Capability | Why not |
|---|---|
| Delete issues | Seros never deletes a customer's work. There is no product reason and enormous downside |
| Edit existing issues not created by Seros | v0 creates; it does not modify what the team already owns. This keeps the blast radius to rows Seros itself made |
| Administer the tracker workspace, billing or membership | Not needed, and it turns an install into a procurement conversation |
| Read all projects when only one is mapped | Where the tracker supports project-scoped grants, request only the mapped projects |

### 2.2 Rate limits

**ASSUMPTION:** every candidate tracker enforces per-token or per-organisation limits with a
`Retry-After` or a cost-based budget header. The design assumes limits exist and does not
depend on their exact values.

| Concern | Design response |
|---|---|
| Write bursts | Writes are serialised per connection through the `write` queue with a modest concurrency ceiling. A confirmed item is durable, so a slow write is a delay and never a loss |
| Dedupe reads | Cached with a short time-to-live and scoped to the mapped project, so a busy detection run does not generate a read per candidate |
| Roster sync | Scheduled, incremental, and paced. Full sync only on connect or on explicit request |
| 429 | Honour `Retry-After`, exponential backoff with jitter, cap total attempts, then move the item to `needs_review` rather than retrying forever. See [RUNBOOK.md](RUNBOOK.md) |
| Bulk operations | None in v0. There is no batch import path and no bulk task creation |

### 2.3 Tokens, storage and rotation

Identical handling to Slack: encrypted at rest with a per-workspace key, never logged, never
exported, proactive refresh before expiry, rotation on suspicion or personnel change. Two
additions:

- **Read and write use separate code paths.** Dedupe reads through a read-only client
  surface, so a bug in dedupe cannot create or modify a task.
- **The connection records which projects were mapped.** A write to an unmapped project is
  refused by Seros before the API is called, so a routing bug cannot leak a task into an
  unrelated project.

### 2.4 Disconnect behaviour

1. Writes stop immediately; confirmed-but-unwritten items are cancelled with a visible
   status, not silently retried later.
2. Tokens are destroyed; the connection row survives as a tombstone.
3. Cached issue titles used for dedupe are deleted.
4. Tasks already created remain in the tracker. Seros does not delete or alter the
   customer's work, and the disconnect screen states this in one sentence.
5. Audit event, plus an email confirming what was deleted on our side.

## 3. Cross-cutting integration rules

| Rule | Reason |
|---|---|
| Every scope requested is displayed to the admin in plain English at connect time, alongside what it is used for | The roadmap requires clearly listed scopes; a customer who understands the ask says yes more often |
| Scopes are re-displayed on the connection settings page, showing what was actually granted | Granted and requested can differ, and the difference explains degraded behaviour |
| Missing-scope errors degrade a feature and name it | "Owner suggestion is off because the app cannot read users" is a support ticket avoided |
| No integration ever fetches file contents in v0 | Files are a different sensitivity class and a different set of promises |
| No integration call is made inside a web request | Third-party latency must never be user-visible latency |
| Every write carries an idempotency key derived from the confirmation id | Duplicate tasks are a trust incident |
| Every integration error is recorded as a class, never as a raw body | Provider error bodies can contain customer content |
| Integration error rate is a tracked metric with a target under one percent | It is a v1 exit criterion, so it must be measured from v0 |

## 4. Open questions

1. **Which tracker is v0?** Everything in section 2 becomes concrete the day this is
   answered. Ask the first five design partners.
2. Does the chosen tracker support project-scoped grants, or is access all-or-nothing at the
   organisation level? This changes what can honestly be said on the trust page.
3. Completion signal: webhook or polling? Webhooks are cheaper and faster but add an inbound
   endpoint to secure and a delivery-reliability problem.
4. Should the Slack confirm action be a message action, a modal, or both? The modal supports
   editing before confirming, which is where most of the value of the Slack surface is.
5. Where a tracker offers a marketplace listing, does listing require a security review that
   the company cannot pass yet? That is a go-to-market dependency hiding inside a technical
   decision.
