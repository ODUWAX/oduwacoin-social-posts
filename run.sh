#!/usr/bin/env bash
# Daily runner: ./run.sh image|reel <graph.facebook.com credential handle>
# Generates today's media if missing (Pacific date), pushes it to GitHub Pages, then publishes one post.
set -euo pipefail
KIND="$1"; HANDLE="$2"
cd "$(dirname "$0")"
git pull -q --rebase
DATE=$(TZ=America/Los_Angeles date +%F)
if [ ! -f "media/$DATE/meta.json" ] || [ ! -f "media/$DATE/reel.mp4" ]; then
  python3 generate.py --date "$DATE"
  git add "media/$DATE"
  git commit -q -m "Media for $DATE

Co-authored-by: Perplexity <noreply@perplexity.ai>"
  git push -q
fi
pplx credentials run "$HANDLE" -- python3 publish.py --date "$DATE" --only "$KIND" || STATUS=$?
git add posted.json
git commit -q -m "Posted $KIND for $DATE

Co-authored-by: Perplexity <noreply@perplexity.ai>" || true
git push -q || true
exit "${STATUS:-0}"
