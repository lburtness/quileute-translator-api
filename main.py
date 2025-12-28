from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict
import uvicorn
import json
import os

app = FastAPI()

# CORS settings — allow any origin for testing/development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load the dictionary once at startup
dictionary_data: List[Dict] = []

@app.on_event("startup")
def load_dictionary():
    global dictionary_data
    file_path = os.path.join(os.path.dirname(__file__), "QuilDict_Unicode.json")
    print("Loading dictionary from:", file_path)
    with open(file_path, "r", encoding="utf-8") as f:
        dictionary_data = json.load(f)

@app.get("/")
def root():
    return {"status": "Quileute Translator API is live"}

def find_entry(word: str) -> Dict:
    word = word.strip().lower()
    for entry in dictionary_data:
        if entry.get("english", "").strip().lower() == word:
            return entry
    return None

@app.get("/translate")
def translate(sentence: str = Query(..., description="English sentence to translate")):
    words = sentence.strip().split()
    quileute_output = []
    phonetic_output = []
    morphology = []

    for word in words:
        match = find_entry(word)
        if match:
            quileute_word = match.get("quileute_unicode", "[hypothetical]")
            phonetic = match.get("pronunciation", "[unknown]")
            audio = match.get("audio_file", {}).get("mp3")

            quileute_output.append(quileute_word)
            phonetic_output.append(phonetic)

            morphology.append({
                "english": word,
                "quileute": quileute_word,
                "phonetic": phonetic,
                "audio": audio
            })
        else:
            morphology.append({
                "english": word,
                "quileute": "[hypothetical]",
                "phonetic": "[unknown]",
                "audio": None
            })

    return {
        "quileute_unicode": " ".join(quileute_output) if quileute_output else "[hypothetical]",
        "phonetic": " ".join(phonetic_output) if phonetic_output else "[unknown]",
        "morphology": morphology
    }

# Uncomment to run locally
# if __name__ == "__main__":
#     uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
