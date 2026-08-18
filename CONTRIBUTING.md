# Contributing to the Seros product repository

The organisation-wide contributing guide applies here: see `CONTRIBUTING.md` in the
[Seros-LLC/.github](https://github.com/Seros-LLC/.github) repository. It covers issues,
pull requests, commit conventions, review expectations, security reporting and ownership of
contributions. Read it first; this file only adds what is specific to the product.

## This repository is documentation-first

There is no application code here yet, and the language and runtime have not been chosen
([ADR 0003](docs/adr/0003-language-and-runtime.md)). Until that ADR is accepted:

- **Do not add application code, dependency manifests, lockfiles, build configuration or
  scaffolding.** A single file in a language decides the language. That decision has its own
  ADR and its own evidence, and it is not made by a pull request that needed somewhere to
  put a helper.
- Tooling that is genuinely language-neutral (documentation checks, link checking, secret
  scanning) is welcome.

## Repository-specific rules

| Rule | Why |
|---|---|
| **A change to a product principle needs an ADR, not a paragraph.** | Principles are published in the terms and on the website. Changing one is a customer communication before it is a commit |
| **Do not name a vendor, framework, language or model as chosen** unless an accepted ADR says so | This repository's job right now is to keep those decisions open and visible |
| **No invented numbers.** No benchmark, no cost figure, no accuracy claim without a recorded measurement | An assumption written as a fact becomes a promise in a sales call three months later |
| **Mark assumptions** with the word ASSUMPTION, in the document where they are made | Someone has to be able to find every assumption and correct it |
| **No customer content anywhere** — not in fixtures, not in examples, not in screenshots, not in issue descriptions | See [docs/TESTING-STRATEGY.md](docs/TESTING-STRATEGY.md) section 3 for how real threads are handled |
| **No emoji** in documents or commit messages | House style. Plain, calm, concrete |
| **Relative links must resolve within this repository** | CI enforces it. Do not link across repository boundaries with `../`; name the other repository in prose instead |
| **A control in [docs/SECURITY-CONTROLS.md](docs/SECURITY-CONTROLS.md) may only be marked `Implemented` with a link to the artefact** | CI enforces it. The document is the backlog behind the legal pack, and an unbacked claim there is a misrepresentation |
| **The three rules in the [README](README.md) are not negotiable in a pull request** | Human confirmation before any write, no customer content in logs, every model call metered |

## When code does arrive

The first code pull request should also:

1. Fill in the setup section of the README with commands that were actually run on a clean
   machine.
2. Add the test suite entry point and wire it into CI.
3. Update [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) where the implementation differs from
   the plan. The document is wrong the moment the code disagrees with it, and the document
   is the thing that gets fixed.
4. Supersede [ADR 0003](docs/adr/0003-language-and-runtime.md) with the decision and the
   spike measurements that produced it.

## Style

Markdown, ATX headings, tables where a table is clearer than prose, sentences that a tired
person can read. Say what is not known as plainly as what is.
