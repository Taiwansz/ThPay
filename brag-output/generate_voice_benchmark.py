#!/usr/bin/env python3
"""
ThPay Voice Narration Benchmark Generator
Generates the exact same narration text across 5 free TTS engines for direct comparison.
"""

import os
import subprocess
from gtts import gTTS

OUTPUT_DIR = "brag-output/voice-comparison"
os.makedirs(OUTPUT_DIR, exist_ok=True)

NARRATION_TEXT = (
    "O fechamento mensal de folha como você conhece acabou. "
    "Conheça o ThPay: a infraestrutura de Continuous Payroll em tempo real. "
    "Quatrocentas vidas processadas centavo a centavo, eSocial nativo e guias pagas via Pix. "
    "Tecnologia que cuida do processo e das pessoas."
)

print(f"Generating voice comparison suite in {OUTPUT_DIR}...")
print(f"Target Text: \"{NARRATION_TEXT}\"\n")

# 1. Edge-TTS Antonio (Male Neural)
print("1/5 Generating Edge-TTS Antonio (pt-BR-AntonioNeural)...")
out_antonio = os.path.join(OUTPUT_DIR, "01_edge_antonio_neural.mp3")
subprocess.run([
    "edge-tts",
    "--voice", "pt-BR-AntonioNeural",
    "--rate=+2%",
    "--text", NARRATION_TEXT,
    "--write-media", out_antonio
], check=True)

# 2. Edge-TTS Francisca (Female Neural)
print("2/5 Generating Edge-TTS Francisca (pt-BR-FranciscaNeural)...")
out_francisca = os.path.join(OUTPUT_DIR, "02_edge_francisca_neural.mp3")
subprocess.run([
    "edge-tts",
    "--voice", "pt-BR-FranciscaNeural",
    "--rate=+2%",
    "--text", NARRATION_TEXT,
    "--write-media", out_francisca
], check=True)

# 3. Edge-TTS Thalita (Female Multilingual Neural)
print("3/5 Generating Edge-TTS Thalita (pt-BR-ThalitaMultilingualNeural)...")
out_thalita = os.path.join(OUTPUT_DIR, "03_edge_thalita_neural.mp3")
subprocess.run([
    "edge-tts",
    "--voice", "pt-BR-ThalitaMultilingualNeural",
    "--rate=+2%",
    "--text", NARRATION_TEXT,
    "--write-media", out_thalita
], check=True)

# 4. Google gTTS (pt-BR)
print("4/5 Generating Google gTTS (pt-BR)...")
out_google = os.path.join(OUTPUT_DIR, "04_google_gtts.mp3")
tts_google = gTTS(text=NARRATION_TEXT, lang="pt", tld="com.br", slow=False)
tts_google.save(out_google)

# 5. Piper Local ONNX (pt_BR-faber-medium)
print("5/5 Generating Piper Local Offline (pt_BR-faber-medium)...")
piper_model = "/tmp/piper_model/pt_BR-faber-medium.onnx"
piper_config = "/tmp/piper_model/pt_BR-faber-medium.onnx.json"
out_piper_wav = os.path.join(OUTPUT_DIR, "05_piper_local_offline.wav")
out_piper_mp3 = os.path.join(OUTPUT_DIR, "05_piper_local_offline.mp3")

proc = subprocess.Popen([
    "piper",
    "-m", piper_model,
    "-c", piper_config,
    "-f", out_piper_wav
], stdin=subprocess.PIPE)
proc.communicate(input=NARRATION_TEXT.encode("utf-8"))
proc.wait()

# Convert Piper WAV to MP3 for consistency
subprocess.run([
    "ffmpeg", "-y",
    "-i", out_piper_wav,
    "-codec:a", "libmp3lame",
    "-b:a", "192k",
    out_piper_mp3
], check=True)
os.remove(out_piper_wav)

print("\nSUCCESS: All 5 voice samples generated cleanly!")
