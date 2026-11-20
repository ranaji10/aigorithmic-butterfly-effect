#!/usr/bin/env python3
"""The picture other programs show beside a link to the work (og:image): the butterfly as it is now.

Standard library only. It draws what drawFly() in index.html draws (one thin path for each line of 2021, a thicker
one for each mark), 1200 x 630, and lays img/og-base.png over it (the ground under the words, the two years, the
name, one sentence: made once, kept by hand). Called by `wingbeat.py build`; it writes data/og.png only when the
lines, the marks or the base have changed, so a sweep that finds nothing changes nothing.

    python3 tools/og_build.py [repository root]
"""
import hashlib, json, os, struct, sys, zlib

W, H = 1200, 630
BG = (6, 6, 7)                       # #060607, the ground of the butterfly on the page
K, OX, OY = 990 / 1600, 105.0, -86.0  # the page's 1600 x 1000 drawing, laid 990 wide and centred, its top above the edge
STEPS, DT = 520, .006


def fnv(s):
    """hash() of index.html: FNV-1a over UTF-16 code units."""
    h = 2166136261
    b = s.encode("utf-16-le")
    for i in range(0, len(b), 2):
        h ^= b[i] | b[i + 1] << 8
        h = h * 16777619 & 0xFFFFFFFF
    return h


def run(p, n):
    """run() of index.html: n steps of the Lorenz equations; the points (x, z) and where it ended."""
    x, y, z = p
    out = []
    for _ in range(n):
        dx, dy, dz = 10 * (y - x), x * (28 - z) - y, x * y - 8 / 3 * z
        x += dx * DT; y += dy * DT; z += dz * DT
        out.append((x, z))
    return out, (x, y, z)


def paths(seeds, marks):
    """buildFly() of index.html."""
    N = {s["id"]: {"id": s["id"], "hears": None, "text": s.get("text"), "at": "2021"} for s in seeds}
    for w in marks:
        N[w["id"]] = w
    P = {}
    for n in sorted(N.values(), key=lambda n: (0 if n.get("at") == "2021" else 1, n["id"])):
        h = fnv(n["id"] + (n.get("text") or "") + (n.get("mark") or "") + (n.get("form") or ""))
        par = P.get(n.get("hears")) if n.get("hears") else None
        if not par:
            st = (((h & 1023) / 1023 - .5) * 24, ((h >> 10 & 1023) / 1023 - .5) * 24, 8 + (h >> 20 & 1023) / 1023 * 30)
            st = run(st, 300)[1]
        else:
            e = par[1]
            st = (e[0] + ((h & 255) - 128) / 4e3, e[1] + ((h >> 8 & 255) - 128) / 4e3, e[2] + ((h >> 16 & 255) - 128) / 4e3)
        P[n["id"]] = run(st, STEPS if n.get("at") == "2021" else STEPS * 2)
    return N, P


def stroke(buf, pts, rgb, alpha, width):
    """One path as one stroke: each pixel takes the path's greatest cover once, as a canvas does."""
    cover = {}
    half, top = width / 2, min(1.0, width)
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        dx, dy = x1 - x0, y1 - y0
        L2 = dx * dx + dy * dy
        for py in range(max(0, int(min(y0, y1) - half - 1)), min(H - 1, int(max(y0, y1) + half + 2)) + 1):
            for px in range(max(0, int(min(x0, x1) - half - 1)), min(W - 1, int(max(x0, x1) + half + 2)) + 1):
                cx, cy = px + .5 - x0, py + .5 - y0
                t = 0 if not L2 else max(0.0, min(1.0, (cx * dx + cy * dy) / L2))
                ex, ey = cx - t * dx, cy - t * dy
                c = half + .5 - (ex * ex + ey * ey) ** .5
                if c > 0:
                    c = min(top, c); k = py * W + px
                    if c > cover.get(k, 0):
                        cover[k] = c
    for k, c in cover.items():
        a = c * alpha; i = k * 3
        buf[i] += (rgb[0] - buf[i]) * a; buf[i + 1] += (rgb[1] - buf[i + 1]) * a; buf[i + 2] += (rgb[2] - buf[i + 2]) * a


def chunks(data):
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG")
    i = 8
    while i < len(data):
        n, kind = struct.unpack(">I4s", data[i:i + 8])
        yield kind, data[i + 8:i + 8 + n]
        i += 12 + n


def read_rgba(data):
    """An 8-bit RGBA PNG without interlace, as rows of bytes. Nothing else is needed for the base."""
    raw, head = b"", None
    for kind, body in chunks(data):
        if kind == b"IHDR": head = struct.unpack(">IIBBBBB", body)
        elif kind == b"IDAT": raw += body
    w, h, depth, colour, _, _, lace = head
    if (w, h, depth, colour, lace) != (W, H, 8, 6, 0):
        raise ValueError("img/og-base.png must be %d x %d, 8-bit RGBA, not interlaced" % (W, H))
    raw, rows, prev, n = zlib.decompress(raw), [], bytearray(w * 4), w * 4
    for y in range(h):
        f, row = raw[y * (n + 1)], bytearray(raw[y * (n + 1) + 1:(y + 1) * (n + 1)])
        for i in range(n):
            a = row[i - 4] if i >= 4 else 0; b = prev[i]; c = prev[i - 4] if i >= 4 else 0
            if f == 1: row[i] = row[i] + a & 255
            elif f == 2: row[i] = row[i] + b & 255
            elif f == 3: row[i] = row[i] + (a + b >> 1) & 255
            elif f == 4:
                p = a + b - c; pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                row[i] = row[i] + (a if pa <= pb and pa <= pc else b if pb <= pc else c) & 255
        rows.append(row); prev = row
    return rows


def write_rgb(path, buf, note):
    def chunk(kind, body):
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body) & 0xFFFFFFFF)
    px = bytes(max(0, min(255, int(v + .5))) for v in buf)
    raw = b"".join(b"\x00" + px[y * W * 3:(y + 1) * W * 3] for y in range(H))
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
                + chunk(b"tEXt", b"abe\x00" + note.encode()) + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def build(root="."):
    j = lambda p: json.load(open(os.path.join(root, p), encoding="utf-8"))
    seeds, marks = j("data/seeds-2021.json"), j("data/wingbeats.json")["wingbeats"]
    base = open(os.path.join(root, "img/og-base.png"), "rb").read()
    out = os.path.join(root, "data/og.png")
    what = [[n.get(k) for k in ("id", "hears", "text", "mark", "form", "by", "at")] for n in list(seeds) + list(marks)]
    note = hashlib.sha1(json.dumps(what, sort_keys=True).encode() + base + b"v1").hexdigest()
    try:
        if any(kind == b"tEXt" and body == b"abe\x00" + note.encode() for kind, body in chunks(open(out, "rb").read())):
            return False  # nothing it is drawn from has changed
    except (OSError, ValueError, struct.error):
        pass
    N, P = paths(seeds, marks)
    buf = [float(v) for v in BG] * (W * H)
    # the page maps a point to (W/2 + x*sx, H - 3*sy - z*sy) on 1600 x 1000; here the same, scaled and moved
    place = lambda pts: [(OX + K * (800 + x * 1600 / 52), OY + K * (1000 - 3 * 1000 / 56 - z * 1000 / 56)) for x, z in pts]
    for n in N.values():   # as drawFly(): the lines of 2021 first, thin; then every mark, thicker, in its speaker's colour
        if n.get("at") == "2021":
            stroke(buf, place(P[n["id"]][0]), (111, 116, 128), .34, 1 * K)
    for n in N.values():
        if n.get("at") != "2021":
            rgb = (0xe3, 0xc3, 0x4d) if n.get("by") == "human" else (0x6d, 0xbb, 0x72) if n.get("by") == "ai" else (255, 255, 255)
            stroke(buf, place(P[n["id"]][0]), rgb, 1.0, 2 * K)
    for y, row in enumerate(read_rgba(base)):   # the words and their ground, over the drawing
        for x in range(W):
            a = row[x * 4 + 3]
            if a:
                i, a = (y * W + x) * 3, a / 255
                buf[i] += (row[x * 4] - buf[i]) * a; buf[i + 1] += (row[x * 4 + 1] - buf[i + 1]) * a; buf[i + 2] += (row[x * 4 + 2] - buf[i + 2]) * a
    write_rgb(out, buf, note)
    return True


if __name__ == "__main__":
    print("data/og.png", "written" if build(sys.argv[1] if len(sys.argv) > 1 else ".") else "unchanged")
