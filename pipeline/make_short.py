"""Automation #1: topic -> finished 9:16 short. Zero cost, zero manual steps.

Usage: .venv/bin/python pipeline/make_short.py "why most trading strategies fail"
Output: workspace/<slug>/final.mp4 + meta.json (title, description, hashtags)

Stages: Gemini script -> edge-tts voice (word timestamps) -> ASS karaoke
captions -> Pexels stock background clips -> ffmpeg 1080x1920 render.
Falls back to flat dark bg if Pexels returns nothing.
"""
import asyncio
import json
import os
import re
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

VOICE = os.getenv("TTS_VOICE", "en-US-ChristopherNeural")
MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


def gen_script(topic: str) -> dict:
    from google import genai
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    prompt = (
        "Write a YouTube Short voiceover script about: " + topic + "\n"
        "Rules: 90-110 words, ~40 seconds spoken. First sentence must be a hook. "
        "Punchy short sentences. No emojis, no stage directions, plain spoken text only.\n"
        "Also give 3 stock-video search keywords (2-3 words each, concrete visual nouns "
        "matching the topic, e.g. 'red panda', 'city night traffic').\n"
        'Return JSON: {"title": "...", "description": "...", "hashtags": ["#...", ...], '
        '"script": "...", "visual_keywords": ["...", "...", "..."]}'
    )
    import time
    for attempt in range(4):
        try:
            r = client.models.generate_content(
                model=MODEL, contents=prompt,
                config={"response_mime_type": "application/json", "temperature": 0.8},
            )
            return json.loads(r.text)
        except Exception:
            if attempt == 3:
                raise
            time.sleep(30 * (attempt + 1))


async def tts(script: str, mp3_path: Path) -> list:
    """Speak script, return [(word, start_s, end_s)] from WordBoundary events."""
    import edge_tts
    words = []
    com = edge_tts.Communicate(script, VOICE, boundary="WordBoundary")
    with open(mp3_path, "wb") as f:
        async for chunk in com.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                start = chunk["offset"] / 1e7
                words.append((chunk["text"], start, start + chunk["duration"] / 1e7))
    return words


ASS_HEADER = """[Script Info]
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, Bold, Outline, Alignment
Style: Word,Arial,130,&H00FFFFFF,&H00000000,1,8,5

[Events]
Format: Layer, Start, End, Style, Text
"""


def ass_time(s: float) -> str:
    h, m = divmod(int(s) // 60, 60)
    return f"{h}:{m:02d}:{int(s) % 60:02d}.{int(s * 100) % 100:02d}"


def write_captions(words: list, ass_path: Path):
    # one word on screen at a time, held until the next word starts
    lines = []
    for i, (w, start, end) in enumerate(words):
        until = words[i + 1][1] if i + 1 < len(words) else end
        lines.append(f"Dialogue: 0,{ass_time(start)},{ass_time(until)},Word,{w.upper()}")
    ass_path.write_text(ASS_HEADER + "\n".join(lines))


def duration_of(media: Path) -> float:
    return float(subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(media)]).strip())


def fetch_background(keywords: list, need_s: float, work: Path) -> Path | None:
    """Download Pexels portrait clips covering need_s seconds, normalize, concat."""
    import requests
    key = os.getenv("PEXELS_API_KEY")
    if not key:
        return None
    clips, covered, per_clip_cap = [], 0.0, 8
    for kw in keywords:
        if covered >= need_s:
            break
        r = requests.get("https://api.pexels.com/videos/search",
                         params={"query": kw, "orientation": "portrait", "per_page": 4},
                         headers={"Authorization": key}, timeout=30)
        if not r.ok:
            continue
        for v in r.json().get("videos", []):
            if covered >= need_s:
                break
            files = sorted((f for f in v["video_files"] if f["height"] >= 1280),
                           key=lambda f: f["height"])
            if not files:
                continue
            raw = work / f"bg_raw_{len(clips)}.mp4"
            with open(raw, "wb") as fh:
                fh.write(requests.get(files[0]["link"], timeout=120).content)
            norm = work / f"bg_{len(clips)}.mp4"
            take = min(v["duration"], per_clip_cap)
            subprocess.run([
                "ffmpeg", "-y", "-v", "error", "-i", str(raw), "-t", str(take),
                "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,"
                       "crop=1080:1920,fps=30,eq=brightness=-0.15",
                "-an", "-c:v", "libx264", "-preset", "fast", str(norm)], check=True)
            raw.unlink()
            clips.append(norm)
            covered += take
    if not clips:
        return None
    concat_list = work / "bg_list.txt"
    concat_list.write_text("".join(f"file '{c.name}'\n" for c in clips))
    bg = work / "bg.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
                    "-i", str(concat_list), "-c", "copy", str(bg)], check=True)
    return bg


def render(mp3: Path, ass: Path, out: Path, bg: Path | None):
    dur = duration_of(mp3)
    src = ["-stream_loop", "-1", "-i", str(bg)] if bg else \
          ["-f", "lavfi", "-i", f"color=c=0x101020:s=1080x1920:d={dur + 0.5}"]
    subprocess.run([
        "ffmpeg", "-y", "-v", "error", *src,
        "-i", str(mp3),
        "-vf", f"ass={ass}",
        "-t", str(dur + 0.3),
        "-c:v", "libx264", "-preset", "fast", "-c:a", "aac",
        str(out)], check=True)


def main():
    topic = sys.argv[1]
    slug = re.sub(r"[^a-z0-9]+", "-", topic.lower()).strip("-")[:60]
    work = ROOT / "workspace" / slug
    work.mkdir(parents=True, exist_ok=True)

    meta = gen_script(topic)
    print(f"[script] {meta['title']} ({len(meta['script'].split())} words)")

    mp3 = work / "voice.mp3"
    words = asyncio.run(tts(meta["script"], mp3))
    print(f"[tts] {len(words)} words, voice={VOICE}")

    ass = work / "captions.ass"
    write_captions(words, ass)

    bg = fetch_background(meta.get("visual_keywords", []), duration_of(mp3), work)
    print(f"[bg] {'pexels ' + bg.name if bg else 'flat fallback'}")

    out = work / "final.mp4"
    render(mp3, ass, out, bg)
    (work / "meta.json").write_text(json.dumps(meta, indent=2))
    print(f"[done] {out}")


if __name__ == "__main__":
    main()
