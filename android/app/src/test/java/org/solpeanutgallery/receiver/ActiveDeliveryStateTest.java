// SPDX-License-Identifier: GPL-3.0-or-later
package org.solpeanutgallery.receiver;

import org.junit.Test;

import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertSame;
import static org.junit.Assert.assertTrue;

public final class ActiveDeliveryStateTest {
    private static final String TEN = "00000000-0000-4000-8000-000000000010";
    private static final String ELEVEN = "00000000-0000-4000-8000-000000000011";

    @Test
    public void staleCompletionCannotReleaseNewerBurstDelivery() {
        ActiveDeliveryState sequenceTen = ActiveDeliveryState.active(TEN, 10L, 10_000L);
        ActiveDeliveryState completingTen = sequenceTen.claimCompletion(TEN, 10L, 1_000L, 61_000L);
        ActiveDeliveryState finishedTen = completingTen.clearIfMatches(TEN, 10L);
        ActiveDeliveryState sequenceEleven = ActiveDeliveryState.active(ELEVEN, 11L, 20_000L);

        assertFalse(finishedTen.isPresent());
        assertSame(sequenceEleven, sequenceEleven.claimCompletion(TEN, 10L, 2_000L, 62_000L));
        assertSame(sequenceEleven, sequenceEleven.clearIfMatches(TEN, 10L));
        assertTrue(sequenceEleven.matches(ELEVEN, 11L));
    }

    @Test
    public void duplicateCompletionCanBeClaimedOnlyOnce() {
        ActiveDeliveryState active = ActiveDeliveryState.active(TEN, 10L, 10_000L);
        ActiveDeliveryState claimed = active.claimCompletion(TEN, 10L, 1_000L, 61_000L);

        assertTrue(claimed.completionClaimed);
        assertSame(claimed, claimed.claimCompletion(TEN, 10L, 2_000L, 62_000L));
    }

    @Test
    public void expiredCompletionIsRejectedForAtLeastOnceRedelivery() {
        ActiveDeliveryState expired = ActiveDeliveryState.active(TEN, 10L, 5_000L);

        assertSame(expired, expired.claimCompletion(TEN, 10L, 5_000L, 65_000L));
        assertFalse(expired.clearIfExpired(5_000L).isPresent());
    }

    @Test
    public void matchingCompletionDoesNotClearDifferentIdentity() {
        ActiveDeliveryState active = ActiveDeliveryState.active(ELEVEN, 11L, 20_000L);

        assertSame(active, active.clearIfMatches(ELEVEN, 10L));
        assertSame(active, active.clearIfMatches(TEN, 11L));
        assertFalse(active.clearIfMatches(ELEVEN, 11L).isPresent());
    }

    @Test
    public void restoredInFlightCompletionRetainsIdentityAndGuard() {
        ActiveDeliveryState restored = ActiveDeliveryState.restore(ELEVEN, 11L, 61_000L, true);

        assertTrue(restored.matches(ELEVEN, 11L));
        assertTrue(restored.completionClaimed);
        assertTrue(restored.remaining(1_000L) == 60_000L);
    }
}
