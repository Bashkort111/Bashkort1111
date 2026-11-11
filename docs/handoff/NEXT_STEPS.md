# Next steps

1. Evaluate the Pollinations `gptimage` result. If it is good, add `--provider pollinations` to
   `thumbgen gen` (reference images must be public URLs; grabbed YouTube thumbnails map back to
   i.ytimg.com automatically).
2. If quality or limits are not good enough, ask the user to add `HF_TOKEN` (free Hugging Face account) or
   a Gemini key as a project variable, then run `thumbgen gen` with FLUX.2-dev (or a Gemini provider).
3. Overlay mode: generate clean art, then draw the exact title with `build.py --art`.
4. Document thumbgen usage in README.md and share results with the user.
