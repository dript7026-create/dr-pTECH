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
import android.view.HapticFeedbackConstants;
import android.view.View;
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
    private static final String GLYPH_PULSE = "◎";
    private static final String GLYPH_SHAPE = "◇";
    private static final String GLYPH_REFLEX = "✦";
    private static final String GLYPH_MENU = "≡";
    private static final String GLYPH_CLOSE = "×";
    private static final long CONTROL_OVERLAY_FADE_DELAY_MS = 1800L;

    private final Handler handler = new Handler(Looper.getMainLooper());

    private PlaybackSurfaceView surfaceView;
    private PlaybackRenderer renderer;
    private DirkOddsSimulator simulator;
    private QuickthingsAudioEngine quickthingsAudioEngine;
    private SportsCrowdAudioEngine sportsCrowdAudioEngine;
    private QuickthingsHaptics quickthingsHaptics;

    private TextView scoreView;
    private TextView promptView;
    private TextView eventView;
    private TextView identityView;
    private TextView resultView;
    private TextView badgeView;
    private LinearLayout controlOverlayStrip;
    private LinearLayout glyphLegendPanel;
    private TextView pulseGlyphView;
    private TextView shapeGlyphView;
    private TextView reflexGlyphView;
    private GridView metricView;
    private Button pulseButton;
    private Button shapeButton;
    private Button reflexButton;
    private Button glyphMenuButton;
    private boolean lastQteState;
    private boolean glyphLegendOpen;

    private final Runnable fadeControlsRunnable = () -> {
        if (controlOverlayStrip != null && !glyphLegendOpen) {
            controlOverlayStrip.animate().alpha(0.26f).setDuration(320L).start();
        }
    };

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
            if (quickthingsAudioEngine != null) {
                quickthingsAudioEngine.updateState(state);
            }
            if (sportsCrowdAudioEngine != null) {
                sportsCrowdAudioEngine.updateState(state);
            }
            if (quickthingsHaptics != null) {
                quickthingsHaptics.updateState(state);
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
        if (scenario.isQuickthings()) {
            quickthingsAudioEngine = new QuickthingsAudioEngine();
            quickthingsHaptics = new QuickthingsHaptics(this);
        } else {
            sportsCrowdAudioEngine = new SportsCrowdAudioEngine();
        }

        FrameLayout root = new FrameLayout(this);
        root.addView(surfaceView, new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.MATCH_PARENT));

        LinearLayout topOverlay = new LinearLayout(this);
        topOverlay.setOrientation(LinearLayout.VERTICAL);
        topOverlay.setPadding(dp(12), dp(10), dp(12), dp(10));
        topOverlay.setBackground(buildOverlayBackground(156, Color.rgb(8, 12, 28), Color.rgb(12, 21, 42)));

        badgeView = new TextView(this);
        badgeView.setTextColor(Color.rgb(24, 246, 210));
        badgeView.setTypeface(Typeface.create("sans-serif-medium", Typeface.BOLD));
        badgeView.setLetterSpacing(0.12f);
        badgeView.setTextSize(TypedValue.COMPLEX_UNIT_SP, 10);
        badgeView.setPadding(0, 0, 0, dp(4));
        topOverlay.addView(badgeView);

        scoreView = new TextView(this);
        scoreView.setTextColor(Color.rgb(242, 247, 255));
        scoreView.setTypeface(Typeface.create("sans-serif-black", Typeface.BOLD));
        scoreView.setTextSize(TypedValue.COMPLEX_UNIT_SP, 19);
        topOverlay.addView(scoreView);

        eventView = new TextView(this);
        eventView.setTextColor(Color.rgb(121, 232, 245));
        eventView.setTypeface(Typeface.create("monospace", Typeface.BOLD));
        eventView.setTextSize(TypedValue.COMPLEX_UNIT_SP, 11);
        eventView.setPadding(0, dp(2), 0, dp(4));
        topOverlay.addView(eventView);

        promptView = new TextView(this);
        promptView.setTextColor(Color.rgb(255, 198, 86));
        promptView.setTextSize(TypedValue.COMPLEX_UNIT_SP, 12);
        promptView.setPadding(0, 0, 0, dp(8));
        topOverlay.addView(promptView);

        identityView = new TextView(this);
        identityView.setTextColor(Color.rgb(197, 211, 233));
        identityView.setTextSize(TypedValue.COMPLEX_UNIT_SP, 11);
        identityView.setPadding(0, 0, 0, dp(8));
        topOverlay.addView(identityView);

        metricView = new GridView(this);
        topOverlay.addView(metricView, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT));

        resultView = new TextView(this);
        resultView.setTextColor(Color.rgb(255, 255, 255));
        resultView.setTypeface(Typeface.create("sans-serif-black", Typeface.BOLD));
        resultView.setTextSize(TypedValue.COMPLEX_UNIT_SP, 13);
        resultView.setPadding(0, dp(6), 0, 0);
        topOverlay.addView(resultView);

        FrameLayout.LayoutParams topParams = new FrameLayout.LayoutParams(
            compactOverlayWidth(),
                ViewGroup.LayoutParams.WRAP_CONTENT,
            Gravity.TOP | Gravity.START);
        topParams.leftMargin = dp(10);
        topParams.topMargin = dp(10);
        root.addView(topOverlay, topParams);

        FrameLayout controlHudLayer = new FrameLayout(this);
        controlHudLayer.setPadding(dp(12), dp(8), dp(12), dp(8));

        glyphLegendPanel = buildGlyphLegendPanel(scenario.isQuickthings());
        glyphLegendPanel.setVisibility(View.GONE);
        glyphLegendPanel.setAlpha(0f);
        FrameLayout.LayoutParams legendParams = new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT,
                Gravity.TOP | Gravity.CENTER_HORIZONTAL);
        controlHudLayer.addView(glyphLegendPanel, legendParams);

        controlOverlayStrip = new LinearLayout(this);
        controlOverlayStrip.setOrientation(LinearLayout.HORIZONTAL);
        controlOverlayStrip.setGravity(Gravity.CENTER);
        controlOverlayStrip.setPadding(dp(10), dp(8), dp(10), dp(8));
        controlOverlayStrip.setBackground(buildOverlayBackground(152, Color.rgb(8, 12, 24), Color.rgb(20, 18, 38)));
        controlOverlayStrip.setAlpha(0.84f);

        pulseGlyphView = createGlyphPad(GLYPH_PULSE, scenario.isQuickthings() ? "RIFT" : "PULSE", Color.rgb(19, 247, 209));
        controlOverlayStrip.addView(pulseGlyphView, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));

        shapeGlyphView = createGlyphPad(GLYPH_SHAPE, scenario.isQuickthings() ? "SYNC" : "SHAPE", Color.rgb(255, 193, 67));
        LinearLayout.LayoutParams centerGlyphParams = new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f);
        centerGlyphParams.setMargins(dp(8), 0, dp(8), 0);
        controlOverlayStrip.addView(shapeGlyphView, centerGlyphParams);

        reflexGlyphView = createGlyphPad(GLYPH_REFLEX, scenario.isQuickthings() ? "STRIKE" : "REFLEX", Color.rgb(255, 79, 196));
        controlOverlayStrip.addView(reflexGlyphView, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));

        glyphMenuButton = new Button(this);
        glyphMenuButton.setText(GLYPH_MENU + " Glyphs");
        styleActionButton(glyphMenuButton, Color.rgb(88, 108, 156), Color.rgb(154, 173, 220), false);
        glyphMenuButton.setTextSize(TypedValue.COMPLEX_UNIT_SP, 12);
        glyphMenuButton.setOnClickListener(view -> toggleGlyphLegend());
        LinearLayout.LayoutParams glyphMenuParams = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        glyphMenuParams.setMargins(dp(8), 0, 0, 0);
        controlOverlayStrip.addView(glyphMenuButton, glyphMenuParams);

        FrameLayout.LayoutParams stripParams = new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT,
                Gravity.BOTTOM | Gravity.CENTER_HORIZONTAL);
        controlHudLayer.addView(controlOverlayStrip, stripParams);

        FrameLayout.LayoutParams hudParams = new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT,
                Gravity.BOTTOM);
        hudParams.bottomMargin = dp(86);
        root.addView(controlHudLayer, hudParams);

        LinearLayout controls = new LinearLayout(this);
        controls.setOrientation(LinearLayout.HORIZONTAL);
        controls.setPadding(dp(12), dp(10), dp(12), dp(10));
        controls.setBackground(buildOverlayBackground(182, Color.rgb(9, 13, 28), Color.rgb(18, 14, 35)));

        pulseButton = new Button(this);
        pulseButton.setText(controlButtonText(GLYPH_PULSE, scenario.isQuickthings() ? "Rift" : "Pulse"));
        styleActionButton(pulseButton, Color.rgb(19, 247, 209), Color.rgb(126, 255, 234), false);
        pulseButton.setOnClickListener(view -> {
            performActionHaptics(view, false);
            pulseControlDisplay(pulseGlyphView);
            simulator.pulsePrediction();
        });
        controls.addView(pulseButton, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));

        shapeButton = new Button(this);
        shapeButton.setText(controlButtonText(GLYPH_SHAPE, scenario.isQuickthings() ? "Sync" : "Shape"));
        styleActionButton(shapeButton, Color.rgb(255, 193, 67), Color.rgb(255, 229, 136), false);
        shapeButton.setOnClickListener(view -> {
            performActionHaptics(view, false);
            pulseControlDisplay(shapeGlyphView);
            simulator.holdShape();
        });
        controls.addView(shapeButton, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));

        reflexButton = new Button(this);
        reflexButton.setText(controlButtonText(GLYPH_REFLEX, scenario.isQuickthings() ? "Strike" : "Reflex"));
        styleActionButton(reflexButton, Color.rgb(255, 79, 196), Color.rgb(255, 154, 220), true);
        reflexButton.setOnClickListener(view -> {
            performActionHaptics(view, true);
            pulseControlDisplay(reflexGlyphView);
            simulator.triggerReflex();
        });
        controls.addView(reflexButton, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));

        Button closeButton = new Button(this);
        closeButton.setText("Leave");
        styleActionButton(closeButton, Color.rgb(108, 130, 158), Color.rgb(174, 188, 205), false);
        closeButton.setOnClickListener(view -> finish());
        controls.addView(closeButton, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 0.9f));

        FrameLayout.LayoutParams bottomParams = new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT,
                Gravity.BOTTOM);
        root.addView(controls, bottomParams);

        setContentView(root);
        showControlOverlay();
        updateUi(simulator.snapshot());
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (surfaceView != null) {
            surfaceView.onResume();
        }
        if (quickthingsAudioEngine != null) {
            quickthingsAudioEngine.start();
        }
        if (sportsCrowdAudioEngine != null) {
            sportsCrowdAudioEngine.start();
        }
        if (quickthingsHaptics != null) {
            quickthingsHaptics.start();
        }
        showControlOverlay();
        handler.removeCallbacks(tickLoop);
        handler.post(tickLoop);
    }

    @Override
    protected void onPause() {
        handler.removeCallbacks(tickLoop);
        handler.removeCallbacks(fadeControlsRunnable);
        if (quickthingsAudioEngine != null) {
            quickthingsAudioEngine.stop();
        }
        if (sportsCrowdAudioEngine != null) {
            sportsCrowdAudioEngine.stop();
        }
        if (quickthingsHaptics != null) {
            quickthingsHaptics.stop();
        }
        if (surfaceView != null) {
            surfaceView.onPause();
        }
        super.onPause();
    }

    private void updateUi(DirkOddsMatchState state) {
        refreshControlLabels(state.scenario.isQuickthings(), state.qteActive);
        if (state.scenario.isQuickthings()) {
            updateQuickthingsUi(state);
            return;
        }
        badgeView.setText(buildBadge(state));
        scoreView.setText(String.format(Locale.US,
                "%s | %s %d - %d %s",
                state.clockLabel,
                state.scenario.homeTeam,
                state.homeScore,
                state.awayScore,
                state.scenario.awayTeam));
        eventView.setText(state.eventLabel + " | " + state.scenario.venue + " | " + state.scenario.homeIdentity.shortMark() + " vs " + state.scenario.awayIdentity.shortMark());
        promptView.setText((state.qteActive ? "LIVE WINDOW // " : "FLOW // ") + state.prompt);
        promptView.setTextColor(state.qteActive ? Color.rgb(255, 208, 96) : Color.rgb(158, 231, 243));
        identityView.setText(
            state.scenario.homeIdentity.mascotLine() + " | " + state.scenario.homeIdentity.cheerNote + "\n" +
            state.scenario.awayIdentity.mascotLine() + " | " + state.scenario.awayIdentity.cheerNote);

        List<GridView.GridMetric> metrics = new ArrayList<>();
        metrics.add(new GridView.GridMetric("Prediction Edge", state.predictedLabel, state.predictionEdge, 0xFFE9C46A));
        metrics.add(new GridView.GridMetric("Momentum", state.scenario.homeTeam + " <> " + state.scenario.awayTeam, state.momentum, blend(state.scenario.awayColor, state.scenario.homeColor, state.momentum)));
        metrics.add(new GridView.GridMetric("Control", "coach stability", state.control, 0xFF5DD39E));
        metrics.add(new GridView.GridMetric("Reflex", state.qteActive ? "window open" : "window closed", state.reflex, 0xFF4DA8DA));
        metrics.add(new GridView.GridMetric("Pressure", state.finished ? "final state" : "live stress", state.pressure, 0xFFF25F5C));
        metricView.setMetrics(metrics);

        resultView.setText(state.finished
            ? (state.predictionCorrect ? "Call held through the final sequence." : "Final state broke the active call.")
            : "Active call: " + state.predictedLabel);
        if (state.finished) {
            resultView.setTextColor(state.predictionCorrect ? Color.rgb(42, 246, 186) : Color.rgb(255, 106, 144));
        } else {
            resultView.setTextColor(Color.rgb(255, 255, 255));
        }
        pulseButton.setEnabled(!state.finished);
        shapeButton.setEnabled(!state.finished);
        reflexButton.setEnabled(!state.finished);
        reflexButton.setText(controlButtonText(GLYPH_REFLEX, state.qteActive ? "Hit Reflex" : "Hold Reflex"));
        styleActionButton(reflexButton, state.qteActive ? Color.rgb(255, 79, 196) : Color.rgb(101, 119, 151), state.qteActive ? Color.rgb(255, 154, 220) : Color.rgb(150, 168, 198), state.qteActive);
        if (state.qteActive != lastQteState) {
            animateCueState(state.qteActive);
            lastQteState = state.qteActive;
        }
    }

        private void updateQuickthingsUi(DirkOddsMatchState state) {
        badgeView.setText(buildBadge(state));
        scoreView.setText(String.format(
            Locale.US,
                "%s | %s | Cleared %d",
            state.clockLabel,
                state.shotPhase,
                state.homeScore));
            eventView.setText(state.courseLabel + " stage | " + state.activeClub + " | " + state.activeIntent + " | " + state.syncLabel + " | phase " + Math.round(state.shotPhaseProgress * 100f) + "%");
        promptView.setText((state.qteActive ? "SYNC WINDOW // " : "COURSE FLOW // ") + state.prompt);
        promptView.setTextColor(state.qteActive ? Color.rgb(255, 208, 96) : Color.rgb(158, 231, 243));
        identityView.setText(
            state.scenario.quickthings.rulesAim + "\n"
                + String.format(
                    Locale.US,
                        "Consensus %.0f%% | Entropy %.0f%% | Vacuum %.0f%% | Sink Margin %.0f%% | Portals %d | Shot Phase %.0f%%",
                    state.consensus * 100f,
                    state.entropy * 100f,
                    state.remainingVacuum * 100f,
                    state.sinkMargin * 100f,
                        state.portalCount,
                        state.shotPhaseProgress * 100f));

        List<GridView.GridMetric> metrics = new ArrayList<>();
        metrics.add(new GridView.GridMetric("Consensus", "codex alignment", state.consensus, 0xFFE9C46A));
        metrics.add(new GridView.GridMetric("Entropy", "vacuum drag", state.entropy, 0xFFF25F5C));
        metrics.add(new GridView.GridMetric("Boson Sync", state.syncLabel.toLowerCase(Locale.US), state.bosonSync, 0xFF4DA8DA));
        metrics.add(new GridView.GridMetric("Card Charge", state.activeClub, state.cardCharge, 0xFF5DD39E));
        metrics.add(new GridView.GridMetric("Vacuum Left", state.courseLabel, state.remainingVacuum, blend(state.scenario.awayColor, state.scenario.homeColor, state.remainingVacuum)));
        metrics.add(new GridView.GridMetric("Sink Margin", state.activeIntent, state.sinkMargin, 0xFFFFB703));
            metrics.add(new GridView.GridMetric("Shot Time", state.shotPhase, state.shotPhaseProgress, 0xFFB8A1FF));
        metricView.setMetrics(metrics);

        resultView.setText(state.finished
            ? (state.predictionCorrect ? "Quickthings run stabilized through the full codex cycle." : "The cosmocourse broke before the final sink chain held.")
            : "Active lane: " + state.predictedLabel);
        resultView.setTextColor(state.finished
            ? (state.predictionCorrect ? Color.rgb(42, 246, 186) : Color.rgb(255, 106, 144))
            : Color.rgb(255, 255, 255));

        pulseButton.setEnabled(!state.finished);
        shapeButton.setEnabled(!state.finished);
        reflexButton.setEnabled(!state.finished);
        reflexButton.setText(controlButtonText(GLYPH_REFLEX, state.qteActive ? "Strike Now" : "Strike"));
        styleActionButton(reflexButton, state.qteActive ? Color.rgb(255, 79, 196) : Color.rgb(101, 119, 151), state.qteActive ? Color.rgb(255, 154, 220) : Color.rgb(150, 168, 198), state.qteActive);
        if (state.qteActive != lastQteState) {
            animateCueState(state.qteActive);
            lastQteState = state.qteActive;
        }
        }

    private LinearLayout buildGlyphLegendPanel(boolean quickthings) {
        LinearLayout panel = new LinearLayout(this);
        panel.setOrientation(LinearLayout.VERTICAL);
        panel.setPadding(dp(12), dp(12), dp(12), dp(12));
        panel.setBackground(buildOverlayBackground(214, Color.rgb(10, 13, 29), Color.rgb(24, 18, 40)));

        TextView title = new TextView(this);
        title.setText(GLYPH_MENU + " Touch Glyph Map");
        title.setTextColor(Color.rgb(241, 246, 255));
        title.setTypeface(Typeface.create("sans-serif-black", Typeface.BOLD));
        title.setTextSize(TypedValue.COMPLEX_UNIT_SP, 15);
        panel.addView(title);

        TextView subtitle = new TextView(this);
        subtitle.setText("Open this panel to inspect the touch glyphs. Close it to return to the phased-out gamepad strip.");
        subtitle.setTextColor(Color.rgb(182, 199, 222));
        subtitle.setTextSize(TypedValue.COMPLEX_UNIT_SP, 12);
        subtitle.setPadding(0, dp(4), 0, dp(10));
        panel.addView(subtitle);

        panel.addView(createGlyphLegendRow(GLYPH_PULSE, quickthings ? "Rift" : "Pulse", quickthings ? "Press to force lane pressure and widen the active branch." : "Press to pressure the active call and push momentum."));
        panel.addView(createGlyphLegendRow(GLYPH_SHAPE, quickthings ? "Sync" : "Shape", quickthings ? "Press to tighten geometry and keep consensus readable." : "Press to stabilize the formation and slow volatility."));
        panel.addView(createGlyphLegendRow(GLYPH_REFLEX, quickthings ? "Strike" : "Reflex", quickthings ? "Press during the live window to lock the chosen branch." : "Press during the live window to win the cue."));

        Button closeGlyphPanel = new Button(this);
        closeGlyphPanel.setText(GLYPH_CLOSE + " Close Glyph Map");
        styleActionButton(closeGlyphPanel, Color.rgb(98, 118, 161), Color.rgb(170, 186, 219), false);
        closeGlyphPanel.setOnClickListener(view -> toggleGlyphLegend());
        LinearLayout.LayoutParams closeParams = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        closeParams.topMargin = dp(10);
        panel.addView(closeGlyphPanel, closeParams);
        return panel;
    }

    private LinearLayout createGlyphLegendRow(String glyph, String label, String description) {
        LinearLayout row = new LinearLayout(this);
        row.setOrientation(LinearLayout.HORIZONTAL);
        row.setGravity(Gravity.CENTER_VERTICAL);
        row.setPadding(0, dp(4), 0, dp(4));

        TextView glyphBlock = new TextView(this);
        glyphBlock.setText(glyph);
        glyphBlock.setGravity(Gravity.CENTER);
        glyphBlock.setTextColor(Color.rgb(247, 249, 255));
        glyphBlock.setTypeface(Typeface.create("sans-serif-black", Typeface.BOLD));
        glyphBlock.setTextSize(TypedValue.COMPLEX_UNIT_SP, 20);
        glyphBlock.setBackground(buildGlyphBackground(Color.rgb(94, 234, 255), false));
        glyphBlock.setPadding(dp(12), dp(8), dp(12), dp(8));
        row.addView(glyphBlock, new LinearLayout.LayoutParams(dp(52), ViewGroup.LayoutParams.WRAP_CONTENT));

        TextView descriptionView = new TextView(this);
        descriptionView.setText(label.toUpperCase(Locale.US) + " // " + description);
        descriptionView.setTextColor(Color.rgb(207, 218, 236));
        descriptionView.setTextSize(TypedValue.COMPLEX_UNIT_SP, 12);
        descriptionView.setPadding(dp(10), 0, 0, 0);
        row.addView(descriptionView, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));
        return row;
    }

    private TextView createGlyphPad(String glyph, String label, int accentColor) {
        TextView view = new TextView(this);
        view.setGravity(Gravity.CENTER);
        view.setText(controlGlyphText(glyph, label));
        view.setTextColor(Color.rgb(242, 246, 255));
        view.setTypeface(Typeface.create("sans-serif-black", Typeface.BOLD));
        view.setTextSize(TypedValue.COMPLEX_UNIT_SP, 12);
        view.setPadding(dp(10), dp(8), dp(10), dp(8));
        view.setBackground(buildGlyphBackground(accentColor, false));
        view.setTag(accentColor);
        return view;
    }

    private GradientDrawable buildGlyphBackground(int accentColor, boolean active) {
        int start = active ? accentColor : Color.argb(148, 12, 16, 28);
        int end = active ? lightenColor(accentColor, 0.24f) : Color.argb(132, 28, 30, 46);
        GradientDrawable background = new GradientDrawable(
                GradientDrawable.Orientation.TL_BR,
                new int[] {start, end});
        background.setCornerRadius(dp(18));
        background.setStroke(dp(1), Color.argb(active ? 220 : 158, Color.red(accentColor), Color.green(accentColor), Color.blue(accentColor)));
        return background;
    }

    private void refreshControlLabels(boolean quickthings, boolean qteActive) {
        if (pulseGlyphView == null || shapeGlyphView == null || reflexGlyphView == null) {
            return;
        }
        String pulseLabel = quickthings ? "RIFT" : "PULSE";
        String shapeLabel = quickthings ? "SYNC" : "SHAPE";
        String reflexLabel = quickthings ? (qteActive ? "STRIKE NOW" : "STRIKE") : (qteActive ? "HIT REFLEX" : "HOLD REFLEX");
        pulseGlyphView.setText(controlGlyphText(GLYPH_PULSE, pulseLabel));
        shapeGlyphView.setText(controlGlyphText(GLYPH_SHAPE, shapeLabel));
        reflexGlyphView.setText(controlGlyphText(GLYPH_REFLEX, reflexLabel));
    }

    private void pulseControlDisplay(TextView targetView) {
        showControlOverlay();
        if (targetView == null) {
            return;
        }
        int accentColor = targetView.getTag() instanceof Integer ? (Integer) targetView.getTag() : Color.rgb(94, 234, 255);
        targetView.setBackground(buildGlyphBackground(accentColor, true));
        targetView.animate().scaleX(1.08f).scaleY(1.08f).setDuration(120L).withEndAction(() -> {
            targetView.setBackground(buildGlyphBackground(accentColor, false));
            targetView.animate().scaleX(1f).scaleY(1f).setDuration(180L).start();
        }).start();
    }

    private void showControlOverlay() {
        if (controlOverlayStrip == null) {
            return;
        }
        handler.removeCallbacks(fadeControlsRunnable);
        controlOverlayStrip.animate().alpha(0.94f).setDuration(140L).start();
        if (!glyphLegendOpen) {
            handler.postDelayed(fadeControlsRunnable, CONTROL_OVERLAY_FADE_DELAY_MS);
        }
    }

    private void toggleGlyphLegend() {
        if (glyphLegendPanel == null || glyphMenuButton == null) {
            return;
        }
        glyphLegendOpen = !glyphLegendOpen;
        handler.removeCallbacks(fadeControlsRunnable);
        if (glyphLegendOpen) {
            glyphMenuButton.setText(GLYPH_CLOSE + " Close");
            glyphLegendPanel.setVisibility(View.VISIBLE);
            glyphLegendPanel.animate().alpha(1f).setDuration(180L).start();
            if (controlOverlayStrip != null) {
                controlOverlayStrip.animate().alpha(1f).setDuration(120L).start();
            }
        } else {
            glyphMenuButton.setText(GLYPH_MENU + " Glyphs");
            glyphLegendPanel.animate().alpha(0f).setDuration(150L).withEndAction(() -> glyphLegendPanel.setVisibility(View.GONE)).start();
            handler.postDelayed(fadeControlsRunnable, 120L);
        }
    }

    private String controlGlyphText(String glyph, String label) {
        return glyph + "\n" + label;
    }

    private String controlButtonText(String glyph, String label) {
        return glyph + "  " + label;
    }

    private SpannableString buildBadge(DirkOddsMatchState state) {
        String sport = state.scenario.isQuickthings()
            ? "QUICKTHINGS"
            : titleCase(state.scenario.sport).toUpperCase(Locale.US);
        String status = state.finished ? "FINAL" : (state.qteActive ? "WINDOW OPEN" : "LIVE FLOW");
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
        showControlOverlay();
        if (qteActive) {
            badgeView.animate().scaleX(1.04f).scaleY(1.04f).setDuration(140).withEndAction(
                    () -> badgeView.animate().scaleX(1f).scaleY(1f).setDuration(180).start()).start();
            promptView.animate().alpha(0.68f).setDuration(0).withEndAction(
                    () -> promptView.animate().alpha(1f).setDuration(220).start()).start();
            reflexButton.animate().scaleX(1.06f).scaleY(1.06f).setDuration(120).withEndAction(
                    () -> reflexButton.animate().scaleX(1f).scaleY(1f).setDuration(180).start()).start();
            pulseControlDisplay(reflexGlyphView);
        } else {
            reflexButton.animate().rotation(0f).setDuration(120).start();
            promptView.animate().alpha(0.9f).setDuration(120).start();
        }
    }

    private void performActionHaptics(View view, boolean emphatic) {
        if (quickthingsHaptics != null) {
            quickthingsHaptics.performTapFeedback(view, emphatic);
        } else if (view != null) {
            view.performHapticFeedback(emphatic
                    ? HapticFeedbackConstants.LONG_PRESS
                    : HapticFeedbackConstants.VIRTUAL_KEY);
        }
    }

    private int blend(int awayColor, int homeColor, float t) {
        float clamped = Math.max(0f, Math.min(1f, t));
        int r = (int) (Color.red(awayColor) + (Color.red(homeColor) - Color.red(awayColor)) * clamped);
        int g = (int) (Color.green(awayColor) + (Color.green(homeColor) - Color.green(awayColor)) * clamped);
        int b = (int) (Color.blue(awayColor) + (Color.blue(homeColor) - Color.blue(awayColor)) * clamped);
        return Color.rgb(r, g, b);
    }

    private int lightenColor(int color, float amount) {
        int r = (int) (Color.red(color) + (255 - Color.red(color)) * amount);
        int g = (int) (Color.green(color) + (255 - Color.green(color)) * amount);
        int b = (int) (Color.blue(color) + (255 - Color.blue(color)) * amount);
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

    private int compactOverlayWidth() {
        int screenWidth = getResources().getDisplayMetrics().widthPixels;
        return Math.min(dp(352), screenWidth - dp(20));
    }
}