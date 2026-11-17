#!/usr/bin/env bash
# Reinstala o video-use (https://github.com/browser-use/video-use) num container novo.
# A chave da ElevenLabs NÃO fica aqui: salve-a em Network secrets do ambiente
# (host api.elevenlabs.io, header xi-api-key) ou em ~/Developer/video-use/.env.
set -euo pipefail

DEST="$HOME/Developer/video-use"

if [ -d "$DEST/.git" ]; then
  git -C "$DEST" pull --ff-only
else
  mkdir -p "$(dirname "$DEST")"
  git clone https://github.com/browser-use/video-use "$DEST"
fi

cd "$DEST"
if command -v uv >/dev/null; then uv sync; else pip install -e .; fi

command -v ffmpeg >/dev/null || { sudo apt-get update && sudo apt-get install -y ffmpeg; }

mkdir -p "$HOME/.claude/skills"
ln -sfn "$DEST" "$HOME/.claude/skills/video-use"

# Os helpers exigem a variável; com Network secrets o proxy troca o valor pela chave real.
if ! grep -q '^ELEVENLABS_API_KEY=..' .env 2>/dev/null; then
  printf 'ELEVENLABS_API_KEY=proxy-injected\n' > .env
  chmod 600 .env
fi

ffprobe -version | head -1
.venv/bin/python helpers/grade.py --list-presets >/dev/null && echo "video-use pronto em $DEST"
