// SPDX-License-Identifier: GPL-3.0-or-later
package org.solpeanutgallery.receiver;

import org.junit.Test;

import static org.junit.Assert.assertEquals;

public final class DisplayTimingTest {
    @Test
    public void plainContentUsesRequestedDuration() {
        assertEquals(7_000L, DisplayTiming.milliseconds(7, false, false, 0));
    }

    @Test
    public void shortGifGetsAtLeastFourCompleteLoops() {
        assertEquals(8_000L, DisplayTiming.milliseconds(3, true, false, 2_000));
    }

    @Test
    public void captionedGifGetsAtLeastTwelveSecondsAndEndsOnBoundary() {
        assertEquals(12_500L, DisplayTiming.milliseconds(3, true, true, 2_500));
    }

    @Test
    public void gifNeverExceedsThirtySecondCeiling() {
        assertEquals(30_000L, DisplayTiming.milliseconds(30, true, true, 8_000));
    }

    @Test
    public void longerGifUsesAvailableLoopBoundary() {
        assertEquals(16_000L, DisplayTiming.milliseconds(3, true, true, 8_000));
    }
}
