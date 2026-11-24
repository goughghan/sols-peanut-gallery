# Beginner quick start

This guide proves the local display path first, then adds an assistant only if
you want one. You do not need a Raspberry Pi: any always-on Linux computer with
Python 3.9+, systemd, and network access from the Android device can host the
bridge.

## What you need

- A Linux host on your private network. Raspberry Pi OS Lite, Debian, Ubuntu,
  and similar systemd distributions are suitable.
- An Android 8.0 or newer phone/tablet that can remain on the same network.
- The release wheel, Android APK, and `SHA256SUMS` from the GitHub release.
- This repository's matching release source, either from the tag or source
  archive.

The reference host is a Raspberry Pi 2 Model B with 1 GB RAM and 32-bit ARMv7
Raspberry Pi OS. Newer ARM and x86-64 Linux computers also work.

## 1. Verify the downloads

Put the downloaded wheel, APK, and `SHA256SUMS` in one directory and run:

```text
sha256sum --check SHA256SUMS
```

Every listed file must report `OK`. Stop if a hash fails.

Before sideloading, scan the APK with a security tool you trust and investigate
any alert. The checksum proves that your download matches the published file;
it is not a substitute for source review or malware scanning.

If Android SDK Build Tools are available, verify the APK signature directly:

```text
apksigner verify --verbose --print-certs SolPeanutGallery-1.0.0.apk
```

The release must verify with APK Signature Schemes v2 and v3. Its signer
certificate SHA-256 fingerprint is:

```text
3c888c4e480bee019fb2904a03da9f86e6ac479e790353c85adf5852cd2f6e99
```

Stop if the signature fails or the fingerprint differs. The matching public
certificate is also supplied as a release asset.

## 2. Prepare the Linux host

Install the small set of operating-system prerequisites. On Raspberry Pi OS,
Debian, or Ubuntu:

```text
sudo apt update
sudo apt install python3 python3-venv openssl
```

From the matching release source directory, run the read-only preflight:

```text
./deploy/bin/pi-preflight.sh
```

Review the proposed installation without changing the host:

```text
./deploy/bin/install-bridge.sh --dry-run /path/to/sol_peanut_gallery_bridge-1.0.0-py3-none-any.whl
```

If the paths are correct, apply the plan:

```text
sudo ./deploy/bin/install-bridge.sh --apply /path/to/sol_peanut_gallery_bridge-1.0.0-py3-none-any.whl
```

The installer creates a dedicated unprivileged account, versioned Python
environment, empty catalog, host-encrypted random credentials, and hardened
systemd unit. It does **not** start the service automatically.

Start it only after the installer reports a valid empty catalog:

```text
sudo systemctl enable --now sol-peanut-gallery.service
systemctl status sol-peanut-gallery.service --no-pager
```

The final status should be `active (running)`. Do not expose port 8765 through
your router or directly to the public internet.

## 3. Install and pair Android

Copy `SolPeanutGallery-1.0.0.apk` to the Android device and open it. Android may
ask you to permit installation from the file manager you used; grant that only
for this installation, then turn it back off if desired.

On the Linux host, create a five-minute one-time pairing code:

```text
sudo -u sol-peanut-gallery \
  /opt/sol-peanut-gallery/current/bin/sol-peanut-gallery \
  --config /etc/sol-peanut-gallery/bridge.json pairing-code
```

In the Android app:

1. Enter `http://HOST-IP:8765` as the bridge URL. Replace `HOST-IP` with the
   Linux host's private network address.
2. Enter the six-digit pairing code and a recognizable device label.
3. Tap **Pair receiver**, then **Enable foreground listener**.
4. Allow notifications and full-screen reactions when Android requests them.
5. For a dedicated display, enable **Turn the dedicated display off after each
   reaction** and approve the optional device-administrator permission.
6. On aggressive battery-saving devices, set this app to unrestricted battery
   use so its foreground listener is not stopped.

## 4. Prove local delivery

Darken the Android screen, then run this on the Linux host:

```text
sudo -u sol-peanut-gallery \
  /opt/sol-peanut-gallery/current/bin/sol-peanut-gallery \
  --config /etc/sol-peanut-gallery/bridge.json \
  queue-local --emoji "🥜" --caption "The Peanut Gallery is listening."
```

The receiver should wake, show the reaction in landscape, acknowledge it, and
optionally turn the display dark again. Complete this local test before adding
a tunnel, assistant, automation, or private media.

## 5. Optional media catalog

The empty catalog supports text and emoji immediately. To add JPEG and GIF
reactions, place media you have the right to use under:

```text
/var/lib/sol-peanut-gallery/catalog/media/
```

Create entries in `catalog-index.json` using `sample-catalog/README.md` as the
format guide, then validate before restarting:

```text
sudo -u sol-peanut-gallery \
  /opt/sol-peanut-gallery/current/bin/sol-peanut-gallery \
  --config /etc/sol-peanut-gallery/bridge.json validate-catalog
```

The app and public release contain no memes, GIF collection, private catalog,
address, or credential.

## 6. Optional ChatGPT connection

ChatGPT can connect through a custom MCP plugin. For a bridge on a private
network, use OpenAI's Secure MCP Tunnel instead of port forwarding. Configure
the tunnel client to reach `http://127.0.0.1:8765/mcp` and add the
`X-Peanut-Gallery-Token` header from the bridge's protected transport
credential. The included inactive tunnel unit template shows the intended
least-privilege service shape.

Then, in ChatGPT on the web:

1. Open **Plugins** and choose **Add custom MCP server**.
2. Select **Tunnel** and choose the tunnel associated with this bridge.
3. Review the discovered `find_display_items` and `queue_display` tools.
4. Create and install the personal plugin, then select it with `@` in a chat.

OpenAI's current instructions are:

- <https://developers.openai.com/api/docs/guides/custom-mcp-server>
- <https://developers.openai.com/api/docs/guides/tools-connectors-mcp>

Workspace policy and feature availability can differ. The project is not tied
to ChatGPT; another assistant, Home Assistant, Node-RED, monitoring service, or
ordinary script can use the authenticated HTTP/MCP contract instead.

## A useful assistant instruction

Adapt this to your own taste:

> You may occasionally use Sol's Peanut Gallery when a short visual reaction
> genuinely adds value. Prefer an existing catalog item when it fits; text and
> emoji are always available. Keep captions brief, avoid sensitive content,
> and do not interrupt urgent or serious work. A successful tool call means the
> reaction was queued, not necessarily displayed.

## Troubleshooting

- **The phone cannot pair:** open `http://HOST-IP:8765/healthz` in the phone's
  browser. If it cannot connect, confirm both devices are on the same network
  and that the host firewall permits private-LAN access to TCP 8765.
- **The code is invalid:** pairing codes expire after five minutes and work
  only once. Generate a new one.
- **The reaction becomes a notification:** grant notification and full-screen
  reaction access. On Android 14+, review the app's full-screen intent setting.
- **Listening stops later:** allow unrestricted battery use and confirm the
  persistent listener notification remains present.
- **The service will not start:** run
  `journalctl -u sol-peanut-gallery.service -n 100 --no-pager` and review the
  first error before changing anything.

See [`OPERATIONS.md`](OPERATIONS.md) for upgrades, recovery, removal, and
credential boundaries.
