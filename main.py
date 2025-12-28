from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict
import uvicorn
import json
import requests  # ← properly import at top
import unicodedata

app = FastAPI()

# Allow frontend on any domain to connect (for now, for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load the dictionary at startup
dictionary_data: List[Dict] = []

@app.on_event("startup")
def load_dictionary():
    global dictionary_data
    url = "https://quileutelanguage.com/data/QuilDict_Unicode.json"
    response = requests.get(url)
    response.raise_for_status()
    dictionary_data = response.json()

# Optional root endpoint to avoid 502 from Render
@app.get("/")
def root():
    return {"status": "Quileute Translator API is live"}

# Utility function to normalize and search entries
def find_entries(english: str) -> List[Dict]:
    english = english.lower().strip()
    return [entry for entry in dictionary_data if entry["english"].lower().strip() == english]

# Core translation endpoint
@app.get("/translate")
def translate(sentence: str = Query(..., description="English sentence to translate")):
    words = sentence.strip().split()
    output_quileute = []
    output_phonetic = []
    morphology = []

    for word in words:
        matches = find_entries(word)
        if matches:
            # Use the first matching dictionary entry
            match = matches[0]
            output_quileute.append(match["quileute_unicode"])
            output_phonetic.append(match["pronunciation"])
            morphology.append({
                "english": word,
                "quileute": match["quileute_unicode"],
                "phonetic": match["pronunciation"],
                "audio": match.get("audio_file", {}).get("mp3", None)
            })
        else:
            morphology.append({
                "english": word,
                "quileute": "[hypothetical]",
                "phonetic": "[unknown]",
                "audio": None
            })

    return {
        "quileute_unicode": " ".join(output_quileute) if output_quileute else "[hypothetical]",
        "phonetic": " ".join(output_phonetic) if output_phonetic else "[unknown]",
        "morphology": morphology
    }

# Uncomment this if running locally for testing
# if __name__ == "__main__":
#     uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
