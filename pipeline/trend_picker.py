"""Pick today's most viral-able short topic from live internet trends.

Usage: .venv/bin/python pipeline/trend_picker.py [channel-name]
Prints one topic line (stdout) -> pipe into make_short.py.
With channel-name: reads channels/<name>/config.json niche, keeps per-channel
used-topics list, and picks/invents a topic fitting that niche.

Sources (both free, no key, work from datacenter IPs — Reddit 403s GCP):
Google Trends daily RSS + Wikipedia top-viewed articles yesterday.
"""
import datetime
import json
import os
import re
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

SEEN = ROOT / "workspace" / "used_topics.txt"
UA = {"User-Agent": "trend-picker/1.0"}


def fetch_trends() -> list:
    items = []
    r = requests.get("https://trends.google.com/trending/rss?geo=US", headers=UA, timeout=30)
    if r.ok:
        items += [f"[Google search trend] {t}" for t in re.findall(r"<title>(.*?)</title>", r.text)[1:26]]
    day = datetime.date.today() - datetime.timedelta(days=2)
    r = requests.get(
        f"https://wikimedia.org/api/rest_v1/metrics/pageviews/top/en.wikipedia/all-access/{day:%Y/%m/%d}",
        headers=UA, timeout=30)
    if r.ok:
        arts = r.json()["items"][0]["articles"]
        items += [f"[Wikipedia trending] {a['article'].replace('_', ' ')}" for a in arts
                  if not re.match(r"Main Page|Special:|Wikipedia:|Portal:", a["article"].replace("_", " "))][:25]
    if not items:
        raise RuntimeError("both trend sources failed")
    return items


def pick(titles: list, used: str, niche: str = "") -> dict:
    from google import genai
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    niche_rule = (
        f"\n\nThe channel niche is: {niche}\nThe topic MUST fit this niche. If nothing "
        "trending fits, ignore the trends and invent a fresh evergreen viral topic in "
        "this niche instead." if niche else "")
    prompt = (
        "Here is what is trending on the internet today:\n\n" + "\n".join(titles) +
        "\n\nAlready-used topics (avoid repeats):\n" + (used or "none") + niche_rule +
        "\n\nPick the ONE topic with highest viral potential as a 40-second faceless "
        "YouTube Short (broad curiosity, strong hook, explainable in 100 words, "
        "evergreen enough to not need footage of the event). Rewrite it as a "
        "self-contained video topic, not a reference to the post. "
        "The topic must be ONE line, under 15 words.\n"
        'Return JSON: {"topic": "...", "why_viral": "..."}'
    )
    import time
    for attempt in range(4):
        try:
            r = client.models.generate_content(
                model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"), contents=prompt,
                config={"response_mime_type": "application/json", "temperature": 0.7},
            )
            return json.loads(r.text)
        except Exception:
            if attempt == 3:
                raise
            time.sleep(30 * (attempt + 1))


if __name__ == "__main__":
    import sys
    niche = ""
    seen = SEEN
    if len(sys.argv) > 1:
        cfg = ROOT / "channels" / sys.argv[1] / "config.json"
        niche = json.loads(cfg.read_text())["niche"]
        seen = ROOT / "channels" / sys.argv[1] / "used_topics.txt"
    used = seen.read_text() if seen.exists() else ""
    choice = pick(fetch_trends(), used, niche)
    seen.parent.mkdir(exist_ok=True)
    with open(seen, "a") as f:
        f.write(choice["topic"] + "\n")
    print(choice["topic"])
