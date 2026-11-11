# History

## 2026-11-11 — Vindicta (Deadlock) thumbnail

- Request: a YouTube thumbnail ("превью") matching the channel's existing thumbnails. The character
  "Venedikt Dedlok" is interpreted as **Vindicta from Deadlock** (the channel covers Dota 2 and Deadlock).
  The background should be a related location, slightly blurred.
- Studied the channel grid (user attachment): one big outlined Cyrillic title word, often split around a
  centred character with glowing eyes (ТИТАНЫ, БАЛАНС), thick dark outlines, coloured glow, saturated rim light.
- Vindicta references (deadlockwiki.org / steamdb card art): pale blue skin, long white-blue hair parted in
  the middle, glowing eyes with black tear streaks, purple lips, triangle forehead mark, crimson high-collar
  coat with a dark bow and gold brooch, crow familiar.
- Built `thumbnails/vindicta/`: hand-drawn SVG bust (`assets/vindicta.svg`), procedural Deadlock-style night
  city (art-deco tower, gothic spires, water towers, ziplines, warm windows) under a blood moon with a
  Gaussian blur, split title in Rubik Wet Paint (OFL), rendered by headless Chrome at 2x, graded with Pillow
  (bloom, vignette, grain).
- Checkpoint 1 (82809d2): v1 render; title too small and partly hidden.
- v2–v4 (fc16941): bigger condensed title, hair/face shading, magenta horizon, feathers, +14 % saturation.

## 2026-11-11 — Follow-up: find/build an AI tool that makes a thumbnail "like the reference"

- The user asked for a tool (e.g. on GitHub) that generates a thumbnail like a reference they send, and to
  make the Vindicta thumbnail with it.
- The channel is **Di ray** (@diray, UCzB2V3zc2E4dy3-nxJoD0Yg). Its latest 15 thumbnails were downloaded at
  1280×720 as style references (git-ignored `refs/`, the repo is public and the art is not ours).
- GitHub tools found: yoanbernabeu/NanoThumbnail (best fit: style references, Nano Banana, browser app),
  manuarora700/youtube-thumbnail-generator, bhancockio/adk-youtube-thumbnail-agent. All need a paid
  Gemini/OpenAI/OpenRouter/Replicate key; the project has no keys configured.
- Free routes checked:
  - Hugging Face ZeroGPU demos: FLUX.2-dev works anonymously (8-step test image in 10.6 s), but the shared
    anonymous quota for this sandbox IP then ran out ("164s requested vs. -82s left"). Qwen-Image-Edit-2511
    rejects anonymous calls (360 s request is above the anonymous maximum).
  - Pollinations: the new API needs a key; the keyless Classic API allows `flux` and `gptimage`
    (1 image / 45 s per IP); kontext, nanobanana and seedream need a key.
  - Omni Image Editor Space requires a Cloudflare Turnstile token: skipped.
- Built `thumbgen/thumbgen.py`: `grab` (full-res thumbnails from video links/IDs or a channel's latest
  uploads via RSS) and `gen` (FLUX.2-dev Space via gradio_client, style + character + layout references,
  title lettered by AI or overlaid). `thumbnails/vindicta/build.py` gained `--art`, `--no-title`,
  `--left-end`, `--right-start`, `--title-y` so it can put the exact title over an AI picture.
- Checkpoint 3 (0329fa2): tool committed; testing Pollinations `gptimage` with reference images.
- Pollinations Classic test: the keyless `gptimage` request returned in 5 s, but the JPEG's EXIF says the model
  was `sana`: references ignored (generic dark-haired girl), pollinations.ai watermark despite `nologo`.
  Unusable for style copying.
- Hugging Face ZeroGPU quotas (docs, Nov 2026): 2 min/day unauthenticated (per IP), 5 min/day free account,
  40 min/day PRO; `xlarge` Spaces such as FLUX.2-dev count 2×; quota resets 24 h after first use.
  `thumbgen gen` default steps lowered 28 → 24 (2 refs → 144 s requested) so a free account gets ~3 images/day.
- README documents thumbgen. `uv run` verified for both scripts; `build.py --art` overlay smoke-tested.
- Checkpoint 4: waiting for the user to choose how to unlock generation (free HF token, Gemini key, or
  NanoThumbnail themselves).
