# 🎵 Database Schema - Optimized for VA Mood Algorithm

## Current Schema (21 Columns)

### 1. **Identifiers**
| Column | Type | Purpose |
|--------|------|---------|
| `song_id` | INTEGER (PK) | Unique song identifier |
| `song_name` | TEXT | Song title (Vietnamese) |
| `artist` | TEXT | Artist/Band name |
| `genre` | TEXT | Music genre (Pop, Rock, Ballad, etc) |
| `source` | TEXT | Data source (tunebat, spotify, youtube, manual) |

### 2. **Core Audio Features** (Required for Algorithm)
All values are 0-100 scale unless otherwise noted.

| Column | Type | Range | Algorithm Use | How to Get |
|--------|------|-------|---|---|
| `happiness` | INTEGER | 0-100 | **V = 0.85 × happiness + 0.15 × danceability** | TuneBat, Spotify API |
| `danceability` | INTEGER | 0-100 | V calculation (20% weight), A calculation | TuneBat, Spotify API |
| `energy` | INTEGER | 0-100 | **A = energy + (loud + 60)/12 + weights...** | TuneBat, Spotify API |
| `loudness` | INTEGER | -60 to 0 | A calculation (loudness normalization) | TuneBat (dBFS) |
| `tempo` | INTEGER | 0-250 BPM | A calculation (tempo normalization) | TuneBat (BPM) |
| `acousticness` | INTEGER | 0-100 | A = A - 0.3 × acousticness (penalty) | TuneBat, Spotify API |

**What is V, A?**
- **V (Valence)** = Happiness/Positivity score (0-100)
- **A (Arousal)** = Energy/Intensity score (0-100)

### 3. **Enhanced Features** (Optional - for future ML improvements)
These fields are not currently used but good to have for future model training.

| Column | Type | Range | Purpose | How to Get |
|--------|------|-------|---------|-----------|
| `speechiness` | INTEGER | 0-100 | Detect spoken words vs music | TuneBat, Spotify API |
| `instrumentalness` | INTEGER | 0-100 | Detect presence of vocals | TuneBat, Spotify API |
| `liveness` | INTEGER | 0-100 | Detect live performance | TuneBat, Spotify API |
| `popularity` | INTEGER | 0-100 | Global/chart ranking | Spotify API only |

### 4. **Computed Mood Scores** (Auto-filled by Algorithm)
These are **calculated automatically** when you call the mood prediction endpoints. You **don't need to fill these manually**.

| Column | Type | Formula/Source | When Calculated |
|--------|------|---|---|
| `valence_score` | REAL | 0.85 × happiness + 0.15 × danceability | When mood_api.predict_one() is called |
| `arousal_score` | REAL | energy + weights × (tempo/loud/dance - acoustic_penalty) | When mood_api.predict_one() is called |
| `mood` | TEXT | Classification: "energetic" \| "happy" \| "sad" \| "stress" \| "angry" | When mood_api.predict_one() is called |
| `intensity` | INTEGER | 1=low \| 2=medium \| 3=high (derived from arousal_score) | When mood_api.predict_one() is called |
| `mood_score` | REAL | Gaussian probability (0-1) | When mood_api.predict_one() is called |
| `mood_confidence` | REAL | Confidence of the prediction (0-1) | When mood_api.predict_one() is called |

## 📊 Mood Classification Logic

```
Based on Valence (V) and Arousal (A) thresholds:

          High V
            ▲
    Happy  │  Energetic
            │
    ────────┼────────► High A
            │
    Sad    │  Stress/Angry
          Low V
```

### Mood Rules:
```python
if V ≥ 50 and A ≥ 50:
    mood = "energetic"      # High energy, high happiness
elif V ≥ 50 and A < 50:
    mood = "happy"          # Low energy, high happiness
elif V < 50 and A < 50:
    mood = "sad"            # Low energy, low happiness
elif V < 50 and A ≥ 50:
    if loudness ≥ -5 and tempo ≥ 120:
        mood = "angry"      # High loudness & tempo = angry
    else:
        mood = "stress"     # Otherwise = stressed
```

## 🎯 Which Columns to Fill from TuneBat

**You only need to fill 6 core columns from TuneBat:**

1. ✅ **happiness** (0-100) - Valence in TuneBat
2. ✅ **danceability** (0-100) - Danceability in TuneBat
3. ✅ **energy** (0-100) - Energy in TuneBat
4. ✅ **loudness** (-60 to 0) - Loudness in TuneBat (dBFS)
5. ✅ **tempo** (0-250) - Tempo in TuneBat (BPM)
6. ✅ **acousticness** (0-100) - Acousticness in TuneBat

**Optional (skip if not available):**
- `speechiness` - From Spotify API
- `instrumentalness` - From Spotify API
- `liveness` - From Spotify API
- `popularity` - From Spotify API only

**Never fill (auto-calculated):**
- ❌ `valence_score` - Auto
- ❌ `arousal_score` - Auto
- ❌ `mood` - Auto
- ❌ `intensity` - Auto
- ❌ `mood_score` - Auto
- ❌ `mood_confidence` - Auto

## 🔄 Update Strategy

1. **Initial Load**: Insert all 30 songs with core 6 columns
2. **Run Prediction**: Call `POST /api/moods/update-all` to auto-fill computed columns
3. **Verify**: Check `GET /api/moods/stats` to confirm moods are assigned
4. **Enhance**: Optionally add speechiness/instrumentalness/liveness later

## 📝 Example Song Entry

```json
{
  "song_name": "Lạc Trôi",
  "artist": "Sơn Tùng MTP",
  "genre": "Pop",
  "happiness": 17,
  "danceability": 64,
  "energy": 87,
  "loudness": -4,
  "tempo": 135,
  "acousticness": 33,
  "source": "tunebat"
  
  // These will be auto-filled:
  // "valence_score": null
  // "arousal_score": null
  // "mood": null
  // "intensity": null
  // "mood_confidence": null
}
```

## 🚀 Next Steps

1. ✅ Database schema is ready
2. 📊 Fill in TuneBat data for all 30 songs
3. 🔮 Run mood prediction to populate computed columns
4. 🎯 Test search and recommendation APIs
