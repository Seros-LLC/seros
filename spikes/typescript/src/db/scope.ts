import { and, desc, eq, sql } from 'drizzle-orm';
import { randomUUID } from 'node:crypto';
import type { Db } from './client.ts';
import {
  actionMeter, auditLog, confirmations, drafts, jobs, members, sourceMessages, workspaces,
} from './schema.ts';

export type Actor = { kind: 'system'; name: string } | { kind: 'member'; memberId: string };
const actorLabel = (a: Actor) => (a.kind === 'system' ? `system:${a.name}` : `member:${a.memberId}`);

declare const proofBrand: unique symbol;
/**
 * Proof that a Confirmation row exists. Only WorkspaceScope.proveConfirmation can produce
 * one, and the tracker writer will not accept anything else, so "no tracker write without
 * a human confirmation" (ADR 0002) is a type-level fact, not a code-review habit.
 */
export type ConfirmationProof = {
  readonly [proofBrand]: true;
  readonly workspaceId: string;
  readonly confirmationId: string;
  readonly draftId: string;
  readonly memberId: string;
};

export type DraftRow = typeof drafts.$inferSelect;
export type MessageRow = typeof sourceMessages.$inferSelect;
export type MeterOutcome = typeof actionMeter.$inferSelect['outcome'];

export class UnknownWorkspaceError extends Error {}

/**
 * The ONLY way to read or write tenant-owned rows.
 *
 * Structural properties:
 *  - It cannot be constructed without an existing workspace id (open() checks).
 *  - Every method injects `workspaceId` itself; callers pass Omit<Insert,'workspaceId'>,
 *    so passing another tenant's id is a compile error, not a runtime bug.
 *  - There is no escape hatch: no raw query method, no db getter.
 */
export class WorkspaceScope {
  private constructor(private readonly db: Db, readonly workspaceId: string) {}

  static open(db: Db, workspaceId: string): WorkspaceScope {
    const row = db.select().from(workspaces).where(eq(workspaces.id, workspaceId)).get();
    if (!row) throw new UnknownWorkspaceError(`unknown workspace ${workspaceId}`);
    return new WorkspaceScope(db, workspaceId);
  }

  private mine<T extends { workspaceId: any }>(table: T) {
    return eq(table.workspaceId, this.workspaceId);
  }

  // ---------- audit + meter ----------

  audit(input: {
    entity: string; entityId: string; action: string; actor: Actor;
    metadata?: Record<string, string | number | null>;
  }): void {
    this.db.insert(auditLog).values({
      workspaceId: this.workspaceId,
      id: randomUUID(),
      entity: input.entity,
      entityId: input.entityId,
      action: input.action,
      actor: actorLabel(input.actor),
      metadata: input.metadata ?? {},
      at: Date.now(),
    }).run();
  }

  listAudit() {
    return this.db.select().from(auditLog).where(this.mine(auditLog)).orderBy(auditLog.at).all();
  }

  meter(row: Omit<typeof actionMeter.$inferInsert, 'workspaceId' | 'id' | 'at'>): void {
    this.db.insert(actionMeter).values({
      ...row, workspaceId: this.workspaceId, id: randomUUID(), at: Date.now(),
    }).run();
  }

  listMeter() {
    return this.db.select().from(actionMeter).where(this.mine(actionMeter)).orderBy(actionMeter.at).all();
  }

  spentMicros(): number {
    const r = this.db.select({ total: sql<number>`coalesce(sum(${actionMeter.costMicros}), 0)` })
      .from(actionMeter).where(this.mine(actionMeter)).get();
    return r?.total ?? 0;
  }

  budgetMicros(): number {
    const r = this.db.select().from(workspaces).where(eq(workspaces.id, this.workspaceId)).get();
    return r?.budgetMicros ?? 0;
  }

  // ---------- members ----------

  listMembers() {
    return this.db.select().from(members).where(this.mine(members)).all();
  }

  member(memberId: string) {
    return this.db.select().from(members)
      .where(and(this.mine(members), eq(members.id, memberId))).get() ?? null;
  }

  addMember(input: Omit<typeof members.$inferInsert, 'workspaceId'>) {
    this.db.insert(members).values({ ...input, workspaceId: this.workspaceId }).run();
  }

  // ---------- ingest ----------

  /** Idempotent on (workspace_id, channel_id, slack_ts). */
  ingestMessage(input: Omit<typeof sourceMessages.$inferInsert, 'workspaceId' | 'id' | 'receivedAt'>)
    : { message: MessageRow; created: boolean } {
    const existing = this.db.select().from(sourceMessages).where(and(
      this.mine(sourceMessages),
      eq(sourceMessages.channelId, input.channelId),
      eq(sourceMessages.slackTs, input.slackTs),
    )).get();
    if (existing) return { message: existing, created: false };
    const row = {
      ...input, workspaceId: this.workspaceId, id: randomUUID(), receivedAt: Date.now(),
    };
    this.db.insert(sourceMessages).values(row).run();
    this.audit({
      entity: 'source_message', entityId: row.id, action: 'ingested',
      actor: { kind: 'system', name: 'webhook' },
      metadata: { channel_id: row.channelId, slack_ts: row.slackTs, chars: row.text.length },
    });
    return { message: row, created: true };
  }

  getMessage(id: string) {
    return this.db.select().from(sourceMessages)
      .where(and(this.mine(sourceMessages), eq(sourceMessages.id, id))).get() ?? null;
  }

  listMessages() {
    return this.db.select().from(sourceMessages).where(this.mine(sourceMessages)).all();
  }

  // ---------- drafts ----------

  /** Idempotent on (workspace_id, source_message_id, prompt_version). */
  upsertDraft(input: Omit<typeof drafts.$inferInsert, 'workspaceId' | 'id' | 'createdAt' | 'status'>)
    : { draft: DraftRow; created: boolean } {
    const existing = this.db.select().from(drafts).where(and(
      this.mine(drafts),
      eq(drafts.sourceMessageId, input.sourceMessageId),
      eq(drafts.promptVersion, input.promptVersion),
    )).get();
    if (existing) return { draft: existing, created: false };
    const row = {
      ...input,
      proposedOwnerId: input.proposedOwnerId ?? null,
      dueDate: input.dueDate ?? null,
      trackerTaskId: input.trackerTaskId ?? null,
      workspaceId: this.workspaceId, id: randomUUID(),
      status: 'pending' as const, createdAt: Date.now(),
    };
    this.db.insert(drafts).values(row).run();
    this.audit({
      entity: 'draft', entityId: row.id, action: 'created',
      actor: { kind: 'system', name: 'worker' },
      metadata: { source_message_id: row.sourceMessageId, prompt_version: row.promptVersion, confidence: row.confidence },
    });
    return { draft: row, created: true };
  }

  getDraft(id: string): DraftRow | null {
    return this.db.select().from(drafts)
      .where(and(this.mine(drafts), eq(drafts.id, id))).get() ?? null;
  }

  listDrafts(status?: DraftRow['status']) {
    const where = status ? and(this.mine(drafts), eq(drafts.status, status)) : this.mine(drafts);
    return this.db.select().from(drafts).where(where).orderBy(desc(drafts.createdAt)).all();
  }

  updateDraft(id: string, patch: Partial<Pick<DraftRow,
    'title' | 'outcome' | 'proposedOwnerId' | 'dueDate' | 'status' | 'trackerTaskId'>>, actor: Actor)
    : DraftRow | null {
    const before = this.getDraft(id);
    if (!before) return null;
    this.db.update(drafts).set(patch).where(and(this.mine(drafts), eq(drafts.id, id))).run();
    this.audit({
      entity: 'draft', entityId: id, action: `updated:${Object.keys(patch).sort().join(',')}`,
      actor, metadata: { status: patch.status ?? before.status, tracker_task_id: patch.trackerTaskId ?? null },
    });
    return this.getDraft(id);
  }

  // ---------- confirmation ----------

  /** Idempotent on (draft_id, member_id): first confirmation wins. */
  confirm(draftId: string, memberId: string): { confirmationId: string; created: boolean } {
    const draft = this.getDraft(draftId);
    if (!draft) throw new Error(`draft ${draftId} not in workspace ${this.workspaceId}`);
    const member = this.member(memberId);
    if (!member) throw new Error(`member ${memberId} not in workspace ${this.workspaceId}`);
    if (member.role === 'viewer') throw new Error('viewer may not confirm');
    const existing = this.db.select().from(confirmations).where(and(
      this.mine(confirmations), eq(confirmations.draftId, draftId), eq(confirmations.memberId, memberId),
    )).get();
    if (existing) return { confirmationId: existing.id, created: false };
    const id = randomUUID();
    this.db.insert(confirmations).values({
      workspaceId: this.workspaceId, id, draftId, memberId, createdAt: Date.now(),
    }).run();
    this.updateDraft(draftId, { status: 'confirmed' }, { kind: 'member', memberId });
    this.audit({
      entity: 'confirmation', entityId: id, action: 'created',
      actor: { kind: 'member', memberId }, metadata: { draft_id: draftId },
    });
    return { confirmationId: id, created: true };
  }

  /** The only producer of ConfirmationProof. Returns null when no confirmation exists. */
  proveConfirmation(confirmationId: string): ConfirmationProof | null {
    const row = this.db.select().from(confirmations)
      .where(and(this.mine(confirmations), eq(confirmations.id, confirmationId))).get();
    if (!row) return null;
    return {
      workspaceId: row.workspaceId, confirmationId: row.id,
      draftId: row.draftId, memberId: row.memberId,
    } as ConfirmationProof;
  }

  listConfirmations() {
    return this.db.select().from(confirmations).where(this.mine(confirmations)).all();
  }

  // ---------- queue ----------

  enqueue(queue: typeof jobs.$inferSelect['queue'], type: string, payload: Record<string, string>): string {
    const id = randomUUID();
    this.db.insert(jobs).values({
      workspaceId: this.workspaceId, id, queue, type, payload,
      status: 'queued', attempts: 0, maxAttempts: 3, runAt: Date.now(), createdAt: Date.now(),
    }).run();
    return id;
  }

  listJobs() {
    return this.db.select().from(jobs).where(this.mine(jobs)).all();
  }
}
