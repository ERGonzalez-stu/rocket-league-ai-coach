"""
Data Collection Module for Rocket League Replays
Fetches player-specific replay data from Ballchasing API
"""

import requests
import time
from typing import List, Dict, Optional
from config import BALLCHASING_API_KEY


class BallchasingAPI:
    """Wrapper for Ballchasing API"""

    BASE_URL = "https://ballchasing.com/api"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {"Authorization": api_key}

    def search_replays(self, player_name: str, count: int = 30) -> List[Dict]:
        """
        Search for replays by player name

        Args:
            player_name: Name of the player to search for
            count: Number of replays to fetch (max 200)

        Returns:
            List of replay metadata dictionaries
        """
        params = {
            "player-name": player_name,
            "count": min(count, 200),  # API max is 200
            "sort-by": "replay-date",
            "sort-dir": "desc"  # Most recent first
        }

        try:
            response = requests.get(
                f"{self.BASE_URL}/replays",
                headers=self.headers,
                params=params
            )
            response.raise_for_status()

            data = response.json()
            replays = data.get("list", [])

            print(f"Found {len(replays)} replays for player: {player_name}")
            return replays

        except requests.exceptions.RequestException as e:
            print(f"Error fetching replays: {e}")
            return []

    def get_replay_details(self, replay_id: str) -> Optional[Dict]:
        """
        Get detailed stats for a specific replay

        Args:
            replay_id: Unique replay identifier

        Returns:
            Detailed replay data including all player stats
        """
        try:
            response = requests.get(
                f"{self.BASE_URL}/replays/{replay_id}",
                headers=self.headers
            )
            response.raise_for_status()

            return response.json()

        except requests.exceptions.RequestException as e:
            print(f"Error fetching replay {replay_id}: {e}")
            return None

    def get_player_stats_from_replay(self, replay_data: Dict, player_name: str) -> Optional[Dict]:
        """
        Extract stats for a specific player from replay data

        Args:
            replay_data: Full replay data from get_replay_details()
            player_name: Name of player to extract stats for

        Returns:
            Dictionary of player stats for this game
        """
        # Check both teams
        for team_color in ["blue", "orange"]:
            team_data = replay_data.get(team_color, {})
            players = team_data.get("players", [])

            for player in players:
                # Case-insensitive name matching
                if player.get("name", "").lower() == player_name.lower():
                    # Extract core stats
                    stats = player.get("stats", {})
                    core = stats.get("core", {})
                    boost = stats.get("boost", {})
                    movement = stats.get("movement", {})
                    positioning = stats.get("positioning", {})

                    # Determine if player won
                    blue_goals = replay_data.get("blue", {}).get("stats", {}).get("core", {}).get("goals", 0)
                    orange_goals = replay_data.get("orange", {}).get("stats", {}).get("core", {}).get("goals", 0)

                    if team_color == "blue":
                        won = blue_goals > orange_goals
                    else:
                        won = orange_goals > blue_goals

                    return {
                        # Game metadata
                        "replay_id": replay_data.get("id"),
                        "date": replay_data.get("date"),
                        "duration": replay_data.get("duration"),
                        "playlist": replay_data.get("playlist_name"),

                        # Player info
                        "player_name": player.get("name"),
                        "team": team_color,
                        "won": won,

                        # Core stats
                        "goals": core.get("goals", 0),
                        "assists": core.get("assists", 0),
                        "saves": core.get("saves", 0),
                        "shots": core.get("shots", 0),
                        "score": core.get("score", 0),
                        "shooting_percentage": core.get("shooting_percentage", 0),

                        # Boost stats
                        "boost_collected": boost.get("bcpm", 0),  # boost collected per minute
                        "boost_stolen": boost.get("stolen", 0),
                        "boost_used": boost.get("used_while_supersonic", 0),

                        # Movement
                        "avg_speed": movement.get("avg_speed", 0),
                        "time_supersonic": movement.get("time_supersonic_speed", 0),

                        # Positioning
                        "time_defensive_third": positioning.get("time_defensive_third", 0),
                        "time_neutral_third": positioning.get("time_neutral_third", 0),
                        "time_offensive_third": positioning.get("time_offensive_third", 0),
                    }

        # Player not found in this replay
        return None

    def get_player_match_history(self, player_name: str, num_games: int = 30) -> List[Dict]:
        """
        Get complete match history for a player

        Args:
            player_name: Name of player to analyze
            num_games: Number of games to fetch

        Returns:
            List of dictionaries containing player stats from each game
        """
        print(f"\n🔍 Fetching match history for: {player_name}")
        print(f"Target: {num_games} games\n")

        # Step 1: Search for replays
        replays = self.search_replays(player_name, count=num_games)

        if not replays:
            print(f"❌ No replays found for {player_name}")
            return []

        # Step 2: Get detailed stats for each replay
        match_history = []

        for i, replay in enumerate(replays, 1):
            replay_id = replay.get("id")

            print(f"Processing game {i}/{len(replays)}: {replay_id}")

            # Get detailed replay data
            detailed_replay = self.get_replay_details(replay_id)

            if not detailed_replay:
                continue

            # Check if player with exact name is in this replay
            player_found = False
            for team_color in ["blue", "orange"]:
                team_data = detailed_replay.get(team_color, {})
                players = team_data.get("players", [])
                for player in players:
                    if player.get("name", "").lower() == player_name.lower():
                        player_found = True
                        break
                if player_found:
                    break

            if not player_found:
                print(f"  ⏭️  Skipping - exact player name '{player_name}' not in replay")
                continue

            # Extract player's stats from this game
            player_stats = self.get_player_stats_from_replay(detailed_replay, player_name)

            if player_stats:
                match_history.append(player_stats)
            else:
                print(f"  ⚠️  Player {player_name} not found in replay {replay_id}")

            # Rate limiting - be nice to the API
            time.sleep(0.5)  # Wait 500ms between requests

        print(f"\n✅ Successfully retrieved {len(match_history)} games")
        return match_history


# Example usage
if __name__ == "__main__":
    # Initialize API
    api = BallchasingAPI(BALLCHASING_API_KEY)

    # Test with a popular player
    player_name = "Squishy"  # You can change this to any player

    # Get their last 10 games (using 10 for quick testing)
    match_history = api.get_player_match_history(player_name, num_games=10)

    # Display results
    if match_history:
        print(f"\n📊 Stats Summary for {player_name}:")
        print(f"Games analyzed: {len(match_history)}")

        # Calculate averages
        avg_goals = sum(g["goals"] for g in match_history) / len(match_history)
        avg_assists = sum(g["assists"] for g in match_history) / len(match_history)
        avg_saves = sum(g["saves"] for g in match_history) / len(match_history)
        wins = sum(1 for g in match_history if g["won"])
        win_rate = (wins / len(match_history)) * 100

        print(f"Average Goals: {avg_goals:.2f}")
        print(f"Average Assists: {avg_assists:.2f}")
        print(f"Average Saves: {avg_saves:.2f}")
        print(f"Win Rate: {win_rate:.1f}%")