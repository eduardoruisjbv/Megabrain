#!/usr/bin/env bash
# MEGABRAIN uninstaller - convenience wrapper for `bash install.sh uninstall`.
# Removes only what MEGABRAIN itself installed; your vault is kept unless you
# pass --purge-vault. Accepts the same options as install.sh (-y, --no-anim...).
d="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec bash "$d/install.sh" uninstall "$@"
