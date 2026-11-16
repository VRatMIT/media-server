#!/usr/bin/env bash
set -euo pipefail
cd /home/pi/media-server

as_pi() { sudo -u pi -H "$@"; }

as_pi git fetch origin
LOCAL=$(as_pi git rev-parse HEAD)
REMOTE=$(as_pi git rev-parse @{u})

if [ "$LOCAL" != "$REMOTE" ]; then
    echo "$LOCAL to $REMOTE"
    as_pi git pull --ff-only
    as_pi /home/pi/.local/bin/uv sync --frozen
    systemctl restart bot
else
    echo "No update needed."
fi
