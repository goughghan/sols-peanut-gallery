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
import android.os.Build;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;
import android.util.TypedValue;
import android.view.DisplayCutout;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.view.Window;
import android.view.WindowInsets;
import android.view.WindowInsetsController;
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
        prepareWindowBeforeCreate();
        super.onCreate(state);
        disableLaunchTransition();
        immersive();
        try {
            delivery = Delivery.from(getIntent());
            View content = buildReaction();
            content.setOnLongClickListener(view -> {
                complete("dismissed", null);
                return true;
            });
            setContentView(content);
            installImmersiveGuard();
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

    private void prepareWindowBeforeCreate() {
        Window window = getWindow();
        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON
                | WindowManager.LayoutParams.FLAG_SHOW_WHEN_LOCKED
                | WindowManager.LayoutParams.FLAG_TURN_SCREEN_ON
                | WindowManager.LayoutParams.FLAG_FULLSCREEN
                | WindowManager.LayoutParams.FLAG_SECURE);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            window.setNavigationBarContrastEnforced(false);
            window.setStatusBarContrastEnforced(false);
        }
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
            WindowManager.LayoutParams attributes = window.getAttributes();
            attributes.layoutInDisplayCutoutMode =
                    WindowManager.LayoutParams.LAYOUT_IN_DISPLAY_CUTOUT_MODE_SHORT_EDGES;
            window.setAttributes(attributes);
        }
        immersive();
    }

    @SuppressWarnings("deprecation")
    private void disableLaunchTransition() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.UPSIDE_DOWN_CAKE) {
            overrideActivityTransition(OVERRIDE_TRANSITION_OPEN, 0, 0);
        } else {
            overridePendingTransition(0, 0);
        }
    }

    @SuppressWarnings("deprecation")
    private void installImmersiveGuard() {
        View decor = getWindow().getDecorView();
        decor.setOnSystemUiVisibilityChangeListener(visibility -> {
            int hidden = View.SYSTEM_UI_FLAG_FULLSCREEN | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION;
            if ((visibility & hidden) != hidden) decor.post(this::immersive);
        });
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
        installBalancedCutoutPadding(root);
        if ("text".equals(delivery.kind)) {
            if (!delivery.emoji.isEmpty()) {
                TextView emoji = label(delivery.emoji, 104);
                root.addView(emoji, new LinearLayout.LayoutParams(
                        ViewGroup.LayoutParams.MATCH_PARENT, 0, delivery.caption.isEmpty() ? 1f : 0.65f));
            }
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
                    ViewGroup.LayoutParams.MATCH_PARENT, 0, delivery.caption.isEmpty() ? 1f : 0.70f));
        }
        if (!delivery.caption.isEmpty()) {
            TextView caption = label(delivery.caption, 34);
            caption.setPadding(dp(12), dp(8), dp(12), dp(8));
            caption.setIncludeFontPadding(false);
            caption.setMaxLines(4);
            caption.setLineSpacing(0f, 1.05f);
            caption.setAutoSizeTextTypeUniformWithConfiguration(
                    14, 34, 1, TypedValue.COMPLEX_UNIT_SP);
            float captionWeight = "text".equals(delivery.kind)
                    ? (delivery.emoji.isEmpty() ? 1f : 0.35f)
                    : 0.30f;
            root.addView(caption, new LinearLayout.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT, 0, captionWeight));
        }
        return root;
    }

    private void installBalancedCutoutPadding(View root) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.P) return;
        int horizontal = dp(24);
        int vertical = dp(18);
        root.setOnApplyWindowInsetsListener((view, insets) -> {
            DisplayCutout cutout = insets.getDisplayCutout();
            if (cutout == null) {
                view.setPadding(horizontal, vertical, horizontal, vertical);
                return insets;
            }
            int side = BalancedCutoutPadding.maximum(
                    cutout.getSafeInsetLeft(), cutout.getSafeInsetRight());
            int end = BalancedCutoutPadding.maximum(
                    cutout.getSafeInsetTop(), cutout.getSafeInsetBottom());
            view.setPadding(horizontal + side, vertical + end,
                    horizontal + side, vertical + end);
            return insets;
        });
        root.requestApplyInsets();
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

    @SuppressWarnings("deprecation")
    private void immersive() {
        Window window = getWindow();
        window.getDecorView().setSystemUiVisibility(
                View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
                        | View.SYSTEM_UI_FLAG_LOW_PROFILE
                        | View.SYSTEM_UI_FLAG_FULLSCREEN
                        | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
                        | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
                        | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
                        | View.SYSTEM_UI_FLAG_LAYOUT_STABLE);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            window.setDecorFitsSystemWindows(false);
            WindowInsetsController controller = window.getInsetsController();
            if (controller != null) {
                controller.setSystemBarsBehavior(
                        WindowInsetsController.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE);
                controller.hide(WindowInsets.Type.systemBars());
            }
        }
    }

    @Override
    public void onAttachedToWindow() {
        super.onAttachedToWindow();
        immersive();
    }

    @Override
    protected void onResume() {
        super.onResume();
        immersive();
    }

    @Override
    protected void onPostResume() {
        super.onPostResume();
        immersive();
        getWindow().getDecorView().post(this::immersive);
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
