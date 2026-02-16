"""
Visualization module for creating charts and graphs
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from typing import Dict, List


class PlayerVisualizations:
    """Create interactive visualizations for player stats"""

    def __init__(self, stats_df: pd.DataFrame, player_name: str):
        """
        Initialize with player stats

        Args:
            stats_df: DataFrame from database
            player_name: Name of player for titles
        """
        self.df = stats_df.sort_values("date")  # Sort chronologically
        self.player_name = player_name

        # Color scheme
        self.colors = {
            "primary": "#1f77b4",
            "secondary": "#ff7f0e",
            "success": "#2ca02c",
            "danger": "#d62728",
            "warning": "#ff9800",
            "info": "#17a2b8"
        }

    def create_performance_timeline(self) -> go.Figure:
        """
        Line chart showing performance over time with rolling averages
        """
        if len(self.df) == 0:
            return go.Figure()

        # Calculate rolling averages
        df = self.df.copy()
        df["rolling_goals"] = df["goals"].rolling(window=5, min_periods=1).mean()
        df["rolling_assists"] = df["assists"].rolling(window=5, min_periods=1).mean()
        df["rolling_saves"] = df["saves"].rolling(window=5, min_periods=1).mean()

        fig = go.Figure()

        # Add traces
        fig.add_trace(go.Scatter(
            x=list(range(len(df))),
            y=df["rolling_goals"],
            mode='lines',
            name='Goals',
            line=dict(color=self.colors["primary"], width=2)
        ))

        fig.add_trace(go.Scatter(
            x=list(range(len(df))),
            y=df["rolling_assists"],
            mode='lines',
            name='Assists',
            line=dict(color=self.colors["secondary"], width=2)
        ))

        fig.add_trace(go.Scatter(
            x=list(range(len(df))),
            y=df["rolling_saves"],
            mode='lines',
            name='Saves',
            line=dict(color=self.colors["success"], width=2)
        ))

        fig.update_layout(
            title=f"{self.player_name} - Performance Trend (5-Game Rolling Average)",
            xaxis_title="Game Number",
            yaxis_title="Average per Game",
            hovermode='x unified',
            template="plotly_white",
            height=400
        )

        return fig

    def create_stats_radar(self, summary_stats: Dict) -> go.Figure:
        """
        Radar chart comparing different stat categories
        """
        if not summary_stats:
            return go.Figure()

        # Normalize stats to 0-10 scale for radar chart
        categories = ['Goals', 'Assists', 'Saves', 'Shots', 'Score/100']

        values = [
            min(summary_stats.get("avg_goals", 0) * 2, 10),  # Scale goals
            min(summary_stats.get("avg_assists", 0) * 2, 10),  # Scale assists
            min(summary_stats.get("avg_saves", 0) * 2, 10),  # Scale saves
            min(summary_stats.get("avg_shots", 0) / 2, 10),  # Scale shots
            min(summary_stats.get("avg_score", 0) / 100, 10),  # Scale score
        ]

        fig = go.Figure()

        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name=self.player_name,
            line=dict(color=self.colors["primary"])
        ))

        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 10]
                )
            ),
            showlegend=False,
            title=f"{self.player_name} - Stat Profile",
            height=400
        )

        return fig

    def create_win_loss_chart(self, summary_stats: Dict) -> go.Figure:
        """
        Pie chart showing win/loss distribution
        """
        if not summary_stats:
            return go.Figure()

        wins = summary_stats.get("wins", 0)
        losses = summary_stats.get("losses", 0)

        fig = go.Figure(data=[go.Pie(
            labels=['Wins', 'Losses'],
            values=[wins, losses],
            marker=dict(colors=[self.colors["success"], self.colors["danger"]]),
            hole=.3
        )])

        fig.update_layout(
            title=f"{self.player_name} - Win/Loss Record",
            height=400
        )

        return fig

    def create_playlist_comparison(self, playlist_stats: Dict) -> go.Figure:
        """
        Bar chart comparing performance across different playlists
        """
        if not playlist_stats:
            return go.Figure()

        playlists = list(playlist_stats.keys())
        win_rates = [stats["win_rate"] for stats in playlist_stats.values()]
        avg_goals = [stats["avg_goals"] for stats in playlist_stats.values()]
        games = [stats["games"] for stats in playlist_stats.values()]

        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=("Win Rate by Mode", "Avg Goals by Mode")
        )

        # Win rate bars
        fig.add_trace(
            go.Bar(
                x=playlists,
                y=win_rates,
                name="Win Rate %",
                marker_color=self.colors["primary"],
                text=[f"{wr:.1f}%" for wr in win_rates],
                textposition='outside'
            ),
            row=1, col=1
        )

        # Goals bars
        fig.add_trace(
            go.Bar(
                x=playlists,
                y=avg_goals,
                name="Avg Goals",
                marker_color=self.colors["secondary"],
                text=[f"{g:.2f}" for g in avg_goals],
                textposition='outside'
            ),
            row=1, col=2
        )

        fig.update_layout(
            title=f"{self.player_name} - Performance by Game Mode",
            showlegend=False,
            height=400
        )

        fig.update_xaxes(tickangle=45)

        return fig

    def create_score_distribution(self) -> go.Figure:
        """
        Histogram showing score distribution
        """
        if len(self.df) == 0:
            return go.Figure()

        fig = go.Figure(data=[go.Histogram(
            x=self.df["score"],
            nbinsx=20,
            marker_color=self.colors["info"],
            name="Games"
        )])

        # Add mean line
        mean_score = self.df["score"].mean()
        fig.add_vline(
            x=mean_score,
            line_dash="dash",
            line_color=self.colors["danger"],
            annotation_text=f"Average: {mean_score:.0f}",
            annotation_position="top"
        )

        fig.update_layout(
            title=f"{self.player_name} - Score Distribution",
            xaxis_title="Score",
            yaxis_title="Number of Games",
            template="plotly_white",
            height=400
        )

        return fig

    def create_improvement_chart(self, comparison: Dict) -> go.Figure:
        """
        Bar chart showing improvement between early and recent games
        """
        if not comparison:
            return go.Figure()

        improvements = comparison.get("improvement", {})

        metrics = ['Goals', 'Assists', 'Saves', 'Score/100', 'Win Rate']
        changes = [
            improvements.get("goals_change", 0),
            improvements.get("assists_change", 0),
            improvements.get("saves_change", 0),
            improvements.get("score_change", 0) / 100,
            improvements.get("win_rate_change", 0)
        ]

        colors = [self.colors["success"] if c > 0 else self.colors["danger"] for c in changes]

        fig = go.Figure(data=[go.Bar(
            x=metrics,
            y=changes,
            marker_color=colors,
            text=[f"{c:+.2f}" for c in changes],
            textposition='outside'
        )])

        fig.add_hline(y=0, line_dash="dash", line_color="gray")

        fig.update_layout(
            title=f"{self.player_name} - Improvement Over Time",
            yaxis_title="Change (Recent vs Early Games)",
            template="plotly_white",
            height=400
        )

        return fig

    def create_all_visualizations(self, summary_stats: Dict, playlist_stats: Dict, comparison: Dict) -> Dict[
        str, go.Figure]:
        """
        Generate all visualizations at once

        Returns:
            Dictionary of figure objects
        """
        return {
            "timeline": self.create_performance_timeline(),
            "radar": self.create_stats_radar(summary_stats),
            "win_loss": self.create_win_loss_chart(summary_stats),
            "playlist": self.create_playlist_comparison(playlist_stats),
            "score_dist": self.create_score_distribution(),
            "improvement": self.create_improvement_chart(comparison)
        }


# Example usage
if __name__ == "__main__":
    from database import RocketLeagueDB
    from analytics import PlayerAnalytics

    # Load data
    db = RocketLeagueDB(db_path="../data/rl_stats.db")
    stats_df = db.get_player_stats("Squishy")

    # Create analytics
    analytics = PlayerAnalytics(stats_df)
    summary = analytics.get_summary_stats()
    playlist_stats = analytics.get_stats_by_playlist()
    comparison = analytics.compare_performance(first_n=5, last_n=5)

    # Create visualizations
    viz = PlayerVisualizations(stats_df, "Squishy")

    # Generate one chart as test
    fig = viz.create_performance_timeline()
    fig.show()  # This will open in browser

    print("✅ Visualization created! Check your browser.")