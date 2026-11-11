# Next steps

1. **If `HF_TOKEN` is set** (check presence only: `test -n "${HF_TOKEN:-}"`):
   `uv run thumbgen/thumbgen.py grab https://www.youtube.com/@diray --out refs/diray`, copy the Vindicta card
   (https://steamdb.com/assets/deadlock/heroes/vindicta-card.png) to `refs/vindicta/card.png`, then run `gen`
   with `--style refs/diray/VDBooG7nxJ4.jpg` (ТИТАНЫ) and `--title "ВИНД|ИКТА"`: one AI-title run, then one
   `--title-mode overlay` run if quota is left. Review at full size and at feed size, commit the chosen
   outputs to `thumbnails/vindicta/out/ai/`.
2. **If `GEMINI_API_KEY` is set:** add a Gemini (Nano Banana) provider to `thumbgen gen`
   (multiple reference images + prompt), test it, then run step 1's references through it.
3. **If the user sends their own reference thumbnail:** it arrives under `.hoplite/attachments/<id>/`; pass it
   with `--style` (or a YouTube link via `grab`).
4. Keep `refs/` out of git (public repo).
