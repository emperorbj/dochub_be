# generate_audio_translations.py
# This script creates MP3 files for Japanese, Korean, and Spanish translations
# of the sentence: "The men are hungry and looking for food in the dangerous, lonely jungle in Costa Rica."

from gtts import gTTS

# Translations
translations = {
    "Japanese": "男たちは空腹で、コスタリカの危険で孤独なジャングルで食べ物を探しています。",
    "Korean": "그 남자들은 배가 고프고 코스타리카의 위험하고 외로운 정글에서 음식을 찾고 있습니다.",
    "Spanish": "Los hombres tienen hambre y están buscando comida en la peligrosa y solitaria selva de Costa Rica."
}

# Language codes for Google TTS
lang_codes = {"Japanese": "ja", "Korean": "ko", "Spanish": "es"}

# Generate and save MP3s
for lang, text in translations.items():
    print(f"Generating {lang} audio...")
    tts = gTTS(text=text, lang=lang_codes[lang])
    filename = f"{lang.lower()}_translation.mp3"
    tts.save(filename)
    print(f"✅ Saved: {filename}")

print("\nAll audio files generated successfully!")
