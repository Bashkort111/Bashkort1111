# Verification

Environment: Python 3.12.3, Pillow 13.0.0, numpy 2.5.4 (venv at /tmp/thumbvenv), Google Chrome for Testing
157.0.8103.38. This is an asset repo with no automated tests; checks are renders plus visual review.

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
