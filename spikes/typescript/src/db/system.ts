// The ONLY cross-tenant code path in the spike, and it reads identifiers, never content.
// Everything else must go through WorkspaceScope. The tenant lint allowlists exactly this
// file and scope.ts to import the tenant tables.
import { and, eq, inArray, lte } from 'drizzle-orm';
import type { Db } from './client.ts';
import { jobs, workspaces } from './schema.ts';
import { WorkspaceScope } from './scope.ts';

export type JobRow = typeof jobs.$inferSelect;

export function createWorkspace(db: Db, input: { id: string; name: string; budgetMicros?: number }) {
  db.insert(workspaces).values({
    id: input.id, name: input.name,
    budgetMicros: input.budgetMicros ?? 1_000_000, createdAt: Date.now(),
  }).onConflictDoNothing().run();
  return WorkspaceScope.open(db, input.id);
}

export function listWorkspaces(db: Db) {
  return db.select().from(workspaces).all();
}

/** Atomically claim the next runnable job from the given queues. */
export function claimNextJob(db: Db, queues: JobRow['queue'][]): JobRow | null {
  return db.transaction((tx) => {
    const job = tx.select().from(jobs).where(and(
      eq(jobs.status, 'queued'), lte(jobs.runAt, Date.now()), inArray(jobs.queue, queues),
    )).orderBy(jobs.runAt).limit(1).get();
    if (!job) return null;
    tx.update(jobs).set({ status: 'running', attempts: job.attempts + 1 })
      .where(and(eq(jobs.workspaceId, job.workspaceId), eq(jobs.id, job.id))).run();
    return { ...job, status: 'running' as const, attempts: job.attempts + 1 };
  });
}

export function finishJob(db: Db, job: JobRow) {
  db.update(jobs).set({ status: 'done' })
    .where(and(eq(jobs.workspaceId, job.workspaceId), eq(jobs.id, job.id))).run();
}

/** Bounded retry with backoff; dead-letter after maxAttempts (ADR 0004 rule 9). */
export function failJob(db: Db, job: JobRow, error: string) {
  const dead = job.attempts >= job.maxAttempts;
  const backoffMs = Math.min(30_000, 250 * 2 ** job.attempts) + Math.floor(Math.random() * 100);
  db.update(jobs).set({
    status: dead ? 'dead' : 'queued',
    lastError: error.slice(0, 500),
    runAt: Date.now() + backoffMs,
  }).where(and(eq(jobs.workspaceId, job.workspaceId), eq(jobs.id, job.id))).run();
  return { dead };
}

export function countDeadJobs(db: Db): number {
  return db.select().from(jobs).where(eq(jobs.status, 'dead')).all().length;
}
