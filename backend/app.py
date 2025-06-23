from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import joblib
import numpy as np
import pandas as pd
import os
import random

# Load model components
try:
    tfidf = joblib.load("tfidf_vectorizer.pkl")
except Exception as e:
    print(f"Error loading tfidf_vectorizer.pkl: {e}")
    tfidf = None

try:
    label_encoder = joblib.load("label_encoder.pkl")
except Exception as e:
    print(f"Error loading label_encoder.pkl: {e}")
    label_encoder = None

try:
    rf_model = joblib.load("random_forest_model.pkl")
except Exception as e:
    print(f"Error loading random_forest_model.pkl: {e}")
    rf_model = None

# Load datasets
try:
    movie_df = pd.read_csv("movies.csv")
    movie_df['Genre_List'] = movie_df['Genre'].apply(lambda x: [g.strip() for g in str(x).split(',')])
except Exception as e:
    print(f"Error loading movies.csv: {e}")
    movie_df = pd.DataFrame()

try:
    series_df = pd.read_csv("series.csv")
    series_df['Genre'] = series_df['Genre'].astype(str)
except Exception as e:
    print(f"Error loading series.csv: {e}")
    series_df = pd.DataFrame()

try:
    songs_df = pd.read_csv("songs.csv")
except Exception as e:
    print(f"Error loading songs.csv: {e}")
    songs_df = pd.DataFrame()

# Emotion-to-genre mappings
emotion_movie_map = {
    'anger': ['Action', 'Crime', 'War', 'Western'],
    'fear': ['Biography','Horror', 'Thriller'],
    'joy': ['Animation', 'Comedy', 'Music', 'Musical', 'Sport'],
    'love': ['Family', 'Romance'],
    'sad': ['Drama', 'Film-Noir', 'History'],
    'surprise': ['Adventure', 'Fantasy', 'Mystery', 'Sci-Fi']
}

emotion_series_map = {
    "anger": ["Action & Adventure", "Crime", "Thriller", "Cult", "Sport"],
    "fear": ["Horror", "Mystery", "Thriller", "Science-Fiction", "Crime"],
    "joy": ["Comedy", "Animation", "Stand-up & Talk", "Game Show", "Food", "Travel"],
    "love": ["Romance", "Musical", "Family", "LGBTQ"],
    "sad": ["Biography", "Drama", "Documentary", "History", "Children"],
    "surprise": ["Science-Fiction", "Anime", "Fantasy", "Cult", "Reality"]
}

# Song filter function
def song_matches_emotion(row, emotion):
    v, e, d, t, a, s = row['valence'], row['energy'], row['danceability'], row['tempo'], row['acousticness'], row['speechiness']
    if emotion == 'sad':
        return v < 0.3 and e < 0.6 and t < 100
    elif emotion == 'anger':
        return v < 0.4 and e > 0.85 and t > 120
    elif emotion == 'fear':
        return v < 0.4 and s > 0.06 and t < 110
    elif emotion == 'surprise':
        return 0.4 <= v <= 0.6 and e > 0.85 and d > 0.65 and t > 115
    elif emotion == 'joy':
        return v > 0.6 and e > 0.75 and d > 0.65 and t > 110
    elif emotion == 'love':
        return v > 0.5 and d > 0.6 and a > 0.05
    return False

# FastAPI app
app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static frontend files
frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../frontend"))
app.mount("/static", StaticFiles(directory=frontend_path), name="static")

@app.get("/")
def read_index():
    return FileResponse(os.path.join(frontend_path, "index.html"))

# Request structure
class SentenceInput(BaseModel):
    sentence: str

@app.post("/predict/")
def predict_emotion(data: SentenceInput):
    if not tfidf or not label_encoder or not rf_model:
        raise HTTPException(status_code=500, detail="Model files not loaded properly.")

    try:
        X_input = tfidf.transform([data.sentence])
        proba = rf_model.predict_proba(X_input)[0]
        predicted_emotion = label_encoder.inverse_transform([np.argmax(proba)])[0]

        emotion_percentages = {
            emotion: round(prob * 100, 2)
            for emotion, prob in zip(label_encoder.classes_, proba)
        }

        # Recommendations
        movie = recommend_movie(predicted_emotion)
        series = recommend_series(predicted_emotion)
        song = recommend_song(predicted_emotion)

        return {
            "predicted_emotion": predicted_emotion,
            "emotion_percentages": emotion_percentages,
            "recommendations": {
                "movie": movie,
                "series": series,
                "song": song
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {e}")

# Movie recommendation
def recommend_movie(emotion: str):
    genres = set(emotion_movie_map.get(emotion.lower(), []))
    matches = movie_df[movie_df['Genre_List'].apply(lambda g: any(genre in genres for genre in g))]
    if matches.empty:
        return {"message": "No movie found"}
    return matches.sample(1).drop(columns=['Genre_List']).to_dict(orient="records")[0]

# Series recommendation
def recommend_series(emotion: str):
    genres = emotion_series_map.get(emotion.lower(), [])
    matches = series_df[series_df['Genre'].apply(lambda g: any(gen in g for gen in genres))]
    if matches.empty:
        return {"message": "No series found"}
    return matches.sample(1).to_dict(orient="records")[0]

# Song recommendation
def recommend_song(emotion: str):
    matches = songs_df[songs_df.apply(lambda row: song_matches_emotion(row, emotion), axis=1)]
    if matches.empty:
        return {"message": "No song found"}
    song = matches.sample(1).iloc[0]
    return {
        "track_name": song['track_name'],
        "artist": song['track_artist'],
        "valence": song['valence'],
        "energy": song['energy'],
        "danceability": song['danceability'],
        "tempo": song['tempo'],
        "acousticness": song['acousticness'],
        "speechiness": song['speechiness']
    }
