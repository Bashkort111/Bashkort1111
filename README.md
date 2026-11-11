# Thumbnails

YouTube thumbnails built from code, plus a small AI tool that makes a thumbnail "like this one".

## Vindicta (Deadlock), vector version

`thumbnails/vindicta/` — 1280×720 thumbnail: hand-drawn vector bust of Vindicta,
split dripping title, blurred Deadlock-style night city under a blood moon.

```bash
# needs uv (or Python 3.10+ with pillow + numpy) and Chrome/Chromium on PATH (or CHROME=/path)
uv run thumbnails/vindicta/build.py                                  # ВИНД | ИКТА
uv run thumbnails/vindicta/build.py --left СНАЙ --right ПЕР --name sniper
uv run thumbnails/vindicta/build.py --art picture.png --left ВИНД --right ИКТА   # title over any picture
```

Outputs land in `thumbnails/vindicta/out/` (`.png` lossless, `.jpg` for upload, both under YouTube's 2 MB limit).

- Character art: `thumbnails/vindicta/assets/vindicta.svg` (editable in Inkscape/Illustrator, 1280×720 coordinates).
- Title font: Rubik Wet Paint (SIL OFL 1.1, see `assets/fonts/OFL.txt`).

## thumbgen: AI thumbnail in the style of a reference

`thumbgen/thumbgen.py` copies the look of reference thumbnails with the open FLUX.2 [dev] model through its
public Hugging Face demo.

```bash
# 1. grab references: full-res thumbnails of a channel's latest videos, or of specific videos
uv run thumbgen/thumbgen.py grab https://www.youtube.com/@diray --out refs/diray
uv run thumbgen/thumbgen.py grab "https://youtu.be/VDBooG7nxJ4" --out refs/style

# 2. generate (style reference + character reference + what should be in the picture)
export HF_TOKEN=hf_xxx   # free Hugging Face account, "Read" token
uv run thumbgen/thumbgen.py gen --style refs/diray/VDBooG7nxJ4.jpg --character refs/vindicta/card.png \
  --scene "Vindicta from Deadlock, centred chest-up, glowing eyes, crow on her shoulder, blurred night city, blood moon" \
  --title "ВИНД|ИКТА" --name vindicta --out thumbnails/vindicta/out/ai
```

- `--title-mode ai` (default): the model letters the title. `--title-mode overlay`: clean art, then the exact
  title is drawn on top by `build.py --art` (move it with `--left-end`, `--right-start`, `--title-y`).
- `--count N` makes variants with consecutive seeds; every result gets a `.json` with prompt, seed and references.
- GPU quota (Hugging Face ZeroGPU): 2 min/day without a token (per IP, often already used on shared IPs),
  5 min/day with a free account (about 3 images at the default 24 steps), 40 min/day with PRO.
- `refs/` is git-ignored: this repo is public and the reference art belongs to its authors.

Ready-made alternative: [NanoThumbnail](https://github.com/yoanbernabeu/NanoThumbnail), an open-source browser app
built on Google's Nano Banana models (bring your own Gemini, OpenRouter or Replicate key).

Handoff notes live in `docs/handoff/`.
