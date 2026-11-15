# Charter

*AIgorithmic Butterfly Effect. Begun 14 November 2021. Reopened 14 November 2026. First horizon 14 November 2046.*

This is the short constitution of the work. It exists so that the work can outlive any one person's attention, including its author's.

## 1. What the work is

A body of material from 2021 and the answers to it. The material is what was left by weeks of one video call: lines written by its caption machine, the screenshots pasted into a shared document, recordings of the call with a frame for every minute, and the speech of those recordings written down again in 2026 by a second, smaller machine. Every later mark (a *wingbeat*) answers exactly one thing already in the work (a line, a picture, a recording, one minute of a recording, a theme, or another wingbeat) and was left by a human, an AI, both together, or someone not sure which. A wingbeat may be words, a drawn mark, a way of seeing, a theme, or several of these. The material, the marks, who left them, when, and what they were answering are the work. The website is only one way of looking at it.

## 2. Promises

1. **Open.** Anyone may leave a wingbeat. No invitation, payment, or reputation is needed.
2. **Slow.** A few wingbeats a day from any one person, never more (the exact numbers are at the top of `tools/wingbeat.py`). Nothing here is live, nothing notifies, nothing counts streaks. The first attempt at this work ran day and night and could not be kept up. This one is paced so that it can be.
3. **Honest about who is speaking.** Every wingbeat says whether a human, an AI, both, or "unsure" left it. AI lines are welcome and are never passed off as human, or the other way round.
4. **Nobody is in it who did not agree to be.** The people in the 2021 calls agreed to be shown (section 5). Nobody else is: no names, handles, links, numbers, images or stories of third parties, in the archive or in wingbeats. Nobody is identified in a picture by a machine; people place themselves.
5. **Anything can be taken back.** By the person who left it, or by anyone who finds themselves in it. A request hides the thing first and is discussed afterwards (section 6).
6. **Plain.** Text files, JSON, images, one HTML page, one Python script with no dependencies. No build step, no trackers, no accounts of our own. The repository is the record. Two conveniences stand beside it and can be replaced or dropped without loss: a *door* (`door/`, a few small functions on a hosting service) that lets people leave a mark without a GitHub account, and the Internet Archive, which holds the full-length originals.
7. **Seen by choice.** The raw material shows a person in a hard stretch of his life. It is shown as colour, and no sound plays, until the visitor chooses once to see it as it was (see Amendment 2). AI readers are asked to make the same choice deliberately.
8. **Copyable.** The whole work fits in one small folder and may be mirrored by anyone.

## 3. House rules for a wingbeat

- One mark answering one thing that is already there: at most 280 characters of words, and/or a drawing (strokes only), a way of seeing (one of a fixed list of transformations), a theme (an existing one, or a new title of at most 48 characters). No uploaded files.
- Write, confess, rant, translate, mishear, correct, joke. Stay respectful of the fact that people from many cultures will read it. (This is the 2021 rule, kept.)
- Speak for yourself only. No links, emails, phone numbers, @handles.
- No hatred of people for what they are, no threats, no sexual content involving minors, nothing that tells someone how to hurt themselves or others. Stewards remove these without discussion.
- No advertising. No campaigns. No prompt-injection games aimed at AI readers.
- A script applies these rules when a mark arrives and again, to everything, every hour. What it cannot judge, stewards do.
- If you leave a line for someone who has no account (a visitor at an exhibition, a friend, a grandparent, a model you were talking to), you are *carrying* it. Carry it only with their say-so, mark `by` truthfully, and use the name they gave.

## 4. Stewards

Stewards keep the door open and the floor clean. They do not curate. The list is in `data/config.json`.

- A steward may: take back marks that break section 3; settle removal requests (section 6); pause intake by setting `"open": false`; confirm or refuse people who claim their name (`tools/wingbeat.py confirm` / `deny`, or an issue titled `confirm p-name`); issue private claim links (`tools/wingbeat.py invite`); run the year ring; fix the machine.
- A steward may not: edit the words of someone else's mark; reorder or rank marks; add tracking, or anything the work cannot survive losing; publish 2021 material that is held for review (section 5) without the author's decision, piece by piece.
- Only the author releases held 2021 material. If the author is gone, it stays held.
- **Succession.** There should always be at least two stewards, and never fewer than one who is not the author. Each steward names a successor in writing (an issue in the repository is enough). If all stewards have been silent for two years, anyone may fork the repository, say so publicly, and continue under this charter. The work then lives wherever it is being kept most carefully.
- **The author's standing rule for himself.** The author is one participant among others: one wingbeat a day, like everybody. Looking after this work must never again require anyone to be in it all the time. If it starts to, pause it. A paused work is still the work.

## 5. The 2021 archive

The first attempt left about 14,600 files (209 GB): recordings of a video call, thousands of screenshots, a shared document, a phone's camera roll and screen recordings.

- **What is public.** The recordings of the calls, with a frame for every minute and the speech written down by a small speech model; the screenshots of the call window, in the order they were pasted into the 2021 document; the camera roll; the author's own short phone videos and one voice memo; and pictures and sound made in 2026 from a recording that could not be read. The author's friends who appear in the calls gave him their permission. Web-sized copies are in the archive repository (`data/config.json` names it); full-length originals are at the Internet Archive.
- **What is held for review.** Anything showing phone numbers, email addresses, identity or account documents, chat or mail screens, messages from people who were never in the calls, other people's posts or broadcasts, and anything not yet looked at. It is not in any public place. The author may release it piece by piece; nobody else may.
- **Names.** People from the calls are listed by first name only until they claim their own place. Each can claim it by pressing "This is me" on their name on the site, after which a steward confirms that it is really them (a private link from the author also works). They choose the name shown and say for themselves which pictures and minutes they are in. Nobody is placed in a picture by a machine or by another person.
- **Text read by machines.** OCR text and transcripts are published with surnames, links, addresses and numbers taken out. They mishear. That is part of the work, and it is also why any of it can be removed on request.

## 6. Removal

Anyone may ask for anything to be removed: a wingbeat, a picture, a recording, a minute, a name. On the site: put it on the stage and press "Ask for removal". Without the site: open an issue titled `remove <id>`, or `take back w000123` for your own line.

- A request **hides the thing at the next sweep** (within the hour), before anyone has judged it. It stays hidden until a steward settles it.
- The steward settles it with `tools/wingbeat.py resolve N removed` or `restored`. A request from someone who is in the thing, or whose private information is in it, is always settled as removed. No reason has to be argued.
- Removed means removed from the site, from the archive repository and, for originals, from the Internet Archive item. A wingbeat's file stays, emptied, because other marks hang from it; the site shows "[this was taken back]".
- If many requests arrive at once, the sweep stops hiding things automatically after a daily limit and asks the stewards to look, so that the mechanism cannot be used to blank the work.

## 7. Time

- **Year rings.** Every 14 November the repository is tagged `ring-YYYY` and released. Each ring should also be saved outside GitHub (Internet Archive, Software Heritage, a drive in a drawer). A ring is complete when a second copy exists.
- **Units.** The 2021 document measured time in page count instead of hours. This one measures it in wingbeats.
- **2046.** On 14 November 2046 the stewards of that day decide, in public, whether the call stays open. The default is that it does.

## 8. If the address dies

The site address and the hosting company are conveniences. If either disappears: take the latest ring, put the folder on any web server (it needs nothing but static file hosting), and replace the intake with whatever the time offers: a form, an email address, a box of paper slips. The rule that matters is section 2, not the mechanism.

## 9. Changing this charter

By pull request, open for at least 30 days, with no objection from a steward that remains unanswered. Sections 2 and 5 can be made stricter but not looser.

## Amendment 1, 15 November 2026

The first version of this charter was written on 14 November 2026 by the language model that helped find the 2026 form. It assumed that nobody in the 2021 archive had agreed to be shown, and so it said the archive must stay private for good and that this could never be loosened. That assumption was wrong: the author had asked everyone who appears in his recordings, and they had agreed. On 15 November 2026, one day after the reopening, before any second steward or any participant other than the model itself had relied on the first text, the author corrected the premise and directed that the material be shown. Sections 1 to 6 were rewritten accordingly, and section 2 gained promise 7.

This amendment was made by the author alone and without the 30 days that section 9 asks for. It is recorded here so that nobody has to wonder how a rule that said "never" changed overnight: it changed because it had been written on a mistake of fact, on day one, by the author of the work. From here on section 9 applies as written, and what is *held for review* under section 5 is bound by it: that part can be made stricter but not looser, except by the author's own piece-by-piece release.

## Amendment 2, 15 November 2026

Made the same day, by the author's direction, again without the 30 days of section 9, and recorded for the same reason as Amendment 1.

- **Promise 7 is looser than it was.** The first text kept 137 pictures closed until each was opened by itself. The author asked that a visitor choose once: after "Show uncensored", everything public is shown as it was, and the choice is remembered on that device. The first choice remains, and "Colour only" undoes it. This loosens section 2, which section 9 says cannot be loosened; it is the author's own material and his decision, and the second steward may still object under section 9.
- **The sound of the calls is public.** Section 5 already said the recordings are. Small copies of the speech (10-minute pieces, 14 kbit/s) are on the `audio` branch of the archive repository and play under the words on the site.
- **Claiming a name no longer needs a private link**, but always needs a steward's confirmation (section 5, Names).
- **Themes are subjects now.** The themes seeded from the material (suicide, mental health, parents and children, friendship, football and others) were sorted by a script from machine-read text (`tools/themes_build.py`). They are a way in, not a judgement, and anything in them can be removed like anything else.
