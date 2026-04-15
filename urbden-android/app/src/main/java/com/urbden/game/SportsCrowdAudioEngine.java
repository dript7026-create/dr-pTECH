package com.urbden.game;

import android.media.AudioAttributes;
import android.media.AudioFormat;
import android.media.AudioTrack;
import android.os.Build;

final class SportsCrowdAudioEngine {
    private static final int SAMPLE_RATE = 48000;
    private static final int CHANNELS = 2;
    private static final int FRAMES_PER_BUFFER = 960;
    private static final float LIMITER_THRESHOLD = 0.82f;
    private static final float MASTER_GAIN = 0.21f;

    private final Object stateLock = new Object();

    private AudioTrack audioTrack;
    private Thread audioThread;
    private volatile boolean running;
    private DirkOddsMatchState latestState;
    private double crowdPhase;
    private double crowdNoisePhase;
    private double cheerPhaseA;
    private double cheerPhaseB;
    private double oyPhase;
    private double dismayPhase;
    private double stereoPhase;
    private double busFollower;
    private double pressureMemory = 0.34;
    private double momentumMemory = 0.5;
    private double cheerEnvelope;
    private double oyEnvelope;
    private double dismayEnvelope;
    private boolean qteLatch;
    private boolean finishedLatch;

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
        audioThread = new Thread(this::renderLoop, "SportsCrowdAudioEngine");
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
        float momentum = state == null ? 0.5f : state.momentum;
        float pressure = state == null ? 0.34f : state.pressure;
        float control = state == null ? 0.52f : state.control;
        float reflex = state == null ? 0.48f : state.reflex;
        float progress = state == null ? 0f : state.progress;
        boolean qteActive = state != null && state.qteActive;
        boolean finished = state != null && state.finished;
        boolean predictionCorrect = state != null && state.predictionCorrect;

        double momentumDelta = momentum - momentumMemory;
        double pressureDelta = pressure - pressureMemory;
        double crowdLift = Math.abs(momentum - 0.5f) * 2.0;

        if (qteActive && !qteLatch) {
            oyEnvelope = Math.max(oyEnvelope, 0.52 + pressure * 0.32);
            cheerEnvelope = Math.max(cheerEnvelope, 0.18 + pressure * 0.16 + crowdLift * 0.08);
        }
        if (pressureDelta > 0.038) {
            oyEnvelope = Math.max(oyEnvelope, 0.24 + pressureDelta * 5.6 + pressure * 0.16);
        }
        if (momentumDelta > 0.032) {
            cheerEnvelope = Math.max(cheerEnvelope, 0.14 + momentumDelta * 4.8 + crowdLift * 0.2);
        }
        if (momentumDelta < -0.034 && pressure > 0.46f) {
            dismayEnvelope = Math.max(dismayEnvelope, 0.16 + (-momentumDelta) * 4.4 + pressure * 0.18);
        }
        if (finished && !finishedLatch) {
            if (predictionCorrect) {
                cheerEnvelope = Math.max(cheerEnvelope, 0.76 + pressure * 0.18 + crowdLift * 0.12);
            } else {
                dismayEnvelope = Math.max(dismayEnvelope, 0.74 + pressure * 0.22);
                oyEnvelope = Math.max(oyEnvelope, 0.28 + pressure * 0.14);
            }
        }

        double baseCrowdHz = 118.0 + pressure * 42.0 + crowdLift * 24.0;
        double murmurHz = 42.0 + control * 24.0;
        double cheerHzA = 286.0 + pressure * 66.0 + crowdLift * 72.0;
        double cheerHzB = 462.0 + reflex * 118.0 + pressure * 36.0;
        double oyHz = 188.0 + pressure * 94.0;
        double dismayHz = 154.0 - control * 30.0 + pressure * 42.0;
        double stereoWidth = 0.12 + pressure * 0.12 + crowdLift * 0.09;
        double bedGain = 0.72 + pressure * 0.18 + (qteActive ? 0.12 : 0.0);

        double crowdStep = (Math.PI * 2.0 * baseCrowdHz) / SAMPLE_RATE;
        double noiseStep = (Math.PI * 2.0 * murmurHz) / SAMPLE_RATE;
        double cheerStepA = (Math.PI * 2.0 * cheerHzA) / SAMPLE_RATE;
        double cheerStepB = (Math.PI * 2.0 * cheerHzB) / SAMPLE_RATE;
        double oyStep = (Math.PI * 2.0 * oyHz) / SAMPLE_RATE;
        double dismayStep = (Math.PI * 2.0 * dismayHz) / SAMPLE_RATE;
        double stereoStep = (Math.PI * 2.0 * (0.08 + pressure * 0.08 + progress * 0.04)) / SAMPLE_RATE;

        for (int frame = 0; frame < FRAMES_PER_BUFFER; frame++) {
            crowdPhase += crowdStep;
            crowdNoisePhase += noiseStep;
            cheerPhaseA += cheerStepA;
            cheerPhaseB += cheerStepB;
            oyPhase += oyStep;
            dismayPhase += dismayStep;
            stereoPhase += stereoStep;

            double crowdBed = (Math.sin(crowdPhase) * 0.24
                    + Math.sin(crowdPhase * 1.7) * 0.14
                    + Math.sin(crowdNoisePhase * 0.46) * 0.18
                    + Math.sin(crowdNoisePhase * 0.91) * 0.1) * bedGain;
            double rustle = (Math.sin(crowdNoisePhase * 1.32) * 0.08
                    + Math.sin(crowdNoisePhase * 2.28) * 0.05) * (0.48 + pressure * 0.32);

            double cheerVoice = (Math.sin(cheerPhaseA)
                    + Math.sin(cheerPhaseA * 1.97) * 0.46
                    + Math.sin(cheerPhaseB) * 0.34) * cheerEnvelope;
            double oyFormant = (Math.sin(oyPhase) * 0.76 + Math.sin(oyPhase * 2.42) * 0.28);
            double oyTail = Math.sin(oyPhase * 1.34 + 0.8) * 0.2;
            double oyVoice = (oyFormant + oyTail) * oyEnvelope;
            double dismayVoice = (Math.sin(dismayPhase) * 0.58
                    + Math.sin(dismayPhase * 0.74 + 1.2) * 0.34
                    + Math.sin(dismayPhase * 1.56) * 0.18) * dismayEnvelope;

            double widthSwing = Math.sin(stereoPhase) * stereoWidth;
            double left = crowdBed + rustle * 0.86 + cheerVoice * (0.62 + widthSwing) + oyVoice * (0.84 + widthSwing * 0.6) + dismayVoice * 0.74;
            double right = crowdBed - rustle * 0.82 + cheerVoice * (0.88 - widthSwing) + oyVoice * (0.58 - widthSwing * 0.4) + dismayVoice * 0.92;

            double monoEnergy = (Math.abs(left) + Math.abs(right)) * 0.5;
            double followerRate = monoEnergy > busFollower ? 0.12 : 0.02;
            busFollower += (monoEnergy - busFollower) * followerRate;
            double busGain = 1.0 / (1.0 + Math.max(0.0, busFollower - 0.26) * 1.8);

            left = limited(left * MASTER_GAIN * busGain, LIMITER_THRESHOLD);
            right = limited(right * MASTER_GAIN * busGain, LIMITER_THRESHOLD);

            pcm[frame * 2] = (short) Math.round(left * 32767.0);
            pcm[frame * 2 + 1] = (short) Math.round(right * 32767.0);

            cheerEnvelope *= 0.9986;
            oyEnvelope *= 0.9978;
            dismayEnvelope *= 0.9981;
        }

        pressureMemory += (pressure - pressureMemory) * 0.24;
        momentumMemory += (momentum - momentumMemory) * 0.2;
        qteLatch = qteActive;
        finishedLatch = finished;
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