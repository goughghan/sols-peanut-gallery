#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# Install a verified release wheel into the standard Linux layout.

set -euo pipefail

usage() {
    printf 'usage: %s [--dry-run|--apply] /path/to/sol_peanut_gallery_bridge-VERSION-py3-none-any.whl\n' "$0" >&2
}

mode='dry-run'
case "${1:-}" in
    '--dry-run') shift ;;
    '--apply') mode='apply'; shift ;;
    *) ;;
esac
if test "$#" -ne 1; then
    usage
    exit 2
fi

wheel_input=$1
if ! test -f "$wheel_input"; then
    printf 'error=wheel does not exist: %s\n' "$wheel_input" >&2
    exit 2
fi
wheel=$(readlink -f "$wheel_input")
wheel_name=$(basename "$wheel")
case "$wheel_name" in
    sol_peanut_gallery_bridge-*-py3-none-any.whl) ;;
    *) printf 'error=unexpected wheel filename: %s\n' "$wheel_name" >&2; exit 2 ;;
esac
version=${wheel_name#sol_peanut_gallery_bridge-}
version=${version%-py3-none-any.whl}
case "$version" in
    *[!0-9A-Za-z.-]*|'') printf 'error=invalid wheel version\n' >&2; exit 2 ;;
esac

script_directory=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
project_root=$(CDPATH= cd -- "$script_directory/../.." && pwd)
environment="/opt/sol-peanut-gallery/venv-$version"
configuration='/etc/sol-peanut-gallery/bridge.json'
catalog_directory='/var/lib/sol-peanut-gallery/catalog'
credential_directory='/etc/credstore.encrypted'
service_target='/etc/systemd/system/sol-peanut-gallery.service'

printf 'mode=%s\n' "$mode"
printf 'wheel=%s\n' "$wheel"
printf 'version=%s\n' "$version"
printf 'environment=%s\n' "$environment"
printf 'configuration=%s\n' "$configuration"
printf 'service=%s\n' "$service_target"
if test "$mode" != 'apply'; then
    printf 'result=no changes made; inspect this plan and rerun with --apply\n'
    exit 0
fi
if test "${EUID:-$(id -u)}" -ne 0; then
    printf 'error=--apply requires root\n' >&2
    exit 1
fi
for required in python3 openssl systemctl systemd-creds runuser; do
    if ! command -v "$required" >/dev/null 2>&1; then
        printf 'error=required command is missing: %s\n' "$required" >&2
        exit 1
    fi
done
if ! python3 -m venv --help >/dev/null 2>&1; then
    printf 'error=python3-venv is unavailable\n' >&2
    exit 1
fi

"$project_root/deploy/bin/create-layout.sh" --apply
install -d -o sol-peanut-gallery -g sol-peanut-gallery -m 0750 "$catalog_directory/media"
if ! test -e "$catalog_directory/catalog-index.json"; then
    printf '%s\n' '{"schema_version":1,"entries":[]}' |
        install -o sol-peanut-gallery -g sol-peanut-gallery -m 0640 /dev/stdin \
            "$catalog_directory/catalog-index.json"
fi
if ! test -e "$configuration"; then
    install -o root -g sol-peanut-gallery -m 0640 \
        "$project_root/deploy/config/bridge.example.json" "$configuration"
fi

if test -e "$environment"; then
    printf 'error=versioned environment already exists: %s\n' "$environment" >&2
    exit 1
fi
python3 -m venv "$environment"
"$environment/bin/python" -m pip install --no-deps "$wheel"
ln -sfn "$environment" /opt/sol-peanut-gallery/current

umask 077
install -d -o root -g root -m 0700 "$credential_directory"
systemd-creds setup >/dev/null
create_credential() {
    name=$1
    destination=$2
    if test -e "$destination"; then
        printf 'credential_preserved=%s\n' "$destination"
        return
    fi
    openssl rand -hex 32 | systemd-creds encrypt --quiet --with-key=host \
        --name="$name" - "$destination"
    chmod 0600 "$destination"
    printf 'credential_created=%s\n' "$destination"
}
create_credential transport-token "$credential_directory/sol-peanut-gallery-transport-token.cred"
create_credential status-token "$credential_directory/sol-peanut-gallery-status-token.cred"

install -o root -g root -m 0644 \
    "$project_root/deploy/systemd/sol-peanut-gallery.service" "$service_target"
systemctl daemon-reload
runuser -u sol-peanut-gallery -- \
    /opt/sol-peanut-gallery/current/bin/sol-peanut-gallery \
    --config "$configuration" validate-catalog

printf 'result=installed but not started\n'
printf 'next=sudo systemctl enable --now sol-peanut-gallery.service\n'
