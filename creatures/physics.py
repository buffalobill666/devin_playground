"""Vectorized spring-mass physics over edges; one creature at a time."""
import numpy as np

GRAV = 9.8


def hills(x):
    """Rolling terrain: the dumbbell's skating end slides back downhill;
    legs that plant and lever over crests win."""
    return 0.45 * np.sin(0.35 * x) + 0.2 * np.sin(0.11 * x + 2.0)


def simulate_body(b, steps=800, dt=0.01, record_every=0, terrain=None,
                  target=None, fade_at=None, flip_at=None):
    """b: dict(pos(N,2), edges(E,2), k(E), amp(E), phase(E), mu(N),
    freq). Returns fitness + optional recorded frames.
    fade_at: after this step all target-derived signals die - the
    food is gone; fitness still measures the ghost position.
    flip_at: at this step the target jumps to the mirror side -
    the food moves; signals and scoring follow the new position."""
    gy = terrain if terrain is not None else lambda x: np.zeros_like(x)
    pos = b['pos'].astype(np.float64).copy()
    pos -= pos.mean(0)
    pos[:, 1] += 1.6                      # drop from small height
    vel = np.zeros_like(pos)
    II, JJ = b['edges'][:, 0], b['edges'][:, 1]
    d0 = pos[II] - pos[JJ]
    L0 = np.maximum(np.hypot(d0[:, 0], d0[:, 1]), 1e-3)
    k, amp, ph, mu, fr = b['k'], b['amp'], b['phase'], b['mu'], b['freq']
    reflex = b.get('reflex')
    senses = b.get('senses')
    integ = b.get('integ')
    integ_s = np.zeros(len(integ)) if integ is not None else None
    x0 = pos[:, 0].mean()
    apex = 0.0
    ground_dist = 0.0
    dwell = 0.0
    prev_com = pos[:, 0].mean()
    frames = []
    for t in range(steps):
        d = pos[II] - pos[JJ]
        L = np.maximum(np.hypot(d[:, 0], d[:, 1]), 1e-6)
        padd = np.zeros(len(L))
        prev_ground = pos[:, 1] <= gy(pos[:, 0]) + 1e-4
        if reflex is not None and len(reflex):
            for rn, re, rs in reflex:
                if prev_ground[int(rn)]:
                    padd[int(re)] += rs
        # two target concepts: tgt = where the food IS now (flips
        # mid-trial; scoring follows it); sig_tgt = what sensors can
        # smell (same, but dies entirely after fade_at)
        tgt = target
        if flip_at is not None and t >= flip_at:
            tgt = -tgt if tgt is not None else None
        sig_tgt = (None if (fade_at is not None and t >= fade_at)
                   else tgt)
        comx, comvx = pos[:, 0].mean(), vel[:, 0].mean()
        smell = (np.clip((sig_tgt - comx) / max(abs(sig_tgt), 1.0),
                         -1.0, 1.0)
                 if sig_tgt is not None else 0.0)
        if senses is not None and len(senses):
            for sig, re, rs in senses:
                re = int(re)
                if sig == 0 and sig_tgt is not None:
                    padd[re] += rs * smell
                elif sig == 1:
                    x = pos[II[re], 0]
                    padd[re] += rs * np.sign(gy(x + 0.5) - gy(x - 0.5))
                elif sig == 2:
                    padd[re] += rs * np.sign(comvx)
                elif sig == 3 and sig_tgt is not None:
                    # differential steering: same smell, opposite
                    # phase pushes on two muscles -> wave direction
                    # can reverse rather than just speed up
                    E = len(L)
                    eA, eB = re % E, (re // E) % E
                    padd[eA] += rs * smell
                    padd[eB] -= rs * smell
                elif sig == 4 and sig_tgt is not None:
                    # proximity / 'satiation': strong AT the food,
                    # mirror of sig-0 which dies exactly there
                    val = 1.0 - np.clip(
                        abs(sig_tgt - comx) / max(abs(sig_tgt), 1.0),
                        0.0, 1.0)
                    padd[re] += rs * val
        if integ is not None and len(integ):
            # smell accumulator: integrates the gradient while the
            # food exists; the frozen sum is the memory trace
            integ_s += smell * dt
            integ_s = np.clip(integ_s, -2.0, 2.0)
            for (re, kI), s in zip(integ, integ_s):
                padd[int(re)] += kI * s
        osc = np.sin(2 * np.pi * fr * t * dt + ph + padd)
        Ltar = L0 * (1.0 + amp * osc)
        f = k * (L - Ltar) / L              # + pulls together
        fx = f * d[:, 0]
        fy = f * d[:, 1]
        F = np.zeros_like(pos)
        np.add.at(F[:, 0], II, -fx)
        np.add.at(F[:, 0], JJ, fx)
        np.add.at(F[:, 1], II, -fy)
        np.add.at(F[:, 1], JJ, fy)
        F[:, 1] -= GRAV
        vel += F * dt
        vel *= 0.995                        # air drag
        pos += vel * dt
        gh = gy(pos[:, 0])
        ground = pos[:, 1] < gh
        if ground.any():
            pos[ground, 1] = gh[ground]
            vel[ground, 0] *= 1.0 - mu[ground] * 0.9
            vel[ground, 1] = np.abs(vel[ground, 1]) * 0.05
        apex = max(apex, (pos[:, 1] - gh).max())
        # anti-rocket: only grounded locomotion counts; if a target
        # exists, progress TOWARD it is signed (away = negative)
        com_x = pos[:, 0].mean()
        if (pos[:, 1] < gh + 0.15).any():
            step = com_x - prev_com
            ground_dist += (np.sign(tgt - prev_com) * step
                            if tgt is not None else abs(step))
        prev_com = com_x
        if tgt is not None:
            # dwell pays only inside a real basin around the food
            # (|target|/3): sitting at spawn or camping near the
            # OTHER target earns nothing
            dwell += max(0.0, 1.0 - abs(tgt - com_x)
                         / (abs(tgt) / 3.0))
        if record_every and t % record_every == 0:
            frames.append(pos.copy())
        if not np.isfinite(pos).all():
            break
    dist = abs(pos[:, 0].mean() - x0)
    return dict(fitness=ground_dist, dist=ground_dist, dwell=dwell,
                ballistic=dist, apex=apex, frames=frames,
                L0=L0, edges=b['edges'], body=b)


def simulate(g, steps=800, dt=0.01, record_every=0, terrain=None):
    """Legacy: fixed-format float genome -> complete-graph body."""
    from .body import decode, EDGES
    bd = decode(g)
    b = dict(pos=bd['pos'], edges=EDGES, k=bd['k'], amp=bd['amp'],
             phase=bd['phase'], mu=bd['mu'], freq=bd['freq'])
    return simulate_body(b, steps, dt, record_every, terrain)
