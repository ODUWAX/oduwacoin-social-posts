#!/usr/bin/env bash
# Daily runner: ./run.sh image|reel
# Optional: PUBLISH_WRAPPER="<command prefix that supplies the Page token>"
#           PLATFORMS=instagram,facebook   POST_TO_X=1|0
# Generates today's media if missing (Pacific date), pushes it to GitHub Pages, then publishes one post.
set -euo pipefail
KIND="$1"
cd "$(dirname "$0")"
git pull -q --rebase
DATE=$(TZ=America/Los_Angeles date +%F)
if [ ! -f "media/$DATE/meta.json" ] || [ ! -f "media/$DATE/reel.mp4" ]; then
  timeout 1500 python3 generate.py --date "$DATE"
  git add "media/$DATE"
  git commit -q -m "Media for $DATE"
  git push -q
fi
timeout 1200 ${PUBLISH_WRAPPER:-} python3 publish.py --date "$DATE" --only "$KIND" --platforms "${PLATFORMS:-instagram,facebook}" || STATUS=$?
if [ "${POST_TO_X:-1}" = "1" ]; then
  timeout 900 python3 x_post.py --date "$DATE" --only "$KIND" || STATUS=$?
fi
git add posted.json
git commit -q -m "Posted $KIND for $DATE" || true
git push -q || true
exit "${STATUS:-0}"
