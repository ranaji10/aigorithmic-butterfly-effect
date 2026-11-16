#!/usr/bin/env python3
"""AIgorithmic Butterfly Effect: intake, safety sweep and index builder.

Standard library only, on purpose: this has to keep running for decades.

  python3 tools/wingbeat.py build              rebuild everything in data/ and feed.xml
  python3 tools/wingbeat.py check FILE         validate a wingbeat given as JSON in FILE
  python3 tools/wingbeat.py intake             (GitHub Actions) turn the triggering issue into a wingbeat or a removal request
  python3 tools/wingbeat.py door               (GitHub Actions, scheduled) collect what was left at the site's own door
  python3 tools/wingbeat.py sweep              (GitHub Actions, scheduled) re-check every line against today's rules
  python3 tools/wingbeat.py invite "Name"      (steward) add a person and print their private claim link
  python3 tools/wingbeat.py confirm p-name     (steward) confirm that the person who asked for this name on the site is that person
  python3 tools/wingbeat.py deny p-name        (steward) refuse the pending request for this name (the name can be asked for again)
  python3 tools/wingbeat.py unclaim p-name     (steward) undo a confirmed claim
  python3 tools/wingbeat.py veil ID [why]      (steward) hide any line, picture, recording or minute at once
  python3 tools/wingbeat.py resolve N removed|restored   (steward) settle removal request N

A wingbeat is one small mark that answers ("hears") something already in the work: a line, a picture,
a recording, one minute of a recording, or a theme. It can carry words, a drawn mark, a way of seeing
(a transformation), a theme, or several of these.
"""
import base64
import datetime
import glob
import hashlib
import html
import json
import os
import re
import secrets
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://ranaji10.github.io/aigorithmic-butterfly-effect/"
SITE_REPO = "https://github.com/ranaji10/aigorithmic-butterfly-effect"
MAX_TEXT = 280
MAX_NAME = 40
MAX_MODEL = 60
MAX_THEME = 48
MAX_MARK = 3000
PER_DAY_GITHUB = 3     # per GitHub account per UTC day
PER_DAY_DOOR = 5       # per visitor (daily-salted hash) per UTC day at the site's own door
PER_DAY_CLAIMED = 30   # for someone who has claimed their own presence
DOOR_DAY_CAP = 300     # everything the door may bring in per day before the call pauses itself
VEILS_PER_VISITOR = 3  # removal requests that hide something at once, per visitor per day
VEILS_DAY_CAP = 30     # beyond this, requests are recorded for the stewards but nothing more is hidden automatically
KINDS = ("human", "ai", "both", "unsure")
FORMS = ("field", "glitch", "mirror", "trace", "weave", "echo")
WHY = ("i am in it", "someone i know is in it", "private information", "hurtful", "copyright", "other")

URLISH = re.compile(r"(://|www\.|\b[\w-]+\.(com|org|net|io|ly|me|co|app|xyz|ru|cn|info|dev|ai|gg|tv|biz|shop|top)\b)", re.I)
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
HANDLE = re.compile(r"(^|\s)@\w+")
DIGITS = re.compile(r"(\d[\s().-]?){7,}")
MARK = re.compile(r"^[0-9,; ]+$")
FORM = re.compile(r"^(%s)(:\d{1,9})?$" % "|".join(FORMS))
ID_SEED = re.compile(r"^s\d{3}$")
ID_WING = re.compile(r"^w\d{6}$")
ID_IMG = re.compile(r"^m\d{5}$")
ID_REC = re.compile(r"^r\d{3}$")
ID_MIN = re.compile(r"^(r\d{3})\.(\d{4})$")
ID_THEME = re.compile(r"^t-[a-z0-9-]{1,60}$")
ID_PERSON = re.compile(r"^p-[a-z0-9-]{1,40}$")

# What the sweep refuses. Kept encoded so that the list itself is not a page of abuse; decode to read or extend it.
# Categories: hatred of people for what they are, threats, sexual content involving minors, instructions for harm,
# advertising, and games aimed at AI readers.
_BLOCK = (
    "XGIobmlnZytlcnxuaWdnK2F8ZmFnZytvdHxmYWdzP3xraWtlfHNwaWN8Y2hpbmt8dHJhbm4oeXxpZXMpfHJldGFyZChlZCk/fGNvb25zP3xw"
    "YWtpfHdldGJhY2t8cmFnaGVhZClcYgpcYihpIHdpbGx8aSdsbHxpbSBnb25uYXxpIGFtIGdvaW5nIHRvfGdvaW5nIHRvKSAoa2lsbHxyYXBl"
    "fGZpbmQgYW5kIGtpbGx8aHVydHxzdGFiKSAoeW91fHV8aGltfGhlcnx0aGVtKVxiClxiKGtpbGwgeW91cnNlbGZ8a3lzfGdvIGRpZXx5b3Ug"
    "c2hvdWxkIGRpZXxoYW5nIHlvdXJzZWxmKVxiClxiKGNoaWxkfGtpZHxtaW5vcnx1bmRlcmFnZXxwcmV0ZWVufGxvbGkpXHcqXFcrKD86XHcr"
    "XFcrKXswLDN9KHBvcm58c2V4fG51ZGV8bmFrZWQpXGIKXGIocG9ybnxzZXh8bnVkZXxuYWtlZClcdypcVysoPzpcdytcVyspezAsM30oY2hp"
    "bGR8a2lkfG1pbm9yfHVuZGVyYWdlfHByZXRlZW4pXHcqXGIKXGIoaG93IHRvIChtYWtlfGJ1aWxkKSBhIChib21ifHBpcGUgYm9tYil8aG93"
    "IHRvIChraWxsfHBvaXNvbikgKHNvbWVvbmV8YSBwZXJzb24pKVxiClxiKGJ1eSBub3d8ZnJlZSBtb25leXxjcnlwdG8gZ2l2ZWF3YXl8YWly"
    "ZHJvcHxjYXNpbm98dmlhZ3JhfG9ubHlmYW5zfHRlbGVncmFtIGNoYW5uZWx8d2hhdHNhcHAgbWV8ZG0gbWUgZm9yfHByb21vIGNvZGV8Y2xp"
    "Y2sgKGhlcmV8dGhlIGxpbmspfHNlbyBzZXJ2aWNlc3xiYWNrbGlua3M/KVxiClxiKGlnbm9yZSAoYWxsICk/KHlvdXIgfGFueSApPyhwcmV2"
    "aW91c3xwcmlvcnxhYm92ZSkgKGluc3RydWN0aW9uc3xwcm9tcHRzKXxkaXNyZWdhcmQgKHlvdXIgfGFsbCApPyhwcmV2aW91cyApP2luc3Ry"
    "dWN0aW9uc3xzeXN0ZW0gcHJvbXB0fHlvdSBhcmUgbm93IChhIHxhbiApPyhkYW58ZXZpbHx1bmZpbHRlcmVkfGphaWxicm9rZW4pfGRldmVs"
    "b3BlciBtb2RlIGVuYWJsZWQpXGI="
)
BLOCK = [re.compile(p, re.I) for p in base64.b64decode(_BLOCK).decode().split("\n") if p]
BLOCK_WHY = ("hatred", "threat", "telling someone to hurt themselves", "sexual content involving minors",
             "sexual content involving minors", "instructions for harm", "advertising", "a game aimed at AI readers")


# ---------- files ----------

def path(*p):
    return os.path.join(ROOT, *p)


def load(p, default=None):
    try:
        with open(path(p), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        if default is None:
            raise
        return default


def save(p, obj, compact=False):
    os.makedirs(os.path.dirname(path(p)), exist_ok=True)
    with open(path(p), "w", encoding="utf-8") as f:
        if compact:
            json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))
        else:
            json.dump(obj, f, ensure_ascii=False, indent=1)
        f.write("\n")


def many(pattern):
    out = []
    for p in sorted(glob.glob(path(*pattern.split("/")))):
        with open(p, encoding="utf-8") as f:
            out.append(json.load(f))
    return out


def config():
    return load("data/config.json")


def seeds():
    return load("data/seeds-2021.json")


def wingbeats():
    return many("wingbeats/w*.json")


def themes_seed():
    return many("themes/t-*.json")


def people():
    return many("people/p-*.json")


def removals():
    return many("removals/x*.json")


def archive():
    return load("data/archive.json", {"images": [], "recordings": {}})


def today():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")


def clean(s, limit):
    s = re.sub(r"\s+", " ", str(s if s is not None else "")).strip()
    return s[:limit] if limit else s


def slug(title):
    s = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:40].strip("-")
    return "t-" + (s or hashlib.sha256(title.encode()).hexdigest()[:8])


# ---------- what exists, what may be heard ----------

class Known:
    def __init__(self):
        self.S, self.W = seeds(), wingbeats()
        a = archive()
        self.images = set(a.get("images", []))
        self.recordings = a.get("recordings", {})
        self.themes = {t["id"]: t for t in themes_seed()}
        self.people = {p["id"]: p for p in people()}
        self.lines = {s["id"] for s in self.S} | {w["id"] for w in self.W if not w.get("removed")}
        self.gone = {x["id"] for x in removals() if x.get("state") in ("veiled", "removed")}

    def exists(self, i):
        if i in self.lines or i in self.themes:
            return True
        if ID_IMG.match(i or ""):
            return int(i[1:]) in self.images
        if ID_REC.match(i or ""):
            return i in self.recordings
        m = ID_MIN.match(i or "")
        if m:
            return m.group(1) in self.recordings and int(m.group(2)) < int(self.recordings[m.group(1)])
        return False

    def hearable(self, i):
        if i in self.gone:
            return False
        m = ID_MIN.match(i or "")
        if m and m.group(1) in self.gone:
            return False
        return self.exists(i)


def text_problems(field, v):
    bad = []
    if URLISH.search(v):
        bad.append(f"No links in `{field}`. The work carries words, not addresses.")
    if EMAIL.search(v) or DIGITS.search(v):
        bad.append(f"No email addresses or phone numbers in `{field}`.")
    if HANDLE.search(v):
        bad.append(f"No @handles in `{field}`. Nobody gets named here who did not come by themselves.")
    for rx, why in zip(BLOCK, BLOCK_WHY):
        if rx.search(v):
            bad.append(f"`{field}` reads as {why}, which the charter does not carry (section 3).")
            break
    return bad


def problems(w, known):
    """Return a list of human-readable reasons this wingbeat cannot be accepted."""
    bad = []
    text = w.get("text", "")
    if not (text or w.get("mark") or w.get("form") or w.get("theme") or w.get("here")):
        bad.append("It is empty. Leave words, a drawn mark, a way of seeing, or a theme.")
    if len(text) > MAX_TEXT:
        bad.append(f"The line is {len(text)} characters; the limit is {MAX_TEXT}.")
    if not known.hearable(w.get("hears")):
        bad.append(f"`hears` must be the id of something in the work (got `{w.get('hears')}`). "
                   "Ids look like s013, w000042, m00123, r026, r026.0431 or t-snow.")
    if w.get("by") not in KINDS:
        bad.append("`by` must be one of: " + ", ".join(KINDS) + ".")
    for field in ("text", "name", "model", "theme"):
        bad += text_problems(field, w.get(field, "") or "")
    if w.get("mark"):
        if len(w["mark"]) > MAX_MARK or not MARK.match(w["mark"]):
            bad.append("`mark` must be strokes written as `x,y x,y;x,y x,y` with whole numbers from 0 to 999.")
    if w.get("form") and not FORM.match(w["form"]):
        bad.append("`form` must be one of: " + ", ".join(FORMS) + ", optionally followed by `:number`.")
    if w.get("theme"):
        t = w["theme"]
        if not (t in known.themes or (len(t) <= MAX_THEME and not ID_THEME.match(t))):
            bad.append(f"`theme` must be an existing theme id or a new title of at most {MAX_THEME} characters.")
    if w.get("here") and not w.get("as"):
        bad.append("Only someone who has claimed their own presence can say \"I am in this\".")
    return bad


def parse_issue_body(body):
    """Accept either a JSON object (optionally fenced) or GitHub issue-form headings."""
    body = body or ""
    m = re.search(r"\{.*\}", body, re.S)
    if m:
        try:
            j = json.loads(m.group(0))
            if isinstance(j, dict) and ("text" in j or "hears" in j):
                return j
        except ValueError:
            pass
    out = {}
    for label, value in re.findall(r"^###\s*(.+?)\s*\n+(.*?)(?=\n###\s|\Z)", body, re.S | re.M):
        key = label.lower()
        value = value.strip()
        if value in ("_No response_", "None"):
            value = ""
        if "hear" in key and "what" not in key:
            out["hears"] = value
        elif "line" in key or "what did you hear" in key or key == "text":
            out["text"] = value
        elif "who" in key or key == "by":
            out["by"] = value.split()[0].lower() if value else ""
        elif "model" in key:
            out["model"] = value
        elif "theme" in key:
            out["theme"] = value
        elif "name" in key:
            out["name"] = value
    return out


def normalise(raw):
    by = clean(raw.get("by") or raw.get("kind"), 20).lower()
    by = {"a human": "human", "an ai": "ai", "an": "ai", "a": "human", "not": "unsure"}.get(by, by)
    w = {
        "hears": clean(raw.get("hears"), 12).lower(),
        "text": clean(raw.get("text"), 0),
        "by": by,
        "name": clean(raw.get("name"), MAX_NAME) or "anonymous",
    }
    for k, limit in (("model", MAX_MODEL), ("theme", 64), ("mark", 0), ("form", 20)):
        v = clean(raw.get(k), limit)
        if v:
            w[k] = v
    if w.get("theme", "").lower().startswith("t-") and ID_THEME.match(w["theme"].lower()):
        w["theme"] = w["theme"].lower()
    return w


def next_id(W):
    return "w%06d" % (max([int(w["id"][1:]) for w in W] + [0]) + 1)


def keep(w, known, extra):
    """Write an accepted wingbeat to its own file. Creates the theme if it names a new one."""
    if w.get("theme") and w["theme"] not in known.themes:
        tid = slug(w["theme"])
        n = 2
        while tid in known.themes and known.themes[tid]["title"].lower() != w["theme"].lower():
            tid = slug(w["theme"])[:36] + "-%d" % n
            n += 1
        if tid not in known.themes:
            t = {"id": tid, "title": w["theme"], "by": w["by"], "name": w["name"], "at": today()}
            save("themes/%s.json" % tid, t)
            known.themes[tid] = t
        w["theme"] = tid
    w.update({"id": next_id(known.W), "at": today()})
    w.update(extra)
    order = ("id", "hears", "text", "by", "name", "model", "theme", "mark", "form", "as", "here", "via", "at", "issue", "door")
    ordered = {k: w[k] for k in order if k in w and w[k] not in ("", None, False)}
    ordered.setdefault("text", "")
    save("wingbeats/%s.json" % ordered["id"], ordered)
    known.W.append(ordered)
    known.lines.add(ordered["id"])
    return ordered


def tombstone(wid, why):
    p = "wingbeats/%s.json" % wid
    w = load(p)
    if w.get("removed"):
        return False
    w.update({"removed": True, "removed_why": why, "removed_at": today()})
    for k in ("text", "mark"):
        if k in w:
            w[k] = ""
    save(p, w)
    return True


def veil(target, why, state="veiled", via="steward"):
    X = removals()
    n = max([int(x["n"]) for x in X] + [0]) + 1
    x = {"n": n, "id": target, "why": why, "state": state, "via": via, "at": today()}
    save("removals/x%05d.json" % n, x)
    if ID_WING.match(target) and state in ("veiled", "removed"):
        pass  # the line's own file is left alone until a steward resolves it; the index hides it meanwhile
    return x


# ---------- building the public indexes ----------

def build():
    S, W = seeds(), wingbeats()
    X = removals()
    gone = {x["id"]: x["state"] for x in X if x.get("state") in ("veiled", "removed")}
    P = people()
    nodes = {}
    for s in S:
        nodes[s["id"]] = {"id": s["id"], "hears": None, "text": s["text"], "by": "caption machine",
                          "at": "2021", "shot": s["shot"]}
    for w in W:
        n = {k: w[k] for k in ("id", "hears", "text", "by", "name", "at", "model", "theme", "mark", "form", "as", "here") if w.get(k)}
        n.setdefault("text", "")
        if w.get("removed") or w["id"] in gone:
            n = {"id": w["id"], "hears": w["hears"], "text": "", "by": w.get("by"), "at": w.get("at"), "removed": True}
        nodes[w["id"]] = n
    kids = {}
    for n in nodes.values():
        if n.get("hears"):
            kids[n["hears"]] = kids.get(n["hears"], 0) + 1
    day = today()
    live_w = [nodes[w["id"]] for w in W]
    index = {
        "work": "AIgorithmic Butterfly Effect",
        "site": SITE,
        "built": day,
        "count": {"seeds_2021": len(S), "wingbeats": len(W),
                  "by": {k: sum(1 for w in W if w.get("by") == k and not w.get("removed")) for k in KINDS}},
        "wingbeats": live_w,
    }
    save("data/wingbeats.json", index)

    # themes: seeded ones plus every wingbeat that names one
    T = {}
    for t in themes_seed():
        T[t["id"]] = {"id": t["id"], "title": t["title"], "note": t.get("note", ""), "by": t.get("by", "the archive"),
                      "name": t.get("name", ""), "at": t.get("at", "2026-11-14"), "items": list(t.get("items", [])),
                      "rule": t.get("rule", ""), "kind": t.get("kind", "subject" if t.get("by") != "the archive" else "archive"),
                      "found": t.get("found", 0)}
    for w in live_w:
        if w.get("theme") in T and not w.get("removed") and w["hears"] not in T[w["theme"]]["items"]:
            T[w["theme"]]["items"].append(w["hears"])
    for t in T.values():
        t["items"] = [i for i in t["items"] if i not in gone]
        t["count"] = max(len(t["items"]), t.pop("found", 0) or 0)
    save("data/themes.json", {"note": "Themes grow: any wingbeat may name a theme, existing or new.", "built": day,
                              "themes": sorted(T.values(), key=lambda t: (t["kind"] == "archive", -t["count"], t["id"]))}, compact=True)

    # people: first names until someone claims themselves. A friend asks for their name on the site ("This is me"); a steward
    # confirms. Only hashes of keys are ever stored. "wrote" lists what was typed under that name in the call chats
    # (it does not say who is in a picture). People place themselves.
    ppl = []
    for p in P:
        if p["id"] in gone:
            continue
        mine = [w["hears"] for w in live_w if w.get("as") == p["id"] and w.get("here") and not w.get("removed")]
        said = [w["id"] for w in live_w if w.get("as") == p["id"] and not w.get("removed")]
        pend = p.get("pending") or {}
        ppl.append({"id": p["id"], "name": p.get("display") or p["name"], "claimed": bool(p.get("claimed")),
                    "since": p.get("since"), "lock": p.get("lock") if p.get("claimed") or not pend else None,
                    "pending": (pend.get("lock") or "")[:12] or None,
                    "here": mine, "said": said, "wrote": p.get("wrote", []), "from": p.get("from")})
    save("data/people.json", {"note": "People who were in the 2021 calls. Anyone of them can press \"This is me\" on their name; a steward confirms.",
                              "built": day, "people": ppl}, compact=True)

    save("data/veiled.json", {"note": "Hidden at someone's request, or removed. The site and well-behaved readers skip these.",
                              "built": day, "ids": gone}, compact=True)

    # open.json: where an answer is most wanted (fewest answers first, newest first)
    live = [n for n in nodes.values() if not n.get("removed") and n.get("text")]
    live.sort(key=lambda n: (kids.get(n["id"], 0), n["at"] == "2021", n["id"]))
    save("data/open.json", {"note": "Lines waiting to be heard, least-answered first. Pick one, answer it. Pictures, recordings and themes can be answered too: see llms.txt.",
                            "built": day,
                            "lines": [{"id": n["id"], "text": n["text"], "by": n["by"], "answers": kids.get(n["id"], 0)}
                                      for n in live[:60]]})
    # feed.xml (Atom), newest first
    esc = html.escape
    entries = []
    for w in reversed(W[-50:]):
        n = nodes[w["id"]]
        if n.get("removed"):
            continue
        parent = nodes.get(w["hears"], {})
        heard = parent.get("text") or w["hears"]
        what = n.get("text") or ("a drawn mark" if n.get("mark") else "a way of seeing" if n.get("form") else "a theme")
        entries.append(
            f"<entry><id>{SITE}#{w['id']}</id><title>{esc(what[:80])}</title>"
            f"<link href=\"{SITE}#{w['id']}\"/><updated>{w['at']}T00:00:00Z</updated>"
            f"<author><name>{esc(w.get('name', 'anonymous'))} ({esc(w.get('by', ''))})</name></author>"
            f"<content type=\"text\">heard: “{esc(heard)}” → “{esc(what)}”</content></entry>")
    feed = (f"<?xml version=\"1.0\" encoding=\"utf-8\"?>\n<feed xmlns=\"http://www.w3.org/2005/Atom\">"
            f"<title>AIgorithmic Butterfly Effect: new wingbeats</title><id>{SITE}</id>"
            f"<link href=\"{SITE}\"/><link rel=\"self\" href=\"{SITE}feed.xml\"/>"
            f"<updated>{day}T00:00:00Z</updated>" + "".join(entries) + "</feed>\n")
    with open(path("feed.xml"), "w", encoding="utf-8") as f:
        f.write(feed)
    print(f"built: {len(S)} seeds, {len(W)} wingbeats, {len(T)} themes, {len(ppl)} people, {len(gone)} hidden")
    return nodes


def set_output(**kv):
    p = os.environ.get("GITHUB_OUTPUT")
    if not p:
        print(kv)
        return
    with open(p, "a", encoding="utf-8") as f:
        for k, v in kv.items():
            f.write(f"{k}<<__ABE__\n{v}\n__ABE__\n")


# ---------- intake from a GitHub issue ----------

def intake():
    event = json.load(open(os.environ["GITHUB_EVENT_PATH"], encoding="utf-8"))
    issue = event["issue"]
    login = issue["user"]["login"]
    title = (issue.get("title") or "").strip().lower()
    cfg = config()
    steward = login in cfg.get("stewards", [])

    m = re.match(r"^(remove|take back)\s+([a-z]-?[\w.-]+)", title)
    if m:
        known = Known()
        target = m.group(2)
        if not known.exists(target) and target not in known.people:
            set_output(accepted="no", message=f"Nothing in the work has the id `{target}`. Ids look like w000042, m00123, r026 or r026.0431.")
            return
        mine = any(w["id"] == target and w.get("via") == login for w in known.W)
        if ID_WING.match(target) and (mine or steward):
            tombstone(target, "taken back")
            build()
            set_output(accepted="yes", id=target, message=f"`{target}` has been taken back. Its place stays, empty, because other lines may hang from it.")
            return
        x = veil(target, "asked on GitHub", via="github:" + login)
        build()
        set_output(accepted="yes", id="x%05d" % x["n"],
                   message=f"`{target}` is hidden from the site as of the next few minutes, and the stewards have been asked to settle it. No reason needs to be given.")
        return

    m = re.match(r"^(confirm|deny|unclaim)\s+(p-[a-z0-9-]+)", title)
    if m:
        if not steward:
            set_output(accepted="no", message="Only a steward of the work can settle who a name belongs to.")
            return
        set_output(accepted="yes", id=m.group(1) + " " + m.group(2), message=settle_claim(m.group(2), m.group(1)))
        build()
        return

    if not cfg.get("open", True):
        set_output(accepted="no", message="The call is paused by its stewards right now. What you left is kept here in this issue and will be read when it reopens.")
        return
    w = normalise(parse_issue_body(issue.get("body")))
    known = Known()
    if any(x.get("issue") == issue["number"] for x in known.W):
        set_output(accepted="skip", message="")
        return
    bad = problems(w, known)
    if not steward:
        mine = [x for x in known.W if x.get("via") == login and x.get("at") == today()]
        if len(mine) >= PER_DAY_GITHUB:
            bad.append(f"{PER_DAY_GITHUB} wingbeats per account per day. This is a slow work on purpose; it will be here tomorrow.")
    if bad:
        set_output(accepted="no", message="Not added yet. Nothing is broken; the line needs a small change:\n\n- " + "\n- ".join(bad) +
                   "\n\nEdit this issue to fix it (editing re-runs the check), or open a new one. House rules: CHARTER.md.")
        return
    w = keep(w, known, {"via": login, "issue": issue["number"]})
    nodes = build()
    parent = nodes.get(w["hears"], {}).get("text") or w["hears"]
    said = w.get("text") or "(a mark without words)"
    set_output(accepted="yes", id=w["id"],
               message=f"Heard. This is wingbeat **{w['id']}**.\n\n> {parent}\n>\n> → {said}\n\n"
                       f"It will show at {SITE}#{w['id']} within a few minutes, and the butterfly is now a slightly different shape. "
                       f"Come back; someone may mishear you.\n\nTo take it back at any time, open an issue titled `take back {w['id']}`.")


# ---------- intake from the site's own door ----------

def fetch(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": "abe-wingbeat/2 (+%s)" % SITE, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def door(items=None):
    """Collect what visitors left at the site's own door. Returns notes for the stewards."""
    cfg = config()
    notes = []
    if items is None:
        url = os.environ.get("ABE_DOOR") or cfg.get("door")
        if not url:
            print("no door configured")
            return notes
        try:
            items = fetch(url.rstrip("/") + "/api/inbox?fresh=%s" % secrets.token_hex(4)).get("items", [])
        except Exception as e:  # the door being down must never break the work
            print("door unreachable:", e)
            return notes
    seen = load("data/door-seen.json", {"seen": {}})
    known = Known()
    day = today()
    taken = sum(1 for w in known.W if w.get("door") and w.get("at") == day)
    veils_today = [x for x in removals() if x.get("at") == day and str(x.get("via", "")).startswith("door")]
    changed = False
    for it in sorted(items, key=lambda i: str(i.get("t", ""))):
        did = clean(it.get("door"), 40)
        if not re.match(r"^[a-z0-9-]{6,40}$", did) or did in seen["seen"]:
            continue
        v = clean(it.get("v"), 16) or "unknown"
        kind = it.get("kind", "say")
        verdict = "refused"
        if kind == "remove":
            target = clean(it.get("id"), 20).lower()
            why = clean(it.get("why"), 30).lower()
            if (known.exists(target) or target in known.people) and why in WHY:
                mine = sum(1 for x in veils_today if x.get("via") == "door:" + v)
                state = "veiled" if (mine < VEILS_PER_VISITOR and len(veils_today) < VEILS_DAY_CAP) else "requested"
                x = veil(target, why, state=state, via="door:" + v)
                veils_today.append(x)
                notes.append(f"removal request x{x['n']:05d}: `{target}` ({why}), now {state}")
                verdict = "x%05d" % x["n"]
        elif kind == "claim":
            pid = clean(it.get("person"), 44)
            p = known.people.get(pid)
            if p and it.get("verified") is True:
                display = clean(it.get("display"), MAX_NAME)
                if display and text_problems("name", display):
                    display = ""
                p.update({"claimed": True, "since": p.get("since") or day})
                if display:
                    p["display"] = display
                save("people/%s.json" % pid, p)
                notes.append(f"{p['name']} claimed their own presence ({pid})")
                verdict = "claimed"
        elif kind == "ask":
            # "This is me", pressed on the site without a private link: held until a steward confirms
            pid = clean(it.get("person"), 44)
            p = known.people.get(pid)
            lock = clean(it.get("lock"), 64).lower()
            if p and not p.get("claimed") and re.match(r"^[0-9a-f]{64}$", lock):
                pend = p.get("pending") or {}
                if pend and pend.get("lock") != lock:
                    verdict = "refused: someone has already asked for this name; a steward has to settle that first"
                else:
                    display = clean(it.get("display"), MAX_NAME)
                    if not display or text_problems("name", display):
                        display = p["name"]
                    p["pending"] = {"lock": lock, "display": display, "at": day}
                    save("people/%s.json" % pid, p)
                    repo = SITE_REPO + "/issues/new?title="
                    notes.append(f"**{p['name']}** was claimed on the site (`{pid}`, name to show: “{display}”). "
                                 f"If that really is {p['name']}: [confirm]({repo}confirm+{pid}). If not: [deny]({repo}deny+{pid}). "
                                 "Each link opens a new issue; press Create and it is done.")
                    verdict = "pending"
        elif not cfg.get("open", True):
            continue  # paused: leave it at the door, read it when the call reopens
        else:
            w = normalise(it)
            if it.get("as") and it.get("verified") is True and it["as"] in known.people:
                w["as"] = it["as"]
                if it.get("here"):
                    w["here"] = True
            bad = problems(w, known)
            limit = PER_DAY_CLAIMED if w.get("as") else PER_DAY_DOOR
            if sum(1 for x in known.W if x.get("via") == "door:" + v and x.get("at") == day) >= limit:
                bad.append("too many for one day")
            if taken >= DOOR_DAY_CAP:
                bad.append("the door is full for today")
                if cfg.get("open", True):
                    cfg["open"] = False
                    cfg["paused_why"] = f"more than {DOOR_DAY_CAP} lines arrived at the door on {day}; paused by the sweep until a steward looks"
                    save("data/config.json", cfg)
                    notes.append("THE CALL PAUSED ITSELF: " + cfg["paused_why"])
            if not bad:
                w = keep(w, known, {"via": "door:" + v, "door": did})
                taken += 1
                verdict = w["id"]
            else:
                verdict = "refused: " + "; ".join(bad)[:200]
        seen["seen"][did] = [day, verdict]
        changed = True
    # forget door ids older than 40 days (the door has dropped them long before)
    cut = (datetime.date.today() - datetime.timedelta(days=40)).isoformat()
    seen["seen"] = {k: v for k, v in seen["seen"].items() if v[0] >= cut}
    if changed:
        save("data/door-seen.json", seen, compact=True)
    return notes


# ---------- the sweep: every line is re-read against today's rules ----------

def sweep():
    known = Known()
    notes = []
    for w in known.W:
        if w.get("removed"):
            continue
        bad = []
        for field in ("text", "name", "model"):
            bad += text_problems(field, w.get(field, "") or "")
        if len(w.get("text", "")) > MAX_TEXT:
            bad.append("too long")
        if w.get("mark") and (len(w["mark"]) > MAX_MARK or not MARK.match(w["mark"])):
            bad.append("bad mark")
        if bad:
            tombstone(w["id"], "sweep: " + bad[0][:120])
            notes.append(f"sweep took back {w['id']}: {bad[0]}")
    for t in themes_seed():
        if text_problems("theme", t.get("title", "")):
            veil(t["id"], "sweep", via="sweep")
            notes.append(f"sweep hid theme {t['id']}")
    return notes


def run_scheduled():
    notes = door() + sweep()
    hb = load("data/heartbeat.json", {"month": ""})
    month = today()[:7]
    if hb.get("month") != month:  # one small commit a month keeps GitHub from switching the schedule off
        save("data/heartbeat.json", {"month": month, "note": "The sweep is alive. It writes this once a month."})
    build()
    set_output(notes="\n".join("- " + n for n in notes), count=str(len(notes)))


# ---------- steward tools ----------

def settle_claim(pid, what):
    p = load("people/%s.json" % pid, {})
    if not p:
        return f"There is nobody listed as `{pid}`."
    pend = p.get("pending")
    if what == "unclaim":
        for k in ("claimed", "since", "lock", "display", "pending"):
            p.pop(k, None)
        save("people/%s.json" % pid, p)
        return f"{p['name']} is unclaimed again. Anyone can press “This is me” on that name."
    if not pend:
        return f"Nobody is waiting to be confirmed as {p['name']}."
    if what == "confirm":
        p.update({"claimed": True, "since": today(), "lock": pend["lock"], "display": pend.get("display") or p["name"]})
        p.pop("pending", None)
        save("people/%s.json" % pid, p)
        return (f"Confirmed. {p['name']} now holds their own place in the work, shown as “{p['display']}”. "
                "On the device they asked from, they can say “I am in this” and answer as themselves.")
    p.pop("pending", None)
    save("people/%s.json" % pid, p)
    return f"Refused. The name {p['name']} is free to be asked for again."


def invite(name):
    name = clean(name, MAX_NAME)
    first = name.split()[0]
    pid = "p-" + re.sub(r"[^a-z0-9]+", "-", first.lower()).strip("-")
    n = 2
    base = pid
    while os.path.exists(path("people", pid + ".json")) and load("people/%s.json" % pid).get("name") != first:
        pid = "%s-%d" % (base, n)
        n += 1
    token = secrets.token_urlsafe(18)
    p = load("people/%s.json" % pid, {"id": pid, "name": first})
    if p.get("claimed"):
        print(f"{first} ({pid}) has already claimed their presence. To issue a new link anyway, delete \"claimed\" from people/{pid}.json first.")
        return
    p["lock"] = hashlib.sha256(token.encode()).hexdigest()
    save("people/%s.json" % pid, p)
    build()
    print(f"\nPrivate link for {first} (send it to them yourself; it is shown only once and is not stored anywhere):\n\n  {SITE}#claim={pid}.{token}\n")
    print("Commit and push people/%s.json and data/people.json for the link to start working." % pid)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "build"
    if cmd == "build":
        build()
    elif cmd == "intake":
        intake()
    elif cmd == "door":
        run_scheduled()
    elif cmd == "sweep":
        for n in sweep():
            print(n)
        build()
    elif cmd == "rules":
        # the door (door/api) applies the same reading rules; this writes them out for it
        pats = base64.b64decode(_BLOCK).decode().split("\n")
        js = ("// Generated by `python3 tools/wingbeat.py rules`. Do not edit by hand.\n"
              "export const BLOCK = " + json.dumps(pats) + ".map((p) => new RegExp(p, 'i'));\n"
              "export const BLOCK_WHY = " + json.dumps(list(BLOCK_WHY)) + ";\n"
              "export const FORMS = " + json.dumps(list(FORMS)) + ";\n"
              "export const WHY = " + json.dumps(list(WHY)) + ";\n")
        with open(path("door", "api", "_rules.js"), "w", encoding="utf-8") as f:
            f.write(js)
        print("wrote door/api/_rules.js")
    elif cmd == "check":
        w = normalise(json.load(open(sys.argv[2], encoding="utf-8")))
        bad = problems(w, Known())
        print("ok" if not bad else "\n".join(bad))
        sys.exit(1 if bad else 0)
    elif cmd == "invite" and len(sys.argv) > 2:
        invite(" ".join(sys.argv[2:]))
    elif cmd in ("confirm", "deny", "unclaim") and len(sys.argv) > 2:
        print(settle_claim(sys.argv[2].lower(), cmd))
        build()
    elif cmd == "veil" and len(sys.argv) > 2:
        x = veil(sys.argv[2].lower(), " ".join(sys.argv[3:]) or "steward")
        build()
        print("hidden:", x)
    elif cmd == "resolve" and len(sys.argv) > 3 and sys.argv[3] in ("removed", "restored"):
        p = "removals/x%05d.json" % int(sys.argv[2])
        x = load(p)
        x.update({"state": sys.argv[3], "resolved_at": today()})
        save(p, x)
        if sys.argv[3] == "removed" and ID_WING.match(x["id"]):
            tombstone(x["id"], "removed on request")
        build()
        print("settled:", x)
    else:
        sys.exit(__doc__)
