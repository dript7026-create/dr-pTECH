package com.urbden.game;

import android.content.Context;
import android.os.Build;
import android.os.VibrationEffect;
import android.os.Vibrator;
import android.os.VibratorManager;
import android.view.HapticFeedbackConstants;
import android.view.View;

final class QuickthingsHaptics {
    private static final long[] PATTERN_SEED = {0L, 12L};
    private static final long[] PATTERN_WINDUP = {0L, 18L, 20L, 12L};
    private static final long[] PATTERN_SUSPEND = {0L, 26L};
    private static final long[] PATTERN_RUPTURE = {0L, 12L, 26L, 28L};
    private static final long[] PATTERN_COLLAPSE = {0L, 38L};
    private static final long[] PATTERN_ECHO = {0L, 10L, 14L, 10L};
    private static final long[] PATTERN_WINDOW_OPEN = {0L, 18L, 28L, 18L};
    private static final long[] PATTERN_WINDOW_CLOSE = {0L, 14L};
    private static final long[] PATTERN_STAGE_SHIFT = {0L, 14L, 16L, 18L};
    private static final long[] PATTERN_ROUND_CLEAR = {0L, 22L, 28L, 24L, 36L, 32L};
    private static final long[] PATTERN_RUN_STABLE = {0L, 26L, 22L, 24L, 20L, 42L};
    private static final long[] PATTERN_RUN_BREAK = {0L, 20L, 18L, 16L, 20L, 12L};

    private final Vibrator vibrator;

    private boolean active;
    private boolean hasState;
    private boolean lastFinished;
    private boolean lastQteActive;
    private int lastCourseStage;
    private int lastRoundIndex;
    private int lastShotsTaken;
    private String lastShotPhase = "";

    QuickthingsHaptics(Context context) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            VibratorManager manager = (VibratorManager) context.getSystemService(Context.VIBRATOR_MANAGER_SERVICE);
            vibrator = manager != null ? manager.getDefaultVibrator() : null;
        } else {
            vibrator = (Vibrator) context.getSystemService(Context.VIBRATOR_SERVICE);
        }
    }

    void start() {
        active = true;
    }

    void stop() {
        active = false;
        cancel();
        hasState = false;
        lastFinished = false;
        lastShotPhase = "";
    }

    void updateState(DirkOddsMatchState state) {
        if (!active || state == null) {
            return;
        }
        if (!hasState) {
            hasState = true;
            lastFinished = state.finished;
            lastQteActive = state.qteActive;
            lastCourseStage = state.courseStage;
            lastRoundIndex = state.roundIndex;
            lastShotsTaken = state.shotsTaken;
            lastShotPhase = state.shotPhase;
            return;
        }

        if (state.finished && !lastFinished) {
            vibratePattern(state.predictionCorrect ? PATTERN_RUN_STABLE : PATTERN_RUN_BREAK);
        }

        if (state.roundIndex > lastRoundIndex) {
            vibratePattern(PATTERN_ROUND_CLEAR);
        } else if (state.courseStage != lastCourseStage) {
            vibratePattern(PATTERN_STAGE_SHIFT);
        } else if (state.shotsTaken > lastShotsTaken || !state.shotPhase.equals(lastShotPhase)) {
            vibrateForPhase(state.shotPhase);
        }

        if (state.qteActive && !lastQteActive) {
            vibratePattern(PATTERN_WINDOW_OPEN);
        } else if (!state.qteActive && lastQteActive) {
            vibratePattern(PATTERN_WINDOW_CLOSE);
        }

        lastFinished = state.finished;
        lastQteActive = state.qteActive;
        lastCourseStage = state.courseStage;
        lastRoundIndex = state.roundIndex;
        lastShotsTaken = state.shotsTaken;
        lastShotPhase = state.shotPhase;
    }

    void performTapFeedback(View view, boolean emphatic) {
        if (view == null) {
            return;
        }
        view.performHapticFeedback(emphatic
                ? HapticFeedbackConstants.LONG_PRESS
                : HapticFeedbackConstants.VIRTUAL_KEY);
        if (emphatic) {
            vibratePattern(PATTERN_RUPTURE);
        }
    }

    private void vibrateForPhase(String shotPhase) {
        switch (shotPhase) {
            case "SEED":
                vibratePattern(PATTERN_SEED);
                break;
            case "WINDUP":
                vibratePattern(PATTERN_WINDUP);
                break;
            case "SUSPEND":
                vibratePattern(PATTERN_SUSPEND);
                break;
            case "RUPTURE":
                vibratePattern(PATTERN_RUPTURE);
                break;
            case "COLLAPSE":
                vibratePattern(PATTERN_COLLAPSE);
                break;
            case "ECHO":
                vibratePattern(PATTERN_ECHO);
                break;
            default:
                break;
        }
    }

    private void vibratePattern(long[] timings) {
        if (!active || vibrator == null || !vibrator.hasVibrator()) {
            return;
        }
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            int[] amplitudes = new int[timings.length];
            for (int i = 0; i < amplitudes.length; i++) {
                amplitudes[i] = i == 0 ? 0 : Math.min(255, 110 + i * 26);
            }
            vibrator.vibrate(VibrationEffect.createWaveform(timings, amplitudes, -1));
        } else {
            vibrator.vibrate(timings, -1);
        }
    }

    private void cancel() {
        if (vibrator != null) {
            vibrator.cancel();
        }
    }
}