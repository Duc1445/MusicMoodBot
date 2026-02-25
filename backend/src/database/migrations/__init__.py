"""
Database Migrations Package
===========================

Contains migration scripts for the MusicMoodBot database schema evolution.

Migrations:
- migrate_conversation_v3.py: Multi-turn conversation system schema
"""

from .migrate_conversation_v3 import ConversationMigration, MIGRATION_VERSION

__all__ = ['ConversationMigration', 'MIGRATION_VERSION']
