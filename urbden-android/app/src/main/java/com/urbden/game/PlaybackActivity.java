package com.urbden.game;

import android.app.Activity;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.text.SpannableString;
import android.text.Spanned;
import android.text.style.ForegroundColorSpan;
import android.util.TypedValue;
import android.view.Gravity;
import android.view.ViewGroup;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.TextView;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

public class PlaybackActivity extends Activity {
    private final Handler handler = new Handler(Looper.getMainLooper());

    private PlaybackSurfaceView surfaceView;
    private PlaybackRenderer renderer;
    private DirkOddsSimulator simulator;

    private TextView scoreView;
    private TextView promptView;
    private TextView eventView;
    private TextView resultView;
    private TextView badgeView;
    private GridView metricView;
    private Button pulseButton;
    private Button shapeButton;
    private Button reflexButton;
    private boolean lastQteState;

    private final Runnable tickLoop = new Runnable() {
        @Override
        public void run() {
            if (simulator == null) {
                return;
            }
            simulator.tick(0.1f);
            DirkOddsMatchState state = simulator.snapshot();
            updateUi(state);
            if (surfaceView != null) {
                surfaceView.queueEvent(() -> renderer.updateState(state));
            }
            if (!state.finished) {
                handler.postDelayed(this, 100L);
            }
        }
    };

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);

        String scenarioId = getIntent().getStringExtra("scenario_id");
        int predictedOutcome = getIntent().getIntExtra("predicted_outcome", DirkOddsSimulator.OUTCOME_HOME);
        DirkOddsScenario scenario = DirkOddsScenarioRepository.findById(this, scenarioId);
        if (scenario == null) {
            finish();
            return;
        }

        simulator = new DirkOddsSimulator(scenario, predictedOutcome);
        renderer = new PlaybackRenderer(getAssets(), scenario);
        surfaceView = new PlaybackSurfaceView(this, renderer);

        FrameLayout root = new FrameLayout(this);
        root.addView(surfaceView, new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.MATCH_PARENT));

        LinearLayout topOverlay = new LinearLayout(this);
        topOverlay.setOrientation(LinearLayout.VERTICAL);
        topOverlay.setPadding(dp(14), dp(12), dp(14), dp(12));
        topOverlay.setBackground(buildOverlayBackground(168, Color.rgb(8, 12, 28), Color.rgb(12, 21, 42)));

        badgeView = new TextView(this);
        badgeView.setTextColor(Color.rgb(24, 246, 210));
        badgeView.setTypeface(Typeface.create("sans-serif-medium", Typeface.BOLD));
        badgeView.setLetterSpacing(0.12f);
        badgeView.setTextSize(TypedValue.COMPLEX_UNIT_SP, 11);
        badgeView.setPadding(0, 0, 0, dp(6));
        topOverlay.addView(badgeView);

        scoreView = new TextView(this);
        scoreView.setTextColor(Color.rgb(242, 247, 255));
        scoreView.setTypeface(Typeface.create("sans-serif-black", Typeface.BOLD));
        scoreView.setTextSize(TypedValue.COMPLEX_UNIT_SP, 22);
        topOverlay.addView(scoreView);

        eventView = new TextView(this);
        eventView.setTextColor(Color.rgb(121, 232, 245));
        eventView.setTypeface(Typeface.create("monospace", Typeface.BOLD));
        eventView.setTextSize(TypedValue.COMPLEX_UNIT_SP, 13);
        eventView.setPadding(0, dp(2), 0, dp(6));
        topOverlay.addView(eventView);

        promptView = new TextView(this);
        promptView.setTextColor(Color.rgb(255, 198, 86));
        promptView.setTextSize(TypedValue.COMPLEX_UNIT_SP, 13);
        promptView.setPadding(0, 0, 0, dp(10));
        topOverlay.addView(promptView);

        metricView = new GridView(this);
        topOverlay.addView(metricView, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT));

        resultView = new TextView(this);
        resultView.setTextColor(Color.rgb(255, 255, 255));
        resultView.setTypeface(Typeface.create("sans-serif-black", Typeface.BOLD));
        resultView.setTextSize(TypedValue.COMPLEX_UNIT_SP, 15);
        resultView.setPadding(0, dp(8), 0, 0);
        topOverlay.addView(resultView);

        FrameLayout.LayoutParams topParams = new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT,
                Gravity.TOP);
        root.addView(topOverlay, topParams);

        LinearLayout controls = new LinearLayout(this);
        controls.setOrientation(LinearLayout.HORIZONTAL);
        controls.setPadding(dp(12), dp(10), dp(12), dp(10));
        controls.setBackground(buildOverlayBackground(182, Color.rgb(9, 13, 28), Color.rgb(18, 14, 35)));

        pulseButton = new Button(this);
        pulseButton.setText("Pulse Pick");
        styleActionButton(pulseButton, Color.rgb(19, 247, 209), Color.rgb(126, 255, 234), false);
        pulseButton.setOnClickListener(view -> simulator.pulsePrediction());
        controls.addView(pulseButton, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));

        shapeButton = new Button(this);
        shapeButton.setText("Set Shape");
        styleActionButton(shapeButton, Color.rgb(255, 193, 67), Color.rgb(255, 229, 136), false);
        shapeButton.setOnClickListener(view -> simulator.holdShape());
        controls.addView(shapeButton, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));

        reflexButton = new Button(this);
        reflexButton.setText("Reflex Tap");
        styleActionButton(reflexButton, Color.rgb(255, 79, 196), Color.rgb(255, 154, 220), true);
        reflexButton.setOnClickListener(view -> simulator.triggerReflex());
        controls.addView(reflexButton, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));

        Button closeButton = new Button(this);
        closeButton.setText("Exit");
        styleActionButton(closeButton, Color.rgb(108, 130, 158), Color.rgb(174, 188, 205), false);
        closeButton.setOnClickListener(view -> finish());
        controls.addView(closeButton, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 0.9f));

        FrameLayout.LayoutParams bottomParams = new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT,
                Gravity.BOTTOM);
        root.addView(controls, bottomParams);

        setContentView(root);
        updateUi(simulator.snapshot());
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (surfaceView != null) {
            surfaceView.onResume();
        }
        handler.removeCallbacks(tickLoop);
        handler.post(tickLoop);
    }

    @Override
    protected void onPause() {
        handler.removeCallbacks(tickLoop);
        if (surfaceView != null) {
            surfaceView.onPause();
        }
        super.onPause();
    }

    private void updateUi(DirkOddsMatchState state) {
        badgeView.setText(buildBadge(state));
        scoreView.setText(String.format(Locale.US,
                "%s | %s %d - %d %s",
                state.clockLabel,
                state.scenario.homeTeam,
                state.homeScore,
                state.awayScore,
                state.scenario.awayTeam));
        eventView.setText(state.eventLabel + " | " + state.scenario.venue + " | " + titleCase(state.scenario.sport));
        promptView.setText((state.qteActive ? "[LIVE CUE] " : "") + state.prompt);
        promptView.setTextColor(state.qteActive ? Color.rgb(255, 208, 96) : Color.rgb(158, 231, 243));

        List<GridView.GridMetric> metrics = new ArrayList<>();
        metrics.add(new GridView.GridMetric("Prediction Edge", state.predictedLabel, state.predictionEdge, 0xFFE9C46A));
        metrics.add(new GridView.GridMetric("Momentum", state.scenario.homeTeam + " <> " + state.scenario.awayTeam, state.momentum, blend(state.scenario.awayColor, state.scenario.homeColor, state.momentum)));
        metrics.add(new GridView.GridMetric("Control", "coach stability", state.control, 0xFF5DD39E));
        metrics.add(new GridView.GridMetric("Reflex", state.qteActive ? "window open" : "window closed", state.reflex, 0xFF4DA8DA));
        metrics.add(new GridView.GridMetric("Pressure", state.finished ? "final state" : "live stress", state.pressure, 0xFFF25F5C));
        metricView.setMetrics(metrics);

        resultView.setText(state.finished
                ? (state.predictionCorrect ? "Prediction confirmed in live play." : "Prediction missed the final lane.")
                : "Prediction target: " + state.predictedLabel);
        if (state.finished) {
            resultView.setTextColor(state.predictionCorrect ? Color.rgb(42, 246, 186) : Color.rgb(255, 106, 144));
        } else {
            resultView.setTextColor(Color.rgb(255, 255, 255));
        }
        pulseButton.setEnabled(!state.finished);
        shapeButton.setEnabled(!state.finished);
        reflexButton.setEnabled(!state.finished);
        reflexButton.setText(state.qteActive ? "Reflex Tap" : "Hold Reflex");
        styleActionButton(reflexButton, state.qteActive ? Color.rgb(255, 79, 196) : Color.rgb(101, 119, 151), state.qteActive ? Color.rgb(255, 154, 220) : Color.rgb(150, 168, 198), state.qteActive);
        if (state.qteActive != lastQteState) {
            animateCueState(state.qteActive);
            lastQteState = state.qteActive;
        }
    }

    private SpannableString buildBadge(DirkOddsMatchState state) {
        String sport = titleCase(state.scenario.sport).toUpperCase(Locale.US);
        String status = state.finished ? "FINAL" : (state.qteActive ? "QTE OPEN" : "SIM FLOW");
        String text = "LIVE//" + sport + "//" + status;
        SpannableString styled = new SpannableString(text);
        styled.setSpan(new ForegroundColorSpan(Color.rgb(24, 246, 210)), 0, 6, Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);
        int sportStart = 6;
        int sportEnd = sportStart + sport.length();
        styled.setSpan(new ForegroundColorSpan(Color.rgb(246, 248, 255)), sportStart, sportEnd, Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);
        int statusStart = sportEnd + 2;
        styled.setSpan(new ForegroundColorSpan(state.finished
                ? (state.predictionCorrect ? Color.rgb(42, 246, 186) : Color.rgb(255, 106, 144))
                : (state.qteActive ? Color.rgb(255, 208, 96) : Color.rgb(121, 232, 245))), statusStart, text.length(), Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);
        return styled;
    }

    private GradientDrawable buildOverlayBackground(int alpha, int startColor, int endColor) {
        GradientDrawable background = new GradientDrawable(
                GradientDrawable.Orientation.TL_BR,
                new int[] {
                        Color.argb(alpha, Color.red(startColor), Color.green(startColor), Color.blue(startColor)),
                        Color.argb(alpha, Color.red(endColor), Color.green(endColor), Color.blue(endColor))
                });
        background.setCornerRadius(dp(22));
        background.setStroke(dp(1), Color.argb(176, 103, 241, 255));
        return background;
    }

    private void styleActionButton(Button button, int startColor, int endColor, boolean brightText) {
        button.setAllCaps(false);
        button.setTextSize(TypedValue.COMPLEX_UNIT_SP, 13);
        button.setTypeface(Typeface.create("sans-serif-black", Typeface.BOLD));
        button.setTextColor(brightText ? Color.rgb(17, 14, 27) : Color.rgb(13, 18, 28));
        button.setPadding(dp(6), dp(14), dp(6), dp(14));
        GradientDrawable background = new GradientDrawable(
                GradientDrawable.Orientation.LEFT_RIGHT,
                new int[] {startColor, endColor});
        background.setCornerRadius(dp(18));
        background.setStroke(dp(1), Color.argb(188, 255, 255, 255));
        button.setBackground(background);
    }

    private void animateCueState(boolean qteActive) {
        if (qteActive) {
            badgeView.animate().scaleX(1.04f).scaleY(1.04f).setDuration(140).withEndAction(
                    () -> badgeView.animate().scaleX(1f).scaleY(1f).setDuration(180).start()).start();
            promptView.animate().alpha(0.68f).setDuration(0).withEndAction(
                    () -> promptView.animate().alpha(1f).setDuration(220).start()).start();
            reflexButton.animate().scaleX(1.06f).scaleY(1.06f).setDuration(120).withEndAction(
                    () -> reflexButton.animate().scaleX(1f).scaleY(1f).setDuration(180).start()).start();
        } else {
            reflexButton.animate().rotation(0f).setDuration(120).start();
            promptView.animate().alpha(0.9f).setDuration(120).start();
        }
    }

    private int blend(int awayColor, int homeColor, float t) {
        float clamped = Math.max(0f, Math.min(1f, t));
        int r = (int) (Color.red(awayColor) + (Color.red(homeColor) - Color.red(awayColor)) * clamped);
        int g = (int) (Color.green(awayColor) + (Color.green(homeColor) - Color.green(awayColor)) * clamped);
        int b = (int) (Color.blue(awayColor) + (Color.blue(homeColor) - Color.blue(awayColor)) * clamped);
        return Color.rgb(r, g, b);
    }

    private String titleCase(String value) {
        if (value == null || value.isEmpty()) {
            return "Sport";
        }
        return Character.toUpperCase(value.charAt(0)) + value.substring(1);
    }

    private int dp(int value) {
        return Math.round(TypedValue.applyDimension(
                TypedValue.COMPLEX_UNIT_DIP,
                value,
                getResources().getDisplayMetrics()));
    }
}