# STACK — zero-cost tools per stage

All choices TBD until repo ranking. Candidates (all $0):

| Stage | Candidates |
|---|---|
| Script gen | Claude (existing sub), local LLM (ollama) |
| TTS | edge-tts (free MS voices), piper, kokoro (local) |
| Visuals | Pexels/Pixabay free API (stock), matplotlib/manim (charts), ffmpeg slideshow |
| Assembly | ffmpeg (raw), moviepy if ffmpeg args get painful |
| Thumbnail | PIL/Pillow |
| Upload | YouTube Data API v3 (free quota: 10k units/day, upload=1600 units → ~6 uploads/day) |
| Scheduling | cron (this server) |
| Analytics | YouTube Analytics API (free) |

Rule: no paid tool without DECISIONS.md entry.
