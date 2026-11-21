# DESIGN.md: how AIgorithmic Butterfly Effect looks, and why

One page, no build step, no font files, no pictures of its own except the work's. Character comes from scale, from two colours that mean something, and from three drawn objects: the butterfly, the ruler and, where a recording is sound alone, its waveform.

Every value below is a token at the top of the stylesheet in `index.html` (`:root`). Use a token, not a new value. This file is true to the page as of 21 November 2026 (Amendment 15); if you change a token, change its row here in the same commit.

## Colour (every colour has one job)

| Token | Value | Job |
|---|---|---|
| `--bg` | `#0a0a0b` | the ground of every view |
| `--pit` | `#060607` | the ground of the butterfly and of the introduction |
| `--panel` | `#111113` | a card, a closed day, a placeholder for a picture, a dialog: anything lying on the ground |
| `--ink` | `#ece8df` | text that is read; headings |
| `--soft` | `#cfcbc2` | second-level text: notes under a heading, machine-read lines, what was heard around a minute |
| `--dim` | `#8f8b83` | labels and counts (5.8:1 on the ground; never smaller than 11 px) |
| `--line`, `--line-2` | `#25252a`, `#2a2a30` | hairlines between things, and the faint ticks inside a drawn band (decoration) |
| `--edge`, `--edge-2` | `#6b6b73`, `#3a3a41` | the border of anything that can be typed into (3.75:1); the thumb of a thin scrollbar |
| `--rim`, `--rim-2` | `#fff8`, `#fff5` | the border of a pill that is pressed; the quieter border a card or a round button gets under the pointer |
| `--wall`, `--wall-hi`, `--wall-dim` | `#e3c34d`, `#f3d869`, `#1d1a0c` | **a human**; and the one accent: where you are, the next step, the thing playing. Its hover; its darkest, under the call in a day's band |
| `--hood` | `#6dbb72` | **an AI** |
| white | `#fff` | both together, or not sure |
| `--machine` | `#8a8f9c` | the caption machine of 2021, in a legend (on a canvas its paths are the darker `#6f7480`, thin and many) |
| `--by` | set by the script on `body` | the colour of whoever is speaking now; the button that sends wears it. A row of the marks carries its own |
| `--on-wall` | `#151204` | text on a filled button (10.9:1 on yellow, about 8:1 on green, more on white) |
| `--on-pic` | `#fffc` | what is written or pressed on a picture: the id, the round buttons in its corner |
| `--scrim`, `--scrim-2` | `#0009`, `#000c` | the dark under words or buttons that lie on a picture; the dark behind a dialog |
| `--tint` | `#ffffff0d` | the faint lift of the thing chosen in a list |
| `--clear` | `#fff0` | white that is not there yet (the arrows at the edges of the stage, before the pointer comes) |

Yellow, green and white are never decoration: wherever they colour a mark, a square, a label or a path, they say who spoke. There is no red, no blue, no gradient except the scrims that keep words readable on a picture. There is no light mode: the material is screens photographed at night.

What is still written as a value in the stylesheet: `#fff`, `#000`, and a few transparencies used once each (most of them the scrims of the theme tiles). The canvases in the script keep their own values, with the token's name in a comment beside them.

## Type (three voices, system fonts only)

| Voice | Stack | Used for |
|---|---|---|
| Serif | `--serif` (Iowan Old Style, Palatino, Georgia) | **what was said or written**: captions, quotations, headings, the question, the words of a mark |
| Mono | `--mono` (ui-monospace, Menlo, Consolas) | **what a machine measured**: times, ids, counts, labels; small capitals, letter-spacing .04 to .14em |
| Sans | the body font (system-ui) | **what the page says to the visitor**: notes, instructions, buttons |

Scale: `--t-label` 11, `--t-note` 13, `--t-small` 15, `--t-body` 16, `--t-quote` 19, `--t-head` 22, `--t-line` clamp(19px,1.7vw,26px) (the caption on the stage; 18 px on a phone, and 17 px there for a line a machine read), `--t-title` clamp(26px,3.4vw,40px), `--t-display` clamp(30px,5vw,54px). Three sizes keep a clamp of their own and say so in the stylesheet: a heading inside a view (`h3.sh`), the large quotation inside a theme (`.mo q`), and the introduction. Three levels on any one screen: a label, reading text, one large thing. Reading text keeps to 68 characters a line. Headings and single sentences are balanced (`text-wrap:balance`), paragraphs avoid a lone last word (`pretty`); figures in labels and counts are tabular.

The caption on the stage is never cut without a sign: while something plays, its box follows the word being said; at rest a caption longer than its box fades at its foot and "Read all of it" opens it (`#lmore`).

## Space, shape, depth, motion

Space in steps of 4 (4, 8, 12, 16, 24, 32, 44). The content is at most 1,240 px wide, 16 px from the edge (12 on phones); the marks, which are read, keep to 820. Radii: `--r-pic` 4 (a picture), `--r-card` 8, `--r-sheet` 14, `--r-pill` 999 (anything pressed). No shadow lifts anything; the only shadows are the dark under a bar that lies over the page.

Layers have names, never numbers: `--z-on` 2 and `--z-on-2` 3 (what lies on the picture), `--z-dock` 12 (the small bar), `--z-lift` 15 (the words and controls above the large ruler), `--z-ruler` 16, `--z-tip` 17, `--z-bar` 20, `--z-room` 50 (the butterfly in a room), `--z-full` 60, `--z-intro` 100, `--z-skip` 200.

Motion: `--fast` 150 ms for a state and for the change of a view, `--slow` 700 ms for a picture; the introduction keeps .9 s. Words of a caption arrive one by one, as they did in 2021: that is the one animation that belongs to the work. Everything stops under `prefers-reduced-motion`.

## Things that are pressed

| Thing | Class | Use |
|---|---|---|
| Filled pill | `.btn.go` | the next step of a screen |
| Outlined pill | `.btn`, `.btn.sm`, `.pill` | every other action; a chosen chip is outlined in yellow (`.on`) |
| Round icon | `.cb` (40 px, 44 on phones), `.ob` on a picture (32 px, 44 under a finger) | the stage's controls; each has a name for screen readers. A control that needs words is `.cb.txt` |
| Text button | `.lk` | an action inside a sentence, underlined |
| Who is speaking | `#byrow` buttons | a radio group; each with the square of its colour |
| A row | `.mcard`, `.ln` | something to be read that opens on the stage: a hairline above, no card ground. What Find finds is such rows; the word that was looked for is lifted (`--tint`, white, a hairline under it), never coloured |
| A field to look for a word | `#fq` | one on the page, in Find: a pill like everything pressed, the border of anything typed into (`--edge`) |
| A name in People | `.tcard`; `.here`, `.asked`, `.pin` | a name to open. A name a steward confirmed wears a human's yellow: an edge, the darkest yellow as its ground, and a filled label "✓ here". A name asked for and waiting has a dashed border and the label outlined |
| Bars of the nine weeks | `#tspark`, `#fspark` | when a theme, or a word, came up, day by day; a bar is pressed to go to its day |

States for all: hover (a brighter border or brighter words), focus (2 px yellow ring, 2 px away), chosen (yellow border or `aria-current`, never colour alone), disabled (35% and no pointer), busy (`aria-busy`, the label says what is happening). Nothing pressed is smaller than 24 px in either direction, and 44 under a finger. A row of many small things (a strip of frames, the calendar, an hour's pictures) is one stop for the Tab key; the arrows move inside it.

On the wide stage, with a mouse, the controls that lie on the picture rest at 45% and come up under the pointer or the keyboard. While the picture is censored, and under a finger, they are at full strength.

In full screen, seen as it was, only the picture and the words stay: the controls and the ruler lie over the foot of the picture on `--scrim-2` and leave it after three seconds without a move of the mouse, a key or a tap (`--fast`, no motion under `prefers-reduced-motion`); the pointer goes with them. Any of the three brings them back, and the press that does so does nothing else. Censored, full screen keeps the plain column with everything in sight.

## Pictures

A picture of the work is shown whole (`object-fit:contain` on the stage) and never cropped to decorate, except as the small cover of a row or tile. Censored, a picture is its colours and nothing else. No icons except the stage's line icons (20 px, stroke 2). No illustration, no stock picture, no emoji.

A long run of pictures is never one endless grid. It is told by day and hour and opened a piece at a time (`.phr`, a `<details>`, on one's own place in People): a closed piece shows six of its pictures and says how many it holds; the word that opens it is yellow, because it is the next step.

## The work's own three objects

**The butterfly** (the Lorenz drawing): thin grey for each line of 2021, thicker yellow, green or white for each mark. It is the picture of the whole (in About it fits one screen with its legend), what stands on the stage while the work opens, and the work's face to the outside (`data/og.png`, drawn again by `tools/og_build.py` whenever a mark arrives). **The icon** is the butterfly too, reduced to what a small square can hold: one turn round each wing, the left in a human's yellow, the right in an AI's green, on `--pit`. In a tab (`favicon.ico` at 16, 32 and 48 px, `img/icon.svg`) it is those two turns alone, each size with its own stroke; on a home screen (`img/touch-icon.png`, `img/icon-192.png`, `img/icon-512.png`, `img/icon-mask-512.png`) they lie over the grey paths of the 98 lines. `tools/icons_build.py` drew them; they are kept by hand. **The ruler**: every picture's colour above, the nine weeks below. **The waveform**: a phone call or a voice memo has no picture, so the stage draws its sound, bars about a middle line from the start of the recording to its end. What has been played is `--wall` (where you are), the rest `--dim`, and a line of `--ink` stands where the sound is now; it moves only because the recording does, and under `prefers-reduced-motion` in steps. The same drawing, still and in `--soft` on `--panel`, is the recording's picture wherever a call would show a frame (`wave.png`, made by `tools/wave_build.py`); in "Calls" it lies across the pieces of the recording's strip. It is a measure, not an ornament: never draw one for anything but a recording's own sound. Nothing else on the page is drawn.

## Time

The bar says which of its twenty years the work is in (`#yr`), and a yellow hairline under it has the length of the time that has passed (`--gone`). It counts nothing a visitor does, and it never moves while one looks.

## Do not

Add a font file, a second accent, a gradient, a glass panel, a card shadow, an emoji, a counter of a visitor's own activity, or a word in capitals longer than a label. Do not use yellow or green for anything but a human, an AI, or the next step.
