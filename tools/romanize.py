#!/usr/bin/env python3
"""Hindi (Devanagari) and Bengali written in the English alphabet, the way people type them in a chat.

Standard library only.   from romanize import latin;  latin('मैं ठीक हूँ') -> 'main theek hoon'

Not a scholar's transliteration: no dots or bars, long vowels doubled (aa, ee, oo), the unspoken "a" left out where a
speaker leaves it out. Anything that is not Devanagari or Bengali passes through untouched, so mixed speech keeps its
English words. It is a rule, and it mishears like everything else here.
"""
import re
import unicodedata

_DV = dict(zip('कखगघङचछजझञटठडढणतथदधनपफबभमयरलवशषसहळ', ['k','kh','g','gh','ng','ch','chh','j','jh','n','t','th','d','dh','n','t','th','d','dh','n','p','ph','b','bh','m','y','r','l','v','sh','sh','s','h','l']))
_DV.update({'क़':'q','ख़':'kh','ग़':'gh','ज़':'z','ड़':'r','ढ़':'rh','फ़':'f','य़':'y'})
_DVV = {'अ':'a','आ':'aa','इ':'i','ई':'ee','उ':'u','ऊ':'oo','ऋ':'ri','ए':'e','ऐ':'ai','ओ':'o','औ':'au','ऑ':'o','ऍ':'e'}
_DVM = {'ा':'aa','ि':'i','ी':'ee','ु':'u','ू':'oo','ृ':'ri','े':'e','ै':'ai','ो':'o','ौ':'au','ॉ':'o','ॅ':'e'}
_BN = dict(zip('কখগঘঙচছজঝঞটঠডঢণতথদধনপফবভমযরলশষসহ', ['k','kh','g','gh','ng','ch','chh','j','jh','n','t','th','d','dh','n','t','th','d','dh','n','p','ph','b','bh','m','j','r','l','sh','sh','s','h']))
_BN.update({'ড়':'r','ঢ়':'rh','য়':'y','ৎ':'t'})
_BNV = {'অ':'o','আ':'a','ই':'i','ঈ':'i','উ':'u','ঊ':'u','ঋ':'ri','এ':'e','ঐ':'oi','ও':'o','ঔ':'ou'}
_BNM = {'\u09be':'a','\u09bf':'i','\u09c0':'i','\u09c1':'u','\u09c2':'u','\u09c3':'ri','\u09c7':'e','\u09c8':'oi','\u09cb':'o','\u09cc':'ou'}
_NUKTA = {'क':'क़','ख':'ख़','ग':'ग़','ज':'ज़','ड':'ड़','ढ':'ढ़','फ':'फ़','य':'य़','ড':'ড়','ঢ':'ঢ়','য':'য়'}
_DIG = {**{c: str(i) for i, c in enumerate('०१२३४५६७८९')}, **{c: str(i) for i, c in enumerate('০১২৩৪৫৬৭৮৯')}}


def _word(w, cons, vow, mat, halant, inherent, nasal, bengali):
    """One word -> list of [consonant letters, vowel] units, then the unspoken inherent vowels are taken out."""
    units = []; i = 0; n = len(w)
    while i < n:
        c = w[i]
        if i + 1 < n and w[i + 1] in '़়' and c in _NUKTA: c = _NUKTA[c]; i += 1
        if c in cons:
            v = inherent; j = i + 1; own = False
            if j < n and w[j] in mat: v = mat[w[j]]; j += 1; own = True
            elif j < n and w[j] == halant: v = ''; j += 1; own = True
            units.append([cons[c], v, not own]); i = j
        elif c in vow: units.append(['', vow[c], False]); i += 1
        elif c in 'ंঁँং':
            nxt = w[i + 1] if i + 1 < n else ''
            s = 'ng' if c == 'ং' else ('m' if nxt and nxt in 'पफबभमপফবভম' else 'n')
            if units: units[-1][1] += s
            else: units.append(['', s, False])
            i += 1
        elif c in 'ःঃ':
            if units: units[-1][1] += 'h'
            i += 1
        elif c in _DIG: units.append(['', _DIG[c], False]); i += 1
        else: units.append(['', c if c not in '़়्্‌‍' else '', False]); i += 1
    # the last unspoken vowel of a word is silent (except in one-syllable words: na, ka)
    sounded = [k for k, u in enumerate(units) if u[1]]
    if units and units[-1][2] and len(sounded) > 1: units[-1][1] = ''
    elif units and len(sounded) > 1 and units[-1][1] in ('aa', 'ee'): units[-1][1] = 'a' if units[-1][1] == 'aa' else 'i'     # ladka, nahi: as people type it
    if not bengali:
        # Hindi: an unspoken "a" between two sounded syllables falls out (ladaka -> ladka), never two in a row
        k = len(units) - 2
        while k >= 1:
            u = units[k]
            if u[2] and u[1] == 'a' and units[k + 1][1] and units[k - 1][1] and units[k - 1][1][-1] in 'aeiou' and units[k + 1][0]: u[1] = ''; k -= 2
            else: k -= 1
    return ''.join(a + b for a, b, _ in units)


def latin(text):
    def dv(m): return _word(m.group(0), _DV, _DVV, _DVM, '्', 'a', None, False)
    def bn(m): return _word(m.group(0), _BN, _BNV, _BNM, '্', 'o', None, True)
    text = unicodedata.normalize('NFC', text)
    text = re.sub('[\u0900-\u0963\u0966-\u097f]+', dv, text)
    text = re.sub('[\u0980-\u09ff]+', bn, text)
    return text.replace('।', '.').replace('॥', '.')


if __name__ == '__main__':
    import sys
    print(latin(' '.join(sys.argv[1:]) or 'मैं ठीक हूँ, तुम कैसे हो? लड़का मीटिंग में है। আমি ভালো আছি, তুমি কেমন আছো? কাল দেখা হবে।'))
