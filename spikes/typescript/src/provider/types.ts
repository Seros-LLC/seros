// ADR 0004 rule 1: the narrowest possible provider surface. One operation, no streaming,
// no tools, no provider SDK type anywhere else in the codebase.
export type ModelTier = 'cheap' | 'standard' | 'careful';

export interface ProviderMessage { role: 'system' | 'user'; content: string }

export interface ProviderRequest {
  modelId: string;
  messages: ProviderMessage[];
  maxOutputTokens: number;
  timeoutMs: number;
  temperature: number;
}

export interface ProviderResponse {
  text: string;
  inputTokens: number;
  outputTokens: number;
  modelId: string;
}

/** The whole vendor boundary. Two implementations: FakeProvider and HttpProvider. */
export interface ModelProvider {
  readonly name: string;
  generate(req: ProviderRequest): Promise<ProviderResponse>;
}

export class MissingCredentialError extends Error { readonly kind = 'missing_credential'; }
export class ProviderTimeoutError extends Error { readonly kind = 'timeout'; }
export class ProviderCallError extends Error { readonly kind = 'provider_error'; }
export class InvalidOutputError extends Error {
  readonly kind = 'invalid_output';
  constructor(message: string, readonly detail: string) { super(message); }
}
export class BudgetBlockedError extends Error { readonly kind = 'budget_blocked'; }
