#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["gradio_client>=1.3", "pillow>=10", "numpy>=1.26"]
# ///
"""thumbgen: make a YouTube thumbnail "like this one" with a free open image model.

Commands
  grab   download full-resolution YouTube thumbnails from video links/IDs or a channel's latest uploads
  gen    generate a thumbnail with FLUX.2 [dev] (public Hugging Face demo, no key needed) from style
         reference thumbnails plus character reference images; optionally overlay a crisp title

Examples
  uv run thumbgen/thumbgen.py grab https://www.youtube.com/@diray --limit 15
  uv run thumbgen/thumbgen.py gen --style refs/diray/VDBooG7nxJ4.jpg --character refs/vindicta/card.png \\
      --scene "Vindicta from Deadlock ..." --title "ВИНД|ИКТА" --name vindicta

Anonymous use has a small daily GPU quota; set HF_TOKEN (free Hugging Face account) for more.
"""
from __future__ import annotations

import argparse
import inspect
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parent.parent
TITLER = ROOT / "thumbnails" / "vindicta" / "build.py"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0 Safari/537.36"
VIDEO_PATTERNS = [r"[?&]v=([\w-]{11})", r"youtu\.be/([\w-]{11})", r"/(?:shorts|live|embed)/([\w-]{11})"]
STYLE_WORDS = ("hand-painted anime illustration, bold black ink outlines, painterly cel shading, strong coloured "
               "rim light, saturated colours, dramatic glow")


def fetch(url: str, timeout: int = 30) -> bytes:
    # the consent cookie keeps YouTube from answering with its EU cookie wall
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Cookie": "CONSENT=YES+1; SOCS=CAI"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


# ----------------------------------------------------------------- grab ----
def oembed_title(vid: str) -> str:
    try:
        return json.loads(fetch(f"https://www.youtube.com/oembed?format=json&url=https://youtu.be/{vid}")).get("title", "")
    except Exception:  # noqa: BLE001 - the title is cosmetic
        return ""


def resolve(target: str) -> list[tuple[str, str]]:
    """[(video_id, title)] for a video link/ID, or the latest uploads of a channel link/@handle/UC-id."""
    for pat in VIDEO_PATTERNS:
        if m := re.search(pat, target):
            return [(m.group(1), oembed_title(m.group(1)))]
    if re.fullmatch(r"[\w-]{11}", target):
        return [(target, oembed_title(target))]
    if m := re.search(r"(UC[\w-]{22})", target):
        cid = m.group(1)
    else:
        url = target if target.startswith("http") else "https://www.youtube.com/" + target.lstrip("/")
        html = fetch(url).decode("utf-8", "replace")
        m = re.search(r'"externalId":"(UC[\w-]{22})"', html) or re.search(r"channel/(UC[\w-]{22})", html)
        if not m:
            raise SystemExit(f"no channel id found on {url}")
        cid = m.group(1)
    feed = ET.fromstring(fetch(f"https://www.youtube.com/feeds/videos.xml?channel_id={cid}"))
    ns = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015"}
    return [(e.findtext("yt:videoId", namespaces=ns), e.findtext("a:title", namespaces=ns) or "")
            for e in feed.findall("a:entry", ns)]


def cmd_grab(a: argparse.Namespace) -> None:
    a.out.mkdir(parents=True, exist_ok=True)
    rows = []
    for target in a.targets:
        for vid, title in resolve(target)[: a.limit]:
            for size in ("maxresdefault", "sddefault", "hqdefault"):
                try:
                    data = fetch(f"https://i.ytimg.com/vi/{vid}/{size}.jpg")
                except Exception:  # noqa: BLE001 - fall back to the next size
                    continue
                path = a.out / f"{vid}.jpg"
                path.write_bytes(data)
                w, h = Image.open(path).size
                rows.append(f"{vid}\t{w}x{h}\t{title}")
                print(f"{vid}  {w}x{h}  {title}")
                break
            else:
                print(f"{vid}  no thumbnail available", file=sys.stderr)
    with open(a.out / "index.tsv", "a", encoding="utf-8") as fh:
        fh.writelines(r + "\n" for r in rows)
    print(f"{len(rows)} thumbnail(s) -> {a.out}")


# ------------------------------------------------------------------ gen ----
def split_title(text: str) -> tuple[str, str]:
    if "|" in text:
        left, right = text.split("|", 1)
    else:
        left, right = text[: (len(text) + 1) // 2], text[(len(text) + 1) // 2:]
    return left.strip().upper(), right.strip().upper()


def build_prompt(a: argparse.Namespace, n_style: int, n_char: int, n_layout: int) -> str:
    def refs(start: int, n: int) -> str:
        return " and ".join(f"image {i}" for i in range(start, start + n))

    style, char, layout = refs(1, n_style), refs(1 + n_style, n_char), refs(1 + n_style + n_char, n_layout)
    parts = ["A YouTube video thumbnail, 16:9.",
             f"Copy the art style of {style} exactly: drawing technique, line art, shading, colour grading and "
             f"lettering style ({STYLE_WORDS}). Do not copy its character, objects or text."]
    if n_char:
        parts.append(f"The character must look like {char}: same face, hair, outfit and colours.")
    if n_layout:
        parts.append(f"Keep the composition of {layout}: same framing, pose and placement, but repaint everything "
                     "in the reference art style.")
    parts.append(a.scene.strip())
    if a.title and a.title_mode == "ai":
        left, right = split_title(a.title)
        script = "Cyrillic " if re.search("[А-Яа-яЁё]", a.title) else ""
        parts.append(f'Title: the huge hand-lettered {script}word "{left}{right}" split into "{left}" left of the '
                     f'head and "{right}" right of the head, lettered like the title in {style}'
                     + (f", {a.title_style}" if a.title_style else "") + ". Spell it exactly. No other text.")
    elif a.title:
        parts.append("No text or letters anywhere; keep the dark areas left and right of the head clear for a title.")
    else:
        parts.append("No text or letters anywhere.")
    parts.append("No watermark, no logo, no video length badge.")
    return " ".join(parts)


def make_client(space: str, token: str | None):
    from gradio_client import Client

    kw: dict = {"verbose": False}
    if token:  # gradio_client renamed hf_token -> token in 2.x
        kw["token" if "token" in inspect.signature(Client.__init__).parameters else "hf_token"] = token
    return Client(space, **kw)


def cmd_gen(a: argparse.Namespace) -> None:
    from gradio_client import handle_file

    refs = [*a.style, *a.character, *a.layout]
    for p in refs:
        if not p.exists():
            raise SystemExit(f"missing reference image: {p}")
    prompt = a.prompt or build_prompt(a, len(a.style), len(a.character), len(a.layout))
    a.out.mkdir(parents=True, exist_ok=True)
    client = make_client(a.space, os.environ.get("HF_TOKEN") or None)
    print(f"prompt: {prompt}\n")

    with tempfile.TemporaryDirectory() as td:
        images = []
        for i, p in enumerate(refs):  # the demo works at <=1024 px anyway; smaller uploads are faster
            im = Image.open(p).convert("RGB")
            im.thumbnail((1024, 1024), Image.LANCZOS)
            im.save(Path(td) / f"{i:02d}.png")
            images.append({"image": handle_file(str(Path(td) / f"{i:02d}.png")), "caption": None})

        for k in range(a.count):
            seed, t0 = a.seed + k, time.time()
            try:
                res = client.predict(prompt=prompt, input_images=images, seed=seed, randomize_seed=False,
                                     width=a.width, height=a.height, num_inference_steps=a.steps,
                                     guidance_scale=a.guidance, prompt_upsampling=False, api_name="/infer")
            except Exception as e:  # noqa: BLE001
                msg = str(e)
                if re.search(r"quota|duration|exceeded", msg, re.I):
                    msg += ("\nThe free GPU quota is used up or the request is too long: wait for the daily reset, "
                            "set HF_TOKEN (free Hugging Face account), or use fewer --steps / references.")
                raise SystemExit(f"generation failed: {msg}")
            out = res[0] if isinstance(res, (list, tuple)) else res
            out = out.get("path") or out.get("url") if isinstance(out, dict) else out

            stem = f"{a.name}_s{seed}"
            raw = Image.open(out).convert("RGB")
            raw.save(a.out / f"{stem}_raw.png")
            big = ImageOps.fit(raw, (1280, 720), Image.LANCZOS).filter(ImageFilter.UnsharpMask(1.2, 60, 2))
            big.save(a.out / f"{stem}.png", optimize=True)
            big.save(a.out / f"{stem}.jpg", quality=93, optimize=True, progressive=True)
            meta = {"space": a.space, "prompt": prompt, "seed": seed, "steps": a.steps, "guidance": a.guidance,
                    "size": [a.width, a.height], "references": [str(p) for p in refs], "title": a.title,
                    "title_mode": a.title_mode, "seconds": round(time.time() - t0, 1)}
            (a.out / f"{stem}.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"[{k + 1}/{a.count}] seed {seed}: {raw.size[0]}x{raw.size[1]} in {meta['seconds']} s -> "
                  f"{a.out / stem}.jpg")

            if a.title and a.title_mode == "overlay":
                left, right = split_title(a.title)
                cmd = [sys.executable, str(TITLER), "--art", str(a.out / f"{stem}.png"), "--left", left,
                       "--right", right, "--name", f"{stem}_title", "--out", str(a.out),
                       "--left-end", str(a.left_end), "--right-start", str(a.right_start), "--title-y", str(a.title_y)]
                subprocess.run(cmd, check=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("grab", help="download full-resolution YouTube thumbnails")
    g.add_argument("targets", nargs="+", help="video links/IDs, channel links, @handles or UC… channel IDs")
    g.add_argument("--limit", type=int, default=15, help="max videos per channel (the feed has the latest 15)")
    g.add_argument("--out", type=Path, default=ROOT / "refs" / "grabbed")
    g.set_defaults(func=cmd_grab)

    n = sub.add_parser("gen", help="generate a thumbnail in the style of reference thumbnails")
    n.add_argument("--style", type=Path, nargs="+", required=True, help="thumbnail(s) whose look to copy")
    n.add_argument("--character", type=Path, nargs="*", default=[], help="character reference image(s)")
    n.add_argument("--layout", type=Path, nargs="*", default=[], help="optional composition sketch/render")
    n.add_argument("--scene", default="", help="who is in the picture, pose, background")
    n.add_argument("--title", default="", help='title text; "LEFT|RIGHT" sets where it splits around the head')
    n.add_argument("--title-mode", choices=["ai", "overlay"], default="ai",
                   help="ai: the model letters the title; overlay: clean art + exact title drawn on top")
    n.add_argument("--title-style", default="", help="extra lettering instructions for --title-mode ai")
    n.add_argument("--left-end", type=float, default=494, help="overlay: x where the left half ends")
    n.add_argument("--right-start", type=float, default=786, help="overlay: x where the right half starts")
    n.add_argument("--title-y", type=float, default=338, help="overlay: title baseline y (of 720)")
    n.add_argument("--prompt", default="", help="use this exact prompt instead of the built one")
    n.add_argument("--count", type=int, default=1, help="number of variants (seed, seed+1, …)")
    n.add_argument("--seed", type=int, default=2026)
    # 24 steps with two references asks ZeroGPU for 144 s, so a free account (300 s/day) gets ~3 images
    n.add_argument("--steps", type=int, default=24)
    n.add_argument("--guidance", type=float, default=4.0)
    n.add_argument("--width", type=int, default=1024, help="the demo allows 256..1024")
    n.add_argument("--height", type=int, default=576)
    n.add_argument("--space", default="black-forest-labs/FLUX.2-dev", help="Hugging Face Space to call")
    n.add_argument("--name", default="thumb", help="output file stem")
    n.add_argument("--out", type=Path, default=ROOT / "thumbgen" / "out")
    n.set_defaults(func=cmd_gen)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
