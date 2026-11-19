# Showing the work in a room

The work lives online, but it was born in a room: one person, one laptop, one yellow wall. These notes are for anyone who wants to put it back into a room. No permission is needed for non-commercial showings; tell a steward so the showing can be recorded in the work's history.

## The smallest version (one screen)

Open `https://ranaji10.github.io/aigorithmic-butterfly-effect/?exhibit` in any browser, full screen. It needs no interaction: a line appears every 24 seconds over the colour of the screenshot it came from, and every few minutes the butterfly fills the screen. It reloads itself hourly to pick up new wingbeats. Without internet: clone the repository, run `python3 -m http.server` in it, open `http://localhost:8000/?exhibit`.

Put the QR code (`print/qr.png`) next to the screen, at hand height. That is the whole door.

## The full version (a room)

1. **The call.** One projection or large screen running exhibition mode, sound off, in a dim room. If a wall can be painted, paint the wall behind the visitor yellow (the stage colours are taken from a yellow wall, around `#e3c34d`). Visitors standing in front of the projection then put a person-shaped shadow back into the picture.
2. **The weather.** `print/weather-2021-x8.png` printed as large as the wall allows, never smoothed (ask the printer for nearest-neighbour scaling). At 3 m wide each screenshot is about 3 cm. It reads as cloth from across the room and as 5,909 small windows up close.
3. **The clock.** `print/call-2021-x8.png` printed as a long horizontal strip at eye level. One row per day, midnight to midnight. People find the nights by themselves.
4. **The snow.** The eighteen photographs in `img/` on the floor, face up, in a path leading to the desk. Visitors will hesitate before walking next to them. That is correct.
5. **The desk.** A small table with one laptop or tablet open on the site, and a chair. Next to it a box, paper slips and pencils for people who do not want to touch a screen. A slip has three blanks: *the line I am answering*, *what I heard*, *human / machine / both / not sure*. Whoever looks after the room carries the slips into the work once a day (charter, section 3: carried lines), one account per carrier per day, so a busy room needs several carriers or patience. Both are in the spirit of the thing.
6. **The label.**

> **AIgorithmic Butterfly Effect**, 2021, reopened 2026, open until at least 2046
> Rana, with a caption machine, a language model, and whoever came
> 14,586 files reduced to colour; 98 lines misheard by software; one line a day from anyone since
> *What did you hear?*

## Care for the room

- Nothing in the room is live video and nothing records visitors. Say so on the label if people ask. This matters: the first version recorded everything.
- Do not show uncensored screenshots or footage from 2021, even if they become available to you. They contain people who never agreed.
- The lines on screen are written by strangers and are only lightly filtered. A steward can take any line back within the day (charter, section 6). For showings to children, run from a local copy and remove what you need to.
- If someone tells you the work is talking to them in particular, be kind, and get them a glass of water and a person to sit with.

## Technical sheet

| | |
|---|---|
| Duration | continuous; no beginning or end |
| Hardware | any device with a browser from the last ten years; projector or screen, 16:9 preferred |
| Network | optional (local copy works; new wingbeats then arrive when you `git pull`) |
| Sound | none |
| Print files | `print/poster-A3.png` (300 dpi), `print/weather-2021-x8.png`, `print/call-2021-x8.png`, `print/qr.png` |
| Credit line | Rana, *AIgorithmic Butterfly Effect*, 2021 to 2046, with contributions from humans and AI agents |
