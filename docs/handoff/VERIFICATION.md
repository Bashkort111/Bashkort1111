# Verification

Environment: Python 3.12.3, Pillow 13.0.0, numpy 2.5.4, gradio_client 2.7.2 (venv at /tmp/thumbvenv),
Google Chrome for Testing 157.0.8103.38. This is an asset repo with no automated tests; checks are renders,
tool runs and visual review.

| Stage | Check | Result |
| --- | --- | --- |
| v1 | `python thumbnails/vindicta/build.py --html` | OK in 5.9 s; title 152 px; PNG 1422 KB, JPG 265 KB; 1280×720 |
| v1 | Visual review | Composition reads; title too small, Д/И hidden behind hair |
| v2 | Render | OK; title 207 px; PNG 1458 KB, JPG 276 KB |
| v2 | 2× close-up of the head (x 400–880, y 70–520) | Face, tears, mark, collar and brooch read well; flyaway strands look like blades |
| v3 | Render after removing flyaways | OK; PNG 1449 KB, JPG 273 KB |
| v3 | Pasted at 336×189 into the user's channel-grid screenshot | Title legible at feed size, eyes are the focal point; slightly muted next to the other thumbnails |
| v4 | Render with +14 % saturation | OK; title 207 px; PNG 1463 KB, JPG 274 KB; JPG is 1280×720 RGB; both under YouTube's 2 MB limit |
| v4 | Visual review | Coat and moon richer, no clipping or banding noticed |
| tool | `build.py` after adding `--art/--no-title/...`, default args, diffed against committed PNG | Pixel-identical (`ImageChops.difference(...).getbbox() is None`) |
| tool | `thumbgen.py grab https://www.youtube.com/@diray --limit 15 --out refs/diray` | 15 thumbnails, all 1280×720, titles from the RSS feed |
| tool | `thumbgen.py grab "https://www.youtube.com/watch?v=y59rL72foMs"` | 1 thumbnail 1280×720, title via oEmbed |
| tool | Anonymous FLUX.2-dev text-only test (8 steps, 512×288) | OK in 10.6 s |
| tool | `thumbgen.py gen` FLUX.2-dev, 2 refs, 28 steps | FAILED: "exceeded your ZeroGPU quota (164s requested vs. -82s left)" |
| tool | Qwen/Qwen-Image-Edit-2511 anonymous | FAILED: "requested GPU duration (360s) is larger than the maximum allowed" |
| tool | Pollinations: gen.pollinations.ai anonymous / classic kontext, nanobanana, seedream | 401 key required / 403 not in Classic API |
