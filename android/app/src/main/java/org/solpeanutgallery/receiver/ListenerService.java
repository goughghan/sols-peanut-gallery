// SPDX-License-Identifier: GPL-3.0-or-later
package org.solpeanutgallery.receiver;

import android.annotation.SuppressLint;
import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Context;
import android.content.Intent;
import android.content.pm.ServiceInfo;
import android.os.Build;
import android.os.IBinder;
import android.os.PowerManager;
import android.util.Log;

import java.io.File;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;

public final class ListenerService extends Service {
    private static final String TAG = "PeanutListener";
    private static final String ACTION_START = "org.solpeanutgallery.receiver.START";
    private static final String ACTION_STOP = "org.solpeanutgallery.receiver.STOP";
    private static final String ACTION_COMPLETE = "org.solpeanutgallery.receiver.COMPLETE";
    private static final String ACTION_OPENED = "org.solpeanutgallery.receiver.OPENED";
    private static final String LISTENER_CHANNEL = "listener";
    private static final String REACTION_CHANNEL = "reactions-quiet-v2";
    private static final int LISTENER_NOTIFICATION = 100;
    private static final int REACTION_NOTIFICATION_BASE = 10_000;

    private final ExecutorService loopExecutor = Executors.newSingleThreadExecutor();
    private final ExecutorService completionExecutor = Executors.newSingleThreadExecutor();
    private final AtomicBoolean loopRunning = new AtomicBoolean(false);
    private AppPreferences preferences;
    private PowerManager.WakeLock wakeLock;

    static void start(Context context) {
        Intent intent = new Intent(context, ListenerService.class).setAction(ACTION_START);
        context.startForegroundService(intent);
    }

    static void stop(Context context) {
        Intent intent = new Intent(context, ListenerService.class).setAction(ACTION_STOP);
        context.startService(intent);
    }

    static void complete(Context context, Delivery delivery, String outcome, String error) {
        Intent intent = new Intent(context, ListenerService.class).setAction(ACTION_COMPLETE);
        delivery.putInto(intent);
        intent.putExtra("outcome", outcome);
        intent.putExtra("error", error);
        context.startForegroundService(intent);
    }

    static void opened(Context context, Delivery delivery) {
        Intent intent = new Intent(context, ListenerService.class).setAction(ACTION_OPENED);
        delivery.putInto(intent);
        context.startForegroundService(intent);
    }

    @Override
    public void onCreate() {
        super.onCreate();
        preferences = new AppPreferences(this);
        createChannels();
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        String action = intent == null ? ACTION_START : intent.getAction();
        if (ACTION_STOP.equals(action)) {
            stopForeground(true);
            stopSelf();
            return START_NOT_STICKY;
        }
        ensureForeground();
        acquireWakeLock();
        if (ACTION_OPENED.equals(action)) {
            handleOpened(intent);
        } else if (ACTION_COMPLETE.equals(action)) {
            handleCompletion(intent);
        }
        if (preferences.listenerEnabled()) startLoop();
        return START_STICKY;
    }

    private void handleOpened(Intent intent) {
        try {
            Delivery delivery = Delivery.from(intent);
            ActiveDeliveryState active = preferences.activeDelivery();
            if (!active.matches(delivery.deliveryId, delivery.sequence)
                    || active.remaining(System.currentTimeMillis()) == 0L) {
                Log.i(TAG, "Ignored stale activity-opened signal for sequence " + delivery.sequence);
                return;
            }
            notificationManager().cancel(reactionNotificationId(delivery.deliveryId));
        } catch (Exception invalid) {
            Log.w(TAG, "Ignored invalid activity-opened signal: " + invalid.getClass().getSimpleName());
        }
    }

    private void handleCompletion(Intent intent) {
        final Delivery delivery;
        final String outcome = intent.getStringExtra("outcome");
        final String error = intent.getStringExtra("error");
        try {
            delivery = Delivery.from(intent);
            if (!("displayed".equals(outcome) || "dismissed".equals(outcome) || "failed".equals(outcome))) {
                Log.w(TAG, "Ignored completion with an invalid outcome.");
                return;
            }
        } catch (Exception invalid) {
            Log.w(TAG, "Ignored invalid completion: " + invalid.getClass().getSimpleName());
            return;
        }
        long now = System.currentTimeMillis();
        if (!preferences.claimCompletion(delivery, now, now + 60_000L)) {
            Log.i(TAG, "Ignored stale or duplicate completion for sequence " + delivery.sequence);
            return;
        }
        notificationManager().cancel(reactionNotificationId(delivery.deliveryId));
        completionExecutor.execute(() -> {
            try {
                BridgeClient client = client();
                client.acknowledge(delivery, outcome, "failed".equals(outcome) ? boundedError(error) : null);
            } catch (Exception failure) {
                Log.w(TAG, "Completion acknowledgment will be retried through at-least-once delivery: "
                        + failure.getClass().getSimpleName());
            } finally {
                preferences.clearActiveDelivery(delivery);
            }
        });
    }

    private void startLoop() {
        if (!loopRunning.compareAndSet(false, true)) return;
        loopExecutor.execute(() -> {
            long backoff = 2_000L;
            try {
                while (preferences.listenerEnabled() && !Thread.currentThread().isInterrupted()) {
                    long now = System.currentTimeMillis();
                    ActiveDeliveryState active = preferences.activeDelivery();
                    long remaining = active.remaining(now);
                    if (remaining > 0) {
                        sleep(Math.min(remaining, 2_000L));
                        continue;
                    }
                    if (active.isPresent() && preferences.clearExpiredActive(now)) {
                        notificationManager().cancel(reactionNotificationId(active.deliveryId));
                    }
                    try {
                        Delivery delivery = client().next();
                        if (delivery == null) {
                            backoff = 2_000L;
                            sleep(2_000L);
                            continue;
                        }
                        File media = null;
                        if ("media".equals(delivery.kind)) {
                            try {
                                media = client().download(delivery, getCacheDir());
                            } catch (Exception mediaFailure) {
                                client().acknowledge(delivery, "failed", boundedError(mediaFailure.getMessage()));
                                continue;
                            }
                        }
                        long visible = DisplayTiming.milliseconds(delivery);
                        if (!preferences.activateDelivery(
                                delivery, System.currentTimeMillis() + visible + 5_000L)) {
                            throw new IllegalStateException("Cannot persist active delivery identity.");
                        }
                        showReaction(delivery, media);
                        backoff = 2_000L;
                    } catch (Exception networkOrProtocolFailure) {
                        Log.w(TAG, "Polling paused after " + networkOrProtocolFailure.getClass().getSimpleName());
                        sleep(backoff);
                        backoff = Math.min(backoff * 2L, 60_000L);
                    }
                }
            } finally {
                loopRunning.set(false);
                if (!preferences.listenerEnabled()) stopSelf();
            }
        });
    }

    private BridgeClient client() throws Exception {
        String token = new SecretStore(this).get();
        String url = preferences.bridgeUrl();
        if (token == null || url.isEmpty()) {
            preferences.setListenerEnabled(false);
            throw new IllegalStateException("receiver is not paired");
        }
        return new BridgeClient(url, token);
    }

    private void showReaction(Delivery delivery, File media) {
        Intent activity = new Intent(this, ReactionActivity.class)
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_SINGLE_TOP);
        delivery.putInto(activity);
        if (media != null) activity.putExtra("media_path", media.getAbsolutePath());
        int notificationId = reactionNotificationId(delivery.deliveryId);
        PendingIntent pending = PendingIntent.getActivity(
                this, notificationId, activity,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        Notification reaction = new Notification.Builder(this, REACTION_CHANNEL)
                .setSmallIcon(R.drawable.ic_display)
                .setContentTitle("Incoming reaction")
                .setContentText("Tap to display if it did not open automatically")
                .setCategory(Notification.CATEGORY_CALL)
                .setVisibility(Notification.VISIBILITY_PUBLIC)
                .setContentIntent(pending)
                .setFullScreenIntent(pending, true)
                .setOnlyAlertOnce(true)
                .setDefaults(0)
                .setAutoCancel(true)
                .build();
        notificationManager().notify(notificationId, reaction);
    }

    static int reactionNotificationId(String deliveryId) {
        return REACTION_NOTIFICATION_BASE + (deliveryId.hashCode() & 0x3fffffff);
    }

    private NotificationManager notificationManager() {
        return (NotificationManager) getSystemService(NOTIFICATION_SERVICE);
    }

    private void ensureForeground() {
        Intent settings = new Intent(this, ConfigActivity.class);
        PendingIntent pending = PendingIntent.getActivity(
                this, 0, settings, PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        Notification notification = new Notification.Builder(this, LISTENER_CHANNEL)
                .setSmallIcon(R.drawable.ic_display)
                .setContentTitle(getString(R.string.listener_active))
                .setContentText(getString(R.string.listener_detail))
                .setContentIntent(pending)
                .setOngoing(true)
                .setCategory(Notification.CATEGORY_SERVICE)
                .build();
        if (Build.VERSION.SDK_INT >= 34) {
            startForeground(LISTENER_NOTIFICATION, notification, ServiceInfo.FOREGROUND_SERVICE_TYPE_REMOTE_MESSAGING);
        } else {
            startForeground(LISTENER_NOTIFICATION, notification);
        }
    }

    private void createChannels() {
        NotificationManager manager = (NotificationManager) getSystemService(NOTIFICATION_SERVICE);
        NotificationChannel listener = new NotificationChannel(
                LISTENER_CHANNEL, getString(R.string.listener_channel), NotificationManager.IMPORTANCE_LOW);
        listener.setDescription("Persistent notification for the explicitly enabled receiver listener.");
        manager.createNotificationChannel(listener);
        NotificationChannel reactions = new NotificationChannel(
                REACTION_CHANNEL, getString(R.string.reaction_channel), NotificationManager.IMPORTANCE_HIGH);
        reactions.setDescription("Full-screen notifications for queued reactions.");
        reactions.setLockscreenVisibility(Notification.VISIBILITY_PUBLIC);
        reactions.setSound(null, null);
        reactions.enableVibration(false);
        manager.createNotificationChannel(reactions);
    }

    @SuppressLint("WakelockTimeout") // Explicit listener mode is continuous on a dedicated display; onDestroy releases it.
    private void acquireWakeLock() {
        if (wakeLock != null && wakeLock.isHeld()) return;
        PowerManager power = (PowerManager) getSystemService(POWER_SERVICE);
        wakeLock = power.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "sol-peanut-gallery:listener");
        wakeLock.setReferenceCounted(false);
        wakeLock.acquire();
    }

    private static String boundedError(String value) {
        String safe = value == null || value.isEmpty() ? "receiver could not display verified media" : value;
        return safe.length() > 180 ? safe.substring(0, 180) : safe;
    }

    private static void sleep(long milliseconds) {
        try {
            TimeUnit.MILLISECONDS.sleep(milliseconds);
        } catch (InterruptedException interrupted) {
            Thread.currentThread().interrupt();
        }
    }

    @Override
    public void onDestroy() {
        loopExecutor.shutdownNow();
        completionExecutor.shutdownNow();
        if (wakeLock != null && wakeLock.isHeld()) wakeLock.release();
        super.onDestroy();
    }

    @Override
    public IBinder onBind(Intent intent) { return null; }
}
