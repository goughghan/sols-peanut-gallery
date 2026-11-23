# SPDX-License-Identifier: GPL-3.0-or-later

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
ANDROID = ROOT / "android" / "app" / "src" / "main"


class AndroidSourceTests(unittest.TestCase):
    def test_android_8_target_and_recovery_components_are_declared(self):
        build = (ROOT / "android" / "app" / "build.gradle").read_text(encoding="utf-8")
        manifest = (ANDROID / "AndroidManifest.xml").read_text(encoding="utf-8")
        self.assertIn("minSdk 26", build)
        self.assertIn("targetSdk 35", build)
        self.assertIn('applicationIdSuffix ".test"', build)
        self.assertIn("android.intent.action.BOOT_COMPLETED", manifest)
        self.assertIn("android.intent.action.MY_PACKAGE_REPLACED", manifest)
        self.assertIn('android:foregroundServiceType="remoteMessaging"', manifest)

    def test_debug_receiver_has_distinct_test_identity(self):
        build = (ROOT / "android" / "app" / "build.gradle").read_text(encoding="utf-8")
        label = (ROOT / "android" / "app" / "src" / "debug" / "res" / "values" / "strings.xml").read_text(
            encoding="utf-8")
        self.assertIn("versionCode 6", build)
        self.assertIn('versionNameSuffix "-test7"', build)
        self.assertIn("signingConfig null", build)
        self.assertIn("Peanut Gallery Test 7", label)

    def test_completion_is_identity_guarded_and_notification_is_per_delivery(self):
        service = (ANDROID / "java" / "org" / "solpeanutgallery" / "receiver" / "ListenerService.java").read_text(
            encoding="utf-8")
        activity = (ANDROID / "java" / "org" / "solpeanutgallery" / "receiver" / "ReactionActivity.java").read_text(
            encoding="utf-8")
        claim = "preferences.claimCompletion(delivery, now, now + 60_000L)"
        acknowledge = "client.acknowledge(delivery, outcome"
        clear = "preferences.clearActiveDelivery(delivery)"
        self.assertIn(claim, service)
        self.assertLess(service.index(claim), service.index(acknowledge))
        self.assertLess(service.index(acknowledge), service.index(clear))
        self.assertIn("reactionNotificationId(delivery.deliveryId)", service)
        self.assertIn('REACTION_CHANNEL = "reactions-quiet-v2"', service)
        self.assertIn("reactions.setSound(null, null)", service)
        self.assertIn("reactions.enableVibration(false)", service)
        self.assertIn("ListenerService.opened(this, opened);", activity)
        self.assertIn("delivery.sameIdentity(incoming)", activity)
        self.assertNotIn("startActivity(activity);", service)

    def test_gif_renderer_replaces_canvas_before_drawing_each_frame(self):
        renderer = (ANDROID / "java" / "org" / "solpeanutgallery" / "receiver" / "GifView.java").read_text(
            encoding="utf-8")
        clear = "canvas.drawColor(Color.BLACK, PorterDuff.Mode.SRC);"
        draw = "movie.draw(canvas, 0, 0);"
        self.assertEqual(1, renderer.count(clear))
        self.assertEqual(1, renderer.count(draw))
        self.assertLess(renderer.index(clear), renderer.index(draw))

    def test_reaction_caption_autosizes_inside_reserved_space(self):
        activity = (ANDROID / "java" / "org" / "solpeanutgallery" / "receiver" / "ReactionActivity.java").read_text(
            encoding="utf-8")
        self.assertIn("setAutoSizeTextTypeUniformWithConfiguration", activity)
        self.assertIn("14, 34, 1, TypedValue.COMPLEX_UNIT_SP", activity)
        self.assertIn("caption.setMaxLines(4)", activity)
        self.assertIn('delivery.emoji.isEmpty() ? 1f : 0.35f', activity)
        self.assertIn(': 0.30f;', activity)

    def test_reaction_window_hides_system_bars_before_and_after_wake(self):
        manifest = (ANDROID / "AndroidManifest.xml").read_text(encoding="utf-8")
        styles = (ANDROID / "res" / "values" / "styles.xml").read_text(encoding="utf-8")
        activity = (ANDROID / "java" / "org" / "solpeanutgallery" / "receiver" / "ReactionActivity.java").read_text(
            encoding="utf-8")
        self.assertIn('android:theme="@style/ReactionTheme"', manifest)
        self.assertIn('name="android:windowDisablePreview">true', styles)
        self.assertIn('name="android:windowFullscreen">true', styles)
        self.assertIn("FLAG_FULLSCREEN", activity)
        self.assertIn("SYSTEM_UI_FLAG_LOW_PROFILE", activity)
        self.assertIn("protected void onPostResume()", activity)
        self.assertIn("post(this::immersive)", activity)

    def test_receiver_rejects_redirects_and_verifies_download(self):
        client = (ANDROID / "java" / "org" / "solpeanutgallery" / "receiver" / "BridgeClient.java").read_text(
            encoding="utf-8")
        self.assertIn("setInstanceFollowRedirects(false)", client)
        self.assertIn('MessageDigest.getInstance("SHA-256")', client)
        self.assertIn("verifyDecodedMedia(data, delivery)", client)
        self.assertNotIn("setInstanceFollowRedirects(true)", client)

    def test_receiver_reports_battery_without_changing_delivery_polling(self):
        client = (ANDROID / "java" / "org" / "solpeanutgallery" / "receiver" / "BridgeClient.java").read_text(
            encoding="utf-8")
        service = (ANDROID / "java" / "org" / "solpeanutgallery" / "receiver" / "ListenerService.java").read_text(
            encoding="utf-8")
        self.assertIn('"/v1/receiver/status"', client)
        self.assertIn('put("battery_percent", batteryPercent)', client)
        self.assertIn("STATUS_INTERVAL_MILLIS = 5L * 60L * 1_000L", service)
        self.assertIn("battery.isCharging()", service)
        self.assertIn("maybeReportStatus();", service)

    def test_base_application_has_no_media_asset_directory(self):
        for directory in (ANDROID / "assets", ANDROID / "res" / "raw"):
            self.assertFalse(directory.exists())


if __name__ == "__main__":
    unittest.main()
