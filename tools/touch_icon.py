"""img/touch-icon.png, made once: the butterfly alone on #060607, 180 x 180, drawn by the routines of tools/og_build.py
(the same paths as the page's #fly), the whole figure fitted into the square with a margin."""
import json, os, sys
root = sys.argv[1]
sys.path.insert(0, os.path.join(root, "tools"))
import og_build as og
S = 180
og.W = og.H = S
seeds = json.load(open(os.path.join(root, "data/seeds-2021.json"), encoding="utf-8"))
marks = json.load(open(os.path.join(root, "data/wingbeats.json"), encoding="utf-8"))["wingbeats"]
N, P = og.paths(seeds, marks)
pts = [p for v in P.values() for p in v[0]]
x0, x1 = min(p[0] for p in pts), max(p[0] for p in pts); z0, z1 = min(p[1] for p in pts), max(p[1] for p in pts)
R = (1600 / 52) / (1000 / 56)   # the page draws x and z at these two scales; the icon keeps the page's proportions
k = (S - 2 * 12) / max((x1 - x0) * R, z1 - z0)
place = lambda q: [(S / 2 + (x - (x0 + x1) / 2) * k * R, S / 2 - (z - (z0 + z1) / 2) * k) for x, z in q]
buf = [float(v) for v in og.BG] * (S * S)
for n in N.values():
    if n.get("at") == "2021": og.stroke(buf, place(P[n["id"]][0]), (138, 143, 156), .30, .7)
for n in N.values():
    if n.get("at") != "2021":
        rgb = (0xe3, 0xc3, 0x4d) if n.get("by") == "human" else (0x6d, 0xbb, 0x72) if n.get("by") == "ai" else (255, 255, 255)
        og.stroke(buf, place(P[n["id"]][0]), rgb, 1.0, 1.3)
og.write_rgb(os.path.join(root, "img/touch-icon.png"), buf, "touch icon")
print("img/touch-icon.png written", round(k, 3))
