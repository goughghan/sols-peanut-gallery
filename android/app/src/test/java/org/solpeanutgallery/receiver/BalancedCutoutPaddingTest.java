// SPDX-License-Identifier: GPL-3.0-or-later
package org.solpeanutgallery.receiver;

import org.junit.Test;

import static org.junit.Assert.assertEquals;

public final class BalancedCutoutPaddingTest {
    @Test
    public void leftCutoutIsMirroredToBothSides() {
        assertEquals(42, BalancedCutoutPadding.maximum(42, 0));
    }

    @Test
    public void rightCutoutIsMirroredToBothSides() {
        assertEquals(36, BalancedCutoutPadding.maximum(0, 36));
    }

    @Test
    public void malformedNegativeInsetsCannotReducePadding() {
        assertEquals(0, BalancedCutoutPadding.maximum(-1, -2));
    }
}
