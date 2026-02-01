"""
Search Routes
=============
Text search and autocomplete endpoints.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, List, Optional

router = APIRouter()

# Lazy load search engine
_search_engine = None


def get_search_engine():
    """Get or create the search engine"""
    global _search_engine
    if _search_engine is None:
        from backend.src.search.tfidf_search import create_search_engine
        from backend.repositories import SongRepository
        repo = SongRepository()
        songs = repo.get_all(limit=10000)
        _search_engine = create_search_engine(songs)
    return _search_engine


@router.get("/")
def search_songs(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=50)
):
    """Full-text search for songs using TF-IDF"""
    try:
        search_engine = get_search_engine()
        results = search_engine.search(q, top_k=limit)
        return [
            {**song, "relevance_score": float(score)}
            for song, score in results
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/suggest")
def suggest_songs(
    prefix: str = Query(..., min_length=1, description="Prefix to search"),
    limit: int = Query(5, ge=1, le=20)
):
    """Autocomplete suggestions"""
    try:
        search_engine = get_search_engine()
        suggestions = search_engine.autocomplete(prefix, top_k=limit)
        return suggestions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Suggest failed: {str(e)}")


@router.get("/vietnamese")
def search_vietnamese(
    q: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=50)
):
    """Vietnamese-aware search (handles diacritics)"""
    try:
        # Remove diacritics for broader matching
        import unicodedata
        
        def remove_diacritics(text):
            return ''.join(
                c for c in unicodedata.normalize('NFD', text)
                if unicodedata.category(c) != 'Mn'
            )
        
        search_engine = get_search_engine()
        # Search with original and normalized
        results1 = search_engine.search(q, top_k=limit)
        results2 = search_engine.search(remove_diacritics(q), top_k=limit)
        
        # Merge results
        seen = set()
        merged = []
        for song, score in results1 + results2:
            song_id = song.get("song_id")
            if song_id not in seen:
                seen.add(song_id)
                merged.append({**song, "relevance_score": float(score)})
        
        return merged[:limit]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
