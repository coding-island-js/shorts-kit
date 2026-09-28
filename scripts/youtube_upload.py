"""
youtube_upload.py: upload output/<slug>.mp4 to your own YouTube channel.

Usage:
  python scripts/youtube_upload.py <slug>                         # private (default, safest)
  python scripts/youtube_upload.py <slug> --unlisted
  python scripts/youtube_upload.py <slug> --public
  python scripts/youtube_upload.py <slug> --schedule 2026-10-01T16:00:00Z

Needs client_secret.json in the repo root (your own Google Cloud OAuth client,
see docs/youtube-setup.md). The first run opens a browser to sign in and saves
token.json. Both files stay on your machine and are gitignored.

A vertical video under 3 minutes is filed as a Short automatically.
"""

import argparse
import csv
from datetime import datetime

from common import ROOT, OUTPUT, load_meta, write_json, WORK, fail

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",  # posting the first comment
]
CLIENT_SECRET = ROOT / "client_secret.json"
TOKEN = ROOT / "token.json"


def authenticate():
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError:
        fail("Google libraries missing. Run: pip install -r requirements.txt")

    creds = Credentials.from_authorized_user_file(str(TOKEN), SCOPES) if TOKEN.is_file() else None
    if creds and creds.valid:
        return creds
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except Exception:
            # Apps left in "Testing" mode get refresh tokens that die after 7 days.
            print("  Saved sign-in expired, signing in again...")
            creds = None
    if not creds or not creds.valid:
        if not CLIENT_SECRET.is_file():
            fail("client_secret.json not found in the repo root. See docs/youtube-setup.md")
        print("Opening your browser to sign in to YouTube...")
        creds = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET), SCOPES).run_local_server(port=0)
    TOKEN.write_text(creds.to_json(), encoding="utf-8")
    return creds


def upload(slug, privacy="private", schedule_at=None):
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    meta = load_meta(slug)
    video = OUTPUT / f"{slug}.mp4"
    if not video.is_file():
        fail(f"output/{slug}.mp4 not found. Render it first.")
    if schedule_at:
        privacy = "private"  # YouTube requires private + publishAt

    title = meta["title"][:100]
    print(f"Uploading {slug}: {title}")
    print(f"  Privacy: {privacy}{'  publishes ' + schedule_at if schedule_at else ''}")

    youtube = build("youtube", "v3", credentials=authenticate())
    status = {"privacyStatus": privacy, "selfDeclaredMadeForKids": False}
    if schedule_at:
        status["publishAt"] = schedule_at
    body = {
        "snippet": {
            "title": title,
            "description": meta.get("description", "")[:5000],
            "tags": meta.get("tags", []),
            "categoryId": meta.get("category_id", "28"),
        },
        "status": status,
    }
    request = youtube.videos().insert(
        part="snippet,status", body=body,
        media_body=MediaFileUpload(str(video), mimetype="video/mp4", resumable=True, chunksize=5 * 1024 * 1024),
    )
    response = None
    while response is None:
        progress, response = request.next_chunk()
        if progress:
            print(f"\r  {int(progress.progress() * 100)}%", end="", flush=True)
    video_id = response["id"]
    url = f"https://youtube.com/shorts/{video_id}"
    print(f"\r  Uploaded: {url}")

    thumb = OUTPUT / f"{slug}-thumb.png"
    if thumb.is_file():
        try:
            youtube.thumbnails().set(videoId=video_id, media_body=MediaFileUpload(str(thumb))).execute()
            print("  Thumbnail set")
        except Exception as e:
            print(f"  Thumbnail skipped ({e.__class__.__name__}). Custom thumbnails need a phone-verified channel.")

    comment = meta.get("first_comment")
    if comment and privacy == "public" and not schedule_at:
        # YouTube rejects comments on private and scheduled videos.
        youtube.commentThreads().insert(part="snippet", body={"snippet": {
            "videoId": video_id, "topLevelComment": {"snippet": {"textOriginal": comment}}}}).execute()
        print("  First comment posted (pin it in YouTube Studio; the API cannot pin)")

    log = ROOT / "uploads.csv"
    new = not log.is_file()
    with open(log, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["date", "slug", "title", "url", "privacy", "publish_at"])
        w.writerow([datetime.now().strftime("%Y-%m-%d %H:%M"), slug, title, url, privacy, schedule_at or ""])

    meta.update({"youtube_id": video_id, "youtube_url": url})
    write_json(WORK / slug / "meta.json", meta)
    return url


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--public", action="store_true")
    g.add_argument("--unlisted", action="store_true")
    g.add_argument("--schedule", metavar="ISO_TIME", help="e.g. 2026-10-01T16:00:00Z")
    a = ap.parse_args()
    upload(a.slug, "public" if a.public else "unlisted" if a.unlisted else "private", a.schedule)
