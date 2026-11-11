# Status

- **State:** blocked on the user (needs an access key). The vector thumbnail is final
  (`thumbnails/vindicta/out/vindicta_thumbnail.jpg`).
- **thumbgen:** `grab` verified (channel @handle and single video). `gen` (FLUX.2-dev on Hugging Face) is
  written and its API call matches the Space's signature, but it has **not produced an image with references
  yet**: the anonymous ZeroGPU quota for this sandbox IP is exhausted. Overlay mode (`build.py --art`) verified.
- **No keyless route works:** Pollinations Classic silently falls back to `sana` (ignores references, adds a
  watermark); Qwen-Image-Edit rejects anonymous calls; Omni Image Editor needs a Turnstile token.
- **Asked the user:** free HF token (`HF_TOKEN`, ~3 FLUX.2 images/day), Gemini key (`GEMINI_API_KEY`, Nano
  Banana, best quality, paid per image), or run NanoThumbnail themselves.
- **Assumptions:** character = Vindicta; title = ВИНДИКТА split ВИНД | ИКТА (the video title was not given).
