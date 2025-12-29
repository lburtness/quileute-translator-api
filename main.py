from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Optional
import json
import os

app = FastAPI()

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Load both datasets at startup
with open("normalized_quileute_dataset.json", encoding="utf-8") as f:
    normalized_dict = json.load(f)

with open("QuilDict_Unicode.json", encoding="utf-8") as f:
    original_dict = json.load(f)

# Helper to compute audio URL
def get_audio_url(mp3_filename: Optional[str]) -> Optional[str]:
    if not mp3_filename:
        return None
    try:
        number = int(mp3_filename.split(".")[0])
        folder = number // 1000
        return f"https://quileutelanguage.com/data/audio/{folder}/{mp3_filename}"
    except ValueError:
        return None

# Lookup in normalized dictionary
def search_normalized(word: str):
    word = word.lower().strip()

    for entry in normalized_dict:
        # Safely pull candidate match fields
        base = entry.get("base_english", "").lower().strip()
        norm = entry.get("normalized_english", "").lower().strip()

        # Match either base or normalized
        if word == base or word == norm:
            return {
                "english": norm or base,
                "quileute": entry.get("quileute_unicode", ""),
                "phonetic": entry.get("quileute_phonetic", ""),
                "audio": entry.get("audio", None),
                "person": entry.get("person", ""),
                "tense": entry.get("tense", ""),
                "aspect": entry.get("aspect", ""),
            }

    return None


# Lookup in original dictionary
def search_original(word: str) -> Optional[Dict]:
    word = word.lower().strip()
    for entry in original_dict:
        if isinstance(entry, dict) and entry.get("english", "").lower().strip() == word:
            return {
                "english": word,
                "quileute": entry.get("quileute_unicode", entry.get("quileute", "")),
                "phonetic": entry.get("pronunciation", ""),
                "audio": get_audio_url(entry.get("audio_file", {}).get("mp3"))
            }
    return None

@app.get("/")
def root():
    return {"status": "Quileute Translator API is live"}

@app.get("/translate")
def translate(sentence: str = Query(..., min_length=1)):
    words = sentence.strip().split()
    results = []

    for word in words:
        entry = search_normalized(word)
        if not entry:
            entry = search_original(word)

        if not entry:
            entry = {
                "english": word,
                "quileute": "[hypothetical]",
                "phonetic": "[unknown]",
                "audio": None
            }

        results.append(entry)

    return {
        "quileute_unicode": " ".join(e["quileute"] for e in results),
        "phonetic": " ".join(e["phonetic"] for e in results),
        "morphology": results
    }
