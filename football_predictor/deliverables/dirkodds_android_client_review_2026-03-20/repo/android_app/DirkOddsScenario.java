package com.urbden.game;

import android.graphics.Color;

import org.json.JSONObject;

public final class DirkOddsScenario {
    public final String id;
    public final String sport;
    public final String title;
    public final String summary;
    public final String venue;
    public final String homeTeam;
    public final String awayTeam;
    public final float homeProbability;
    public final float drawProbability;
    public final float awayProbability;
    public final float tempo;
    public final int homeColor;
    public final int awayColor;

    DirkOddsScenario(
            String id,
            String sport,
            String title,
            String summary,
            String venue,
            String homeTeam,
            String awayTeam,
            float homeProbability,
            float drawProbability,
            float awayProbability,
            float tempo,
            int homeColor,
            int awayColor) {
        this.id = id;
        this.sport = sport;
        this.title = title;
        this.summary = summary;
        this.venue = venue;
        this.homeTeam = homeTeam;
        this.awayTeam = awayTeam;
        this.homeProbability = homeProbability;
        this.drawProbability = drawProbability;
        this.awayProbability = awayProbability;
        this.tempo = tempo;
        this.homeColor = homeColor;
        this.awayColor = awayColor;
    }

    public static DirkOddsScenario fromJson(JSONObject object) {
        return new DirkOddsScenario(
                object.optString("id", "scenario"),
                object.optString("sport", "football"),
                object.optString("title", "DirkOdds Scenario"),
                object.optString("summary", "Synthetic prediction test"),
                object.optString("venue", "Anonymous Arena"),
                object.optString("home_team", "Home"),
                object.optString("away_team", "Away"),
                (float) object.optDouble("home_probability", 0.38),
                (float) object.optDouble("draw_probability", 0.24),
                (float) object.optDouble("away_probability", 0.38),
                (float) object.optDouble("tempo", 0.55),
                Color.parseColor(object.optString("home_color", "#E36B5D")),
                Color.parseColor(object.optString("away_color", "#4DA3D9")));
    }

    public int teamSize() {
        switch (sport) {
            case "basketball":
                return 5;
            case "baseball":
                return 6;
            default:
                return 6;
        }
    }

    public boolean supportsDraw() {
        return "football".equals(sport);
    }

    public float probabilityForOutcome(int outcome) {
        if (outcome == DirkOddsSimulator.OUTCOME_HOME) {
            return homeProbability;
        }
        if (outcome == DirkOddsSimulator.OUTCOME_AWAY) {
            return awayProbability;
        }
        return drawProbability;
    }
}