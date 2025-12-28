from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import json

app = FastAPI()

# CORS middleware
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

# Load the dictionary at startup
with open("QuilDict_Unicode.json", encoding="utf-8") as f:
    dictionary = json.load(f)

# Safe lookup of dictionary entries
def find_entries(english_word: str):
    results = []
    word_lower = english_word.strip().lower()

    for entry in dictionary:
        # Skip invalid entries
        if not isinstance(entry, dict):
            continue

        english_value = entry.get("english")
        if not isinstance(english_value, str):
            continue

        if english_value.strip().lower() != word_lower:
            continue

        # Handle audio
        audio_file = entry.get("audio_file", {}).get("mp3")
        audio_url = None

        if isinstance(audio_file, str):
            try:
                number = int(audio_file.split(".")[0])
                folder = number // 1000
                audio_url = f"https://quileutelanguage.com/data/audio/{folder}/{audio_file}"
            except ValueError:
                pass  # Leave audio_url as None

        results.append({
            "english": english_value,
            "quileute": entry.get("quileute_unicode", entry.get("quileute", "")),
            "phonetic": entry.get("pronunciation", ""),
            "audio": audio_url
        })

    return results

@app.get("/")
def root():
    return {"status": "Quileute Translator API is live"}

@app.get("/translate")
def translate(sentence: str = Query(..., min_length=1)):
    words = sentence.strip().lower().split()
    all_matches = []
    i = 0
    n = len(words)

    while i < n:
        found = False
        # Try longest possible phrase from i
        for j in range(n, i, -1):
            phrase = " ".join(words[i:j])
            matches = find_entries(phrase)
            if matches:
                all_matches.extend(matches)
                i = j  # advance past matched phrase
                found = True
                break

        if not found:
            all_matches.append({
                "english": words[i],
                "quileute": "[hypothetical]",
                "phonetic": "[unknown]",
                "audio": None
            })
            i += 1

    return {
        "quileute_unicode": " ".join(entry["quileute"] for entry in all_matches),
        "phonetic": " ".join(entry["phonetic"] for entry in all_matches),
        "morphology": all_matches
    }
