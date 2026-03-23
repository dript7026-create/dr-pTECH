package com.urbden.game;

public final class DirkOddsMatchState {
    public final DirkOddsScenario scenario;
    public final String clockLabel;
    public final String prompt;
    public final String eventLabel;
    public final String predictedLabel;
    public final int predictedOutcome;
    public final int homeScore;
    public final int awayScore;
    public final float progress;
    public final float momentum;
    public final float control;
    public final float reflex;
    public final float pressure;
    public final float predictionEdge;
    public final float focusX;
    public final float focusZ;
    public final boolean qteActive;
    public final boolean finished;
    public final boolean predictionCorrect;

    DirkOddsMatchState(
            DirkOddsScenario scenario,
            String clockLabel,
            String prompt,
            String eventLabel,
            String predictedLabel,
            int predictedOutcome,
            int homeScore,
            int awayScore,
            float progress,
            float momentum,
            float control,
            float reflex,
            float pressure,
            float predictionEdge,
            float focusX,
            float focusZ,
            boolean qteActive,
            boolean finished,
            boolean predictionCorrect) {
        this.scenario = scenario;
        this.clockLabel = clockLabel;
        this.prompt = prompt;
        this.eventLabel = eventLabel;
        this.predictedLabel = predictedLabel;
        this.predictedOutcome = predictedOutcome;
        this.homeScore = homeScore;
        this.awayScore = awayScore;
        this.progress = progress;
        this.momentum = momentum;
        this.control = control;
        this.reflex = reflex;
        this.pressure = pressure;
        this.predictionEdge = predictionEdge;
        this.focusX = focusX;
        this.focusZ = focusZ;
        this.qteActive = qteActive;
        this.finished = finished;
        this.predictionCorrect = predictionCorrect;
    }
}