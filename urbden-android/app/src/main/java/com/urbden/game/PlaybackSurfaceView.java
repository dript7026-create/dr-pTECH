package com.urbden.game;

import android.content.Context;
import android.opengl.GLSurfaceView;
import android.view.MotionEvent;

public class PlaybackSurfaceView extends GLSurfaceView {
    private final PlaybackRenderer renderer;
    private float previousX;
    private float previousY;
    private float previousSpan;

    public PlaybackSurfaceView(Context context, PlaybackRenderer renderer) {
        super(context);
        this.renderer = renderer;
        setEGLContextClientVersion(2);
        setRenderer(renderer);
        setRenderMode(GLSurfaceView.RENDERMODE_CONTINUOUSLY);
    }

    @Override
    public boolean onTouchEvent(MotionEvent event) {
        int action = event.getActionMasked();
        if (event.getPointerCount() >= 2) {
            float span = spacing(event);
            if (action == MotionEvent.ACTION_POINTER_DOWN) {
                previousSpan = span;
            } else if (action == MotionEvent.ACTION_MOVE && previousSpan > 0f) {
                final float zoomDelta = (previousSpan - span) * 0.01f;
                queueEvent(() -> renderer.adjustZoom(zoomDelta));
                previousSpan = span;
            }
            return true;
        }

        float x = event.getX();
        float y = event.getY();
        switch (action) {
            case MotionEvent.ACTION_DOWN:
                previousX = x;
                previousY = y;
                return true;
            case MotionEvent.ACTION_MOVE:
                final float dx = x - previousX;
                final float dy = y - previousY;
                queueEvent(() -> renderer.adjustOrbit(dx * 0.35f, dy * 0.35f));
                previousX = x;
                previousY = y;
                return true;
            default:
                return super.onTouchEvent(event);
        }
    }

    private float spacing(MotionEvent event) {
        if (event.getPointerCount() < 2) {
            return 0f;
        }
        float dx = event.getX(0) - event.getX(1);
        float dy = event.getY(0) - event.getY(1);
        return (float) Math.sqrt(dx * dx + dy * dy);
    }
}