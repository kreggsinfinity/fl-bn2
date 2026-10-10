"""
VOCABULARY UPGRADE PODCAST - 16:9 FULL HD (1920x1080)
UI Style: Cyber Slate & Neon Glassmorphism Studio
- Left Side: High-tech broadcast boom microphone & acoustic cyber studio (without girl)
- Active 24-bar Neon Cyan/Emerald stereo audio equalizer dancing to vocal frequencies
- Single-line futuristic HUD glass subtitle ribbon with highlighted neon lime keywords
"""
import os, sys, json, math, subprocess, random, requests, re, asyncio
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from dotenv import load_dotenv
import edge_tts

if sys.platform == 'win32':
    try: sys.stdout.reconfigure(encoding='utf-8')
    except Exception: pass

load_dotenv()

BASE_DIR = Path(__file__).parent
ASSETS_DIR = BASE_DIR / "assets"
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
FPS = 30

CYAN = (0, 240, 255)
NEON_LIME = (57, 255, 20)
WHITE = (255, 255, 255)
MUTED_CYAN = (160, 220, 240)
DARK_BG = (8, 14, 28)
DARK_PANEL = (14, 22, 42)
CHANNEL_NAME = "VOCAB UPGRADE PODCAST"

EMMA_VOICE = "en-US-AvaNeural"
ANDREW_VOICE = "en-US-AndrewNeural"
VOICE_RATE = "-15%"

TOPICS = [
    {
        "topic": "Stop Saying Very Tired: Master The Word EXHAUSTED",
        "basic": "VERY TIRED",
        "upgrade": "EXHAUSTED",
        "keyword": "EXHAUSTED",
        "sub": "UPGRADE FROM BASIC TO NATIVE"
    },
    {
        "topic": "Stop Saying Very Angry: Master The Word FURIOUS",
        "basic": "VERY ANGRY",
        "upgrade": "FURIOUS",
        "keyword": "FURIOUS",
        "sub": "SOUND MORE EXPRESSIVE IN ENGLISH"
    }
]

def load_font(size, bold=True):
    fonts_to_try = [
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for p in fonts_to_try:
        if Path(p).exists():
            try: return ImageFont.truetype(p, size)
            except: continue
    return ImageFont.load_default()

def clean_text(text):
    text = re.sub(r'\b(mm+|um+|uh+|ah+)\b', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def generate_script_ai(topic_item, target_turns=4):
    prompt = f"""Write {target_turns} turns of a slow, clear English podcast between Emma and Andrew.
Topic: {topic_item['topic']}
Basic word to avoid: {topic_item['basic']}
Advanced upgrade word: {topic_item['upgrade']}
RULES:
- Dialogue alternating between Host1 (Emma) and Host2 (Andrew)
- Each turn MUST be 1-2 concise sentences (14-22 words) fitting in a clean single line
- Wrap exactly 1 key learning word per turn in **asterisks**
- Return as clean JSON array only:
[{{"speaker":"Host1","text":"..."}},{{"speaker":"Host2","text":"..."}}]"""

    key = os.getenv("POLLINATIONS_API_KEY")
    if key:
        try:
            resp = requests.post("https://gen.pollinations.ai/v1/chat/completions", json={
                "model": "gemini-fast",
                "messages": [
                    {"role": "system", "content": "You write educational, natural English learning podcast dialogue with single-line turns. Wrap 1 key word per turn in **asterisks**."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.8
            }, headers={"Authorization": f"Bearer {key}"}, timeout=60)
            if resp.status_code == 200:
                raw = resp.json()["choices"][0]["message"]["content"].strip()
                if "```json" in raw: raw = raw.split("```json")[1].split("```")[0].strip()
                elif "```" in raw: raw = raw.split("```")[1].split("```")[0].strip()
                script = json.loads(raw)
                if isinstance(script, list) and len(script) > 0:
                    for i, turn in enumerate(script):
                        turn["speaker"] = "Host1" if i % 2 == 0 else "Host2"
                        turn["text"] = clean_text(turn["text"])
                        if "**" not in turn["text"]:
                            words = turn["text"].split()
                            if len(words) > 2:
                                idx = len(words) // 2
                                words[idx] = f"**{words[idx]}**"
                                turn["text"] = " ".join(words)
                    return script[:target_turns]
        except Exception:
            pass

    return [
        {"speaker": "Host1", "text": f"Welcome back! Today we show you why saying {topic_item['basic']} limits your **fluency**."},
        {"speaker": "Host2", "text": f"Native speakers rarely say {topic_item['basic']}, because a much stronger word is **{topic_item['upgrade']}**."},
        {"speaker": "Host1", "text": f"Instead of saying you worked all day and are very tired, say you feel **{topic_item['upgrade']}**."},
        {"speaker": "Host2", "text": f"It immediately makes your English confident, sophisticated, and completely **natural**!"}
    ][:target_turns]

async def generate_audio_files(turns, run_dir):
    audio_dir = run_dir / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    audio_list = []
    for i, turn in enumerate(turns):
        mp3_p = audio_dir / f"turn_{i:03d}.mp3"
        spoken = re.sub(r'\*\*(.*?)\*\*', r'\1', turn["text"])
        voice = EMMA_VOICE if turn["speaker"] == "Host1" else ANDREW_VOICE
        comm = edge_tts.Communicate(spoken, voice, rate=VOICE_RATE)
        await comm.save(str(mp3_p))

        try:
            r = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1", str(mp3_p)],
                capture_output=True, text=True, check=True
            )
            duration = float(r.stdout.strip())
        except:
            duration = 5.0
        audio_list.append({"path": str(mp3_p), "duration": duration, "speaker": turn["speaker"]})
    return audio_list

def draw_cyber_equalizer(draw, center_x, center_y, frame_phase=0):
    """24-bar high-tech neon cyan and emerald spectrum equalizer"""
    num_bars = 24
    bar_w = 7
    gap = 8
    total_w = num_bars * bar_w + (num_bars - 1) * gap
    start_x = center_x - total_w // 2

    for i in range(num_bars):
        h = int(12 + 55 * abs(math.sin(frame_phase * 0.75 + i * 0.42)))
        x = start_x + i * (bar_w + gap)
        y_top = center_y - h // 2
        y_bot = center_y + h // 2
        col = NEON_LIME if (8 <= i <= 15) else CYAN
        draw.rounded_rectangle([(x, y_top), (x + bar_w, y_bot)], radius=3, fill=col)

def render_frame_ui2(topic_item, turn, frame_phase, elapsed, total_dur, out_path):
    # Use clean background without person, tint it with futuristic cyber slate atmosphere
    bg_path = ASSETS_DIR / "background.png"
    if bg_path.exists():
        canvas = Image.open(bg_path).convert("RGBA").resize((VIDEO_WIDTH, VIDEO_HEIGHT), Image.Resampling.LANCZOS)
    else:
        canvas = Image.new("RGBA", (VIDEO_WIDTH, VIDEO_HEIGHT), DARK_BG)

    draw = ImageDraw.Draw(canvas)

    # Left Studio Element: High-Tech Broadcast Microphone Stand (No person, sleek cyber studio aesthetic)
    mic_x, mic_y = 380, 520
    # Floating acoustic halo
    draw.ellipse([(mic_x - 180, mic_y - 180), (mic_x + 180, mic_y + 180)], outline=(20, 60, 90), width=4)
    draw.ellipse([(mic_x - 140, mic_y - 140), (mic_x + 140, mic_y + 140)], outline=CYAN, width=2)
    # Broadcast mic capsule
    draw.rounded_rectangle([(mic_x - 45, mic_y - 120), (mic_x + 45, mic_y + 30)], radius=22, fill=(25, 35, 55), outline=CYAN, width=3)
    # Mic grill lines
    for gl in range(mic_y - 95, mic_y + 10, 16):
        draw.line([(mic_x - 30, gl), (mic_x + 30, gl)], fill=CYAN, width=2)
    # Boom arm & shockmount
    draw.ellipse([(mic_x - 65, mic_y - 65), (mic_x + 65, mic_y + 65)], outline=NEON_LIME, width=3)
    draw.line([(mic_x, mic_y + 65), (mic_x, mic_y + 260)], fill=(40, 50, 75), width=10)
    draw.rounded_rectangle([(mic_x - 90, mic_y + 260), (mic_x + 90, mic_y + 290)], radius=8, fill=(30, 40, 65))
    # LED indicator on mic
    draw.ellipse([(mic_x - 8, mic_y - 15), (mic_x + 8, mic_y + 1)], fill=NEON_LIME)

    # 1. Top Left Channel Badge
    font_tab = load_font(30, bold=True)
    draw.rounded_rectangle([(60, 40), (620, 110)], radius=18, fill=DARK_PANEL, outline=CYAN, width=3)
    draw.text((180, 75), CHANNEL_NAME, fill=WHITE, font=font_tab, anchor="lm")
    # Mini icon
    draw.text((95, 75), "⚡", fill=CYAN, font=font_tab, anchor="lm")

    # 2. Top Center Topic Pill
    draw.rounded_rectangle([(660, 40), (1460, 110)], radius=18, fill=(18, 32, 58), outline=NEON_LIME, width=2)
    f_topic = load_font(26, bold=True)
    draw.text((1060, 75), f"UPGRADE: {topic_item['basic']} ➔ {topic_item['upgrade']}", fill=NEON_LIME, font=f_topic, anchor="mm")

    # 3. Top Right Speaker Badge
    speaker_name = "EMMA" if turn["speaker"] == "Host1" else "ANDREW"
    font_spk = load_font(28, bold=True)
    draw.rounded_rectangle([(1520, 40), (1860, 110)], radius=18, fill=DARK_PANEL, outline=CYAN, width=3)
    draw.text((1690, 75), f"🎙️ HOST: {speaker_name}", fill=CYAN, font=font_spk, anchor="mm")

    # 4. ACTIVE NEON EQUALIZER CONSOLE (Center Right)
    eq_x = 1320
    eq_y = 440
    draw.rounded_rectangle([(eq_x - 220, eq_y - 50), (eq_x + 220, eq_y + 50)], radius=18, fill=(10, 18, 38), outline=CYAN, width=2)
    draw_cyber_equalizer(draw, eq_x, eq_y, frame_phase=frame_phase)
    f_eq_lbl = load_font(20, bold=True)
    draw.text((eq_x, eq_y + 70), f"AUDIO FREQUENCY ANALYZER • ACTIVE VOICE", fill=MUTED_CYAN, font=f_eq_lbl, anchor="mm")

    # 5. SINGLE-LINE HUD GLASS SUBTITLE DISPLAY
    text = turn["text"]
    parts = re.split(r'(\*\*.*?\*\*)', text)
    words_list = []
    for p in parts:
        if p.startswith('**') and p.endswith('**'):
            words_list.append((p[2:-2], True))
        elif p:
            for w in p.split(' '):
                if w: words_list.append((w, False))

    sub_font = load_font(52, bold=True)
    word_widths = []
    for w, is_y in words_list:
        bb = draw.textbbox((0, 0), w, font=sub_font)
        word_widths.append((w, is_y, bb[2] - bb[0] + 14))

    total_sub_w = sum(ww[2] for ww in word_widths)
    sub_x = 1320
    sub_y = 680

    card_left = max(740, sub_x - total_sub_w // 2 - 45)
    card_right = min(1860, sub_x + total_sub_w // 2 + 45)
    draw.rounded_rectangle([(card_left, sub_y - 50), (card_right, sub_y + 50)], radius=25, fill=(12, 20, 42), outline=CYAN, width=3)

    cur_x = (card_left + card_right) // 2 - total_sub_w // 2
    for word, is_highlight, ww in word_widths:
        col = NEON_LIME if is_highlight else WHITE
        draw.text((cur_x, sub_y), word, fill=col, font=sub_font, anchor="lm")
        cur_x += ww

    # 6. Bottom Progress & Branding
    draw.line([(0, 1020), (VIDEO_WIDTH, 1020)], fill=(20, 35, 60), width=3)
    ratio = min(1.0, elapsed / max(1.0, total_dur))
    draw.line([(0, 1020), (int(VIDEO_WIDTH * ratio), 1020)], fill=CYAN, width=6)

    font_sub = load_font(26, bold=False)
    draw.text((70, 1050), "Cyber Slate Studio • Vocabulary Upgrade Podcast • Sound Like A Native", fill=MUTED_CYAN, font=font_sub, anchor="lm")
    time_str = f"{int(elapsed // 60):02d}:{int(elapsed % 60):02d} / {int(total_dur // 60):02d}:{int(total_dur % 60):02d}"
    draw.text((1850, 1050), time_str, fill=CYAN, font=font_sub, anchor="rm")

    canvas.convert("RGB").save(out_path, quality=92)

def assemble_video_ui2(topic_item, turns, audio_list, run_dir):
    frames_dir = run_dir / "frames"
    clips_dir = run_dir / "clips"
    frames_dir.mkdir(parents=True, exist_ok=True)
    clips_dir.mkdir(parents=True, exist_ok=True)

    total_dur = sum(a["duration"] for a in audio_list)
    elapsed = 0.0
    clips = []

    for i, (turn, audio) in enumerate(zip(turns, audio_list)):
        dur = audio["duration"]
        clip_p = clips_dir / f"clip_{i:03d}.mp4"

        num_subframes = max(4, int(dur * 2))
        for f_idx in range(num_subframes):
            frame_p = frames_dir / f"frame_{i:03d}_{f_idx:02d}.png"
            render_frame_ui2(topic_item, turn, frame_phase=f_idx, elapsed=elapsed, total_dur=total_dur, out_path=str(frame_p))

        subprocess.run([
            "ffmpeg", "-y", "-framerate", "2", "-i", str(frames_dir / f"frame_{i:03d}_%02d.png"),
            "-i", audio["path"], "-c:v", "libx264", "-c:a", "aac", "-b:a", "192k",
            "-pix_fmt", "yuv420p", "-preset", "fast", "-t", f"{dur:.3f}", str(clip_p)
        ], check=True, capture_output=True)

        clips.append(clip_p)
        elapsed += dur

    concat_txt = run_dir / "concat.txt"
    with open(concat_txt, "w") as f:
        for c in clips: f.write(f"file '{c.resolve().as_posix()}'\n")

    final_video = run_dir / "vocab_upgrade_podcast_final.mp4"
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_txt), "-c", "copy", str(final_video)], check=True, capture_output=True)
    return final_video, total_dur

async def run_vocab_generation(topic_idx=0, turns_count=4):
    topic_item = TOPICS[topic_idx % len(TOPICS)]
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = OUTPUT_DIR / f"run_{ts}"
    run_dir.mkdir(parents=True, exist_ok=True)

    print(f"[Vocab Podcast] Generating 16:9 Cyber Glass Studio: '{topic_item['topic']}'...")
    turns = generate_script_ai(topic_item, target_turns=turns_count)
    audio_list = await generate_audio_files(turns, run_dir)
    video_p, dur = assemble_video_ui2(topic_item, turns, audio_list, run_dir)

    meta = {
        "title": f"Stop Saying {topic_item['basic']}! Master {topic_item['upgrade']} 🎙️ Cyber Studio Podcast",
        "description": f"Learn why native speakers avoid '{topic_item['basic']}' and how to use '{topic_item['upgrade']}' naturally! Join Emma and Andrew in our cyber studio podcast. 🌟📚",
        "duration_seconds": dur
    }
    with open(run_dir / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    return video_p, meta
