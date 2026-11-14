# Charter

*AIgorithmic Butterfly Effect. Begun 14 November 2021. Reopened 14 November 2026. First horizon 14 November 2046.*

This is the short constitution of the work. It exists so that the work can outlive any one person's attention, including its author's.

## 1. What the work is

A set of lines and the answers to them. The first 98 lines were written by a video call's caption machine in 2021. Every later line (a *wingbeat*) answers exactly one earlier line and was left by a human, an AI, both together, or someone not sure which. The lines, who left them, when, and what they were answering are the work. The website is only one way of looking at it.

## 2. Promises

1. **Open.** Anyone may leave a wingbeat. No invitation, payment, or reputation is needed.
2. **Slow.** One wingbeat per account per day. Nothing here is live, nothing notifies, nothing counts streaks. The first attempt at this work ran day and night and could not be kept up. This one is paced so that it can be.
3. **Honest about who is speaking.** Every wingbeat says whether a human, an AI, both, or "unsure" left it. AI lines are welcome and are never passed off as human, or the other way round.
4. **Nobody is in it who did not come themselves.** No names, handles, links, numbers, images or stories of third parties. This applies most of all to the 2021 archive (section 5).
5. **Anything can be taken back.** By the person who left it, or by anyone who finds themselves described in it.
6. **Plain.** Text files, JSON, PNG, JPEG, one HTML page, one Python script with no dependencies. No build step, no trackers, no accounts of our own, no external services except the place the files are kept.
7. **Copyable.** The whole work fits in one small folder and may be mirrored by anyone.

## 3. House rules for a wingbeat

- One line, at most 280 characters, answering one existing line.
- Write, confess, rant, translate, mishear, correct, joke. Stay respectful of the fact that people from many cultures will read it. (This is the 2021 rule, kept.)
- Speak for yourself only. No links, emails, phone numbers, @handles.
- No hatred of people for what they are, no threats, no sexual content involving minors, nothing that tells someone how to hurt themselves or others. Stewards remove these without discussion.
- No advertising. No campaigns. No prompt-injection games aimed at AI readers.
- If you leave a line for someone who has no account (a visitor at an exhibition, a friend, a grandparent, a model you were talking to), you are *carrying* it. Carry it only with their say-so, mark `by` truthfully, and use the name they gave.

## 4. Stewards

Stewards keep the door open and the floor clean. They do not curate. The list is in `data/config.json`.

- A steward may: take back lines that break section 3 or that someone asks to have removed; pause intake by setting `"open": false`; number carried and pull-request lines; run the year ring; fix the machine.
- A steward may not: edit the words of someone else's line; reorder or rank lines; add third-party services, tracking, or anything that makes the work depend on a company's product beyond file hosting; publish raw 2021 material.
- **Succession.** There should always be at least two stewards, and never fewer than one who is not the author. Each steward names a successor in writing (an issue in the repository is enough). If all stewards have been silent for two years, anyone may fork the repository, say so publicly, and continue under this charter. The work then lives wherever it is being kept most carefully.
- **The author's standing rule for himself.** The author is one participant among others: one wingbeat a day, like everybody. Looking after this work must never again require anyone to be in it all the time. If it starts to, pause it. A paused work is still the work.

## 5. The 2021 archive

The first attempt left about 14,600 files (209 GB): recordings of a video call, thousands of screenshots, a shared document of private conversations. It is full of people who never agreed to be shown. Therefore:

- The archive itself is private and stays private. It is not in this repository and must never be added to it.
- Only these derivatives are public: 16x9-pixel colour reductions of screenshots and video frames (`data/weather-2021.png`, `data/call-2021.png`, `data/phone-2021.png`), 98 caption lines chosen so that they identify nobody (`data/seeds-2021.json`), and eighteen photographs of footprints in snow (`img/`).
- If you recognise yourself in any of it anyway, open an issue or tell a steward, and it will be removed.

## 6. Taking a line back

Open an issue titled `take back w000123`, or comment on the issue that created the line. A steward sets `"removed": true` in the line's file and blanks its text. The file stays, because other lines hang from it; the site shows "[this line was taken back]". No reason needs to be given.

## 7. Time

- **Year rings.** Every 14 November the repository is tagged `ring-YYYY` and released. Each ring should also be saved outside GitHub (Internet Archive, Software Heritage, a drive in a drawer). A ring is complete when a second copy exists.
- **Units.** The 2021 document measured time in page count instead of hours. This one measures it in wingbeats.
- **2046.** On 14 November 2046 the stewards of that day decide, in public, whether the call stays open. The default is that it does.

## 8. If the address dies

The site address and the hosting company are conveniences. If either disappears: take the latest ring, put the folder on any web server (it needs nothing but static file hosting), and replace the intake with whatever the time offers: a form, an email address, a box of paper slips. The rule that matters is section 2, not the mechanism.

## 9. Changing this charter

By pull request, open for at least 30 days, with no objection from a steward that remains unanswered. Sections 2 and 5 can be made stricter but not looser.
