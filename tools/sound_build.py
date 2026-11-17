#!/usr/bin/env python3
"""Find, for every screenshot of the call, the moment of the recording it was taken at, so that the site can play the
sound of that moment under the picture instead of having a machine read the caption aloud.

    python3 tools/sound_build.py <folder of the archive repository>      writes <archive>/i/sound.json

Standard library only. It compares two machines' hearings of the same speech: the captions the 2021 caption machine
wrote (read off the screenshots, i/text.json) and what the small speech model made of the recordings in 2026
(r/<id>/voice.json). Both mishear, differently, but a run of a few shared words in the same order is rare enough to
find the place. A match is kept only if enough of the caption is found there, and if it agrees with its neighbours
in the document (screenshots were pasted more or less in the order they were taken) or is very strong by itself.

What is written, per picture number:  [recording, start s, end s, [[word, s], ...]]
  start/end: the stretch of the recording in which the words on the screenshot are spoken;
  the pairs say at which second the caption has reached which of its words (words as split at spaces), so that the
  page can light the words up as they are heard.
The same for the 98 lines of 2021 (data/seeds-2021.json), whose words are an excerpt of their screenshot's caption.
"""
import collections
import datetime
import difflib
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORD = re.compile(r"[a-z']+")
RATE = 2.6            # words a second, for the stretches of a caption that found no partner


def toks(s):
    return WORD.findall(s.lower().replace('’', "'"))


def main(arch):
    tx = json.load(open(os.path.join(arch, 'i/text.json'), encoding='utf-8'))['text']
    ix = json.load(open(os.path.join(arch, 'i/index.json'), encoding='utf-8'))['images']
    recs = json.load(open(os.path.join(arch, 'r/index.json'), encoding='utf-8'))['recordings']
    seeds = json.load(open(os.path.join(HERE, 'data/seeds-2021.json'), encoding='utf-8'))
    recw, aud = {}, {}
    for r in recs:
        if r['kind'] != 'call' or not r.get('aud'):
            continue
        v = json.load(open(os.path.join(arch, 'r', r['id'], 'voice.json'), encoding='utf-8'))
        ws = []
        for s, e, t in v['segs']:
            tk = toks(t)
            for i, w in enumerate(tk):
                ws.append((s + (e - s) * i / max(1, len(tk)), w))
        ws.append((ws[-1][0] + 1 if ws else 0, ''))
        recw[r['id']] = ws
        aud[r['id']] = (set(r['aud']), r['sec'])
    idx = collections.defaultdict(list)
    for rid, ws in recw.items():
        for i in range(len(ws) - 1):
            idx[ws[i][1] + ' ' + ws[i + 1][1]].append((rid, i))
    total = sum(len(v) for v in idx.values())

    def align(tk, rid, a, z):
        """Best run of the caption's words inside words a..z of a recording: (matched, [(caption index, word index), ...])."""
        ws = recw[rid]
        a, z = max(0, a), min(len(ws), z)
        sm = difflib.SequenceMatcher(None, tk, [w for _, w in ws[a:z]], autojunk=False)
        bl = [m for m in sm.get_matching_blocks() if m.size >= 2]
        # keep the blocks that lie on one line through the recording: a caption is some seconds long, not minutes
        if not bl:
            return 0, []
        core = max(bl, key=lambda m: m.size)
        bl = [m for m in bl if abs((m.b - m.a) - (core.b - core.a)) <= 25]
        return sum(m.size for m in bl), [(m.a, a + m.b, m.size) for m in bl]

    def search(tk):
        votes = collections.Counter()
        for i in range(len(tk) - 1):
            h = idx.get(tk[i] + ' ' + tk[i + 1])
            if not h or len(h) > 400:
                continue
            w = math.log(total / len(h))
            for rid, j in h:
                votes[(rid, (j - i) // 40)] += w
        best = (0, None, [])
        for (rid, b), _ in votes.most_common(4):
            m, bl = align(tk, rid, b * 40 - 40, b * 40 + len(tk) + 80)
            if m > best[0]:
                best = (m, rid, bl)
        return best

    def entry(text, rid, bl):
        """Turn matched runs into [rid, start, end, [[word index at spaces, second], ...]]."""
        ws = recw[rid]
        words = text.split()
        of = []                                   # caption-token index -> index of the word (split at spaces) it sits in
        for wi, w in enumerate(words):
            of += [wi] * len(toks(w))
        n = len(of)
        pts = []
        for a, b, size in bl:
            pts.append((a, ws[b][0]))
            pts.append((a + size - 1, ws[b + size - 1][0]))
        pts.sort()
        mono = []
        for a, t in pts:                           # time must not run backwards
            if not mono or (a > mono[-1][0] and t >= mono[-1][1]):
                mono.append((a, t))
        a0, t0 = mono[0]
        a1, t1 = mono[-1]
        start = max(0.0, t0 - min(a0 / RATE, 8.0))
        end = t1 + min((n - 1 - a1) / RATE, 6.0) + 0.4
        anchors = [[0, round(start, 1)]] + [[of[a] if a < n else len(words), round(t, 1)] for a, t in mono] + [[len(words), round(end, 1)]]
        out = []
        for w, t in anchors:
            if not out or (w >= out[-1][0] and t >= out[-1][1]):
                if out and w == out[-1][0]:
                    continue
                out.append([w, t])
        if out[-1][0] != len(words):
            out.append([len(words), round(end, 1)])
        return [rid, round(start, 1), round(end, 1), out]

    def has_sound(rid, a, b):
        hours, sec = aud[rid]
        return b <= sec + 2 and all(h in hours for h in range(int(a // 3600), int(b // 3600) + 1))

    pics = sorted(k for k in tx if ix.get(str(int(k[1:])), [0, 0, '?'])[2] == 'd')
    first = {}
    for k in pics:
        tk = toks(tx[k])
        if len(tk) < 6:
            continue
        m, rid, bl = search(tk)
        if rid:
            first[k] = (m, len(tk), rid, bl)
    strong = lambda v: v[0] >= 6 and v[0] / v[1] >= 0.4
    good = [k for k in pics if k in first and strong(first[k])]
    when = lambda k: recw[first[k][2]][first[k][3][0][1]][0]
    kept = {}
    for i, k in enumerate(good):                   # agree with a neighbour in the document, or be very strong alone
        near = [g for g in good[max(0, i - 3):i] + good[i + 1:i + 4] if first[g][2] == first[k][2] and abs(when(g) - when(k)) < 2400]
        if near or (first[k][0] >= 12 and first[k][0] / first[k][1] >= 0.7):
            kept[k] = first[k]
    # second look: a picture that found nothing sure, between two that did, is searched for only between them
    order = sorted(kept)
    import bisect
    second = 0
    for k in pics:
        if k in kept:
            continue
        tk = toks(tx[k])
        if len(tk) < 5:
            continue
        i = bisect.bisect(order, k)
        nb = [order[j] for j in (i - 1, i) if 0 <= j < len(order)]
        best = (0, None, [])
        for g in nb:
            rid = kept[g][2]
            j = kept[g][3][0][1]
            m, bl = align(tk, rid, j - 900, j + 900)          # about five minutes either side
            if m > best[0]:
                best = (m, rid, bl)
        if best[1] and best[0] >= 4 and best[0] / len(tk) >= 0.34:
            kept[k] = (best[0], len(tk), best[1], best[2])
            second += 1
    at = {}
    for k, (m, n, rid, bl) in sorted(kept.items()):
        e = entry(tx[k], rid, bl)
        if e[2] - e[1] < 1.5 or e[2] - e[1] > 75 or not has_sound(rid, e[1], e[2]):
            continue
        at[str(int(k[1:]))] = e
    lines = {}
    for s in seeds:
        k = 'm%05d' % s.get('shot', 0)
        if k not in kept or not s.get('text'):
            continue
        rid = kept[k][2]
        j = kept[k][3][0][1]
        tk = toks(s['text'])
        m, bl = align(tk, rid, j - 200, j + 300)
        if m >= 4 and m / max(1, len(tk)) >= 0.4:
            e = entry(s['text'], rid, bl)
            if 1.5 <= e[2] - e[1] <= 75 and has_sound(rid, e[1], e[2]):
                lines[s['id']] = e
    out = {
        'note': ('Where in the recordings each screenshot of the call was taken, found by comparing two hearings of the same speech: the captions '
                 'of 2021 (i/text.json) and the small speech model of 2026 (r/<id>/voice.json). n: [recording, start s, end s, [[word, s], ...]]: '
                 'the stretch in which the words on the picture are spoken, and at which second the caption has reached which of its words '
                 '(words as split at spaces). "lines": the same for the lines of 2021. Made by tools/sound_build.py in the main repository. '
                 'A picture that is not listed was not found, or was not found surely enough; nothing is played for it.'),
        'built': datetime.date.today().isoformat(),
        'at': at, 'lines': lines}
    json.dump(out, open(os.path.join(arch, 'i/sound.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print('screenshots of the document with words: %d; first look sure: %d; kept after neighbours: %d; second look: +%d; written: %d pictures, %d lines'
          % (len(first), len(good), len(kept) - second, second, len(at), len(lines)))


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(sys.argv[1])
