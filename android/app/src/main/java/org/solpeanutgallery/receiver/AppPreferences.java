// SPDX-License-Identifier: GPL-3.0-or-later
package org.solpeanutgallery.receiver;

import android.annotation.SuppressLint;
import android.content.Context;
import android.content.SharedPreferences;

final class AppPreferences {
    private static final String FILE = "receiver_preferences";
    private static final String URL = "bridge_url";
    private static final String ENABLED = "listener_enabled";
    private static final String SCREEN_OFF = "screen_off_after_reaction";
    private static final String ACTIVE_ID = "active_delivery_id";
    private static final String ACTIVE_SEQUENCE = "active_delivery_sequence";
    private static final String ACTIVE_UNTIL = "active_delivery_until";
    private static final String ACTIVE_COMPLETION = "active_delivery_completion_claimed";

    private final SharedPreferences values;

    AppPreferences(Context context) {
        values = context.getSharedPreferences(FILE, Context.MODE_PRIVATE);
    }

    String bridgeUrl() { return values.getString(URL, ""); }
    void setBridgeUrl(String value) { values.edit().putString(URL, value).apply(); }
    boolean listenerEnabled() { return values.getBoolean(ENABLED, false); }
    void setListenerEnabled(boolean value) { values.edit().putBoolean(ENABLED, value).apply(); }
    boolean screenOffAfterReaction() { return values.getBoolean(SCREEN_OFF, false); }
    void setScreenOffAfterReaction(boolean value) { values.edit().putBoolean(SCREEN_OFF, value).apply(); }

    synchronized ActiveDeliveryState activeDelivery() {
        return ActiveDeliveryState.restore(
                values.getString(ACTIVE_ID, null),
                values.getLong(ACTIVE_SEQUENCE, 0L),
                values.getLong(ACTIVE_UNTIL, 0L),
                values.getBoolean(ACTIVE_COMPLETION, false));
    }

    synchronized boolean activateDelivery(Delivery delivery, long activeUntil) {
        return writeActive(ActiveDeliveryState.active(delivery.deliveryId, delivery.sequence, activeUntil));
    }

    synchronized boolean claimCompletion(Delivery delivery, long now, long guardUntil) {
        ActiveDeliveryState current = activeDelivery();
        ActiveDeliveryState claimed = current.claimCompletion(
                delivery.deliveryId, delivery.sequence, now, guardUntil);
        return claimed != current && writeActive(claimed);
    }

    synchronized boolean clearActiveDelivery(Delivery delivery) {
        ActiveDeliveryState current = activeDelivery();
        ActiveDeliveryState cleared = current.clearIfMatches(delivery.deliveryId, delivery.sequence);
        return cleared != current && writeActive(cleared);
    }

    synchronized boolean clearExpiredActive(long now) {
        ActiveDeliveryState current = activeDelivery();
        ActiveDeliveryState cleared = current.clearIfExpired(now);
        return cleared != current && writeActive(cleared);
    }

    @SuppressLint("ApplySharedPref") // This identity must reach disk before display/ack transitions continue.
    private boolean writeActive(ActiveDeliveryState state) {
        SharedPreferences.Editor edit = values.edit();
        if (state.isPresent()) {
            edit.putString(ACTIVE_ID, state.deliveryId)
                    .putLong(ACTIVE_SEQUENCE, state.sequence)
                    .putLong(ACTIVE_UNTIL, state.activeUntil)
                    .putBoolean(ACTIVE_COMPLETION, state.completionClaimed);
        } else {
            edit.remove(ACTIVE_ID)
                    .remove(ACTIVE_SEQUENCE)
                    .remove(ACTIVE_UNTIL)
                    .remove(ACTIVE_COMPLETION);
        }
        return edit.commit();
    }
}
