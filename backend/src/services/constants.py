"""Shared constants for the mood engine module."""

from typing import Dict

# Database configuration
TABLE_SONGS = "songs"

# Mood labels
MOODS = ["energetic", "happy", "sad", "stress", "angry"]

# Type aliases
Song = Dict[str, object]
