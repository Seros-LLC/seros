// Relational schema. Tenant-owned tables carry workspace_id in a COMPOSITE PRIMARY KEY,
// so a row cannot exist outside a workspace and no unique constraint is global.
import { sqliteTable, text, integer, primaryKey, uniqueIndex } from 'drizzle-orm/sqlite-core';

export const workspaces = sqliteTable('workspaces', {
  id: text('id').primaryKey(),
  name: text('name').notNull(),
  budgetMicros: integer('budget_micros').notNull().default(1_000_000),
  createdAt: integer('created_at').notNull(),
});

export const members = sqliteTable('members', {
  workspaceId: text('workspace_id').notNull().references(() => workspaces.id),
  id: text('id').notNull(),
  name: text('name').notNull(),
  role: text('role', { enum: ['admin', 'member', 'viewer'] }).notNull(),
}, (t) => [primaryKey({ columns: [t.workspaceId, t.id] })]);

export const sourceMessages = sqliteTable('source_messages', {
  workspaceId: text('workspace_id').notNull().references(() => workspaces.id),
  id: text('id').notNull(),
  channelId: text('channel_id').notNull(),
  slackTs: text('slack_ts').notNull(),
  authorId: text('author_id').notNull(),
  text: text('text').notNull(),
  permalink: text('permalink').notNull(),
  receivedAt: integer('received_at').notNull(),
}, (t) => [
  primaryKey({ columns: [t.workspaceId, t.id] }),
  // Ingest idempotency key from ARCHITECTURE.md section 6, scoped by tenant.
  uniqueIndex('source_messages_ingest_key').on(t.workspaceId, t.channelId, t.slackTs),
]);

export const drafts = sqliteTable('drafts', {
  workspaceId: text('workspace_id').notNull().references(() => workspaces.id),
  id: text('id').notNull(),
  sourceMessageId: text('source_message_id').notNull(),
  title: text('title').notNull(),
  outcome: text('outcome').notNull(),
  proposedOwnerId: text('proposed_owner_id'),
  dueDate: text('due_date'),
  sourcePermalink: text('source_permalink').notNull(),
  status: text('status', { enum: ['pending', 'confirmed', 'written', 'rejected', 'needs_review'] }).notNull(),
  promptVersion: text('prompt_version').notNull(),
  confidence: integer('confidence').notNull(),
  trackerTaskId: text('tracker_task_id'),
  createdAt: integer('created_at').notNull(),
}, (t) => [
  primaryKey({ columns: [t.workspaceId, t.id] }),
  // Draft idempotency: one draft per source message per prompt version.
  uniqueIndex('drafts_source_prompt_key').on(t.workspaceId, t.sourceMessageId, t.promptVersion),
]);

export const confirmations = sqliteTable('confirmations', {
  workspaceId: text('workspace_id').notNull().references(() => workspaces.id),
  id: text('id').notNull(),
  draftId: text('draft_id').notNull(),
  memberId: text('member_id').notNull(),
  createdAt: integer('created_at').notNull(),
}, (t) => [
  primaryKey({ columns: [t.workspaceId, t.id] }),
  // Confirm idempotency key (draft_id, member_id): first confirmation wins.
  uniqueIndex('confirmations_key').on(t.workspaceId, t.draftId, t.memberId),
]);

export const auditLog = sqliteTable('audit_log', {
  workspaceId: text('workspace_id').notNull().references(() => workspaces.id),
  id: text('id').notNull(),
  entity: text('entity').notNull(),
  entityId: text('entity_id').notNull(),
  action: text('action').notNull(),
  actor: text('actor').notNull(),
  // Content-free metadata only (README rule 2: never log customer content).
  metadata: text('metadata', { mode: 'json' }).$type<Record<string, string | number | null>>().notNull(),
  at: integer('at').notNull(),
}, (t) => [primaryKey({ columns: [t.workspaceId, t.id] })]);

export const actionMeter = sqliteTable('action_meter', {
  workspaceId: text('workspace_id').notNull().references(() => workspaces.id),
  id: text('id').notNull(),
  provider: text('provider').notNull(),
  modelId: text('model_id').notNull(),
  tier: text('tier').notNull(),
  purpose: text('purpose').notNull(),
  promptVersion: text('prompt_version').notNull(),
  inputTokens: integer('input_tokens').notNull(),
  outputTokens: integer('output_tokens').notNull(),
  costMicros: integer('cost_micros').notNull(),
  latencyMs: integer('latency_ms').notNull(),
  outcome: text('outcome', {
    enum: ['ok', 'provider_error', 'timeout', 'invalid_output', 'budget_blocked', 'missing_credential'],
  }).notNull(),
  at: integer('at').notNull(),
}, (t) => [primaryKey({ columns: [t.workspaceId, t.id] })]);

export const jobs = sqliteTable('jobs', {
  workspaceId: text('workspace_id').notNull().references(() => workspaces.id),
  id: text('id').notNull(),
  queue: text('queue', { enum: ['detect', 'write', 'maintenance'] }).notNull(),
  type: text('type').notNull(),
  // Payload carries identifiers only, never message content.
  payload: text('payload', { mode: 'json' }).$type<Record<string, string>>().notNull(),
  status: text('status', { enum: ['queued', 'running', 'done', 'dead'] }).notNull(),
  attempts: integer('attempts').notNull().default(0),
  maxAttempts: integer('max_attempts').notNull().default(3),
  runAt: integer('run_at').notNull(),
  lastError: text('last_error'),
  createdAt: integer('created_at').notNull(),
}, (t) => [primaryKey({ columns: [t.workspaceId, t.id] })]);

/** Every tenant-owned table. The tenant lint script reads this list. */
export const TENANT_TABLES = [
  'members', 'source_messages', 'drafts', 'confirmations',
  'audit_log', 'action_meter', 'jobs',
] as const;
