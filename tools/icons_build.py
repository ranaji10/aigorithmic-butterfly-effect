#!/usr/bin/env python3
"""The small face of the work: the icon in a browser's tab, in bookmarks, on a phone's home screen.

Standard library only. Made once, on 20 November 2026, and kept by hand like img/og-base.png: run it again only if
the icon itself is to change.

    python3 tools/icons_build.py [repository root]

Every icon is the butterfly and nothing else: two turns of the same Lorenz path the page draws (run() in index.html
and in tools/og_build.py), one around each wing, the left in the colour of a human (--wall), the right in the colour
of an AI (--hood), on the ground of the butterfly (--pit). Each size is drawn for itself, never scaled down from a
larger one, and the larger a place is, the more of the real butterfly it shows:

    favicon.ico                16, 32 and 48 px   the two turns alone, their stroke fitted to the pixels of each size
                                                  (old browsers, Safari, anything that asks for /favicon.ico)
    img/icon.svg               any size           the same two turns as a drawing (the tab of a current browser)
    img/touch-icon.png         180 px, no corners the two turns over the thin grey paths of the 98 lines of 2021
                                                  (a phone's home screen; iOS cuts the corners itself)
    img/icon-192.png, -512.png rounded            the same (Android, a desktop shortcut), named in manifest.webmanifest
    img/icon-mask-512.png      to the edge        the same, smaller, inside the circle a phone may cut out ("maskable")

The grey paths are those of data/seeds-2021.json, which never change, so the icons never need the sweep.
"""
import json, os, struct, sys, zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import og_build as og

PIT = (6, 6, 7)            # --pit
WALL = (0xe3, 0xc3, 0x4d)  # --wall, a human
HOOD = (0x6d, 0xbb, 0x72)  # --hood, an AI
THREAD = (111, 116, 128)   # the paths of the caption machine on a canvas (as og_build.py)
R = (1600 / 52) / (1000 / 56)   # the page draws x and z at these two scales


def turns():
    """One long path on the butterfly, cut into its turns (from one lowest point to the next), each with the wing it
    goes round and how far out it reaches. The two icons' turns are the widest-reaching ones near 17.6."""
    p = og.run((1.0, 1.0, 20.0), 300)[1]
    x, y, z = p
    pts = []
    for _ in range(60000):
        dx, dy, dz = 10 * (y - x), x * (28 - z) - y, x * y - 8 / 3 * z
        x += dx * og.DT; y += dy * og.DT; z += dz * og.DT
        pts.append((x, z))
    lows = [i for i in range(1, len(pts) - 1) if pts[i][1] < pts[i - 1][1] and pts[i][1] <= pts[i + 1][1]]
    out = []
    for a, b in zip(lows, lows[1:]):
        seg = pts[a:b + 1]
        out.append((1 if sum(q[0] for q in seg) > 0 else -1, max(abs(q[0]) for q in seg), seg))
    return out


def wing(T, side, reach=17.6):
    return min((t for t in T if t[0] == side), key=lambda t: abs(t[1] - reach))[2]


def fit(paths, S, width, dy=0.0):
    """Lay the paths into an S x S square: `width` of it wide, centred on what is drawn."""
    xs = [x * R for p in paths for x, _ in p]; zs = [z for p in paths for _, z in p]
    k = S * width / (max(xs) - min(xs))
    cx, cz = (max(xs) + min(xs)) / 2, (max(zs) + min(zs)) / 2
    return lambda p: [(S / 2 + (x * R - cx) * k, S / 2 + dy * S - (z - cz) * k) for x, z in p]


def tile(S, radius):
    """How much of each pixel lies inside a square with rounded corners (1 = all of it)."""
    a = [1.0] * (S * S)
    if radius <= 0:
        return a
    for y in range(S):
        for x in range(S):
            cx = min(max(x + .5, radius), S - radius); cy = min(max(y + .5, radius), S - radius)
            d = ((x + .5 - cx) ** 2 + (y + .5 - cy) ** 2) ** .5
            a[y * S + x] = max(0.0, min(1.0, radius + .5 - d))
    return a


def draw(S, L, Rt, threads=(), width=.84, stroke=None, radius=0.0, thread_w=None, dy=0.0):
    og.W = og.H = S
    place = fit([L, Rt], S, width, dy)
    buf = [float(v) for v in PIT] * (S * S)
    for t in threads:
        og.stroke(buf, place(t), THREAD, .34, thread_w or max(.6, S / 260))
    w = stroke or S / 13
    og.stroke(buf, place(L), WALL, 1.0, w)
    og.stroke(buf, place(Rt), HOOD, 1.0, w)
    return buf, tile(S, radius * S)


def png(S, buf, alpha, note):
    def chunk(kind, body):
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body) & 0xFFFFFFFF)
    solid = all(a >= 1 for a in alpha)
    px = bytearray()
    for y in range(S):
        px.append(0)
        for x in range(S):
            i = y * S + x
            px += bytes(max(0, min(255, int(v + .5))) for v in buf[i * 3:i * 3 + 3])
            if not solid:
                px.append(max(0, min(255, int(alpha[i] * 255 + .5))))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", S, S, 8, 2 if solid else 6, 0, 0, 0))
            + chunk(b"tEXt", b"abe\x00" + note.encode()) + chunk(b"IDAT", zlib.compress(bytes(px), 9)) + chunk(b"IEND", b""))


def ico(images):
    """An .ico whose pictures are PNGs (every browser since 2010 reads these)."""
    head = struct.pack("<HHH", 0, 1, len(images))
    off, table, body = 6 + 16 * len(images), b"", b""
    for S, data in images:
        table += struct.pack("<BBBBHHII", S % 256, S % 256, 0, 0, 1, 32, len(data), off)
        off += len(data); body += data
    return head + table + body


def svg(L, Rt):
    """The two turns as a drawing, 64 units square; the stroke is 7.5% of the side, as at 32 px."""
    S = 64
    place = fit([L, Rt], S, .80)
    def d(p):
        q = place(p)
        q = q[::3] + ([q[-1]] if (len(q) - 1) % 3 else [])
        return "M" + " ".join("%.1f %.1f" % xy for xy in q)
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
            '<title>AIgorithmic Butterfly Effect</title>'
            '<rect width="64" height="64" rx="12" fill="#060607"/>'
            '<g fill="none" stroke-width="4.8" stroke-linecap="round" stroke-linejoin="round">'
            '<path stroke="#e3c34d" d="%s"/><path stroke="#6dbb72" d="%s"/></g></svg>\n' % (d(L), d(Rt)))


def build(root="."):
    T = turns()
    L, Rt = wing(T, -1), wing(T, 1)
    seeds = json.load(open(os.path.join(root, "data/seeds-2021.json"), encoding="utf-8"))
    N, P = og.paths(seeds, [])
    threads = [P[n["id"]][0] for n in N.values()]
    out = {}
    # the tab: the two turns alone. Stroke: 1.5 px at 16 (thinner breaks up), 2.5 at 32, 3.4 at 48
    small = [(16, 1.5, .83, .16), (32, 2.5, .84, .19), (48, 3.4, .82, .19)]
    out["favicon.ico"] = ico([(S, png(S, *draw(S, L, Rt, width=wd, stroke=w, radius=r), "icon %d" % S)) for S, w, wd, r in small])
    out["img/icon.svg"] = svg(L, Rt).encode()
    # a home screen: the two turns over the lines of 2021
    out["img/touch-icon.png"] = png(180, *draw(180, L, Rt, threads, width=.78, stroke=9.0), "touch icon")
    out["img/icon-192.png"] = png(192, *draw(192, L, Rt, threads, width=.80, stroke=9.6, radius=.19), "icon 192")
    out["img/icon-512.png"] = png(512, *draw(512, L, Rt, threads, width=.80, stroke=24.0, radius=.19), "icon 512")
    out["img/icon-mask-512.png"] = png(512, *draw(512, L, Rt, threads, width=.60, stroke=18.0), "icon maskable")
    for name, data in out.items():
        with open(os.path.join(root, name), "wb") as f:
            f.write(data)
        print("%-24s %6d bytes" % (name, len(data)))


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else ".")
