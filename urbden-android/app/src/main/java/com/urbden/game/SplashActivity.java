package com.urbden.game;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.util.TypedValue;
import android.view.Gravity;
import android.view.ViewGroup;
import android.view.WindowManager;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.TextView;

public class SplashActivity extends Activity {
    private final Handler handler = new Handler(Looper.getMainLooper());
    private final Runnable launchMain = new Runnable() {
        @Override
        public void run() {
            Intent intent = new Intent(SplashActivity.this, MainActivity.class);
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP);
            startActivity(intent);
            finish();
            overridePendingTransition(android.R.anim.fade_in, android.R.anim.fade_out);
        }
    };

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN);

        FrameLayout root = new FrameLayout(this);
        root.setBackground(buildBackground());

        LinearLayout hero = new LinearLayout(this);
        hero.setOrientation(LinearLayout.VERTICAL);
        hero.setPadding(dp(24), dp(24), dp(24), dp(24));
        hero.setBackground(buildHeroCard());

        TextView eyebrow = new TextView(this);
        eyebrow.setText("PREVIEW SIGNAL FEED");
        eyebrow.setTextColor(Color.rgb(122, 231, 255));
        eyebrow.setLetterSpacing(0.16f);
        eyebrow.setTypeface(Typeface.create("sans-serif-medium", Typeface.BOLD));
        eyebrow.setTextSize(TypedValue.COMPLEX_UNIT_SP, 11);
        hero.addView(eyebrow);

        TextView title = new TextView(this);
        title.setText("DIRK//ODDS\nSIGNAL ARENA");
        title.setTextColor(Color.rgb(245, 248, 255));
        title.setTypeface(Typeface.create("sans-serif-black", Typeface.BOLD));
        title.setTextSize(TypedValue.COMPLEX_UNIT_SP, 34);
        title.setPadding(0, dp(6), 0, dp(8));
        hero.addView(title);

        LinearLayout chipRow = new LinearLayout(this);
        chipRow.setOrientation(LinearLayout.HORIZONTAL);
        chipRow.addView(buildChip("SYNTHETIC SPORTS", Color.rgb(86, 229, 255), Color.rgb(12, 42, 54)));
        chipRow.addView(buildChip("CLIENT REVIEW", Color.rgb(255, 210, 120), Color.rgb(52, 31, 10)));
        hero.addView(chipRow);

        TextView subtitle = new TextView(this);
        subtitle.setText("Broadcast-style prediction review with fictional teams, interactive coaching cues, and abstract 3D live-play testing.");
        subtitle.setTextColor(Color.rgb(186, 197, 216));
        subtitle.setTextSize(TypedValue.COMPLEX_UNIT_SP, 15);
        subtitle.setPadding(0, dp(12), 0, 0);
        hero.addView(subtitle);

        FrameLayout.LayoutParams heroParams = new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT,
                Gravity.CENTER);
        heroParams.leftMargin = dp(16);
        heroParams.rightMargin = dp(16);
        root.addView(hero, heroParams);

        TextView footer = new TextView(this);
        footer.setText("No real clubs, leagues, players, or licensed likenesses");
        footer.setTextColor(Color.rgb(122, 140, 164));
        footer.setTextSize(TypedValue.COMPLEX_UNIT_SP, 12);
        footer.setTypeface(Typeface.create("sans-serif-medium", Typeface.BOLD));
        FrameLayout.LayoutParams footerParams = new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.WRAP_CONTENT,
                ViewGroup.LayoutParams.WRAP_CONTENT,
                Gravity.BOTTOM | Gravity.CENTER_HORIZONTAL);
        footerParams.bottomMargin = dp(28);
        root.addView(footer, footerParams);

        setContentView(root);

        hero.setAlpha(0f);
        hero.setTranslationY(dp(18));
        hero.animate().alpha(1f).translationY(0).setDuration(420).start();
        footer.setAlpha(0f);
        footer.animate().alpha(1f).setStartDelay(180).setDuration(320).start();
    }

    @Override
    protected void onResume() {
        super.onResume();
        handler.removeCallbacks(launchMain);
        handler.postDelayed(launchMain, 1650L);
    }

    @Override
    protected void onPause() {
        handler.removeCallbacks(launchMain);
        super.onPause();
    }

    private GradientDrawable buildBackground() {
        return new GradientDrawable(
                GradientDrawable.Orientation.TL_BR,
                new int[] {Color.rgb(6, 10, 24), Color.rgb(13, 18, 43), Color.rgb(24, 12, 37)});
    }

    private GradientDrawable buildHeroCard() {
        GradientDrawable background = new GradientDrawable(
                GradientDrawable.Orientation.TL_BR,
                new int[] {Color.argb(238, 10, 18, 36), Color.argb(238, 22, 17, 45), Color.argb(238, 12, 31, 39)});
        background.setCornerRadius(dp(30));
        background.setStroke(dp(1), Color.argb(220, 104, 223, 255));
        return background;
    }

    private TextView buildChip(String text, int textColor, int fillColor) {
        TextView chip = new TextView(this);
        chip.setText(text);
        chip.setTextColor(textColor);
        chip.setTextSize(TypedValue.COMPLEX_UNIT_SP, 11);
        chip.setTypeface(Typeface.create("sans-serif-medium", Typeface.BOLD));
        chip.setPadding(dp(10), dp(6), dp(10), dp(6));
        GradientDrawable background = new GradientDrawable();
        background.setColor(fillColor);
        background.setCornerRadius(dp(999));
        background.setStroke(dp(1), Color.argb(180, Color.red(textColor), Color.green(textColor), Color.blue(textColor)));
        chip.setBackground(background);
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.WRAP_CONTENT,
                ViewGroup.LayoutParams.WRAP_CONTENT);
        params.rightMargin = dp(8);
        chip.setLayoutParams(params);
        return chip;
    }

    private int dp(int value) {
        return Math.round(TypedValue.applyDimension(
                TypedValue.COMPLEX_UNIT_DIP,
                value,
                getResources().getDisplayMetrics()));
    }
}