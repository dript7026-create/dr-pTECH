package com.driptech.pocode.data

import android.content.Context
import com.driptech.pocode.campaign.PlayerProgress
import com.driptech.pocode.campaign.ProjectRequest
import org.json.JSONArray
import org.json.JSONObject

data class SavedCampaignState(
    val request: ProjectRequest,
    val progress: PlayerProgress,
)

object PocodeProgressStore {
    private const val FileName = "pocode_progress.json"

    fun save(context: Context, request: ProjectRequest, progress: PlayerProgress) {
        val payload = JSONObject()
            .put("request", JSONObject()
                .put("projectIdea", request.projectIdea)
                .put("language", request.language)
                .put("learnerLevel", request.learnerLevel)
                .put("sessionLengthMinutes", request.sessionLengthMinutes)
                .put("seedWord", request.seedWord)
            )
            .put("progress", JSONObject()
                .put("completedLessonIds", JSONArray(progress.completedLessonIds.toList()))
                .put("totalSuccesses", progress.totalSuccesses)
                .put("totalMistakes", progress.totalMistakes)
                .put("recentAccuracy", progress.recentAccuracy.toDouble())
                .put("activeRestReliefNodes", progress.activeRestReliefNodes)
                .put("avatarInventory", JSONArray(progress.avatarInventory))
                .put("conceptMistakes", JSONObject(progress.conceptMistakes.mapValues { it.value }))
            )

        context.openFileOutput(FileName, Context.MODE_PRIVATE).bufferedWriter().use { writer ->
            writer.write(payload.toString(2))
        }
    }

    fun load(context: Context): SavedCampaignState? {
        val text = runCatching {
            context.openFileInput(FileName).bufferedReader().use { it.readText() }
        }.getOrNull() ?: return null

        val payload = JSONObject(text)
        val requestJson = payload.getJSONObject("request")
        val progressJson = payload.getJSONObject("progress")

        val request = ProjectRequest(
            projectIdea = requestJson.getString("projectIdea"),
            language = requestJson.getString("language"),
            learnerLevel = requestJson.getString("learnerLevel"),
            sessionLengthMinutes = requestJson.getInt("sessionLengthMinutes"),
            seedWord = requestJson.getString("seedWord"),
        )

        val completed = buildSet {
            val array = progressJson.getJSONArray("completedLessonIds")
            for (index in 0 until array.length()) {
                add(array.getString(index))
            }
        }
        val inventory = buildList {
            val array = progressJson.getJSONArray("avatarInventory")
            for (index in 0 until array.length()) {
                add(array.getString(index))
            }
        }
        val mistakes = mutableMapOf<String, Int>()
        val mistakesJson = progressJson.getJSONObject("conceptMistakes")
        mistakesJson.keys().forEach { key ->
            mistakes[key] = mistakesJson.getInt(key)
        }

        val progress = PlayerProgress(
            completedLessonIds = completed,
            totalSuccesses = progressJson.getInt("totalSuccesses"),
            totalMistakes = progressJson.getInt("totalMistakes"),
            recentAccuracy = progressJson.getDouble("recentAccuracy").toFloat(),
            conceptMistakes = mistakes,
            activeRestReliefNodes = progressJson.getInt("activeRestReliefNodes"),
            avatarInventory = inventory,
        )

        return SavedCampaignState(request = request, progress = progress)
    }
}