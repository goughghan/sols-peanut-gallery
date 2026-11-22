// SPDX-License-Identifier: GPL-3.0-or-later
package org.solpeanutgallery.receiver;

import android.annotation.SuppressLint;
import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Movie;
import android.graphics.PorterDuff;
import android.os.SystemClock;
import android.view.View;

@SuppressLint("ViewConstructor") // This view is created only with its already-decoded Movie.
final class GifView extends View {
    private final Movie movie;
    private final long started = SystemClock.uptimeMillis();

    GifView(Context context, Movie movie) {
        super(context);
        this.movie = movie;
        setLayerType(View.LAYER_TYPE_SOFTWARE, null);
    }

    @Override
    protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);
        canvas.drawColor(Color.BLACK, PorterDuff.Mode.SRC);
        int duration = movie.duration() > 0 ? movie.duration() : 1_000;
        movie.setTime((int) ((SystemClock.uptimeMillis() - started) % duration));
        float scale = Math.min(getWidth() / (float) movie.width(), getHeight() / (float) movie.height());
        float left = (getWidth() - movie.width() * scale) / 2f;
        float top = (getHeight() - movie.height() * scale) / 2f;
        canvas.save();
        canvas.translate(left, top);
        canvas.scale(scale, scale);
        movie.draw(canvas, 0, 0);
        canvas.restore();
        postInvalidateOnAnimation();
    }
}
