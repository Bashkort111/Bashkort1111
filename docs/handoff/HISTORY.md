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
- v2: title condensed to 74 % width and fitted per half (207 px), halves kept clear of the hair; hair got
  cel shading, an anime shine band and a soft inner rim light; face got hair shadows and cheek shading;
  magenta horizon glow behind the skyline; two proper feathers instead of four stray marks.
- v3: removed flyaway strands (they read as white blades at the temples and bars beside the eyes).
- v4 (final): +14 % saturation in grading so it holds up next to the channel's saturated thumbnails.
  Final PNG/JPG committed.
