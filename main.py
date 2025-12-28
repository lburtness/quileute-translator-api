from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict
import json
import os

app = FastAPI()

# Enable CORS for frontend access (local + deployed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:8000",
        "https://quileutelanguage.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load the dictionary JSON once at startup
try:
    with open("QuilDict_Unicode.json", encoding="utf-8") as f:
        dictionary: List[Dict] = json.load(f)
except Exception as e:
    print("Error loading dictionary:", e)
    dictionary = []

# Optional health check route
@app.get("/")
def root():
    return {"status": "Quileute Translator API is live"}

# Internal helper to find matching words and build audio URL
def find_entries(english_word: str) -> List[Dict]:
    results = []
    word_lower = english_word.strip().lower()

    for entry in dictionary:
        entry_english = entry.get("english", "").strip().lower()
        if entry_english == word_lower:
            # Audio path logic
            audio_file = entry.get("audio_file", {}).get("mp3")
            audio_url = None

            if audio_file:
                try:
                    audio_number = int(audio_file.split(".")[0])
                    folder = audio_number // 1000
                    audio_url = f"https://quileutelanguage.com/data/audio/{folder}/{audio_file}"
                except ValueError:
                    pass

            results.append({
                "english": entry.get("english", ""),
                "quileute": entry.get("quileute_unicode", entry.get("quileute", "")),
                "phonetic": entry.get("pronunciation", ""),
                "audio": audio_url
            })

    return results

# Translation endpoint
@app.get("/translate")
def translate(sentence: str = Query(..., min_length=1)):
    words = sentence.strip().split()
    results = []

    for word in words:
        entries = find_entries(word)
        if entries:
            results.extend(entries)
        else:
            results.append({
                "english": word,
                "quileute": "[hypothetical]",
                "phonetic": "[unknown]",
                "audio": None
            })

    return {
        "quileute_unicode": " ".join(entry["quileute"] for entry in results),
        "phonetic": " ".join(entry["phonetic"] for entry in results),
        "morphology": results
    }
