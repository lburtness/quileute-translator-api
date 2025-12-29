from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import json
import os

app = FastAPI()

# Allow requests from local frontend and production site
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
    dictionary_data = json.load(f)

# Load normalized dataset
with open("normalized_quileute_dataset.json", encoding="utf-8") as f:
    normalized_data = json.load(f)

# Load lexical suffixes
with open("quileute_lexical_suffixes_expanded.json", encoding="utf-8") as f:
    suffix_data = json.load(f)


def search_dictionary(word: str):
    results = []
    for entry in dictionary_data:
        eng = str(entry.get("english", "")).strip().lower()
        if eng == word:
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


def search_normalized(word: str):
    word = word.strip().lower()
    for entry in normalized_data:
        eng = str(entry.get("english", "")).strip().lower()
        if eng == word:
            return {
                "english": entry.get("english", ""),
                "quileute": entry.get("quileute", ""),
                "phonetic": entry.get("phonetic", ""),
                "audio": None
            }
    return None


def search_suffixes(word: str):
    word = word.strip().lower()
    for entry in suffix_data:
        eng = str(entry.get("english", "")).strip().lower()
        if eng == word:
            return {
                "english": entry.get("english", ""),
                "quileute": entry.get("quileute", ""),
                "phonetic": entry.get("phonetic", ""),
                "audio": None
            }
    return None


@app.get("/translate")
def translate(sentence: str = Query(..., min_length=1)):
    words = sentence.strip().split()
    all_matches = []

    for word in words:
        word_lc = word.lower().strip()
        print(f"\n🔍 Looking up: {word_lc}")

        matches = search_dictionary(word_lc)
        if matches:
            print("✅ Found in original dictionary")
            all_matches.extend(matches)
            continue

        normalized_match = search_normalized(word_lc)
        if normalized_match:
            print("✅ Found in normalized dataset")
            all_matches.append(normalized_match)
            continue

        suffix_match = search_suffixes(word_lc)
        if suffix_match:
            print("✅ Found in lexical suffixes")
            all_matches.append(suffix_match)
            continue

        print("❌ No match found")
        all_matches.append({
            "english": word,
            "quileute": "[hypothetical]",
            "phonetic": "[unknown]",
            "audio": None
        })

    # Build aggregate response
    unicode_combined = " ".join(entry["quileute"] for entry in all_matches)
    phonetic_combined = " ".join(entry["phonetic"] for entry in all_matches)

    return {
        "quileute_unicode": unicode_combined,
        "phonetic": phonetic_combined,
        "morphology": all_matches
    }
