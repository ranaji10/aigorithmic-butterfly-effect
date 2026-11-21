#!/usr/bin/env python3
"""Draw the sound of the recordings that have no picture: the phone calls and the voice memos.

  python3 tools/wave_build.py ARCHIVE_CLONE SOUND_DIR [r248 r065 ...]

ARCHIVE_CLONE is a clone of the archive repository (branch main). SOUND_DIR holds its branch `audio`, checked out
somewhere else: <id>/<KKK>.webm, ten minutes each. Without ids, every recording of r/index.json that has sound and no
frames (`frames: 0`, `audio: true`) is drawn.

For each recording it writes, into the archive clone:
  r/<id>/wave.json    how loud the recording is from its start to its end: 1,200 steps, in each the loudest moment of
                      that step, 0 to 255, where 255 is the loudest moment of the whole recording (base64 of the bytes);
                      `sec` is the length of the sound itself. The page draws it on the stage and moves along it.
  r/<id>/wave.png     the same as a picture, 960 by 540, and
  r/<id>/wave.s.png   320 by 180: what a tile shows where a call shows a frame.
and it sets `"wave": 1` on the recording in r/index.json. It says so when the length of the sound and `sec` in the
index differ by more than a second; it does not change `sec` by itself.

It measures loudness and nothing else: no word and no voice can be read back from 1,200 numbers. A recording that is
listed without its sound (`audio: false`) is not drawn, because its sound is not in the archive.

Standard library only, and one outside program: ffmpeg, which reads the sound (as tools/relisten.py needs a library).
Run it again when a recording of sound alone is added or its sound is cut again; then push the archive.
"""
import array
import base64
import json
import os
import struct
import subprocess
import sys
import zlib

STEPS = 1200
RATE = 8000
GROUND, HAIR, BAR = (0x11, 0x11, 0x13), (0x2A, 0x2A, 0x30), (0xCF, 0xCB, 0xC2)  # --panel, --line-2, --soft of the page


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def samples(sound_dir, rid):
    """the whole recording as 16-bit samples, its ten-minute pieces one after another"""
    d = os.path.join(sound_dir, rid)
    pieces = sorted(f for f in os.listdir(d) if f.endswith(".webm")) if os.path.isdir(d) else []
    a = array.array("h")
    for f in pieces:
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", os.path.join(d, f), "-ac", "1", "-ar", str(RATE), "-f", "s16le", "-"],
                             stdout=subprocess.PIPE, check=True).stdout
        a.frombytes(raw[:len(raw) // 2 * 2])
    if sys.byteorder == "big":
        a.byteswap()
    return a


def peaks(a, steps=STEPS):
    n = len(a)
    out = []
    for i in range(steps):
        lo, hi = i * n // steps, max(i * n // steps + 1, (i + 1) * n // steps)
        s = a[lo:hi]
        out.append(max(max(s), -min(s)) if len(s) else 0)
    top = max(out) or 1
    return bytes(min(255, round(v * 255 / top)) for v in out)


def png(path, w, h, p):
    """bars about a middle line, as an indexed PNG of three colours"""
    pitch = 4 if w >= 900 else 2
    bw = pitch - 1
    pad = round(w * .04)
    n = (w - 2 * pad) // pitch
    mid, amp = h // 2, h * .36
    rows = [bytearray(w) for _ in range(h)]
    for x in range(pad, w - pad):
        rows[mid][x] = 1
    for i in range(n):
        lo, hi = i * len(p) // n, max(i * len(p) // n + 1, (i + 1) * len(p) // n)
        half = max(1, round(max(p[lo:hi]) / 255 * amp))
        for y in range(mid - half, mid + half):
            for x in range(pad + i * pitch, pad + i * pitch + bw):
                rows[y][x] = 2
    raw = b"".join(b"\x00" + bytes(r) for r in rows)

    def chunk(kind, data):
        c = kind + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 3, 0, 0, 0))
                + chunk(b"PLTE", bytes(GROUND + HAIR + BAR)) + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    arch, sound = sys.argv[1], sys.argv[2]
    ix_path = os.path.join(arch, "r", "index.json")
    ix = load(ix_path)
    want = set(sys.argv[3:])
    done = 0
    for r in ix["recordings"]:
        rid = r["id"]
        if want and rid not in want:
            continue
        if not want and (r.get("frames") or not r.get("audio")):
            continue
        a = samples(sound, rid)
        if not len(a):
            print("%s: no sound found in %s, left as it is" % (rid, sound))
            continue
        sec = round(len(a) / RATE, 1)
        p = peaks(a)
        d = os.path.join(arch, "r", rid)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "wave.json"), "w", encoding="utf-8") as f:
            json.dump({"id": rid, "note": "How loud this recording is from its start to its end: %d steps, in each the loudest "
                       "moment of that step, 0 to 255 (255 is the loudest moment of the whole recording), as base64. "
                       "It measures loudness and nothing else. Made by tools/wave_build.py of the site repository." % STEPS,
                       "sec": sec, "steps": STEPS, "peaks": base64.b64encode(p).decode("ascii")}, f, ensure_ascii=False, separators=(",", ":"))
        png(os.path.join(d, "wave.png"), 960, 540, p)
        png(os.path.join(d, "wave.s.png"), 320, 180, p)
        r["wave"] = 1
        done += 1
        print("%s: %s s of sound drawn%s" % (rid, sec, "" if abs(sec - r.get("sec", 0)) <= 1 else
                                              "  (the index says %s s)" % r.get("sec")))
    with open(ix_path, "w", encoding="utf-8") as f:
        json.dump(ix, f, ensure_ascii=False, separators=(",", ":"))
    print("drawn: %d" % done)


if __name__ == "__main__":
    main()
