package com.urbden.game;

import java.util.Locale;
import java.util.Random;

public final class DirkOddsSimulator {
    public static final int OUTCOME_AWAY = 0;
    public static final int OUTCOME_DRAW = 1;
    public static final int OUTCOME_HOME = 2;

    private static final String[] QUICKTHINGS_CLUBS = {
            "Flux Iron 4", "Rift Iron 7", "Mass Iron 5", "Vector Iron 8", "Driver 9", "Putter 6"
    };
    private static final String[] QUICKTHINGS_INTENTS = {
            "Drive", "Pierce", "Arc", "Fold", "Drift", "Sink"
    };
    private static final String[] QUICKTHINGS_STAGES = {
            "Dust", "Rock", "Moon", "Planet", "Ring", "Starwell"
    };
        private static final String[] QUICKTHINGS_SHOT_PHASES = {
            "SEED", "WINDUP", "SUSPEND", "RUPTURE", "COLLAPSE", "ECHO"
        };

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

    private float quickthingsConsensus;
    private float quickthingsEntropy;
    private float quickthingsRemainingVacuum;
    private float quickthingsSinkMargin;
    private float quickthingsBosonSync;
    private float quickthingsCardCharge;
    private int quickthingsPortalCount;
    private int quickthingsCourseStage;
    private int quickthingsRoundIndex;
    private int quickthingsShotsTaken;
    private String quickthingsActiveClub;
    private String quickthingsActiveIntent;
    private String quickthingsSyncLabel;
    private String quickthingsShotPhase;
    private float quickthingsShotPhaseProgress;
    private float quickthingsShotWindowStartSeconds;
    private float quickthingsShotWindowDurationSeconds;

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

        if (scenario.isQuickthings()) {
            DirkOddsScenario.QuickthingsProfile profile = scenario.quickthings;
            this.quickthingsConsensus = 0f;
            this.quickthingsEntropy = 1.5f;
            this.quickthingsRemainingVacuum = profile.vacuumLength;
            this.quickthingsSinkMargin = -profile.choiceWellRadius;
            this.quickthingsBosonSync = 0.46f;
            this.quickthingsCardCharge = 0.36f;
            this.quickthingsPortalCount = 1;
            this.quickthingsCourseStage = 0;
            this.quickthingsRoundIndex = 1;
            this.quickthingsShotsTaken = 0;
            this.quickthingsActiveClub = QUICKTHINGS_CLUBS[0];
            this.quickthingsActiveIntent = QUICKTHINGS_INTENTS[4];
            this.quickthingsSyncLabel = "SYNC IDLE";
            this.quickthingsShotPhase = QUICKTHINGS_SHOT_PHASES[0];
            this.quickthingsShotPhaseProgress = 0f;
            this.quickthingsShotWindowStartSeconds = 0f;
            this.quickthingsShotWindowDurationSeconds = 2.2f;
            this.prompt = "Seed the black hole, line up the first club, and stabilize the bream before the cosmocourse hardens.";
            this.eventLabel = "Black hole seeding live at " + scenario.venue + ".";
            this.nextEventSeconds = 2.2f;
            this.nextQteSeconds = 3.1f;
        }
    }

    public void tick(float deltaSeconds) {
        if (finished) {
            return;
        }
        if (scenario.isQuickthings()) {
            tickQuickthings(deltaSeconds);
        } else {
            tickMatch(deltaSeconds);
        }
    }

    public void pulsePrediction() {
        if (finished) {
            return;
        }
        if (scenario.isQuickthings()) {
            applyQuickthingsPulse();
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
        if (scenario.isQuickthings()) {
            applyQuickthingsShape();
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
        if (scenario.isQuickthings()) {
            applyQuickthingsReflex();
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
        if (scenario.isQuickthings()) {
            boolean predictionHeld = finished && quickthingsConsensus >= quickthingsEntropy;
            return new DirkOddsMatchState(
                    scenario,
                    quickthingsClockLabel(),
                    prompt,
                    eventLabel,
                    scenario.activeCallText(predictedOutcome),
                    predictedOutcome,
                    quickthingsRoundIndex - 1,
                    Math.round(quickthingsEntropy),
                    clamp(elapsedSeconds / totalSeconds, 0f, 1f),
                    clamp(quickthingsCardCharge, 0f, 1f),
                    clamp((quickthingsConsensus + 12f) / 24f, 0f, 1f),
                    clamp(quickthingsBosonSync, 0f, 1f),
                    clamp(quickthingsEntropy / 18f, 0f, 1f),
                    scenario.probabilityForOutcome(predictedOutcome),
                    focusX,
                    focusZ,
                    qteActive,
                    finished,
                    predictionHeld,
                    clamp((quickthingsConsensus + 12f) / 24f, 0f, 1f),
                    clamp(quickthingsEntropy / 18f, 0f, 1f),
                    clamp(quickthingsRemainingVacuum / Math.max(1f, scenario.quickthings.vacuumLength), 0f, 1f),
                    clamp((quickthingsSinkMargin + 6f) / 12f, 0f, 1f),
                    clamp(quickthingsBosonSync, 0f, 1f),
                    clamp(quickthingsCardCharge, 0f, 1f),
                    quickthingsPortalCount,
                    quickthingsCourseStage,
                    quickthingsRoundIndex,
                    scenario.quickthings.rounds,
                    quickthingsShotsTaken,
                    quickthingsActiveClub,
                    quickthingsActiveIntent,
                    quickthingsSyncLabel,
                    QUICKTHINGS_STAGES[quickthingsCourseStage],
                    quickthingsShotPhase,
                    quickthingsShotPhaseProgress);
        }
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
                predictionCorrect(),
                control,
                pressure,
                0f,
                0.5f,
                reflex,
                clamp(Math.abs(momentum), 0f, 1f),
                0,
                0,
                0,
                0,
                0,
                "",
                "",
                "",
                "",
                "FLOW",
                stateProgress(elapsedSeconds, totalSeconds));
    }

    private void tickMatch(float deltaSeconds) {
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

    private void tickQuickthings(float deltaSeconds) {
        DirkOddsScenario.QuickthingsProfile profile = scenario.quickthings;
        elapsedSeconds = Math.min(totalSeconds, elapsedSeconds + deltaSeconds);
        pulseBias *= 0.9f;
        shapeBias *= 0.92f;

        quickthingsCardCharge = clamp(quickthingsCardCharge * 0.985f + scenario.tempo * 0.012f + Math.abs(pulseBias) * 0.03f + shapeBias * 0.02f, 0f, 1f);
        quickthingsBosonSync = clamp(quickthingsBosonSync * 0.988f + shapeBias * 0.018f - quickthingsEntropy * 0.0018f + randomRange(-0.02f, 0.02f), 0f, 1f);
        control = clamp(control * 0.99f + 0.01f + shapeBias * 0.01f, 0f, 1f);
        reflex = clamp(reflex * 0.994f + 0.004f - (qteActive ? 0.003f : 0f), 0f, 1f);
        pressure = clamp(0.24f + quickthingsPortalCount * 0.14f + quickthingsEntropy * 0.032f + quickthingsCourseStage * 0.08f, 0f, 1f);

        float orbit = elapsedSeconds * 0.55f + quickthingsShotsTaken * 0.4f;
        focusX = (float) (Math.sin(orbit) * (1.2f + quickthingsCardCharge * 1.8f));
        focusZ = (float) (Math.cos(orbit * 0.8f) * (0.9f + quickthingsBosonSync * 1.5f));
        updateQuickthingsShotPhase();

        if (qteActive) {
            qteRemaining -= deltaSeconds;
            if (qteRemaining <= 0f) {
                qteActive = false;
                quickthingsSyncLabel = "FORKED PATH";
                quickthingsEntropy = clamp(quickthingsEntropy + 0.6f, 0f, 18f);
                prompt = phasePromptForCurrentShot("The sync gate slipped. The next shot will fork unless you re-stabilize.");
            }
        } else if (elapsedSeconds >= nextQteSeconds && !finished) {
            qteActive = true;
            qteRemaining = 1.1f + random.nextFloat() * 0.55f;
            nextQteSeconds += 3.8f + random.nextFloat() * 1.8f;
            prompt = "Boson sync window open. Hit reflex to hold the chosen branch before the portals shear.";
            quickthingsSyncLabel = "SYNC WINDOW";
        }

        if (elapsedSeconds >= nextEventSeconds && !finished) {
            resolveQuickthingsShot(profile);
            nextEventSeconds += 2.6f + random.nextFloat() * 1.6f;
        }

        if (quickthingsRoundIndex > profile.rounds) {
            finished = true;
            qteActive = false;
            prompt = quickthingsFinalPrompt();
            eventLabel = "Choice Well audit complete.";
        }
    }

    private void applyQuickthingsPulse() {
        if ("WINDUP".equals(quickthingsShotPhase)) {
            pulseBias += 0.72f;
            quickthingsCardCharge = clamp(quickthingsCardCharge + 0.18f, 0f, 1f);
            quickthingsSinkMargin += predictedOutcome == OUTCOME_HOME ? 1.2f : 0.35f;
            quickthingsEntropy = Math.max(0f, quickthingsEntropy - 0.15f);
            prompt = "Pulse caught the windup. Time compresses behind the club and the shot gains interior weight.";
            return;
        }
        if ("SUSPEND".equals(quickthingsShotPhase)) {
            shapeBias += 0.18f;
            quickthingsConsensus = clamp(quickthingsConsensus + 0.9f, -12f, 12f);
            quickthingsBosonSync = clamp(quickthingsBosonSync + 0.08f, 0f, 1f);
            prompt = "Pulse inside suspension thickens the time pocket without tearing it open.";
            return;
        }
        if ("RUPTURE".equals(quickthingsShotPhase)) {
            pulseBias += 0.54f;
            quickthingsPortalCount = Math.min(3, quickthingsPortalCount + 1);
            quickthingsEntropy = clamp(quickthingsEntropy + 0.4f, 0f, 18f);
            prompt = "Pulse during rupture forces the portals wider. It is powerful, but the course pays for it.";
            return;
        }
        quickthingsCardCharge = clamp(quickthingsCardCharge + 0.12f, 0f, 1f);
        quickthingsEntropy = Math.max(0f, quickthingsEntropy - 0.2f);
        prompt = "Card pressure committed. The cosmocourse is reacting to your chosen lane.";
    }

    private void applyQuickthingsShape() {
        if ("SEED".equals(quickthingsShotPhase) || "WINDUP".equals(quickthingsShotPhase)) {
            shapeBias += 0.42f;
            quickthingsConsensus = clamp(quickthingsConsensus + 1.2f, -12f, 12f);
            quickthingsBosonSync = clamp(quickthingsBosonSync + 0.1f, 0f, 1f);
            pressure = clamp(pressure - 0.1f, 0f, 1f);
            prompt = "Shape locked early. The shot is now organizing itself before the first real tear appears.";
            return;
        }
        if ("COLLAPSE".equals(quickthingsShotPhase)) {
            quickthingsSinkMargin = clamp(quickthingsSinkMargin + 1.0f, -6f, 6f);
            quickthingsConsensus = clamp(quickthingsConsensus + 0.7f, -12f, 12f);
            prompt = "Shape applied during collapse. The shot is hardening into cleaner terrain and a better landing line.";
            return;
        }
        shapeBias += predictedOutcome == OUTCOME_DRAW ? 0.55f : 0.34f;
        quickthingsConsensus = clamp(quickthingsConsensus + 1.0f, -12f, 12f);
        quickthingsBosonSync = clamp(quickthingsBosonSync + 0.09f, 0f, 1f);
        pressure = clamp(pressure - 0.08f, 0f, 1f);
        prompt = "Geometry tightened. Consensus is holding and the portal lattice is easier to read.";
    }

    private void applyQuickthingsReflex() {
        if (qteActive) {
            qteActive = false;
            reflex = clamp(reflex + 0.16f, 0f, 1f);
            if ("SUSPEND".equals(quickthingsShotPhase)) {
                quickthingsBosonSync = clamp(quickthingsBosonSync + 0.24f, 0f, 1f);
                quickthingsConsensus = clamp(quickthingsConsensus + 1.8f, -12f, 12f);
                quickthingsEntropy = Math.max(0f, quickthingsEntropy - 0.7f);
                quickthingsSyncLabel = "TIMELOCK SYNC";
                prompt = "Reflex landed at suspension. The branch locks and the shot seems to stand still around you.";
                return;
            }
            if ("RUPTURE".equals(quickthingsShotPhase)) {
                quickthingsBosonSync = clamp(quickthingsBosonSync + 0.12f, 0f, 1f);
                quickthingsPortalCount = Math.max(1, quickthingsPortalCount - 1);
                quickthingsEntropy = Math.max(0f, quickthingsEntropy - 0.35f);
                quickthingsSyncLabel = "SHEAR CUT";
                prompt = "Reflex hit inside rupture. One bad branch was cut away before it could scar the course.";
                return;
            }
            quickthingsBosonSync = clamp(quickthingsBosonSync + 0.18f, 0f, 1f);
            quickthingsConsensus = clamp(quickthingsConsensus + 1.4f, -12f, 12f);
            quickthingsEntropy = Math.max(0f, quickthingsEntropy - 0.5f);
            quickthingsSyncLabel = "RESONANT SYNC";
            prompt = "Clean sync read. The bream locks onto the parallel branch with minimal shear.";
            return;
        }
        quickthingsEntropy = clamp(quickthingsEntropy + 0.45f, 0f, 18f);
        if ("COLLAPSE".equals(quickthingsShotPhase)) {
            quickthingsSinkMargin = clamp(quickthingsSinkMargin - 0.8f, -6f, 6f);
            prompt = "Late reflex during collapse jolted the landing line. The shot lost some of its final certainty.";
        } else {
            prompt = "No sync window was open. Vacuum noise has roughened the next shot.";
        }
        quickthingsSyncLabel = "EARLY TRIGGER";
    }

    private void updateQuickthingsShotPhase() {
        float phaseProgress = stateProgress(elapsedSeconds - quickthingsShotWindowStartSeconds, quickthingsShotWindowDurationSeconds);
        quickthingsShotPhaseProgress = phaseProgress;
        if (phaseProgress < 0.12f) {
            quickthingsShotPhase = QUICKTHINGS_SHOT_PHASES[0];
        } else if (phaseProgress < 0.3f) {
            quickthingsShotPhase = QUICKTHINGS_SHOT_PHASES[1];
        } else if (phaseProgress < 0.52f) {
            quickthingsShotPhase = QUICKTHINGS_SHOT_PHASES[2];
        } else if (phaseProgress < 0.73f) {
            quickthingsShotPhase = QUICKTHINGS_SHOT_PHASES[3];
        } else if (phaseProgress < 0.9f) {
            quickthingsShotPhase = QUICKTHINGS_SHOT_PHASES[4];
        } else {
            quickthingsShotPhase = QUICKTHINGS_SHOT_PHASES[5];
        }

        if (!qteActive && !finished) {
            prompt = phasePromptForCurrentShot(prompt);
        }
    }

    private void resolveQuickthingsShot(DirkOddsScenario.QuickthingsProfile profile) {
        quickthingsShotsTaken += 1;
        quickthingsShotWindowStartSeconds = elapsedSeconds;
        quickthingsShotWindowDurationSeconds = 2.3f + random.nextFloat() * 1.1f;
        quickthingsShotPhase = QUICKTHINGS_SHOT_PHASES[1];
        quickthingsShotPhaseProgress = 0.16f;

        int intentIndex = (quickthingsShotsTaken + predictedOutcome + random.nextInt(QUICKTHINGS_INTENTS.length)) % QUICKTHINGS_INTENTS.length;
        quickthingsActiveIntent = QUICKTHINGS_INTENTS[intentIndex];
        int clubOffset = predictedOutcome == OUTCOME_AWAY ? 1 : predictedOutcome == OUTCOME_DRAW ? 3 : 5;
        quickthingsActiveClub = QUICKTHINGS_CLUBS[(clubOffset + quickthingsShotsTaken) % QUICKTHINGS_CLUBS.length];

        float portalPressure = predictedOutcome == OUTCOME_AWAY ? 0.9f : predictedOutcome == OUTCOME_DRAW ? 0.55f : 0.35f;
        int portalBase = 1 + (int) Math.floor((quickthingsCardCharge + portalPressure + random.nextFloat() * 0.6f) * 1.4f);
        quickthingsPortalCount = Math.max(1, Math.min(3, portalBase));

        float higgsDelta = Math.abs((3f + quickthingsPortalCount + quickthingsCardCharge * 4f) - profile.higgsDensity);
        float syncBonus = quickthingsBosonSync * 3.1f + (predictedOutcome == OUTCOME_DRAW ? 0.8f : 0f);
        float distance = 2.4f + quickthingsCardCharge * 5.8f + quickthingsPortalCount * 1.35f + syncBonus - higgsDelta * 0.75f;
        if (predictedOutcome == OUTCOME_HOME) {
            distance += Math.max(0f, quickthingsSinkMargin) * 0.15f;
        } else if (predictedOutcome == OUTCOME_AWAY) {
            distance += 0.9f;
        }

        quickthingsRemainingVacuum = Math.max(0f, quickthingsRemainingVacuum - Math.max(1.4f, distance));

        float consensusGain = quickthingsBosonSync * 1.6f + (predictedOutcome == OUTCOME_DRAW ? 0.7f : 0.35f) - higgsDelta * 0.12f;
        float entropyGain = Math.max(0.15f, quickthingsPortalCount * 0.32f + higgsDelta * 0.18f - quickthingsBosonSync * 0.65f);
        if (predictedOutcome == OUTCOME_AWAY) {
            entropyGain += 0.2f;
        }
        if (predictedOutcome == OUTCOME_HOME) {
            consensusGain += 0.25f;
        }

        quickthingsConsensus = clamp(quickthingsConsensus + consensusGain, -12f, 12f);
        quickthingsEntropy = clamp(quickthingsEntropy + entropyGain, 0f, 18f);
        quickthingsSinkMargin = clamp(quickthingsConsensus - quickthingsEntropy * 0.42f + control * 4f - profile.choiceWellRadius, -6f, 6f);
        quickthingsCourseStage = Math.min(5, quickthingsShotsTaken / 2);

        if (quickthingsBosonSync >= 0.82f) {
            quickthingsSyncLabel = "PERFECT SYNC";
        } else if (quickthingsBosonSync >= 0.64f) {
            quickthingsSyncLabel = "RESONANT SYNC";
        } else if (quickthingsBosonSync >= 0.48f) {
            quickthingsSyncLabel = "STABLE SYNC";
        } else if (quickthingsBosonSync >= 0.32f) {
            quickthingsSyncLabel = "DECOHERENCE";
        } else {
            quickthingsSyncLabel = "VACUUM RUPTURE";
        }

        eventLabel = String.format(
                Locale.US,
                "%s / %s // %s // %d portal%s // stage %s",
                quickthingsActiveClub,
                quickthingsActiveIntent,
                quickthingsSyncLabel,
                quickthingsPortalCount,
                quickthingsPortalCount == 1 ? "" : "s",
                QUICKTHINGS_STAGES[quickthingsCourseStage]);

        if (quickthingsRemainingVacuum <= 0f) {
            if (quickthingsSinkMargin >= 0f) {
                homeScore += 1;
                quickthingsRoundIndex += 1;
                quickthingsRemainingVacuum = profile.vacuumLength + Math.min(10f, quickthingsRoundIndex * 0.7f);
                quickthingsShotsTaken = 0;
                quickthingsCourseStage = 0;
                quickthingsShotWindowStartSeconds = elapsedSeconds;
                quickthingsShotWindowDurationSeconds = 2.1f;
                quickthingsShotPhase = QUICKTHINGS_SHOT_PHASES[0];
                quickthingsShotPhaseProgress = 0f;
                quickthingsEntropy = Math.max(0f, quickthingsEntropy - 1.2f);
                quickthingsConsensus = clamp(quickthingsConsensus + 1.4f, -12f, 12f);
                eventLabel = String.format(Locale.US, "Choice Well sunk cleanly. Round %d opens through fresh dust geometry.", quickthingsRoundIndex);
                prompt = "Hole collapsed into stable object-space. Reset your angle before the next black-hole seed.";
            } else {
                awayScore += 1;
                quickthingsEntropy = clamp(quickthingsEntropy + 0.8f, 0f, 18f);
                quickthingsRemainingVacuum = profile.choiceWellRadius + 2f;
                eventLabel = "Sink attempt rejected. The bream ricocheted off the Choice Well lip.";
                prompt = "You reached the Well without enough margin. Build one cleaner sync chain before the next sink.";
            }
        } else {
            prompt = phasePromptForCurrentShot(String.format(
                    Locale.US,
                    "Remaining vacuum %.1f quanta. Keep entropy below consensus and prepare the next card release.",
                    quickthingsRemainingVacuum));
        }
    }

    private String phasePromptForCurrentShot(String fallback) {
        switch (quickthingsShotPhase) {
            case "SEED":
                return "Black-hole seed forming. The shot has not begun yet; time is gathering around the club face.";
            case "WINDUP":
                return "Windup phase. The club is choosing an angle and the bream is pulling time inward before release.";
            case "SUSPEND":
                return "Suspension phase. The shot is hanging inside a pocket of slowed consensus where the branch is still editable.";
            case "RUPTURE":
                return "Rupture phase. Portal edges are cutting the vacuum and the shot is deciding what kind of reality it wants.";
            case "COLLAPSE":
                return "Collapse phase. The shot is turning into object-space; every gain or mistake becomes terrain now.";
            case "ECHO":
                return fallback + " The last shot is still echoing through the course shell.";
            default:
                return fallback;
        }
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
            case "multisport":
                return "Reflex cue: mixed-sport seam opening. Tap now to ride the football break, basketball snap, baseball release, and hockey lane in one continuous read.";
            case "hockey":
                return "Reflex cue: lane seam opening off the boards. Tap now to turn the pressure read into a clean ice break.";
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

    private String quickthingsFinalPrompt() {
        boolean held = quickthingsConsensus >= quickthingsEntropy;
        return (held
                ? "The codex held. Consensus beat entropy across the cosmocourse run."
                : "Entropy overtook consensus before the final sink chain stabilized.")
                + " Review portal count, sync quality, and card timing before the next attempt.";
    }

    private String clockLabel() {
        float progress = clamp(elapsedSeconds / totalSeconds, 0f, 1f);
        switch (scenario.sport) {
            case "multisport": {
                String segment;
                if (progress < 0.25f) {
                    segment = "football pressure";
                } else if (progress < 0.5f) {
                    segment = "basketball snap";
                } else if (progress < 0.75f) {
                    segment = "baseball read";
                } else {
                    segment = "hockey lane";
                }
                int minute = Math.min(99, Math.max(1, Math.round(progress * 99f)));
                return String.format(Locale.US, "%d' hybrid clock | %s", minute, segment);
            }
            case "hockey": {
                int period = Math.min(3, (int) (progress * 3f) + 1);
                float periodProgress = (progress * 3f) - (period - 1);
                int secondsLeft = Math.max(0, (int) ((1f - Math.min(1f, periodProgress)) * 240f));
                return String.format(Locale.US, "P%d %d:%02d | %s", period, secondsLeft / 60, secondsLeft % 60, pressure > 0.58f ? "late shift" : "line flow");
            }
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

    private String quickthingsClockLabel() {
        return String.format(Locale.US, "Round %d/%d | Shot %d", quickthingsRoundIndex, scenario.quickthings.rounds, Math.max(1, quickthingsShotsTaken));
    }

    private float durationForSport(String sport) {
        switch (sport) {
            case "multisport":
                return 126f;
            case "hockey":
                return 114f;
            case "basketball":
                return 108f;
            case "baseball":
                return 112f;
            case "quickthings":
                return 96f;
            default:
                return 120f;
        }
    }

    private float positive(float value) {
        return Math.max(0.01f, value);
    }

    private float randomRange(float minValue, float maxValue) {
        return minValue + random.nextFloat() * (maxValue - minValue);
    }

    private float stateProgress(float elapsed, float duration) {
        if (duration <= 0f) {
            return 1f;
        }
        return clamp(elapsed / duration, 0f, 1f);
    }

    private float clamp(float value, float minValue, float maxValue) {
        return Math.max(minValue, Math.min(maxValue, value));
    }
}