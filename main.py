from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import json
import os

app = FastAPI()

# Allow frontend access from localhost and production domain
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

# Load both dictionaries
with open("QuilDict_Unicode.json", encoding="utf-8") as f:
    legacy_dict = json.load(f)

with open("normalized_quileute_dataset.json", encoding="utf-8") as f:
    normalized_dict = json.load(f)

# --- Helper: Search full phrase in normalized dataset
def search_full_phrase(phrase):
    for entry in normalized_dict:
        if entry.get("english", "").lower().strip() == phrase.lower().strip():
            return entry
    return None

# --- Helper: Search single word in normalized dataset
def search_normalized_word(word):
    for entry in normalized_dict:
        if entry.get("english", "").lower().strip() == word.lower().strip():
            return {
                "english": entry["english"],
                "quileute": entry["quileute_unicode"],
                "phonetic": entry.get("phonetic", "[unknown]"),
                "audio": entry.get("audio", None)
            }
    return None

# --- Helper: Search single word in legacy dictionary
def search_legacy(word):
    for entry in legacy_dict:
        if isinstance(entry, dict):
            if entry.get("english", "").lower().strip() == word.lower().strip():
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

                return {
                    "english": entry.get("english", ""),
                    "quileute": entry.get("quileute_unicode", entry.get("quileute", "")),
                    "phonetic": entry.get("pronunciation", "[unknown]"),
                    "audio": audio_url
                }
    return None

# --- Translation endpoint
@app.get("/translate")
def translate(sentence: str = Query(..., min_length=1)):
    sentence = sentence.strip()
    
    # 1. Try full-phrase match in normalized dataset
    full_match = search_full_phrase(sentence)
    if full_match:
        return {
            "quileute_unicode": full_match["quileute_unicode"],
            "phonetic": full_match.get("phonetic", "[unknown]"),
            "morphology": full_match.get("morphology", [])
        }

    # 2. Tokenize and search word-by-word
    words = sentence.split()
    morphology = []
    quileute_parts = []
    phonetic_parts = []

    for word in words:
        # Try normalized word first
        result = search_normalized_word(word)

        # If not found, try legacy
        if not result:
            result = search_legacy(word)

        # If still not found, return fallback
        if not result:
            result = {
                "english": word,
                "quileute": "[hypothetical]",
                "phonetic": "[unknown]",
                "audio": None
            }

        morphology.append(result)
        quileute_parts.append(result["quileute"])
        phonetic_parts.append(result["phonetic"])

    return {
        "quileute_unicode": " ".join(quileute_parts),
        "phonetic": " ".join(phonetic_parts),
        "morphology": morphology
    }
