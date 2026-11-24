// SPDX-License-Identifier: GPL-3.0-or-later
package org.solpeanutgallery.receiver;

final class BalancedCutoutPadding {
    private BalancedCutoutPadding() {}

    static int maximum(int first, int second) {
        return Math.max(0, Math.max(first, second));
    }
}
