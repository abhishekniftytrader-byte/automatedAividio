"""One-time YouTube OAuth for headless server, per channel.

Step 1: python pipeline/yt_auth.py <channel-name>            -> prints consent URL
Step 2: python pipeline/yt_auth.py <channel-name> "<redirect URL>" -> saves channels/<name>/token.json
"""
import os
import sys
from pathlib import Path

from google_auth_oauthlib.flow import Flow

ROOT = Path(__file__).resolve().parent.parent
SCOPES = os.getenv("OAUTH_SCOPES", "https://www.googleapis.com/auth/youtube.upload").split()

flow = Flow.from_client_secrets_file(
    str(ROOT / "client_secret.json"), scopes=SCOPES,
    redirect_uri="http://localhost")

channel_dir = ROOT / "channels" / sys.argv[1]
channel_dir.mkdir(parents=True, exist_ok=True)
verifier_file = channel_dir / ".oauth_verifier"

if len(sys.argv) == 2:
    url, _ = flow.authorization_url(access_type="offline", prompt="consent")
    verifier_file.write_text(flow.code_verifier)
    print(url)
else:
    flow.code_verifier = verifier_file.read_text()
    flow.fetch_token(authorization_response=sys.argv[2])
    verifier_file.unlink()
    token_file = channel_dir / "token.json"
    token_file.write_text(flow.credentials.to_json())
    token_file.chmod(0o600)
    print(f"{token_file} saved, refresh token:", bool(flow.credentials.refresh_token))
