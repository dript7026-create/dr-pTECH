package com.urbden.game;

import android.content.res.AssetManager;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.LinearGradient;
import android.graphics.Paint;
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

    private Mesh planeMesh;
    private Mesh standeeMesh;
    private Mesh blockMesh;
    private int program;
    private int positionHandle;
    private int texCoordHandle;
    private int normalHandle;
    private int mvpHandle;
    private int modelHandle;
    private int lightHandle;
    private int textureHandle;
    private int fieldTextureId;
    private int homeTextureId;
    private int awayTextureId;
    private int neutralTextureId;
    private int focusTextureId;
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
        textureHandle = GLES20.glGetUniformLocation(program, "uTexture");

        try {
            planeMesh = loadObjMesh("playback/meshes/street_plane.obj");
            standeeMesh = loadObjMesh("playback/meshes/rival_standee.obj");
            blockMesh = loadObjMesh("playback/meshes/courthouse_block.obj");
            fieldTextureId = createTexture(fieldTextureId());
            homeTextureId = createTexture("dirkodds_home");
            awayTextureId = createTexture("dirkodds_away");
            neutralTextureId = createTexture("dirkodds_neutral");
            focusTextureId = createTexture("dirkodds_focus");
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
        if (program == 0 || planeMesh == null || standeeMesh == null || blockMesh == null || state == null) {
            return;
        }

        float orbit = -28f + state.progress * 18f;
        float yawRadians = (float) Math.toRadians(orbit);
        float eyeX = (float) (Math.sin(yawRadians) * 8.8f);
        float eyeY = 4.8f;
        float eyeZ = (float) (Math.cos(yawRadians) * 8.8f);
        Matrix.setLookAtM(viewMatrix, 0, eyeX, eyeY, eyeZ, 0f, 0.8f, 0f, 0f, 1f, 0f);
        Matrix.multiplyMM(viewProjectionMatrix, 0, projectionMatrix, 0, viewMatrix, 0);

        GLES20.glUseProgram(program);
        GLES20.glUniform3f(lightHandle, 0.42f, 0.88f, 0.24f);

        float[] fieldScale = fieldScale();
        drawMesh(planeMesh, fieldTextureId, 0f, 0f, 0f, 0f, 0f, 0f, fieldScale[0], 1f, fieldScale[1]);
        drawMesh(blockMesh, neutralTextureId, -fieldScale[0] * 1.5f, 0.02f, 0f, 0f, 0f, 0f, 0.18f, 0.18f, 0.18f);
        drawMesh(blockMesh, neutralTextureId, fieldScale[0] * 1.5f, 0.02f, 0f, 0f, 180f, 0f, 0.18f, 0.18f, 0.18f);
        drawMesh(blockMesh, focusTextureId, state.focusX, 0.02f, state.focusZ, 0f, state.progress * 720f, 0f, 0.08f, 0.08f + state.pressure * 0.08f, 0.08f);

        int teamSize = scenario.teamSize();
        for (int index = 0; index < teamSize; index++) {
            float[] home = playerPosition(index, true, state);
            float[] away = playerPosition(index, false, state);
            drawMesh(standeeMesh, homeTextureId, home[0], home[1], home[2], 0f, home[3], 0f, 0.34f, 0.42f, 0.34f);
            drawMesh(standeeMesh, awayTextureId, away[0], away[1], away[2], 0f, away[3], 0f, 0.34f, 0.42f, 0.34f);
        }
    }

    public void updateState(DirkOddsMatchState state) {
        currentState = state;
    }

    public void adjustOrbit(float deltaYaw, float deltaPitch) {
    }

    public void adjustZoom(float deltaDistance) {
    }

    private float[] fieldScale() {
        switch (scenario.sport) {
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

    private void drawMesh(Mesh mesh, int textureId, float px, float py, float pz, float rx, float ry, float rz, float sx, float sy, float sz) {
        Matrix.setIdentityM(modelMatrix, 0);
        Matrix.translateM(modelMatrix, 0, px, py, pz);
        Matrix.rotateM(modelMatrix, 0, rx, 1f, 0f, 0f);
        Matrix.rotateM(modelMatrix, 0, ry, 0f, 1f, 0f);
        Matrix.rotateM(modelMatrix, 0, rz, 0f, 0f, 1f);
        Matrix.scaleM(modelMatrix, 0, sx, sy, sz);
        Matrix.multiplyMM(modelViewProjectionMatrix, 0, viewProjectionMatrix, 0, modelMatrix, 0);

        GLES20.glUniformMatrix4fv(mvpHandle, 1, false, modelViewProjectionMatrix, 0);
        GLES20.glUniformMatrix4fv(modelHandle, 1, false, modelMatrix, 0);

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
        GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_WRAP_S, GLES20.GL_REPEAT);
        GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_WRAP_T, GLES20.GL_REPEAT);
        GLUtils.texImage2D(GLES20.GL_TEXTURE_2D, 0, bitmap, 0);
        bitmap.recycle();
        return textureIds[0];
    }

    private String fieldTextureId() {
        switch (scenario.sport) {
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

        if ("dirkodds_football_field".equals(textureId)) {
            paint.setShader(new LinearGradient(0f, 0f, 0f, 256f, Color.rgb(28, 89, 56), Color.rgb(18, 63, 42), Shader.TileMode.CLAMP));
            canvas.drawRect(0f, 0f, 256f, 256f, paint);
            paint.setShader(null);
            linePaint.setColor(Color.argb(180, 238, 242, 245));
            linePaint.setStrokeWidth(4f);
            canvas.drawRect(18f, 18f, 238f, 238f, linePaint);
            canvas.drawLine(128f, 18f, 128f, 238f, linePaint);
            canvas.drawCircle(128f, 128f, 34f, linePaint);
        } else if ("dirkodds_basketball_field".equals(textureId)) {
            paint.setShader(new LinearGradient(0f, 0f, 0f, 256f, Color.rgb(177, 128, 84), Color.rgb(128, 82, 51), Shader.TileMode.CLAMP));
            canvas.drawRect(0f, 0f, 256f, 256f, paint);
            paint.setShader(null);
            linePaint.setColor(Color.argb(200, 79, 46, 18));
            linePaint.setStrokeWidth(5f);
            canvas.drawRect(16f, 16f, 240f, 240f, linePaint);
            canvas.drawLine(128f, 16f, 128f, 240f, linePaint);
            canvas.drawCircle(128f, 128f, 28f, linePaint);
        } else if ("dirkodds_baseball_field".equals(textureId)) {
            canvas.drawColor(Color.rgb(42, 92, 58));
            paint.setColor(Color.rgb(174, 132, 82));
            RectF diamond = new RectF(42f, 42f, 214f, 214f);
            canvas.save();
            canvas.rotate(45f, 128f, 128f);
            canvas.drawRect(diamond, paint);
            canvas.restore();
            linePaint.setColor(Color.argb(190, 238, 240, 236));
            linePaint.setStrokeWidth(4f);
            canvas.drawLine(128f, 38f, 42f, 124f, linePaint);
            canvas.drawLine(128f, 38f, 214f, 124f, linePaint);
            canvas.drawLine(42f, 124f, 128f, 210f, linePaint);
            canvas.drawLine(214f, 124f, 128f, 210f, linePaint);
        } else if ("dirkodds_home".equals(textureId) || "dirkodds_away".equals(textureId)) {
            int teamColor = "dirkodds_home".equals(textureId) ? scenario.homeColor : scenario.awayColor;
            canvas.drawColor(Color.TRANSPARENT);
            paint.setShader(new LinearGradient(0f, 0f, 0f, 256f, lighten(teamColor, 0.2f), darken(teamColor, 0.24f), Shader.TileMode.CLAMP));
            canvas.drawRoundRect(new RectF(54f, 20f, 202f, 236f), 28f, 28f, paint);
            paint.setShader(null);
            paint.setColor(Color.argb(245, 244, 237, 228));
            canvas.drawCircle(128f, 66f, 30f, paint);
            paint.setColor(Color.argb(240, 24, 27, 32));
            canvas.drawRect(105f, 96f, 151f, 196f, paint);
            canvas.drawRect(82f, 114f, 174f, 136f, paint);
            canvas.drawText(shortLabel("dirkodds_home".equals(textureId) ? scenario.homeTeam : scenario.awayTeam), 28f, 244f, textPaint);
        } else if ("dirkodds_focus".equals(textureId)) {
            paint.setShader(new LinearGradient(0f, 0f, 256f, 256f, Color.rgb(246, 189, 96), Color.rgb(244, 96, 54), Shader.TileMode.CLAMP));
            canvas.drawRoundRect(new RectF(18f, 18f, 238f, 238f), 44f, 44f, paint);
            paint.setShader(null);
            linePaint.setColor(Color.argb(230, 255, 246, 214));
            linePaint.setStrokeWidth(6f);
            canvas.drawCircle(128f, 128f, 52f, linePaint);
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
            "attribute vec3 aPosition;\n" +
            "attribute vec2 aTexCoord;\n" +
            "attribute vec3 aNormal;\n" +
            "varying vec2 vTexCoord;\n" +
            "varying float vLight;\n" +
            "void main() {\n" +
            "  vec3 normal = normalize((uModelMatrix * vec4(aNormal, 0.0)).xyz);\n" +
            "  vLight = max(dot(normal, normalize(uLightDir)), 0.0) * 0.65 + 0.35;\n" +
            "  vTexCoord = aTexCoord;\n" +
            "  gl_Position = uMvpMatrix * vec4(aPosition, 1.0);\n" +
            "}";

    private static final String FRAGMENT_SHADER =
            "precision mediump float;\n" +
            "uniform sampler2D uTexture;\n" +
            "varying vec2 vTexCoord;\n" +
            "varying float vLight;\n" +
            "void main() {\n" +
            "  vec4 color = texture2D(uTexture, vTexCoord);\n" +
            "  gl_FragColor = vec4(color.rgb * vLight, color.a);\n" +
            "}";
}
