# Archived application product brief

This is the essential product brief preserved from the retired application repository. It is
historical evidence for the paused product, not current consulting positioning and not a claim
that the product is deployed or available.

## Platform

Web application.

## Intended users

Delivery leads, product leads, operations leaders, and technical agencies whose commitments
were made in Slack but needed to be tracked in a task system. The intended job was to close the
handoff from a specific conversation to an owned task without losing source context.

## Product purpose

Seros turned commitments from explicitly selected Slack channels into proposed tracker issues.
A human reviewer edited, confirmed, or rejected every proposal before Seros wrote anything to
the tracker.

## Positioning at the time

A permissioned, human-confirmed commitment-to-task workflow. It did not autonomously create
tracker work and did not ingest channels the workspace had not selected.

## Operating context

A workspace owner created a workspace, connected Slack, selected in-scope channels, and
reviewed drafts in an application queue. Confirmed work was written to a tracker with source
context. Members could inspect confirmed tasks and audit records.

## Capabilities and constraints

- Slack was connected by an owner or administrator.
- Unticked channels were not read.
- A proposed owner or due date was retained only when supported by the conversation.
- The production tracker integration was Linear.
- Production was not to expose synthetic or demo paths.
- The application was server-rendered TypeScript/Express with CSP-safe markup.

## Product principles

- Human confirmation was mandatory before every tracker write.
- Channel scope was chosen explicitly, not inferred.
- Source context survived the Slack-to-tracker handoff.
- A missed commitment was preferable to an unreviewed task.
- The product was intended to make accountability clearer, not add automation theater.

## Accessibility

The intended web experience included keyboard-operable controls, meaningful form states,
responsive layout, and reduced-motion support, with WCAG 2.2 AA as the target where practical.
