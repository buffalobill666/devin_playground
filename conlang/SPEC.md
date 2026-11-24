# Conlang — working name decided by the generator

"Outside the world" direction from `INTERESTS.md` (item A).
First move: phonology + word generator (`gen.py`).

## Phonology v0.1

**Consonants (9):** p t k m n s l r w. A small system:
three voiceless stops, two nasals, one fricative, a trill,
a lateral, a glide.

**Vowels (5):** a e i o u.

**Syllable:** (C)V(N) — open, optional nasal coda.
Nasal harmony: `n` after front vowels (e, i), `m` after
back (o, u); after `a` — m.

**Phonotactics:**
- no clusters except nasal+consonant across a syllable
  boundary (`tam.ka` is the only permitted kind)
- no vowel sequences: hiatus resolves either with a glide
  (30%; `j` after a/e/i, `w` after o/u) or a regular onset
- words begin with a consonant

**Onset weights:** p t k s l frequent, w rare — rarity of the
sound = rarity of words containing it = future markedness.

## Morphology v0.1 (`morph.py`)

Agglutinative suffixes; affixes obey phonotactics:

- **Hiatus allomorphy:** a vowel-initial suffix after a
  vowel-final stem inserts the epenthetic glide by the same
  rule the word generator uses: `j` after a/e/i, `w` after
  o/u. `luno`+`-in` = `lunowin`, `lale`+`-an` = `lalejan`.
  Allomorphy isn't chosen — it *follows* from phonology.
- **Nouns:** -in plural, -an collective, -ka definite,
  -ti diminutive.
- **Verbs:** -sa past, -ra future; present = bare stem.
- **Derivation (verb→noun):** -ne "one who", -la "place of",
  -um "the act of". `polara` "to look" → `polarajum` "a look".
- **Syntax:** SOV, no cases — roles by word order.

## Open questions (next moves)

- pragmatics: who is the language for — people, fields,
  archives?
- `gen.py` emits words; no glossary attached yet — meanings
  await the grammar, not the other way round
