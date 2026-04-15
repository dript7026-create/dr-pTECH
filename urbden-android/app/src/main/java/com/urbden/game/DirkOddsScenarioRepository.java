package com.urbden.game;

import android.content.Context;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.Collections;
import java.util.List;

public final class DirkOddsScenarioRepository {
    private DirkOddsScenarioRepository() {
    }

    public static List<DirkOddsScenario> load(Context context) {
        try {
            String json = readAsset(context, "dirkodds/scenarios.json");
            JSONArray items = new JSONArray(json);
            List<DirkOddsScenario> scenarios = new ArrayList<>();
            for (int i = 0; i < items.length(); i++) {
                scenarios.add(DirkOddsScenario.fromJson(items.getJSONObject(i)));
            }
            scenarios.sort(Comparator.comparingInt(DirkOddsScenarioRepository::scenarioPriority));
            return scenarios;
        } catch (Exception exception) {
            return Collections.emptyList();
        }
    }

    public static DirkOddsScenario findById(Context context, String id) {
        for (DirkOddsScenario scenario : load(context)) {
            if (scenario.id.equals(id)) {
                return scenario;
            }
        }
        List<DirkOddsScenario> scenarios = load(context);
        return scenarios.isEmpty() ? null : scenarios.get(0);
    }

    private static String readAsset(Context context, String path) throws IOException {
        StringBuilder builder = new StringBuilder();
        try (InputStream input = context.getAssets().open(path);
             BufferedReader reader = new BufferedReader(new InputStreamReader(input))) {
            String line;
            while ((line = reader.readLine()) != null) {
                builder.append(line);
            }
        }
        return builder.toString();
    }

    private static int scenarioPriority(DirkOddsScenario scenario) {
        if (scenario == null) {
            return Integer.MAX_VALUE;
        }
        if ("multisport".equals(scenario.sport)) {
            return 0;
        }
        if ("football".equals(scenario.sport)) {
            return 1;
        }
        if ("basketball".equals(scenario.sport)) {
            return 2;
        }
        if ("baseball".equals(scenario.sport)) {
            return 3;
        }
        if ("hockey".equals(scenario.sport)) {
            return 4;
        }
        if (scenario.isQuickthings()) {
            return 9;
        }
        return 5;
    }
}