// SPDX-License-Identifier: GPL-3.0-or-later
package org.solpeanutgallery.receiver;

import android.app.Activity;
import android.app.admin.DevicePolicyManager;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Color;
import android.graphics.Movie;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.view.WindowManager;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.TextView;

import org.json.JSONException;

import java.io.File;
import java.io.IOException;

public final class ReactionActivity extends Activity {
    private static final String TAG = "PeanutReaction";
    private final Handler handler = new Handler(Looper.getMainLooper());
    private Delivery delivery;
    private boolean completed;

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON
                | WindowManager.LayoutParams.FLAG_SHOW_WHEN_LOCKED
                | WindowManager.LayoutParams.FLAG_TURN_SCREEN_ON
                | WindowManager.LayoutParams.FLAG_SECURE);
        immersive();
        try {
            delivery = Delivery.from(getIntent());
            View content = buildReaction();
            content.setOnLongClickListener(view -> {
                complete("dismissed", null);
                return true;
            });
            setContentView(content);
            handler.postDelayed(() -> complete("displayed", null), DisplayTiming.milliseconds(delivery));
            notifyOpened(delivery);
        } catch (Exception failure) {
            try {
                delivery = Delivery.from(getIntent());
                complete("failed", safeMessage(failure));
            } catch (JSONException invalidIntent) {
                finishAndRemoveTask();
            }
        }
    }

    @Override
    protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        try {
            Delivery incoming = Delivery.from(intent);
            if (delivery != null && delivery.sameIdentity(incoming)) {
                setIntent(intent);
                notifyOpened(incoming);
                return;
            }
            Log.w(TAG, "Ignored unexpected replacement delivery while reaction activity was active.");
            finishAndRemoveTask();
        } catch (Exception invalid) {
            Log.w(TAG, "Ignored invalid replacement delivery: " + invalid.getClass().getSimpleName());
        }
    }

    private void notifyOpened(Delivery opened) {
        try {
            ListenerService.opened(this, opened);
        } catch (RuntimeException unavailable) {
            Log.w(TAG, "Could not clear the opened reaction notification immediately.");
        }
    }

    private View buildReaction() throws IOException {
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setGravity(Gravity.CENTER);
        root.setPadding(dp(24), dp(18), dp(24), dp(18));
        root.setBackgroundColor(Color.BLACK);
        if ("text".equals(delivery.kind)) {
            TextView emoji = label(delivery.emoji, 104);
            root.addView(emoji, new LinearLayout.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT, 0, delivery.caption.isEmpty() ? 1f : 0.68f));
        } else {
            File media = verifiedCacheFile();
            View mediaView;
            if ("image/gif".equals(delivery.mimeType)) {
                Movie movie = Movie.decodeFile(media.getAbsolutePath());
                if (movie == null || movie.width() != delivery.width || movie.height() != delivery.height) {
                    throw new IOException("Verified GIF could not be decoded for display.");
                }
                mediaView = new GifView(this, movie);
            } else {
                Bitmap bitmap = BitmapFactory.decodeFile(media.getAbsolutePath());
                if (bitmap == null || bitmap.getWidth() != delivery.width || bitmap.getHeight() != delivery.height) {
                    throw new IOException("Verified JPEG could not be decoded for display.");
                }
                ImageView image = new ImageView(this);
                image.setImageBitmap(bitmap);
                image.setScaleType(ImageView.ScaleType.FIT_CENTER);
                mediaView = image;
            }
            root.addView(mediaView, new LinearLayout.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT, 0, delivery.caption.isEmpty() ? 1f : 0.78f));
        }
        if (!delivery.caption.isEmpty()) {
            TextView caption = label(delivery.caption, 34);
            caption.setPadding(dp(12), dp(8), dp(12), dp(8));
            root.addView(caption, new LinearLayout.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT, 0, "text".equals(delivery.kind) ? 0.32f : 0.22f));
        }
        return root;
    }

    private File verifiedCacheFile() throws IOException {
        String path = getIntent().getStringExtra("media_path");
        if (path == null) throw new IOException("Verified media path is missing.");
        File expectedDirectory = new File(getCacheDir(), "verified-media").getCanonicalFile();
        File candidate = new File(path).getCanonicalFile();
        if (!expectedDirectory.equals(candidate.getParentFile()) || !candidate.getName().startsWith(delivery.mediaId + ".")) {
            throw new IOException("Media path escaped the private verified cache.");
        }
        return candidate;
    }

    private TextView label(String value, int size) {
        TextView label = new TextView(this);
        label.setText(value);
        label.setTextColor(Color.WHITE);
        label.setTextSize(size);
        label.setGravity(Gravity.CENTER);
        return label;
    }

    private void complete(String outcome, String error) {
        if (completed || delivery == null) return;
        completed = true;
        handler.removeCallbacksAndMessages(null);
        ListenerService.complete(this, delivery, outcome, error);
        boolean lock = new AppPreferences(this).screenOffAfterReaction();
        DevicePolicyManager policy = (DevicePolicyManager) getSystemService(Context.DEVICE_POLICY_SERVICE);
        ComponentName admin = new ComponentName(this, ScreenAdminReceiver.class);
        finishAndRemoveTask();
        if (lock && policy.isAdminActive(admin)) policy.lockNow();
    }

    private void immersive() {
        getWindow().getDecorView().setSystemUiVisibility(
                View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
                        | View.SYSTEM_UI_FLAG_FULLSCREEN
                        | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
                        | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
                        | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
                        | View.SYSTEM_UI_FLAG_LAYOUT_STABLE);
    }

    @Override
    public void onWindowFocusChanged(boolean hasFocus) {
        super.onWindowFocusChanged(hasFocus);
        if (hasFocus) immersive();
    }

    private int dp(int value) { return Math.round(value * getResources().getDisplayMetrics().density); }
    private static String safeMessage(Exception error) {
        String message = error.getMessage();
        if (message == null || message.isEmpty()) message = error.getClass().getSimpleName();
        return message.length() > 180 ? message.substring(0, 180) : message;
    }
}
