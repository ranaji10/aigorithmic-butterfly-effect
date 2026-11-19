#!/usr/bin/env python3
"""A second plan for listening again: every stretch of speech the model that knows Hindi and Bengali has not heard yet.

Standard library only.   python3 tools/relisten_sweep.py ARCHIVE_CLONE [OUT.json]

tools/relisten_find.py marked only the parts of the first hearing that carried no meaning (18 of 92 hours of speech on
18 November 2026). But a very small English-only model also turns Hindi and Bengali into sentences that look like
English, and those were never marked. This lists all the rest: the speech of every recording, outside the windows of the
first plan (relisten/plan.json) and outside what was already heard as Hindi or Bengali ("lang" in voice.json), as windows
of at most four minutes with the sign "sweep". tools/relisten.py asks the model which language each piece of such a window
is in and writes down only the pieces in Hindi or Bengali; English is left as the first hearing has it.
Writes {"plan": {recording: [[start s, end s, ["sweep"]], ...]}} (by default to ARCHIVE_CLONE/relisten/plan2.json).
"""
import glob, json, os, sys
ARCH = sys.argv[1]; OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ARCH, 'relisten', 'plan2.json')
first = json.load(open(os.path.join(ARCH, 'relisten', 'plan.json'), encoding='utf-8')).get('plan', {})
plan = {}; total = 0.0
for p in sorted(glob.glob(os.path.join(ARCH, 'r', 'r*', 'voice.json'))):
    v = json.load(open(p, encoding='utf-8')); rid = v['id']
    done = [(a, b) for a, b, _ in first.get(rid, [])] + [(a, b) for a, b, _ in v.get('lang', [])]
    segs = sorted(s for s in v.get('segs', []) if not any(a <= (s[0] + s[1]) / 2 < b for a, b in done))
    wins = []
    for s in segs:
        a, b = max(0.0, s[0] - 0.3), s[1] + 0.3
        if wins and a - wins[-1][1] <= 6 and b - wins[-1][0] <= 240: wins[-1][1] = max(wins[-1][1], b)
        else: wins.append([a, b])
    wins = [[round(a, 1), round(b, 1), ['sweep']] for a, b in wins if b - a >= 1.5]
    if wins: plan[rid] = wins; total += sum(b - a for a, b, _ in wins)
json.dump({'note': 'Speech not yet heard by the model that knows Hindi and Bengali (tools/relisten_sweep.py). recording: [[start s, end s, ["sweep"]]]. Only pieces heard as Hindi or Bengali are written down.', 'plan': plan},
          open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print('%d recordings, %d windows, %.1f hours' % (len(plan), sum(len(w) for w in plan.values()), total / 3600))
