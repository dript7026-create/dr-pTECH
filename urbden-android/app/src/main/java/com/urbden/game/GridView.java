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
import java.util.Locale;

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
    private final Paint accentPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint valuePaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint rowPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final RectF rect = new RectF();

    public GridView(Context context) {
        super(context);
        framePaint.setStyle(Paint.Style.STROKE);
        framePaint.setStrokeWidth(dp(1f));
        framePaint.setColor(Color.argb(172, 109, 244, 255));

        trackPaint.setStyle(Paint.Style.FILL);
        trackPaint.setColor(Color.argb(212, 7, 18, 29));

        glowPaint.setStyle(Paint.Style.FILL);
        glowPaint.setAlpha(86);

        fillPaint.setStyle(Paint.Style.FILL);

        accentPaint.setStyle(Paint.Style.FILL);
        accentPaint.setColor(Color.argb(210, 22, 248, 208));

        rowPaint.setStyle(Paint.Style.FILL);
        rowPaint.setColor(Color.argb(48, 255, 255, 255));

        labelPaint.setColor(Color.rgb(241, 246, 255));
        labelPaint.setTextSize(sp(12));
        labelPaint.setFakeBoldText(true);

        detailPaint.setColor(Color.rgb(110, 235, 247));
        detailPaint.setTextSize(sp(10));

        valuePaint.setColor(Color.rgb(255, 255, 255));
        valuePaint.setTextSize(sp(11));
        valuePaint.setFakeBoldText(true);
        valuePaint.setTextAlign(Paint.Align.RIGHT);
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
        int columnCount = columnCountForWidth(MeasureSpec.getSize(widthMeasureSpec));
        int rowCount = Math.max(1, (int) Math.ceil(metrics.size() / (float) columnCount));
        int minHeight = dp(104);
        int desiredHeight = dp(24) + rowCount * dp(62) + Math.max(0, rowCount - 1) * dp(8);
        int resolvedHeight = resolveSize(Math.max(minHeight, desiredHeight), heightMeasureSpec);
        int resolvedWidth = resolveSize(dp(320), widthMeasureSpec);
        setMeasuredDimension(resolvedWidth, resolvedHeight);
    }

    @Override
    protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);

        float width = getWidth();
        float height = getHeight();
        float outer = dp(6);
        float corner = dp(18);
        rect.set(outer, outer, width - outer, height - outer);
        canvas.drawRoundRect(rect, corner, corner, trackPaint);
        canvas.drawRoundRect(rect, corner, corner, framePaint);

        rect.set(outer + dp(8), outer + dp(8), width - outer - dp(8), outer + dp(12));
        canvas.drawRoundRect(rect, dp(8), dp(8), accentPaint);

        if (metrics.isEmpty()) {
            detailPaint.setTextAlign(Paint.Align.CENTER);
            canvas.drawText("No metrics loaded", width / 2f, height / 2f, detailPaint);
            detailPaint.setTextAlign(Paint.Align.LEFT);
            return;
        }

        int columnCount = columnCountForWidth((int) width);
        int rowCount = Math.max(1, (int) Math.ceil(metrics.size() / (float) columnCount));
        float left = outer + dp(8);
        float top = outer + dp(18);
        float right = width - outer - dp(8);
        float bottom = height - outer - dp(8);
        float columnGap = dp(8);
        float rowGap = dp(8);
        float cellWidth = (right - left - (columnCount - 1) * columnGap) / columnCount;
        float cellHeight = rowCount > 0
                ? Math.max(dp(52), (bottom - top - (rowCount - 1) * rowGap) / rowCount)
                : dp(52);
        float trackCorner = dp(8);

        for (int index = 0; index < metrics.size(); index++) {
            GridMetric metric = metrics.get(index);
            int column = index % columnCount;
            int row = index / columnCount;
            float cellLeft = left + column * (cellWidth + columnGap);
            float cellTop = top + row * (cellHeight + rowGap);
            float cellRight = cellLeft + cellWidth;
            float cellBottom = cellTop + cellHeight;

            rect.set(cellLeft, cellTop, cellRight, cellBottom);
            canvas.drawRoundRect(rect, dp(12), dp(12), rowPaint);

            accentPaint.setColor(metric.color);
            rect.set(cellLeft + dp(8), cellTop + dp(8), cellLeft + dp(12), cellTop + dp(24));
            canvas.drawRoundRect(rect, dp(4), dp(4), accentPaint);

            float labelLeft = cellLeft + dp(18);
            float labelBaseline = cellTop + dp(18);
            float detailBaseline = cellTop + dp(31);
            float valueRight = cellRight - dp(8);
            canvas.drawText(metric.label, labelLeft, labelBaseline, labelPaint);
            canvas.drawText(metric.detail, labelLeft, detailBaseline, detailPaint);
            canvas.drawText(String.format(Locale.US, "%02d", Math.round(metric.value * 100f)), valueRight, labelBaseline, valuePaint);

            float trackLeft = cellLeft + dp(8);
            float trackRight = cellRight - dp(8);
            float trackTop = cellBottom - dp(16);
            float trackBottom = cellBottom - dp(8);
            rect.set(trackLeft, trackTop, trackRight, trackBottom);
            canvas.drawRoundRect(rect, trackCorner, trackCorner, framePaint);
            canvas.drawRoundRect(rect, trackCorner, trackCorner, trackPaint);

            float fillRight = trackLeft + (trackRight - trackLeft) * metric.value;
            if (fillRight > trackLeft) {
                glowPaint.setColor(metric.color);
                rect.set(trackLeft, trackTop - dp(1), fillRight, trackBottom + dp(1));
                canvas.drawRoundRect(rect, trackCorner, trackCorner, glowPaint);

                fillPaint.setColor(metric.color);
                rect.set(trackLeft, trackTop, fillRight, trackBottom);
                canvas.drawRoundRect(rect, trackCorner, trackCorner, fillPaint);

                canvas.drawCircle(fillRight, (trackTop + trackBottom) / 2f, dp(3), fillPaint);
            }
        }
    }

    private int columnCountForWidth(int width) {
        return width < dp(300) ? 1 : 2;
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
