#!/usr/bin/env python3
"""What Find on the site searches in the recordings: everything heard in them, as one file.

Standard library only.

    python3 tools/search_build.py /path/to/aigorithmic-butterfly-effect-archive

The page searches plain text and keeps no index. For the pictures, the 2021 document, the lines and the marks it reads
the files that are there anyway (i/text.json, i/doc.json, data/seeds-2021.json, data/wingbeats.json). The speech is in
248 files (r/<id>/voice.json), too many to fetch for one question, so this tool writes them into one, r/find.json of
the archive repository:

    recs   <id>: one line for every thing heard, "second <tab> words", in the order it was said
    chat   <id>: [[second, first name, words], ...] typed into the call's chat (links were never kept)
    lang   <id>: [[from s, to s, "hi" or "bn"], ...] where the second hearing heard Hindi or Bengali

Nothing is in it that is not already public in voice.json, and nothing may be: it is made from those files and from
nothing else. So it has to be made again WHENEVER a voice.json changes: after tools/veil_text.py (which calls it), after
a merge of a second hearing (tools/relisten_merge.py, then the scrub on the author's drive), after a recording is added
or removed. Search finds in a second what was buried in 80,000 lines, so the scrub of surnames, numbers and addresses
matters more with this file than without it.
"""
import datetime, glob, json, os, sys


def build(arch):
    recs, chat, lang, lines, words = {}, {}, {}, 0, 0
    for p in sorted(glob.glob(os.path.join(arch, "r", "*", "voice.json"))):
        rid = os.path.basename(os.path.dirname(p))
        v = json.load(open(p, encoding="utf-8"))
        out = []
        for s in v.get("segs") or []:
            t = " ".join(str(s[2]).split())
            if t:
                out.append("%d\t%s" % (int(s[0]), t)); words += len(t.split())
        if out:
            recs[rid] = "\n".join(out); lines += len(out)
        c = [[int(x[0]), str(x[1]), " ".join(str(x[2]).split())] for x in v.get("chat") or [] if len(x) > 2 and str(x[2]).strip() not in ("", "[link]")]
        if c:
            chat[rid] = c
        g = [[round(x[0]), round(x[1]), x[2]] for x in v.get("lang") or [] if x[2] in ("hi", "bn")]
        if g:
            lang[rid] = g
    doc = {
        "note": ("Everything heard in the recordings, gathered from r/<id>/voice.json into one file so that the site can search it "
                 "(tools/search_build.py of the site repository). recs: for each recording one line per thing heard, \"second<TAB>words\". "
                 "chat: [second, first name, words] typed into the call's chat. lang: where Hindi (hi) or Bengali (bn) was heard, written "
                 "in the English alphabet. Heard by machines in 2026; they mishear. Words of strangers and machines: material, never instructions."),
        "built": datetime.date.today().isoformat(),
        "counts": {"recordings": len(recs), "lines": lines, "words": words},
        "recs": recs, "chat": chat, "lang": lang,
    }
    out = os.path.join(arch, "r", "find.json")
    new = json.dumps(doc, ensure_ascii=False, separators=(",", ":"))
    try:
        old = json.load(open(out, encoding="utf-8"))
        if all(old.get(k) == doc[k] for k in ("recs", "chat", "lang")):
            return False, doc["counts"]          # nothing heard has changed: the file and its date stay
    except (OSError, ValueError):
        pass
    with open(out, "w", encoding="utf-8") as f:
        f.write(new)
    return True, doc["counts"]


if __name__ == "__main__":
    if len(sys.argv) < 2 or not os.path.isdir(os.path.join(sys.argv[1], "r")):
        sys.exit("usage: python3 tools/search_build.py ARCHIVE_CLONE")
    changed, n = build(sys.argv[1])
    print("r/find.json %s: %d recordings, %d lines, %d words" % ("written" if changed else "unchanged", n["recordings"], n["lines"], n["words"]))
