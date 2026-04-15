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
    public final float consensus;
    public final float entropy;
    public final float remainingVacuum;
    public final float sinkMargin;
    public final float bosonSync;
    public final float cardCharge;
    public final int portalCount;
    public final int courseStage;
    public final int roundIndex;
    public final int totalRounds;
    public final int shotsTaken;
    public final String activeClub;
    public final String activeIntent;
    public final String syncLabel;
    public final String courseLabel;
    public final String shotPhase;
    public final float shotPhaseProgress;

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
            boolean predictionCorrect,
            float consensus,
            float entropy,
            float remainingVacuum,
            float sinkMargin,
            float bosonSync,
            float cardCharge,
            int portalCount,
            int courseStage,
            int roundIndex,
            int totalRounds,
            int shotsTaken,
            String activeClub,
            String activeIntent,
            String syncLabel,
            String courseLabel,
            String shotPhase,
            float shotPhaseProgress) {
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
        this.consensus = consensus;
        this.entropy = entropy;
        this.remainingVacuum = remainingVacuum;
        this.sinkMargin = sinkMargin;
        this.bosonSync = bosonSync;
        this.cardCharge = cardCharge;
        this.portalCount = portalCount;
        this.courseStage = courseStage;
        this.roundIndex = roundIndex;
        this.totalRounds = totalRounds;
        this.shotsTaken = shotsTaken;
        this.activeClub = activeClub;
        this.activeIntent = activeIntent;
        this.syncLabel = syncLabel;
        this.courseLabel = courseLabel;
        this.shotPhase = shotPhase;
        this.shotPhaseProgress = shotPhaseProgress;
    }
}