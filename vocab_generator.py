"""
VOCABULARY BOOST STUDIO - 16:9 FULL HD (1920x1080)
Format: 1920x1080 Landscape Studio Broadcast
Features:
- Photorealistic dual-host studio setting: Sophia on the left, Liam on the right
- Spacious center negative space for high-contrast subtitles and audio visualizer
- Dynamic host pills with live speaker indicator (Sophia vs Liam)
- SentenceBoundary millisecond-synchronized subtitle phrasing with active gold word karaoke
- Physically reactive 16-band audio equalizer synchronized to vocal frequencies
- Fixed bottom branding ribbon with smooth progress indicator
"""
import os, sys, json, math, subprocess, random, requests, re, asyncio
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from dotenv import load_dotenv
import edge_tts
import numpy as np
from pydub import AudioSegment

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

# Color Palette
GOLD_ACCENT = (255, 215, 0)         # Radiant Gold (#FFD700)
WHITE = (255, 255, 255)
MUTED_WHITE = (210, 218, 230)
DARK_BAR_ACTIVE = (16, 20, 32, 235)
DARK_BAR_INACTIVE = (12, 16, 24, 170)
BORDER_INACTIVE = (60, 75, 95, 160)
MUTED_TEXT = (160, 175, 195)
LIVE_GREEN = (34, 197, 94)
MUTED_GOLD = (235, 225, 200)

CHANNEL_NAME = "VOCAB BOOST STUDIO"
TAGLINE = "Stop Saying VERY  •  Master Native Vocabulary  •  Daily English Podcast"

# Two Hosts Configuration
SOPHIA_VOICE = "en-US-JennyNeural"
LIAM_VOICE = "en-US-BrianNeural"
VOICE_RATE = "-12%"

TOPICS = [
    {
        "topic": "Stop Saying Very Tired: Master The Word EXHAUSTED",
        "basic": "VERY TIRED",
        "advanced": "EXHAUSTED",
        "turns": [
            {"speaker": "Host1", "text": "Welcome to Vocab Boost Studio! Today we are upgrading one of the most overused words: **very tired**."},
            {"speaker": "Host2", "text": "Instead of saying 'I was very tired', say: After that long flight, I was completely **exhausted**."},
            {"speaker": "Host1", "text": "Exhausted paints a vivid picture of deep physical fatigue that simple words just cannot **match**."},
            {"speaker": "Host2", "text": "Try using exhausted in your next conversation, and your English will immediately sound more **natural**!"}
        ]
    },
    {
        "topic": "Stop Saying Very Busy: Master SWAMPED and OVERWHELMED",
        "basic": "VERY BUSY",
        "advanced": "SWAMPED",
        "turns": [
            {"speaker": "Host1", "text": "Hey everyone! When work piles up, stop saying 'I am very busy' every single **day**."},
            {"speaker": "Host2", "text": "A brilliant native upgrade is: I'm completely **swamped** with work this afternoon."},
            {"speaker": "Host1", "text": "Swamped means you have so much work you feel like you are sinking beneath a **wave**."},
            {"speaker": "Host2", "text": "Use swamped casually with coworkers, and notice how confident and fluent you **sound**!"}
        ]
    },
    {
        "topic": "Stop Saying Very Cold: Master FREEZING and BITTER",
        "basic": "VERY COLD",
        "advanced": "FREEZING",
        "turns": [
            {"speaker": "Host1", "text": "Winter is here, but don't just say 'it is very cold' whenever you step **outside**."},
            {"speaker": "Host2", "text": "Instead, natives will exclaim: Don't forget your coat, it's absolutely **freezing** out there!"},
            {"speaker": "Host1", "text": "Freezing conveys intense chill instantly, making your descriptions sharp and **expressive**."},
            {"speaker": "Host2", "text": "Small vocabulary upgrades like freezing will transform your everyday English into **second nature**!"}
        ]
    }
]


def configure_edge_tts():
    """Ensure edge_tts connects to Microsoft's active Cognitive Services endpoint to avoid 403 Forbidden."""
    try:
        import edge_tts.constants
        import edge_tts.communicate
        token = getattr(edge_tts.constants, "TRUSTED_CLIENT_TOKEN", "6A5AA1D4EAFF4E9FB37E23D68491D6F4")
        new_url = (
            "wss://api.msedgeservices.com/tts/cognitiveservices/websocket/v1"
            f"?Ocp-Apim-Subscription-Key={token}"
        )
        edge_tts.constants.WSS_URL = new_url
        edge_tts.communicate.WSS_URL = new_url
    except Exception as e:
        print(f"[edge_tts] configure warning: {e}")

async def synthesize_turn_speech(spoken, voice, rate, pitch=None, max_retries=3):
    """Synthesizes speech with active endpoint, 3x self-healing retries, and gTTS fallback."""
    configure_edge_tts()
    for attempt in range(max_retries):
        try:
            kwargs = {"rate": rate}
            if pitch:
                kwargs["pitch"] = pitch
            comm = edge_tts.Communicate(spoken, voice, **kwargs)
            sentences = []
            audio_bytes = bytearray()
            async for chunk in comm.stream():
                if chunk.get("type") == "SentenceBoundary":
                    start_s = chunk["offset"] / 10_000_000.0
                    dur_s = chunk["duration"] / 10_000_000.0
                    sentences.append({
                        "text": chunk["text"],
                        "start": start_s,
                        "duration": dur_s,
                        "end": start_s + dur_s
                    })
                elif chunk.get("type") == "audio":
                    audio_bytes.extend(chunk["data"])
            
            if len(audio_bytes) > 500:
                return audio_bytes, sentences
            else:
                print(f"    [TTS] Attempt {attempt+1}: bytes too small ({len(audio_bytes)}), retrying...")
        except Exception as e:
            print(f"    [TTS] Attempt {attempt+1} error: {e}")
        await asyncio.sleep(2 * (attempt + 1))
    
    # Fallback to gTTS if Edge TTS drops out
    try:
        from gtts import gTTS
        import io
        print(f"    [TTS] Active endpoint exhausted. Using gTTS fallback...")
        tts = gTTS(text=spoken, lang="en")
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        return bytearray(buf.getvalue()), []
    except Exception as fb_err:
        print(f"    [TTS] Fallback error: {fb_err}")
        return None, []

def load_font(size, bold=True):
    fonts_to_try = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/trebucbd.ttf" if bold else "C:/Windows/Fonts/trebuc.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
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
    prompt = f"""Write {target_turns} turns of a natural, engaging vocabulary upgrade podcast dialogue between Sophia (female host) and Liam (male host) discussing: {topic_item['topic']}.

RULES:
- Dialogue alternating between Host1 (Sophia) and Host2 (Liam)
- Each turn MUST be 2 short, clear sentences (16-24 words)
- Natural, conversational, encouraging flow
- Wrap exactly 1 key learning word per turn in **asterisks**
- Return as clean JSON array only:
[{{"speaker":"Host1","text":"..."}},{{"speaker":"Host2","text":"..."}}]"""

    key = os.getenv("POLLINATIONS_API_KEY")
    if key:
        try:
            resp = requests.post("https://gen.pollinations.ai/v1/chat/completions", json={
                "model": "gemini-fast",
                "messages": [
                    {"role": "system", "content": "You write educational, natural English vocabulary upgrade podcast dialogue. Wrap 1 key word per turn in **asterisks**."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.8
            }, headers={"Authorization": f"Bearer {key}"}, timeout=20)
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
        except Exception as e:
            print(f"[script] AI note: {e}, using curated fallback.")

    return topic_item.get("turns", [
        {"speaker": "Host1", "text": "Welcome to Vocab Boost Studio! Today we are upgrading one of the most overused words: **very tired**."},
        {"speaker": "Host2", "text": "Instead of saying 'I was very tired', say: After that long flight, I was completely **exhausted**."},
        {"speaker": "Host1", "text": "Exhausted paints a vivid picture of deep physical fatigue that simple words just cannot **match**."},
        {"speaker": "Host2", "text": "Try using exhausted in your next conversation, and your English will immediately sound more **natural**!"}
    ])[:target_turns]

async def generate_audio_files(turns, run_dir):
    audio_dir = run_dir / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    audio_list = []
    
    for i, turn in enumerate(turns):
        mp3_p = audio_dir / f"turn_{i:03d}.mp3"
        spoken = re.sub(r'\*\*(.*?)\*\*', r'\1', turn["text"])
        voice = SOPHIA_VOICE if turn["speaker"] == "Host1" else LIAM_VOICE
        audio_bytes, sentences = await synthesize_turn_speech(spoken, voice, rate=VOICE_RATE)
        if audio_bytes is None:
            audio_bytes = bytearray()
        with open(mp3_p, "wb") as f:
            f.write(audio_bytes)

        # Measure audio duration via ffprobe
        try:
            r = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1", str(mp3_p)],
                capture_output=True, text=True, check=True
            )
            duration = float(r.stdout.strip())
        except:
            duration = sentences[-1]["end"] if sentences else 5.0

        # Subdivide long sentences into short bite-sized clauses (max 8 words) for clean subtitles
        timed_phrases = []
        for s in sentences:
            s_text = s["text"]
            s_start = s["start"]
            s_dur = s["duration"]
            words = s_text.split()
            
            if len(words) <= 8:
                timed_phrases.append({
                    "text": s_text,
                    "start": s_start,
                    "end": s_start + s_dur,
                    "duration": s_dur
                })
            else:
                # Split at comma / punctuation or midpoint
                parts = [p.strip() for p in re.split(r'(?<=[,;:])\s+', s_text) if p.strip()]
                if len(parts) > 1:
                    total_w = sum(len(p.split()) for p in parts)
                    cur_t = s_start
                    for p in parts:
                        p_w = len(p.split())
                        p_dur = s_dur * (p_w / max(1, total_w))
                        timed_phrases.append({
                            "text": p,
                            "start": cur_t,
                            "end": cur_t + p_dur,
                            "duration": p_dur
                        })
                        cur_t += p_dur
                else:
                    mid = len(words) // 2
                    p1 = " ".join(words[:mid])
                    p2 = " ".join(words[mid:])
                    dur1 = s_dur * (len(p1.split()) / len(words))
                    dur2 = s_dur - dur1
                    timed_phrases.append({"text": p1, "start": s_start, "end": s_start + dur1, "duration": dur1})
                    timed_phrases.append({"text": p2, "start": s_start + dur1, "end": s_start + s_dur, "duration": dur2})

        # Load raw audio samples for 100% physical FFT frequency equalizer calculation
        audio_seg = AudioSegment.from_file(str(mp3_p))
        sample_rate = audio_seg.frame_rate
        raw_samples = np.array(audio_seg.get_array_of_samples(), dtype=float)
        if audio_seg.channels > 1:
            raw_samples = raw_samples.reshape((-1, audio_seg.channels)).mean(axis=1)

        audio_list.append({
            "path": str(mp3_p),
            "duration": duration,
            "speaker": turn["speaker"],
            "turn_text": turn["text"],
            "timed_phrases": timed_phrases,
            "raw_samples": raw_samples,
            "sample_rate": sample_rate
        })
        
    return audio_list

def load_base_studio_canvas():
    studio_path = ASSETS_DIR / "two_hosts_studio.png"
    if studio_path.exists():
        img = Image.open(studio_path).convert("RGBA")
        return img.resize((VIDEO_WIDTH, VIDEO_HEIGHT), Image.Resampling.LANCZOS)
    else:
        canvas = Image.new("RGBA", (VIDEO_WIDTH, VIDEO_HEIGHT), (16, 18, 28, 255))
        return canvas

def draw_vector_mic(draw, center_x, center_y, color=GOLD_ACCENT):
    draw.rounded_rectangle([(center_x - 6, center_y - 12), (center_x + 6, center_y + 4)], radius=4, fill=color)
    draw.arc([(center_x - 10, center_y - 4), (center_x + 10, center_y + 10)], start=0, end=180, fill=color, width=3)
    draw.line([(center_x, center_y + 10), (center_x, center_y + 16)], fill=color, width=3)
    draw.line([(center_x - 6, center_y + 16), (center_x + 6, center_y + 16)], fill=color, width=3)

def compute_physical_equalizer_bars(raw_samples, sample_rate, t_sec, num_bars=16):
    """
    Computes 16-band physical frequency spectrum directly from voice audio samples at timestamp t_sec.
    When speaking: bars dance to actual vocal frequencies.
    When pausing/silent: smoothly drops to 4px resting floor.
    """
    win_size = int(0.06 * sample_rate) # 60ms analysis window
    center_idx = int(t_sec * sample_rate)
    start_idx = max(0, center_idx - win_size // 2)
    end_idx = min(len(raw_samples), center_idx + win_size // 2)
    chunk = raw_samples[start_idx:end_idx]

    if len(chunk) < 100:
        return [4] * num_bars

    rms = np.sqrt(np.mean(chunk**2))
    if rms < 350.0:  # Silence / breath between words
        return [4] * num_bars

    fft_vals = np.abs(np.fft.rfft(chunk))
    fft_freqs = np.fft.rfftfreq(len(chunk), 1.0 / sample_rate)

    bar_heights = []
    for b in range(num_bars):
        f_min = 100 * (1.28 ** b)
        f_max = 100 * (1.28 ** (b + 1))
        mask = (fft_freqs >= f_min) & (fft_freqs < f_max)
        if np.any(mask):
            val = np.mean(fft_vals[mask])
            h = int(min(1.0, val / 320000.0) * 44)
        else:
            h = 4
        bar_heights.append(max(4, min(48, h)))

    return bar_heights

def render_podcast_frame(base_canvas, speaker, phrase_text, active_w_idx, eq_bars, frame_idx, elapsed, total_dur, out_path):
    canvas = base_canvas.copy()
    draw = ImageDraw.Draw(canvas)

    f_pills = load_font(28, bold=True)
    pill_h = 66
    pill_t = 40
    pill_b = pill_t + pill_h

    # 1. Left Host Badge: SOPHIA (Active when Host1 speaks)
    is_sophia_active = (speaker == "Host1")
    spk_sophia = "HOST: SOPHIA"
    tb_sophia = draw.textbbox((0, 0), spk_sophia, font=f_pills)
    tw_sophia = tb_sophia[2] - tb_sophia[0]
    sophia_w = tw_sophia + 130
    sophia_l = 60
    sophia_r = sophia_l + sophia_w

    bg_sophia = DARK_BAR_ACTIVE if is_sophia_active else DARK_BAR_INACTIVE
    outline_sophia = GOLD_ACCENT if is_sophia_active else BORDER_INACTIVE
    text_col_sophia = GOLD_ACCENT if is_sophia_active else MUTED_TEXT
    mic_col_sophia = GOLD_ACCENT if is_sophia_active else (120, 135, 155)

    draw.rounded_rectangle([(sophia_l, pill_t), (sophia_r, pill_b)], radius=20, fill=bg_sophia, outline=outline_sophia, width=3 if is_sophia_active else 2)
    mic_x_s = sophia_l + 35
    mic_y_s = pill_t + pill_h // 2
    draw_vector_mic(draw, mic_x_s, mic_y_s, color=mic_col_sophia)

    dot_x_s = mic_x_s + 22
    dot_col_s = LIVE_GREEN if is_sophia_active else (80, 95, 115)
    draw.ellipse([(dot_x_s - 4, mic_y_s - 4), (dot_x_s + 4, mic_y_s + 4)], fill=dot_col_s)
    draw.text((dot_x_s + 18, mic_y_s), spk_sophia, fill=text_col_sophia, font=f_pills, anchor="lm")

    # 2. Right Host Badge: LIAM (Active when Host2 speaks)
    is_liam_active = (speaker == "Host2")
    spk_liam = "HOST: LIAM"
    tb_liam = draw.textbbox((0, 0), spk_liam, font=f_pills)
    tw_liam = tb_liam[2] - tb_liam[0]
    liam_w = tw_liam + 130
    liam_r = 1860
    liam_l = liam_r - liam_w

    bg_liam = DARK_BAR_ACTIVE if is_liam_active else DARK_BAR_INACTIVE
    outline_liam = GOLD_ACCENT if is_liam_active else BORDER_INACTIVE
    text_col_liam = GOLD_ACCENT if is_liam_active else MUTED_TEXT
    mic_col_liam = GOLD_ACCENT if is_liam_active else (120, 135, 155)

    draw.rounded_rectangle([(liam_l, pill_t), (liam_r, pill_b)], radius=20, fill=bg_liam, outline=outline_liam, width=3 if is_liam_active else 2)
    mic_x_l = liam_l + 35
    mic_y_l = pill_t + pill_h // 2
    draw_vector_mic(draw, mic_x_l, mic_y_l, color=mic_col_liam)

    dot_x_l = mic_x_l + 22
    dot_col_l = LIVE_GREEN if is_liam_active else (80, 95, 115)
    draw.ellipse([(dot_x_l - 4, mic_y_l - 4), (dot_x_l + 4, mic_y_l + 4)], fill=dot_col_l)
    draw.text((dot_x_l + 18, mic_y_l), spk_liam, fill=text_col_liam, font=f_pills, anchor="lm")

    # 3. Center Channel Pill: VOCAB BOOST STUDIO (Symmetrical between hosts)
    tb_c = draw.textbbox((0, 0), CHANNEL_NAME, font=f_pills)
    tw_c = tb_c[2] - tb_c[0]
    chan_w = tw_c + 150
    chan_cx = 960
    chan_l = chan_cx - chan_w // 2
    chan_r = chan_cx + chan_w // 2

    draw.rounded_rectangle([(chan_l, pill_t), (chan_r, pill_b)], radius=20, fill=(16, 20, 32, 230), outline=(255, 215, 0, 180), width=2)
    wave_x = chan_l + 28
    wave_cy = pill_t + pill_h // 2
    for b in range(6):
        bh = int(12 + 12 * abs(math.sin(frame_idx * 0.45 + b * 1.15)))
        bx = wave_x + b * 10
        draw.line([(bx, wave_cy - bh // 2), (bx, wave_cy + bh // 2)], fill=GOLD_ACCENT, width=3)
    draw.text((wave_x + 75, wave_cy), CHANNEL_NAME, fill=WHITE, font=f_pills, anchor="lm")

    # 4. Center Subtitle Phrase Rendering (Negative space between hosts, center_x = 960, center_y = 330)
    words_raw = phrase_text.split()
    clean_words = [re.sub(r'[\*\*\.]', '', w).strip() for w in words_raw if w.strip()]
    if not clean_words: clean_words = ["Speak", "clearly"]

    f_sub = load_font(74, bold=True)
    max_sub_w = 780   # Perfectly fitted between Sophia's and Liam's boom arm microphones
    lines = []
    cur_line = []
    cur_w = 0

    for w_i, raw_w in enumerate(words_raw):
        clean_w = re.sub(r'\*\*(.*?)\*\*', r'\1', raw_w)
        wb = draw.textbbox((0, 0), clean_w + " ", font=f_sub)
        wl = wb[2] - wb[0]
        if cur_w + wl > max_sub_w and cur_line:
            lines.append(cur_line)
            cur_line = [(w_i, clean_w, wl)]
            cur_w = wl
        else:
            cur_line.append((w_i, clean_w, wl))
            cur_w += wl
    if cur_line:
        lines.append(cur_line)

    line_h = 100
    total_h = len(lines) * line_h
    center_x = 960
    center_y = 330
    start_y = max(180, center_y - total_h // 2)

    # Soft dark radial background glow for maximum contrast against background wooden panels
    glow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glow)
    glow_w = max(sum(item[2] for item in l) for l in lines) + 140
    glow_h = total_h + 90
    gdraw.rounded_rectangle([
        (center_x - glow_w // 2, start_y + total_h // 2 - glow_h // 2),
        (center_x + glow_w // 2, start_y + total_h // 2 + glow_h // 2)
    ], radius=30, fill=(0, 0, 0, 160))
    glow = glow.filter(ImageFilter.GaussianBlur(25))
    canvas.paste(glow, (0, 0), glow)

    # Deep drop shadow
    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shadow)
    for l_i, line in enumerate(lines):
        lw = sum(item[2] for item in line)
        lx = center_x - lw // 2
        ly = start_y + l_i * line_h
        for (w_i, clean_w, wl) in line:
            sdraw.text((lx + 4, ly + 5), clean_w, fill=(0, 0, 0, 255), font=f_sub)
            lx += wl
    shadow = shadow.filter(ImageFilter.GaussianBlur(5))
    canvas.paste(shadow, (0, 0), shadow)

    # Foreground text with active spoken word highlighted in Gold (#FFD700)
    draw = ImageDraw.Draw(canvas)
    for l_i, line in enumerate(lines):
        lw = sum(item[2] for item in line)
        lx = center_x - lw // 2
        ly = start_y + l_i * line_h
        for (w_i, clean_w, wl) in line:
            is_active = (w_i == active_w_idx)
            col = GOLD_ACCENT if is_active else WHITE
            draw.text((lx, ly), clean_w, fill=col, font=f_sub)
            lx += wl

    # 5. Physically Synchronized Sound Equalizer Plate in the Center
    # Generous breathing gap below subtitle text (center_y = 585)
    eq_cx = 960
    eq_cy = 585
    eq_w = 440
    eq_h = 58
    draw.rounded_rectangle([
        (eq_cx - eq_w // 2, eq_cy - eq_h // 2),
        (eq_cx + eq_w // 2, eq_cy + eq_h // 2)
    ], radius=16, fill=(14, 18, 28, 220), outline=(255, 215, 0, 180), width=2)

    num_b = 16
    bw = 12
    gap = 12
    total_bars_w = num_b * bw + (num_b - 1) * gap
    start_bx = eq_cx - total_bars_w // 2

    for b_i in range(num_b):
        bh = eq_bars[b_i] if b_i < len(eq_bars) else 4
        bx = start_bx + b_i * (bw + gap)
        by_top = eq_cy - bh // 2
        by_bot = eq_cy + bh // 2
        draw.rounded_rectangle([(bx, by_top), (bx + bw, by_bot)], radius=6, fill=GOLD_ACCENT)

    # 6. Fixed Bottom Footer Ribbon (Permanent, NO jumping text, NO timers)
    draw.line([(0, 1025), (VIDEO_WIDTH, 1025)], fill=(45, 52, 72), width=2)
    ratio = min(1.0, elapsed / max(1.0, total_dur))
    draw.line([(0, 1025), (int(VIDEO_WIDTH * ratio), 1025)], fill=GOLD_ACCENT, width=4)

    f_foot = load_font(28, bold=False)
    draw.text((center_x, 1052), TAGLINE, fill=MUTED_GOLD, font=f_foot, anchor="mm")

    canvas.convert("RGB").save(out_path, quality=95)

def assemble_video(topic_item, turns, audio_list, run_dir):
    frames_dir = run_dir / "frames"
    clips_dir = run_dir / "clips"
    frames_dir.mkdir(parents=True, exist_ok=True)
    clips_dir.mkdir(parents=True, exist_ok=True)

    base_canvas = load_base_studio_canvas()
    total_dur = sum(a["duration"] for a in audio_list)
    elapsed = 0.0
    clips = []

    for i, audio in enumerate(audio_list):
        dur = audio["duration"]
        speaker = audio["speaker"]
        timed_phrases = audio["timed_phrases"]
        raw_samples = audio["raw_samples"]
        sample_rate = audio["sample_rate"]

        turn_frames_dir = frames_dir / f"turn_{i:03d}"
        turn_frames_dir.mkdir(parents=True, exist_ok=True)

        # Video at 10 frames per second for ultra-fluid synchronization
        fps_turn = 10
        total_turn_frames = max(1, int(dur * fps_turn))

        for f_idx in range(total_turn_frames):
            frame_p = turn_frames_dir / f"frame_{f_idx:04d}.png"
            t_in_turn = (f_idx / total_turn_frames) * dur
            sub_elapsed = elapsed + t_in_turn

            # 1. Active phrase from Edge TTS timestamps
            active_phrase = timed_phrases[0] if timed_phrases else {"text": "Listen carefully", "start": 0, "end": dur}
            for p in timed_phrases:
                if p["start"] <= t_in_turn <= p["end"]:
                    active_phrase = p
                    break
                elif t_in_turn > p["end"]:
                    active_phrase = p

            # 2. Active word within active phrase
            p_text = active_phrase["text"]
            p_words = p_text.split()
            p_dur = max(0.2, active_phrase["end"] - active_phrase["start"])
            rel_t = max(0.0, min(p_dur, t_in_turn - active_phrase["start"]))
            active_w_idx = min(len(p_words) - 1, int((rel_t / p_dur) * len(p_words)))

            # 3. 16-band physical audio equalizer directly from real voice audio
            eq_bars = compute_physical_equalizer_bars(raw_samples, sample_rate, t_in_turn, num_bars=16)

            render_podcast_frame(
                base_canvas, speaker, p_text, active_w_idx,
                eq_bars, f_idx, sub_elapsed, total_dur, str(frame_p)
            )

        clip_p = clips_dir / f"clip_{i:03d}.mp4"
        input_pattern = str(turn_frames_dir / "frame_%04d.png")

        cmd = [
            "ffmpeg", "-y",
            "-framerate", str(fps_turn),
            "-i", input_pattern,
            "-i", audio["path"],
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            "-preset", "ultrafast",
            str(clip_p)
        ]
        subprocess.run(cmd, check=True, capture_output=True)

        clips.append(clip_p)
        elapsed += dur

    concat_txt = run_dir / "concat.txt"
    with open(concat_txt, "w") as f:
        for c in clips:
            f.write(f"file '{c.resolve().as_posix()}'\n")

    final_video = run_dir / "vocab_upgrade_final.mp4"
    subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_txt),
        "-c", "copy",
        str(final_video)
    ], check=True, capture_output=True)

    return final_video, total_dur

async def run_vocab_generation(topic_idx=0, turns_count=4):
    topic_item = TOPICS[topic_idx % len(TOPICS)]
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = OUTPUT_DIR / f"run_{ts}"
    run_dir.mkdir(parents=True, exist_ok=True)

    print(f"[Vocab Boost Studio] Generating 16:9 Broadcast: '{topic_item['topic']}' ({turns_count} turns)...")
    turns = generate_script_ai(topic_item, target_turns=turns_count)
    audio_list = await generate_audio_files(turns, run_dir)
    video_p, dur = assemble_video(topic_item, turns, audio_list, run_dir)

    meta = {
        "title": f"Vocabulary Upgrade Podcast: {topic_item['topic']} 🎙️ Sophia & Liam",
        "description": f"Master spoken English! Today's vocabulary upgrade: '{topic_item['topic']}'. Follow for daily English practice! ☕✨",
        "topic": topic_item["topic"],
        "duration_seconds": dur
    }
    with open(run_dir / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print(f"[Vocab Boost Studio] Video ready: {video_p}")
    return video_p, meta

if __name__ == "__main__":
    asyncio.run(run_vocab_generation(topic_idx=0, turns_count=4))
