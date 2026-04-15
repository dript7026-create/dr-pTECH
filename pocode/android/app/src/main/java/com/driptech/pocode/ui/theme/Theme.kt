package com.driptech.pocode.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

private val PocodeLight = lightColorScheme(
    primary = Color(0xFF0B57D0),
    secondary = Color(0xFF00897B),
    tertiary = Color(0xFFE67E22),
    background = Color(0xFFF1F5FF),
    surface = Color(0xFFFFFFFF),
    surfaceVariant = Color(0xFFDDE7FF),
)

private val PocodeDark = darkColorScheme(
    primary = Color(0xFF9BC1FF),
    secondary = Color(0xFF72D6C9),
    tertiary = Color(0xFFFFB870),
    background = Color(0xFF121826),
    surface = Color(0xFF1A2234),
    surfaceVariant = Color(0xFF24304A),
)

@Composable
fun PocodeTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = if (isSystemInDarkTheme()) PocodeDark else PocodeLight,
        content = content,
    )
}