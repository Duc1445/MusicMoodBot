"""Logistic Regression model for user preference prediction."""

from __future__ import annotations

from typing import List, Dict, Optional, Tuple
import pickle
import numpy as np
from pathlib import Path

from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score


class PreferenceModel:
    """
    Logistic Regression model for predicting user preference.
    
    Predicts if user will like a song based on:
    - Audio features (energy, valence, tempo, loudness, etc.)
    - Mood classification
    - Genre
    """
    
    def __init__(self, random_state: int = 42):
        """
        Initialize preference model.
        
        Args:
            random_state: Random seed for reproducibility
        """
        self.model: Optional[LogisticRegression] = None
        self.scaler = StandardScaler()
        self.feature_names: List[str] = []
        self.is_fitted = False
        self.random_state = random_state
        
    def fit(
        self,
        songs: List[Dict],
        preferences: List[int]
    ) -> PreferenceModel:
        """
        Train preference model on user feedback.
        
        Args:
            songs: List of song dictionaries
            preferences: List of binary labels (0=dislike, 1=like)
            
        Returns:
            self for chaining
            
        Example:
            songs = [
                {"energy": 80, "valence": 70, "tempo": 120, ...},
                {"energy": 30, "valence": 35, "tempo": 72, ...},
            ]
            preferences = [1, 0]  # Like first, dislike second
            
            model = PreferenceModel()
            model.fit(songs, preferences)
        """
        if len(songs) != len(preferences):
            raise ValueError("Songs and preferences must have same length")
        
        # Extract features
        X = self._extract_features(songs)
        y = np.array(preferences)
        
        # Standardize features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train logistic regression
        self.model = LogisticRegression(
            random_state=self.random_state,
            max_iter=1000,
            class_weight='balanced'  # Handle imbalanced data
        )
        self.model.fit(X_scaled, y)
        
        self.is_fitted = True
        return self
    
    def predict(self, song: Dict) -> int:
        """
        Predict if user will like a song.
        
        Args:
            song: Song dictionary
            
        Returns:
            0 = dislike, 1 = like
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted. Call fit() first.")
        
        X = self._extract_features([song])
        X_scaled = self.scaler.transform(X)
        prediction = self.model.predict(X_scaled)[0]
        
        return int(prediction)
    
    def predict_proba(self, song: Dict) -> Tuple[float, float]:
        """
        Predict probability of user liking a song.
        
        Args:
            song: Song dictionary
            
        Returns:
            (prob_dislike, prob_like) - both in [0, 1]
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted. Call fit() first.")
        
        X = self._extract_features([song])
        X_scaled = self.scaler.transform(X)
        proba = self.model.predict_proba(X_scaled)[0]
        
        return float(proba[0]), float(proba[1])
    
    def batch_predict(self, songs: List[Dict]) -> List[int]:
        """Predict for multiple songs."""
        return [self.predict(song) for song in songs]
    
    def batch_predict_proba(self, songs: List[Dict]) -> List[Tuple[float, float]]:
        """Predict probabilities for multiple songs."""
        return [self.predict_proba(song) for song in songs]
    
    def score(
        self,
        songs: List[Dict],
        preferences: List[int]
    ) -> Dict[str, float]:
        """
        Evaluate model performance.
        
        Args:
            songs: Test songs
            preferences: True preferences
            
        Returns:
            Dictionary with accuracy, precision, recall
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted. Call fit() first.")
        
        predictions = self.batch_predict(songs)
        preferences = np.array(preferences)
        
        metrics = {
            'accuracy': float(accuracy_score(preferences, predictions)),
            'precision': float(precision_score(preferences, predictions, zero_division=0)),
            'recall': float(recall_score(preferences, predictions, zero_division=0))
        }
        
        return metrics
    
    def _extract_features(self, songs: List[Dict]) -> np.ndarray:
        """Extract numerical features from songs."""
        feature_keys = [
            'energy', 'happiness', 'tempo', 'loudness',
            'danceability', 'acousticness', 'intensity'
        ]
        
        if not self.feature_names:
            self.feature_names = feature_keys
        
        features = []
        for song in songs:
            values = []
            for key in feature_keys:
                val = song.get(key, 50)
                # Handle empty strings and None values
                if val is None or val == '':
                    val = 50
                try:
                    values.append(float(val))
                except (ValueError, TypeError):
                    values.append(50.0)  # Default to 50 if conversion fails
            features.append(values)
        
        return np.array(features)
    
    def save(self, path: str) -> None:
        """Save model and scaler to file."""
        with open(path, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'scaler': self.scaler,
                'feature_names': self.feature_names
            }, f)
    
    def load(self, path: str) -> None:
        """Load model and scaler from file."""
        with open(path, 'rb') as f:
            data = pickle.load(f)
            self.model = data['model']
            self.scaler = data['scaler']
            self.feature_names = data['feature_names']
            self.is_fitted = True


class UserPreferenceTracker:
    """
    Track user preferences over time and retrain model.
    
    Stores user feedback and manages model training/updating.
    """
    
    def __init__(self, user_id: str = "default"):
        """
        Initialize tracker.
        
        Args:
            user_id: Unique user identifier
        """
        self.user_id = user_id
        self.feedback: List[Tuple[Dict, int]] = []  # (song, preference)
        self.model = PreferenceModel()
    
    def record_preference(self, song: Dict, preference: int) -> None:
        """
        Record user preference for a song.
        
        Args:
            song: Song dictionary
            preference: 0 (dislike) or 1 (like)
        """
        if preference not in [0, 1]:
            raise ValueError("Preference must be 0 or 1")
        self.feedback.append((song, preference))
    
    def retrain(self) -> None:
        """Retrain model on collected feedback."""
        if len(self.feedback) < 3:
            print(f"[WARNING] Need at least 3 samples to train. Got {len(self.feedback)}")
            return
        
        songs, preferences = zip(*self.feedback)
        self.model.fit(list(songs), list(preferences))
    
    def predict_preference(self, song: Dict) -> float:
        """
        Predict user preference probability.
        
        Args:
            song: Song to predict
            
        Returns:
            Probability user will like (0-1)
        """
        if not self.model.is_fitted:
            return 0.5  # Default to neutral if no data
        
        _, prob_like = self.model.predict_proba(song)
        return prob_like
    
    def get_stats(self) -> Dict:
        """Get feedback statistics."""
        if not self.feedback:
            return {'total': 0, 'likes': 0, 'dislikes': 0}
        
        likes = sum(1 for _, pref in self.feedback if pref == 1)
        dislikes = len(self.feedback) - likes
        
        return {
            'total': len(self.feedback),
            'likes': likes,
            'dislikes': dislikes,
            'like_ratio': likes / len(self.feedback) if self.feedback else 0
        }
