package com.urbden.game;

import android.graphics.Color;

import org.json.JSONObject;

import java.util.Locale;

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
    public final TeamIdentity homeIdentity;
    public final TeamIdentity awayIdentity;
    public final QuickthingsProfile quickthings;

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
            int awayColor,
            TeamIdentity homeIdentity,
            TeamIdentity awayIdentity,
            QuickthingsProfile quickthings) {
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
        this.homeIdentity = homeIdentity;
        this.awayIdentity = awayIdentity;
        this.quickthings = quickthings;
    }

    public static DirkOddsScenario fromJson(JSONObject object) {
        int homeColor = parseColor(object.optString("home_color", "#E36B5D"), Color.rgb(227, 107, 93));
        int awayColor = parseColor(object.optString("away_color", "#4DA3D9"), Color.rgb(77, 163, 217));
        String homeTeam = object.optString("home_team", "Home");
        String awayTeam = object.optString("away_team", "Away");
        return new DirkOddsScenario(
                object.optString("id", "scenario"),
                object.optString("sport", "football"),
                object.optString("title", "DirkOdds Scenario"),
                object.optString("summary", "Synthetic prediction test"),
                object.optString("venue", "Anonymous Arena"),
                homeTeam,
                awayTeam,
                (float) object.optDouble("home_probability", 0.38),
                (float) object.optDouble("draw_probability", 0.24),
                (float) object.optDouble("away_probability", 0.38),
                (float) object.optDouble("tempo", 0.55),
                homeColor,
                awayColor,
                TeamIdentity.fromJson(object.optJSONObject("home_identity"), homeTeam, homeColor),
                TeamIdentity.fromJson(object.optJSONObject("away_identity"), awayTeam, awayColor),
                QuickthingsProfile.fromJson(object.optJSONObject("quickthings")));
    }

    public boolean isQuickthings() {
        return "quickthings".equals(sport);
    }

    public String matchupDeckLabel() {
        return String.format(Locale.US, "%s // %s vs %s", homeIdentity.shortMark(), homeTeam, awayTeam);
    }

    public String identityHeadline() {
        if (isQuickthings()) {
            return quickthings.rulesAim + " // " + quickthings.protocolSummary();
        }
        return homeIdentity.broadcastLine() + "  <>  " + awayIdentity.broadcastLine();
    }

    public String sidelineBrief() {
        if (isQuickthings()) {
            return String.format(
                    Locale.US,
                    "Cosmocourse: %d rounds | VL %d | PS %d | HD %d | CT %d | CW %d",
                    quickthings.rounds,
                    quickthings.vacuumLength,
                    quickthings.portalStability,
                    quickthings.higgsDensity,
                    quickthings.collapseThreshold,
                    quickthings.choiceWellRadius);
        }
        return "Home sideline: " + homeIdentity.bannerLine + " | " + homeIdentity.cheerNote
                + "\nAway sideline: " + awayIdentity.bannerLine + " | " + awayIdentity.cheerNote;
    }

    public String uniformBrief() {
        if (isQuickthings()) {
            return "Deck: 52 clubs across four irons, drivers, and putters | Codex: 709 numeric cause/effect protocols";
        }
        return "Uniforms: " + homeIdentity.uniformNote + " | " + awayIdentity.uniformNote;
    }

    public int teamSize() {
        if (isQuickthings()) {
            return 0;
        }
        switch (sport) {
            case "multisport":
                return 6;
            case "hockey":
                return 6;
            case "basketball":
                return 5;
            case "baseball":
                return 6;
            default:
                return 6;
        }
    }

    public boolean supportsDraw() {
        return "football".equals(sport) || "multisport".equals(sport) || isQuickthings();
    }

    public String laneLabel(int outcome) {
        if (!isQuickthings()) {
            if (outcome == DirkOddsSimulator.OUTCOME_AWAY) {
                return "Away Lane";
            }
            if (outcome == DirkOddsSimulator.OUTCOME_DRAW) {
                return "Draw Lane";
            }
            return "Home Lane";
        }
        if (outcome == DirkOddsSimulator.OUTCOME_AWAY) {
            return "Rift Lane";
        }
        if (outcome == DirkOddsSimulator.OUTCOME_DRAW) {
            return "Consensus Line";
        }
        return "Sink Line";
    }

    public String activeCallText(int outcome) {
        if (!isQuickthings()) {
            if (outcome == DirkOddsSimulator.OUTCOME_AWAY) {
                return awayTeam + " edge";
            }
            if (outcome == DirkOddsSimulator.OUTCOME_DRAW) {
                return "balanced draw lane";
            }
            return homeTeam + " edge";
        }
        if (outcome == DirkOddsSimulator.OUTCOME_AWAY) {
            return "Rift lane: force extra portals and long vacuum cuts";
        }
        if (outcome == DirkOddsSimulator.OUTCOME_DRAW) {
            return "Consensus line: balance portals, sync, and entropy control";
        }
        return "Sink line: tighter geometry and Choice Well finishing";
    }

    public float probabilityForOutcome(int outcome) {
        if (isQuickthings()) {
            if (outcome == DirkOddsSimulator.OUTCOME_AWAY) {
                return 0.34f;
            }
            if (outcome == DirkOddsSimulator.OUTCOME_DRAW) {
                return 0.33f;
            }
            return 0.33f;
        }
        if (outcome == DirkOddsSimulator.OUTCOME_HOME) {
            return homeProbability;
        }
        if (outcome == DirkOddsSimulator.OUTCOME_AWAY) {
            return awayProbability;
        }
        return drawProbability;
    }

    private static int parseColor(String value, int fallbackColor) {
        try {
            return Color.parseColor(value);
        } catch (IllegalArgumentException exception) {
            return fallbackColor;
        }
    }

    public static final class TeamIdentity {
        public final String teamName;
        public final String sigil;
        public final String mascotName;
        public final String mascotType;
        public final String bannerLine;
        public final String uniformNote;
        public final String cheerNote;
        public final String designNote;
        public final int accentColor;

        TeamIdentity(
                String teamName,
                String sigil,
                String mascotName,
                String mascotType,
                String bannerLine,
                String uniformNote,
                String cheerNote,
                String designNote,
                int accentColor) {
            this.teamName = teamName;
            this.sigil = sigil;
            this.mascotName = mascotName;
            this.mascotType = mascotType;
            this.bannerLine = bannerLine;
            this.uniformNote = uniformNote;
            this.cheerNote = cheerNote;
            this.designNote = designNote;
            this.accentColor = accentColor;
        }

        static TeamIdentity fromJson(JSONObject object, String fallbackName, int fallbackColor) {
            if (object == null) {
                return new TeamIdentity(
                        fallbackName,
                        deriveInitials(fallbackName),
                        fallbackName,
                        "synthetic creature",
                        fallbackName.toUpperCase(Locale.US),
                        "abstract match kit",
                        "coordinated sideline line",
                        "derived from anonymous geometric forms",
                        fallbackColor);
            }
            return new TeamIdentity(
                    fallbackName,
                    object.optString("sigil", deriveInitials(fallbackName)),
                    object.optString("mascot_name", fallbackName),
                    object.optString("mascot_type", "synthetic creature"),
                    object.optString("banner_line", fallbackName.toUpperCase(Locale.US)),
                    object.optString("uniform_note", "abstract match kit"),
                    object.optString("cheer_note", "coordinated sideline line"),
                    object.optString("design_note", "derived from anonymous geometric forms"),
                    parseColor(object.optString("accent_color", "#FFFFFF"), fallbackColor));
        }

        public String shortMark() {
            return sigil == null || sigil.trim().isEmpty() ? deriveInitials(teamName) : sigil.toUpperCase(Locale.US);
        }

        public String mascotLine() {
            return mascotName + " the " + mascotType;
        }

        public String broadcastLine() {
            return shortMark() + " | " + mascotLine();
        }

        private static String deriveInitials(String value) {
            if (value == null || value.trim().isEmpty()) {
                return "TEAM";
            }
            String[] words = value.trim().split("\\s+");
            StringBuilder builder = new StringBuilder();
            for (String word : words) {
                if (!word.isEmpty()) {
                    builder.append(Character.toUpperCase(word.charAt(0)));
                }
            }
            return builder.length() == 0 ? "TEAM" : builder.toString();
        }
    }

    public static final class QuickthingsProfile {
        public final int rounds;
        public final int vacuumLength;
        public final int portalStability;
        public final int higgsDensity;
        public final int collapseThreshold;
        public final int choiceWellRadius;
        public final String rulesAim;

        QuickthingsProfile(
                int rounds,
                int vacuumLength,
                int portalStability,
                int higgsDensity,
                int collapseThreshold,
                int choiceWellRadius,
                String rulesAim) {
            this.rounds = rounds;
            this.vacuumLength = vacuumLength;
            this.portalStability = portalStability;
            this.higgsDensity = higgsDensity;
            this.collapseThreshold = collapseThreshold;
            this.choiceWellRadius = choiceWellRadius;
            this.rulesAim = rulesAim;
        }

        static QuickthingsProfile fromJson(JSONObject object) {
            if (object == null) {
                return new QuickthingsProfile(
                        9,
                        18,
                        6,
                        5,
                        11,
                        3,
                        "Seed first, bend the bream cleanly, and sink consensus into the Choice Well.");
            }
            return new QuickthingsProfile(
                    object.optInt("rounds", 9),
                    object.optInt("vacuum_length", 18),
                    object.optInt("portal_stability", 6),
                    object.optInt("higgs_density", 5),
                    object.optInt("collapse_threshold", 11),
                    object.optInt("choice_well_radius", 3),
                    object.optString("rules_aim", "Seed first, bend the bream cleanly, and sink consensus into the Choice Well."));
        }

        public String protocolSummary() {
            return String.format(
                    Locale.US,
                    "52 clubs | %d rounds | 709 rules",
                    rounds);
        }
    }
}