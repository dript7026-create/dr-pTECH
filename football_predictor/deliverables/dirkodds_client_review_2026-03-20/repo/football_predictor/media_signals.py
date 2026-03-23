from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence
from xml.etree import ElementTree

import numpy as np
import pandas as pd
import requests


POSITIVE_TERMS = {
    "fit",
    "boost",
    "surge",
    "return",
    "confident",
    "sharp",
    "momentum",
    "dominant",
    "improving",
    "recovered",
}

NEGATIVE_TERMS = {
    "injury",
    "suspension",
    "fatigue",
    "rumour",
    "gossip",
    "doubt",
    "setback",
    "poor",
    "crisis",
    "absence",
    "unrest",
}


@dataclass
class MediaArticle:
    title: str
    summary: str
    link: str
    published: Optional[str] = None

    @property
    def text(self) -> str:
        return f"{self.title} {self.summary}".strip()


def fetch_rss_articles(urls: Sequence[str]) -> List[MediaArticle]:
    articles: List[MediaArticle] = []
    for url in urls:
        response = requests.get(url, timeout=20)
        response.raise_for_status()
        root = ElementTree.fromstring(response.content)
        for item in root.findall(".//item"):
            articles.append(
                MediaArticle(
                    title=(item.findtext("title") or "").strip(),
                    summary=(item.findtext("description") or "").strip(),
                    link=(item.findtext("link") or "").strip(),
                    published=(item.findtext("pubDate") or "").strip() or None,
                )
            )
    return articles


def article_sentiment_score(text: str) -> float:
    lowered = text.lower()
    positive_hits = sum(1 for term in POSITIVE_TERMS if term in lowered)
    negative_hits = sum(1 for term in NEGATIVE_TERMS if term in lowered)
    return float(positive_hits - negative_hits)


def aggregate_team_media_signals(
    team_names: Iterable[str],
    articles: Sequence[MediaArticle],
    aliases: Optional[Dict[str, Sequence[str]]] = None,
) -> pd.DataFrame:
    rows = []
    alias_map = aliases or {}
    for team_name in team_names:
        terms = {team_name.lower()}
        terms.update(alias.lower() for alias in alias_map.get(team_name, []))
        matching_articles = []
        scores = []
        for article in articles:
            text = article.text.lower()
            if any(term and term in text for term in terms):
                score = article_sentiment_score(article.text)
                matching_articles.append(article)
                scores.append(score)
        article_count = len(matching_articles)
        sentiment = float(np.mean(scores)) if scores else 0.0
        buzz = float(np.log1p(article_count))
        rows.append(
            {
                "team_name": team_name,
                "media_article_count": article_count,
                "media_sentiment": sentiment,
                "media_buzz": buzz,
            }
        )
    return pd.DataFrame(rows)


def build_fixture_media_frame(
    fixtures_df: pd.DataFrame,
    articles: Sequence[MediaArticle],
    aliases: Optional[Dict[str, Sequence[str]]] = None,
) -> pd.DataFrame:
    teams = sorted(set(fixtures_df["home_team"].astype(str)).union(set(fixtures_df["away_team"].astype(str))))
    team_signals = aggregate_team_media_signals(teams, articles, aliases=aliases)
    team_lookup = team_signals.set_index("team_name") if not team_signals.empty else pd.DataFrame()

    rows = []
    for fixture in fixtures_df.itertuples(index=False):
        home = team_lookup.loc[fixture.home_team] if fixture.home_team in team_lookup.index else None
        away = team_lookup.loc[fixture.away_team] if fixture.away_team in team_lookup.index else None
        home_sentiment = float(home["media_sentiment"]) if home is not None else 0.0
        away_sentiment = float(away["media_sentiment"]) if away is not None else 0.0
        home_buzz = float(home["media_buzz"]) if home is not None else 0.0
        away_buzz = float(away["media_buzz"]) if away is not None else 0.0
        rows.append(
            {
                "fixture_key": fixture_key(fixture.home_team, fixture.away_team, fixture.date),
                "media_sentiment_home": home_sentiment,
                "media_sentiment_away": away_sentiment,
                "media_buzz_home": home_buzz,
                "media_buzz_away": away_buzz,
                "media_signal_gap": (home_sentiment + 0.35 * home_buzz) - (away_sentiment + 0.35 * away_buzz),
            }
        )
    return pd.DataFrame(rows)


def fixture_key(home_team: str, away_team: str, match_date) -> str:
    date_str = pd.to_datetime(match_date, errors="coerce")
    key_date = date_str.strftime("%Y-%m-%d") if pd.notna(date_str) else "undated"
    return f"{home_team.strip().lower()}::{away_team.strip().lower()}::{key_date}"