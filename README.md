# Thumbnails

YouTube thumbnails built from code (SVG → headless Chrome → Pillow).

## Vindicta (Deadlock)

`thumbnails/vindicta/` — 1280×720 thumbnail: hand-drawn vector bust of Vindicta,
split dripping title, blurred Deadlock-style night city under a blood moon.

```bash
# needs uv (or Python 3.10+ with pillow + numpy) and Chrome/Chromium on PATH (or CHROME=/path)
uv run thumbnails/vindicta/build.py                                  # ВИНД | ИКТА
uv run thumbnails/vindicta/build.py --left СНАЙ --right ПЕР --name sniper
```

Outputs land in `thumbnails/vindicta/out/` (`.png` lossless, `.jpg` for upload, both under YouTube's 2 MB limit).

- Character art: `thumbnails/vindicta/assets/vindicta.svg` (editable in Inkscape/Illustrator, 1280×720 coordinates).
- Title font: Rubik Wet Paint (SIL OFL 1.1, see `assets/fonts/OFL.txt`).

Handoff notes live in `docs/handoff/`.
