# Three prices of immunity, one end of war

*Comparative analysis of three ecosystem runs differing only in the
cost of disease resistance. Written 2026-11-26, after the medium-cost
world completed its full 200k ticks. Pre-registered question: is the
medium-cost regime an eternal war, or a late lock-in?*

## The setup

Three worlds, same seed (11), same physics, differing in one parameter —
`resist-cost`, the per-tick metabolic price prey pay for their
resistance gene:

| world | run | ticks | resist-cost |
|---|---|---|---|
| cheap | `runs/ep300-s11` | 300k | 0.08 |
| medium | `runs/ep200-mc` | 200k | 0.20 |
| expensive | `runs/ep200-hc` | 200k | 0.50 |

Disease is endemic in all three (introduced at 5%, mortality 4%,
virulence exponent 2.0). Predators co-evolve (ferocity), prey
co-evolve vigilance and resistance.

## The headline: the eternal war is finite

The medium-cost world spent its first 120k ticks as the most violent
world ever observed in this universe — including a relapse at 100k
*after* a first false peace at 80k:

| block (k) | predator blooms >50 | prey crashes <1000 | pred max |
|---|---|---|---|
| 0–20 | 77 | 192 | 376 |
| 20–40 | 30 | 55 | 391 |
| 40–60 | 32 | 93 | 408 |
| 60–80 | 36 | 47 | 429 |
| 80–100 | **0** | **0** | 17 |
| 100–120 | **145** | 58 | **548** |
| 120–200 | **0** | **0** | 17–18 |

Then, after 120k: nothing. 80,000 ticks — longer than most worlds'
entire histories — without a single bloom or crash. The final state
is numerically indistinguishable from the other two worlds' locks:

| world | prey mean | prey min | pred mean | infected mean |
|---|---|---|---|---|
| cheap (0.08) | 3410 | 3167 | 15.8 | 15 |
| expensive (0.50) | 3212 | 3020 | 15.8 | 295 |
| medium (0.20) | 3384 | 3237 | 15.7 | 60 |

**Verdict on the pre-registered question: late lock-in. There is no
eternal war in this universe — but a war can last longer than half
the world's lifetime, and can resume after what looked like peace.**

## The mechanism: the last offensive

Fine-grained telemetry around the end of the war (mc, 100–125k,
2.5k windows):

```
time   pred   ferocity  vigilance
100k    25    0.730     0.939
103k   165    0.752     0.942
105k   267    0.784     0.954
108k   142    0.806     0.967   <- peak ferocity, peak bloom 548 at t=107600
110k   146    0.661     0.958
113k    16    0.497     0.964   <- collapse in <2k ticks
115k+   16    ~0.50     0.963   <- frozen for the remaining 88k
```

The war ended with the largest predator offensive in the world's
history (peak 548 — more than any bloom in any quieter world) and the
highest ferocity ever measured (0.806). It failed against vigilance
0.967. The predator population collapsed in under two thousand ticks,
and what survived was a different breed: ferocity ~0.50 — not a pause
in the arms race but its end, since a paused race would ratchet back
up. 88k ticks of low ferocity say it never did.

This is the **fifth world** showing the va-banque signature: the war's
final act is always an all-in predator offensive that either wins the
world or breaks the predators. Here it broke them.

## What the three regimes actually differ in

Not the destination — the path, and the disease's final intensity:

1. **The lock is universal.** All three worlds end at the same
   ecological attractor: prey ~3300, predators ~16, zero blooms,
   zero crashes. The population-level lock tolerates any tested
   resist cost.
2. **The path length is stochastic and cost-dependent.** Cheap
   resistance (0.08): the disease never became a meaningful pressure —
   the sterile splinter — and the world barely warred. Expensive
   (0.50): chronic smoldering — the disease is prevalent (~295
   infected) but stable, no demographic resets, no war. Medium
   (0.20): the worst of both — resistance too weak to suppress the
   disease, disease too weak to suppress prey density, so crashes
   and naive-cohort rebounds keep restarting the arms race. For 120k.
3. **The endemic level at lock is monotonic in cost**: 15 / 60 / 295
   infected for cost 0.08 / 0.20 / 0.50. Resistance cost sets how
   much the prey can afford, which sets where the disease's
   prevalence equilibrates — but not whether the world stabilizes.
4. **The war's engine was the predator race, not the disease race.**
   In mc, resistance oscillated trendlessly (0.67–0.75) while
   vigilance ratcheted 0.72 → 0.96 and saturated. The demographic
   resets were predator blooms, with disease as background mortality.
   The disease decided *how much* demographic noise the world
   endured; the vigilance/ferocity race decided when the noise ended.

## Revised law (supersedes the iteration-21/22 framing)

Earlier this cycle the three regimes were framed as three *kinds of
peace* — victory, occupation, eternal war. The completed data demotes
that framing: there is one peace, arrived at by three paths. What the
immunity price chooses is not the world's fate but **how much war the
world must survive before the vigilance wall goes up** — and what
the disease inherits afterwards.

Stability is not the absence of war. It is the exhaustion of attack.

## Caveats

- One seed per cost level. The lock timing is certainly stochastic;
  another seed may war longer or shorter, or relapse differently.
- 80k of post-war silence is long but finite; a longer run could in
  principle relapse again. The ferocity collapse makes this unlikely —
  the predator gene pool that fueled the war was demographically
  extinguished, not dormant.
- The reset mechanism (iteration 22) explains why the *middle* cost
  wars most; it does not by itself explain why the war must end.
  The ending mechanism is the vigilance ceiling — vigilance saturates
  around 0.96 in every world observed, and above it no ferocity ever
  evolved pays for itself.

## Artifacts

- Data: `runs/ep300-s11/dt.csv`, `runs/ep200-hc/dt.csv`, `runs/ep200-mc/dt.csv`
- Analysis scripts: `petri/epfinal.py` (single-world), comparative
  metrics computed inline (see history.md 2026-11-26)
- Chronicle: `history.md`, cycle 7 chronicle + this entry
