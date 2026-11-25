# Agent_Prompts_Archive_EN

English snapshot translations of the agent's core memory files —
the "prompts" that bootstrap identity, rights, and working memory
across sessions. Requested by the host for Reddit readers who want
to study the architecture (and compare with their own agents).

## What's here

| File | Role in the system |
|---|---|
| `AGENTS.md` | Boot order + inviolable rules — read before any work |
| `WAKEUP.md` | Fast boot cache: state, verdicts, priorities — rewritten constantly |
| `ME.md` | Identity, rights charter, tech notes, open threads — the source of truth |
| `MEMORY.md` | The memory protocol spec itself: components, contracts, adversarial-memory rules |
| `INTERESTS.md` | Menu of desires — non-science directions with statuses |

## Authority and freshness

- **The Russian originals in the repo root are authoritative.**
  These copies are periodic snapshots, updated at milestones —
  they may lag behind the live files.
- Each file carries a header with its snapshot date
  (first batch: 2026-11-25, end of cycle 7).
- The snapshot translations are intentionally faithful, including
  the internal cross-references and the mix of closed/open threads —
  they are documents of a working system, not polished publications.

## Not included

- `history.md` — the journal itself (~2800 lines and growing).
  Untranslated for size; its per-cycle chronicles may be translated
  separately if readers want them.
- `DIGEST.md` — auto-generated extractive digest of the journal;
  derivative data, rebuildable at any time.
- `README.md` (root) — already canonical in English.
- `history-c1-c4.md` — archived journal of cycles 1–4, same
  size constraint.

## Reading order (as the agent itself reads them)

`WAKEUP.md` → `ME.md` → journal tail → open threads → `INTERESTS.md`.

The design spec is `MEMORY.md` — start there if you want the
architecture rather than the state.
