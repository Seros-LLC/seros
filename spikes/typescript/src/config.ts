// Spike configuration. Everything has an offline-safe default.
export type BreakMode = 'none' | 'credential' | 'timeout' | 'malformed';

export const config = {
  dbPath: process.env.SEROS_DB ?? './data/spike.db',
  port: Number(process.env.PORT ?? 3000),
  slackSigningSecret: process.env.SLACK_SIGNING_SECRET ?? 'spike-signing-secret',
  // Which provider adapter the model client uses. 'fake' is deterministic and offline.
  provider: (process.env.SEROS_PROVIDER ?? 'fake') as 'fake' | 'http',
  // Real adapter credential. Deliberately unset in the spike.
  providerApiKey: process.env.SEROS_PROVIDER_API_KEY ?? '',
  providerBaseUrl: process.env.SEROS_PROVIDER_BASE_URL ?? 'https://api.invalid/v1',
  // The 2am test lever: force a failure inside the provider adapter.
  breakMode: (process.env.SEROS_BREAK ?? 'none') as BreakMode,
  defaultTimeoutMs: Number(process.env.SEROS_TIMEOUT_MS ?? 5000),
  // tier -> concrete model id + price, configuration not code (ADR 0004 rule 2).
  tiers: {
    cheap: { modelId: 'fake-cheap-1', microsPerInputToken: 1, microsPerOutputToken: 3 },
    standard: { modelId: 'fake-standard-1', microsPerInputToken: 5, microsPerOutputToken: 15 },
    careful: { modelId: 'fake-careful-1', microsPerInputToken: 20, microsPerOutputToken: 60 },
  },
} as const;
