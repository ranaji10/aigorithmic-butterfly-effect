#!/usr/bin/env python3
"""Last step of listening again: put the second hearing into r/<id>/voice.json where the first one carried no meaning.

Standard library only.
  python3 tools/relisten_merge.py ARCHIVE_CLONE HEARD_DIR [PRIVATE_NAMES.txt] [--dry]

HEARD_DIR holds what the workflow "listen again" wrote (branch "relisten" of the archive repository: heard/<id>.json).
For every piece of sound that was heard again (at most 28 seconds):
  - heard as Hindi or Bengali: what the first, English-only hearing wrote there is replaced;
  - heard as English: replaced only if the first hearing was marked there (a loop, too many words, word pairs found
    nowhere else); where the second hearing hears no speech at all, a loop of the first is taken out and nothing put in;
  - otherwise the first hearing stays.
A piece from the sweep (tools/relisten_sweep.py) heard as Hindi or Bengali is taken only where the model was sure of the
language; one it skipped as English is left alone; a recording never heard before (sign "new") is taken whole.
A line of the second hearing that is itself a loop, or that the model was unsure was speech, is not taken.
Taken out of every new line before it is written: links, mail addresses, handles, runs of seven or more digits, and
the words listed in PRIVATE_NAMES.txt (surnames; one per line; a file on the author's drive, never in a repository).
Minutes that are hidden (data/veiled.json) get no new words. "segs" keeps its three-part rows; which language a
stretch was heard in stands beside it as "lang": [[start s, end s, "hi" | "bn"]].
A line that spells out an address ("something dot com") or holds one runaway token of more than 40 letters is not taken.
PRIVATE_NAMES.txt cannot know every surname a model will write down. So after this, and before anything is pushed, run
the scrub the author keeps beside that file (relisten_scrub.py: it takes out the capitalised word after a first name,
and prints what is left for a person to read). On 18 November 2026 the second hearing wrote about ninety surnames.
Afterwards: tools/sound_build.py, tools/themes_build.py, and commit the archive.
"""
import collections, glob, json, os, re, sys, zlib
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
args = [a for a in sys.argv[1:] if not a.startswith('--')]; DRY = '--dry' in sys.argv
ARCH, HEARD = args[0], args[1]
NAMES = [l.strip() for l in open(args[2], encoding='utf-8')] if len(args) > 2 else []
NAMES = [n for n in NAMES if len(n) >= 3]
NAME_RE = re.compile(r'\b(' + '|'.join(re.escape(n) for n in sorted(NAMES, key=len, reverse=True)) + r')\b', re.I) if NAMES else None
veiled = json.load(open(os.path.join(ROOT, 'data', 'veiled.json'), encoding='utf-8')).get('ids', {})
tok = lambda t: re.findall(r"[a-z']+", t.lower())
uni = collections.Counter(); bi = collections.Counter(); voices = {}
for p in sorted(glob.glob(os.path.join(ARCH, 'r', 'r*', 'voice.json'))):
    v = json.load(open(p, encoding='utf-8')); voices[v['id']] = v
    for s in v.get('segs', []):
        w = tok(s[2]); uni.update(w); bi.update(zip(w, w[1:]))


def loop(t):
    w = tok(t); n = len(w)
    if n < 6: return False
    run = best = 1
    for a, b in zip(w, w[1:]):
        run = run + 1 if a == b else 1; best = max(best, run)
    grams = collections.Counter(tuple(w[i:i + k]) for k in (1, 2, 3, 4) for i in range(n - k + 1))
    rep = max([c * len(g) for g, c in grams.items() if c >= 3 and (len(g) > 1 or c >= 5)] or [0])
    return best >= 4 or rep >= 0.5 * n or (len(t) >= 80 and len(zlib.compress(t.encode())) / len(t) < 0.38)


def marked(s):
    t = s[2]; w = tok(t); n = len(w); d = max(0.2, s[1] - s[0])
    if loop(t) or (n / d > 5.2 and n >= 8) or (d >= 8 and n <= 2): return True
    if n >= 5:
        pairs = list(zip(w, w[1:]))
        if sum(1 for p in pairs if bi[p] <= 1) / len(pairs) >= 0.55 or sum(1 for x in w if uni[x] <= 2) / n >= 0.25: return True
    return False


SPELT = re.compile(r'\b(?:dot|slash)\s+(?:com|dev|io|org|net|in|cz|co)\b|\b[\w-]+\.(?:io|com|org|net|dev|cz)\b', re.I)


def clean(t):
    if SPELT.search(t) or any(len(w) > 40 for w in t.split()): return ''
    t = re.sub(r'\b(?:https?://|www\.)\S+|\b\S+@\S+\.\S+|(?<!\w)@\w{2,}', '[link]', t)
    t = re.sub(r'(?:\d[\s().-]?){7,}', ' ', t)
    if NAME_RE: t = NAME_RE.sub('', t)
    return re.sub(r'\s+([,.?!])', r'\1', re.sub(r'\s{2,}', ' ', t)).strip()


tally = collections.Counter(); secs = collections.Counter(); touched = []
for f in sorted(glob.glob(os.path.join(HEARD, 'r*.json'))):
    h = json.load(open(f, encoding='utf-8')); rid = h['id']; v = voices.get(rid)
    if not v or not h.get('windows'): continue
    old = v['segs']; drop = set(); new = []; lang = []
    for w in h['windows'].values():
        fresh = 'new' in (w.get('signs') or [])       # a recording that was never heard: everything the model wrote is taken
        for c in w['chunks']:
            a, b = c['s'], c['e']; tally['pieces'] += 1; secs[c['lang']] += b - a; tally['heard ' + c['lang']] += 1
            if c.get('skipped'): tally['sweep: English, left alone'] += 1; continue
            # a sweep replaces English that may well be right: it is believed only where the model was sure of the language
            # (at least an even chance, and twice as likely as English). On 19 Nov 2026 a piece heard as "Hindi" at 42% against
            # 42% English was an English sentence, written down correctly by the first hearing and garbled by the second.
            if 'sweep' in (w.get('signs') or []) and c['lang'] in ('hi', 'bn') and not (c['p'].get(c['lang'], 0) >= 0.5 and c['p'].get(c['lang'], 0) >= 2 * c['p'].get('en', 0)):
                tally['sweep: language not sure enough, left alone'] += 1; continue
            if any(veiled.get('%s.%04d' % (rid, m)) for m in range(int(a // 60), int(b // 60) + 1)) or veiled.get(rid): tally['hidden, left alone'] += 1; continue
            inside = [i for i, s in enumerate(old) if a <= (s[0] + s[1]) / 2 < b]
            good = [[r[0], r[1], clean(r[2])] for r in c['segs'] if not loop(r[2]) and not (r[4] > 0.8 and r[3] < -0.6) and r[3] > -1.3]
            good = [g for g in good if len(g[2]) > 1]
            bad_old = [i for i in inside if marked(old[i])]
            if fresh:
                if good:
                    drop.update(inside); new += good; tally['new recording: ' + c['lang']] += 1
                    if c['lang'] in ('hi', 'bn'): lang.append([round(a, 1), round(b, 1), c['lang']])
            elif c['lang'] in ('hi', 'bn'):
                if good: drop.update(inside); new += good; lang.append([round(a, 1), round(b, 1), c['lang']]); tally['replaced: ' + c['lang']] += 1
                elif bad_old and all(loop(old[i][2]) for i in bad_old): drop.update(bad_old); tally['loop taken out, nothing heard'] += 1
                else: tally['kept the first hearing'] += 1
            elif bad_old:
                if good: drop.update(inside); new += good; tally['replaced: en'] += 1
                elif not c['segs'] and any(loop(old[i][2]) for i in bad_old): drop.update(i for i in bad_old if loop(old[i][2])); tally['loop taken out, nothing heard'] += 1
                else: tally['kept the first hearing'] += 1
            else: tally['kept the first hearing'] += 1
    if not drop and not new: continue
    segs = sorted([s for i, s in enumerate(old) if i not in drop] + new, key=lambda s: (s[0], s[1]))
    lang = sorted([list(l) for l in v.get('lang', []) if not any(l[0] < n[1] and n[0] < l[1] for n in lang)] + lang); merged = []   # what an earlier merge heard as Hindi or Bengali stays
    for l in lang:
        if merged and merged[-1][2] == l[2] and l[0] - merged[-1][1] <= 1.0: merged[-1][1] = l[1]
        else: merged.append(list(l))
    v['segs'] = segs; v['lang'] = merged
    if not v.get('model') or v.get('model') == h.get('model'):     # heard for the first time, by the larger model alone
        v['model'] = h.get('model', ''); v['heard_hours'] = list(range(v.get('of_hours') or 1))
        touched.append(rid); tally['lines out'] += len(drop); tally['lines in'] += len(new)
        if not DRY: json.dump(v, open(os.path.join(ARCH, 'r', rid, 'voice.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
        continue
    v['model2'] = h.get('model', '')
    v['note'] = ('The voice layer: what machines made of the sound in 2026. First a very small speech model that knows only English (%s). Where its words '
                 'carried no meaning, the sound was heard again by a model that knows Hindi, Bengali and English (%s); Hindi and Bengali are written in the '
                 'English alphabet, as people type them. "lang" says where: [start s, end s, "hi" or "bn"]. Both mishear, as the 2021 caption machine did. '
                 '[start s, end s, text].') % (v.get('model', ''), v['model2'])
    touched.append(rid); tally['lines out'] += len(drop); tally['lines in'] += len(new)
    if not DRY: json.dump(v, open(os.path.join(ARCH, 'r', rid, 'voice.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
if touched and not DRY:
    ip = os.path.join(ARCH, 'r', 'index.json'); idx = json.load(open(ip, encoding='utf-8'))
    for r in idx['recordings']:
        if r['id'] in touched:
            v = voices[r['id']]; r['lines'] = len(v['segs'])
            if not r.get('heard') and v.get('heard_hours'): r['heard'] = v['heard_hours']; r['speech_s'] = round(sum(s[1] - s[0] for s in v['segs']))
    json.dump(idx, open(ip, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    ap = os.path.join(ROOT, 'data', 'archive.json'); a = json.load(open(ap, encoding='utf-8'))
    a['counts']['spoken_lines'] = sum(r.get('lines', 0) for r in idx['recordings']); json.dump(a, open(ap, 'w', encoding='utf-8'), ensure_ascii=False)
print(('DRY RUN. ' if DRY else '') + '%d recordings changed' % len(touched)); print(dict(tally)); print({k: round(x / 3600, 2) for k, x in secs.items()}, 'hours by language')
