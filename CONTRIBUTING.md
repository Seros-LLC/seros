# Contributing to the Seros product repository

The organisation-wide contributing guide applies here: see `CONTRIBUTING.md` in the
[Seros-LLC/.github](https://github.com/Seros-LLC/.github) repository. It covers issues,
pull requests, commit conventions, review expectations, security reporting and ownership of
contributions. Read it first; this file only adds what is specific to the product.

## This repository is documentation-first

This repository is the specification of a paused product. The language and runtime were
chosen: [ADR 0005](docs/adr/0005-language-and-runtime-typescript.md) records TypeScript on
Node and supersedes [ADR 0003](docs/adr/0003-language-and-runtime.md). The application lives
in [Seros-LLC/app](https://github.com/Seros-LLC/app), which is public. Application code
belongs there, not here; the only code in this repository is the archived evidence under
[`spikes/`](spikes/README.md).

## Repository-specific rules

| Rule | Why |
|---|---|
| **A change to a product principle needs an ADR, not a paragraph.** | The principles were drafted as the product's commitments. Changing one is a decision, not an edit |
| **Do not name a vendor, framework, language or model as chosen** unless an accepted ADR says so | Decisions are recorded in ADRs, with their evidence |
| **No invented numbers.** No benchmark, no cost figure, no accuracy claim without a recorded measurement | An assumption written as a fact becomes a promise in a sales call three months later |
| **Mark assumptions** with the word ASSUMPTION, in the document where they are made | Someone has to be able to find every assumption and correct it |
| **No customer content anywhere** — not in fixtures, not in examples, not in screenshots, not in issue descriptions | See [docs/TESTING-STRATEGY.md](docs/TESTING-STRATEGY.md) section 3 for how real threads are handled |
| **No emoji** in documents or commit messages | House style. Plain, calm, concrete |
| **Relative links must resolve within this repository** | CI enforces it. Do not link across repository boundaries with `../`; name the other repository in prose instead |
| **A control in [docs/SECURITY-CONTROLS.md](docs/SECURITY-CONTROLS.md) may only be marked `Implemented` with a link to the artefact** | CI enforces it. The document maps the product's drafted commitments to controls, and an unbacked claim there is a misrepresentation |
| **The three rules in the [README](README.md) are not negotiable in a pull request** | Human confirmation before any write, no customer content in logs, every model call metered |

## Style

Markdown, ATX headings, tables where a table is clearer than prose, sentences that a tired
person can read. Say what is not known as plainly as what is.
