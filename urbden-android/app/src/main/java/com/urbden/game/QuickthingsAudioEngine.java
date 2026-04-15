package com.urbden.game;

import android.media.AudioAttributes;
import android.media.AudioFormat;
import android.media.AudioTrack;
import android.os.Build;

final class QuickthingsAudioEngine {
    private static final int SAMPLE_RATE = 48000;
    private static final int CHANNELS = 2;
    private static final int FRAMES_PER_BUFFER = 960;
    private static final float LIMITER_THRESHOLD = 0.82f;
    private static final float MASTER_GAIN = 0.24f;

    private final Object stateLock = new Object();

    private AudioTrack audioTrack;
    private Thread audioThread;
    private volatile boolean running;
    private DirkOddsMatchState latestState;
    private double phaseA;
    private double phaseB;
    private double phaseC;
    private double phaseD;
    private double phaseE;
    private double phaseNoise;
    private double stereoPhase;
    private double busFollower;
    private double phaseProgressMemory;

    void start() {
        if (running) {
            return;
        }
        int minBuffer = AudioTrack.getMinBufferSize(
                SAMPLE_RATE,
                AudioFormat.CHANNEL_OUT_STEREO,
                AudioFormat.ENCODING_PCM_16BIT);
        int bufferSize = Math.max(minBuffer, FRAMES_PER_BUFFER * CHANNELS * 2 * 4);

        AudioAttributes attributes = new AudioAttributes.Builder()
                .setUsage(AudioAttributes.USAGE_GAME)
                .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION)
                .build();
        AudioFormat format = new AudioFormat.Builder()
                .setEncoding(AudioFormat.ENCODING_PCM_16BIT)
                .setSampleRate(SAMPLE_RATE)
                .setChannelMask(AudioFormat.CHANNEL_OUT_STEREO)
                .build();

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            audioTrack = new AudioTrack.Builder()
                    .setAudioAttributes(attributes)
                    .setAudioFormat(format)
                    .setTransferMode(AudioTrack.MODE_STREAM)
                    .setBufferSizeInBytes(bufferSize)
                    .build();
        } else {
            audioTrack = new AudioTrack(
                    attributes,
                    format,
                    bufferSize,
                    AudioTrack.MODE_STREAM,
                    AudioTrack.WRITE_BLOCKING);
        }

        running = true;
        audioTrack.play();
        audioThread = new Thread(this::renderLoop, "QuickthingsAudioEngine");
        audioThread.start();
    }

    void stop() {
        running = false;
        if (audioThread != null) {
            try {
                audioThread.join(600L);
            } catch (InterruptedException ignored) {
                Thread.currentThread().interrupt();
            }
            audioThread = null;
        }
        if (audioTrack != null) {
            try {
                audioTrack.pause();
                audioTrack.flush();
                audioTrack.release();
            } catch (IllegalStateException ignored) {
            }
            audioTrack = null;
        }
    }

    void updateState(DirkOddsMatchState state) {
        synchronized (stateLock) {
            latestState = state;
        }
    }

    private void renderLoop() {
        short[] pcm = new short[FRAMES_PER_BUFFER * CHANNELS];
        while (running && audioTrack != null) {
            DirkOddsMatchState state;
            synchronized (stateLock) {
                state = latestState;
            }
            renderBuffer(pcm, state);
            audioTrack.write(pcm, 0, pcm.length);
        }
    }

    private void renderBuffer(short[] pcm, DirkOddsMatchState state) {
        float consensus = state == null ? 0.45f : state.consensus;
        float entropy = state == null ? 0.2f : state.entropy;
        float bosonSync = state == null ? 0.45f : state.bosonSync;
        float pressure = state == null ? 0.35f : state.pressure;
        float cardCharge = state == null ? 0.42f : state.cardCharge;
        float phaseProgress = state == null ? 0f : state.shotPhaseProgress;
        boolean qteActive = state != null && state.qteActive;
        String shotPhase = state == null ? "SEED" : state.shotPhase;

        double subCarrierHz = 36.0 + consensus * 8.0;
        double harmonicHz = 72.0 + bosonSync * 34.0;
        double shimmerHz = 220.0 + entropy * 140.0;
        double presenceHz = 1480.0 + consensus * 540.0 + bosonSync * 210.0;
        double airHz = 3600.0 + entropy * 2200.0 + cardCharge * 700.0;
        double phaseMod = Math.sin(phaseProgress * Math.PI);
        double phaseMotion = Math.max(0.0, phaseProgress - phaseProgressMemory);
        double crispAccent = Math.min(1.0, phaseMotion * 28.0 + (qteActive ? 0.22 : 0.0));
        double broadcastDrive = 0.92 + pressure * 0.22 + crispAccent * 0.12;
        double stereoWidth = 0.18 + entropy * 0.08 + crispAccent * 0.1;

        if ("SUSPEND".equals(shotPhase)) {
            subCarrierHz *= 0.82;
            shimmerHz *= 0.65;
            presenceHz *= 0.92;
            airHz *= 0.84;
        } else if ("RUPTURE".equals(shotPhase)) {
            harmonicHz *= 1.08;
            shimmerHz *= 1.22;
            presenceHz *= 1.16;
            airHz *= 1.18;
            broadcastDrive += 0.08;
        } else if ("COLLAPSE".equals(shotPhase)) {
            subCarrierHz *= 0.92;
            harmonicHz *= 0.9;
            presenceHz *= 0.9;
            airHz *= 0.8;
            stereoWidth *= 0.72;
        } else if ("ECHO".equals(shotPhase)) {
            harmonicHz *= 0.96;
            shimmerHz *= 1.08;
            airHz *= 1.06;
        }

        double subStep = (Math.PI * 2.0 * subCarrierHz) / SAMPLE_RATE;
        double harmonicStep = (Math.PI * 2.0 * harmonicHz) / SAMPLE_RATE;
        double shimmerStep = (Math.PI * 2.0 * shimmerHz) / SAMPLE_RATE;
        double presenceStep = (Math.PI * 2.0 * presenceHz) / SAMPLE_RATE;
        double airStep = (Math.PI * 2.0 * airHz) / SAMPLE_RATE;
        double noiseStep = (Math.PI * 2.0 * (0.16 + entropy * 0.35)) / SAMPLE_RATE;
        double stereoStep = (Math.PI * 2.0 * (0.09 + bosonSync * 0.07)) / SAMPLE_RATE;

        for (int frame = 0; frame < FRAMES_PER_BUFFER; frame++) {
            phaseA += subStep;
            phaseB += harmonicStep;
            phaseC += shimmerStep;
            phaseD += presenceStep;
            phaseE += airStep;
            phaseNoise += noiseStep;
            stereoPhase += stereoStep;

            double sub = Math.sin(phaseA) * (0.28 + phaseMod * 0.08);
            double psychoBass = Math.sin(phaseA * 2.0) * 0.16 + Math.sin(phaseA * 3.0) * 0.11;
            double harmonic = Math.sin(phaseB) * (0.15 + bosonSync * 0.08);
            double shimmer = Math.sin(phaseC) * (0.04 + entropy * 0.05);
            double presence = (Math.sin(phaseD) + Math.sin(phaseD * 1.97) * 0.4) * (0.04 + consensus * 0.03 + crispAccent * 0.02);
            double air = (Math.sin(phaseE) * 0.45 + Math.sin(phaseE * 1.53) * 0.32 + Math.sin(phaseE * 2.11) * 0.23)
                    * (0.012 + entropy * 0.018 + crispAccent * 0.015);
            double noiseBed = (Math.sin(phaseNoise) * 0.5 + Math.sin(phaseNoise * 0.27) * 0.5) * (0.016 + entropy * 0.025);
            double transientClick = Math.sin(phaseD * 3.2) * crispAccent * (0.006 + cardCharge * 0.01);
            double widthSwing = Math.sin(stereoPhase) * stereoWidth;

            double left = sub + psychoBass + harmonic + shimmer + presence * (0.82 + widthSwing) + air * (0.7 + widthSwing) + noiseBed + transientClick;
            double right = sub + psychoBass - harmonic + shimmer + presence * (1.02 - widthSwing) + air * (1.16 - widthSwing) - noiseBed - transientClick * 0.72;

            double monoEnergy = (Math.abs(left) + Math.abs(right)) * 0.5;
            double followerRate = monoEnergy > busFollower ? 0.12 : 0.018;
            busFollower += (monoEnergy - busFollower) * followerRate;
            double busGain = 1.0 / (1.0 + Math.max(0.0, busFollower - 0.24) * 1.65);

            left = limited(left * MASTER_GAIN * busGain * broadcastDrive, LIMITER_THRESHOLD);
            right = limited(right * MASTER_GAIN * busGain * broadcastDrive, LIMITER_THRESHOLD);

            pcm[frame * 2] = (short) Math.round(left * 32767.0);
            pcm[frame * 2 + 1] = (short) Math.round(right * 32767.0);
        }

        phaseProgressMemory += (phaseProgress - phaseProgressMemory) * 0.38;
    }

    private double limited(double sample, double threshold) {
        double normalized = sample / Math.max(0.0001, threshold);
        double compressed = Math.tanh(normalized) * threshold;
        if (compressed > threshold) {
            return threshold;
        }
        if (compressed < -threshold) {
            return -threshold;
        }
        return compressed;
    }
}