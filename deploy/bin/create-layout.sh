#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# Create only the neutral service account and directory layout.

set -euo pipefail

service_user='sol-peanut-gallery'
service_group='sol-peanut-gallery'
paths=(
    '/opt/sol-peanut-gallery'
    '/etc/sol-peanut-gallery'
    '/var/lib/sol-peanut-gallery'
    '/var/log/sol-peanut-gallery'
)

apply=false
case "${1:-}" in
    '') ;;
    '--apply') apply=true ;;
    *) printf 'usage: %s [--apply]\n' "$0" >&2; exit 2 ;;
esac

if test "$apply" = true; then
    printf 'mode=apply\n'
else
    printf 'mode=dry-run\n'
fi
printf 'service_user=%s\n' "$service_user"
printf 'service_group=%s\n' "$service_group"
for path in "${paths[@]}"; do
    printf 'directory=%s\n' "$path"
done

if test "$apply" = false; then
    printf 'result=no changes made; pass --apply only after separate review and approval\n'
    exit 0
fi

if test "${EUID:-$(id -u)}" -ne 0; then
    printf 'error=--apply requires root\n' >&2
    exit 1
fi

if ! getent group "$service_group" >/dev/null 2>&1; then
    groupadd --system "$service_group"
fi
if ! id -u "$service_user" >/dev/null 2>&1; then
    useradd --system --gid "$service_group" --home-dir /var/lib/sol-peanut-gallery \
        --shell /usr/sbin/nologin "$service_user"
fi

install -d -o root -g "$service_group" -m 0750 /opt/sol-peanut-gallery
install -d -o root -g "$service_group" -m 0750 /etc/sol-peanut-gallery
install -d -o "$service_user" -g "$service_group" -m 0750 /var/lib/sol-peanut-gallery
install -d -o "$service_user" -g "$service_group" -m 0750 /var/log/sol-peanut-gallery

printf 'result=neutral layout created; no service installed or activated\n'
