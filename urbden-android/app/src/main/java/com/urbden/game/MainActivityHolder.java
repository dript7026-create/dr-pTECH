package com.urbden.game;

import android.content.Context;

// Simple singleton to forward native method calls from GridView to MainActivity's JNI bindings.
public class MainActivityHolder {
    private static MainActivityHolder inst = null;

    private MainActivityHolder() {}

    public static MainActivityHolder getInstance() {
        if (inst == null) inst = new MainActivityHolder();
        return inst;
    }

    // native proxies implemented in MainActivity via JNI
    public native int getWorldWidth();
    public native int getWorldHeight();
    public native int getNPCCount();
    public native int getNPCX(int idx);
    public native int getNPCY(int idx);
    public native boolean isNPCRival(int idx);
    public native float getNPCInfluence(int idx);
    public native java.nio.ByteBuffer getNPCBuffer();
    public native void releaseNPCBuffer();
}
