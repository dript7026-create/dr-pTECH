package com.urbden.game;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.text.SpannableString;
import android.text.Spanned;
import android.text.style.ForegroundColorSpan;
import android.text.style.StyleSpan;
import android.util.TypedValue;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

public class MainActivity extends Activity {
    private final List<Button> scenarioButtons = new ArrayList<>();

    private List<DirkOddsScenario> scenarios;
    private DirkOddsScenario selectedScenario;
    private int predictedOutcome = DirkOddsSimulator.OUTCOME_HOME;

    private TextView scenarioTitleView;
    private TextView scenarioSummaryView;
    private TextView scenarioVenueView;
    private TextView predictionView;
    private GridView metricView;
    private Button awayButton;
    private Button drawButton;
    private Button homeButton;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        scenarios = DirkOddsScenarioRepository.load(this);
        int padding = dp(16);

        ScrollView scrollView = new ScrollView(this);
        scrollView.setFillViewport(true);
        scrollView.setBackgroundColor(Color.rgb(6, 8, 18));
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(padding, padding, padding, padding);
        root.setBackgroundColor(Color.rgb(6, 8, 18));

        TextView eyebrowView = new TextView(this);
        eyebrowView.setText("DIRK//ODDS SIGNAL DECK");
        eyebrowView.setTextColor(Color.rgb(24, 246, 210));
        eyebrowView.setTextSize(TypedValue.COMPLEX_UNIT_SP, 11);
        eyebrowView.setTypeface(Typeface.create("sans-serif-medium", Typeface.BOLD));
        eyebrowView.setLetterSpacing(0.18f);
        root.addView(eyebrowView);

        TextView titleView = new TextView(this);
        titleView.setText(buildBrandTitle());
        titleView.setTextColor(Color.rgb(240, 246, 255));
        titleView.setTextSize(TypedValue.COMPLEX_UNIT_SP, 31);
        titleView.setTypeface(Typeface.create("sans-serif-black", Typeface.BOLD));
        titleView.setPadding(0, dp(4), 0, dp(2));
        root.addView(titleView);

        TextView subtitleView = new TextView(this);
        subtitleView.setText(
                "Anonymous multi-sport prediction testing with abstract 3D playback, subtle reflex windows, and lightweight coaching interactions. " +
                        "No real leagues, franchises, player identities, or licensed likenesses are used in this mobile preview.");
        subtitleView.setTextSize(TypedValue.COMPLEX_UNIT_SP, 15);
        subtitleView.setTextColor(Color.rgb(150, 172, 196));
        subtitleView.setPadding(0, dp(8), 0, dp(16));
        root.addView(subtitleView);

        LinearLayout deckPanel = buildPanel();
        root.addView(deckPanel);

        TextView deckLabel = new TextView(this);
        deckLabel.setText("SYNTHETIC MATCH DECK");
        deckLabel.setTextColor(Color.rgb(24, 246, 210));
        deckLabel.setTypeface(Typeface.create("sans-serif-medium", Typeface.BOLD));
        deckLabel.setLetterSpacing(0.12f);
        deckLabel.setTextSize(TypedValue.COMPLEX_UNIT_SP, 14);
        deckLabel.setPadding(0, 0, 0, dp(8));
        deckPanel.addView(deckLabel);

        LinearLayout scenarioColumn = new LinearLayout(this);
        scenarioColumn.setOrientation(LinearLayout.VERTICAL);
        deckPanel.addView(scenarioColumn);

        LinearLayout detailPanel = buildPanel();
        detailPanel.setPadding(dp(18), dp(18), dp(18), dp(18));
        root.addView(detailPanel);

        scenarioTitleView = new TextView(this);
        scenarioTitleView.setTextColor(Color.rgb(246, 248, 255));
        scenarioTitleView.setTextSize(TypedValue.COMPLEX_UNIT_SP, 23);
        scenarioTitleView.setTypeface(Typeface.create("sans-serif-black", Typeface.BOLD));
        scenarioTitleView.setPadding(0, 0, 0, dp(6));
        detailPanel.addView(scenarioTitleView);

        scenarioSummaryView = new TextView(this);
        scenarioSummaryView.setTextSize(TypedValue.COMPLEX_UNIT_SP, 14);
        scenarioSummaryView.setTextColor(Color.rgb(175, 190, 210));
        detailPanel.addView(scenarioSummaryView);

        scenarioVenueView = new TextView(this);
        scenarioVenueView.setTextSize(TypedValue.COMPLEX_UNIT_SP, 13);
        scenarioVenueView.setTextColor(Color.rgb(248, 88, 182));
        scenarioVenueView.setTypeface(Typeface.create("monospace", Typeface.BOLD));
        scenarioVenueView.setPadding(0, dp(6), 0, dp(10));
        detailPanel.addView(scenarioVenueView);

        metricView = new GridView(this);
        detailPanel.addView(metricView, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT));

        LinearLayout pickPanel = buildPanel();
        root.addView(pickPanel);

        TextView pickLabel = new TextView(this);
        pickLabel.setText("PREDICTION LANE");
        pickLabel.setTextColor(Color.rgb(255, 192, 65));
        pickLabel.setTypeface(Typeface.create("sans-serif-medium", Typeface.BOLD));
        pickLabel.setLetterSpacing(0.1f);
        pickLabel.setTextSize(TypedValue.COMPLEX_UNIT_SP, 14);
        pickLabel.setPadding(0, dp(12), 0, dp(8));
        pickPanel.addView(pickLabel);

        LinearLayout pickRow = new LinearLayout(this);
        pickRow.setOrientation(LinearLayout.HORIZONTAL);
        pickPanel.addView(pickRow);

        awayButton = buildPredictionButton("Away Edge", DirkOddsSimulator.OUTCOME_AWAY);
        drawButton = buildPredictionButton("Draw Lane", DirkOddsSimulator.OUTCOME_DRAW);
        homeButton = buildPredictionButton("Home Edge", DirkOddsSimulator.OUTCOME_HOME);
        pickRow.addView(awayButton, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));
        pickRow.addView(drawButton, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));
        pickRow.addView(homeButton, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));

        predictionView = new TextView(this);
        predictionView.setTextSize(TypedValue.COMPLEX_UNIT_SP, 14);
    predictionView.setTextColor(Color.rgb(221, 230, 244));
        predictionView.setPadding(0, dp(10), 0, dp(12));
    pickPanel.addView(predictionView);

        Button launchButton = new Button(this);
    stylePrimaryButton(launchButton, Color.rgb(255, 74, 194), Color.rgb(255, 196, 88));
    launchButton.setText("Launch Neon 3D Test");
        launchButton.setOnClickListener(view -> launchScenario());
    pickPanel.addView(launchButton);

        TextView footer = new TextView(this);
        footer.setText(
                "The mobile preview uses fictional team identities, abstract avatars, and synthetic match states. " +
                        "It is intended for interaction design, prediction testing, and review, not guaranteed forecasting.");
        footer.setTextSize(TypedValue.COMPLEX_UNIT_SP, 12);
    footer.setTextColor(Color.rgb(112, 130, 154));
        footer.setPadding(0, dp(10), 0, 0);
        root.addView(footer);

        for (DirkOddsScenario scenario : scenarios) {
            Button button = new Button(this);
            button.setText(String.format(Locale.US, "%s  %s vs %s", sportGlyph(scenario.sport), scenario.homeTeam, scenario.awayTeam));
            styleScenarioButton(button, scenario);
            button.setOnClickListener(view -> selectScenario(scenario));
            scenarioButtons.add(button);
            scenarioColumn.addView(button);
        }

        if (!scenarios.isEmpty()) {
            selectScenario(scenarios.get(0));
        } else {
            scenarioTitleView.setText("No scenarios available");
            scenarioSummaryView.setText("The packaged mobile scenario deck could not be loaded.");
            scenarioVenueView.setText("Add assets/dirkodds/scenarios.json before launching playback.");
        }

        scrollView.addView(root);
        setContentView(scrollView);
    }

    private Button buildPredictionButton(String label, int outcome) {
        Button button = new Button(this);
        stylePredictionButton(button);
        button.setText(label);
        button.setOnClickListener(view -> setPredictedOutcome(outcome));
        return button;
    }

    private void selectScenario(DirkOddsScenario scenario) {
        selectedScenario = scenario;
        scenarioTitleView.setText(scenario.title);
        scenarioSummaryView.setText(scenario.summary);
        scenarioVenueView.setText(String.format(Locale.US, "%s  %s | %s vs %s | %s", sportGlyph(scenario.sport), titleCase(scenario.sport), scenario.homeTeam, scenario.awayTeam, scenario.venue));

        List<GridView.GridMetric> metrics = new ArrayList<>();
        metrics.add(new GridView.GridMetric("Away", scenario.awayTeam, scenario.awayProbability, scenario.awayColor));
        if (scenario.supportsDraw()) {
            metrics.add(new GridView.GridMetric("Draw", "balanced lane", scenario.drawProbability, 0xFFB9A44C));
        }
        metrics.add(new GridView.GridMetric("Home", scenario.homeTeam, scenario.homeProbability, scenario.homeColor));
        metrics.add(new GridView.GridMetric("Tempo", scenario.venue, scenario.tempo, 0xFF7AC74F));
        metricView.setMetrics(metrics);

        if (!scenario.supportsDraw() && predictedOutcome == DirkOddsSimulator.OUTCOME_DRAW) {
            predictedOutcome = scenario.homeProbability >= scenario.awayProbability
                    ? DirkOddsSimulator.OUTCOME_HOME
                    : DirkOddsSimulator.OUTCOME_AWAY;
        }

        for (int i = 0; i < scenarioButtons.size(); i++) {
            Button button = scenarioButtons.get(i);
            boolean active = scenarios.get(i) == scenario;
            button.setEnabled(!active);
            button.setAlpha(active ? 1f : 0.92f);
            button.animate()
                    .scaleX(active ? 1.03f : 1.0f)
                    .scaleY(active ? 1.03f : 1.0f)
                    .translationX(active ? dp(4) : 0)
                    .setDuration(180)
                    .start();
        }
        updatePredictionUi();
    }

    private void setPredictedOutcome(int outcome) {
        if (selectedScenario == null) {
            return;
        }
        if (outcome == DirkOddsSimulator.OUTCOME_DRAW && !selectedScenario.supportsDraw()) {
            return;
        }
        predictedOutcome = outcome;
        updatePredictionUi();
    }

    private void updatePredictionUi() {
        awayButton.setEnabled(predictedOutcome != DirkOddsSimulator.OUTCOME_AWAY);
        homeButton.setEnabled(predictedOutcome != DirkOddsSimulator.OUTCOME_HOME);
        drawButton.setEnabled(selectedScenario != null && selectedScenario.supportsDraw() && predictedOutcome != DirkOddsSimulator.OUTCOME_DRAW);
        if (selectedScenario == null) {
            predictionView.setText("No scenario selected.");
            return;
        }

        String prediction;
        if (predictedOutcome == DirkOddsSimulator.OUTCOME_AWAY) {
            prediction = selectedScenario.awayTeam + " edge";
            tintPredictionButton(awayButton, true, selectedScenario.awayColor);
            tintPredictionButton(drawButton, false, 0xFFB9A44C);
            tintPredictionButton(homeButton, false, selectedScenario.homeColor);
        } else if (predictedOutcome == DirkOddsSimulator.OUTCOME_DRAW) {
            prediction = "balanced draw lane";
            tintPredictionButton(awayButton, false, selectedScenario.awayColor);
            tintPredictionButton(drawButton, true, 0xFFB9A44C);
            tintPredictionButton(homeButton, false, selectedScenario.homeColor);
        } else {
            prediction = selectedScenario.homeTeam + " edge";
            tintPredictionButton(awayButton, false, selectedScenario.awayColor);
            tintPredictionButton(drawButton, false, 0xFFB9A44C);
            tintPredictionButton(homeButton, true, selectedScenario.homeColor);
        }
        predictionView.setText("Current test pick: " + prediction + ". Use pulse, shape, and reflex taps during playback to pressure-test it in motion.");
        predictionView.animate()
            .alpha(0.72f)
            .setDuration(0)
            .withEndAction(() -> predictionView.animate().alpha(1f).setDuration(180).start())
            .start();
    }

    private SpannableString buildBrandTitle() {
        String text = "DIRK//ODDS MOBILE";
        SpannableString styled = new SpannableString(text);
        styled.setSpan(new ForegroundColorSpan(Color.rgb(30, 242, 216)), 0, 4, Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);
        styled.setSpan(new ForegroundColorSpan(Color.rgb(246, 248, 255)), 4, 6, Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);
        styled.setSpan(new ForegroundColorSpan(Color.rgb(255, 88, 196)), 6, 10, Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);
        styled.setSpan(new ForegroundColorSpan(Color.rgb(255, 196, 88)), 11, text.length(), Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);
        styled.setSpan(new StyleSpan(Typeface.BOLD), 0, text.length(), Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);
        return styled;
    }

    private LinearLayout buildPanel() {
        LinearLayout panel = new LinearLayout(this);
        panel.setOrientation(LinearLayout.VERTICAL);
        panel.setPadding(dp(18), dp(18), dp(18), dp(18));
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT);
        params.bottomMargin = dp(14);
        panel.setLayoutParams(params);
        GradientDrawable background = new GradientDrawable(
                GradientDrawable.Orientation.TL_BR,
                new int[] {Color.rgb(11, 16, 32), Color.rgb(18, 24, 44)});
        background.setCornerRadius(dp(22));
        background.setStroke(dp(1), Color.argb(168, 98, 241, 255));
        panel.setBackground(background);
        return panel;
    }

    private void styleScenarioButton(Button button, DirkOddsScenario scenario) {
        button.setAllCaps(false);
        button.setTextColor(Color.rgb(236, 244, 255));
        button.setTextSize(TypedValue.COMPLEX_UNIT_SP, 14);
        button.setTypeface(Typeface.create("sans-serif-medium", Typeface.BOLD));
        button.setPadding(dp(14), dp(14), dp(14), dp(14));
        GradientDrawable background = new GradientDrawable(
                GradientDrawable.Orientation.LEFT_RIGHT,
                new int[] {Color.argb(255, 18, 32, 56), Color.argb(255, 11, 18, 32)});
        background.setCornerRadius(dp(18));
        background.setStroke(dp(2), blendColors(scenario.awayColor, scenario.homeColor));
        button.setBackground(background);
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT);
        params.bottomMargin = dp(10);
        button.setLayoutParams(params);
    }

    private void stylePredictionButton(Button button) {
        button.setAllCaps(false);
        button.setTextColor(Color.rgb(244, 248, 255));
        button.setTextSize(TypedValue.COMPLEX_UNIT_SP, 13);
        button.setTypeface(Typeface.create("sans-serif-medium", Typeface.BOLD));
        button.setPadding(dp(8), dp(14), dp(8), dp(14));
    }

    private void tintPredictionButton(Button button, boolean active, int accentColor) {
        GradientDrawable background = new GradientDrawable(
                GradientDrawable.Orientation.LEFT_RIGHT,
                active
                        ? new int[] {accentColor, shiftColor(accentColor, 0.78f)}
                        : new int[] {Color.rgb(14, 21, 38), Color.rgb(10, 15, 28)});
        background.setCornerRadius(dp(18));
        background.setStroke(dp(active ? 2 : 1), active ? Color.rgb(244, 248, 255) : accentColor);
        button.setBackground(background);
        button.setTextColor(active ? Color.rgb(8, 12, 22) : Color.rgb(235, 244, 255));
        button.setAlpha(active ? 1f : 0.96f);
    }

    private void stylePrimaryButton(Button button, int startColor, int endColor) {
        button.setAllCaps(false);
        button.setTextColor(Color.rgb(9, 10, 20));
        button.setTextSize(TypedValue.COMPLEX_UNIT_SP, 16);
        button.setTypeface(Typeface.create("sans-serif-black", Typeface.BOLD));
        button.setPadding(dp(12), dp(16), dp(12), dp(16));
        GradientDrawable background = new GradientDrawable(
                GradientDrawable.Orientation.LEFT_RIGHT,
                new int[] {startColor, endColor});
        background.setCornerRadius(dp(20));
        background.setStroke(dp(1), Color.argb(190, 255, 255, 255));
        button.setBackground(background);
    }

    private int blendColors(int awayColor, int homeColor) {
        int r = (Color.red(awayColor) + Color.red(homeColor)) / 2;
        int g = (Color.green(awayColor) + Color.green(homeColor)) / 2;
        int b = (Color.blue(awayColor) + Color.blue(homeColor)) / 2;
        return Color.rgb(r, g, b);
    }

    private int shiftColor(int color, float factor) {
        int r = Math.min(255, Math.round(Color.red(color) + (255 - Color.red(color)) * factor));
        int g = Math.min(255, Math.round(Color.green(color) + (255 - Color.green(color)) * factor));
        int b = Math.min(255, Math.round(Color.blue(color) + (255 - Color.blue(color)) * factor));
        return Color.rgb(r, g, b);
    }

    private String sportGlyph(String sport) {
        switch (sport) {
            case "basketball":
                return "◎";
            case "baseball":
                return "◇";
            default:
                return "▲";
        }
    }

    private void launchScenario() {
        if (selectedScenario == null) {
            return;
        }
        Intent intent = new Intent(this, PlaybackActivity.class);
        intent.putExtra("scenario_id", selectedScenario.id);
        intent.putExtra("predicted_outcome", predictedOutcome);
        startActivity(intent);
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
