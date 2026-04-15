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
    private TextView scenarioIdentityView;
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
        scrollView.setBackgroundColor(Color.rgb(5, 8, 20));
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(padding, padding, padding, padding);
        root.setBackgroundColor(Color.rgb(5, 8, 20));

        LinearLayout heroPanel = buildHeroPanel();
        root.addView(heroPanel);

        TextView eyebrowView = new TextView(this);
        eyebrowView.setText("CLIENT REVIEW BUILD");
        eyebrowView.setTextColor(Color.rgb(96, 230, 255));
        eyebrowView.setTextSize(TypedValue.COMPLEX_UNIT_SP, 11);
        eyebrowView.setTypeface(Typeface.create("sans-serif-medium", Typeface.BOLD));
        eyebrowView.setLetterSpacing(0.18f);
        heroPanel.addView(eyebrowView);

        TextView titleView = new TextView(this);
        titleView.setText(buildBrandTitle());
        titleView.setTextColor(Color.rgb(240, 246, 255));
        titleView.setTextSize(TypedValue.COMPLEX_UNIT_SP, 33);
        titleView.setTypeface(Typeface.create("sans-serif-black", Typeface.BOLD));
        titleView.setPadding(0, dp(6), 0, dp(4));
        heroPanel.addView(titleView);

        LinearLayout heroChipRow = new LinearLayout(this);
        heroChipRow.setOrientation(LinearLayout.HORIZONTAL);
        heroChipRow.setPadding(0, dp(4), 0, dp(4));
        heroChipRow.addView(buildHeroChip("SYNTHETIC SPORTS", Color.rgb(96, 230, 255), Color.rgb(9, 39, 52)));
        heroChipRow.addView(buildHeroChip("LIVE 3D TESTBED", Color.rgb(255, 212, 128), Color.rgb(52, 32, 11)));
        heroPanel.addView(heroChipRow);

        TextView subtitleView = new TextView(this);
        subtitleView.setText(
            "Fast signal reads, interactive playback, and coached pressure testing for fictional matchups. " +
                "No real leagues, clubs, players, or licensed likenesses appear in this preview.");
        subtitleView.setTextSize(TypedValue.COMPLEX_UNIT_SP, 15);
        subtitleView.setTextColor(Color.rgb(186, 196, 216));
        subtitleView.setPadding(0, dp(10), 0, 0);
        heroPanel.addView(subtitleView);

        LinearLayout deckPanel = buildPanel();
        root.addView(deckPanel);

        TextView deckLabel = new TextView(this);
        deckLabel.setText("TEST SCENARIOS");
        deckLabel.setTextColor(Color.rgb(96, 230, 255));
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

        scenarioIdentityView = new TextView(this);
        scenarioIdentityView.setTextSize(TypedValue.COMPLEX_UNIT_SP, 13);
        scenarioIdentityView.setTextColor(Color.rgb(196, 211, 232));
        scenarioIdentityView.setPadding(0, 0, 0, dp(10));
        detailPanel.addView(scenarioIdentityView);

        metricView = new GridView(this);
        detailPanel.addView(metricView, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT));

        LinearLayout pickPanel = buildPanel();
        root.addView(pickPanel);

        TextView pickLabel = new TextView(this);
        pickLabel.setText("CALL THE LANE");
        pickLabel.setTextColor(Color.rgb(255, 212, 128));
        pickLabel.setTypeface(Typeface.create("sans-serif-medium", Typeface.BOLD));
        pickLabel.setLetterSpacing(0.1f);
        pickLabel.setTextSize(TypedValue.COMPLEX_UNIT_SP, 14);
        pickLabel.setPadding(0, dp(12), 0, dp(8));
        pickPanel.addView(pickLabel);

        LinearLayout pickRow = new LinearLayout(this);
        pickRow.setOrientation(LinearLayout.HORIZONTAL);
        pickPanel.addView(pickRow);

        awayButton = buildPredictionButton("Away Lane", DirkOddsSimulator.OUTCOME_AWAY);
        drawButton = buildPredictionButton("Draw Lane", DirkOddsSimulator.OUTCOME_DRAW);
        homeButton = buildPredictionButton("Home Lane", DirkOddsSimulator.OUTCOME_HOME);
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
        launchButton.setText("Enter Signal Arena");
        launchButton.setOnClickListener(view -> launchScenario());
        pickPanel.addView(launchButton);

        TextView footer = new TextView(this);
        footer.setText(
                "Fictional identities only. Built for client review, interaction testing, and prediction-flow evaluation rather than guaranteed forecasting.");
        footer.setTextSize(TypedValue.COMPLEX_UNIT_SP, 12);
        footer.setTextColor(Color.rgb(112, 130, 154));
        footer.setPadding(0, dp(10), 0, 0);
        root.addView(footer);

        for (DirkOddsScenario scenario : scenarios) {
            Button button = new Button(this);
            button.setText(String.format(Locale.US, "%s  %s", sportGlyph(scenario.sport), scenario.matchupDeckLabel()));
            styleScenarioButton(button, scenario);
            button.setOnClickListener(view -> selectScenario(scenario));
            scenarioButtons.add(button);
            scenarioColumn.addView(button);
        }

        if (!scenarios.isEmpty()) {
            selectScenario(scenarios.get(0));
        } else {
            scenarioTitleView.setText("No scenarios loaded");
            scenarioSummaryView.setText("The packaged scenario deck is missing from this build.");
            scenarioVenueView.setText("Restore assets/dirkodds/scenarios.json to enable playback.");
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
        scenarioIdentityView.setText(
            scenario.identityHeadline() + "\n" +
            scenario.sidelineBrief() + "\n" +
            scenario.uniformBrief());

        List<GridView.GridMetric> metrics = new ArrayList<>();
        metrics.add(new GridView.GridMetric(scenario.laneLabel(DirkOddsSimulator.OUTCOME_AWAY), scenario.awayTeam, scenario.awayProbability, scenario.awayColor));
        if (scenario.supportsDraw()) {
            metrics.add(new GridView.GridMetric(scenario.laneLabel(DirkOddsSimulator.OUTCOME_DRAW), scenario.isQuickthings() ? "codex balance" : "balanced lane", scenario.drawProbability, 0xFFB9A44C));
        }
        metrics.add(new GridView.GridMetric(scenario.laneLabel(DirkOddsSimulator.OUTCOME_HOME), scenario.homeTeam, scenario.homeProbability, scenario.homeColor));
        metrics.add(new GridView.GridMetric(scenario.isQuickthings() ? "Course Tempo" : "Tempo", scenario.venue, scenario.tempo, 0xFF7AC74F));
        metricView.setMetrics(metrics);

        awayButton.setText(scenario.laneLabel(DirkOddsSimulator.OUTCOME_AWAY));
        drawButton.setText(scenario.laneLabel(DirkOddsSimulator.OUTCOME_DRAW));
        homeButton.setText(scenario.laneLabel(DirkOddsSimulator.OUTCOME_HOME));

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
            predictionView.setText("Pick a scenario to arm the playback lane.");
            return;
        }

        String prediction;
        if (predictedOutcome == DirkOddsSimulator.OUTCOME_AWAY) {
            prediction = selectedScenario.activeCallText(predictedOutcome);
            tintPredictionButton(awayButton, true, selectedScenario.awayColor);
            tintPredictionButton(drawButton, false, 0xFFB9A44C);
            tintPredictionButton(homeButton, false, selectedScenario.homeColor);
        } else if (predictedOutcome == DirkOddsSimulator.OUTCOME_DRAW) {
            prediction = selectedScenario.activeCallText(predictedOutcome);
            tintPredictionButton(awayButton, false, selectedScenario.awayColor);
            tintPredictionButton(drawButton, true, 0xFFB9A44C);
            tintPredictionButton(homeButton, false, selectedScenario.homeColor);
        } else {
            prediction = selectedScenario.activeCallText(predictedOutcome);
            tintPredictionButton(awayButton, false, selectedScenario.awayColor);
            tintPredictionButton(drawButton, false, 0xFFB9A44C);
            tintPredictionButton(homeButton, true, selectedScenario.homeColor);
        }
        predictionView.setText(selectedScenario.isQuickthings()
                ? "Active call: " + prediction + ". Use Rift, Sync, and Strike control during playback to route the bream through portals, keep entropy below consensus, and sink the Choice Well."
                : "Active call: " + prediction + ". Use pulse, shape, and reflex during playback to test whether the read survives live pressure.");
        predictionView.animate()
            .alpha(0.72f)
            .setDuration(0)
            .withEndAction(() -> predictionView.animate().alpha(1f).setDuration(180).start())
            .start();
    }

    private SpannableString buildBrandTitle() {
        String text = "DIRK//ODDS\nSIGNAL ARENA";
        SpannableString styled = new SpannableString(text);
        styled.setSpan(new ForegroundColorSpan(Color.rgb(96, 230, 255)), 0, 4, Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);
        styled.setSpan(new ForegroundColorSpan(Color.rgb(246, 248, 255)), 4, 6, Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);
        styled.setSpan(new ForegroundColorSpan(Color.rgb(255, 122, 186)), 6, 10, Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);
        styled.setSpan(new ForegroundColorSpan(Color.rgb(255, 212, 128)), 11, text.length(), Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);
        styled.setSpan(new StyleSpan(Typeface.BOLD), 0, text.length(), Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);
        return styled;
    }

    private LinearLayout buildHeroPanel() {
        LinearLayout panel = new LinearLayout(this);
        panel.setOrientation(LinearLayout.VERTICAL);
        panel.setPadding(dp(20), dp(20), dp(20), dp(20));
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT);
        params.bottomMargin = dp(14);
        panel.setLayoutParams(params);
        GradientDrawable background = new GradientDrawable(
                GradientDrawable.Orientation.TL_BR,
                new int[] {Color.rgb(7, 12, 28), Color.rgb(18, 16, 42), Color.rgb(12, 29, 37)});
        background.setCornerRadius(dp(26));
            background.setStroke(dp(1), Color.argb(220, 120, 222, 255));
        panel.setBackground(background);
        return panel;
    }

    private TextView buildHeroChip(String label, int textColor, int fillColor) {
        TextView chip = new TextView(this);
        chip.setText(label);
        chip.setTextColor(textColor);
        chip.setTextSize(TypedValue.COMPLEX_UNIT_SP, 11);
        chip.setTypeface(Typeface.create("sans-serif-medium", Typeface.BOLD));
        chip.setPadding(dp(10), dp(6), dp(10), dp(6));
        GradientDrawable background = new GradientDrawable();
        background.setColor(fillColor);
        background.setCornerRadius(dp(999));
        background.setStroke(dp(1), Color.argb(180, Color.red(textColor), Color.green(textColor), Color.blue(textColor)));
        chip.setBackground(background);
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.WRAP_CONTENT,
                ViewGroup.LayoutParams.WRAP_CONTENT);
        params.rightMargin = dp(8);
        chip.setLayoutParams(params);
        return chip;
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
            case "multisport":
                return "◈";
            case "quickthings":
                return "◉";
            case "hockey":
                return "⌁";
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
