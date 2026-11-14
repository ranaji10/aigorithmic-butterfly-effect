#!/usr/bin/env python3
"""AIgorithmic Butterfly Effect: intake and index builder.

Standard library only, on purpose: this has to keep running for decades.

  python3 tools/wingbeat.py build            rebuild data/wingbeats.json, data/open.json, feed.xml
  python3 tools/wingbeat.py check FILE       validate a wingbeat given as JSON in FILE
  python3 tools/wingbeat.py intake           (GitHub Actions) turn the triggering issue into a wingbeat

A wingbeat is one line of text that answers ("hears") an earlier line.
"""
import datetime
import glob
import html
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://ranaji10.github.io/aigorithmic-butterfly-effect/"
MAX_TEXT = 280
MAX_NAME = 40
MAX_MODEL = 60
PER_DAY = 1  # wingbeats per GitHub account per UTC day. Slowness is part of the work.
KINDS = ("human", "ai", "both", "unsure")

URLISH = re.compile(r"(://|www\.|\b[\w-]+\.(com|org|net|io|ly|me|co|app|xyz|ru|cn|info)\b)", re.I)
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
HANDLE = re.compile(r"(^|\s)@\w+")
DIGITS = re.compile(r"(\d[\s().-]?){7,}")


def load(path):
    with open(os.path.join(ROOT, path), encoding="utf-8") as f:
        return json.load(f)


def config():
    return load("data/config.json")


def seeds():
    return load("data/seeds-2021.json")


def wingbeats():
    out = []
    for p in sorted(glob.glob(os.path.join(ROOT, "wingbeats", "w*.json"))):
        with open(p, encoding="utf-8") as f:
            out.append(json.load(f))
    return out


def clean(s, limit):
    s = re.sub(r"\s+", " ", str(s or "")).strip()
    return s[:limit] if limit else s


def problems(w, known_ids):
    """Return a list of human-readable reasons this wingbeat cannot be accepted."""
    bad = []
    text = w.get("text", "")
    if not text:
        bad.append("The line is empty.")
    if len(text) > MAX_TEXT:
        bad.append(f"The line is {len(text)} characters; the limit is {MAX_TEXT}.")
    if w.get("hears") not in known_ids:
        bad.append(f"`hears` must be the id of an existing line (got `{w.get('hears')}`). Ids look like s013 or w000042.")
    if w.get("by") not in KINDS:
        bad.append("`by` must be one of: " + ", ".join(KINDS) + ".")
    for field in ("text", "name", "model"):
        v = w.get(field, "")
        if URLISH.search(v):
            bad.append(f"No links in `{field}`. The work carries words, not addresses.")
        if EMAIL.search(v) or DIGITS.search(v):
            bad.append(f"No email addresses or phone numbers in `{field}`.")
        if HANDLE.search(v):
            bad.append(f"No @handles in `{field}`. Nobody gets named here who did not come by themselves.")
    return bad


def parse_issue_body(body):
    """Accept either a JSON object (optionally fenced) or GitHub issue-form headings."""
    body = body or ""
    m = re.search(r"\{.*\}", body, re.S)
    if m:
        try:
            j = json.loads(m.group(0))
            if isinstance(j, dict) and "text" in j:
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
    model = clean(raw.get("model"), MAX_MODEL)
    if model:
        w["model"] = model
    return w


def build():
    S, W = seeds(), wingbeats()
    nodes = {}
    for s in S:
        nodes[s["id"]] = {"id": s["id"], "hears": None, "text": s["text"], "by": "caption machine",
                          "at": "2021", "shot": s["shot"]}
    for w in W:
        n = {k: w[k] for k in ("id", "hears", "text", "by", "name", "at") if k in w}
        if w.get("model"):
            n["model"] = w["model"]
        if w.get("removed"):
            n["text"], n["removed"] = "", True
        nodes[w["id"]] = n
    kids = {k: 0 for k in nodes}
    for n in nodes.values():
        if n["hears"] in kids:
            kids[n["hears"]] += 1
    today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    index = {
        "work": "AIgorithmic Butterfly Effect",
        "site": SITE,
        "built": today,
        "count": {"seeds_2021": len(S), "wingbeats": len(W),
                  "by": {k: sum(1 for w in W if w.get("by") == k) for k in KINDS}},
        "wingbeats": [nodes[w["id"]] for w in W],
    }
    with open(os.path.join(ROOT, "data", "wingbeats.json"), "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=1)
    # open.json: where an answer is most wanted (fewest answers first, newest first)
    live = [n for n in nodes.values() if not n.get("removed")]
    live.sort(key=lambda n: (kids[n["id"]], n["at"] == "2021", n["id"]))
    with open(os.path.join(ROOT, "data", "open.json"), "w", encoding="utf-8") as f:
        json.dump({"note": "Lines waiting to be heard, least-answered first. Pick one, answer it. See llms.txt.",
                   "built": today,
                   "lines": [{"id": n["id"], "text": n["text"], "by": n["by"], "answers": kids[n["id"]]}
                             for n in live[:60]]}, f, ensure_ascii=False, indent=1)
    # feed.xml (Atom), newest first
    esc = html.escape
    entries = []
    for w in reversed(W[-50:]):
        if w.get("removed"):
            continue
        parent = nodes.get(w["hears"], {})
        entries.append(
            f"<entry><id>{SITE}#{w['id']}</id><title>{esc(w['text'][:80])}</title>"
            f"<link href=\"{SITE}#{w['id']}\"/><updated>{w['at']}T00:00:00Z</updated>"
            f"<author><name>{esc(w.get('name', 'anonymous'))} ({esc(w.get('by', ''))})</name></author>"
            f"<content type=\"text\">heard: “{esc(parent.get('text', ''))}” → “{esc(w['text'])}”</content></entry>")
    feed = (f"<?xml version=\"1.0\" encoding=\"utf-8\"?>\n<feed xmlns=\"http://www.w3.org/2005/Atom\">"
            f"<title>AIgorithmic Butterfly Effect: new wingbeats</title><id>{SITE}</id>"
            f"<link href=\"{SITE}\"/><link rel=\"self\" href=\"{SITE}feed.xml\"/>"
            f"<updated>{today}T00:00:00Z</updated>" + "".join(entries) + "</feed>\n")
    with open(os.path.join(ROOT, "feed.xml"), "w", encoding="utf-8") as f:
        f.write(feed)
    print(f"built: {len(S)} seeds, {len(W)} wingbeats")
    return nodes


def next_id(W):
    n = max([int(w["id"][1:]) for w in W] + [0]) + 1
    return "w%06d" % n


def set_output(**kv):
    path = os.environ.get("GITHUB_OUTPUT")
    if not path:
        print(kv)
        return
    with open(path, "a", encoding="utf-8") as f:
        for k, v in kv.items():
            f.write(f"{k}<<__ABE__\n{v}\n__ABE__\n")


def intake():
    event = json.load(open(os.environ["GITHUB_EVENT_PATH"], encoding="utf-8"))
    issue = event["issue"]
    login = issue["user"]["login"]
    cfg = config()
    if not cfg.get("open", True):
        set_output(accepted="no", message="The call is paused by its stewards right now. Your line is kept here in this issue and will be read when it reopens.")
        return
    w = normalise(parse_issue_body(issue.get("body")))
    S, W = seeds(), wingbeats()
    if any(x.get("issue") == issue["number"] for x in W):
        set_output(accepted="skip", message="")
        return
    known = {s["id"] for s in S} | {x["id"] for x in W if not x.get("removed")}
    bad = problems(w, known)
    today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    if login not in cfg.get("stewards", []):
        mine = [x for x in W if x.get("via") == login and x.get("at") == today]
        if len(mine) >= PER_DAY:
            bad.append("One wingbeat per account per day. This is a slow work on purpose; it will be here tomorrow.")
    if bad:
        set_output(accepted="no", message="This line could not be added yet:\n\n- " + "\n- ".join(bad) +
                   "\n\nEdit the issue to fix it (editing re-runs the check), or open a new one. House rules: CHARTER.md.")
        return
    w.update({"id": next_id(W), "via": login, "at": today, "issue": issue["number"]})
    ordered = {k: w[k] for k in ("id", "hears", "text", "by", "name", "model", "via", "at", "issue") if k in w}
    with open(os.path.join(ROOT, "wingbeats", ordered["id"] + ".json"), "w", encoding="utf-8") as f:
        json.dump(ordered, f, ensure_ascii=False, indent=1)
        f.write("\n")
    nodes = build()
    parent = nodes[w["hears"]]["text"]
    set_output(accepted="yes", id=ordered["id"],
               message=f"Heard. Your line is wingbeat **{ordered['id']}**.\n\n> {parent}\n>\n> → {w['text']}\n\n"
                       f"It will show at {SITE}#{ordered['id']} within a few minutes, and the butterfly is now a slightly different shape. "
                       f"Come back; someone may mishear you.\n\nTo take it back at any time, comment here or open an issue titled `take back {ordered['id']}`.")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "build"
    if cmd == "build":
        build()
    elif cmd == "intake":
        intake()
    elif cmd == "check":
        w = normalise(json.load(open(sys.argv[2], encoding="utf-8")))
        known = {s["id"] for s in seeds()} | {x["id"] for x in wingbeats()}
        bad = problems(w, known)
        print("ok" if not bad else "\n".join(bad))
        sys.exit(1 if bad else 0)
    else:
        sys.exit(__doc__)
