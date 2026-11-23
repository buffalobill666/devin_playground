"""Draw creature frames with PIL; reuse petri's make_gif."""
import numpy as np
from PIL import Image, ImageDraw

W, H, SCALE = 640, 360, 55
GROUND_Y = H - 60


def frame(pos, L0, body, camera_x):
    """pos: (N,2) world coords. body: dict with edges, k, mu."""
    EDGES = body['edges']
    N = len(pos)
    img = Image.new('RGB', (W, H), (16, 20, 28))
    dr = ImageDraw.Draw(img)

    def px(x, y):
        return (W // 2 + int((x - camera_x) * SCALE),
                GROUND_Y - int(y * SCALE))

    terr = body.get('terrain')
    if terr is None:
        dr.line([(0, GROUND_Y), (W, GROUND_Y)], fill=(70, 80, 90), width=2)
    else:
        xs = np.linspace(camera_x - W / 2 / SCALE,
                         camera_x + W / 2 / SCALE, 160)
        pts = [px(x, terr(x)) for x in xs]
        dr.line(pts, fill=(70, 80, 90), width=2)
    d = pos[EDGES[:, 0]] - pos[EDGES[:, 1]]
    L = np.hypot(d[:, 0], d[:, 1])
    strain = np.clip((L - L0) / np.maximum(L0, 1e-6), -0.5, 0.5)
    for e, (i, j) in enumerate(EDGES):
        if body['k'][e] < 0.5:
            continue
        s = strain[e]
        col = (min(255, 90 + int(300 * max(s, 0))),
               90,
               min(255, 90 + int(300 * max(-s, 0))))
        w = 1 + min(4, int(body['k'][e] / 15))
        dr.line([px(*pos[i]), px(*pos[j])], fill=col, width=w)
    for i in range(N):
        x, y = px(*pos[i])
        r = 3 + int(5 * body['mu'][i])
        c = (255, int(140 + 100 * body['mu'][i]), 60)
        dr.ellipse([x - r, y - r, x + r, y + r], fill=c)
    if body.get('target') is not None:
        tx, ty = px(body['target'],
                    (terr or (lambda x: 0))(body['target']))
        dr.polygon([(tx, ty - 26), (tx + 9, ty - 20), (tx, ty - 14)],
                   fill=(80, 255, 140))
        dr.line([(tx, ty), (tx, ty - 26)], fill=(80, 255, 140), width=2)
    return img


def render_run(sim_result, out_dir, terrain=None):
    """Save PNG sequence for a recorded simulation."""
    from pathlib import Path
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    sim_result['body']['terrain'] = terrain
    frames = sim_result['frames']
    for t, pos in enumerate(frames):
        img = frame(pos, sim_result['L0'], sim_result['body'],
                    camera_x=pos[:, 0].mean())
        img.save(out_dir / f'{t:04d}.png')
    return out_dir
