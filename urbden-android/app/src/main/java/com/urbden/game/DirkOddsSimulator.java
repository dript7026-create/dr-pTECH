package com.urbden.game;

import java.util.Locale;
import java.util.Random;

public final class DirkOddsSimulator {
    public static final int OUTCOME_AWAY = 0;
    public static final int OUTCOME_DRAW = 1;
    public static final int OUTCOME_HOME = 2;

    private final DirkOddsScenario scenario;
    private final int predictedOutcome;
    private final Random random;
    private final float totalSeconds;

    private float elapsedSeconds;
    private float momentum;
    private float control;
    private float reflex;
    private float pressure;
    private float focusX;
    private float focusZ;
    private float nextEventSeconds;
    private float nextQteSeconds;
    private float qteRemaining;
    private float pulseBias;
    private float shapeBias;
    private boolean qteActive;
    private boolean finished;
    private int homeScore;
    private int awayScore;
    private String prompt;
    private String eventLabel;

    public DirkOddsSimulator(DirkOddsScenario scenario, int predictedOutcome) {
        this.scenario = scenario;
        this.predictedOutcome = predictedOutcome;
        this.random = new Random((scenario.id + ":" + predictedOutcome).hashCode());
        this.totalSeconds = durationForSport(scenario.sport);
        this.momentum = scenario.homeProbability - scenario.awayProbability;
        this.control = 0.54f;
        this.reflex = 0.5f;
        this.pressure = 0.4f;
        this.prompt = "Wait for the first pressure window, then coach your prediction through the live flow.";
        this.eventLabel = scenario.venue;
        this.nextEventSeconds = 5f;
        this.nextQteSeconds = 7f;
    }

    public void tick(float deltaSeconds) {
        if (finished) {
            return;
        }

        elapsedSeconds = Math.min(totalSeconds, elapsedSeconds + deltaSeconds);
        pulseBias *= 0.92f;
        shapeBias *= 0.91f;

        float baseLean = scenario.homeProbability - scenario.awayProbability;
        float noise = (random.nextFloat() - 0.5f) * 0.09f;
        momentum = clamp(momentum * 0.985f + baseLean * 0.018f + pulseBias * 0.042f + shapeBias * 0.016f + noise, -1f, 1f);
        control = clamp(control * 0.992f + 0.004f + shapeBias * 0.025f - pressure * 0.006f, 0f, 1f);
        reflex = clamp(reflex * 0.996f + 0.002f - (qteActive ? 0.004f : 0f), 0f, 1f);
        pressure = clamp(0.28f + Math.abs(momentum) * 0.42f + scenario.tempo * 0.16f + (random.nextFloat() - 0.5f) * 0.08f, 0f, 1f);
        focusX = (float) (Math.sin(elapsedSeconds * 0.55f) * 2.4f + momentum * 2.1f);
        focusZ = (float) (Math.cos(elapsedSeconds * 0.37f) * 1.35f);

        if (qteActive) {
            qteRemaining -= deltaSeconds;
            if (qteRemaining <= 0f) {
                qteActive = false;
                reflex = clamp(reflex - 0.08f, 0f, 1f);
                prompt = "Reflex window slipped. Re-center and look for the next subtle tell.";
            }
        } else if (elapsedSeconds >= nextQteSeconds && !finished) {
            qteActive = true;
            qteRemaining = 1.35f;
            nextQteSeconds += 10f - scenario.tempo * 3.5f + random.nextFloat() * 2.2f;
            prompt = cuePrompt();
        }

        if (elapsedSeconds >= nextEventSeconds && !finished) {
            resolveEvent();
            nextEventSeconds += 5.5f - scenario.tempo * 1.8f + random.nextFloat() * 4.0f;
        }

        if (elapsedSeconds >= totalSeconds) {
            finished = true;
            prompt = finalPrompt();
            eventLabel = "Final whistle";
        }
    }

    public void pulsePrediction() {
        if (finished) {
            return;
        }
        if (predictedOutcome == OUTCOME_HOME) {
            pulseBias += 0.78f;
        } else if (predictedOutcome == OUTCOME_AWAY) {
            pulseBias -= 0.78f;
        } else {
            shapeBias += 0.25f;
            momentum *= 0.84f;
        }
        control = clamp(control + 0.05f, 0f, 1f);
        prompt = "Prediction pulse committed. Keep the lane readable without over-forcing it.";
    }

    public void holdShape() {
        if (finished) {
            return;
        }
        shapeBias += predictedOutcome == OUTCOME_DRAW ? 0.55f : 0.3f;
        pressure = clamp(pressure - 0.08f, 0f, 1f);
        control = clamp(control + 0.08f, 0f, 1f);
        prompt = "Shape tightened. The simulator is favoring disciplined transitions over chaos.";
    }

    public void triggerReflex() {
        if (finished) {
            return;
        }
        if (qteActive) {
            qteActive = false;
            reflex = clamp(reflex + 0.18f, 0f, 1f);
            control = clamp(control + 0.07f, 0f, 1f);
            if (predictedOutcome == OUTCOME_HOME) {
                momentum = clamp(momentum + 0.14f, -1f, 1f);
            } else if (predictedOutcome == OUTCOME_AWAY) {
                momentum = clamp(momentum - 0.14f, -1f, 1f);
            } else {
                momentum *= 0.82f;
            }
            prompt = "Clean reflex read. Your abstract squad tracked the cue and stabilized the phase.";
        } else {
            reflex = clamp(reflex - 0.04f, 0f, 1f);
            prompt = "No live cue was open. Save the next reflex tap for a real pressure window.";
        }
    }

    public DirkOddsMatchState snapshot() {
        return new DirkOddsMatchState(
                scenario,
                clockLabel(),
                prompt,
                eventLabel,
                predictedLabel(),
                predictedOutcome,
                homeScore,
                awayScore,
                clamp(elapsedSeconds / totalSeconds, 0f, 1f),
                clamp((momentum + 1f) * 0.5f, 0f, 1f),
                control,
                reflex,
                pressure,
                scenario.probabilityForOutcome(predictedOutcome),
                focusX,
                focusZ,
                qteActive,
                finished,
                predictionCorrect());
    }

    private void resolveEvent() {
        float homeWeight = positive(scenario.homeProbability + momentum * 0.42f + control * 0.08f + reflex * 0.05f);
        float awayWeight = positive(scenario.awayProbability - momentum * 0.42f + (1f - control) * 0.05f + reflex * 0.04f);
        float drawWeight = positive(scenario.supportsDraw() ? scenario.drawProbability + (1f - pressure) * 0.08f - Math.abs(momentum) * 0.06f : 0f);
        float attackWeight = homeWeight + awayWeight + drawWeight;
        if (attackWeight <= 0f) {
            return;
        }

        float eventRoll = random.nextFloat();
        float scoreChance = 0.48f + pressure * 0.22f + scenario.tempo * 0.1f;
        if (eventRoll <= scoreChance) {
            float outcomeRoll = random.nextFloat() * attackWeight;
            if (outcomeRoll < homeWeight) {
                homeScore += 1;
                eventLabel = scenario.homeTeam + " convert an abstract lane break.";
            } else if (outcomeRoll < homeWeight + drawWeight) {
                eventLabel = "The phase compresses into a neutral scramble with no clean finish.";
            } else {
                awayScore += 1;
                eventLabel = scenario.awayTeam + " steal the rhythm and finish the sequence.";
            }
        } else {
            if (Math.abs(momentum) > 0.25f) {
                eventLabel = "Momentum swings through the center channel. The next cue will matter.";
            } else {
                eventLabel = "Compact spacing, low-ident detail, and a slow read phase keep the match balanced.";
            }
        }
    }

    private boolean predictionCorrect() {
        int actual = actualOutcome();
        return finished && actual == predictedOutcome;
    }

    private int actualOutcome() {
        if (homeScore > awayScore) {
            return OUTCOME_HOME;
        }
        if (awayScore > homeScore) {
            return OUTCOME_AWAY;
        }
        return OUTCOME_DRAW;
    }

    private String predictedLabel() {
        switch (predictedOutcome) {
            case OUTCOME_AWAY:
                return scenario.awayTeam + " edge";
            case OUTCOME_DRAW:
                return "balanced draw lane";
            default:
                return scenario.homeTeam + " edge";
        }
    }

    private String cuePrompt() {
        switch (scenario.sport) {
            case "basketball":
                return "Reflex cue: soft closeout window. Tap now to turn the prediction read into a clean drive lane.";
            case "baseball":
                return "Reflex cue: subtle release tell. Tap now to sharpen the abstract swing or pitch read.";
            default:
                return "Reflex cue: pressure pocket opening. Tap now to read the shape before the breakaway resolves.";
        }
    }

    private String finalPrompt() {
        String verdict = predictionCorrect() ? "Prediction held through the live test." : "Prediction drifted off the final result line.";
        return verdict + " Review the pressure, control, and reflex bars before rerunning the scenario.";
    }

    private String clockLabel() {
        float progress = clamp(elapsedSeconds / totalSeconds, 0f, 1f);
        switch (scenario.sport) {
            case "basketball": {
                int quarter = Math.min(4, (int) (progress * 4f) + 1);
                float quarterProgress = (progress * 4f) - (quarter - 1);
                int secondsLeft = Math.max(0, (int) ((1f - Math.min(1f, quarterProgress)) * 180f));
                return String.format(Locale.US, "Q%d %d:%02d", quarter, secondsLeft / 60, secondsLeft % 60);
            }
            case "baseball": {
                int inning = Math.min(9, (int) (progress * 9f) + 1);
                return String.format(Locale.US, "Inning %d | %s", inning, pressure > 0.55f ? "two-strike pressure" : "live count");
            }
            default: {
                int minute = Math.min(90, Math.max(1, Math.round(progress * 90f)));
                return String.format(Locale.US, "%d' synthetic clock", minute);
            }
        }
    }

    private float durationForSport(String sport) {
        switch (sport) {
            case "basketball":
                return 108f;
            case "baseball":
                return 112f;
            default:
                return 120f;
        }
    }

    private float positive(float value) {
        return Math.max(0.01f, value);
    }

    private float clamp(float value, float minValue, float maxValue) {
        return Math.max(minValue, Math.min(maxValue, value));
    }
}