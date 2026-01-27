📍 PROJECT COMPONENTS - LOCATIONS

## 1. Production main.py
📁 Location: d:\MMB\backend\main.py
- FastAPI application entry point
- Includes CORS middleware configuration
- Health check endpoint
- Serves API documentation (Swagger UI, ReDoc)

## 2. .env.example
📁 Location: d:\MMB\backend\.env.example (if exists) or create it
- Example environment variables file
- Should contain: API_PORT, DEBUG, DATABASE_PATH, etc.

## 3. Health Checks
📁 Location: d:\MMB\backend\src\api\mood_api.py (lines 30-40)
🔗 Endpoint: GET /health
- Returns service status, version, uptime
- Global endpoint: GET /health

## 4. CORS Middleware
📁 Location: d:\MMB\backend\main.py (lines 20-28)
- Configured to allow all origins
- Methods: GET, POST, OPTIONS, etc.
- Headers: All

## 5. Logistic Regression Preference Model
📁 Location: d:\MMB\backend\src\ranking\preference_model.py
- Class: PreferenceModel
- Features: LogisticRegression + StandardScaler
- Input: 7 audio features (energy, valence/happiness, tempo, loudness, danceability, acousticness, intensity)
- Output: Binary prediction (0=dislike, 1=like) + probability

## 6. User Preference Tracker
📁 Location: d:\MMB\backend\src\ranking\preference_model.py
- Class: UserPreferenceTracker
- Methods:
  - record_preference(song, feedback)
  - retrain()
  - get_stats()
  - predict_proba(song)

## 7. REST API (13 endpoints)
📁 Location: d:\MMB\backend\src\api\mood_api.py (459 lines)

### Mood Endpoints:
  GET /api/moods/health           - Health check
  GET /api/moods/moods            - List available moods
  GET /api/moods/stats            - Database statistics
  POST /api/moods/predict         - Predict mood from song features
  POST /api/moods/update-missing  - Compute moods for NULL rows
  POST /api/moods/update-all      - Recompute all moods

### Search Endpoints:
  GET /api/moods/search                  - Full-text search by query
  GET /api/moods/search/by-mood/{mood}   - Filter by mood
  GET /api/moods/search/by-genre/{genre} - Filter by genre
  GET /api/moods/search/suggest          - Autocomplete suggestions

### User Preference Endpoints:
  POST /api/moods/user/{user_id}/preference           - Record feedback
  POST /api/moods/user/{user_id}/train               - Train preference model
  GET /api/moods/user/{user_id}/predict/{song_id}    - Predict user preference
  GET /api/moods/user/{user_id}/stats                - User statistics
  GET /api/moods/user/{user_id}/recommend            - Get recommendations

## 8. TF-IDF Search Engine
📁 Location: d:\MMB\backend\src\search\tfidf_search.py (203 lines)
- Class: TFIDFSearchEngine
- Methods:
  - fit(songs)                    - Build TF-IDF matrix
  - search(query, top_k)          - Full-text search
  - search_by_field(field, value) - Filter by column
  - suggest(prefix, top_k)        - Autocomplete
- Vectorizer: TfidfVectorizer with char n-grams (2-3)
- Indexes: song_name, artist, genre, mood, intensity

---

📊 SUPPORTING MODULES

Mood Engine (Valence-Arousal)
📁 d:\MMB\backend\src\pipelines\mood_engine.py
- Computes V, A, mood classification
- Methods: valence_score(), arousal_score(), predict_one()

Database Layer
📁 d:\MMB\backend\src\repo\song_repo.py
- Methods: connect(), fetch_songs(), fetch_song_by_id(), update_song()

Services Layer
📁 d:\MMB\backend\src\services\mood_services.py
- DBMoodEngine wrapper class

Constants
📁 d:\MMB\backend\src\services\constants.py
- MOODS list, Song type, table names

---

🗄️ DATABASE

📁 d:\MMB\backend\src\database\music.db
- 30 Vietnamese songs
- 21 columns (6 core audio + 4 optional + 6 computed + 5 metadata)
- Schema: init_db.py

---

✅ QUICK REFERENCE

Component                      | File Path
-------------------------------|----------------------------------------------
Main FastAPI app               | backend/main.py
Health check                   | src/api/mood_api.py (line 30)
CORS middleware                | backend/main.py (line 20)
REST API endpoints             | src/api/mood_api.py
TF-IDF search                  | src/search/tfidf_search.py
Logistic regression            | src/ranking/preference_model.py
User preference tracker        | src/ranking/preference_model.py
Mood algorithm (VA)            | src/pipelines/mood_engine.py
Database                       | src/database/music.db
Schema initialization          | src/database/init_db.py
Bulk data update tool          | src/database/bulk_update.py

