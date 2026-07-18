"""Publish a workspace short to Instagram as a Reel.

Usage: .venv/bin/python pipeline/ig_upload.py workspace/<slug>

Flow: upload final.mp4 to own Google Drive (drive.file token) -> make public
-> IG Graph API creates Reel container from that URL -> publish -> delete
Drive file. Zero third-party hosts, zero cost.
"""
import json
import sys
import time
from pathlib import Path

import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

ROOT = Path(__file__).resolve().parent.parent
IG_FILE = ROOT / "channels" / "ig_trendingshort.json"
IG = json.loads(IG_FILE.read_text())
GRAPH = "https://graph.instagram.com/v21.0"


def refresh_token_if_old():
    """IG long-lived tokens last 60 days; refresh when >30 days old."""
    import datetime
    saved = datetime.date.fromisoformat(IG["token_saved"])
    if (datetime.date.today() - saved).days < 30:
        return
    r = requests.get("https://graph.instagram.com/refresh_access_token", params={
        "grant_type": "ig_refresh_token", "access_token": IG["token"]}, timeout=30)
    if r.ok:
        IG["token"] = r.json()["access_token"]
        IG["token_saved"] = datetime.date.today().isoformat()
        IG_FILE.write_text(json.dumps(IG))
        print("[ig] token refreshed")


def drive_service():
    token = ROOT / "channels" / "gdrive" / "token.json"
    creds = Credentials.from_authorized_user_file(str(token))
    if creds.expired:
        creds.refresh(Request())
        token.write_text(creds.to_json())
    return build("drive", "v3", credentials=creds)


def host_on_drive(video: Path) -> tuple:
    drive = drive_service()
    f = drive.files().create(
        body={"name": video.parent.name + ".mp4"},
        media_body=MediaFileUpload(str(video), mimetype="video/mp4", resumable=True),
        fields="id").execute()
    fid = f["id"]
    drive.permissions().create(fileId=fid, body={"type": "anyone", "role": "reader"}).execute()
    return fid, f"https://drive.google.com/uc?export=download&id={fid}"


def publish(work_dir: Path) -> str:
    refresh_token_if_old()
    meta = json.loads((work_dir / "meta.json").read_text())
    caption = meta["title"] + "\n\n" + meta["description"] + "\n\n" + " ".join(meta["hashtags"])

    fid, url = host_on_drive(work_dir / "final.mp4")
    print(f"[drive] hosted {fid}")
    try:
        r = requests.post(f"{GRAPH}/{IG['user_id']}/media", data={
            "media_type": "REELS", "video_url": url, "caption": caption[:2200],
            "access_token": IG["token"]}, timeout=60)
        r.raise_for_status()
        container = r.json()["id"]
        for _ in range(30):  # IG downloads + processes; poll up to ~5 min
            s = requests.get(f"{GRAPH}/{container}", params={
                "fields": "status_code", "access_token": IG["token"]}, timeout=30).json()
            if s.get("status_code") == "FINISHED":
                break
            if s.get("status_code") == "ERROR":
                raise RuntimeError(f"IG container error: {s}")
            time.sleep(10)
        else:
            raise RuntimeError("IG processing timeout")
        r = requests.post(f"{GRAPH}/{IG['user_id']}/media_publish", data={
            "creation_id": container, "access_token": IG["token"]}, timeout=60)
        r.raise_for_status()
        return r.json()["id"]
    finally:
        drive_service().files().delete(fileId=fid).execute()
        print("[drive] cleaned up")


if __name__ == "__main__":
    media_id = publish(Path(sys.argv[1]))
    print(f"published to instagram: media id {media_id} -> instagram.com/{IG['username']}")
