"""
AI Coach module using Groq API
Generates personalized coaching tips based on player stats
"""

from groq import Groq
from typing import Dict, List
try:
    import streamlit as st
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except:
    from config import GROQ_API_KEY


class AICoach:
    """Generate AI-powered coaching tips using Groq"""

    def __init__(self, api_key: str = GROQ_API_KEY):
        """Initialize Groq client"""
        self.client = Groq(api_key=api_key)
        self.model = "llama-3.3-70b-versatile"

    def generate_coaching_tips(self, summary_stats: Dict, recent_form: Dict,
                               strengths: Dict, playlist_stats: Dict = None) -> str:
        """
        Generate personalized coaching tips based on player performance

        Args:
            summary_stats: Overall player statistics
            recent_form: Recent performance data
            strengths: Identified strengths and weaknesses
            playlist_stats: Stats by game mode (optional)

        Returns:
            Formatted coaching advice as string
        """

        # Build context prompt
        prompt = self._build_coaching_prompt(summary_stats, recent_form, strengths, playlist_stats)

        try:
            # Call Groq API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert Rocket League coach with years of experience. 
                        Provide specific, actionable coaching advice based on player statistics. 
                        Be encouraging but honest. Focus on 3-4 key areas for improvement.
                        Keep your response concise and well-structured."""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=800
            )

            return response.choices[0].message.content

        except Exception as e:
            return f"Error generating coaching tips: {str(e)}"

    def _build_coaching_prompt(self, summary_stats: Dict, recent_form: Dict,
                               strengths: Dict, playlist_stats: Dict = None) -> str:
        """Build the prompt for the AI coach"""

        # Extract key stats
        total_games = summary_stats.get('total_games', 0)
        win_rate = summary_stats.get('win_rate', 0)
        avg_goals = summary_stats.get('avg_goals', 0)
        avg_assists = summary_stats.get('avg_assists', 0)
        avg_saves = summary_stats.get('avg_saves', 0)
        avg_score = summary_stats.get('avg_score', 0)
        shooting_pct = summary_stats.get('avg_shooting_pct', 0)

        # Recent form
        recent_wins = recent_form.get('wins', 0)
        recent_games = recent_form.get('games', 0)
        recent_wr = recent_form.get('win_rate', 0)

        # Build prompt
        prompt = f"""Analyze this Rocket League player's performance and provide coaching advice:

OVERALL STATS ({total_games} games):
- Win Rate: {win_rate:.1f}%
- Average Goals: {avg_goals:.2f}
- Average Assists: {avg_assists:.2f}
- Average Saves: {avg_saves:.2f}
- Average Score: {avg_score:.0f}
- Shooting Accuracy: {shooting_pct:.1f}%

RECENT FORM (Last {recent_games} games):
- Wins: {recent_wins}/{recent_games} ({recent_wr:.1f}% win rate)
- Recent Goals: {recent_form.get('avg_goals', 0):.2f}
- Recent Assists: {recent_form.get('avg_assists', 0):.2f}
- Recent Saves: {recent_form.get('avg_saves', 0):.2f}

IDENTIFIED PATTERNS:
Strengths: {', '.join(strengths.get('strengths', []))}
Areas to improve: {', '.join(strengths.get('weaknesses', []))}
"""

        # Add playlist-specific info if available
        if playlist_stats:
            prompt += "\n\nPERFORMANCE BY GAME MODE:\n"
            for playlist, stats in list(playlist_stats.items())[:3]:  # Top 3 playlists
                prompt += f"- {playlist}: {stats['games']} games, {stats['win_rate']:.1f}% win rate\n"

        prompt += """

Provide personalized coaching advice:
1. Start with 1-2 positive observations about their playstyle
2. Identify 2-3 key areas for improvement with specific actionable tips
3. Suggest training focus areas or drills
4. End with motivational insight about their trajectory

Keep it concise, specific, and encouraging."""

        return prompt

    def generate_quick_tips(self, summary_stats: Dict) -> List[str]:
        """
        Generate quick bullet-point tips without full analysis

        Returns:
            List of 3-5 quick tips
        """
        tips = []

        avg_goals = summary_stats.get('avg_goals', 0)
        avg_assists = summary_stats.get('avg_assists', 0)
        avg_saves = summary_stats.get('avg_saves', 0)
        win_rate = summary_stats.get('win_rate', 0)
        shooting_pct = summary_stats.get('avg_shooting_pct', 0)

        # Goal scoring
        if avg_goals < 1.0:
            tips.append("🎯 Work on offensive positioning - look for more scoring opportunities")
        elif avg_goals > 2.0:
            tips.append("💪 Excellent goal scoring! Keep applying offensive pressure")

        # Playmaking
        if avg_assists < 0.8:
            tips.append("🤝 Practice passing plays - look for teammates in better positions")
        elif avg_assists > 1.5:
            tips.append("👏 Great playmaking! Your passing creates opportunities")

        # Defense
        if avg_saves < 1.0:
            tips.append("🛡️ Focus on defensive rotation and positioning")
        elif avg_saves > 2.0:
            tips.append("🔒 Solid defense! You're keeping your team in games")

        # Shooting accuracy
        if shooting_pct < 30:
            tips.append("🎯 Improve shot selection - quality over quantity")
        elif shooting_pct > 50:
            tips.append("🔥 Excellent shooting accuracy! You're efficient with your shots")

        # Win rate
        if win_rate < 45:
            tips.append("📈 Focus on consistency - review replays to identify patterns")
        elif win_rate > 55:
            tips.append("🏆 Great win rate! You're climbing steadily")

        return tips[:5]  # Return max 5 tips


# Example usage
if __name__ == "__main__":
    from database import RocketLeagueDB
    from analytics import PlayerAnalytics

    # Load data
    db = RocketLeagueDB(db_path="../data/rl_stats.db")
    stats_df = db.get_player_stats("Squishy")

    # Get analytics
    analytics = PlayerAnalytics(stats_df)
    summary = analytics.get_summary_stats()
    recent_form = analytics.get_recent_form(10)
    strengths = analytics.get_strengths_and_weaknesses()
    playlist_stats = analytics.get_stats_by_playlist()

    # Generate coaching
    coach = AICoach()

    print("=== GENERATING AI COACHING TIPS ===\n")
    coaching = coach.generate_coaching_tips(summary, recent_form, strengths, playlist_stats)
    print(coaching)

    print("\n\n=== QUICK TIPS ===\n")
    quick_tips = coach.generate_quick_tips(summary)
    for tip in quick_tips:
        print(f"  {tip}")