from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import json
import os

app = FastAPI()

# Allow CORS for local development and deployment domains
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
with open("QuilDict_Unicode.json", encoding="utf-8") as f:
    dictionary = json.load(f)

def find_entries(english_word: str):
    results = []
    for entry in dictionary:
        if entry.get("english", "").lower() == english_word.lower():
            audio_file = entry.get("audio_file", {}).get("mp3")
            if audio_file:
                try:
                    audio_number = int(audio_file.split(".")[0])
                    folder = audio_number // 1000
                    audio_url = f"https://quileutelanguage.com/data/audio/{folder}/{audio_file}"
                except ValueError:
                    audio_url = None
            else:
                audio_url = None

            results.append({
                "english": entry.get("english", ""),
                "quileute": entry.get("quileute_unicode", entry.get("quileute", "")),
                "phonetic": entry.get("pronunciation", ""),
                "audio": audio_url
            })
    return results

@app.get("/translate")
def translate(sentence: str = Query(..., min_length=1)):
    words = sentence.strip().split()
    all_matches = []

    for word in words:
        matches = find_entries(word)
        all_matches.extend(matches)

    if not all_matches:
        return {
            "quileute_unicode": "[hypothetical]",
            "phonetic": "[unknown]",
            "morphology": [{
                "english": words[0] if words else "[unknown]",
                "quileute": "[hypothetical]",
                "phonetic": "[unknown]",
                "audio": None
            }]
        }

    return {
        "quileute_unicode": " ".join(entry["quileute"] for entry in all_matches),
        "phonetic": " ".join(entry["phonetic"] for entry in all_matches),
        "morphology": all_matches
    }
