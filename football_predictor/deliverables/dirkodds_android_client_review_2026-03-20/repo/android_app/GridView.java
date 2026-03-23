package com.urbden.game;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.RectF;
import android.util.TypedValue;
import android.view.View;

import java.util.ArrayList;
import java.util.List;

public class GridView extends View {
    public static class GridMetric {
        public final String label;
        public final String detail;
        public final float value;
        public final int color;

        public GridMetric(String label, String detail, float value, int color) {
            this.label = label;
            this.detail = detail;
            this.value = Math.max(0f, Math.min(1f, value));
            this.color = color;
        }
    }

    private final List<GridMetric> metrics = new ArrayList<>();
    private final Paint framePaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint trackPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint glowPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint fillPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint labelPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint detailPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint rowPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final RectF rect = new RectF();

    public GridView(Context context) {
        super(context);
        framePaint.setStyle(Paint.Style.STROKE);
        framePaint.setStrokeWidth(dp(1f));
        framePaint.setColor(Color.argb(120, 148, 168, 176));

        trackPaint.setStyle(Paint.Style.FILL);
        trackPaint.setColor(Color.argb(120, 17, 35, 44));

        glowPaint.setStyle(Paint.Style.FILL);
        glowPaint.setAlpha(56);

        fillPaint.setStyle(Paint.Style.FILL);

        rowPaint.setStyle(Paint.Style.FILL);
        rowPaint.setColor(Color.argb(28, 255, 255, 255));

        labelPaint.setColor(Color.rgb(236, 238, 242));
        labelPaint.setTextSize(sp(13));
        labelPaint.setFakeBoldText(true);

        detailPaint.setColor(Color.rgb(154, 170, 181));
        detailPaint.setTextSize(sp(11));
    }

    public void setMetrics(List<GridMetric> nextMetrics) {
        metrics.clear();
        if (nextMetrics != null) {
            metrics.addAll(nextMetrics);
        }
        invalidate();
    }

    @Override
    protected void onMeasure(int widthMeasureSpec, int heightMeasureSpec) {
        int minHeight = dp(220);
        int desiredHeight = dp(28) + metrics.size() * dp(42);
        int resolvedHeight = resolveSize(Math.max(minHeight, desiredHeight), heightMeasureSpec);
        int resolvedWidth = resolveSize(dp(320), widthMeasureSpec);
        setMeasuredDimension(resolvedWidth, resolvedHeight);
    }

    @Override
    protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);

        float width = getWidth();
        float height = getHeight();
        float outer = dp(16);
        float corner = dp(18);
        rect.set(outer, outer, width - outer, height - outer);
        canvas.drawRoundRect(rect, corner, corner, trackPaint);
        canvas.drawRoundRect(rect, corner, corner, framePaint);

        if (metrics.isEmpty()) {
            detailPaint.setTextAlign(Paint.Align.CENTER);
            canvas.drawText("No metrics loaded", width / 2f, height / 2f, detailPaint);
            detailPaint.setTextAlign(Paint.Align.LEFT);
            return;
        }

        float labelWidth = dp(110);
        float left = outer + dp(12);
        float top = outer + dp(16);
        float trackLeft = left + labelWidth;
        float trackRight = width - outer - dp(16);
        float rowHeight = dp(34);
        float rowGap = dp(8);
        float trackCorner = dp(9);

        for (int index = 0; index < metrics.size(); index++) {
            GridMetric metric = metrics.get(index);
            float rowTop = top + index * (rowHeight + rowGap);
            float rowBottom = rowTop + rowHeight;

            rect.set(left - dp(4), rowTop - dp(2), trackRight, rowBottom + dp(2));
            canvas.drawRoundRect(rect, dp(12), dp(12), rowPaint);

            float labelBaseline = rowTop + dp(12);
            float detailBaseline = rowTop + dp(25);
            canvas.drawText(metric.label, left, labelBaseline, labelPaint);
            canvas.drawText(metric.detail, left, detailBaseline, detailPaint);

            rect.set(trackLeft, rowTop + dp(6), trackRight, rowBottom - dp(6));
            canvas.drawRoundRect(rect, trackCorner, trackCorner, framePaint);
            canvas.drawRoundRect(rect, trackCorner, trackCorner, trackPaint);

            float fillRight = trackLeft + (trackRight - trackLeft) * metric.value;
            if (fillRight > trackLeft) {
                glowPaint.setColor(metric.color);
                rect.set(trackLeft, rowTop + dp(4), fillRight, rowBottom - dp(4));
                canvas.drawRoundRect(rect, trackCorner, trackCorner, glowPaint);

                fillPaint.setColor(metric.color);
                rect.set(trackLeft, rowTop + dp(8), fillRight, rowBottom - dp(8));
                canvas.drawRoundRect(rect, trackCorner, trackCorner, fillPaint);

                canvas.drawCircle(fillRight, rowTop + rowHeight / 2f, dp(5), fillPaint);
            }
        }
    }

    private int dp(int value) {
        return Math.round(dp((float) value));
    }

    private float dp(float value) {
        return TypedValue.applyDimension(
                TypedValue.COMPLEX_UNIT_DIP,
                value,
                getResources().getDisplayMetrics());
    }

    private float sp(int value) {
        return TypedValue.applyDimension(
                TypedValue.COMPLEX_UNIT_SP,
                value,
                getResources().getDisplayMetrics());
    }
}
