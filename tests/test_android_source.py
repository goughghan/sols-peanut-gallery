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
        self.assertIn("versionCode 2", build)
        self.assertIn('versionNameSuffix "-test3"', build)
        self.assertIn("signingConfig null", build)
        self.assertIn("Peanut Gallery Test 3", label)

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

    def test_receiver_rejects_redirects_and_verifies_download(self):
        client = (ANDROID / "java" / "org" / "solpeanutgallery" / "receiver" / "BridgeClient.java").read_text(
            encoding="utf-8")
        self.assertIn("setInstanceFollowRedirects(false)", client)
        self.assertIn('MessageDigest.getInstance("SHA-256")', client)
        self.assertIn("verifyDecodedMedia(data, delivery)", client)
        self.assertNotIn("setInstanceFollowRedirects(true)", client)

    def test_base_application_has_no_media_asset_directory(self):
        for directory in (ANDROID / "assets", ANDROID / "res" / "raw"):
            self.assertFalse(directory.exists())


if __name__ == "__main__":
    unittest.main()
