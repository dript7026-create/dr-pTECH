package com.urbden.game;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Typeface;
import android.os.Bundle;
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
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(padding, padding, padding, padding);

        TextView titleView = new TextView(this);
        titleView.setText("DirkOdds Mobile Test Arena");
        titleView.setTextSize(TypedValue.COMPLEX_UNIT_SP, 27);
        titleView.setTypeface(Typeface.DEFAULT_BOLD);
        root.addView(titleView);

        TextView subtitleView = new TextView(this);
        subtitleView.setText(
                "Anonymous multi-sport prediction testing with abstract 3D playback, subtle reflex windows, and lightweight coaching interactions. " +
                        "No real leagues, franchises, player identities, or licensed likenesses are used in this mobile preview.");
        subtitleView.setTextSize(TypedValue.COMPLEX_UNIT_SP, 15);
        subtitleView.setPadding(0, dp(8), 0, dp(12));
        root.addView(subtitleView);

        TextView deckLabel = new TextView(this);
        deckLabel.setText("Synthetic Match Deck");
        deckLabel.setTypeface(Typeface.DEFAULT_BOLD);
        deckLabel.setTextSize(TypedValue.COMPLEX_UNIT_SP, 18);
        deckLabel.setPadding(0, 0, 0, dp(8));
        root.addView(deckLabel);

        LinearLayout scenarioColumn = new LinearLayout(this);
        scenarioColumn.setOrientation(LinearLayout.VERTICAL);
        root.addView(scenarioColumn);

        scenarioTitleView = new TextView(this);
        scenarioTitleView.setTextSize(TypedValue.COMPLEX_UNIT_SP, 21);
        scenarioTitleView.setTypeface(Typeface.DEFAULT_BOLD);
        scenarioTitleView.setPadding(0, dp(14), 0, dp(6));
        root.addView(scenarioTitleView);

        scenarioSummaryView = new TextView(this);
        scenarioSummaryView.setTextSize(TypedValue.COMPLEX_UNIT_SP, 14);
        root.addView(scenarioSummaryView);

        scenarioVenueView = new TextView(this);
        scenarioVenueView.setTextSize(TypedValue.COMPLEX_UNIT_SP, 13);
        scenarioVenueView.setPadding(0, dp(6), 0, dp(10));
        root.addView(scenarioVenueView);

        metricView = new GridView(this);
        root.addView(metricView, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT));

        TextView pickLabel = new TextView(this);
        pickLabel.setText("Prediction Lane");
        pickLabel.setTypeface(Typeface.DEFAULT_BOLD);
        pickLabel.setTextSize(TypedValue.COMPLEX_UNIT_SP, 18);
        pickLabel.setPadding(0, dp(12), 0, dp(8));
        root.addView(pickLabel);

        LinearLayout pickRow = new LinearLayout(this);
        pickRow.setOrientation(LinearLayout.HORIZONTAL);
        root.addView(pickRow);

        awayButton = buildPredictionButton("Away Edge", DirkOddsSimulator.OUTCOME_AWAY);
        drawButton = buildPredictionButton("Draw Lane", DirkOddsSimulator.OUTCOME_DRAW);
        homeButton = buildPredictionButton("Home Edge", DirkOddsSimulator.OUTCOME_HOME);
        pickRow.addView(awayButton, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));
        pickRow.addView(drawButton, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));
        pickRow.addView(homeButton, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));

        predictionView = new TextView(this);
        predictionView.setTextSize(TypedValue.COMPLEX_UNIT_SP, 14);
        predictionView.setPadding(0, dp(10), 0, dp(12));
        root.addView(predictionView);

        Button launchButton = new Button(this);
        launchButton.setAllCaps(false);
        launchButton.setText("Launch 3D Prediction Test");
        launchButton.setOnClickListener(view -> launchScenario());
        root.addView(launchButton);

        TextView footer = new TextView(this);
        footer.setText(
                "The mobile preview uses fictional team identities, abstract avatars, and synthetic match states. " +
                        "It is intended for interaction design, prediction testing, and review, not guaranteed forecasting.");
        footer.setTextSize(TypedValue.COMPLEX_UNIT_SP, 12);
        footer.setPadding(0, dp(10), 0, 0);
        root.addView(footer);

        for (DirkOddsScenario scenario : scenarios) {
            Button button = new Button(this);
            button.setAllCaps(false);
            button.setText(String.format(Locale.US, "%s | %s vs %s", titleCase(scenario.sport), scenario.homeTeam, scenario.awayTeam));
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
        button.setAllCaps(false);
        button.setText(label);
        button.setOnClickListener(view -> setPredictedOutcome(outcome));
        return button;
    }

    private void selectScenario(DirkOddsScenario scenario) {
        selectedScenario = scenario;
        scenarioTitleView.setText(scenario.title);
        scenarioSummaryView.setText(scenario.summary);
        scenarioVenueView.setText(String.format(Locale.US, "%s | %s vs %s | %s", titleCase(scenario.sport), scenario.homeTeam, scenario.awayTeam, scenario.venue));

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
            scenarioButtons.get(i).setEnabled(scenarios.get(i) != scenario);
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
        } else if (predictedOutcome == DirkOddsSimulator.OUTCOME_DRAW) {
            prediction = "balanced draw lane";
        } else {
            prediction = selectedScenario.homeTeam + " edge";
        }
        predictionView.setText("Current test pick: " + prediction + ". Use pulse, shape, and reflex taps during playback to pressure-test it in motion.");
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
