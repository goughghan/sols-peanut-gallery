// SPDX-License-Identifier: GPL-3.0-or-later
package org.solpeanutgallery.receiver;

import android.Manifest;
import android.app.Activity;
import android.app.admin.DevicePolicyManager;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.graphics.Typeface;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.provider.Settings;
import android.text.InputType;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.CheckBox;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public final class ConfigActivity extends Activity {
    private final ExecutorService executor = Executors.newSingleThreadExecutor();
    private AppPreferences preferences;
    private SecretStore secrets;
    private EditText url;
    private EditText code;
    private EditText label;
    private TextView status;
    private CheckBox screenOff;

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        preferences = new AppPreferences(this);
        secrets = new SecretStore(this);
        setContentView(buildContent());
        refreshStatus();
    }

    private ScrollView buildContent() {
        int padding = dp(20);
        LinearLayout column = new LinearLayout(this);
        column.setOrientation(LinearLayout.VERTICAL);
        column.setPadding(padding, padding, padding, padding);

        TextView heading = text("Sol's Peanut Gallery receiver", 26);
        heading.setTypeface(Typeface.DEFAULT_BOLD);
        column.addView(heading);
        column.addView(text("Pair this dedicated display with your self-hosted bridge. The app contains no reaction media or server credential.", 16));

        url = field("Bridge URL", InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_URI);
        url.setText(preferences.bridgeUrl());
        column.addView(url);
        code = field("Six-digit one-time pairing code", InputType.TYPE_CLASS_NUMBER);
        column.addView(code);
        label = field("Device label", InputType.TYPE_CLASS_TEXT);
        label.setText(android.os.Build.MODEL);
        column.addView(label);

        Button pair = button("Pair receiver");
        pair.setOnClickListener(view -> pair());
        column.addView(pair);

        Button enable = button("Enable foreground listener");
        enable.setOnClickListener(view -> enableListener());
        column.addView(enable);
        Button disable = button("Disable listener");
        disable.setOnClickListener(view -> disableListener());
        column.addView(disable);

        screenOff = new CheckBox(this);
        screenOff.setText(R.string.screen_off_option);
        screenOff.setChecked(preferences.screenOffAfterReaction());
        screenOff.setOnCheckedChangeListener((button, checked) -> {
            preferences.setScreenOffAfterReaction(checked);
            if (checked && !devicePolicy().isAdminActive(adminComponent())) requestDeviceAdmin();
        });
        column.addView(screenOff);
        Button admin = button("Review optional screen-off permission");
        admin.setOnClickListener(view -> requestDeviceAdmin());
        column.addView(admin);
        if (Build.VERSION.SDK_INT >= 34) {
            Button fullScreen = button("Review full-screen reaction permission");
            fullScreen.setOnClickListener(view -> {
                Intent intent = new Intent(Settings.ACTION_MANAGE_APP_USE_FULL_SCREEN_INTENT,
                        Uri.parse("package:" + getPackageName()));
                startActivity(intent);
            });
            column.addView(fullScreen);
        }

        status = text("", 16);
        status.setPadding(0, dp(14), 0, dp(14));
        column.addView(status);

        TextView legal = text(
                "Independent community project; not an official OpenAI product. Inspired by rsms/esp32-dot without including its source or assets. " +
                "Created and maintained by Will with disclosed ChatGPT assistance. Licensed GPL-3.0-or-later, with ABSOLUTELY NO WARRANTY. " +
                "See the included source repository and LICENSE for the complete terms.", 13);
        column.addView(legal);

        ScrollView scroll = new ScrollView(this);
        scroll.addView(column);
        return scroll;
    }

    private void pair() {
        String bridge = url.getText().toString().trim();
        String oneTimeCode = code.getText().toString().trim();
        String deviceLabel = label.getText().toString().trim();
        if (!oneTimeCode.matches("[0-9]{6}") || deviceLabel.isEmpty() || deviceLabel.length() > 80) {
            toast("Enter a six-digit code and a device label of at most 80 characters.");
            return;
        }
        status.setText(R.string.status_pairing);
        executor.execute(() -> {
            try {
                String normalized = BridgeClient.normalizeBaseUrl(bridge);
                String token = BridgeClient.pair(normalized, oneTimeCode, deviceLabel);
                secrets.put(token);
                preferences.setBridgeUrl(normalized);
                runOnUiThread(() -> {
                    url.setText(normalized);
                    code.setText("");
                    status.setText(R.string.status_paired);
                });
            } catch (Exception error) {
                runOnUiThread(() -> status.setText(getString(R.string.status_pair_failed, safeMessage(error))));
            }
        });
    }

    private void enableListener() {
        if (Build.VERSION.SDK_INT >= 33
                && checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != android.content.pm.PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS}, 100);
        }
        executor.execute(() -> {
            try {
                if (preferences.bridgeUrl().isEmpty() || secrets.get() == null) throw new IllegalStateException("Pair the receiver first.");
                preferences.setListenerEnabled(true);
                ListenerService.start(this);
                runOnUiThread(this::refreshStatus);
            } catch (Exception error) {
                runOnUiThread(() -> status.setText(getString(R.string.status_enable_failed, safeMessage(error))));
            }
        });
    }

    private void disableListener() {
        preferences.setListenerEnabled(false);
        ListenerService.stop(this);
        refreshStatus();
    }

    private void refreshStatus() {
        if (status != null) status.setText(preferences.listenerEnabled()
                ? R.string.status_enabled : R.string.status_disabled);
    }

    private void requestDeviceAdmin() {
        Intent intent = new Intent(DevicePolicyManager.ACTION_ADD_DEVICE_ADMIN);
        intent.putExtra(DevicePolicyManager.EXTRA_DEVICE_ADMIN, adminComponent());
        intent.putExtra(DevicePolicyManager.EXTRA_ADD_EXPLANATION,
                "Optional: allow this dedicated receiver to turn the display off after a reaction.");
        startActivity(intent);
    }

    private DevicePolicyManager devicePolicy() {
        return (DevicePolicyManager) getSystemService(Context.DEVICE_POLICY_SERVICE);
    }

    private ComponentName adminComponent() {
        return new ComponentName(this, ScreenAdminReceiver.class);
    }

    private EditText field(String hint, int inputType) {
        EditText field = new EditText(this);
        field.setHint(hint);
        field.setInputType(inputType);
        field.setSingleLine(true);
        field.setLayoutParams(matchWrap());
        return field;
    }

    private Button button(String title) {
        Button button = new Button(this);
        button.setText(title);
        button.setLayoutParams(matchWrap());
        return button;
    }

    private TextView text(String value, int size) {
        TextView view = new TextView(this);
        view.setText(value);
        view.setTextSize(size);
        view.setLayoutParams(matchWrap());
        return view;
    }

    private LinearLayout.LayoutParams matchWrap() {
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        params.setMargins(0, dp(6), 0, dp(6));
        return params;
    }

    private int dp(int value) { return Math.round(value * getResources().getDisplayMetrics().density); }
    private void toast(String value) { Toast.makeText(this, value, Toast.LENGTH_LONG).show(); }
    private static String safeMessage(Exception error) {
        String message = error.getMessage();
        return message == null || message.isEmpty() ? error.getClass().getSimpleName() : message;
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        executor.shutdownNow();
    }
}
