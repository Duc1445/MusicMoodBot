"""
Backend API Package
===================
Clean API layer with modular routes.
"""

from .v1 import v1_router

__all__ = ["v1_router"]
