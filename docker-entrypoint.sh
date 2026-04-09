#!/bin/bash
set -e

# Default UID/GID to 1000 if not provided
PUID=${PUID:-1000}
PGID=${PGID:-1000}

# Create group if it doesn't exist
if ! getent group appgroup > /dev/null 2>&1; then
    groupadd -g "$PGID" appgroup
fi

# Create user if it doesn't exist
if ! id appuser > /dev/null 2>&1; then
    useradd -u "$PUID" -g "$PGID" -m -s /bin/bash appuser
fi

# Ensure correct ownership of working directory
chown -R appuser:appgroup /MoneyPrinterTurbo 2>/dev/null || true

# Execute command as appuser
exec gosu appuser "$@"
