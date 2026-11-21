#!/usr/bin/env python3
"""Take the machine-read words of hidden things out of the archive repository's JSON.

Standard library only. The sweep hides a picture, a recording or a minute on the site at once (data/veiled.json), but it
holds no key to the archive repository, so what a machine read or heard in the hidden thing stays there as text, with
whatever names it carries, until a steward or a helper runs this:

  python3 tools/veil_text.py ARCHIVE_CLONE KEPT_ASIDE.json            take the words out, keep them aside
  python3 tools/veil_text.py ARCHIVE_CLONE KEPT_ASIDE.json --restore  put back the words of things no longer hidden

KEPT_ASIDE.json must be a file outside both repositories (the author's drive): it holds exactly what was taken out, so
that a thing which is shown again gets its words back. Then commit and push the archive clone.

Touched: i/text.json (words read in pictures), i/doc.json (which words of the 2021 document stand beside a picture),
i/sound.json (where a picture was found in the recordings), i/names.json (where a listed first name was read, and the
recordings the author named somebody in), and
r/<id>/voice.json (what was heard and what was typed in the chat, per minute), and r/find.json, the copy of the voice
files that Find on the site searches (made again by tools/search_build.py at the end). The picture and frame files themselves
are not touched: whether they leave the archive is the author's decision when he settles the request.
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def save(p, obj):
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    arch, aside_path = sys.argv[1], sys.argv[2]
    restore = "--restore" in sys.argv[3:]
    if os.path.abspath(aside_path).startswith((os.path.abspath(arch) + os.sep, ROOT + os.sep)):
        sys.exit("Keep the file of words taken out somewhere outside both repositories.")
    veiled = load(os.path.join(ROOT, "data", "veiled.json")).get("ids", {})
    pics = {i for i in veiled if re.fullmatch(r"m\d{5}", i)}
    recs = {i for i in veiled if re.fullmatch(r"r\d{3}", i)}
    mins = {}
    for i in veiled:
        m = re.fullmatch(r"(r\d{3})\.(\d{4})", i)
        if m:
            mins.setdefault(m.group(1), set()).add(int(m.group(2)))
    aside = load(aside_path) if os.path.exists(aside_path) else {}
    for k in ("text", "doc", "sound", "names", "named", "voice"):
        aside.setdefault(k, {})
    n = {"text": 0, "doc": 0, "sound": 0, "names": 0, "voice": 0, "restored": 0}
    hidden_min = lambda rid, sec: rid in recs or int(sec // 60) in mins.get(rid, ())

    # --- pictures ---
    p = os.path.join(arch, "i", "text.json")
    T = load(p)
    for m in sorted(pics):
        if m in T["text"]:
            aside["text"][m] = T["text"].pop(m)
            n["text"] += 1
    if restore:
        for m in [m for m in aside["text"] if m not in pics]:
            T["text"][m] = aside["text"].pop(m)
            n["restored"] += 1
        T["text"] = dict(sorted(T["text"].items()))
    save(p, T)

    p = os.path.join(arch, "i", "doc.json")
    D = load(p)
    for m in sorted(pics):
        k = str(int(m[1:]))
        if k in D.get("pics", {}):
            aside["doc"][k] = D["pics"].pop(k)
            n["doc"] += 1
    if restore:
        for k in [k for k in aside["doc"] if "m%05d" % int(k) not in pics]:
            D["pics"][k] = aside["doc"].pop(k)
            n["restored"] += 1
    save(p, D)

    p = os.path.join(arch, "i", "sound.json")
    S = load(p)
    for m in sorted(pics):
        k = str(int(m[1:]))
        if k in S.get("at", {}):
            aside["sound"][k] = S["at"].pop(k)
            n["sound"] += 1
    for k in [k for k, v in S.get("at", {}).items() if hidden_min(v[0], v[1])]:   # a picture taken in a hidden minute
        aside["sound"][k] = S["at"].pop(k)
        n["sound"] += 1
    if restore:
        for k in [k for k, v in aside["sound"].items() if "m%05d" % int(k) not in pics and not hidden_min(v[0], v[1])]:
            S["at"][k] = aside["sound"].pop(k)
            n["restored"] += 1
    save(p, S)

    p = os.path.join(arch, "i", "names.json")
    N = load(p)
    gone = {int(m[1:]) for m in pics}
    for pid, v in N.get("people", {}).items():
        out = [x for x in v.get("pics", []) if x in gone]
        if out:
            aside["names"].setdefault(pid, [])
            aside["names"][pid] = sorted(set(aside["names"][pid]) | set(out))
            v["pics"] = [x for x in v["pics"] if x not in gone]
            n["names"] += len(out)
        if restore and aside["names"].get(pid):
            back = [x for x in aside["names"][pid] if x not in gone]
            v["pics"] = sorted(set(v.get("pics", [])) | set(back))
            aside["names"][pid] = [x for x in aside["names"][pid] if x in gone]
            n["restored"] += len(back)
        # the recordings the author himself named this person in (`named`): a hidden recording leaves the list too
        out = [x for x in v.get("named", []) if x in recs]
        if out:
            aside["named"][pid] = sorted(set(aside["named"].get(pid, [])) | set(out))
            v["named"] = [x for x in v["named"] if x not in recs]
            if not v["named"]:
                del v["named"]
            n["names"] += len(out)
        if restore and aside["named"].get(pid):
            back = [x for x in aside["named"][pid] if x not in recs]
            if back:
                v["named"] = sorted(set(v.get("named", [])) | set(back))
            aside["named"][pid] = [x for x in aside["named"][pid] if x in recs]
            n["restored"] += len(back)
    save(p, N)

    # --- recordings: what was heard, what was typed ---
    for rid in sorted(recs | set(mins) | set(aside["voice"])):
        p = os.path.join(arch, "r", rid, "voice.json")
        if not os.path.exists(p):
            continue
        V = load(p)
        kept = aside["voice"].setdefault(rid, {"segs": [], "chat": []})
        for key in ("segs", "chat"):
            rows = V.get(key, [])
            sec = lambda row: float(row[0]) if key == "segs" else float(row[1] if isinstance(row[1], (int, float)) else row[0])
            out = [row for row in rows if hidden_min(rid, sec(row))]
            if out:
                kept[key] += out
                V[key] = [row for row in rows if not hidden_min(rid, sec(row))]
                n["voice"] += len(out)
            if restore:
                back = [row for row in kept[key] if not hidden_min(rid, sec(row))]
                if back:
                    V[key] = sorted(V.get(key, []) + back, key=sec)
                    kept[key] = [row for row in kept[key] if hidden_min(rid, sec(row))]
                    n["restored"] += len(back)
        save(p, V)
    os.makedirs(os.path.dirname(os.path.abspath(aside_path)), exist_ok=True)
    save(aside_path, aside)
    print("taken out: %(text)d picture texts, %(doc)d document places, %(sound)d moments, %(names)d name readings, "
          "%(voice)d spoken or typed lines; put back: %(restored)d" % n)
    # what Find searches in the recordings is a copy of the voice files: it must never hold what they no longer do
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import search_build
    print("r/find.json " + ("written again" if search_build.build(arch)[0] else "unchanged") + " (what Find searches in the recordings)")


if __name__ == "__main__":
    main()
