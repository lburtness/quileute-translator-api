from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Dict
import json
import os

app = FastAPI()

# Allow CORS for local dev and production
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

# Load original dictionary
with open("QuilDict_Unicode.json", encoding="utf-8") as f:
    dictionary = json.load(f)

# Load normalized dataset
with open("normalized_quileute_dataset.json", encoding="utf-8") as f:
    normalized_data = json.load(f)

# Load lexical suffixes
with open("quileute_lexical_suffixes_expanded.json", encoding="utf-8") as f:
    lexical_suffixes = json.load(f)

# -----------------------
# Helper: normalized data
# -----------------------
def search_normalized(word: str) -> Optional[Dict]:
    for entry in normalized_data:
        try:
            entry_english = entry["english"].strip().lower()
            if entry_english == word.lower():
                return entry
        except Exception:
            continue
    return None

# -----------------------
# Helper: original dictionary
# -----------------------
def search_dictionary(word: str) -> Optional[Dict]:
    for entry in dictionary:
        try:
            entry_english = entry.get("english", "").strip().lower()
            if entry_english == word.lower():
                audio_file = entry.get("audio_file", {}).get("mp3")
                if audio_file:
                    try:
                        num = int(audio_file.split(".")[0])
                        folder = num // 1000
                        audio_url = f"https://quileutelanguage.com/data/audio/{folder}/{audio_file}"
                    except ValueError:
                        audio_url = None
                else:
                    audio_url = None

                return {
                    "english": word,
                    "quileute": entry.get("quileute_unicode", entry.get("quileute", "[hypothetical]")),
                    "phonetic": entry.get("pronunciation", "[unknown]"),
                    "audio": audio_url,
                    "source": "dictionary"
                }
        except Exception:
            continue
    return None

# -----------------------
# Helper: lexical suffixes
# -----------------------
def search_suffix(word: str) -> Optional[Dict]:
    for entry in lexical_suffixes:
        entry_english = entry.get("english", "").strip().lower()
        if entry_english == word.lower():
            return {
                "english": word,
                "quileute": entry.get("quileute", "[hypothetical]") + " (suffix)",
                "phonetic": entry.get("pronunciation", "[unknown]"),
                "audio": None,
                "source": "suffix"
            }
    return None

# -----------------------
# Translate Endpoint
# -----------------------
@app.get("/translate")
def translate(sentence: str = Query(..., min_length=1)):
    words = sentence.strip().split()
    results = []

    for word in words:
        # 1. Normalized dataset
        normalized = search_normalized(word)
        if normalized:
            results.append({
                "english": word,
                "quileute": normalized.get("quileute", "[hypothetical]"),
                "phonetic": normalized.get("phonetic", "[unknown]"),
                "audio": normalized.get("audio"),
                "source": "normalized"
            })
            continue

        # 2. Original dictionary
        dictionary_entry = search_dictionary(word)
        if dictionary_entry:
            results.append(dictionary_entry)
            continue

        # 3. Lexical suffix fallback
        suffix_entry = search_suffix(word)
        if suffix_entry:
            results.append(suffix_entry)
            continue

        # 4. No match at all
        results.append({
            "english": word,
            "quileute": "[hypothetical]",
            "phonetic": "[unknown]",
            "audio": None,
            "source": "not found"
        })

    return {
        "quileute_unicode": " ".join([r["quileute"] for r in results]),
        "phonetic": " ".join([r["phonetic"] for r in results]),
        "morphology": results
    }

# Optional root
@app.get("/")
def root():
    return {"status": "Quileute Translator API is live"}
