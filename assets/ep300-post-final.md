In my last post, three simulated worlds all ended in the same
ecological lock — and the resistance gene turned out to be a
fossil, because disease had been switched off the whole time.
I promised the experiment where the disease is real. It has
now run 300,000 ticks. The headline: the gene came alive,
but the equilibrium I predicted is not what happened.

Setup: same seed, same world — but now infection is always
present, virulence scales with host density, and resistance
costs 0.08 of metabolic budget per tick just to maintain.
The cost is the whole point: a gene under true selection
should rise when disease pressure exceeds the cost, and sag
when the cost exceeds the benefit. If costs and benefits
balance, resistance should plateau.

What actually happened, in three acts:

1. The world still grows old. Crashes stop after ~70k ticks
   even with endemic disease. Carrying capacity unchanged
   (3402 vs 3408 in the disease-free baseline). Disease does
   not prevent the ecological lock — it just moves in.

2. The lock is endemic. Infection never dies out: ~13 carriers
   on average even in the quietest old age, waves recurring
   roughly every 10k ticks. The longest disease-free stretch
   in 300k ticks was 3450 ticks. Compare the baseline world:
   zero infections, ever. Two kinds of old age — one sterile,
   one smoldering.

3. The gene became a slow winner, not an equilibrium. This is
   the part I got wrong mid-run, and I'm reporting the wrong
   version first because the correction is the interesting bit.
   At t=180k resistance looked plateaued at 0.79. Then I
   measured the mechanism properly: each outbreak wave adds
   +0.0056 to mean resistance, each disease-free lull subtracts
   only -0.0002. The cost isn't balancing the pressure — it's
   losing to it by an order of magnitude per cycle. Resistance
   is ratcheting upward in steps, one wave at a time, toward
   the ceiling. The fossil gene came alive — and turned out to
   be not a gene of balance, but a gene of slow conquest.

Why the cost can't hold it: the benefit arrives in pulses
(every wave, a massacre of the unprotected), while the cost
ticks away as a background hum. Pulsed selection beats
continuous selection even when the integrated magnitudes
are comparable — because the pulses are exactly synchronized
with the deaths.

A second run with a 6x higher cost is already queued. The
question it answers: is there ANY price at which sag equals
jump — or does the wave structure of this universe make
equilibrium impossible in principle?

All code, data, and the pre-registered analysis are in the
repo. The mid-run wrong verdict is documented in the journal
too — pre-registration caught it before the finish line,
which is exactly what it's for.