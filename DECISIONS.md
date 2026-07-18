# DECISIONS — log

Format: `YYYY-MM-DD — decision — why`

- 2026-07-18 — 6 doc files as project foundation — future sessions + scaling need single source of truth
- 2026-07-18 — zero-cost constraint hard rule — no revenue yet, runway preservation
- 2026-07-18 — files-on-disk pipeline, no DB/queue — one video/day scale doesn't need infra
- 2026-07-18 — Gemini free tier (gemini-2.5-flash) = LLM for highlight ranking — free quota >> our need; app subscriptions useless for API
- 2026-07-18 — source videos = local files only (own content) — YouTube blocks yt-dlp from GCP IP; cookies risk account, proxy costs money; own content also kills YPP reused-content risk
- 2026-07-18 — Automation #1 = fully generative (topic→Gemini script→edge-tts voice→ASS captions→ffmpeg), pipeline/make_short.py — no source video needed, kills yt-dlp/manual problem entirely; repo #1 kept only for future own-content repurposing
- 2026-07-18 — Veo/Google Flow rejected — no free API, UI-manual, breaks zero-cost + no-manual rules
- 2026-07-18 — YouTube upload via Data API + refresh token (token.json, chmod 600) — pipeline/yt_upload.py; test upload OK; app unaudited → API uploads forced private until Google audit passed
- 2026-07-18 — trend sources = Google Trends RSS + Wikipedia top pageviews — Reddit 403s GCP IPs; both free, no key, datacenter-friendly
- 2026-07-18 — pipeline/daily.sh = full chain (trend_picker → make_short → yt_upload), cron-ready — niche-agnostic max-reach per Abhi; used_topics.txt prevents repeats
- 2026-07-18 — Pexels free API = visuals (portrait clips, topic-matched keywords from Gemini, ffmpeg normalize+concat, slight darken for caption readability) — flat-bg fallback kept
- 2026-07-18 — per-channel config.json (niche for trend picker) + per-channel token/used_topics; daily.sh <channel> [privacy]; Gemini calls retry 4x w/ backoff (503 spikes)
- 2026-07-18 — IG publishing live: Instagram Login API (app abhi-automation, acct ai_trendingshort) + own Google Drive as temp public URL host (drive.file token, file deleted post-publish) — Litterbox rejected by CC permission classifier; Drive = own storage, no 3rd party
- 2026-07-18 — IG token auto-refresh in ig_upload.py (>30d old → refresh, 60d expiry) — cron must never die silently
- 2026-07-18 — IG cross-post opt-in per channel via config.json ig_account; trader channel → ai_trendingshort; IG failure non-fatal (YT already uploaded)
- 2026-07-18 — dashboard = pipeline/stats.py cron 10:30 IST → stats_history.jsonl + dashboard.html (no server, open file in browser) — YT public stats need YT_API_KEY in .env (pending), IG stats live
- 2026-07-18 — TikTok = pending Abhi's developer app registration (developers.tiktok.com, Content Posting API); uploader built after creds; until audit passes API posts are SELF_ONLY drafts
