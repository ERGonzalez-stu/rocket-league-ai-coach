"""
Analytics module for calculating player statistics and metrics
"""

import pandas as pd
from typing import Dict, List


class PlayerAnalytics:
    """Calculate statistics and metrics from player data"""

    def __init__(self, stats_df: pd.DataFrame):
        """
        Initialize with player stats DataFrame

        Args:
            stats_df: DataFrame from database.get_player_stats()
        """
        self.df = stats_df

    def get_summary_stats(self) -> Dict:
        """
        Calculate overall summary statistics

        Returns:
            Dictionary of summary stats
        """
        if len(self.df) == 0:
            return {}

        return {
            "total_games": len(self.df),
            "wins": int(self.df["won"].sum()),
            "losses": int((~self.df["won"]).sum()),
            "win_rate": (self.df["won"].sum() / len(self.df) * 100),

            # Averages
            "avg_goals": self.df["goals"].mean(),
            "avg_assists": self.df["assists"].mean(),
            "avg_saves": self.df["saves"].mean(),
            "avg_shots": self.df["shots"].mean(),
            "avg_score": self.df["score"].mean(),

            # Shooting
            "avg_shooting_pct": self.df["shooting_percentage"].mean(),

            # Best performances
            "best_goals": int(self.df["goals"].max()),
            "best_assists": int(self.df["assists"].max()),
            "best_saves": int(self.df["saves"].max()),
            "best_score": int(self.df["score"].max()),
        }

    def get_stats_by_playlist(self) -> Dict[str, Dict]:
        """
        Calculate stats grouped by playlist (game mode)

        Returns:
            Dictionary with playlist names as keys, stats as values
        """
        if len(self.df) == 0:
            return {}

        playlists = {}

        for playlist in self.df["playlist"].unique():
            if pd.isna(playlist):
                continue

            playlist_df = self.df[self.df["playlist"] == playlist]

            playlists[playlist] = {
                "games": len(playlist_df),
                "win_rate": (playlist_df["won"].sum() / len(playlist_df) * 100),
                "avg_goals": playlist_df["goals"].mean(),
                "avg_assists": playlist_df["assists"].mean(),
                "avg_saves": playlist_df["saves"].mean(),
                "avg_score": playlist_df["score"].mean(),
            }

        return playlists

    def get_performance_trend(self) -> pd.DataFrame:
        """
        Calculate performance metrics over time

        Returns:
            DataFrame with date and rolling averages
        """
        if len(self.df) == 0:
            return pd.DataFrame()

        # Sort by date
        df_sorted = self.df.sort_values("date").copy()

        # Calculate rolling averages (last 5 games)
        df_sorted["rolling_goals"] = df_sorted["goals"].rolling(window=5, min_periods=1).mean()
        df_sorted["rolling_assists"] = df_sorted["assists"].rolling(window=5, min_periods=1).mean()
        df_sorted["rolling_saves"] = df_sorted["saves"].rolling(window=5, min_periods=1).mean()
        df_sorted["rolling_score"] = df_sorted["score"].rolling(window=5, min_periods=1).mean()

        return df_sorted

    def get_recent_form(self, num_games: int = 10) -> Dict:
        """
        Analyze recent performance

        Args:
            num_games: Number of recent games to analyze

        Returns:
            Dictionary of recent stats
        """
        if len(self.df) == 0:
            return {}

        # Get most recent games
        recent_df = self.df.head(num_games)

        return {
            "games": len(recent_df),
            "wins": int(recent_df["won"].sum()),
            "win_rate": (recent_df["won"].sum() / len(recent_df) * 100),
            "avg_goals": recent_df["goals"].mean(),
            "avg_assists": recent_df["assists"].mean(),
            "avg_saves": recent_df["saves"].mean(),
            "avg_score": recent_df["score"].mean(),
        }

    def compare_performance(self, first_n: int = 10, last_n: int = 10) -> Dict:
        """
        Compare early games vs recent games

        Args:
            first_n: Number of early games
            last_n: Number of recent games

        Returns:
            Dictionary comparing stats
        """
        if len(self.df) < first_n + last_n:
            return {}

        # Sort by date (oldest first)
        df_sorted = self.df.sort_values("date", ascending=True)

        early_games = df_sorted.head(first_n)
        recent_games = df_sorted.tail(last_n)

        def calc_stats(df):
            return {
                "win_rate": (df["won"].sum() / len(df) * 100),
                "avg_goals": df["goals"].mean(),
                "avg_assists": df["assists"].mean(),
                "avg_saves": df["saves"].mean(),
                "avg_score": df["score"].mean(),
            }

        early_stats = calc_stats(early_games)
        recent_stats = calc_stats(recent_games)

        # Calculate improvements
        improvements = {
            "win_rate_change": recent_stats["win_rate"] - early_stats["win_rate"],
            "goals_change": recent_stats["avg_goals"] - early_stats["avg_goals"],
            "assists_change": recent_stats["avg_assists"] - early_stats["avg_assists"],
            "saves_change": recent_stats["avg_saves"] - early_stats["avg_saves"],
            "score_change": recent_stats["avg_score"] - early_stats["avg_score"],
        }

        return {
            "early": early_stats,
            "recent": recent_stats,
            "improvement": improvements
        }

    def get_strengths_and_weaknesses(self) -> Dict:
        """
        Identify player strengths and weaknesses
        Based on percentiles within their own performance

        Returns:
            Dictionary categorizing stats
        """
        if len(self.df) == 0:
            return {}

        # Calculate percentiles for each stat
        percentiles = {
            "goals": self.df["goals"].mean(),
            "assists": self.df["assists"].mean(),
            "saves": self.df["saves"].mean(),
            "shooting_pct": self.df["shooting_percentage"].mean(),
        }

        strengths = []
        weaknesses = []

        # Simple heuristics (can be improved with rank-based comparisons)
        if percentiles["goals"] > 1.5:
            strengths.append("Goal scoring")
        elif percentiles["goals"] < 0.8:
            weaknesses.append("Goal scoring")

        if percentiles["assists"] > 1.2:
            strengths.append("Playmaking")
        elif percentiles["assists"] < 0.6:
            weaknesses.append("Playmaking")

        if percentiles["saves"] > 1.5:
            strengths.append("Defense")
        elif percentiles["saves"] < 0.8:
            weaknesses.append("Defense")

        if percentiles["shooting_pct"] > 40:
            strengths.append("Shot accuracy")
        elif percentiles["shooting_pct"] < 25:
            weaknesses.append("Shot accuracy")

        return {
            "strengths": strengths if strengths else ["Consistent all-around player"],
            "weaknesses": weaknesses if weaknesses else ["Well-rounded performance"],
            "metrics": percentiles
        }


# Example usage
if __name__ == "__main__":
    from database import RocketLeagueDB

    db = RocketLeagueDB(db_path="../data/rl_stats.db")
    stats_df = db.get_player_stats("Squishy")

    analytics = PlayerAnalytics(stats_df)

    print("=== SUMMARY STATS ===")
    summary = analytics.get_summary_stats()
    for key, value in summary.items():
        print(f"{key}: {value}")

    print("\n=== STATS BY PLAYLIST ===")
    by_playlist = analytics.get_stats_by_playlist()
    for playlist, stats in by_playlist.items():
        print(f"\n{playlist}:")
        for key, value in stats.items():
            print(f"  {key}: {value:.2f}")

    print("\n=== RECENT FORM (Last 10 games) ===")
    recent = analytics.get_recent_form(10)
    for key, value in recent.items():
        print(f"{key}: {value}")