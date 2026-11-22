// SPDX-License-Identifier: GPL-3.0-or-later
package org.solpeanutgallery.receiver;

import android.content.Intent;

import org.json.JSONException;
import org.json.JSONObject;

import java.util.Locale;
import java.util.UUID;

final class Delivery {
    final String deliveryId;
    final long sequence;
    final int displaySeconds;
    final String kind;
    final String emoji;
    final String caption;
    final String mediaId;
    final String mimeType;
    final int byteCount;
    final String sha256;
    final int width;
    final int height;
    final int durationMs;

    private Delivery(String deliveryId, long sequence, int displaySeconds, String kind,
                     String emoji, String caption, String mediaId, String mimeType,
                     int byteCount, String sha256, int width, int height, int durationMs) {
        this.deliveryId = deliveryId;
        this.sequence = sequence;
        this.displaySeconds = displaySeconds;
        this.kind = kind;
        this.emoji = emoji;
        this.caption = caption;
        this.mediaId = mediaId;
        this.mimeType = mimeType;
        this.byteCount = byteCount;
        this.sha256 = sha256;
        this.width = width;
        this.height = height;
        this.durationMs = durationMs;
    }

    static Delivery parse(JSONObject root) throws JSONException {
        String deliveryId = canonicalUuid(root.getString("delivery_id"));
        canonicalUuid(root.getString("request_id"));
        long sequence = root.getLong("sequence");
        int seconds = root.getInt("display_seconds");
        if (sequence < 1 || seconds < 3 || seconds > 30) throw new JSONException("invalid delivery bounds");
        JSONObject content = root.getJSONObject("content");
        String kind = content.getString("kind");
        String caption = content.optString("caption", "");
        if (caption.length() > 180) throw new JSONException("caption is too long");
        if ("text".equals(kind)) {
            String emoji = content.optString("emoji", "");
            int points = emoji.codePointCount(0, emoji.length());
            if ((emoji.isEmpty() && caption.isEmpty()) || points > 16) throw new JSONException("invalid text delivery");
            return new Delivery(deliveryId, sequence, seconds, kind, emoji, caption,
                    null, null, 0, null, 0, 0, 0);
        }
        if (!"media".equals(kind)) throw new JSONException("unsupported delivery kind");
        String mediaId = canonicalUuid(content.getString("media_id"));
        String mime = content.getString("mime_type");
        if (!"image/jpeg".equals(mime) && !"image/gif".equals(mime)) throw new JSONException("invalid media type");
        int bytes = content.getInt("bytes");
        int width = content.getInt("width");
        int height = content.getInt("height");
        String digest = content.getString("sha256").toLowerCase(Locale.ROOT);
        int duration = content.optInt("duration_ms", 0);
        if (bytes < 1 || bytes > 8_388_608 || width < 1 || width > 8192 || height < 1 || height > 8192
                || ((long) width * height) > 33_554_432L || !digest.matches("[0-9a-f]{64}")
                || duration < 0 || duration > 300_000) {
            throw new JSONException("invalid media bounds");
        }
        return new Delivery(deliveryId, sequence, seconds, kind, "", caption,
                mediaId, mime, bytes, digest, width, height, duration);
    }

    private static String canonicalUuid(String value) throws JSONException {
        try {
            String canonical = UUID.fromString(value).toString();
            if (!canonical.equals(value)) throw new IllegalArgumentException();
            return canonical;
        } catch (IllegalArgumentException error) {
            throw new JSONException("invalid UUID");
        }
    }

    void putInto(Intent intent) {
        intent.putExtra("delivery_id", deliveryId);
        intent.putExtra("sequence", sequence);
        intent.putExtra("display_seconds", displaySeconds);
        intent.putExtra("kind", kind);
        intent.putExtra("emoji", emoji);
        intent.putExtra("caption", caption);
        intent.putExtra("media_id", mediaId);
        intent.putExtra("mime_type", mimeType);
        intent.putExtra("bytes", byteCount);
        intent.putExtra("sha256", sha256);
        intent.putExtra("width", width);
        intent.putExtra("height", height);
        intent.putExtra("duration_ms", durationMs);
    }

    boolean sameIdentity(Delivery other) {
        return other != null && deliveryId.equals(other.deliveryId) && sequence == other.sequence;
    }

    static Delivery from(Intent intent) throws JSONException {
        String deliveryId = canonicalUuid(intent.getStringExtra("delivery_id"));
        long sequence = intent.getLongExtra("sequence", 0);
        int seconds = intent.getIntExtra("display_seconds", 0);
        String kind = intent.getStringExtra("kind");
        String emoji = intent.getStringExtra("emoji");
        String caption = intent.getStringExtra("caption");
        if (sequence < 1 || seconds < 3 || seconds > 30 || kind == null || caption == null) {
            throw new JSONException("invalid internal delivery");
        }
        if ("text".equals(kind)) {
            return new Delivery(deliveryId, sequence, seconds, kind, emoji == null ? "" : emoji,
                    caption, null, null, 0, null, 0, 0, 0);
        }
        String mediaId = canonicalUuid(intent.getStringExtra("media_id"));
        return new Delivery(deliveryId, sequence, seconds, kind, "", caption, mediaId,
                intent.getStringExtra("mime_type"), intent.getIntExtra("bytes", 0),
                intent.getStringExtra("sha256"), intent.getIntExtra("width", 0),
                intent.getIntExtra("height", 0), intent.getIntExtra("duration_ms", 0));
    }
}
