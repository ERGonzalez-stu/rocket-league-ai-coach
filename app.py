"""
Streamlit Dashboard for Rocket League AI Coach
"""

import streamlit as st
import sys

sys.path.insert(0, 'src')

from src.database import RocketLeagueDB
from src.data_collection import BallchasingAPI
from src.analytics import PlayerAnalytics
from src.visualizations import PlayerVisualizations
try:
    BALLCHASING_API_KEY = st.secrets["BALLCHASING_API_KEY"]
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except:
    from config import BALLCHASING_API_KEY, GROQ_API_KEY
from src.ai_coach import AICoach

# Page config
st.set_page_config(
    page_title="Rocket League AI Coach",
    layout="wide"
)

# Initialize session state
if 'analyzed_player' not in st.session_state:
    st.session_state.analyzed_player = None

# Header
st.title("Rocket League AI Coach")
st.markdown("**AI-powered performance analytics for Rocket League players**")
st.divider()

# Sidebar - Player input
with st.sidebar:
    st.header("⚙Settings")

    player_name = st.text_input(
        "Enter Player Name",
        placeholder="e.g., Squishy, justin, Firstkiller",
        help="Search for any player who has uploaded replays to Ballchasing.com"
    )

    num_games = st.slider(
        "Number of games to analyze",
        min_value=5,
        max_value=50,
        value=20,
        step=5
    )

    analyze_button = st.button("Analyze Player", type="primary", use_container_width=True)

    st.divider()

    # Quick access to popular players
    st.subheader("Try These Players")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Squishy", use_container_width=True):
            player_name = "Squishy"
            analyze_button = True
        if st.button("justin", use_container_width=True):
            player_name = "justin"
            analyze_button = True
    with col2:
        if st.button("Firstkiller", use_container_width=True):
            player_name = "Firstkiller"
            analyze_button = True
        if st.button("Daniel", use_container_width=True):
            player_name = "Daniel"
            analyze_button = True

# Main content
if analyze_button and player_name:
    with st.spinner(f"Analyzing {player_name}..."):
        try:
            # Initialize
            db = RocketLeagueDB(db_path="data/rl_stats.db")
            api = BallchasingAPI(BALLCHASING_API_KEY)

            # Check if player exists in database
            if not db.player_exists(player_name):
                st.info(f"Fetching data for {player_name} from Ballchasing...")

                # Fetch data
                match_history = api.get_player_match_history(player_name, num_games=num_games)

                if not match_history:
                    st.error(f"No replays found for player: {player_name}")
                    st.info("Try a different player name or check spelling")
                    st.stop()

                # Store in database
                db.add_match_history(player_name, match_history)
                st.success(f"Fetched {len(match_history)} games!")
            else:
                st.info(f"Loading existing data for {player_name}")

            # Get stats
            stats_df = db.get_player_stats(player_name)

            if len(stats_df) == 0:
                st.error(f"No data found for {player_name}")
                st.stop()

            # Store in session
            st.session_state.analyzed_player = player_name

            # Create analytics
            analytics = PlayerAnalytics(stats_df)
            summary = analytics.get_summary_stats()
            playlist_stats = analytics.get_stats_by_playlist()
            recent_form = analytics.get_recent_form(10)
            comparison = analytics.compare_performance(first_n=10, last_n=10) if len(stats_df) >= 20 else {}
            strengths = analytics.get_strengths_and_weaknesses()

            # Create visualizations
            viz = PlayerVisualizations(stats_df, player_name)

            st.success(f"Analysis complete for {player_name}!")

        except Exception as e:
            st.error(f"Error: {str(e)}")
            st.stop()

# Display results if we have an analyzed player
if st.session_state.analyzed_player:
    player_name = st.session_state.analyzed_player

    # Reload data
    db = RocketLeagueDB(db_path="data/rl_stats.db")
    stats_df = db.get_player_stats(player_name)
    analytics = PlayerAnalytics(stats_df)
    summary = analytics.get_summary_stats()
    playlist_stats = analytics.get_stats_by_playlist()
    recent_form = analytics.get_recent_form(10)
    comparison = analytics.compare_performance(first_n=10, last_n=10) if len(stats_df) >= 20 else {}
    strengths = analytics.get_strengths_and_weaknesses()
    viz = PlayerVisualizations(stats_df, player_name)

    # Overview Section
    st.header(f"{player_name} - Performance Overview")

    # Key metrics
    col1, col2, col3, col4, col5 = st.columns([1,1.2,1,1,1])

    with col1:
        st.metric("Total Games", summary.get("total_games", 0))
    with col2:
        win_rate = summary.get('win_rate', 0)
        st.metric("Win Rate", f"{win_rate:.1f}%")
    with col3:
        st.metric("Avg Goals", f"{summary.get('avg_goals', 0):.2f}")
    with col4:
        st.metric("Avg Assists", f"{summary.get('avg_assists', 0):.2f}")
    with col5:
        st.metric("Avg Saves", f"{summary.get('avg_saves', 0):.2f}")

    st.divider()

    # Charts Section
    st.header("Performance Analysis")

    tab1, tab2, tab3, tab4 = st.tabs(["Trends", "Stats Breakdown", "By Game Mode", "Improvement"])

    with tab1:
        st.subheader("Performance Over Time")
        fig_timeline = viz.create_performance_timeline()
        st.plotly_chart(fig_timeline, use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            fig_score = viz.create_score_distribution()
            st.plotly_chart(fig_score, use_container_width=True)
        with col2:
            fig_win_loss = viz.create_win_loss_chart(summary)
            st.plotly_chart(fig_win_loss, use_container_width=True)

    with tab2:
        col1, col2 = st.columns([1, 1])
        with col1:
            fig_radar = viz.create_stats_radar(summary)
            st.plotly_chart(fig_radar, use_container_width=True)

        with col2:
            st.subheader("Detailed Stats")
            st.metric("Best Game (Goals)", summary.get("best_goals", 0))
            st.metric("Best Game (Assists)", summary.get("best_assists", 0))
            st.metric("Best Game (Saves)", summary.get("best_saves", 0))
            st.metric("Best Score", summary.get("best_score", 0))
            st.metric("Avg Shot Accuracy", f"{summary.get('avg_shooting_pct', 0):.1f}%")

    with tab3:
        if playlist_stats:
            fig_playlist = viz.create_playlist_comparison(playlist_stats)
            st.plotly_chart(fig_playlist, use_container_width=True)

            st.subheader("Stats by Game Mode")
            for playlist, stats in playlist_stats.items():
                with st.expander(f"{playlist}"):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Games", stats["games"])
                        st.metric("Win Rate", f"{stats['win_rate']:.1f}%")
                    with col2:
                        st.metric("Avg Goals", f"{stats['avg_goals']:.2f}")
                        st.metric("Avg Assists", f"{stats['avg_assists']:.2f}")
                    with col3:
                        st.metric("Avg Saves", f"{stats['avg_saves']:.2f}")
                        st.metric("Avg Score", f"{stats['avg_score']:.0f}")
        else:
            st.info("Not enough playlist data available")

    with tab4:
        if comparison:
            fig_improvement = viz.create_improvement_chart(comparison)
            st.plotly_chart(fig_improvement, use_container_width=True)

            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Early Games")
                early = comparison.get("early", {})
                st.metric("Win Rate", f"{early.get('win_rate', 0):.1f}%")
                st.metric("Avg Goals", f"{early.get('avg_goals', 0):.2f}")
                st.metric("Avg Score", f"{early.get('avg_score', 0):.0f}")

            with col2:
                st.subheader("Recent Games")
                recent = comparison.get("recent", {})
                st.metric("Win Rate", f"{recent.get('win_rate', 0):.1f}%")
                st.metric("Avg Goals", f"{recent.get('avg_goals', 0):.2f}")
                st.metric("Avg Score", f"{recent.get('avg_score', 0):.0f}")
        else:
            st.info("Need at least 20 games to show improvement analysis")

    st.divider()

    # Insights Section
    # AI Coaching Section
    st.header("AI Coach")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("**Get personalized coaching tips powered by AI**")

        if st.button("Generate AI Coaching", type="primary", use_container_width=True):
            with st.spinner("AI Coach is analyzing your gameplay..."):
                try:
                    coach = AICoach()
                    coaching_tips = coach.generate_coaching_tips(
                        summary,
                        recent_form,
                        strengths,
                        playlist_stats
                    )
                    st.session_state['coaching_tips'] = coaching_tips
                except Exception as e:
                    st.error(f"Error generating coaching: {str(e)}")

    with col2:
        st.markdown("**Quick Tips**")
        try:
            coach = AICoach()
            quick_tips = coach.generate_quick_tips(summary)
            for tip in quick_tips:
                st.info(tip)
        except:
            pass

    # Display AI coaching if generated
    if 'coaching_tips' in st.session_state:
        st.markdown("---")
        st.subheader("Your Personalized Coaching Plan")
        st.markdown(st.session_state['coaching_tips'])

    st.divider()

    # Strengths & Weaknesses
    st.header("Performance Insights")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Strengths")
        for strength in strengths.get("strengths", []):
            st.success(f"✓ {strength}")

    with col2:
        st.subheader("Areas to Improve")
        for weakness in strengths.get("weaknesses", []):
            st.warning(f"→ {weakness}")

    # Recent Form
    st.subheader("Recent Form (Last 10 Games)")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Games", recent_form.get("games", 0))
    with col2:
        st.metric("Wins", recent_form.get("wins", 0))
    with col3:
        st.metric("Win Rate", f"{recent_form.get('win_rate', 0):.1f}%")
    with col4:
        st.metric("Avg Score", f"{recent_form.get('avg_score', 0):.0f}")

else:
    # Welcome screen
    st.info("Enter a player name in the sidebar to get started!")

    st.subheader("How it works:")
    st.markdown("""
    1. **Enter a player name** in the sidebar
    2. Click **Analyze Player** to fetch their data from Ballchasing.com
    3. View **detailed stats, charts, and insights**
    4. Get **personalized recommendations** (coming in Day 3!)

    Try analyzing **Squishy**, **justin**, or **Firstkiller** to see it in action!
    """)

    st.subheader("Features:")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**Performance Trends**")
        st.caption("Track goals, assists, and saves over time")
    with col2:
        st.markdown("**Stat Breakdown**")
        st.caption("Detailed analysis of all metrics")
    with col3:
        st.markdown("**By Game Mode**")
        st.caption("Compare performance across playlists")

# Footer
st.divider()
st.caption("Made with Streamlit and Plotly| Data from Ballchasing.com")