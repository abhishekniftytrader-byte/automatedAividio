"""Collect channel stats -> channels/stats_history.jsonl -> dashboard.html.

Usage: .venv/bin/python pipeline/stats.py
Sources: YouTube Data API public stats (needs YT_API_KEY in .env),
Instagram media list (existing token). Runs daily via cron.
"""
import datetime
import json
import os
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

YT_CHANNELS = {
    "mindsnack-trader": "UC1wke9OXCMPsAxTVqJN9rPA",
    "aicute-animalvlogs": "UCfQI-CKnMUdl6cPgtsZ-1bA",
}
HISTORY = ROOT / "channels" / "stats_history.jsonl"


def yt_stats() -> dict:
    key = os.getenv("YT_API_KEY")
    if not key:
        return {}
    ids = ",".join(YT_CHANNELS.values())
    r = requests.get("https://www.googleapis.com/youtube/v3/channels",
                     params={"part": "statistics", "id": ids, "key": key}, timeout=30)
    r.raise_for_status()
    by_id = {i["id"]: i["statistics"] for i in r.json().get("items", [])}
    return {name: {
        "subs": int(s.get("subscriberCount", 0)),
        "views": int(s.get("viewCount", 0)),
        "videos": int(s.get("videoCount", 0)),
    } for name, cid in YT_CHANNELS.items() if (s := by_id.get(cid))}


def ig_stats() -> dict:
    ig = json.loads((ROOT / "channels" / "ig_trendingshort.json").read_text())
    r = requests.get("https://graph.instagram.com/v21.0/me/media",
                     params={"fields": "like_count,comments_count,timestamp",
                             "limit": 50, "access_token": ig["token"]}, timeout=30)
    if not r.ok:
        return {}
    posts = r.json().get("data", [])
    return {"ig_" + ig["username"]: {
        "posts": len(posts),
        "likes": sum(p.get("like_count", 0) for p in posts),
        "comments": sum(p.get("comments_count", 0) for p in posts),
    }}


def render(history: list):
    today = history[-1]
    prev = history[-2] if len(history) > 1 else today
    rows = []
    for name, s in today["channels"].items():
        p = prev["channels"].get(name, s)
        cells = "".join(
            f"<td>{v:,} <span class='d'>{'+' if v - p.get(k, v) >= 0 else ''}{v - p.get(k, v):,}</span></td>"
            for k, v in s.items())
        rows.append(f"<tr><th>{name}</th>{cells}</tr>")
    heads = {name: list(s) for name, s in today["channels"].items()}
    (ROOT / "dashboard.html").write_text(f"""<!doctype html>
<meta charset="utf-8"><title>Channel Machine</title>
<style>
body{{font:16px system-ui;background:#101020;color:#eee;max-width:720px;margin:2em auto;padding:0 1em}}
table{{border-collapse:collapse;width:100%;margin:1em 0}}
td,th{{padding:.5em .8em;border-bottom:1px solid #333;text-align:right}}
th{{text-align:left}} .d{{color:#7c7;font-size:.8em}} h1{{font-size:1.3em}}
</style>
<h1>📺 Channel Machine — {today['date']}</h1>
<p>Numbers per channel (delta vs previous run in green). Metrics: {json.dumps(heads)}</p>
<table>{''.join(rows)}</table>
<p>History: {len(history)} snapshots in channels/stats_history.jsonl</p>""")


if __name__ == "__main__":
    snap = {"date": datetime.date.today().isoformat(),
            "channels": {**yt_stats(), **ig_stats()}}
    with open(HISTORY, "a") as f:
        f.write(json.dumps(snap) + "\n")
    history = [json.loads(l) for l in HISTORY.read_text().splitlines()]
    render(history)
    print(json.dumps(snap, indent=2))
