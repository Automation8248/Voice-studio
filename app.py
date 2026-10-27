from flask import Flask, render_template, request, jsonify
import edge_tts
import asyncio
import os
import random
import re

app = Flask(__name__)

# Premium Free Voices (Male/Female)
VOICES = {
    "female_nova": "en-US-AriaNeural",      # Nova jaisi clear female voice
    "female_jenny": "en-US-JennyNeural",    # Sweet & conversational
    "male_guy": "en-US-GuyNeural",          # Deep male voice
    "male_chris": "en-US-ChristopherNeural",# Energetic male
    "female_news": "en-US-MichelleNeural",  # Serious news reporter
    "male_news": "en-US-EricNeural"         # Serious male reporter
}

# NotebookLM jaisa Script Processor (Auto Detect & Filler Logic)
def process_script(text, tone):
    # 1. Auto-Detect Logic
    if tone == "auto":
        text_lower = text.lower()
        if any(w in text_lower for w in ["breaking", "news", "report", "today we"]):
            tone = "news"
        elif any(w in text_lower for w in ["welcome", "hey", "podcast", "discuss", "guys"]):
            tone = "podcast"
        elif any(w in text_lower for w in ["wow", "amazing", "let's go", "crazy"]):
            tone = "energetic"
        else:
            tone = "fact"

    # 2. Add Realistic Fillers (Hmm, Umm) for Podcast Tone
    sentences = re.split(r'(?<=[.!?]) +', text)
    processed_text = ""
    
    for i, sentence in enumerate(sentences):
        if tone == "podcast":
            fillers = [" Umm, ", " Well, ", " Hmm... ", " You know, ", " Like, "]
            # Har 2-3 sentence ke baad ek natural filler add karega
            if i > 0 and random.random() > 0.6:
                processed_text += random.choice(fillers)
        processed_text += sentence + " "

    # 3. Tone ke hisaab se Speed aur Pitch set karna
    rate = "+0%"
    pitch = "+0Hz"
    
    if tone == "energetic":
        rate = "+15%"
        pitch = "+5Hz"
    elif tone == "news":
        rate = "+5%"
        pitch = "-2Hz"
    elif tone == "fact":
        rate = "-5%" # Thoda slow taaki easily samajh aaye
    elif tone == "podcast":
        rate = "+0%"
        pitch = "+2Hz"

    return processed_text.strip(), rate, pitch, tone

async def generate_audio_async(text, voice, rate, pitch, output_file):
    communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
    await communicate.save(output_file)

@app.route('/')
def index():
    # Ye aapka main index.html hai
    return render_template('index.html')

@app.route('/voiceover')
def voiceover_tool():
    return render_template('tts.html')

@app.route('/generate', methods=['POST'])
def generate():
    data = request.json
    text = data.get('text', '')
    tone = data.get('tone', 'auto')
    voice_key = data.get('voice', 'female_nova')

    if not text:
        return jsonify({"error": "Text is required"}), 400

    # Script processing for realism
    processed_text, rate, pitch, final_tone = process_script(text, tone)
    voice = VOICES.get(voice_key, VOICES["female_nova"])

    # Output file path
    os.makedirs("static", exist_ok=True)
    output_file = os.path.join("static", "output.mp3")

    # Generate Audio asynchronously
    asyncio.run(generate_audio_async(processed_text, voice, rate, pitch, output_file))

    return jsonify({
        "audio_url": "/static/output.mp3",
        "detected_tone": final_tone,
        "processed_script": processed_text
    })

if __name__ == '__main__':
    app.run(debug=True)
