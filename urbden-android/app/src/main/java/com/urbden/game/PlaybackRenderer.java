package com.urbden.game;

import android.content.res.AssetManager;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.LinearGradient;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.RectF;
import android.graphics.Shader;
import android.opengl.GLES20;
import android.opengl.GLSurfaceView;
import android.opengl.GLUtils;
import android.opengl.Matrix;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.FloatBuffer;
import java.util.ArrayList;
import java.util.List;

import javax.microedition.khronos.egl.EGLConfig;
import javax.microedition.khronos.opengles.GL10;

public class PlaybackRenderer implements GLSurfaceView.Renderer {
    private static final int FLOAT_SIZE = 4;
    private static final int STRIDE_FLOATS = 8;
    private static final int STRIDE_BYTES = STRIDE_FLOATS * FLOAT_SIZE;

    private final AssetManager assetManager;
    private final DirkOddsScenario scenario;
    private final float[] projectionMatrix = new float[16];
    private final float[] viewMatrix = new float[16];
    private final float[] viewProjectionMatrix = new float[16];
    private final float[] modelMatrix = new float[16];
    private final float[] modelViewProjectionMatrix = new float[16];
    private final float[] tempMatrix = new float[16];

    private Mesh planeMesh;
    private Mesh cylinderMesh;
    private Mesh sphereMesh;
    private Mesh blockMesh;
    private int program;
    private int positionHandle;
    private int texCoordHandle;
    private int normalHandle;
    private int mvpHandle;
    private int modelHandle;
    private int lightHandle;
    private int cameraHandle;
    private int textureHandle;
    private int fieldTextureId;
    private int homeTextureId;
    private int awayTextureId;
    private int homeSidelineTextureId;
    private int awaySidelineTextureId;
    private int neutralTextureId;
    private int focusTextureId;
    private int quickthingsCardTextureId;
    private int quickthingsPortalTextureId;
    private int shadowTextureId;
    private int heatTextureId;
    private int crowdTextureId;
    private int fogTextureId;
    private int rayTextureId;
    private volatile DirkOddsMatchState currentState;

    public PlaybackRenderer(AssetManager assetManager, DirkOddsScenario scenario) {
        this.assetManager = assetManager;
        this.scenario = scenario;
    }

    @Override
    public void onSurfaceCreated(GL10 gl, EGLConfig config) {
        GLES20.glClearColor(0.03f, 0.04f, 0.07f, 1f);
        GLES20.glEnable(GLES20.GL_DEPTH_TEST);
        GLES20.glEnable(GLES20.GL_BLEND);
        GLES20.glBlendFunc(GLES20.GL_SRC_ALPHA, GLES20.GL_ONE_MINUS_SRC_ALPHA);

        program = createProgram(VERTEX_SHADER, FRAGMENT_SHADER);
        positionHandle = GLES20.glGetAttribLocation(program, "aPosition");
        texCoordHandle = GLES20.glGetAttribLocation(program, "aTexCoord");
        normalHandle = GLES20.glGetAttribLocation(program, "aNormal");
        mvpHandle = GLES20.glGetUniformLocation(program, "uMvpMatrix");
        modelHandle = GLES20.glGetUniformLocation(program, "uModelMatrix");
        lightHandle = GLES20.glGetUniformLocation(program, "uLightDir");
        cameraHandle = GLES20.glGetUniformLocation(program, "uCameraPos");
        textureHandle = GLES20.glGetUniformLocation(program, "uTexture");

        try {
            planeMesh = createArenaSurfaceMesh();
            blockMesh = loadObjMesh("playback/meshes/courthouse_block.obj");
            cylinderMesh = createCylinderMesh(24);
            sphereMesh = createSphereMesh(28, 20);
            fieldTextureId = createTexture(fieldTextureId());
            homeTextureId = createTexture("dirkodds_home");
            awayTextureId = createTexture("dirkodds_away");
            homeSidelineTextureId = createTexture("dirkodds_home_sideline");
            awaySidelineTextureId = createTexture("dirkodds_away_sideline");
            neutralTextureId = createTexture("dirkodds_neutral");
            focusTextureId = createTexture("dirkodds_focus");
            quickthingsCardTextureId = createTexture("dirkodds_quickthings_card");
            quickthingsPortalTextureId = createTexture("dirkodds_quickthings_portal");
            shadowTextureId = createTexture("dirkodds_shadow");
            heatTextureId = createTexture("dirkodds_heat_haze");
            crowdTextureId = createTexture("dirkodds_crowd_band");
            fogTextureId = createTexture("dirkodds_fog_volume");
            rayTextureId = createTexture("dirkodds_light_ray");
        } catch (Exception ignored) {
        }
    }

    @Override
    public void onSurfaceChanged(GL10 gl, int width, int height) {
        GLES20.glViewport(0, 0, width, height);
        float aspect = height == 0 ? 1f : (float) width / (float) height;
        Matrix.perspectiveM(projectionMatrix, 0, 54f, aspect, 0.1f, 100f);
    }

    @Override
    public void onDrawFrame(GL10 gl) {
        GLES20.glClear(GLES20.GL_COLOR_BUFFER_BIT | GLES20.GL_DEPTH_BUFFER_BIT);
        DirkOddsMatchState state = currentState;
        if (program == 0 || planeMesh == null || cylinderMesh == null || sphereMesh == null || blockMesh == null || state == null) {
            return;
        }

        float orbitProgress = state.progress;
        if (scenario.isQuickthings()) {
            if ("SUSPEND".equals(state.shotPhase)) {
                orbitProgress *= 0.22f;
            } else if ("COLLAPSE".equals(state.shotPhase)) {
                orbitProgress *= 0.4f;
            }
        }
        float orbit = scenario.isQuickthings() ? -42f + orbitProgress * 32f : -28f + state.progress * 18f;
        float yawRadians = (float) Math.toRadians(orbit);
        float eyeDistance = scenario.isQuickthings() ? 10.6f : 8.8f;
        if (scenario.isQuickthings()) {
            if ("SUSPEND".equals(state.shotPhase)) {
                eyeDistance -= 1.15f;
            } else if ("COLLAPSE".equals(state.shotPhase)) {
                eyeDistance -= 0.7f;
            }
        }
        float eyeX = (float) (Math.sin(yawRadians) * eyeDistance);
        float eyeY = scenario.isQuickthings() ? 5.9f : 4.8f;
        if (scenario.isQuickthings()) {
            if ("SUSPEND".equals(state.shotPhase)) {
                eyeY += 0.35f;
            } else if ("COLLAPSE".equals(state.shotPhase)) {
                eyeY += 0.18f;
            }
        }
        float eyeZ = (float) (Math.cos(yawRadians) * eyeDistance);
        float lookY = scenario.isQuickthings() ? 1.1f : 0.8f;
        if (scenario.isQuickthings() && "COLLAPSE".equals(state.shotPhase)) {
            lookY += 0.22f;
        }
        Matrix.setLookAtM(viewMatrix, 0, eyeX, eyeY, eyeZ, 0f, lookY, 0f, 0f, 1f, 0f);
        Matrix.multiplyMM(viewProjectionMatrix, 0, projectionMatrix, 0, viewMatrix, 0);

        GLES20.glUseProgram(program);
        GLES20.glUniform3f(lightHandle, 0.42f, 0.88f, 0.24f);
        GLES20.glUniform3f(cameraHandle, eyeX, eyeY, eyeZ);

        if (scenario.isQuickthings()) {
            drawQuickthingsScene(state);
        } else {
            float[] fieldScale = fieldScale();
            drawArenaFloor(state, fieldScale, false);
            drawArenaShell(state, fieldScale, false);
            drawVolumetricLayers(state, fieldScale, false);
            drawHeatAtmosphere(state, fieldScale, false);
            drawShadowBlob(-fieldScale[0] * 1.5f, 0f, 0.24f, 0.18f, 0.18f, 0f);
            drawShadowBlob(fieldScale[0] * 1.5f, 0f, 0.24f, 0.18f, 0.18f, 0f);
            drawShadowBlob(state.focusX, state.focusZ, 0.24f + state.pressure * 0.12f, 0.18f, 0.18f + state.pressure * 0.12f, state.progress * 180f);
            drawMesh(blockMesh, neutralTextureId, -fieldScale[0] * 1.5f, 0.02f, 0f, 0f, 0f, 0f, 0.18f, 0.18f, 0.18f);
            drawMesh(blockMesh, neutralTextureId, fieldScale[0] * 1.5f, 0.02f, 0f, 0f, 180f, 0f, 0.18f, 0.18f, 0.18f);
            drawMesh(blockMesh, focusTextureId, state.focusX, 0.02f, state.focusZ, 0f, state.progress * 720f, 0f, 0.08f, 0.08f + state.pressure * 0.08f, 0.08f);
            drawSportBackdrop(state, fieldScale, false);
            drawVenueSignage(state, fieldScale);
            drawSidelineIdentity(true, state, fieldScale);
            drawSidelineIdentity(false, state, fieldScale);

            int teamSize = scenario.teamSize();
            for (int index = 0; index < teamSize; index++) {
                float[] home = playerPosition(index, true, state);
                float[] away = playerPosition(index, false, state);
                drawHumanoid(homeTextureId, home, index, true, state);
                drawHumanoid(awayTextureId, away, index, false, state);
            }
        }
    }

    public void updateState(DirkOddsMatchState state) {
        currentState = state;
    }

    public void adjustOrbit(float deltaYaw, float deltaPitch) {
    }

    public void adjustZoom(float deltaDistance) {
    }

    private void drawArenaFloor(DirkOddsMatchState state, float[] scale, boolean quickthings) {
        float lipScaleX = scale[0] * (quickthings ? 1.14f : 1.1f);
        float lipScaleZ = scale[1] * (quickthings ? 1.14f : 1.1f);
        drawMesh(blockMesh, neutralTextureId, 0f, -0.12f, 0f, 0f, 0f, 0f, lipScaleX, 0.12f, lipScaleZ);
        drawMesh(blockMesh, neutralTextureId, 0f, -0.025f, 0f, 0f, 0f, 0f, scale[0] * 1.03f, 0.02f, scale[1] * 1.03f);
        drawMesh(planeMesh, fieldTextureId, 0f, 0.002f, 0f, 0f, 0f, 0f, scale[0], 1f, scale[1]);

        float apronPulse = quickthings ? 0.03f + state.shotPhaseProgress * 0.05f : 0.025f + state.pressure * 0.035f;
        drawMesh(planeMesh, neutralTextureId, 0f, -0.003f, 0f, 0f, 0f, 0f, scale[0] * 1.045f, 1f, scale[1] * 1.045f + apronPulse);
    }

    private void drawArenaShell(DirkOddsMatchState state, float[] scale, boolean quickthings) {
        if (crowdTextureId == 0) {
            return;
        }
        float shellLift = quickthings ? 0.42f : 0.34f;
        float shellDepth = quickthings ? scale[1] + 0.76f : scale[1] + 0.54f;
        float shellWidth = scale[0] + 0.46f;
        float pulse = quickthings
                ? 0.08f + state.bosonSync * 0.12f + state.cardCharge * 0.1f
                : 0.06f + state.pressure * 0.1f + Math.abs(state.momentum - 0.5f) * 0.08f;

        drawMesh(blockMesh, crowdTextureId, 0f, shellLift, -shellDepth, 0f, 0f, 0f, shellWidth, 0.28f + pulse, 0.05f);
        drawMesh(blockMesh, crowdTextureId, 0f, shellLift, shellDepth, 0f, 180f, 0f, shellWidth, 0.24f + pulse * 0.8f, 0.05f);
        drawMesh(blockMesh, crowdTextureId, -shellWidth, shellLift * 0.96f, 0f, 0f, 90f, 0f, shellDepth * 0.9f, 0.22f + pulse * 0.7f, 0.05f);
        drawMesh(blockMesh, crowdTextureId, shellWidth, shellLift * 0.96f, 0f, 0f, -90f, 0f, shellDepth * 0.9f, 0.22f + pulse * 0.7f, 0.05f);

        drawMesh(blockMesh, focusTextureId, 0f, shellLift + 0.1f + pulse * 0.12f, -shellDepth - 0.02f, 0f, state.progress * 42f, 0f, shellWidth * 0.18f, 0.12f, 0.02f);
        if (!quickthings) {
            drawMesh(blockMesh, focusTextureId, 0f, shellLift + 0.08f + pulse * 0.08f, shellDepth + 0.02f, 0f, -state.progress * 30f, 0f, shellWidth * 0.12f, 0.08f, 0.02f);
        }
    }

    private void drawVolumetricLayers(DirkOddsMatchState state, float[] scale, boolean quickthings) {
        if (fogTextureId == 0 || rayTextureId == 0) {
            return;
        }
        float intensity = quickthings
                ? 0.2f + state.bosonSync * 0.22f + state.cardCharge * 0.16f
                : 0.16f + state.pressure * 0.24f + Math.abs(state.momentum - 0.5f) * 0.18f;
        float drift = state.progress * 180f;
        float farZ = scale[1] + (quickthings ? 0.42f : 0.28f);

        for (int index = 0; index < 3; index++) {
            float side = index - 1f;
            float fogX = side * scale[0] * 0.36f;
            float fogZ = -farZ + index * 0.5f;
            float fogY = 0.36f + index * 0.12f + intensity * 0.08f;
            float fogWidth = 1.22f + intensity * 0.42f - index * 0.1f;
            float fogHeight = 0.72f + index * 0.22f + intensity * 0.24f;
            drawMesh(planeMesh, fogTextureId, fogX, fogY, fogZ, 90f, drift * 0.18f + side * 14f, 0f,
                    fogWidth, 1f, fogHeight);
        }

        for (int index = 0; index < 2; index++) {
            float side = index == 0 ? -1f : 1f;
            float rayX = side * scale[0] * 0.62f;
            float rayZ = -scale[1] * 0.34f;
            float rayY = 0.78f + intensity * 0.14f;
            float rayWidth = 0.54f + intensity * 0.16f;
            float rayHeight = 1.46f + intensity * 0.34f;
            drawMesh(planeMesh, rayTextureId, rayX, rayY, rayZ, 90f, side * (12f + drift * 0.08f), 0f,
                    rayWidth, 1f, rayHeight);
        }
    }

    private void drawSportBackdrop(DirkOddsMatchState state, float[] scale, boolean quickthings) {
        float rearZ = scale[1] + 0.42f;
        float pulse = 0.04f + state.pressure * 0.08f;
        if (quickthings) {
            drawMesh(cylinderMesh, quickthingsPortalTextureId, 0f, 0.92f, -rearZ - 0.18f, 90f, state.progress * 90f, 0f, 0.9f, 0.05f, 0.9f);
            drawMesh(blockMesh, crowdTextureId, 0f, 0.46f, -rearZ - 0.18f, 0f, 0f, 0f, 0.68f, 0.42f + pulse, 0.06f);
            return;
        }

        switch (scenario.sport) {
            case "football":
                drawMesh(cylinderMesh, focusTextureId, -0.54f, 0.84f, -rearZ, 0f, 0f, 0f, 0.04f, 0.84f, 0.04f);
                drawMesh(cylinderMesh, focusTextureId, 0.54f, 0.84f, -rearZ, 0f, 0f, 0f, 0.04f, 0.84f, 0.04f);
                drawMesh(cylinderMesh, focusTextureId, 0f, 1.48f, -rearZ, 90f, 0f, 0f, 0.58f, 0.03f, 0.58f);
                break;
            case "basketball":
                drawMesh(blockMesh, crowdTextureId, 0f, 0.92f, -rearZ, 0f, 0f, 0f, 0.34f, 0.26f, 0.03f);
                drawMesh(cylinderMesh, focusTextureId, 0f, 0.56f, -rearZ + 0.08f, 90f, 0f, 0f, 0.16f, 0.01f, 0.16f);
                drawMesh(cylinderMesh, neutralTextureId, 0f, 0.46f, -rearZ, 0f, 0f, 0f, 0.02f, 0.46f, 0.02f);
                break;
            case "baseball":
                drawMesh(blockMesh, crowdTextureId, -0.58f, 0.36f, -rearZ, 0f, 0f, 0f, 0.28f, 0.22f + pulse, 0.1f);
                drawMesh(blockMesh, crowdTextureId, 0.58f, 0.36f, -rearZ, 0f, 0f, 0f, 0.28f, 0.22f + pulse, 0.1f);
                drawMesh(blockMesh, focusTextureId, 0f, 0.58f, -rearZ, 0f, 0f, 0f, 0.86f, 0.06f, 0.04f);
                break;
            case "hockey":
                drawMesh(blockMesh, focusTextureId, 0f, 0.22f, -rearZ, 0f, 0f, 0f, 0.24f, 0.18f, 0.04f);
                drawMesh(cylinderMesh, focusTextureId, -0.22f, 0.42f, -rearZ, 0f, 0f, 0f, 0.02f, 0.34f, 0.02f);
                drawMesh(cylinderMesh, focusTextureId, 0.22f, 0.42f, -rearZ, 0f, 0f, 0f, 0.02f, 0.34f, 0.02f);
                drawMesh(cylinderMesh, focusTextureId, 0f, 0.58f, -rearZ, 90f, 0f, 0f, 0.24f, 0.02f, 0.24f);
                break;
            case "multisport":
                drawMesh(blockMesh, crowdTextureId, 0f, 0.86f, -rearZ, 0f, 0f, 0f, 0.92f, 0.16f + pulse, 0.04f);
                drawMesh(cylinderMesh, focusTextureId, -0.7f, 0.74f, -rearZ, 0f, 0f, 0f, 0.03f, 0.7f, 0.03f);
                drawMesh(cylinderMesh, focusTextureId, 0.7f, 0.74f, -rearZ, 0f, 0f, 0f, 0.03f, 0.7f, 0.03f);
                break;
            default:
                break;
        }
    }

    private void drawVenueSignage(DirkOddsMatchState state, float[] scale) {
        float rearZ = scale[1] + 0.62f;
        float bannerY = 1.18f + state.pressure * 0.18f;
        float pulse = 0.08f + state.pressure * 0.12f + (state.qteActive ? 0.08f : 0f);
        float drift = state.progress * 72f;
        float scoreBias = saturate((state.homeScore - state.awayScore) * 0.16f + 0.5f);
        float homeLift = 0.16f + scoreBias * 0.18f + Math.max(0f, state.momentum - 0.5f) * 0.22f;
        float awayLift = 0.16f + (1f - scoreBias) * 0.18f + Math.max(0f, 0.5f - state.momentum) * 0.22f;

        drawMesh(blockMesh, crowdTextureId, 0f, bannerY + 0.14f, -rearZ, 0f, 0f, 0f, 1.1f + pulse, 0.1f, 0.05f);
        drawMesh(blockMesh, focusTextureId, 0f, bannerY + 0.14f, -rearZ + 0.01f, 0f, drift, 0f, 0.24f + pulse * 0.12f, 0.04f, 0.02f);

        for (int index = 0; index < 2; index++) {
            boolean home = index == 0;
            float side = home ? -1f : 1f;
            int sidelineTexture = home ? homeSidelineTextureId : awaySidelineTextureId;
            int teamTexture = home ? homeTextureId : awayTextureId;
            float towerX = side * (scale[0] + 0.96f);
            float towerLift = home ? homeLift : awayLift;
            float ringSpin = drift * (home ? 1f : -1f);
            float screenTilt = (float) Math.sin(state.progress * 5.2f + index * 1.3f) * (4f + pulse * 16f);

            drawShadowBlob(towerX, -rearZ + 0.16f, 0.18f + towerLift * 0.1f, 0.22f, 0.18f, 0f);
            drawMesh(cylinderMesh, neutralTextureId, towerX, 0.38f + towerLift * 0.08f, -rearZ + 0.16f, 0f, 0f, 0f, 0.05f, 0.48f + towerLift * 0.12f, 0.05f);
            drawMesh(blockMesh, sidelineTexture, towerX, 0.92f + towerLift * 0.16f, -rearZ + 0.08f, 0f, home ? 18f : -18f, screenTilt, 0.28f, 0.12f + towerLift * 0.06f, 0.04f);
            drawMesh(blockMesh, teamTexture, towerX, 0.58f + towerLift * 0.08f, -rearZ + 0.1f, 0f, home ? 18f : -18f, 0f, 0.16f, 0.16f, 0.04f);
            drawMesh(cylinderMesh, focusTextureId, towerX, 0.18f, -rearZ + 0.16f, 90f, ringSpin, 0f, 0.18f + towerLift * 0.08f, 0.012f, 0.18f + towerLift * 0.08f);
        }
    }

    private void drawHeatAtmosphere(DirkOddsMatchState state, float[] scale, boolean quickthings) {
        if (heatTextureId == 0) {
            return;
        }
        float intensity = quickthings
                ? 0.22f + state.cardCharge * 0.36f + state.bosonSync * 0.18f
                : 0.16f + state.pressure * 0.34f + Math.abs(state.momentum - 0.5f) * 0.22f;
        float sweep = state.progress * 360f;
        float width = scale[0] * (quickthings ? 0.94f : 0.82f);
        float depth = scale[1] * (quickthings ? 0.74f : 0.56f);

        drawMesh(planeMesh, heatTextureId, 0f, 0.009f, 0f, 0f, sweep * 0.22f, 0f,
                width, 1f, depth + intensity * 0.18f);
        drawMesh(planeMesh, heatTextureId, 0f, 0.013f, 0f, 0f, -24f - sweep * 0.16f, 0f,
                width * 0.72f, 1f, depth * 1.18f);

        if (quickthings) {
            drawMesh(planeMesh, heatTextureId, state.focusX * 0.36f, 0.017f, state.focusZ * 0.42f - 0.18f,
                    0f, 58f + sweep * 0.28f, 0f,
                    0.68f + state.entropy * 0.24f, 1f, 0.92f + state.cardCharge * 0.32f);
        } else {
            drawMesh(planeMesh, heatTextureId, state.focusX * 0.22f, 0.016f, state.focusZ * 0.2f,
                    0f, 42f + sweep * 0.24f, 0f,
                    0.44f + state.pressure * 0.18f, 1f, 0.82f + intensity * 0.22f);
        }
    }

    private void drawShadowBlob(float px, float pz, float alpha, float scaleX, float scaleZ, float rotationY) {
        if (shadowTextureId == 0) {
            return;
        }
        drawMesh(planeMesh, shadowTextureId, px, 0.005f + alpha * 0.002f, pz, 0f, rotationY, 0f, scaleX, 1f, scaleZ);
    }

    private float[] fieldScale() {
        switch (scenario.sport) {
            case "multisport":
                return new float[] {1.9f, 1.32f};
            case "quickthings":
                return new float[] {2.35f, 2.35f};
            case "hockey":
                return new float[] {1.82f, 1.18f};
            case "basketball":
                return new float[] {1.55f, 1.15f};
            case "baseball":
                return new float[] {1.7f, 1.35f};
            default:
                return new float[] {1.95f, 1.35f};
        }
    }

    private float[] playerPosition(int index, boolean home, DirkOddsMatchState state) {
        float signedMomentum = state.momentum * 2f - 1f;
        float side = home ? -1f : 1f;
        float t = state.progress * 6.28318f;
        if ("multisport".equals(scenario.sport)) {
            float segment = state.progress;
            if (segment < 0.25f) {
                int row = index / 2;
                int col = index % 2;
                float x = side * (2.45f - row * 0.7f) + signedMomentum * (home ? 0.4f : -0.4f);
                float z = -0.9f + col * 1.2f + (index == 4 ? 1.02f : 0f) + (float) Math.sin(t + index * 0.55f) * 0.1f;
                return new float[] {x, 0.05f, z, home ? 90f : -90f};
            }
            if (segment < 0.5f) {
                float lane = index - 2.5f;
                float x = side * (1.42f - index * 0.2f) + signedMomentum * (home ? 0.62f : -0.62f);
                float z = lane * 0.54f + (float) Math.sin(t + index * 0.85f) * 0.18f;
                return new float[] {x, 0.05f, z, home ? 92f : -92f};
            }
            if (segment < 0.75f) {
                float[][] bases = new float[][] {
                        {side * 1.82f, 0.05f, 0f},
                        {side * 1.0f, 0.05f, -0.85f},
                        {side * 0.5f, 0.05f, 1.02f},
                        {side * 0.18f, 0.05f, -1.28f},
                        {side * 0.82f, 0.05f, 1.36f},
                        {side * 1.42f, 0.05f, 0.92f}
                };
                float[] base = bases[index % bases.length];
                return new float[] {
                        base[0] + signedMomentum * (home ? 0.18f : -0.18f),
                        base[1],
                        base[2] + (float) Math.sin(t + index) * 0.12f,
                        home ? 112f : -68f
                };
            }
            float[][] lanes = new float[][] {
                    {side * 1.56f, 0.05f, 0f, home ? 90f : -90f},
                    {side * 1.0f, 0.05f, -0.8f, home ? 96f : -96f},
                    {side * 1.0f, 0.05f, 0.8f, home ? 84f : -84f},
                    {side * 0.36f, 0.05f, -1.02f, home ? 101f : -101f},
                    {side * 0.2f, 0.05f, 1.04f, home ? 79f : -79f},
                    {side * 0.03f, 0.05f, 0f, home ? 90f : -90f}
            };
            float[] lane = lanes[index % lanes.length];
            return new float[] {
                    lane[0] + signedMomentum * (home ? 0.32f : -0.32f),
                    lane[1],
                    lane[2] + (float) Math.sin(t * 1.3f + index * 0.72f) * 0.18f,
                    lane[3]
            };
        }
        if ("hockey".equals(scenario.sport)) {
            float[][] lanes = new float[][] {
                    {side * 1.62f, 0.05f, 0f, home ? 90f : -90f},
                    {side * 1.04f, 0.05f, -0.82f, home ? 96f : -96f},
                    {side * 1.04f, 0.05f, 0.82f, home ? 84f : -84f},
                    {side * 0.38f, 0.05f, -1.1f, home ? 102f : -102f},
                    {side * 0.22f, 0.05f, 1.12f, home ? 78f : -78f},
                    {side * 0.02f, 0.05f, 0f, home ? 90f : -90f}
            };
            float[] lane = lanes[index % lanes.length];
            return new float[] {
                    lane[0] + signedMomentum * (home ? 0.34f : -0.34f),
                    lane[1],
                    lane[2] + (float) Math.sin(t * 1.35f + index * 0.72f) * 0.18f,
                    lane[3]
            };
        }
        if ("basketball".equals(scenario.sport)) {
            float lane = index - 2f;
            float x = side * (1.5f - index * 0.22f) + signedMomentum * (home ? 0.65f : -0.65f);
            float z = lane * 0.62f + (float) Math.sin(t + index * 0.8f) * 0.18f;
            return new float[] {x, 0.05f, z, home ? 90f : -90f};
        }
        if ("baseball".equals(scenario.sport)) {
            float[][] bases = new float[][] {
                    {side * 1.9f, 0.05f, 0f},
                    {side * 1.1f, 0.05f, -0.9f},
                    {side * 0.55f, 0.05f, 1.1f},
                    {side * 0.2f, 0.05f, -1.4f},
                    {side * 0.9f, 0.05f, 1.55f},
                    {side * 1.55f, 0.05f, 1.0f}
            };
            float[] base = bases[index % bases.length];
            return new float[] {
                    base[0] + signedMomentum * (home ? 0.18f : -0.18f),
                    base[1],
                    base[2] + (float) Math.sin(t + index) * 0.12f,
                    home ? 115f : -65f
            };
        }
        int row = index / 2;
        int col = index % 2;
        float x = side * (2.55f - row * 0.75f) + signedMomentum * (home ? 0.42f : -0.42f);
        float z = -0.95f + col * 1.25f + (index == 4 ? 1.1f : 0f) + (float) Math.sin(t + index * 0.55f) * 0.12f;
        return new float[] {x, 0.05f, z, home ? 90f : -90f};
    }

    private void drawHumanoid(int textureId, float[] placement, int index, boolean home, DirkOddsMatchState state) {
        float progressPhase = state.progress * 6.28318f + index * 0.65f + (home ? 0f : 1.3f);
        float gait = (float) Math.sin(progressPhase);
        float gaitOpposed = (float) Math.sin(progressPhase + Math.PI);
        float pressureLift = 0.02f + state.pressure * 0.035f;
        float leanZ = (state.momentum - 0.5f) * (home ? 10f : -10f);
        float torsoYaw = placement[3] + gait * 4f;
        float strideSpread = 0.22f + Math.abs(gait) * 0.04f;
        float shadowDepth = 0.16f + Math.abs(gaitOpposed) * 0.04f + pressureLift * 0.18f;

        drawShadowBlob(placement[0], placement[2], 0.26f + pressureLift * 0.5f, strideSpread, shadowDepth, torsoYaw);

        Matrix.setIdentityM(modelMatrix, 0);
        Matrix.translateM(modelMatrix, 0, placement[0], placement[1] + pressureLift, placement[2]);
        Matrix.rotateM(modelMatrix, 0, torsoYaw, 0f, 1f, 0f);
        Matrix.rotateM(modelMatrix, 0, leanZ, 0f, 0f, 1f);

        drawPart(blockMesh, textureId, 0f, 0.96f, 0f, 0f, 0f, 0f, 0.32f, 0.16f, 0.22f);
        drawPart(blockMesh, textureId, 0f, 0.74f, 0.02f, 0f, 0f, 0f, 0.28f, 0.2f, 0.18f);
        drawPart(cylinderMesh, textureId, 0f, 0.82f, 0f, 0f, 0f, 0f, 0.22f, 0.62f, 0.15f);
        drawPart(cylinderMesh, textureId, 0f, 0.32f, 0f, 0f, 0f, 0f, 0.24f, 0.34f, 0.16f);
        drawPart(cylinderMesh, textureId, 0f, 1.32f, 0f, 0f, 0f, 0f, 0.10f, 0.16f, 0.10f);
        drawPart(sphereMesh, textureId, 0f, 1.64f, 0f, 0f, gait * 8f, 0f, 0.19f, 0.23f, 0.19f);
        drawPart(blockMesh, textureId, -0.22f, 1.02f, 0f, 0f, 0f, 10f, 0.08f, 0.12f, 0.1f);
        drawPart(blockMesh, textureId, 0.22f, 1.02f, 0f, 0f, 0f, -10f, 0.08f, 0.12f, 0.1f);

        drawArm(textureId, -0.28f, 1.18f, 0f, 22f + gait * 18f, -10f + gait * 6f, true);
        drawArm(textureId, 0.28f, 1.18f, 0f, 22f + gaitOpposed * 18f, 10f + gaitOpposed * 6f, false);
        drawLeg(textureId, -0.12f, 0.18f, gaitOpposed * 16f, true);
        drawLeg(textureId, 0.12f, 0.18f, gait * 16f, false);
    }

    private void drawSidelineIdentity(boolean home, DirkOddsMatchState state, float[] fieldScale) {
        float side = home ? -1f : 1f;
        float baseX = side * (fieldScale[0] + 0.72f);
        int teamTexture = home ? homeTextureId : awayTextureId;
        int sidelineTexture = home ? homeSidelineTextureId : awaySidelineTextureId;

        drawShadowBlob(baseX, 0f, 0.22f, 0.24f, 1.04f, home ? 90f : -90f);
        drawShadowBlob(baseX, 1.22f, 0.16f, 0.14f, 0.32f, home ? 90f : -90f);
        drawShadowBlob(baseX, -1.22f, 0.16f, 0.14f, 0.32f, home ? 90f : -90f);

        drawMesh(blockMesh, sidelineTexture, baseX, 0.72f, 0f, 0f, home ? 90f : -90f, 0f, 0.05f, 0.62f, 1.22f);
        drawMesh(blockMesh, sidelineTexture, baseX, 0.42f, 1.22f, 0f, home ? 90f : -90f, 0f, 0.04f, 0.28f, 0.36f);
        drawMesh(blockMesh, sidelineTexture, baseX, 0.42f, -1.22f, 0f, home ? 90f : -90f, 0f, 0.04f, 0.28f, 0.36f);

        drawMascotStandee(teamTexture, sidelineTexture, baseX - side * 0.28f, 0.04f, 1.75f, home, state);
        drawReactiveSidelineDisplay(baseX, side, home, state);

        for (int index = 0; index < 3; index++) {
            float z = -0.82f + index * 0.82f;
            drawCheerFigure(teamTexture, baseX + side * 0.16f, 0.04f, z, home, state, index);
        }
    }

    private void drawReactiveSidelineDisplay(float baseX, float side, boolean home, DirkOddsMatchState state) {
        float idleWeight = state.qteActive ? 0.28f : 0.92f;
        float momentumBias = saturate(0.5f + (home ? state.momentum : -state.momentum) * 0.9f);
        float focusBias = saturate(home ? (-state.focusX + 0.7f) / 3.1f : (state.focusX + 0.7f) / 3.1f);
        float reaction = saturate(0.2f + idleWeight * 0.42f + momentumBias * 0.22f + focusBias * 0.24f + state.pressure * 0.1f);

        for (int index = 0; index < 3; index++) {
            float lane = index - 1f;
            float shimmer = (float) Math.sin(state.progress * (7.8f + index) + lane * 0.8f + (home ? 0f : 1.6f));
            float displayX = baseX - side * (0.11f + index * 0.07f);
            float displayZ = lane * 0.98f;
            float displayY = 0.24f + reaction * 0.18f + Math.abs(shimmer) * 0.08f;
            float columnHeight = 0.18f + reaction * 0.22f + index * 0.05f;
            float plateScale = 0.11f + reaction * 0.05f;

            drawShadowBlob(displayX, displayZ, 0.14f + reaction * 0.08f, 0.12f + reaction * 0.04f, 0.12f + reaction * 0.04f, 0f);

            drawMesh(cylinderMesh, focusTextureId, displayX, displayY, displayZ, 0f, state.progress * 180f + index * 22f, 90f, 0.03f + reaction * 0.015f, columnHeight, 0.03f + reaction * 0.015f);
            drawMesh(blockMesh, focusTextureId, displayX - side * 0.06f, displayY + columnHeight * 0.72f, displayZ, 0f, home ? 90f : -90f, shimmer * 4f, plateScale, 0.016f, 0.18f + reaction * 0.08f);
            drawMesh(cylinderMesh, neutralTextureId, displayX, 0.07f, displayZ, 90f, state.progress * 120f + index * 34f, 0f, 0.14f + reaction * 0.05f, 0.008f, 0.14f + reaction * 0.05f);
        }
    }

    private void drawMascotStandee(int teamTexture, int sidelineTexture, float px, float py, float pz, boolean home, DirkOddsMatchState state) {
        float idleWeight = state.qteActive ? 0.22f : 0.9f;
        float bounce = 0.04f + (float) Math.sin(state.progress * 9.4f + (home ? 0f : 1.6f)) * (0.02f + idleWeight * 0.025f);
        float headTurn = (float) Math.sin(state.progress * 6.1f + (home ? 0.3f : 1.9f)) * (4f + idleWeight * 8f);
        float armFlare = 14f + idleWeight * 14f + state.pressure * 6f;
        drawShadowBlob(px, pz, 0.2f + idleWeight * 0.08f, 0.22f, 0.18f + Math.abs(bounce) * 0.4f, home ? 75f : -75f);
        Matrix.setIdentityM(modelMatrix, 0);
        Matrix.translateM(modelMatrix, 0, px, py + bounce, pz);
        Matrix.rotateM(modelMatrix, 0, (home ? 75f : -75f) + headTurn * 0.2f, 0f, 1f, 0f);
        drawPart(cylinderMesh, teamTexture, 0f, 0.72f, 0f, 0f, 0f, 0f, 0.26f, 0.74f, 0.22f);
        drawPart(blockMesh, sidelineTexture, 0f, 1.06f, 0.12f, 0f, 0f, 0f, 0.24f, 0.18f, 0.04f);
        drawPart(sphereMesh, teamTexture, 0f, 1.44f, 0f, 0f, state.pressure * 18f + headTurn, 0f, 0.24f, 0.29f, 0.24f);
        drawPart(cylinderMesh, teamTexture, -0.17f, 0.18f, 0f, -8f, 0f, 0f, 0.08f, 0.24f, 0.08f);
        drawPart(cylinderMesh, teamTexture, 0.17f, 0.18f, 0f, 8f, 0f, 0f, 0.08f, 0.24f, 0.08f);
        drawPart(cylinderMesh, teamTexture, -0.28f, 0.92f, 0f, armFlare, 0f, 18f + idleWeight * 9f, 0.06f, 0.22f, 0.06f);
        drawPart(cylinderMesh, teamTexture, 0.28f, 0.92f, 0f, -armFlare, 0f, -18f - idleWeight * 9f, 0.06f, 0.22f, 0.06f);
    }

    private void drawCheerFigure(int textureId, float px, float py, float pz, boolean home, DirkOddsMatchState state, int index) {
        float idleWeight = state.qteActive ? 0.24f : 1f;
        float beat = (float) Math.sin(state.progress * (9.5f + idleWeight * 3.5f) + index * 0.85f + (home ? 0f : 1.2f));
        float sway = (float) Math.cos(state.progress * 6.2f + index * 0.55f + (home ? 0.2f : 1.4f)) * idleWeight * 8f;
        drawShadowBlob(px, pz, 0.12f + idleWeight * 0.06f, 0.12f, 0.1f + Math.abs(beat) * 0.08f, home ? 78f : -78f);
        Matrix.setIdentityM(modelMatrix, 0);
        Matrix.translateM(modelMatrix, 0, px, py + 0.02f + Math.abs(beat) * 0.02f, pz);
        Matrix.rotateM(modelMatrix, 0, (home ? 78f : -78f) + sway * 0.18f, 0f, 1f, 0f);
        drawPart(blockMesh, textureId, 0f, 0.34f, 0f, 0f, 0f, 0f, 0.17f, 0.14f, 0.17f);
        drawPart(cylinderMesh, textureId, 0f, 0.62f, 0f, 0f, 0f, 0f, 0.13f, 0.24f, 0.10f);
        drawPart(sphereMesh, textureId, 0f, 0.92f, 0f, 0f, 0f, 0f, 0.12f, 0.14f, 0.12f);
        drawPart(cylinderMesh, textureId, -0.14f, 0.62f, 0f, 42f + beat * (14f + idleWeight * 8f), 0f, 24f + sway * 0.2f, 0.04f, 0.18f, 0.04f);
        drawPart(cylinderMesh, textureId, 0.14f, 0.62f, 0f, -42f - beat * (14f + idleWeight * 8f), 0f, -24f - sway * 0.2f, 0.04f, 0.18f, 0.04f);
        drawPart(cylinderMesh, textureId, -0.06f, 0.08f, 0f, 0f, 0f, 0f, 0.04f, 0.18f, 0.04f);
        drawPart(cylinderMesh, textureId, 0.06f, 0.08f, 0f, 0f, 0f, 0f, 0.04f, 0.18f, 0.04f);
    }

    private void drawQuickthingsScene(DirkOddsMatchState state) {
        float[] courseScale = fieldScale();
        float stageLift = state.courseStage * 0.06f;
        float phasePulse = (float) Math.sin(state.shotPhaseProgress * Math.PI);
        float timeDilation = 0.82f + phasePulse * 0.36f;
        float breamX = state.focusX * 0.62f;
        float breamZ = state.focusZ * 0.72f - state.remainingVacuum * 1.2f + 0.55f + phasePulse * 0.22f;
        float breamY = 0.22f + state.cardCharge * 0.46f + (float) Math.sin(state.progress * 11f) * 0.05f + phasePulse * 0.08f;

        drawArenaFloor(state, new float[] {courseScale[0] * timeDilation, courseScale[1] * timeDilation}, true);
        drawArenaShell(state, new float[] {courseScale[0] * timeDilation, courseScale[1] * timeDilation}, true);
        drawVolumetricLayers(state, new float[] {courseScale[0] * timeDilation, courseScale[1] * timeDilation}, true);
        drawHeatAtmosphere(state, new float[] {courseScale[0] * timeDilation, courseScale[1] * timeDilation}, true);
        drawSportBackdrop(state, new float[] {courseScale[0] * timeDilation, courseScale[1] * timeDilation}, true);
        drawQuickthingsSpectatorDisplay(state, courseScale, phasePulse);
        drawShadowBlob(0f, -1.95f, 0.2f + state.sinkMargin * 0.1f, 0.28f + state.sinkMargin * 0.12f, 0.28f + state.sinkMargin * 0.12f, state.progress * 60f);
        drawMesh(sphereMesh, focusTextureId, 0f, 0.12f + state.sinkMargin * 0.18f, -1.95f, 0f, state.progress * 240f, 0f, 0.34f + state.sinkMargin * 0.1f + phasePulse * 0.08f, 0.09f + state.bosonSync * 0.18f, 0.34f + state.sinkMargin * 0.1f + phasePulse * 0.08f);
        drawShadowBlob(0f, 2.25f, 0.18f, 0.16f, 0.16f, state.progress * 40f);
        drawMesh(blockMesh, neutralTextureId, 0f, 0.02f, 2.25f, 0f, state.progress * 90f, 0f, 0.12f, 0.12f, 0.12f);

        drawShadowBlob(0f, -0.18f, 0.16f + phasePulse * 0.08f, 0.54f + phasePulse * 0.18f, 0.54f + phasePulse * 0.18f, state.progress * 100f);
        drawMesh(cylinderMesh, focusTextureId, 0f, 0.08f + phasePulse * 0.14f, -0.18f, 90f, state.progress * 180f, 0f, 0.5f + phasePulse * 1.2f, 0.012f, 0.5f + phasePulse * 1.2f);

        for (int index = 0; index < state.portalCount; index++) {
            float angle = state.progress * 3.4f + index * 2.1f;
            float radius = 0.9f + index * 0.58f + state.entropy * 0.42f;
            float portalX = (float) Math.cos(angle) * radius;
            float portalZ = (float) Math.sin(angle) * radius - 0.4f;
            float portalY = 0.24f + index * 0.07f + stageLift + phasePulse * 0.06f;
            float portalScale = 0.16f + index * 0.03f + phasePulse * 0.05f;
            drawShadowBlob(portalX, portalZ, 0.12f + portalScale * 0.1f, portalScale * 0.88f, portalScale * 0.88f, angle * 28f);
            drawMesh(cylinderMesh, quickthingsPortalTextureId, portalX, portalY, portalZ, 90f, angle * 57.29578f, state.progress * 90f, portalScale, 0.05f + state.bosonSync * 0.12f + phasePulse * 0.02f, portalScale);
            drawMesh(sphereMesh, quickthingsPortalTextureId, portalX, portalY + 0.02f, portalZ, 0f, state.progress * 140f, 0f, 0.18f + phasePulse * 0.05f, 0.03f, 0.18f + phasePulse * 0.05f);
        }

        for (int index = 0; index < 3; index++) {
            float spread = index - 1f;
            float hover = 1.1f + (float) Math.sin(state.progress * 8f + index) * 0.08f + state.cardCharge * 0.18f + phasePulse * 0.05f;
            float cardZ = 1.35f - index * 0.85f + (float) Math.cos(state.progress * 4f + index) * 0.16f;
            drawShadowBlob(spread * 1.05f, cardZ, 0.16f + state.cardCharge * 0.08f, 0.24f, 0.34f, spread * 12f);
            drawMesh(blockMesh, quickthingsCardTextureId, spread * 1.05f, hover, cardZ, -24f + spread * 7f, state.progress * 160f + index * 28f + phasePulse * 18f, spread * 9f, 0.34f, 0.02f, 0.5f);
            drawMesh(blockMesh, focusTextureId, spread * 1.05f, hover - 0.02f, cardZ, -24f + spread * 7f, state.progress * 160f + index * 28f, spread * 9f, 0.22f, 0.01f, 0.36f);
        }

        drawShadowBlob(breamX, breamZ, 0.16f + state.cardCharge * 0.1f, 0.2f + phasePulse * 0.08f, 0.42f + state.cardCharge * 0.12f, state.progress * 120f);
        drawMesh(cylinderMesh, quickthingsCardTextureId, breamX, breamY, breamZ, 0f, state.progress * 360f, 90f, 0.05f + phasePulse * 0.015f, 0.55f + state.cardCharge * 0.34f + phasePulse * 0.2f, 0.05f + phasePulse * 0.015f);
        drawMesh(sphereMesh, focusTextureId, breamX, breamY + 0.42f, breamZ, 0f, state.progress * 420f, 0f, 0.11f + state.bosonSync * 0.09f + phasePulse * 0.04f, 0.14f + state.bosonSync * 0.12f + phasePulse * 0.06f, 0.11f + state.bosonSync * 0.09f + phasePulse * 0.04f);

        for (int index = 0; index <= state.courseStage; index++) {
            float ringRadius = 0.42f + index * 0.28f;
            drawMesh(cylinderMesh, neutralTextureId, 0f, 0.05f + index * 0.04f + phasePulse * 0.02f, -0.18f * index, 90f, state.progress * 110f + index * 19f, 0f, ringRadius + phasePulse * 0.03f, 0.015f, ringRadius + phasePulse * 0.03f);
        }
    }

    private void drawQuickthingsSpectatorDisplay(DirkOddsMatchState state, float[] courseScale, float phasePulse) {
        float idleWeight = state.qteActive ? 0.26f : 0.96f;
        float observerLift = 0.14f + idleWeight * 0.12f + state.bosonSync * 0.08f;
        float edgeX = courseScale[0] + 0.42f;

        for (int sideIndex = 0; sideIndex < 2; sideIndex++) {
            boolean leftSide = sideIndex == 0;
            float side = leftSide ? -1f : 1f;
            float focusBias = saturate(leftSide ? (-state.focusX + 0.4f) / 2.8f : (state.focusX + 0.4f) / 2.8f);
            float sideReaction = saturate(0.26f + idleWeight * 0.34f + focusBias * 0.28f + state.cardCharge * 0.12f);

            for (int index = 0; index < 3; index++) {
                float lane = index - 1f;
                float z = lane * 1.14f - 0.18f;
                float pulse = (float) Math.sin(state.progress * (6.5f + index) + sideIndex * 1.7f + lane * 0.9f);
                float beaconY = observerLift + Math.abs(pulse) * 0.08f + phasePulse * 0.04f;
                float beaconX = side * edgeX;
                float ringScale = 0.18f + sideReaction * 0.07f + index * 0.03f;

                drawShadowBlob(beaconX, z, 0.12f + sideReaction * 0.08f, ringScale, ringScale, 0f);

                drawMesh(cylinderMesh, focusTextureId, beaconX, beaconY, z, 0f, state.progress * 200f + index * 36f, 90f, 0.028f + sideReaction * 0.018f, 0.22f + sideReaction * 0.12f, 0.028f + sideReaction * 0.018f);
                drawMesh(blockMesh, quickthingsPortalTextureId, beaconX - side * 0.08f, beaconY + 0.12f, z, 0f, leftSide ? 90f : -90f, pulse * 8f, 0.12f + sideReaction * 0.08f, 0.015f, 0.2f + sideReaction * 0.08f);
                drawMesh(cylinderMesh, quickthingsPortalTextureId, beaconX, 0.04f + index * 0.015f, z, 90f, state.progress * 140f + index * 26f, 0f, ringScale + phasePulse * 0.04f, 0.01f, ringScale + phasePulse * 0.04f);
            }
        }
    }

    private void drawArm(int textureId, float shoulderX, float shoulderY, float shoulderZ, float swing, float flare, boolean left) {
        float side = left ? -1f : 1f;
        float upperYaw = flare * side;
        float elbowBend = 18f + Math.abs(swing) * 0.45f;
        float[] upperRadii = new float[] {0.082f, 0.078f, 0.072f};
        float[] lowerRadii = new float[] {0.068f, 0.062f, 0.056f};
        for (int segment = 0; segment < 3; segment++) {
            float t = segment / 3f;
            drawPart(cylinderMesh, textureId,
                    shoulderX + side * 0.055f * segment,
                    shoulderY - 0.14f - segment * 0.18f,
                    shoulderZ,
                    swing + segment * 3f,
                    upperYaw,
                    side * (6f - segment * 1.5f),
                    upperRadii[segment],
                    0.19f,
                    upperRadii[Math.min(upperRadii.length - 1, segment)] * 0.92f);
        }
        float elbowY = shoulderY - 0.56f;
        for (int segment = 0; segment < 3; segment++) {
            drawPart(cylinderMesh, textureId,
                    shoulderX + side * (0.16f + segment * 0.05f),
                    elbowY - 0.10f - segment * 0.16f,
                    shoulderZ,
                    swing + elbowBend + segment * 4f,
                    upperYaw + segment * 1.5f,
                    side * (2f + segment),
                    lowerRadii[segment],
                    0.17f,
                    lowerRadii[segment] * 0.9f);
        }
    }

    private void drawLeg(int textureId, float hipX, float hipY, float swing, boolean left) {
        float side = left ? -1f : 1f;
        drawPart(cylinderMesh, textureId, hipX, hipY - 0.18f, 0f, swing, 0f, side * 1.5f, 0.10f, 0.28f, 0.10f);
        drawPart(cylinderMesh, textureId, hipX + side * 0.01f, hipY - 0.48f, 0f, swing * 0.55f + 12f, 0f, 0f, 0.085f, 0.26f, 0.085f);
        drawPart(cylinderMesh, textureId, hipX + side * 0.02f, hipY - 0.76f, 0.04f, 90f, 0f, 0f, 0.09f, 0.05f, 0.16f);
    }

    private void drawPart(Mesh mesh, int textureId, float px, float py, float pz, float rx, float ry, float rz, float sx, float sy, float sz) {
        Matrix.setIdentityM(tempMatrix, 0);
        Matrix.translateM(tempMatrix, 0, px, py, pz);
        Matrix.rotateM(tempMatrix, 0, rx, 1f, 0f, 0f);
        Matrix.rotateM(tempMatrix, 0, ry, 0f, 1f, 0f);
        Matrix.rotateM(tempMatrix, 0, rz, 0f, 0f, 1f);
        Matrix.scaleM(tempMatrix, 0, sx, sy, sz);
        Matrix.multiplyMM(tempMatrix, 0, modelMatrix, 0, tempMatrix, 0);
        drawMesh(mesh, textureId, tempMatrix);
    }

    private void drawMesh(Mesh mesh, int textureId, float px, float py, float pz, float rx, float ry, float rz, float sx, float sy, float sz) {
        Matrix.setIdentityM(modelMatrix, 0);
        Matrix.translateM(modelMatrix, 0, px, py, pz);
        Matrix.rotateM(modelMatrix, 0, rx, 1f, 0f, 0f);
        Matrix.rotateM(modelMatrix, 0, ry, 0f, 1f, 0f);
        Matrix.rotateM(modelMatrix, 0, rz, 0f, 0f, 1f);
        Matrix.scaleM(modelMatrix, 0, sx, sy, sz);
        drawMesh(mesh, textureId, modelMatrix);
    }

    private void drawMesh(Mesh mesh, int textureId, float[] worldMatrix) {
        Matrix.multiplyMM(modelViewProjectionMatrix, 0, viewProjectionMatrix, 0, worldMatrix, 0);

        GLES20.glUniformMatrix4fv(mvpHandle, 1, false, modelViewProjectionMatrix, 0);
        GLES20.glUniformMatrix4fv(modelHandle, 1, false, worldMatrix, 0);

        GLES20.glActiveTexture(GLES20.GL_TEXTURE0);
        GLES20.glBindTexture(GLES20.GL_TEXTURE_2D, textureId);
        GLES20.glUniform1i(textureHandle, 0);

        mesh.vertices.position(0);
        GLES20.glVertexAttribPointer(positionHandle, 3, GLES20.GL_FLOAT, false, STRIDE_BYTES, mesh.vertices);
        GLES20.glEnableVertexAttribArray(positionHandle);

        mesh.vertices.position(3);
        GLES20.glVertexAttribPointer(texCoordHandle, 2, GLES20.GL_FLOAT, false, STRIDE_BYTES, mesh.vertices);
        GLES20.glEnableVertexAttribArray(texCoordHandle);

        mesh.vertices.position(5);
        GLES20.glVertexAttribPointer(normalHandle, 3, GLES20.GL_FLOAT, false, STRIDE_BYTES, mesh.vertices);
        GLES20.glEnableVertexAttribArray(normalHandle);

        GLES20.glDrawArrays(GLES20.GL_TRIANGLES, 0, mesh.vertexCount);
    }

    private Mesh createCylinderMesh(int radialSegments) {
        List<Float> packed = new ArrayList<>();
        for (int segment = 0; segment < radialSegments; segment++) {
            float u0 = segment / (float) radialSegments;
            float u1 = (segment + 1) / (float) radialSegments;
            float theta0 = (float) (Math.PI * 2.0 * u0);
            float theta1 = (float) (Math.PI * 2.0 * u1);
            float x0 = (float) Math.cos(theta0);
            float z0 = (float) Math.sin(theta0);
            float x1 = (float) Math.cos(theta1);
            float z1 = (float) Math.sin(theta1);

            addVertex(packed, x0, -0.5f, z0, u0, 1f, x0, 0f, z0);
            addVertex(packed, x1, -0.5f, z1, u1, 1f, x1, 0f, z1);
            addVertex(packed, x1, 0.5f, z1, u1, 0f, x1, 0f, z1);

            addVertex(packed, x0, -0.5f, z0, u0, 1f, x0, 0f, z0);
            addVertex(packed, x1, 0.5f, z1, u1, 0f, x1, 0f, z1);
            addVertex(packed, x0, 0.5f, z0, u0, 0f, x0, 0f, z0);

            addVertex(packed, 0f, 0.5f, 0f, 0.5f, 0.5f, 0f, 1f, 0f);
            addVertex(packed, x1, 0.5f, z1, (x1 + 1f) * 0.5f, (z1 + 1f) * 0.5f, 0f, 1f, 0f);
            addVertex(packed, x0, 0.5f, z0, (x0 + 1f) * 0.5f, (z0 + 1f) * 0.5f, 0f, 1f, 0f);

            addVertex(packed, 0f, -0.5f, 0f, 0.5f, 0.5f, 0f, -1f, 0f);
            addVertex(packed, x0, -0.5f, z0, (x0 + 1f) * 0.5f, (z0 + 1f) * 0.5f, 0f, -1f, 0f);
            addVertex(packed, x1, -0.5f, z1, (x1 + 1f) * 0.5f, (z1 + 1f) * 0.5f, 0f, -1f, 0f);
        }
        return buildMeshFromPacked(packed);
    }

    private Mesh createArenaSurfaceMesh() {
        List<Float> packed = new ArrayList<>();
        addVertex(packed, -0.5f, 0f, -0.5f, 0f, 1f, 0f, 1f, 0f);
        addVertex(packed, 0.5f, 0f, -0.5f, 1f, 1f, 0f, 1f, 0f);
        addVertex(packed, 0.5f, 0f, 0.5f, 1f, 0f, 0f, 1f, 0f);

        addVertex(packed, -0.5f, 0f, -0.5f, 0f, 1f, 0f, 1f, 0f);
        addVertex(packed, 0.5f, 0f, 0.5f, 1f, 0f, 0f, 1f, 0f);
        addVertex(packed, -0.5f, 0f, 0.5f, 0f, 0f, 0f, 1f, 0f);
        return buildMeshFromPacked(packed);
    }

    private Mesh createSphereMesh(int lonSegments, int latSegments) {
        List<Float> packed = new ArrayList<>();
        for (int lat = 0; lat < latSegments; lat++) {
            float v0 = lat / (float) latSegments;
            float v1 = (lat + 1) / (float) latSegments;
            float phi0 = (float) (Math.PI * (v0 - 0.5f));
            float phi1 = (float) (Math.PI * (v1 - 0.5f));
            for (int lon = 0; lon < lonSegments; lon++) {
                float u0 = lon / (float) lonSegments;
                float u1 = (lon + 1) / (float) lonSegments;
                float theta0 = (float) (Math.PI * 2.0 * u0);
                float theta1 = (float) (Math.PI * 2.0 * u1);

                float[] p00 = spherePoint(theta0, phi0);
                float[] p10 = spherePoint(theta1, phi0);
                float[] p11 = spherePoint(theta1, phi1);
                float[] p01 = spherePoint(theta0, phi1);

                addVertex(packed, p00[0], p00[1], p00[2], u0, v0, p00[0], p00[1], p00[2]);
                addVertex(packed, p10[0], p10[1], p10[2], u1, v0, p10[0], p10[1], p10[2]);
                addVertex(packed, p11[0], p11[1], p11[2], u1, v1, p11[0], p11[1], p11[2]);

                addVertex(packed, p00[0], p00[1], p00[2], u0, v0, p00[0], p00[1], p00[2]);
                addVertex(packed, p11[0], p11[1], p11[2], u1, v1, p11[0], p11[1], p11[2]);
                addVertex(packed, p01[0], p01[1], p01[2], u0, v1, p01[0], p01[1], p01[2]);
            }
        }
        return buildMeshFromPacked(packed);
    }

    private float[] spherePoint(float theta, float phi) {
        float cosPhi = (float) Math.cos(phi);
        return new float[] {
                cosPhi * (float) Math.cos(theta),
                (float) Math.sin(phi),
                cosPhi * (float) Math.sin(theta)
        };
    }

    private void addVertex(List<Float> packed, float px, float py, float pz, float u, float v, float nx, float ny, float nz) {
        packed.add(px);
        packed.add(py);
        packed.add(pz);
        packed.add(u);
        packed.add(v);
        packed.add(nx);
        packed.add(ny);
        packed.add(nz);
    }

    private Mesh buildMeshFromPacked(List<Float> packed) {
        float[] data = new float[packed.size()];
        for (int index = 0; index < packed.size(); index++) {
            data[index] = packed.get(index);
        }
        ByteBuffer byteBuffer = ByteBuffer.allocateDirect(data.length * FLOAT_SIZE).order(ByteOrder.nativeOrder());
        FloatBuffer buffer = byteBuffer.asFloatBuffer();
        buffer.put(data).position(0);
        return new Mesh(buffer, data.length / STRIDE_FLOATS);
    }

    private Mesh loadObjMesh(String assetPath) throws IOException {
        List<float[]> positions = new ArrayList<>();
        List<float[]> texCoords = new ArrayList<>();
        List<float[]> normals = new ArrayList<>();
        List<Float> packed = new ArrayList<>();

        try (InputStream inputStream = assetManager.open(assetPath);
             BufferedReader reader = new BufferedReader(new InputStreamReader(inputStream))) {
            String line;
            while ((line = reader.readLine()) != null) {
                line = line.trim();
                if (line.isEmpty() || line.startsWith("#")) {
                    continue;
                }
                String[] parts = line.split("\\s+");
                switch (parts[0]) {
                    case "v":
                        positions.add(new float[] {Float.parseFloat(parts[1]), Float.parseFloat(parts[2]), Float.parseFloat(parts[3])});
                        break;
                    case "vt":
                        texCoords.add(new float[] {Float.parseFloat(parts[1]), 1f - Float.parseFloat(parts[2])});
                        break;
                    case "vn":
                        normals.add(new float[] {Float.parseFloat(parts[1]), Float.parseFloat(parts[2]), Float.parseFloat(parts[3])});
                        break;
                    case "f":
                        for (int tri = 1; tri < parts.length - 2; tri++) {
                            appendFaceVertex(parts[1], positions, texCoords, normals, packed);
                            appendFaceVertex(parts[tri + 1], positions, texCoords, normals, packed);
                            appendFaceVertex(parts[tri + 2], positions, texCoords, normals, packed);
                        }
                        break;
                    default:
                        break;
                }
            }
        }

        float[] data = new float[packed.size()];
        for (int index = 0; index < packed.size(); index++) {
            data[index] = packed.get(index);
        }
        ByteBuffer byteBuffer = ByteBuffer.allocateDirect(data.length * FLOAT_SIZE).order(ByteOrder.nativeOrder());
        FloatBuffer buffer = byteBuffer.asFloatBuffer();
        buffer.put(data).position(0);
        return new Mesh(buffer, data.length / STRIDE_FLOATS);
    }

    private void appendFaceVertex(String token, List<float[]> positions, List<float[]> texCoords, List<float[]> normals, List<Float> packed) {
        String[] indices = token.split("/");
        float[] position = positions.get(Integer.parseInt(indices[0]) - 1);
        float[] texCoord = indices.length > 1 && indices[1].length() > 0 ? texCoords.get(Integer.parseInt(indices[1]) - 1) : new float[] {0f, 0f};
        float[] normal = indices.length > 2 && indices[2].length() > 0 ? normals.get(Integer.parseInt(indices[2]) - 1) : new float[] {0f, 1f, 0f};
        packed.add(position[0]);
        packed.add(position[1]);
        packed.add(position[2]);
        packed.add(texCoord[0]);
        packed.add(texCoord[1]);
        packed.add(normal[0]);
        packed.add(normal[1]);
        packed.add(normal[2]);
    }

    private int createTexture(String textureId) {
        Bitmap bitmap = createTextureBitmap(textureId);
        int[] textureIds = new int[1];
        GLES20.glGenTextures(1, textureIds, 0);
        GLES20.glBindTexture(GLES20.GL_TEXTURE_2D, textureIds[0]);
        GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_MIN_FILTER, GLES20.GL_LINEAR);
        GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_MAG_FILTER, GLES20.GL_LINEAR);
        int wrapMode = isArenaTexture(textureId) ? GLES20.GL_CLAMP_TO_EDGE : GLES20.GL_REPEAT;
        GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_WRAP_S, wrapMode);
        GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_WRAP_T, wrapMode);
        GLUtils.texImage2D(GLES20.GL_TEXTURE_2D, 0, bitmap, 0);
        bitmap.recycle();
        return textureIds[0];
    }

    private boolean isArenaTexture(String textureId) {
        return textureId != null && textureId.endsWith("_field") || "dirkodds_quickthings_course".equals(textureId);
    }

    private String fieldTextureId() {
        switch (scenario.sport) {
            case "multisport":
                return "dirkodds_multisport_field";
            case "quickthings":
                return "dirkodds_quickthings_course";
            case "hockey":
                return "dirkodds_hockey_field";
            case "basketball":
                return "dirkodds_basketball_field";
            case "baseball":
                return "dirkodds_baseball_field";
            default:
                return "dirkodds_football_field";
        }
    }

    private Bitmap createTextureBitmap(String textureId) {
        Bitmap bitmap = Bitmap.createBitmap(256, 256, Bitmap.Config.ARGB_8888);
        Canvas canvas = new Canvas(bitmap);
        Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
        Paint linePaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        Paint textPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        textPaint.setColor(Color.argb(225, 245, 247, 250));
        textPaint.setTextSize(24f);
        textPaint.setFakeBoldText(true);

        if ("dirkodds_multisport_field".equals(textureId)) {
            paint.setShader(new LinearGradient(0f, 0f, 256f, 256f, Color.rgb(20, 52, 56), Color.rgb(24, 24, 54), Shader.TileMode.CLAMP));
            canvas.drawRect(0f, 0f, 256f, 256f, paint);
            paint.setShader(null);
            drawPastelPaperOverlay(canvas, Color.argb(26, 255, 242, 214), Color.argb(34, 18, 26, 42));
            drawArenaSheen(canvas, Color.argb(42, 255, 255, 255), Color.argb(128, 4, 8, 16));
            linePaint.setColor(Color.argb(180, 230, 242, 248));
            linePaint.setStrokeWidth(4f);
            canvas.drawRect(18f, 18f, 238f, 238f, linePaint);
            canvas.drawLine(128f, 18f, 128f, 238f, linePaint);
            linePaint.setColor(Color.argb(170, 45, 205, 255));
            canvas.drawCircle(128f, 128f, 30f, linePaint);
            linePaint.setColor(Color.argb(170, 255, 178, 76));
            canvas.drawCircle(74f, 74f, 16f, linePaint);
            canvas.drawCircle(182f, 182f, 16f, linePaint);
            linePaint.setColor(Color.argb(170, 207, 34, 48));
            canvas.drawLine(54f, 36f, 54f, 220f, linePaint);
            canvas.drawLine(202f, 36f, 202f, 220f, linePaint);
            drawFieldShadow(canvas, Color.argb(120, 8, 12, 18));
            drawDiagonalDecals(canvas, Color.argb(24, 99, 213, 255), Color.argb(20, 255, 108, 174));
            drawBannerChip(canvas, 20f, 20f, 148f, 28f, "MX-4");
        } else if ("dirkodds_quickthings_course".equals(textureId)) {
            paint.setShader(new LinearGradient(0f, 0f, 256f, 256f, Color.rgb(5, 9, 26), Color.rgb(24, 16, 48), Shader.TileMode.CLAMP));
            canvas.drawRect(0f, 0f, 256f, 256f, paint);
            paint.setShader(null);
            drawPastelPaperOverlay(canvas, Color.argb(30, 166, 214, 255), Color.argb(40, 18, 8, 36));
            drawArenaSheen(canvas, Color.argb(28, 148, 225, 255), Color.argb(156, 3, 6, 18));
            drawDiagonalDecals(canvas, Color.argb(32, 94, 234, 255), Color.argb(26, 255, 124, 189));
            linePaint.setColor(Color.argb(180, 229, 245, 255));
            linePaint.setStrokeWidth(4f);
            canvas.drawCircle(128f, 128f, 58f, linePaint);
            canvas.drawCircle(128f, 128f, 92f, linePaint);
            canvas.drawCircle(128f, 128f, 122f, linePaint);
            drawFieldShadow(canvas, Color.argb(132, 8, 10, 20));
            drawBannerChip(canvas, 20f, 20f, 142f, 28f, "QT-709");
        } else if ("dirkodds_quickthings_card".equals(textureId)) {
            paint.setShader(new LinearGradient(0f, 0f, 256f, 256f, Color.rgb(250, 241, 214), Color.rgb(238, 202, 118), Shader.TileMode.CLAMP));
            canvas.drawRoundRect(new RectF(34f, 18f, 222f, 238f), 26f, 26f, paint);
            paint.setShader(null);
            linePaint.setColor(Color.rgb(19, 24, 39));
            linePaint.setStrokeWidth(5f);
            canvas.drawRoundRect(new RectF(34f, 18f, 222f, 238f), 26f, 26f, linePaint);
            textPaint.setColor(Color.rgb(16, 20, 34));
            textPaint.setTextSize(28f);
            canvas.drawText("52", 50f, 58f, textPaint);
            textPaint.setTextSize(34f);
            canvas.drawText("QK", 102f, 134f, textPaint);
            textPaint.setTextSize(22f);
            canvas.drawText("BREAM", 86f, 182f, textPaint);
            canvas.drawText("SYNC", 94f, 210f, textPaint);
        } else if ("dirkodds_quickthings_portal".equals(textureId)) {
            paint.setShader(new LinearGradient(0f, 0f, 256f, 256f, Color.rgb(79, 212, 255), Color.rgb(255, 99, 190), Shader.TileMode.CLAMP));
            canvas.drawCircle(128f, 128f, 92f, paint);
            paint.setShader(null);
            paint.setColor(Color.rgb(8, 10, 20));
            canvas.drawCircle(128f, 128f, 52f, paint);
            linePaint.setColor(Color.argb(220, 255, 240, 200));
            linePaint.setStrokeWidth(6f);
            canvas.drawCircle(128f, 128f, 92f, linePaint);
            canvas.drawCircle(128f, 128f, 66f, linePaint);
        } else if ("dirkodds_heat_haze".equals(textureId)) {
            Paint heatPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
            heatPaint.setShader(new LinearGradient(0f, 0f, 256f, 256f,
                    Color.argb(0, 255, 196, 98),
                    Color.argb(64, 255, 116, 42),
                    Shader.TileMode.CLAMP));
            Path heatPath = new Path();
            heatPath.moveTo(12f, 186f);
            heatPath.cubicTo(58f, 132f, 94f, 210f, 132f, 150f);
            heatPath.cubicTo(174f, 94f, 214f, 176f, 244f, 108f);
            heatPath.lineTo(244f, 212f);
            heatPath.cubicTo(198f, 246f, 146f, 214f, 92f, 238f);
            heatPath.cubicTo(56f, 224f, 28f, 228f, 12f, 186f);
            heatPath.close();
            canvas.drawPath(heatPath, heatPaint);

            heatPaint.setShader(new LinearGradient(0f, 256f, 256f, 32f,
                    Color.argb(0, 255, 222, 138),
                    Color.argb(84, 255, 88, 26),
                    Shader.TileMode.CLAMP));
            Path streak = new Path();
            streak.moveTo(20f, 146f);
            streak.cubicTo(72f, 104f, 106f, 166f, 146f, 116f);
            streak.cubicTo(180f, 76f, 216f, 138f, 236f, 92f);
            streak.lineTo(236f, 134f);
            streak.cubicTo(192f, 170f, 156f, 132f, 118f, 172f);
            streak.cubicTo(82f, 194f, 46f, 168f, 20f, 196f);
            streak.close();
            canvas.drawPath(streak, heatPaint);

            Paint sparkPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
            sparkPaint.setColor(Color.argb(98, 255, 226, 162));
            for (int index = 0; index < 7; index++) {
                float x = 34f + index * 30f;
                canvas.drawCircle(x, 88f + (index % 3) * 18f, 4f + (index % 2), sparkPaint);
            }
        } else if ("dirkodds_fog_volume".equals(textureId)) {
            Paint fogPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
            fogPaint.setShader(new LinearGradient(0f, 36f, 0f, 236f,
                    Color.argb(0, 255, 248, 234),
                    Color.argb(90, 244, 236, 225),
                    Shader.TileMode.CLAMP));
            canvas.drawOval(new RectF(18f, 54f, 238f, 214f), fogPaint);
            drawPastelPaperOverlay(canvas, Color.argb(16, 255, 255, 255), Color.argb(10, 184, 160, 148));
            Paint wisps = new Paint(Paint.ANTI_ALIAS_FLAG);
            wisps.setColor(Color.argb(54, 255, 255, 255));
            wisps.setStrokeWidth(6f);
            for (int index = 0; index < 5; index++) {
                float y = 88f + index * 22f;
                canvas.drawArc(new RectF(22f + index * 14f, y - 12f, 188f + index * 8f, y + 22f), 196f, 122f, false, wisps);
            }
        } else if ("dirkodds_light_ray".equals(textureId)) {
            Paint rayPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
            Path ray = new Path();
            ray.moveTo(98f, 24f);
            ray.lineTo(158f, 24f);
            ray.lineTo(216f, 236f);
            ray.lineTo(44f, 236f);
            ray.close();
            rayPaint.setShader(new LinearGradient(128f, 24f, 128f, 236f,
                    Color.argb(126, 255, 240, 182),
                    Color.argb(0, 255, 232, 194),
                    Shader.TileMode.CLAMP));
            canvas.drawPath(ray, rayPaint);
            drawPastelPaperOverlay(canvas, Color.argb(18, 255, 255, 248), Color.argb(8, 120, 96, 74));
        } else if ("dirkodds_crowd_band".equals(textureId)) {
            paint.setShader(new LinearGradient(0f, 0f, 0f, 256f, Color.rgb(18, 23, 36), Color.rgb(42, 16, 24), Shader.TileMode.CLAMP));
            canvas.drawRect(0f, 0f, 256f, 256f, paint);
            paint.setShader(null);
            drawPastelPaperOverlay(canvas, Color.argb(18, 255, 216, 194), Color.argb(18, 22, 18, 28));
            Paint silhouettePaint = new Paint(Paint.ANTI_ALIAS_FLAG);
            silhouettePaint.setColor(Color.argb(196, 10, 12, 20));
            for (int index = 0; index < 11; index++) {
                float x = 14f + index * 22f;
                canvas.drawRect(x, 92f + (index % 3) * 8f, x + 9f, 182f, silhouettePaint);
                canvas.drawCircle(x + 4.5f, 82f + (index % 2) * 8f, 9f, silhouettePaint);
            }
            Paint rimPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
            rimPaint.setShader(new LinearGradient(0f, 28f, 256f, 118f, Color.argb(146, 255, 185, 94), Color.argb(26, 255, 98, 52), Shader.TileMode.CLAMP));
            canvas.drawRect(18f, 24f, 238f, 58f, rimPaint);
            Paint tickPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
            tickPaint.setColor(Color.argb(112, 255, 234, 196));
            tickPaint.setStrokeWidth(3f);
            for (int index = 0; index < 9; index++) {
                float x = 32f + index * 24f;
                canvas.drawLine(x, 34f, x, 54f, tickPaint);
            }
        } else if ("dirkodds_shadow".equals(textureId)) {
            Paint shadowPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
            shadowPaint.setShader(new android.graphics.RadialGradient(
                    128f,
                    128f,
                    110f,
                    new int[] {Color.argb(92, 6, 8, 12), Color.argb(46, 8, 10, 14), Color.argb(0, 8, 10, 14)},
                    new float[] {0f, 0.58f, 1f},
                    Shader.TileMode.CLAMP));
            canvas.drawCircle(128f, 128f, 110f, shadowPaint);
        } else if ("dirkodds_football_field".equals(textureId)) {
            paint.setShader(new LinearGradient(0f, 0f, 0f, 256f, Color.rgb(28, 89, 56), Color.rgb(18, 63, 42), Shader.TileMode.CLAMP));
            canvas.drawRect(0f, 0f, 256f, 256f, paint);
            paint.setShader(null);
            drawPastelPaperOverlay(canvas, Color.argb(24, 232, 255, 234), Color.argb(26, 20, 36, 28));
            drawTurfBands(canvas, Color.argb(34, 80, 128, 84), Color.argb(18, 18, 52, 34));
            drawArenaSheen(canvas, Color.argb(18, 245, 255, 250), Color.argb(110, 12, 24, 20));
            linePaint.setColor(Color.argb(180, 238, 242, 245));
            linePaint.setStrokeWidth(4f);
            canvas.drawRect(18f, 18f, 238f, 238f, linePaint);
            canvas.drawLine(128f, 18f, 128f, 238f, linePaint);
            canvas.drawCircle(128f, 128f, 34f, linePaint);
            drawFootballHashes(canvas, linePaint);
            drawFieldShadow(canvas, Color.argb(124, 10, 18, 14));
            drawDiagonalDecals(canvas, Color.argb(34, 52, 255, 214), Color.argb(26, 255, 86, 178));
            drawBannerChip(canvas, 22f, 22f, 88f, 26f, "FB");
        } else if ("dirkodds_basketball_field".equals(textureId)) {
            paint.setShader(new LinearGradient(0f, 0f, 0f, 256f, Color.rgb(177, 128, 84), Color.rgb(128, 82, 51), Shader.TileMode.CLAMP));
            canvas.drawRect(0f, 0f, 256f, 256f, paint);
            paint.setShader(null);
            drawPastelPaperOverlay(canvas, Color.argb(22, 255, 240, 210), Color.argb(24, 38, 24, 18));
            drawHardwoodPlanks(canvas, Color.argb(52, 92, 52, 28));
            drawArenaSheen(canvas, Color.argb(30, 255, 246, 231), Color.argb(116, 36, 20, 12));
            linePaint.setColor(Color.argb(200, 79, 46, 18));
            linePaint.setStrokeWidth(5f);
            canvas.drawRect(16f, 16f, 240f, 240f, linePaint);
            canvas.drawLine(128f, 16f, 128f, 240f, linePaint);
            canvas.drawCircle(128f, 128f, 28f, linePaint);
            drawFieldShadow(canvas, Color.argb(104, 38, 21, 12));
            drawDiagonalDecals(canvas, Color.argb(28, 255, 173, 51), Color.argb(32, 255, 91, 129));
            drawBannerChip(canvas, 22f, 22f, 88f, 26f, "BK");
        } else if ("dirkodds_hockey_field".equals(textureId)) {
            paint.setShader(new LinearGradient(0f, 0f, 0f, 256f, Color.rgb(230, 241, 250), Color.rgb(196, 215, 228), Shader.TileMode.CLAMP));
            canvas.drawRoundRect(new RectF(16f, 16f, 240f, 240f), 48f, 48f, paint);
            paint.setShader(null);
            drawPastelPaperOverlay(canvas, Color.argb(18, 255, 255, 255), Color.argb(22, 92, 112, 124));
            drawIceScuffs(canvas, Color.argb(26, 114, 144, 166));
            drawArenaSheen(canvas, Color.argb(34, 255, 255, 255), Color.argb(96, 82, 104, 118));
            linePaint.setColor(Color.argb(215, 203, 34, 48));
            linePaint.setStrokeWidth(6f);
            canvas.drawLine(128f, 20f, 128f, 236f, linePaint);
            linePaint.setColor(Color.argb(215, 27, 108, 180));
            canvas.drawLine(72f, 20f, 72f, 236f, linePaint);
            canvas.drawLine(184f, 20f, 184f, 236f, linePaint);
            linePaint.setColor(Color.argb(210, 203, 34, 48));
            linePaint.setStrokeWidth(4f);
            canvas.drawCircle(128f, 128f, 24f, linePaint);
            canvas.drawCircle(72f, 72f, 18f, linePaint);
            canvas.drawCircle(72f, 184f, 18f, linePaint);
            canvas.drawCircle(184f, 72f, 18f, linePaint);
            canvas.drawCircle(184f, 184f, 18f, linePaint);
            linePaint.setColor(Color.argb(180, 235, 243, 249));
            canvas.drawRoundRect(new RectF(16f, 16f, 240f, 240f), 48f, 48f, linePaint);
            drawFieldShadow(canvas, Color.argb(90, 70, 84, 96));
            drawDiagonalDecals(canvas, Color.argb(16, 76, 156, 255), Color.argb(14, 255, 82, 124));
            drawBannerChip(canvas, 22f, 22f, 88f, 26f, "HK");
        } else if ("dirkodds_baseball_field".equals(textureId)) {
            canvas.drawColor(Color.rgb(42, 92, 58));
            drawPastelPaperOverlay(canvas, Color.argb(22, 248, 244, 222), Color.argb(24, 22, 34, 28));
            drawTurfBands(canvas, Color.argb(24, 92, 138, 80), Color.argb(12, 18, 52, 34));
            paint.setColor(Color.rgb(174, 132, 82));
            RectF diamond = new RectF(42f, 42f, 214f, 214f);
            canvas.save();
            canvas.rotate(45f, 128f, 128f);
            canvas.drawRect(diamond, paint);
            canvas.restore();
            drawArenaSheen(canvas, Color.argb(18, 248, 246, 226), Color.argb(118, 18, 28, 20));
            linePaint.setColor(Color.argb(190, 238, 240, 236));
            linePaint.setStrokeWidth(4f);
            canvas.drawLine(128f, 38f, 42f, 124f, linePaint);
            canvas.drawLine(128f, 38f, 214f, 124f, linePaint);
            canvas.drawLine(42f, 124f, 128f, 210f, linePaint);
            canvas.drawLine(214f, 124f, 128f, 210f, linePaint);
            drawBaseballOutfieldArc(canvas, linePaint);
            drawFieldShadow(canvas, Color.argb(118, 10, 18, 14));
            drawDiagonalDecals(canvas, Color.argb(26, 34, 227, 246), Color.argb(24, 255, 185, 77));
            drawBannerChip(canvas, 22f, 22f, 88f, 26f, "BS");
        } else if ("dirkodds_home".equals(textureId) || "dirkodds_away".equals(textureId)) {
            int teamColor = "dirkodds_home".equals(textureId) ? scenario.homeColor : scenario.awayColor;
            canvas.drawColor(Color.TRANSPARENT);
            paint.setShader(new LinearGradient(0f, 0f, 0f, 256f, lighten(teamColor, 0.2f), darken(teamColor, 0.24f), Shader.TileMode.CLAMP));
            canvas.drawRoundRect(new RectF(54f, 20f, 202f, 236f), 28f, 28f, paint);
            paint.setShader(null);
            paint.setColor(Color.argb(42, 255, 255, 255));
            canvas.drawRoundRect(new RectF(70f, 34f, 186f, 56f), 10f, 10f, paint);
            canvas.drawRoundRect(new RectF(70f, 170f, 186f, 190f), 10f, 10f, paint);
            paint.setColor(Color.argb(245, 244, 237, 228));
            canvas.drawCircle(128f, 66f, 30f, paint);
            paint.setColor(Color.argb(240, 24, 27, 32));
            canvas.drawRect(105f, 96f, 151f, 196f, paint);
            canvas.drawRect(82f, 114f, 174f, 136f, paint);
            drawTeamChevron(canvas, teamColor);
            DirkOddsScenario.TeamIdentity identity = "dirkodds_home".equals(textureId) ? scenario.homeIdentity : scenario.awayIdentity;
            canvas.drawText(identity.shortMark(), 28f, 244f, textPaint);
        } else if ("dirkodds_home_sideline".equals(textureId) || "dirkodds_away_sideline".equals(textureId)) {
            boolean home = "dirkodds_home_sideline".equals(textureId);
            DirkOddsScenario.TeamIdentity identity = home ? scenario.homeIdentity : scenario.awayIdentity;
            int teamColor = home ? scenario.homeColor : scenario.awayColor;
            int rivalColor = home ? scenario.awayColor : scenario.homeColor;
            drawSidelineTexture(canvas, paint, linePaint, textPaint, identity, teamColor, rivalColor);
        } else if ("dirkodds_focus".equals(textureId)) {
            paint.setShader(new LinearGradient(0f, 0f, 256f, 256f, Color.rgb(246, 189, 96), Color.rgb(244, 96, 54), Shader.TileMode.CLAMP));
            canvas.drawRoundRect(new RectF(18f, 18f, 238f, 238f), 44f, 44f, paint);
            paint.setShader(null);
            linePaint.setColor(Color.argb(230, 255, 246, 214));
            linePaint.setStrokeWidth(6f);
            canvas.drawCircle(128f, 128f, 52f, linePaint);
            linePaint.setStrokeWidth(10f);
            canvas.drawLine(46f, 128f, 84f, 128f, linePaint);
            canvas.drawLine(172f, 128f, 210f, 128f, linePaint);
            canvas.drawLine(128f, 46f, 128f, 84f, linePaint);
            canvas.drawLine(128f, 172f, 128f, 210f, linePaint);
            canvas.drawText("QTE", 86f, 140f, textPaint);
        } else {
            paint.setShader(new LinearGradient(0f, 0f, 0f, 256f, Color.rgb(80, 88, 104), Color.rgb(42, 48, 63), Shader.TileMode.CLAMP));
            canvas.drawRect(0f, 0f, 256f, 256f, paint);
            paint.setShader(null);
            linePaint.setColor(Color.argb(180, 213, 223, 232));
            linePaint.setStrokeWidth(4f);
            canvas.drawRect(26f, 26f, 230f, 230f, linePaint);
            canvas.drawText("DIRK", 72f, 140f, textPaint);
        }
        return bitmap;
    }

    private void drawDiagonalDecals(Canvas canvas, int firstColor, int secondColor) {
        Paint stripePaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        stripePaint.setStyle(Paint.Style.FILL);
        stripePaint.setColor(firstColor);
        for (int start = -180; start < 320; start += 48) {
            canvas.save();
            canvas.rotate(-24f, 128f, 128f);
            canvas.drawRect(start, -16f, start + 18f, 288f, stripePaint);
            canvas.restore();
        }
        stripePaint.setColor(secondColor);
        for (int start = -156; start < 344; start += 64) {
            canvas.save();
            canvas.rotate(18f, 128f, 128f);
            canvas.drawRect(start, -16f, start + 10f, 288f, stripePaint);
            canvas.restore();
        }
    }

    private void drawPastelPaperOverlay(Canvas canvas, int lightTone, int darkTone) {
        Paint washPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        washPaint.setColor(lightTone);
        for (int index = 0; index < 9; index++) {
            float inset = 10f + index * 12f;
            canvas.drawOval(new RectF(inset, 18f + (index % 3) * 8f, 256f - inset * 0.78f, 246f - (index % 4) * 10f), washPaint);
        }

        Paint toothPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        toothPaint.setColor(darkTone);
        toothPaint.setStrokeWidth(1.6f);
        for (int x = 14; x < 248; x += 18) {
            for (int y = 18; y < 242; y += 20) {
                float dx = (float) Math.sin((x + y) * 0.08f) * 6f;
                canvas.drawLine(x, y, x + dx, y + 6f, toothPaint);
            }
        }
    }

    private void drawArenaSheen(Canvas canvas, int highlightColor, int shadowColor) {
        Paint sheenPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        sheenPaint.setShader(new LinearGradient(28f, 24f, 224f, 220f, highlightColor, Color.TRANSPARENT, Shader.TileMode.CLAMP));
        canvas.drawRect(0f, 0f, 256f, 256f, sheenPaint);
        sheenPaint.setShader(new LinearGradient(0f, 200f, 256f, 96f, shadowColor, Color.TRANSPARENT, Shader.TileMode.CLAMP));
        canvas.drawRect(0f, 0f, 256f, 256f, sheenPaint);
    }

    private void drawFieldShadow(Canvas canvas, int shadowColor) {
        Paint shadowPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        shadowPaint.setColor(shadowColor);
        shadowPaint.setStyle(Paint.Style.STROKE);
        shadowPaint.setStrokeWidth(18f);
        canvas.drawRoundRect(new RectF(20f, 20f, 236f, 236f), 34f, 34f, shadowPaint);
    }

    private void drawTurfBands(Canvas canvas, int firstColor, int secondColor) {
        Paint turfPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        for (int band = 0; band < 8; band++) {
            turfPaint.setColor(band % 2 == 0 ? firstColor : secondColor);
            canvas.drawRect(16f, 18f + band * 28f, 240f, 46f + band * 28f, turfPaint);
        }
    }

    private void drawFootballHashes(Canvas canvas, Paint linePaint) {
        for (int row = 0; row < 9; row++) {
            float y = 30f + row * 24f;
            canvas.drawLine(92f, y, 112f, y, linePaint);
            canvas.drawLine(144f, y, 164f, y, linePaint);
        }
    }

    private void drawHardwoodPlanks(Canvas canvas, int seamColor) {
        Paint seamPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        seamPaint.setColor(seamColor);
        seamPaint.setStrokeWidth(2f);
        for (int x = 24; x < 232; x += 20) {
            canvas.drawLine(x, 16f, x, 240f, seamPaint);
        }
        for (int y = 42; y < 240; y += 36) {
            canvas.drawLine(16f, y, 240f, y, seamPaint);
        }
    }

    private void drawIceScuffs(Canvas canvas, int scuffColor) {
        Paint scuffPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        scuffPaint.setColor(scuffColor);
        scuffPaint.setStrokeWidth(2.6f);
        for (int index = 0; index < 10; index++) {
            float left = 26f + index * 18f;
            canvas.drawLine(left, 60f + (index % 3) * 22f, left + 42f, 34f + (index % 4) * 28f, scuffPaint);
            canvas.drawLine(left + 12f, 196f - (index % 4) * 18f, left + 46f, 164f - (index % 3) * 20f, scuffPaint);
        }
    }

    private void drawBaseballOutfieldArc(Canvas canvas, Paint linePaint) {
        RectF outfieldArc = new RectF(26f, 26f, 230f, 230f);
        canvas.drawArc(outfieldArc, 215f, 110f, false, linePaint);
    }

    private void drawBannerChip(Canvas canvas, float left, float top, float width, float height, String text) {
        Paint chipPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        chipPaint.setColor(Color.argb(192, 10, 15, 28));
        RectF chip = new RectF(left, top, left + width, top + height);
        canvas.drawRoundRect(chip, 12f, 12f, chipPaint);
        chipPaint.setStyle(Paint.Style.STROKE);
        chipPaint.setStrokeWidth(3f);
        chipPaint.setColor(Color.argb(214, 108, 242, 255));
        canvas.drawRoundRect(chip, 12f, 12f, chipPaint);
        Paint chipText = new Paint(Paint.ANTI_ALIAS_FLAG);
        chipText.setColor(Color.rgb(245, 247, 255));
        chipText.setTextSize(20f);
        chipText.setFakeBoldText(true);
        canvas.drawText(text, left + 18f, top + 19f, chipText);
    }

    private void drawTeamChevron(Canvas canvas, int teamColor) {
        Paint chevronPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        chevronPaint.setColor(lighten(teamColor, 0.38f));
        Path path = new Path();
        path.moveTo(128f, 92f);
        path.lineTo(156f, 116f);
        path.lineTo(142f, 116f);
        path.lineTo(168f, 140f);
        path.lineTo(146f, 140f);
        path.lineTo(118f, 114f);
        path.close();
        canvas.drawPath(path, chevronPaint);
    }

    private void drawSidelineTexture(
            Canvas canvas,
            Paint paint,
            Paint linePaint,
            Paint textPaint,
            DirkOddsScenario.TeamIdentity identity,
            int teamColor,
            int rivalColor) {
        paint.setShader(new LinearGradient(0f, 0f, 256f, 256f, darken(teamColor, 0.18f), lighten(teamColor, 0.18f), Shader.TileMode.CLAMP));
        canvas.drawRect(0f, 0f, 256f, 256f, paint);
        paint.setShader(null);
        drawDiagonalDecals(canvas, Color.argb(34, Color.red(rivalColor), Color.green(rivalColor), Color.blue(rivalColor)), Color.argb(24, 255, 255, 255));

        Paint panelPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        panelPaint.setColor(Color.argb(208, 11, 15, 26));
        canvas.drawRoundRect(new RectF(22f, 22f, 234f, 234f), 26f, 26f, panelPaint);

        linePaint.setStyle(Paint.Style.STROKE);
        linePaint.setColor(lighten(identity.accentColor, 0.12f));
        linePaint.setStrokeWidth(4f);
        canvas.drawRoundRect(new RectF(22f, 22f, 234f, 234f), 26f, 26f, linePaint);

        Paint sigilPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        sigilPaint.setColor(Color.rgb(244, 247, 255));
        sigilPaint.setTextSize(54f);
        sigilPaint.setFakeBoldText(true);
        canvas.drawText(identity.shortMark(), 34f, 78f, sigilPaint);

        textPaint.setTextSize(20f);
        canvas.drawText(trim(identity.mascotName.toUpperCase(), 14), 34f, 118f, textPaint);
        textPaint.setTextSize(18f);
        canvas.drawText(trim(identity.mascotType.toUpperCase(), 18), 34f, 144f, textPaint);
        canvas.drawText(trim(identity.bannerLine.toUpperCase(), 22), 34f, 186f, textPaint);
        textPaint.setTextSize(16f);
        canvas.drawText(trim(identity.cheerNote.toUpperCase(), 24), 34f, 214f, textPaint);
    }

    private int lighten(int color, float amount) {
        int r = (int) (Color.red(color) + (255 - Color.red(color)) * amount);
        int g = (int) (Color.green(color) + (255 - Color.green(color)) * amount);
        int b = (int) (Color.blue(color) + (255 - Color.blue(color)) * amount);
        return Color.rgb(r, g, b);
    }

    private int darken(int color, float amount) {
        int r = (int) (Color.red(color) * (1f - amount));
        int g = (int) (Color.green(color) * (1f - amount));
        int b = (int) (Color.blue(color) * (1f - amount));
        return Color.rgb(r, g, b);
    }

    private String shortLabel(String teamName) {
        if (teamName == null || teamName.isEmpty()) {
            return "TEAM";
        }
        String[] words = teamName.split("\\s+");
        return words[0].toUpperCase();
    }

    private String trim(String value, int maxLength) {
        if (value == null) {
            return "";
        }
        if (value.length() <= maxLength) {
            return value;
        }
        return value.substring(0, Math.max(0, maxLength - 3)) + "...";
    }

    private float saturate(float value) {
        return Math.max(0f, Math.min(1f, value));
    }

    private int createShader(int type, String source) {
        int shader = GLES20.glCreateShader(type);
        GLES20.glShaderSource(shader, source);
        GLES20.glCompileShader(shader);
        int[] compiled = new int[1];
        GLES20.glGetShaderiv(shader, GLES20.GL_COMPILE_STATUS, compiled, 0);
        if (compiled[0] == 0) {
            String log = GLES20.glGetShaderInfoLog(shader);
            GLES20.glDeleteShader(shader);
            throw new RuntimeException("Shader compile failed: " + log);
        }
        return shader;
    }

    private int createProgram(String vertexSource, String fragmentSource) {
        int vertexShader = createShader(GLES20.GL_VERTEX_SHADER, vertexSource);
        int fragmentShader = createShader(GLES20.GL_FRAGMENT_SHADER, fragmentSource);
        int shaderProgram = GLES20.glCreateProgram();
        GLES20.glAttachShader(shaderProgram, vertexShader);
        GLES20.glAttachShader(shaderProgram, fragmentShader);
        GLES20.glLinkProgram(shaderProgram);
        int[] linked = new int[1];
        GLES20.glGetProgramiv(shaderProgram, GLES20.GL_LINK_STATUS, linked, 0);
        if (linked[0] == 0) {
            String log = GLES20.glGetProgramInfoLog(shaderProgram);
            GLES20.glDeleteProgram(shaderProgram);
            throw new RuntimeException("Program link failed: " + log);
        }
        return shaderProgram;
    }

    private static final class Mesh {
        final FloatBuffer vertices;
        final int vertexCount;

        Mesh(FloatBuffer vertices, int vertexCount) {
            this.vertices = vertices;
            this.vertexCount = vertexCount;
        }
    }

    private static final String VERTEX_SHADER =
            "uniform mat4 uMvpMatrix;\n" +
            "uniform mat4 uModelMatrix;\n" +
            "uniform vec3 uLightDir;\n" +
            "uniform vec3 uCameraPos;\n" +
            "attribute vec3 aPosition;\n" +
            "attribute vec2 aTexCoord;\n" +
            "attribute vec3 aNormal;\n" +
            "varying vec2 vTexCoord;\n" +
            "varying float vLight;\n" +
            "varying float vRim;\n" +
            "void main() {\n" +
            "  vec3 worldPos = (uModelMatrix * vec4(aPosition, 1.0)).xyz;\n" +
            "  vec3 normal = normalize((uModelMatrix * vec4(aNormal, 0.0)).xyz);\n" +
            "  vec3 viewDir = normalize(uCameraPos - worldPos);\n" +
            "  vLight = max(dot(normal, normalize(uLightDir)), 0.0) * 0.65 + 0.35;\n" +
            "  vRim = pow(1.0 - max(dot(normal, viewDir), 0.0), 2.2);\n" +
            "  vTexCoord = aTexCoord;\n" +
            "  gl_Position = uMvpMatrix * vec4(aPosition, 1.0);\n" +
            "}";

    private static final String FRAGMENT_SHADER =
            "precision mediump float;\n" +
            "uniform sampler2D uTexture;\n" +
            "varying vec2 vTexCoord;\n" +
            "varying float vLight;\n" +
            "varying float vRim;\n" +
            "void main() {\n" +
            "  vec4 color = texture2D(uTexture, vTexCoord);\n" +
            "  vec3 rimTint = vec3(1.0, 0.72, 0.48) * vRim * 0.22;\n" +
            "  gl_FragColor = vec4(color.rgb * vLight + rimTint, color.a);\n" +
            "}";
}
