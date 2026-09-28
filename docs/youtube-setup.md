# Connect your YouTube channel

Uploading uses your own Google Cloud project, so the videos go to your channel and nobody else ever holds your login. It takes about ten minutes, once. It's free.

Your AI agent can walk you through this. Tell it: *"Help me connect my YouTube channel. Follow docs/youtube-setup.md."*

## 1. Make a Google Cloud project

1. Go to [console.cloud.google.com](https://console.cloud.google.com) and sign in with the Google account that owns your channel.
2. Click the project picker at the top, then **New project**. Name it anything, like `shorts-kit`.

## 2. Turn on the YouTube API

1. Open **APIs & Services → Library**.
2. Search for **YouTube Data API v3**, open it, click **Enable**.

## 3. Set up the sign-in screen

1. Open **Google Auth Platform** (it may be listed as **OAuth consent screen**) and click **Get started**.
2. App name: anything. Support email: yours. Audience: **External**. Contact email: yours. Create.
3. Open **Audience → Test users → Add users** and add your own Google email.

## 4. Make the client file

1. Open **Clients → Create client**.
2. Application type: **Desktop app**. Create.
3. Click **Download JSON**. Rename the file to `client_secret.json` and put it in the root of this repo.

It's already in `.gitignore`. Never commit it.

## 5. First upload

```
python scripts/youtube_upload.py <slug>
```

A browser opens. Google will warn that the app isn't verified. That's expected, because it's your app. Click **Continue**. A `token.json` is saved next to `client_secret.json`, and later uploads won't ask again.

## Things Google doesn't tell you up front

- **Uploads may land as private no matter what you ask for.** Google locks API uploads to private for projects that haven't passed the [YouTube API audit](https://support.google.com/youtube/contact/yt_api_form). If that's you, open YouTube Studio and switch the video to Public. It's one click. The kit uploads as private by default anyway, so you can check the video before anyone sees it.
- **The sign-in expires after 7 days while the app is in Testing.** The upload script notices and opens the browser again. To stop that, go to **Audience** and click **Publish app**. You don't need Google to review it for your own use.
- **Custom thumbnails need a verified channel.** Verify your phone at [youtube.com/verify](https://www.youtube.com/verify). Until then the upload works and just skips the thumbnail.
- **YouTube won't take comments on private or scheduled videos.** A `first_comment` is only posted when you upload as public.
- **There's a daily quota.** The free tier covers a handful of uploads a day, which is plenty for Shorts.
