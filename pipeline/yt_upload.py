"""Upload a workspace short to YouTube.

Usage: .venv/bin/python pipeline/yt_upload.py workspace/<slug> [public|unlisted|private] [channel-name]
Default privacy: private (unaudited API clients get forced private anyway).
Token: channels/<channel-name>/token.json if given, else legacy token.json.
"""
import json
import sys
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

ROOT = Path(__file__).resolve().parent.parent


def upload(work_dir: Path, privacy: str = "private", channel: str = None) -> str:
    meta = json.loads((work_dir / "meta.json").read_text())
    token = ROOT / "channels" / channel / "token.json" if channel else ROOT / "token.json"
    creds = Credentials.from_authorized_user_file(str(token))
    if creds.expired:
        creds.refresh(Request())
        token.write_text(creds.to_json())

    yt = build("youtube", "v3", credentials=creds)
    body = {
        "snippet": {
            "title": meta["title"][:100],
            "description": meta["description"] + "\n\n" + " ".join(meta["hashtags"]),
            "categoryId": "27",  # Education
        },
        "status": {"privacyStatus": privacy, "selfDeclaredMadeForKids": False},
    }
    req = yt.videos().insert(
        part="snippet,status",
        body=body,
        media_body=MediaFileUpload(str(work_dir / "final.mp4"), resumable=True),
    )
    resp = None
    while resp is None:
        _, resp = req.next_chunk()
    return resp["id"]


if __name__ == "__main__":
    privacy = sys.argv[2] if len(sys.argv) > 2 else "private"
    channel = sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] else None
    vid = upload(Path(sys.argv[1]), privacy, channel)
    print(f"uploaded: https://youtu.be/{vid} ({privacy}, channel={channel or 'default'})")
