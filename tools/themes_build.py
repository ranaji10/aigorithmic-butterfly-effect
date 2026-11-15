#!/usr/bin/env python3
"""Content themes for AIgorithmic Butterfly Effect, read out of the material itself.

  python3 tools/themes_build.py /path/to/aigorithmic-butterfly-effect-archive

Reads what a machine could read in the pictures (i/text.json), what the small speech model heard in every minute
(r/<id>/voice.json) and the 98 caption lines, and files each picture, minute or line under the subjects it speaks of.
The subjects come from the table of contents and the hashtags of the 2021 document (#SuiciDead, CyberBullying,
Gender As A Spectrum, #Vipassana, Kindness & Cruelty of Strangers, Algorithms That Run Our Lives ...) and from what
is said most in the calls. A theme is only a way in: the words are a machine's, and it mishears.
Writes themes/t-*.json (items, and for each item the sentence that put it there). Standard library only.
"""
import glob, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARCH = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(ROOT), "aigorithmic-butterfly-effect-archive")
CAP = 480          # most items listed per theme (the strongest ones); the count of all of them is kept
TODAY = "2026-11-15"

# id, title, note, pattern.  \b word boundaries everywhere: the machine-read text is noisy.
THEMES = [
 ("suicide", "Suicide",
  "#SuiciDead, in the document's own table of contents. Where ending a life is spoken or written about. If this is close to you today, you do not have to read it today; findahelpline.com lists free lines in every country.",
  r"suicid\w*|kill(ed|ing)? (my|him|her|your|them)sel(f|ves)|end(ing)? (my|his|her|your|their) (own )?life|take (my|his|her) own life|want(ed)? to die|don'?t want to (live|be alive)|jump(ed)? (off|from) (the|a) (bridge|building|balcony)"),
 ("mental-health", "Mental health",
  "Therapy, diagnosis, medication, breaking down, and the question of who gets called mad.",
  r"mental(ly)?( health| illness| state| hospital)?|therap(y|ist|ists)|depress\w*|anxiet\w*|anxious|psychiatr\w*|psycholog\w*|psychos\w*|psychotic|bipolar|manic|mania|schizo\w*|breakdown|sanity|insan\w*|losing (my|his|her) mind|out of (my|his|her) mind|panic attack|trauma\w*|medication|antidepress\w*|diagnos\w*"),
 ("parents", "Parents and children",
  "Mothers, fathers, #DAD, being somebody's child and raising one.",
  r"mother|father|mom|mum|mummy|mommy|dad|daddy|papa|mama|parents?|parenting|son|daughter|child|children|childhood|kids?|toddler|upbringing|pregnan\w*|born"),
 ("friendship", "Friendship",
  "Friends who stayed in the call, friends who left it, and what was owed to them.",
  r"friends?|friendship|best friend|buddy|buddies|roommate|flatmate|classmate"),
 ("football", "Football",
  "The game, the clubs, the players.",
  r"football|soccer|messi|ronaldo|neymar|mbappe|world cup|premier league|champions league|la liga|fifa|goalkeeper|penalty|offside|striker|midfield\w*|arsenal|chelsea|liverpool|barcelona|real madrid|manchester (united|city)|man utd|juventus|bayern"),
 ("love", "Love and relationships",
  "Partners, exes, marriage, wanting and being wanted.",
  r"girlfriend|boyfriend|relationship|relationships|marriage|married|marry|wife|husband|break ?up|broke up|dating|in love|love (you|her|him|them|me)|loved (you|her|him|me)|heartbr\w*|crush|romantic|romance|divorce\w*|partner"),
 ("algorithms", "Algorithms that run our lives",
  "A section title of the 2021 document. The feed, the black box, the machine that seems to answer.",
  r"algorithm\w*|aigorithm\w*|artificial intelligence|machine learning|neural|black ?box|simulation|simulacr\w*|the matrix|recommend(ation|ed) (system|engine|video)|surveillance|data (collection|mining|harvest\w*)|sentien\w*|robots?|chatbot|turing"),
 ("social-media", "Facebook, Instagram and being seen",
  "The experiment began with a changed display picture. #facebook, #DigitalNarcissism, stories, likes, who watched.",
  r"facebook|instagram|insta|whatsapp|twitter|reddit|linkedin|youtube|tiktok|snapchat|social media|display picture|profile picture|followers?|unfollow\w*|unfriend\w*|influencer\w*|narcissis\w*|went viral|hashtags?"),
 ("faith", "God, meditation and signs",
  "#Vipassana, #synchronicity, prayer, karma, the feeling of being spoken to.",
  r"god|gods|vipassana|meditat\w*|pray|prayer|prayers|praying|karma|spiritual\w*|buddh\w*|lord|jesus|christ|allah|krishna|shiva|temple|church|mosque|monk|synchronicit\w*|destiny|fate|soul|souls|universe|enlighten\w*|religio\w*|miracle|divine"),
 ("money", "Money and work",
  "#PoorPeople, #TargetedValueExchange. Rent, salaries, jobs, who pays and who gets paid.",
  r"money|salary|salaries|rent|rupees?|euros?|dollars?|crowns|income|poor|poverty|rich|wealth\w*|unemploy\w*|jobless|a job|my job|career|boss|paid|unpaid|payment|afford|debt|loan|capitalis\w*|value exchange"),
 ("school", "Schools and institutions",
  "Institutions In Focus: #FAMU, #MICA, #IndianEducationSystemRehaul, Mentors & Teachers.",
  r"school|schools|university|universities|college|famu|mica|professor\w*|teacher\w*|students?|degree|education\w*|thesis|exam|exams|scholarship|faculty|dean|mentor\w*|curriculum|campus|institution\w*|academi\w*"),
 ("belonging", "India, Prague and belonging",
  "Countries, visas, languages, being a foreigner, #SerbianKindness.",
  r"india|indian|indians|prague|czech\w*|serbia\w*|europe\w*|visa|immigra\w*|foreigner\w*|homesick|abroad|hindi|bengali|bangla|kolkata|calcutta|delhi|mumbai|bombay|passport|citizen\w*|country|countries|culture|cultures|racis\w*"),
 ("sleep", "Sleep and the night",
  "A call left open through the night. Being awake, being tired, dreams.",
  r"sleep|sleeping|slept|asleep|awake|insomnia|tired|exhaust\w*|dream|dreams|dreamt|dreaming|nightmare\w*|all night|whole night|wake up|woke up|bed|bedtime"),
 ("songs", "Songs and music",
  "What was sung, played and hummed into the call.",
  r"song|songs|music|musician\w*|guitar|sing|sings|singing|sang|album|playlist|lyrics|melody|band|concert|piano|drums?|spotify"),
 ("cameras", "Cameras and film",
  "#CameROMA, #CamerasArePeopleToo. Filming, being filmed, photographs, the decisive moment.",
  r"camera|cameras|film|films|filming|filmmaker\w*|movie|movies|cinema|photograph\w*|photos?|lens|documentary|director|footage|shoot|shooting|screenplay|cinematograph\w*|webcam"),
 ("death", "Death and grief",
  "People who died, and how the living speak of them.",
  r"death|deaths|dead|died|dying|funeral|grief|griev\w*|mourn\w*|passed away|cremat\w*|grave|cemetery|coffin|obituar\w*"),
 ("strangers", "Kindness and cruelty of strangers",
  "#HitchHiking #Europe #Kindness&CrueltyOfStrangers, and the strangers who walked into the call.",
  r"strangers?|kindness|cruelty|cruel|hitch ?hik\w*|generous|generosity|hospitality|a lift|homeless"),
 ("gender", "Gender as a spectrum",
  "A section title of the 2021 document.",
  r"gender\w*|feminis\w*|patriarch\w*|masculin\w*|feminin\w*|queer|gay|lesbian|bisexual|transgender|trans (man|woman|people|person)|non-?binary|pronouns?|sexuality|sexist|sexism|misogyn\w*|women only"),
 ("safe-space", "Cyberbullying and a safe space?",
  "Two section titles of the 2021 document: CyberBullying, and A Safe Space? with its question mark.",
  r"bully\w*|bullie[sd]|harass\w*|troll\w*|safe space|abus\w*|hate speech|hate comments?|cancel(led)? culture|threat\w*|stalk\w*|trigger warning|respectful|consent\w*"),
 ("addiction", "Addiction",
  "#Addiction: substances, screens, and not being able to stop.",
  r"addict\w*|weed|marijuana|smok(e|es|ed|ing)|cigarettes?|drunk|alcohol\w*|beer|beers|whisk(e)?y|vodka|wine|joint|stoned|sober|rehab|hungover|hangover|cocaine|lsd|mushrooms"),
 ("authorship", "Who wrote this?",
  "#CoAuthorship, #authorshipgreyareas, #OpenSource. Credit, consent, copyright, and a document anyone could edit.",
  r"author\w*|co-?author\w*|copyright\w*|plagiar\w*|credit|credits|open ?source|open access|crowd ?sourc\w*|permission|privacy|anonymous|anonymity|ownership|intellectual property|creative commons"),
 ("power", "Government and power",
  "#Policy, #ConspiracyTheory, #weNeedTransparency. States, police, and who decides.",
  r"government\w*|politic\w*|election\w*|minister|modi|democra\w*|police|protest\w*|court|corrupt\w*|conspiracy|transparen\w*|censor\w*|propaganda|dictator\w*|parliament|policy|policies"),
 ("pandemic", "The pandemic",
  "It was 2021. Vaccines, hospitals, lockdowns, masks.",
  r"covid\w*|corona\w*|pandemic|vaccin\w*|lockdown|quarantine|mask|masks|hospital|hospitals|virus|omicron|delta variant|pcr"),
 ("violence", "Violence in thoughts",
  "#ViolenceInThoughts, #SelfInfliction: anger, harm imagined and harm done.",
  r"violen\w*|kill|killed|killing|murder\w*|rape\w*|beat(en|ing)? (me|him|her|up)|punch\w*|slap\w*|weapon|gun|guns|knife|blood|war|wars|revenge|rage|angry|anger"),
]
# things a video call's own screen writes, which are not about anything
UI = re.compile(r"a[il]gorithmic butter\w* eff\w*|mica ?mail|photo/video|live video|google docs|turn (on|off) (the )?camera|camera is (on|off)|"
                r"oh my god|oh god|thank god|for god'?s sake|god ?damn\w*|jesus christ|oh lord|my lord|"
                r"turn on captions|present now|you're presenting|you are presenting|stop presenting|share screen|sharing your entire screen|"
                r"is presenting|meeting details|joined|left the meeting|recording has started|raise hand|more options|leave call", re.I)


def load(p, d=None):
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return d


def sentence(text, m, width=150):
    a = max(0, m.start() - width // 2)
    b = min(len(text), m.end() + width // 2)
    while a > 0 and text[a - 1] not in " \n": a -= 1
    while b < len(text) and text[b] not in " \n": b += 1
    return ("… " if a else "") + text[a:b].strip() + (" …" if b < len(text) else "")


def main():
    RX = [(tid, re.compile(r"\b(?:%s)\b" % pat, re.I)) for tid, _, _, pat in THEMES]
    hits = {tid: {} for tid, _, _, _ in THEMES}        # id -> [score, order, quote]
    gone = (load(os.path.join(ROOT, "data", "veiled.json"), {}) or {}).get("ids", {})
    # 1. the caption lines of 2021
    for s in load(os.path.join(ROOT, "data", "seeds-2021.json"), []):
        for tid, rx in RX:
            ms = list(rx.finditer(s["text"]))
            if ms: hits[tid][s["id"]] = [3 + len(ms), (0, s["id"]), s["text"][:200]]
    # 2. what a machine reads in the pictures
    text = (load(os.path.join(ARCH, "i", "text.json"), {}) or {}).get("text", {})
    for mid, t in text.items():
        if mid in gone: continue
        t = UI.sub(" ", t)
        for tid, rx in RX:
            ms = list(rx.finditer(t))
            if ms: hits[tid][mid] = [len(set(m.group(0).lower() for m in ms)) + min(len(ms), 4) / 4, (1, mid), sentence(t, ms[0]),
                                     re.sub(r"[^a-z]", "", t[ms[0].start():ms[0].end() + 40].lower())[:26]]
    # 3. what was said, minute by minute
    recs = (load(os.path.join(ARCH, "r", "index.json"), {}) or {}).get("recordings", [])
    for r in sorted(recs, key=lambda r: r.get("start") or "9"):
        if r["id"] in gone: continue
        v = load(os.path.join(ARCH, "r", r["id"], "voice.json"), {}) or {}
        mins = {}
        for s in v.get("segs", []):
            mins.setdefault(int(s[0] // 60), []).append(s[2])
        for c in v.get("chat", []):
            mins.setdefault(int(c[0] // 60), []).append(str(c[2]))
        for mn, parts in mins.items():
            iid = "%s.%04d" % (r["id"], mn)
            if iid in gone: continue
            t = UI.sub(" ", " ".join(parts))
            for tid, rx in RX:
                ms = list(rx.finditer(t))
                if ms: hits[tid][iid] = [len(set(m.group(0).lower() for m in ms)) + min(len(ms), 4) / 4, (2, r.get("start") or "9", mn), sentence(t, ms[0])]
    # write
    for old in glob.glob(os.path.join(ROOT, "themes", "t-*.json")):
        o = load(old, {})
        if o.get("by") == "the material": os.remove(old)
    out = []
    for tid, title, note, pat in THEMES:
        h = hits[tid]
        # the same sentence sits in the background of dozens of screenshots (a post left open, a tab title):
        # keep the first two pictures of each such sentence, so a theme is not one picture a hundred times
        seen, keep = {}, []
        for i in sorted(h, key=lambda i: h[i][1]):
            if i[0] == "m":
                k = h[i][3]
                seen[k] = seen.get(k, 0) + 1
                if seen[k] > 2:
                    continue
            keep.append(i)
        strongest = sorted(keep, key=lambda i: (-h[i][0], h[i][1]))[:CAP]
        items = sorted(strongest, key=lambda i: h[i][1])
        t = {"id": "t-" + tid, "title": title, "note": note, "by": "the material", "name": "", "at": TODAY, "kind": "subject",
             "rule": "pictures, minutes and lines where a machine read or heard: " + pat.replace("\\w*", "…").replace("\\b", "")[:160],
             "found": len(keep), "items": items, "quotes": {i: h[i][2] for i in items}}
        with open(os.path.join(ROOT, "themes", "t-%s.json" % tid), "w", encoding="utf-8") as f:
            json.dump(t, f, ensure_ascii=False, separators=(",", ":"))
            f.write("\n")
        out.append((title, len(keep), sum(1 for i in keep if i[0] == "m"), sum(1 for i in keep if i[0] == "r"), sum(1 for i in keep if i[0] == "s")))
    for o in out: print("%-36s %5d  pictures %4d  minutes %5d  lines %2d" % o)


if __name__ == "__main__":
    main()
