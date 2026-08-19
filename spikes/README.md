# Spikes

Two implementations of the same vertical slice, built to decide
[ADR 0003](../docs/adr/0003-language-and-runtime.md) with evidence instead of taste. The
decision and what it actually rested on are in
[ADR 0005](../docs/adr/0005-language-and-runtime-typescript.md).

| | |
|---|---|
| [`typescript/`](typescript) | Option B, typed one-language. **Chosen.** |
| [`python/`](python) | Option A, dynamic batteries-included. Not chosen. |

Both are throwaway. Neither is maintained, neither is wired to anything, and nothing in
either directory should be imported by real code. They are kept because ADR 0003 required
the measurements to be attached to the decision, and because the next person deserves to see
what the alternative actually looked like rather than a description of it.

Dependencies were installed locally when these were built and are gitignored; the source is
what matters here.
