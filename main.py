from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict
import json
import re

app = FastAPI()

# Enable CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict later for security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load the dictionary
with open("QuilDict_Unicode.json", encoding="utf-8") as f:
    dictionary = json.load(f)

# 🧹 Utility: Clean and tokenize English
def tokenize(text: str) -> List[str]:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s]", "", text)  # remove punctuation
    return text.split()

# 🔍 Enhanced matcher
def find_entries(input_text: str) -> List[Dict]:
    input_tokens = tokenize(input_text)
    matches = []

    for entry in dictionary:
        english = entry.get("english", "")
        if not isinstance(english, str):
            continue  # skip malformed entries

        # Tokenize and normalize dictionary gloss
        gloss_variants = [g.strip() for g in english.lower().split(",")]

        for gloss in gloss_variants:
            gloss_tokens = tokenize(gloss)

            # Full phrase match
            if input_tokens == gloss_tokens:
                match_type = "exact"
            # Partial match (one is subset of the other)
            elif set(input_tokens).issubset(set(gloss_tokens)) or set(gloss_tokens).issubset(set(input_tokens)):
                match_type = "partial"
            # Token overlap (at least one word in common)
            elif set(input_tokens) & set(gloss_tokens):
                match_type = "overlap"
            else:
                continue  # no match

            # Construct result
            audio_file = entry.get("audio_file", {}).get("mp3")
            audio_url = None
            if audio_file:
                try:
                    num = int(audio_file.split(".")[0])
                    folder = num // 1000
                    audio_url = f"https://quileutelanguage.com/data/audio/{folder}/{audio_file}"
                except ValueError:
                    pass

            matches.append({
                "english": english,
                "quileute": entry.get("quileute_unicode", entry.get("quileute", "")),
                "phonetic": entry.get("pronunciation", ""),
                "audio": audio_url,
                "match_type": match_type
            })

    # Prefer stronger matches
    matches.sort(key=lambda m: ["exact", "partial", "overlap"].index(m["match_type"]))
    return matches

# 🔁 Translator endpoint
@app.get("/translate")
def translate(sentence: str = Query(..., min_length=1)):
    words = sentence.strip().split()
    morphology = []
    output_quileute = []
    output_phonetic = []

    for word in words:
        entries = find_entries(word)
        if entries:
            top = entries[0]
            output_quileute.append(top["quileute"])
            output_phonetic.append(top["phonetic"])
            morphology.append(top)
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

# Root health check
@app.get("/")
def root():
    return {"status": "Quileute Translator API is live"}
