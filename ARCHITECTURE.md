# ARCHITECTURE

Status: draft. Real design after repo ranking.

## Pipeline (target)

```
idea/niche feed → script gen → TTS voice → visuals → assemble (ffmpeg)
→ thumbnail → upload (YouTube Data API) → analytics loop
```

Each stage = standalone script, files on disk between stages. No queues, no
DB until volume demands. Cron drives it.

## Folder layout (target)

```
youtube-automation/
  CLAUDE.md CONTEXT.md ARCHITECTURE.md STACK.md DECISIONS.md ROADMAP.md
  repos/          # cloned reference repos (read-only)
  pipeline/       # our stage scripts
  workspace/      # per-video working dirs (script.txt, audio.wav, out.mp4)
  channels/       # per-channel config (niche, upload creds, schedule)
```

## Manual steps allowed

- Final review before upload (until trust earned)
- OAuth consent for YouTube API (one-time per channel)

## Scaling notes

- One video end-to-end first. Parallelism/multi-channel later — same scripts,
  more cron entries. No premature framework.
