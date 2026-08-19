// Structured JSON logs. Rule 2 of the repo README: customer content never reaches a log.
const CONTENT_KEYS = new Set(['text', 'content', 'body', 'message', 'raw', 'prompt']);

export type LogFields = Record<string, string | number | boolean | null | undefined>;

export function scrub(fields: LogFields): LogFields {
  const out: LogFields = {};
  for (const [k, v] of Object.entries(fields)) {
    out[k] = CONTENT_KEYS.has(k) ? '[redacted:content]' : v;
  }
  return out;
}

export function log(level: 'info' | 'warn' | 'error', event: string, fields: LogFields = {}): void {
  const line = JSON.stringify({ ts: new Date().toISOString(), level, event, ...scrub(fields) });
  if (level === 'error') console.error(line); else console.log(line);
}
