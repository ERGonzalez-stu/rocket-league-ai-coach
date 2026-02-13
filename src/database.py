"""
Database module for storing player stats
Uses SQLite for simplicity
"""

import sqlite3
import pandas as pd
from typing import List, Dict
from datetime import datetime


class RocketLeagueDB:
    """SQLite database for storing player match history"""

    def __init__(self, db_path: str = "../data/rl_stats.db"):
        self.db_path = db_path
        self.conn = None
        self.create_tables()

    def connect(self):
        """Create database connection"""
        self.conn = sqlite3.connect(self.db_path)
        return self.conn

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

    def create_tables(self):
        """Create database tables if they don't exist"""
        conn = self.connect()
        cursor = conn.cursor()

        # Players table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS players (
                player_id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_name TEXT UNIQUE NOT NULL,
                last_updated TIMESTAMP,
                total_games INTEGER DEFAULT 0
            )
        """)

        # Match history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS match_history (
                match_id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id INTEGER,
                replay_id TEXT UNIQUE,
                date TEXT,
                duration INTEGER,
                playlist TEXT,
                team TEXT,
                won BOOLEAN,
                goals INTEGER,
                assists INTEGER,
                saves INTEGER,
                shots INTEGER,
                score INTEGER,
                shooting_percentage REAL,
                boost_collected REAL,
                boost_stolen INTEGER,
                boost_used INTEGER,
                avg_speed REAL,
                time_supersonic REAL,
                time_defensive_third REAL,
                time_neutral_third REAL,
                time_offensive_third REAL,
                FOREIGN KEY (player_id) REFERENCES players (player_id)
            )
        """)

        conn.commit()
        conn.close()
        print("✅ Database tables created")

    def add_player(self, player_name: str) -> int:
        """
        Add a player to the database

        Returns:
            player_id
        """
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR IGNORE INTO players (player_name, last_updated)
            VALUES (?, ?)
        """, (player_name, datetime.now()))

        # Get player_id
        cursor.execute("SELECT player_id FROM players WHERE player_name = ?", (player_name,))
        player_id = cursor.fetchone()[0]

        conn.commit()
        conn.close()

        return player_id

    def add_match_history(self, player_name: str, match_data: List[Dict]):
        """
        Store match history for a player

        Args:
            player_name: Name of the player
            match_data: List of match stat dictionaries
        """
        conn = self.connect()
        cursor = conn.cursor()

        # Get or create player
        player_id = self.add_player(player_name)

        # Insert each match
        games_added = 0
        for match in match_data:
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO match_history (
                        player_id, replay_id, date, duration, playlist,
                        team, won, goals, assists, saves, shots, score,
                        shooting_percentage, boost_collected, boost_stolen,
                        boost_used, avg_speed, time_supersonic,
                        time_defensive_third, time_neutral_third, time_offensive_third
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    player_id,
                    match.get("replay_id"),
                    match.get("date"),
                    match.get("duration"),
                    match.get("playlist"),
                    match.get("team"),
                    match.get("won"),
                    match.get("goals"),
                    match.get("assists"),
                    match.get("saves"),
                    match.get("shots"),
                    match.get("score"),
                    match.get("shooting_percentage"),
                    match.get("boost_collected"),
                    match.get("boost_stolen"),
                    match.get("boost_used"),
                    match.get("avg_speed"),
                    match.get("time_supersonic"),
                    match.get("time_defensive_third"),
                    match.get("time_neutral_third"),
                    match.get("time_offensive_third")
                ))
                games_added += 1
            except sqlite3.IntegrityError:
                # Replay already exists, skip
                pass

        # Update player record
        cursor.execute("""
            UPDATE players 
            SET last_updated = ?, 
                total_games = (SELECT COUNT(*) FROM match_history WHERE player_id = ?)
            WHERE player_id = ?
        """, (datetime.now(), player_id, player_id))

        conn.commit()
        conn.close()

        print(f"✅ Added {games_added} new games to database for {player_name}")

    def get_player_stats(self, player_name: str) -> pd.DataFrame:
        """
        Retrieve all stats for a player as DataFrame

        Args:
            player_name: Name of the player

        Returns:
            pandas DataFrame with all match data
        """
        conn = self.connect()

        query = """
            SELECT m.* 
            FROM match_history m
            JOIN players p ON m.player_id = p.player_id
            WHERE p.player_name = ?
            ORDER BY m.date DESC
        """

        df = pd.read_sql_query(query, conn, params=(player_name,))
        conn.close()

        return df

    def player_exists(self, player_name: str) -> bool:
        """Check if player data exists in database"""
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM players WHERE player_name = ?", (player_name,))
        exists = cursor.fetchone()[0] > 0

        conn.close()
        return exists


# Example usage
if __name__ == "__main__":
    # Initialize database
    db = RocketLeagueDB()

    # Test adding a player
    player_id = db.add_player("TestPlayer")
    print(f"Player ID: {player_id}")

    # Test data
    test_match = [{
        "replay_id": "test123",
        "date": "2026-02-10",
        "duration": 300,
        "playlist": "Ranked Doubles 2v2",
        "team": "blue",
        "won": True,
        "goals": 2,
        "assists": 1,
        "saves": 3,
        "shots": 5,
        "score": 450,
        "shooting_percentage": 40.0,
        "boost_collected": 250,
        "boost_stolen": 10,
        "boost_used": 200,
        "avg_speed": 1200,
        "time_supersonic": 45,
        "time_defensive_third": 30,
        "time_neutral_third": 40,
        "time_offensive_third": 30
    }]

    db.add_match_history("TestPlayer", test_match)

    # Retrieve and display
    stats_df = db.get_player_stats("TestPlayer")
    print("\nRetrieved stats:")
    print(stats_df[["goals", "assists", "saves", "won"]])