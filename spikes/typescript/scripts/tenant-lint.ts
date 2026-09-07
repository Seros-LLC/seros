/**
 * Static tenancy guard for the TypeScript spike.
 *
 * Tenant-owned schema declarations may only be imported by the scope and the
 * queue/system layer. Route and provider code must reach tenant data through
 * WorkspaceScope, so workspace predicates cannot be accidentally omitted.
 */
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { dirname, join, relative } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const TENANT_TABLES = new Set([
  'members', 'sourceMessages', 'drafts', 'confirmations', 'auditLog', 'actionMeter', 'jobs',
]);
const ALLOWED = new Set([
  'src/db/schema.ts',
  'src/db/scope.ts',
  'src/db/system.ts',
]);

function walk(dir: string, out: string[] = []): string[] {
  for (const name of readdirSync(dir)) {
    if (name === 'node_modules' || name === '.git' || name === 'dist') continue;
    const path = join(dir, name);
    if (statSync(path).isDirectory()) walk(path, out);
    else if (path.endsWith('.ts')) out.push(path);
  }
  return out;
}

const offenders: string[] = [];
const importPattern = /import\s+(?:type\s+)?\{([\s\S]*?)\}\s+from\s+['"][^'"]*schema\.ts['"]/g;
for (const file of walk(join(ROOT, 'src'))) {
  const rel = relative(ROOT, file).replace(/\\/g, '/');
  if (ALLOWED.has(rel)) continue;
  const source = readFileSync(file, 'utf8');
  for (const match of source.matchAll(importPattern)) {
    const names = match[1];
    if (!names) continue;
    for (const raw of names.split(',')) {
      const name = raw.trim().split(/\s+as\s+/)[0]?.trim();
      if (name && TENANT_TABLES.has(name)) offenders.push(`${rel} imports tenant table '${name}'`);
    }
  }
}

if (offenders.length) {
  console.error('TENANCY CHECK FAILED: tenant tables must be accessed through WorkspaceScope');
  for (const offender of offenders) console.error(`  ${offender}`);
  process.exit(1);
}

console.log(JSON.stringify({ level: 'info', event: 'tenant_lint_ok', checked: [...TENANT_TABLES] }));
