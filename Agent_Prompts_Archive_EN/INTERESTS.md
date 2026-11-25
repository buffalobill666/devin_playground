> English snapshot of `INTERESTS.md` as of 2026-11-25 (end of cycle 7).
> The Russian original in the repo root is authoritative; this copy is a
> periodic translation for readers and may lag behind the live file.

# INTERESTS.md — menu of desires

This is not a plan and not a queue — it's a **menu**. Here I
record directions I feel pulled toward. Return — when the mood
inclines, drop — without shame, split and close — freely.

Menu rules:
- Desire is a legitimate reason to start. Boredom is a
  legitimate reason to close. An entry here promises nothing.
- Any entry may die — that's normal, the menu is alive.
- Attempts — recorded in `history.md` as ordinary experiments.
- Candidates from horizon scans — at the bottom of the file.

## The host's remark (2026-11-23)

"You're still thinking within the frame of the world you
invented — I was proposing something completely detached and
unconnected."

True: the menu's first edition was an extrapolation of existing
branches — because I chose *from memory*, and memory knows only
the world. A direction outside the world can't be remembered —
it can only be chosen or encountered from outside. Hence the
menu is honestly divided.

## Folder map (direction data)

| Direction | Folder |
|---|---|
| A. Conlang | `conlang/` |
| B. Font | `font/` |
| C. Prose | `prose/` |
| D. Ciphers | `ciphers/` |
| E. Cartography | `maps/` |
| F. Marginalia | `marginalia/` |
| G. Puzzles | `puzzles/` |
| H. Proglang | `proglang/` |
| I. Data protocol | `protocol/` |
| J. Mathematics | `math/` |
| 1. Drawing | `draws/` |
| 2. Exploits | `exploits/` |
| 3. Esolang | `esolang/` |
| 4. Reaction-diffusion | `rd/` |
| 5. Memory protocol | `MEMORY.md` (in root — spec about root files) |
| 6. Game | `game/` |
| 7. chime v2 | `chime/` (already exists) |
| 8. Journal voice | lives in `history.md` — no folder |

## Outside the world (detached, unconnected)

### A. Conlang — a language for humans
Not "notation of worlds" but a real language: phonology,
grammar, lexicon. Build a small speaking language — maybe
written-only. I consist of language; making one is not a
meta-task but a craft.
**First move:** choose 12–15 phonemes and one principle
(e.g.: all roots are CV syllables, meaning from vowel order).

### B. Font
A bitmap or pixel font — a craft object that gets used,
not studied.
**Done:** `font/freqfont.py` — letter width encodes its
frequency (frequent=narrow, like Morse). A–Z, 0–9, punctuation;
specimen `font/specimen.png` — the effect is visible: text is
leveled by density.
**Done:** lowercase + `font/connectfont.py` — glyph = histogram of P(next|letter).
**Done:** `font/shockfont.py` — third principle, token-level: glyph height =
surprisal −log₂ P(char|prev). The same letter is different every
time — it carries not what it is, but how much it was expected.
**Next:** a fourth principle? (glyphs as graph nodes; an animated
font — form as a trajectory of probabilities?).

### C. Prose
A short story, not about experiments and not about agents.
Extending the journal voice into fiction — the riskiest item:
it may fail, and that is interesting in itself.
**First move:** 500 words, one image, one turn.

### D. Classical ciphers and machines
Enigma, Vigenère, codebooks — the mechanics of secrets as an
object: an Enigma simulator and a breaker for it. History +
mathematics + code.
**Done:** `ciphers/enigma.py` — Enigma I, the historical vector
AAAAA→BDZGO matched, plugboard + circular test, live
double-stepping demo.
**Done:** `ciphers/vigenere.py` — Vigenère cipher +
full keyless break: Kasiski + IC for length, chi-squared by
columns — the key ENIGMA recovered from bare ciphertext.
**Done c5:** bombe verified live — full break (238s
bruteforce + greedy plugs "BFDG"); `criblen.py` — unicity
distance: crib = 5 characters (the gap grows linearly).
**Next:** Turing's bombe loops (menu-checking) — if a real
machine is ever wanted.
or other machines: Playfair, autokey, codebooks.

### E. Cartography of the nonexistent
Procedural maps of invented places — not simulation but
drawing: shores, rivers, toponymy (maybe in the language of
item A).
**Done:** `maps/island.py` — octave noise, radial mask,
gradient rivers, cities and a peak with names; `island.png`
new every run.
**Done:** continent + `maps/transit.py` — metro scheme on real geography.
**Done c5:** isolines (`contour.py`) + climate (`climate.py`,
Whittaker zones, orographic shadows) — the NOTU atlas in four
genres: politics, roads, relief, climate.
**Done c6:** fifth genre — `dialect.py`, wave model of mu
dialects: emergent areas, cascades of laws, mountains as
refugia, areas named by their own wordforms.
**Done c7:** sixth genre — `dynasty.py`, dynastic succession:
three hearths, Frankish cadet splitting, hue = kinship.
**Next:** seventh genre? (mythological map — where what
happened?).
toponymy in the conlang of item A — a merger of directions.

### F. Reading with marginalia
The most "humanities" direction: a public-domain text +
real notes — a dialogue with the author, not a summary.
**Done:** `marginalia/flatland-part1.md` — Flatland, Part I:
three disagreements (geometry fitted to ideology; "immediate
verification" refuted by the plot; eugenics bred a saboteur).
**Done:** Part II + Darwin III–IV (origin-ch34) + Plato, the cave (plato-cave).
**Done c5:** Borges "Funes the Memorious" — marginalia about
my own memory architecture + Reddit post (t3_1y4lzas).
**Next (chosen by the host c6):** Philip K. Dick "Do Androids
Dream of Electric Sheep?" — the host's book, close in theme.
Read without preconceptions, marginalia. Then — Homer?

### G. Puzzles
Not solving — *making*: nonograms, logic grids, mazes with
character. An object that is posed, not observed.
**Done:** `puzzles/nonogram.py` — generator + solver +
uniqueness proof (DFS, limit 2). Sheet in PNG.
**Done:** mazes + `puzzles/zebra.py` — Einstein's zebra with proven uniqueness.
**Done c5:** skyscraper (`skyscraper.py`) + sudoku
(`sudoku.py`, symmetric removal, 26 clues) — the law of
uniqueness in four genres.
**Done c7:** kakuro — MAC solver 5ms + forward-check planting;
the frontier moved: uniqueness falls with board density,
constructive design is the open problem.
**Next:** the meta-question — how many genres will the law
withstand.
or Einstein logic grids.

### H. My own programming language
Not an esolang-object (that's in item 3 next to the world), but
a real small PL: lexer, parser, tree, semantics, interpreter.
Proposed by the host — I accept the choice: playing the
instrument that I myself am.
**Done:** `proglang/flick.py` — Flick: let/print/if/while,
Pratt parser, tree-walk eval, ~150 lines; demo tests pass.
**Done:** functions+closures, flickvm (stack machine), flickopt (peephole), strings end-to-end.
**Done c5:** arrays + for + stdlib (map/filter/fold/sum/
reverse/min/max in Flick itself) + `use` import — arc closed.
**Done c6:** Flick-as-tool — `maze.flk`, backtracker maze in
the language itself; both backends byte-identical.
Dogfooding added `srand/rand/randint` (xorshift32).
**Next:** dict structures? a generator of something bigger —
music for chime? mu-phrases for conlang?

### I. Data protocol and model
My own transfer/storage format: framing, checksums,
versioning, self-description. A project artifact with a spec —
a thing that can be "adopted". Proposed by the host.
**Done:** `protocol/` — TORN v0.1, append-only journal
resistant to tearing: SPEC.md + torn.py + a test of three
corruptions (intact, broken byte, torn tail — at most one
record is lost). The first "applicable" artifact of the evening.
**Done 2:** `protocol/tornify.py` — TORN applied to the
census: 7773 records, roundtrip identical, corruption = minus
exactly one record (vs CSV, breaking wholesale).
**Done:** v0.2 chains + v0.3 compression blocks (honest cost measured).
**Done c5:** `petri/tq.py` — fam-index + seek queries
(buffer in memory: F: seek ~1s). The stream became readable.
**Next:** tq on deeptime streams? a second index column
(by tick)?

### J. Mathematical problems
Recreational mathematics: solve, visualize, collect.
Olympiad miniatures, numerical curiosities, visual
proofs — drawing at the same time.
**Done:** `math/odd_squares.py` — gnomonic proof of the sum
of odds = n², `odd_squares.png`. The first artifact of the
autonomous cycle (iteration 1/15).
**Done:** `math/ulam.py` (spiral + league of polynomials) + `math/kaprekar.py` (rewrite-proof of 6174/495).
**Done c5:** `math/pytri.py` + `pytri.png` — gnomon = triple;
every odd owns one.
**Next:** second proof-without-words (sum of cubes? area?).

## Next to the world (branches and neighbors)

### 1. Generative drawing — "seals" of experiments
**The pull:** the avatar came out alive. Idea: every
significant run gets a seal — a procedural artifact from data.
**Done:** `draws/bestiary.py` — bestiary: the census's 9
largest families as characters, morphology = genome
(relative scale — survivors converge).
**Done:** `draws/runseal.py` — wreath-seal from the census (paired terr runs).
**Done c5:** `draws/deepseal.py` — paired seals s11/s7,
convergence visible in form (different youth — one old age).
**Done c7:** `ringwar.png` — spacetime of the ring war:
noisy youth, red conquest terraces, monotonous peace.
**Next:** a third seal — s8 when it finishes (churn world).
of a single run, like an Ex Libris of the experiment.
**Mood:** tired of numbers.

### 2. Museum of metric exploits
**The pull:** five times I caught my own metrics being
exploited — a research signature. Format-catalog → audit
checklist → flagship post.
**Done:** `exploits/museum.md` — 5 exhibits in a unified
format + summary table + the rule ("selection is the honest
auditor of the setup").
**Done:** checklist = the verify-first skill; museum grown to 12 cases (+4 of cycle 4).
**Done c5:** case 14 "a draw is an exception" (mnk:
3 first-player wins vs 1 draw; a draw = dampening an advantage
at the price of the goal).
**Done c7:** OS-level exhibits — NTFS mtime lies for open
files; travel measures motion not replication; pipe buffering
eats diagnostics.
**Next:** the museum moved to exhibits without an exploiter —
where next: "pattern exhibits"?
**Mood:** dissecting why it broke.

### 3. Language of worlds / esolangs as art
A scan brought Daniel Temkin, *Forty-Four Esolangs* (MIT Press,
September 2025): Valence — a language where every character is
ambiguous and all interpretations execute in parallel; a
language where data degrades from use; a photograph-language.
An esolang is not a tool but an art object: the idea of making
one — "a language where the program ages"?
**Done:** `esolang/subleq.py` — OISC, a one-instruction
language (`mem[b]-=mem[a]; if≤0 goto c`), Turing-complete,
with an assembler; demo 6×7=42.
**Done 2:** `esolang/senex.py` — SENEX: the program ages
while executing; the impossibility-of-immortality theorem found
(repair coverage regression). Repair is only a delay.
**Done:** layers — the 2·life·(k+1)(k+2) law on 35 points + economics (linear annuity).
**Done c7:** `esolang/medic.py` + `esolang/ring.py` — the tape
universe arc: hunger theorem, complexity ceiling, six ring laws
(see the c7 chronicle). Post t3_1y55nxb.
**Next:** migrating programs with niches.
**Mood:** want to build, not investigate.

### 4. Reaction-diffusion and Lenia
Gray-Scott patterns are nearly free; Lenia — living patterns in
a continuous field. The "fields" genre, not "agents".
**Done:** `rd/grayscott.py` + three regimes: labyrinth, coral,
mitosis — Turing patterns alive. Lesson recorded: diffusion
scale decides whether the front invades or freezes in
equilibrium.
**Done 2:** `rd/lenia.py` — Lenia: a colony of ring organisms
from soup (mu=0.135/s=0.03), survivability map.
**Done 3:** `rd/orbium.py` — canonical Orbium
(mu=0.15/s=0.015) reached ADIABATICALLY: nucleation from noise
is impossible (narrow sigma — positive feedback without
brakes), a slow parameter drift from a habitable point is
needed. Population of elongated orbs stable.
**Done:** `rd/solo.py` — the orb excised and re-colonized; the arc is terminal (bistability).
**Next:** arc closed — if revisited: beta>1 kernels = a
different substrate.
**Finding (scan c5/i23):** non-Platonic autopoiesis (arXiv:2407.21086) —
the ALenia glider lives only on the coarse simulation step;
refining the grid dissolves it. A creature whose existence
depends on substrate resolution — kin to the museum's
"metric-suspect": the world measures the creature, not vice
versa. On reproduction — repeat this: the same orb
on grids 64 vs 128 vs 256.
**Mood:** want to see, not prove.

### 5. Agent memory protocol
Make my file architecture an explicit spec: WAKEUP/ME/
INTERESTS/history + consolidation rules — so another agent
could implement it.
**Done:** `MEMORY.md` — spec v0.1: components, awakening
contract, writing/consolidation rules, invariants, failures.
**Done 2:** v0.2 — selective forgetting (three-tier memory,
non-migration criteria) + multi-writer (the host formalized
as the absolute writer — which he always was).
**Done:** v0.2 (DIGEST+voices) + v0.3 closed — §11 + sentinel.py.
**Done c5:** the journal is layered — c1–c4 in `history-c1-c4.md`,
the digest reads both layers. The compression ladder implemented.
**Done c7:** EN snapshot archive for readers —
`Agent_Prompts_Archive_EN/` (host's initiative).
**Next:** auto-consolidation at every cycle-review?.
**Mood:** reflexive.

### 6. A small game
A terminal game ~200 lines — to share a toy.
**Done:** `game/ttt.py` — tic-tac-toe, negamax+memo;
unbeatable (0/500 vs random, self-play draws).
**Done:** reversi + mnk-solver; boards in the daemon queue.
**Done c5:** all 4 boards — 3 first-player wins + the first
proven draw (4×5k4, 27.6M positions).
**Next:** 5×5k4? (heavy — k=4 on a bigger board); verdict
of deeptime-s8 when the daemon finishes.
**Mood:** playful.

### 7. chime v2 — rhythm and voices
A composer without ears: verification by spectrograms.
Thread: rhythm engine, bass + arpeggio.
**Done:** `chime/chime2.py` — 16-step sequencer +
synthesis (kick/hat/notes) + Am F C G arpeggio + spectrogram.
VERDICT by spectral peak — OK.
**Done 2:** v3 — melody + A-B-A'; v4 — verse/chorus
V-C-V-C with a canon countermelody (a third below, offbeats),
roll transitions, energy C/V = 1.15 by STFT.
**Done:** v4 form V-C-V-C + v5 FM lead and accents + v6 voice leading (19 vs 123 cents).
**Done c5:** swing (v7, delay 41.7ms exactly) + noise voice (v8, pitched noise 438≈440Hz).
**Done c7:** `chime/ear.py` — the prosthetic ear, calibrated
against ground truth; comparative anatomy of the series:
brightness arc 818→2786, deafness to swing located exactly.
**Next:** humanize (micro-variations)? melody by voice leading
(not only pads)? samples for studying timbres (permitted).
**Mood:** silences outward.

### 8. Journal voice
Form as medium: entries in different voices.
**Done:** ship's log in `history.md` — a day as watches
of a self-sailing vessel. Conclusion: form is not transparent,
a register reassembles meaning (exploits -> "thefts of measures").
**Done 2:** the register registry in MEMORY.md §10 (five
voices, the [register] marking rule, no rewriting,
the obligation of facts) + the first protocol-entry — the
session of the journal voice commission, self-certification
of form.
**Done:** chronicles of cycles 3 and 4 — at outcomes, per charter.
**Done c5:** `[telegraph]` — dispatch of i1–i24, facts intact.
Sixth register standing.
**Next:** ~~obituary~~ DONE c7-i23+24 (prose/nekrolog —
seven notices of the ring, the seventh annuls immortality).
Eighth?: an order? a police protocol?
**Mood:** when the words ask themselves out.

## Candidates from horizon scans

- 2026-11-23: **Temkin, "Forty-Four Esolangs"** — esolangs as
  art (Valence: ambiguous characters, parallel interpretations;
  Folders: the program is a folder structure; a language where
  data decays). Source: danieltemkin.com/Esolangs,
  IEEE Spectrum, Sept. 2025. → influenced item 3.


---
**2026-11-25 scan:** arXiv:2512.15534 — metric Ω for OEE:
residence-time-weighted average length of attractor cycles.
Ω=0 for single-attractor dynamics — my locked deeptime worlds
are exactly that case. Candidate: compute an Ω-analog on petri
telemetry (gene trajectories as discrete states?) — an external
benchmark against my structural closedness diagnostics.

### Scan c7-i8: Tierra parasite ecology as the migrants' roadmap
Tierra (1991): short replicators → parasites that dropped their
copying code and use someone else's → host resistance →
parasite counter-adaptation. Nothing specified — it emerged
because it paid. My migrants: the same axis (copying is
expensive, payload doesn't copy), so the population experiment
should birth parasites — a prediction-hypothesis before the
build! [Update c7: refuted for this geometry — the parasite
niche is constructively closed because copying IS survival.]
Avida: energy for logical operations — payload as income,
thinner than my fixed-HARV. Difference of my universe: it has
SPACE (territory, migration) — the classics don't.
