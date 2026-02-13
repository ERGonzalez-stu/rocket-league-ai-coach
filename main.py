"""
Main script to fetch and store player data
"""

import sys

sys.path.insert(0, 'src')

from src.data_collection import BallchasingAPI
from src.database import RocketLeagueDB
from config import BALLCHASING_API_KEY


def analyze_player(player_name: str, num_games: int = 30):
    """
    Fetch and store player data

    Args:
        player_name: Name of player to analyze
        num_games: Number of recent games to fetch
    """
    print(f"\n{'=' * 50}")
    print(f"ANALYZING PLAYER: {player_name}")
    print(f"{'=' * 50}\n")

    # Initialize API and database
    api = BallchasingAPI(BALLCHASING_API_KEY)
    db = RocketLeagueDB(db_path="data/rl_stats.db")

    # Check if we already have data
    if db.player_exists(player_name):
        print(f"ℹ️  Player {player_name} already in database")
        print(f"Current data:")
        stats_df = db.get_player_stats(player_name)
        print(f"  - {len(stats_df)} games stored")
        print()
        response = input("Fetch new data anyway? (y/n): ")
        if response.lower() != 'y':
            print("Using existing data...")
            print(f"\n{'=' * 50}")
            print(f"SUMMARY FOR {player_name}")
            print(f"{'=' * 50}")
            print(f"Total games: {len(stats_df)}")
            print(f"Average goals: {stats_df['goals'].mean():.2f}")
            print(f"Average assists: {stats_df['assists'].mean():.2f}")
            print(f"Average saves: {stats_df['saves'].mean():.2f}")
            print(f"Win rate: {(stats_df['won'].sum() / len(stats_df) * 100):.1f}%")
            print(f"Average score: {stats_df['score'].mean():.0f}")
            print(f"{'=' * 50}\n")
            return

    # Fetch match history from API
    match_history = api.get_player_match_history(player_name, num_games)

    if not match_history:
        print(f"❌ Could not fetch data for {player_name}")
        return

    # Store in database
    db.add_match_history(player_name, match_history)

    # Display summary
    stats_df = db.get_player_stats(player_name)
    print(f"\n{'=' * 50}")
    print(f"SUMMARY FOR {player_name}")
    print(f"{'=' * 50}")
    print(f"Total games: {len(stats_df)}")
    print(f"Average goals: {stats_df['goals'].mean():.2f}")
    print(f"Average assists: {stats_df['assists'].mean():.2f}")
    print(f"Average saves: {stats_df['saves'].mean():.2f}")
    print(f"Win rate: {(stats_df['won'].sum() / len(stats_df) * 100):.1f}%")
    print(f"Average score: {stats_df['score'].mean():.0f}")
    print(f"{'=' * 50}\n")


if __name__ == "__main__":
    # Analyze some players
    players_to_analyze = [
        "Squishy",
        "justin.",
    ]

    for player in players_to_analyze:
        try:
            analyze_player(player, num_games=10)
        except Exception as e:
            print(f"❌ Error analyzing {player}: {e}")
            continue

    print("\n🎉 Day 1 Complete! Database has player data ready for Day 2!")