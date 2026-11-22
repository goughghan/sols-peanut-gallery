// SPDX-License-Identifier: GPL-3.0-or-later
package org.solpeanutgallery.receiver;

final class ActiveDeliveryState {
    private static final ActiveDeliveryState NONE = new ActiveDeliveryState(null, 0L, 0L, false);

    final String deliveryId;
    final long sequence;
    final long activeUntil;
    final boolean completionClaimed;

    private ActiveDeliveryState(String deliveryId, long sequence, long activeUntil, boolean completionClaimed) {
        this.deliveryId = deliveryId;
        this.sequence = sequence;
        this.activeUntil = activeUntil;
        this.completionClaimed = completionClaimed;
    }

    static ActiveDeliveryState none() { return NONE; }

    static ActiveDeliveryState restore(String deliveryId, long sequence, long activeUntil,
                                       boolean completionClaimed) {
        if (deliveryId == null || deliveryId.isEmpty() || sequence < 1L || activeUntil < 1L) return NONE;
        return new ActiveDeliveryState(deliveryId, sequence, activeUntil, completionClaimed);
    }

    static ActiveDeliveryState active(String deliveryId, long sequence, long activeUntil) {
        if (deliveryId == null || deliveryId.isEmpty() || sequence < 1L || activeUntil < 1L) {
            throw new IllegalArgumentException("Active delivery identity is invalid.");
        }
        return new ActiveDeliveryState(deliveryId, sequence, activeUntil, false);
    }

    boolean isPresent() { return deliveryId != null; }

    boolean matches(String candidateId, long candidateSequence) {
        return isPresent() && deliveryId.equals(candidateId) && sequence == candidateSequence;
    }

    long remaining(long now) {
        return isPresent() ? Math.max(0L, activeUntil - now) : 0L;
    }

    ActiveDeliveryState claimCompletion(String candidateId, long candidateSequence,
                                        long now, long guardUntil) {
        if (!matches(candidateId, candidateSequence) || completionClaimed
                || activeUntil <= now || guardUntil <= now) return this;
        return new ActiveDeliveryState(deliveryId, sequence, guardUntil, true);
    }

    ActiveDeliveryState clearIfMatches(String candidateId, long candidateSequence) {
        return matches(candidateId, candidateSequence) ? NONE : this;
    }

    ActiveDeliveryState clearIfExpired(long now) {
        return isPresent() && activeUntil <= now ? NONE : this;
    }
}
