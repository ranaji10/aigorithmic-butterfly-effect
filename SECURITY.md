# Security

This is an artwork that strangers, human and machine, can write into without an account. That is the point of it, and it is also the whole attack surface. This page says how the work is defended, what is knowingly left open, and what to do if you find a hole.

## If you find a hole

- Something that lets a person's private information stay visible, lets someone speak as a person from the 2021 calls, or lets the work be blanked or defaced: **do not open a public issue with the details.** Use *Security > Report a vulnerability* on the repository if it is offered, or open an issue titled `security` that says only that you have something to report and how to reach you. A steward answers.
- Something that is in the work and should not be (a name, a picture, a line): that is not a security report, it is a removal request, and it is faster. Put the thing on the stage and press the flag, or open an issue titled `remove <id>`. It is hidden first and discussed afterwards (charter, section 6).

There is no bounty. There is a place in the credits if you want one.

## What is being protected

1. **People.** Nobody is shown who did not agree, nobody is named by a machine, and anything can be taken back (charter, sections 2, 5, 6). The "✓ who was there" on a mark must mean a steward confirmed that person.
2. **The record.** Which marks came from whom, when, answering what. Nobody edits another's mark; removals leave an emptied place.
3. **The floor.** No links, addresses, handles, hatred, threats, advertising or games aimed at AI readers reach the page.
4. **Staying open and slow.** One visitor, or one bad day, must not be able to blank the work, flood it, or close the door for everybody else.

## How

**Two readings.** Every mark is checked at the door (`door/api/_lib.js`) and again in the repository (`tools/wingbeat.py`) before it gets a number, and everything already in the work is re-read on every sweep against the current rules. The repository's reading is the one that counts; the door's is a courtesy that gives a fast answer.

**What a mark may contain.** At most 280 characters of visible text, strokes made of whole numbers, a theme title of at most 48 characters. No files. Links, e-mail addresses, long digit runs and @handles are refused, also when written in full-width or other look-alike letters. Characters nobody can see (controls, direction overrides, zero-width marks, blank fillers, the Unicode tag block) are stripped on arrival and a stored line that carries one is taken back: they are how instructions are hidden from people and shown to machines.

**Limits, all counted in the repository.** Per visitor per day at the door (5), per GitHub account per day (3), for the door as a whole (300, after which the call pauses itself and tells the stewards). A visitor is a salted hash of their network address that changes daily and cannot be turned back into the address; one IPv6 /64 counts as one visitor. Removal requests hide a thing at once only for the first 3 per visitor and the first 30 per day, door and GitHub together; after that they are recorded for a steward, and after 200 in a day they wait where they were left. One request hides at most 30 minutes of one recording (the minute asked for and the others its asker says they had on the stage; nobody can check what somebody looked at, hence the ceiling). A request for a whole recording, or for a thing a steward has restored before, hides nothing: it is recorded and waits for a steward, so that neither one request nor a patient visitor can take back what a steward has decided (Amendment 13). A name can be asked for or claimed through the door a few times a day at most.

**The page.** `index.html` carries a Content-Security-Policy: no script from anywhere but the page itself, no handlers in markup, no frames, and pictures, sound and requests only to the places it names. Text from marks, transcripts and the 2021 document is written into the page as text or through one escape function. Inside someone else's frame the page can be looked at but sends nothing. No cookies, no analytics, no third-party code, no referrer.

**The door.** A few small functions with one dependency (pinned by `door/package-lock.json`). It keeps marks in a waiting room of at most 1,000 small files, answers `GET /api/inbox` from a one-minute memory, and takes at most 10 MCP messages in a batch. Its search (`POST /api/find`, and `search` over MCP) reads only what is public already, keeps, logs and counts no question, refuses a question in an address, answers at most 600 a day per visitor, and matches with plain string search and one fixed pattern per word, so no question can make it think for long (the slowest found in the review of 21 November 2026 took a fifth of a second). A body that is not an object is an empty request. It never returns the reason for an internal error. It holds no key to the repository: it cannot publish anything, only wait to be read.

**The workflows.** They run only code from the main branch, on events that cannot bring a stranger's code with them (issues, schedule, push). Nothing a stranger wrote is pasted into a shell line. The built-in token is the only credential; `actions/checkout` is pinned to a commit. Output handed from the script to the workflow uses a fresh random delimiter each time.

**The clock.** The hourly sweep is started from outside GitHub by a small scheduled function (`tools/sweep_clock.js`, running in the author's Cloudflare account), because GitHub's own schedule drops most runs. It takes no input (its address answers 404) and holds one credential: a GitHub token limited to this repository and to its workflows. That token cannot push, cannot read anything that is not public already, and cannot change what a workflow does.

## Knowingly left open

- **The answer to the stewards' question is sealed, not secret from the stewards' devices.** "Write something that only Rana and <name> will know" is encrypted in the claimant's browser (ECDH on P-256 with a one-time key, then AES-GCM) to the public key in `data/config.json`. The door's waiting room, the repository and the stewards' issue are all public and hold only the sealed text. Whoever holds the stewards' private key can read every answer that is still waiting; it lives in a file the author keeps and in the browser storage of the devices where a steward pasted it. An answer is deleted from `people/p-*.json` when the claim is confirmed or denied (it stays, sealed, in the git history).
- **Names are looked after, not proven.** A mark signed with a first name from `people/` (or the author's) is kept and shown with "name not confirmed" until a steward has confirmed the person (`name_unconfirmed` in `data/wingbeats.json`, set by `tools/wingbeat.py` at every build). The check reads every word of the name and all its letters run together, after folding full-width and upper-case letters; a name written with look-alike letters from another alphabet still passes unmarked. The ✓ remains the only thing that means a steward confirmed someone.
- **"This is me" can be squatted.** Anyone can ask for a name; it stays pending, and blocks others, until a steward denies it. A steward sees every request. Six names a day are taken in; when more arrive, the stewards are told once that a request is waiting.
- **One name for one device is a courtesy.** The page offers a device that holds or awaits a name no second one, but another browser is a stranger: the work has no accounts and the door cannot tell two devices of one person apart. A device that waits for a steward already sees the screenshots and recordings listed under the name it asked for (the author's decision, kept on 22 November 2026), and the index of where each name was read is a public file of the archive repository, like the pictures it lists. What cannot be had this way is the ✓: only a steward's confirmation gives it.
- **The clock's token.** It is kept as an encrypted secret of the clock and nowhere else. Whoever got hold of it could start any workflow of this repository by hand, switch workflows off, or cancel runs; the one start that could not be taken back is a real year ring. It has an end date: when it runs out the clock stops without a sound, and the sweep falls back to GitHub's slow schedule until the author replaces it (`AGENTS.md`, The clock).
- **The door is trusted about who proved a private link.** See `AGENTS.md`: retire the door's address in `data/config.json` before the hosting project.
- **A determined crowd can fill a day.** Three hundred marks from three hundred places pauses the call until a steward reopens it. That is the design: closed and intact rather than open and flooded.
- **The filter is a short list of patterns**, not a judge. It will miss things, and stewards remove what it misses (charter, section 3).
- **The history of the archive repository keeps what was taken out.** Hiding, removing or masking a picture or a recording changes what the site and the archive's pages serve. The file as it was stays in the git history of the archive repository, where anyone who knows the commit can still fetch it, and a copy of an original that was sent to the Internet Archive stays there. For most removals that is accepted. For something that must be gone for good, see "Taking something out for good" below; it is a steward's decision, it cannot be undone, and it has not been done so far.
- **The censoring on the site is a warning, not a lock.** It spares a visitor the material as it was until they ask for it. Everything public is in the archive repository and its index for anyone who reads those directly.

Settled since the first review: the door's storage client is on its 2.x line (2.4.0, pinned); the main branch and the archive's branches can no longer be force-pushed or deleted, and a `ring-*` tag can never be moved (repository rules, 16 November 2026).

## For stewards: taking something out for good

The work's own repository is never rewritten: its history is the work. The archive repository holds media, and a file that must not exist anywhere (a stranger's private details published by mistake, say) can be cut out of its history. This is the only case in which that is right, and only the author decides it.

    # 1. remove the file in the ordinary way first (and its words: tools/veil_text.py), push, let the pages deploy
    # 2. in a fresh full clone of the archive repository:
    git filter-repo --invert-paths --path i/w/m01234.webp --path i/t/m01234.webp     # every path the thing ever had
    # 3. the author lifts the rule "no force-push" on the archive's main for the length of one push, then:
    git push --force origin main          # and the same for the branch `audio` if sound is concerned
    # 4. put the rule back. Ask GitHub Support to clear cached views of the old commits (they keep them otherwise).
    # 5. if an original went to the Internet Archive: delete the file from its item there (the author's account).
    # 6. every clone and fork made before this still has the file. Say so in removals/ where the removal is recorded.

Do this before a year ring is cut and before the archive repository is sent to Software Heritage: both keep for good what they were given.

## For stewards: if something is happening

    # pause intake at once (the site, the door and the issue path all honour it)
    edit data/config.json  ->  "open": false
    # hide one thing now
    python3 tools/wingbeat.py veil <id> "why"
    # an issue "alarm: no sweep for 12 hours": Actions > sweep > Run workflow, then read the issue (AGENTS.md, The watch)
    # see what the sweep has been doing
    ls removals/ | tail ; git log --oneline -20
    # undo a bad hour
    git revert <commit>      # never rewrite history: the history is the work
