package com.driptech.skulldummy.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

private val SkullDummyLight = lightColorScheme(
    primary = Color(0xFF6E1018),
    secondary = Color(0xFF2D5E6C),
    tertiary = Color(0xFFB98B3A),
    background = Color(0xFFF6EEE3),
    surface = Color(0xFFFFFBF5),
    surfaceVariant = Color(0xFFE9D9C4),
)

private val SkullDummyDark = darkColorScheme(
    primary = Color(0xFFF0B7BD),
    secondary = Color(0xFF92C9D6),
    tertiary = Color(0xFFE8C57B),
    background = Color(0xFF0E0E11),
    surface = Color(0xFF17171B),
    surfaceVariant = Color(0xFF24242B),
)

@Composable
fun SkullDummyTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = if (isSystemInDarkTheme()) SkullDummyDark else SkullDummyLight,
        content = content,
    )
}