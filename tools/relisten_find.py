#!/usr/bin/env python3
"""Step 1 of listening again: find the parts of the 2026 transcripts that carry no meaning.

Standard library only.   python3 tools/relisten_find.py ARCHIVE_CLONE [OUT.json]

The first hearing (r/<id>/voice.json) was made by a very small speech model that knows only English. Where people spoke
Hindi or Bengali, or mixed them with English, or where there was music, it wrote English-looking words anyway. This reads
every heard segment [start s, end s, text] and marks the ones that look like that, by four signs:
  loop     the same word or group of words again and again
  rate     far more words than a mouth can say in the time, or a long stretch with next to nothing
  strange  word pairs that occur nowhere else in the 80,000 segments (the transcripts themselves are the yardstick:
           most of what was said is English, so English that was really said shares its word pairs with other segments)
  rare     many words that occur almost nowhere else
A marked segment drags in its minute when most of that minute is marked. Marked segments close together become one
window. Writes {recording: [[start s, end s, [signs]], ...]} for tools/relisten.py to hear again.
"""
import collections, glob, json, math, os, re, sys, zlib
ARCH = sys.argv[1]; OUT = sys.argv[2] if len(sys.argv) > 2 else 'relisten_plan.json'
tok = lambda t: re.findall(r"[a-z']+", t.lower())
recs = {}
for p in sorted(glob.glob(os.path.join(ARCH, 'r', 'r*', 'voice.json'))):
    v = json.load(open(p, encoding='utf-8'))
    if v.get('segs'): recs[v['id']] = v['segs']
uni = collections.Counter(); bi = collections.Counter()
for segs in recs.values():
    for s in segs:
        w = tok(s[2]); uni.update(w); bi.update(zip(w, w[1:]))

def signs(s):
    t = s[2]; w = tok(t); d = max(0.2, s[1] - s[0]); out = []
    n = len(w)
    if n >= 6:
        run = best = 1
        for a, b in zip(w, w[1:]):
            run = run + 1 if a == b else 1; best = max(best, run)
        grams = collections.Counter(tuple(w[i:i + k]) for k in (2, 3, 4) for i in range(n - k + 1))
        rep = max([c * len(g) for g, c in grams.items() if c >= 3] or [0])
        if best >= 4 or rep >= 0.5 * n or (len(t) >= 80 and len(zlib.compress(t.encode())) / len(t) < 0.38): out.append('loop')
    if n / d > 5.2 and n >= 8: out.append('rate')
    if d >= 8 and n <= 2: out.append('rate')
    if n >= 5:
        pairs = list(zip(w, w[1:])); lone = sum(1 for p in pairs if bi[p] <= 1) / len(pairs)
        rare = sum(1 for x in w if uni[x] <= 2) / n
        if lone >= 0.55: out.append('strange')
        if rare >= 0.25: out.append('rare')
    return out

plan = {}; stats = collections.Counter(); secs = 0.0; examples = collections.defaultdict(list)
for rid, segs in recs.items():
    marks = [signs(s) for s in segs]
    # a minute that is mostly marked is marked whole
    by_min = collections.defaultdict(list)
    for i, s in enumerate(segs): by_min[int(s[0] // 60)].append(i)
    for m, idxs in by_min.items():
        dur = sum(segs[i][1] - segs[i][0] for i in idxs); bad = sum(segs[i][1] - segs[i][0] for i in idxs if marks[i])
        if len(idxs) >= 3 and bad >= 0.5 * dur:
            for i in idxs:
                if not marks[i]: marks[i] = ['minute']
    wins = []
    for s, mk in zip(segs, marks):
        if not mk: continue
        for k in mk: stats[k] += 1
        if len(examples[mk[0]]) < 400: examples[mk[0]].append((rid, s[0], s[2]))
        if wins and s[0] - wins[-1][1] <= 12: wins[-1][1] = s[1]; wins[-1][2] = sorted(set(wins[-1][2]) | set(mk))
        else: wins.append([s[0], s[1], list(mk)])
    if wins:
        plan[rid] = [[round(max(0, a - 1.0), 1), round(b + 1.0, 1), k] for a, b, k in wins]; secs += sum(b - a + 2 for a, b, k in wins)
json.dump({'note': 'Parts of the first hearing that carry no meaning, to be heard again (tools/relisten_find.py). recording: [[start s, end s, signs]]',
           'plan': plan}, open(OUT, 'w'), separators=(',', ':'))
total = sum(s[1] - s[0] for segs in recs.values() for s in segs)
print('%d recordings, %d segments, %.1f h heard' % (len(recs), sum(map(len, recs.values())), total / 3600))
print('marked: %d windows in %d recordings, %.1f h' % (sum(map(len, plan.values())), len(plan), secs / 3600), dict(stats))
if os.environ.get('SHOW'):
    import random; random.seed(int(os.environ['SHOW']))
    for k, L in examples.items():
        print('--', k)
        for e in random.sample(L, min(9, len(L))): print('  ', e[0], int(e[1]), '|', e[2][:170])
