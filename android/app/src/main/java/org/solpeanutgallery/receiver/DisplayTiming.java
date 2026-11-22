// SPDX-License-Identifier: GPL-3.0-or-later
package org.solpeanutgallery.receiver;

final class DisplayTiming {
    private DisplayTiming() { }

    static long milliseconds(Delivery delivery) {
        return milliseconds(delivery.displaySeconds, "image/gif".equals(delivery.mimeType),
                !delivery.caption.isEmpty(), delivery.durationMs);
    }

    static long milliseconds(int displaySeconds, boolean animatedGif, boolean captioned, int durationMs) {
        long minimum = displaySeconds * 1000L;
        if (!animatedGif) return minimum;
        if (captioned) minimum = Math.max(minimum, 12_000L);
        int loop = durationMs > 0 ? durationMs : 1_000;
        if (4L * loop <= 30_000L) minimum = Math.max(minimum, 4L * loop);
        if (minimum >= 30_000L) return 30_000L;
        long boundary = ((minimum + loop - 1L) / loop) * loop;
        if (boundary <= 30_000L) return boundary;
        long lastBoundary = (30_000L / loop) * loop;
        return lastBoundary >= minimum ? lastBoundary : 30_000L;
    }
}
