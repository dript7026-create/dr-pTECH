package com.urbden.game;

import android.app.Activity;
import android.graphics.Color;
import android.graphics.Typeface;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
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
    private GridView metricView;
    private Button pulseButton;
    private Button shapeButton;
    private Button reflexButton;

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
        topOverlay.setBackgroundColor(Color.argb(150, 8, 12, 18));

        scoreView = new TextView(this);
        scoreView.setTextColor(Color.rgb(238, 242, 246));
        scoreView.setTypeface(Typeface.DEFAULT_BOLD);
        scoreView.setTextSize(TypedValue.COMPLEX_UNIT_SP, 18);
        topOverlay.addView(scoreView);

        eventView = new TextView(this);
        eventView.setTextColor(Color.rgb(206, 216, 224));
        eventView.setTextSize(TypedValue.COMPLEX_UNIT_SP, 13);
        eventView.setPadding(0, dp(2), 0, dp(6));
        topOverlay.addView(eventView);

        promptView = new TextView(this);
        promptView.setTextColor(Color.rgb(244, 227, 176));
        promptView.setTextSize(TypedValue.COMPLEX_UNIT_SP, 13);
        promptView.setPadding(0, 0, 0, dp(10));
        topOverlay.addView(promptView);

        metricView = new GridView(this);
        topOverlay.addView(metricView, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT));

        resultView = new TextView(this);
        resultView.setTextColor(Color.rgb(239, 244, 248));
        resultView.setTypeface(Typeface.DEFAULT_BOLD);
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
        controls.setBackgroundColor(Color.argb(164, 8, 12, 18));

        pulseButton = new Button(this);
        pulseButton.setAllCaps(false);
        pulseButton.setText("Pulse Pick");
        pulseButton.setOnClickListener(view -> simulator.pulsePrediction());
        controls.addView(pulseButton, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));

        shapeButton = new Button(this);
        shapeButton.setAllCaps(false);
        shapeButton.setText("Set Shape");
        shapeButton.setOnClickListener(view -> simulator.holdShape());
        controls.addView(shapeButton, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));

        reflexButton = new Button(this);
        reflexButton.setAllCaps(false);
        reflexButton.setText("Reflex Tap");
        reflexButton.setOnClickListener(view -> simulator.triggerReflex());
        controls.addView(reflexButton, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));

        Button closeButton = new Button(this);
        closeButton.setAllCaps(false);
        closeButton.setText("Exit");
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
        scoreView.setText(String.format(Locale.US,
                "%s | %s %d - %d %s",
                state.clockLabel,
                state.scenario.homeTeam,
                state.homeScore,
                state.awayScore,
                state.scenario.awayTeam));
        eventView.setText(state.eventLabel + " | " + state.scenario.venue + " | " + titleCase(state.scenario.sport));
        promptView.setText((state.qteActive ? "[LIVE CUE] " : "") + state.prompt);

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
        pulseButton.setEnabled(!state.finished);
        shapeButton.setEnabled(!state.finished);
        reflexButton.setEnabled(!state.finished);
        reflexButton.setText(state.qteActive ? "Reflex Tap" : "Hold Reflex");
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