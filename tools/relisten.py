#!/usr/bin/env python3
"""Step 2 to 4 of listening again: hear the marked parts once more with a model that knows Hindi, Bengali and English.

Runs on a machine with faster-whisper installed (the archive repository's workflow "listen again" does that); the other
tools here need nothing but Python, this one cannot.

  python3 relisten.py --arch ARCHIVE_CLONE --plan relisten_plan.json --out OUTDIR [--shard 0/12] [--only "r004 r011"]
                      [--model large-v3] [--audio https://raw.githubusercontent.com/<archive>/audio/] [--budget 19000]

For each marked window (tools/relisten_find.py) it cuts the sound into pieces of at most 28 seconds along the pauses the
first hearing found, asks the model which language each piece is in, and keeps the answer to English, Hindi or Bengali
(Urdu, Punjabi, Marathi, Nepali, Gujarati count as Hindi, Assamese as Bengali: to a machine they sound alike, and these
calls were held in the three). A piece in Hindi or Bengali is written down twice: as the model writes it, in its own
script, and again with a prompt in the English alphabet, because people in these calls mixed the languages and an English
word should stay an English word. Whatever is still in Devanagari or Bengali letters after that is put into the English
alphabet by rule (tools/romanize.py). Nothing is published by this: it writes OUTDIR/<recording>.json, and
tools/relisten_merge.py decides what replaces the first hearing.
"""
import argparse, json, os, sys, time, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from romanize import latin

ap = argparse.ArgumentParser()
ap.add_argument('--arch', required=True); ap.add_argument('--plan', required=True); ap.add_argument('--out', required=True)
ap.add_argument('--shard', default='0/1'); ap.add_argument('--only', default=''); ap.add_argument('--model', default='large-v3')
ap.add_argument('--audio', default='https://raw.githubusercontent.com/ranaji10/aigorithmic-butterfly-effect-archive/audio/')
ap.add_argument('--budget', type=float, default=19000); ap.add_argument('--threads', type=int, default=4)
A = ap.parse_args()
T0 = time.time(); SR = 16000
FOLD = {'en': 'en', 'hi': 'hi', 'ur': 'hi', 'pa': 'hi', 'mr': 'hi', 'ne': 'hi', 'gu': 'hi', 'sd': 'hi', 'sa': 'hi', 'bn': 'bn', 'as': 'bn'}
PROMPT = {'hi': 'Haan, theek hai. Main bata raha hoon, you know, basically yeh aise hi hota hai. Accha, toh phir kya hua? Mujhe lagta hai ki it is fine.',
          'bn': 'Hyan, thik ache. Ami bolchi, you know, basically eta erokom-i hoy. Accha, tarpor ki holo? Amar mone hoy je it is fine.'}

plan = json.load(open(A.plan, encoding='utf-8'))['plan']
order = sorted(plan, key=lambda r: -sum(b - a for a, b, _ in plan[r]))
i, n = [int(x) for x in A.shard.split('/')]
load = [0.0] * n; mine = []
for r in order:                                    # heaviest first, each to the lightest shard: the same split on every machine
    k = load.index(min(load)); load[k] += sum(b - a for a, b, _ in plan[r])
    if k == i: mine.append(r)
if A.only.strip(): mine = [r for r in A.only.split() if r in plan]
print('shard', A.shard, ':', len(mine), 'recordings,', round(sum(b - a for r in mine for a, b, _ in plan[r]) / 3600, 2), 'h', flush=True)

from faster_whisper import WhisperModel
from faster_whisper.audio import decode_audio
import numpy as np
model = WhisperModel(A.model, device='cpu', compute_type='int8', cpu_threads=A.threads)
os.makedirs(A.out, exist_ok=True); os.makedirs('/tmp/aud', exist_ok=True)
_piece = {}


def keep(res, dst):
    json.dump(res, open(dst + '.part', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':')); os.replace(dst + '.part', dst)


def piece(rid, k):
    """Ten minutes of sound (second // 600 = k) as samples; the last two are kept in memory."""
    if (rid, k) in _piece: return _piece[(rid, k)]
    p = '/tmp/aud/%s_%03d.webm' % (rid, k)
    try:
        if not os.path.exists(p): urllib.request.urlretrieve('%s%s/%03d.webm' % (A.audio, rid, k), p)
        x = decode_audio(p, sampling_rate=SR)
    except Exception as e:
        print('  no sound', rid, k, str(e)[:80], flush=True); x = np.zeros(0, dtype=np.float32)
    for key in list(_piece)[:-1]: del _piece[key]
    _piece[(rid, k)] = x
    try: os.remove(p)
    except OSError: pass
    return x


def cut(rid, a, b):
    out = []; k = int(a // 600)
    while k * 600 < b:
        x = piece(rid, k); lo = max(0, int((a - k * 600) * SR)); hi = min(len(x), int((b - k * 600) * SR))
        if hi > lo: out.append(x[lo:hi])
        k += 1
    return np.concatenate(out) if out else np.zeros(0, dtype=np.float32)


def hear(x, lang, prompt=None):
    segs, info = model.transcribe(x, language=lang, beam_size=3, vad_filter=True, vad_parameters={'min_silence_duration_ms': 400},
                                  condition_on_previous_text=False, initial_prompt=prompt, temperature=[0.0, 0.2, 0.4],
                                  compression_ratio_threshold=2.2, no_speech_threshold=0.6, without_timestamps=False)
    return [[round(s.start, 1), round(s.end, 1), s.text.strip(), round(s.avg_logprob, 2), round(s.no_speech_prob, 2)] for s in segs if s.text.strip()], info


for rid in mine:
    dst = os.path.join(A.out, rid + '.json')
    res = {'id': rid, 'model': 'faster-whisper ' + A.model, 'done': False, 'windows': {}}
    if os.path.exists(dst):
        try: res = json.load(open(dst, encoding='utf-8'))
        except Exception: pass
    if res.get('done'): continue
    voice = json.load(open(os.path.join(A.arch, 'r', rid, 'voice.json'), encoding='utf-8'))
    starts = sorted(s[0] for s in voice.get('segs', []))
    for a, b, signs in plan[rid]:
        key = '%.1f' % a
        if key in res['windows']: continue
        if time.time() - T0 > A.budget:
            keep(res, dst); print('out of time; partly done:', rid, flush=True); sys.exit(0)
        marks = [a] + [s for s in starts if a + 4 < s < b - 2] + [b]; cuts = [a]
        for m in marks[1:]:                           # pieces of at most 28 s, cut where the first hearing found a pause
            if m - cuts[-1] > 28:
                prev = max([q for q in marks if cuts[-1] < q < m and q - cuts[-1] <= 28] or [cuts[-1] + 28]); cuts.append(prev)
                while m - cuts[-1] > 28: cuts.append(cuts[-1] + 28)
        cuts.append(b); chunks = []
        for c0, c1 in zip(cuts, cuts[1:]):
            if c1 - c0 < 0.4: continue
            x = cut(rid, c0, c1)
            if len(x) < SR * 0.4: continue
            try:
                lang0, p0, probs = model.detect_language(x)
            except Exception as e:
                print('  detect failed', rid, c0, str(e)[:80], flush=True); continue
            f = {'en': 0.0, 'hi': 0.0, 'bn': 0.0}
            for l, p in probs:
                if l in FOLD: f[FOLD[l]] += float(p)
            lang = max(f, key=f.get)
            ch = {'s': round(c0, 1), 'e': round(c1, 1), 'lang': lang, 'p': {k: round(v, 3) for k, v in f.items()}, 'said': lang0}
            native, _ = hear(x, lang)
            if lang == 'en': final = native
            else:
                ch['native'] = [[round(c0 + s, 1), round(c0 + e, 1), t, lp, ns] for s, e, t, lp, ns in native]
                final, _ = hear(x, lang, PROMPT[lang])
                if not final: final = native
            ch['segs'] = [[round(c0 + s, 1), round(c0 + e, 1), latin(t), lp, ns] for s, e, t, lp, ns in final]
            chunks.append(ch)
        res['windows'][key] = {'a': a, 'b': b, 'signs': signs, 'chunks': chunks}
        if len(res['windows']) % 10 == 0: keep(res, dst)
    res['done'] = True
    keep(res, dst)
    print('done', rid, len(res['windows']), 'windows,', round((time.time() - T0) / 60), 'min in', flush=True)
