import Database from 'better-sqlite3';
import { drizzle } from 'drizzle-orm/better-sqlite3';
import { migrate } from 'drizzle-orm/better-sqlite3/migrator';
import { mkdirSync } from 'node:fs';
import { dirname } from 'node:path';
import { config } from '../config.ts';

export type Db = ReturnType<typeof drizzle>;

/**
 * Opens the database and applies migrations. The returned handle is deliberately NOT
 * exported as a module singleton: tenant data is only reachable through WorkspaceScope
 * (see scope.ts), and the tenant lint fails the build if any other module imports the
 * tenant tables directly.
 */
export function openDb(path: string = config.dbPath): Db {
  if (path !== ':memory:') mkdirSync(dirname(path), { recursive: true });
  const sqlite = new Database(path);
  sqlite.pragma('journal_mode = WAL');
  sqlite.pragma('foreign_keys = ON');
  const db = drizzle(sqlite);
  migrate(db, { migrationsFolder: new URL('../../drizzle', import.meta.url).pathname });
  return db;
}
