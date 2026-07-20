"""Upload one video to own TikTok account via Content Posting API (direct post).

Usage: python pipeline/tiktok_upload.py <video.mp4> "<title>"
Needs channels/tiktok.json from tt_auth.py.
Unaudited/sandbox clients: TikTok forces SELF_ONLY (private) — same as YouTube.
"""
import json
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")
TOKEN_FILE = ROOT / "channels" / "tiktok.json"
API = "https://open.tiktokapis.com/v2"


def access_token():
    tok = json.loads(TOKEN_FILE.read_text())
    # ponytail: always refresh instead of tracking expiry — 1 extra call/day, zero clock logic
    r = requests.post(f"{API}/oauth/token/", data={
        "client_key": os.environ["TIKTOK_CLIENT_KEY"],
        "client_secret": os.environ["TIKTOK_CLIENT_SECRET"],
        "grant_type": "refresh_token",
        "refresh_token": tok["refresh_token"]}, timeout=30)
    r.raise_for_status()
    d = r.json()
    if "access_token" not in d:
        sys.exit(f"refresh failed: {d}")
    tok.update(d)
    TOKEN_FILE.write_text(json.dumps(tok, indent=1))
    return d["access_token"]


def upload(video: Path, title: str):
    at = access_token()
    size = video.stat().st_size
    # ponytail: single chunk, TikTok allows up to 64MB — shorts are ~5MB; chunk loop if ever bigger
    assert size < 64_000_000, "video >64MB needs chunked upload"
    r = requests.post(f"{API}/post/publish/video/init/",
                      headers={"Authorization": f"Bearer {at}"},
                      json={"post_info": {"title": title, "privacy_level": "SELF_ONLY"},
                            "source_info": {"source": "FILE_UPLOAD", "video_size": size,
                                            "chunk_size": size, "total_chunk_count": 1}},
                      timeout=30)
    d = r.json()
    if d.get("error", {}).get("code") not in (None, "ok"):
        sys.exit(f"init failed: {d['error']}")
    pid, url = d["data"]["publish_id"], d["data"]["upload_url"]
    r = requests.put(url, data=video.read_bytes(),
                     headers={"Content-Type": "video/mp4",
                              "Content-Range": f"bytes 0-{size - 1}/{size}"}, timeout=300)
    r.raise_for_status()
    r = requests.post(f"{API}/post/publish/status/fetch/",
                      headers={"Authorization": f"Bearer {at}"},
                      json={"publish_id": pid}, timeout=30)
    print(f"published: publish_id={pid} status={r.json().get('data', {}).get('status')}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    upload(Path(sys.argv[1]), sys.argv[2])
