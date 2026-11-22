#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# Read-only Raspberry Pi compatibility and health inventory.

set -u

warnings=0

warn() {
    printf 'warning=%s\n' "$1"
    warnings=$((warnings + 1))
}

model='unavailable'
if test -r /proc/device-tree/model; then
    model=$(tr -d '\0' </proc/device-tree/model)
fi
printf 'model=%s\n' "$model"

architecture=$(uname -m)
printf 'architecture=%s\n' "$architecture"
printf 'word_size=%s\n' "$(getconf LONG_BIT 2>/dev/null || printf 'unavailable')"

if command -v dpkg >/dev/null 2>&1; then
    printf 'package_architecture=%s\n' "$(dpkg --print-architecture)"
else
    printf 'package_architecture=unavailable\n'
fi

case "$architecture" in
    armv7l|aarch64) ;;
    *) warn "non-ARM host; useful for script testing but not the intended Pi target" ;;
esac

if test -r /proc/meminfo; then
    memory_kib=$(awk '/^MemTotal:/{print $2}' /proc/meminfo)
    printf 'memory_total_kib=%s\n' "${memory_kib:-unavailable}"
else
    printf 'memory_total_kib=unavailable\n'
fi

state_available_kib=$(df -Pk /var/lib 2>/dev/null | awk 'END{print $4}')
printf 'state_available_kib=%s\n' "${state_available_kib:-unavailable}"

if command -v vcgencmd >/dev/null 2>&1; then
    printf 'temperature=%s\n' "$(vcgencmd measure_temp 2>/dev/null || printf 'unavailable')"
    printf 'throttled=%s\n' "$(vcgencmd get_throttled 2>/dev/null || printf 'unavailable')"
else
    printf 'temperature=unavailable\n'
    printf 'throttled=unavailable\n'
fi

printf 'kernel=%s\n' "$(uname -r)"
if command -v systemctl >/dev/null 2>&1; then
    printf 'systemd=%s\n' "$(systemctl --version | awk 'NR==1{print $2}')"
else
    printf 'systemd=unavailable\n'
    warn 'systemd is unavailable'
fi

if command -v python3 >/dev/null 2>&1; then
    printf 'python=%s\n' "$(python3 --version 2>&1 | awk '{print $2}')"
else
    printf 'python=unavailable\n'
    warn 'python3 is unavailable'
fi

if command -v openssl >/dev/null 2>&1; then
    printf 'openssl=%s\n' "$(openssl version | awk '{print $2}')"
else
    printf 'openssl=unavailable\n'
    warn 'openssl is unavailable'
fi

host_name=$(hostname)
printf 'hostname=%s\n' "$host_name"
if command -v getent >/dev/null 2>&1 && getent hosts "$host_name" >/dev/null 2>&1; then
    printf 'hostname_resolves=yes\n'
else
    printf 'hostname_resolves=no\n'
    warn 'the local hostname does not resolve through the configured hosts sources'
fi

if command -v timedatectl >/dev/null 2>&1; then
    synchronized=$(timedatectl show -p NTPSynchronized --value 2>/dev/null || true)
    printf 'clock_synchronized=%s\n' "${synchronized:-unavailable}"
else
    printf 'clock_synchronized=unavailable\n'
fi

if command -v systemctl >/dev/null 2>&1; then
    failed_units=$(systemctl --failed --no-legend --plain 2>/dev/null | awk 'NF{count++} END{print count+0}')
    printf 'failed_units=%s\n' "$failed_units"
else
    printf 'failed_units=unavailable\n'
fi

if test "$warnings" -eq 0; then
    printf 'preflight_status=ready\n'
else
    printf 'preflight_status=review\n'
fi
printf 'warning_count=%d\n' "$warnings"
