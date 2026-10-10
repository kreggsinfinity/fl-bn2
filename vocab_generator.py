"""
Vocabulary Upgrade Studio - Video Generator (9:16 Vertical Reel)
"Stop Saying VERY... Say THIS Instead!"
Generates high-CTR vocabulary transformation videos with side-by-side contrast cards.
"""
import os, sys, json, subprocess, random, requests, re, asyncio
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from dotenv import load_dotenv
import edge_tts

load_dotenv()

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

WIDTH = 1080
HEIGHT = 1920
FPS = 30

BG_DARK = (15, 23, 42)         # Deep slate navy
RED_CARD = (239, 68, 68)       # #EF4444 Crimson
GREEN_CARD = (16, 185, 129)    # #10B981 Emerald
GOLD = (250, 204, 21)          # #FACC15 Cyber Yellow
WHITE = (255, 255, 255)
CARD_BG_DARK = (30, 41, 59)
TEXT_MUTED = (148, 163, 184)

VOICE_NATIVE = "en-US-AvaNeural"

ITEMS = [
    {
        "basic": "VERY TIRED",
        "advanced": "EXHAUSTED",
        "ipa": "/ ɪɡˈzɔːstɪd /",
        "syllables": "3 SYLLABLES",
        "example": "After running the marathon, I felt completely **exhausted**.",
        "script": [
            "Stop saying 'very tired' in English! Native speakers use a much stronger word.",
            "Instead, say: **EXHAUSTED**! Repeat after me: ex-haust-ed.",
            "Example: After running the marathon, I felt completely exhausted! Save this to upgrade your English!"
        ]
    },
    {
        "basic": "VERY ANGRY",
        "advanced": "FURIOUS",
        "ipa": "/ ˈfjʊəriəs /",
        "syllables": "3 SYLLABLES",
        "example": "He was **furious** when he found out about the broken car.",
        "script": [
            "Stop saying 'very angry'! It sounds basic and repetitive.",
            "Upgrade your vocabulary with: **FURIOUS**!",
            "Example: He was furious when he found out about the broken car. Follow for daily vocabulary!"
        ]
    },
    {
        "basic": "VERY COLD",
        "advanced": "FREEZING",
        "ipa": "/ ˈfriːzɪŋ /",
        "syllables": "2 SYLLABLES",
        "example": "Put on a thick coat, it is absolutely **freezing** outside!",
        "script": [
            "Never say 'very cold' when you want to sound like a native!",
            "Use the word: **FREEZING**!",
            "Example: Put on a jacket, it is absolutely freezing outside! Save this reel!"
        ]
    },
    {
        "basic": "VERY SMART",
        "advanced": "BRILLIANT",
        "ipa": "/ ˈbrɪliənt /",
        "syllables": "2 SYLLABLES",
        "example": "She came up with a **brilliant** solution to the problem.",
        "script": [
            "Want to sound smarter? Stop saying 'very smart' every single time.",
            "Instead, use the word: **BRILLIANT**!",
            "Example: That was a brilliant idea! Drop a like if you learned something new!"
        ]
    }
]

def load_font(size, bold=True):
    fonts_to_try = [
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/trebucbd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    ]
    for p in fonts_to_try:
        if Path(p).exists():
            try: return ImageFont.truetype(p, size)
            except: continue
    return ImageFont.load_default()

def draw_gradient_background():
    img = Image.new("RGBA", (WIDTH, HEIGHT), BG_DARK)
    draw = ImageDraw.Draw(img)
    # Radial or linear gradient
    for y in range(HEIGHT):
        ratio = y / HEIGHT
        r = int(15 + ratio * 20)
        g = int(23 + ratio * 15)
        b = int(42 + ratio * 25)
        draw.line([(0, y), (WIDTH, y)], fill=(r, g, b, 255))
    return img

def render_vocab_frame(item, step_idx, total_steps, out_path):
    canvas = draw_gradient_background()
    draw = ImageDraw.Draw(canvas)

    # 1. Top Header Badge
    f_badge = load_font(32, bold=True)
    draw.rounded_rectangle([(80, 100), (WIDTH - 80, 190)], radius=25, fill=(30, 41, 59), outline=GOLD, width=3)
    draw.text((WIDTH // 2, 145), "⚡ INSTANT VOCABULARY UPGRADE", fill=GOLD, font=f_badge, anchor="mm")

    # 2. Main Title Hook
    f_hook = load_font(60, bold=True)
    draw.text((WIDTH // 2, 280), "STOP SAYING THIS!", fill=WHITE, font=f_hook, anchor="mm")

    # 3. Basic / Avoid Card (Red)
    draw.rounded_rectangle([(80, 360), (WIDTH - 80, 560)], radius=30, fill=(45, 20, 30), outline=RED_CARD, width=4)
    f_tag = load_font(28, bold=True)
    draw.rounded_rectangle([(120, 390), (360, 445)], radius=15, fill=RED_CARD)
    draw.text((240, 417), "❌ BASIC / AVOID", fill=WHITE, font=f_tag, anchor="mm")

    f_basic = load_font(68, bold=True)
    draw.text((WIDTH // 2, 500), f'"{item["basic"]}"', fill=(255, 180, 180), font=f_basic, anchor="mm")

    # Arrow Down
    f_arrow = load_font(52, bold=True)
    draw.text((WIDTH // 2, 620), "⬇️ SAY THIS INSTEAD ⬇️", fill=GOLD, font=f_arrow, anchor="mm")

    # 4. Advanced / Native Upgrade Card (Green Glowing)
    draw.rounded_rectangle([(80, 690), (WIDTH - 80, 1030)], radius=30, fill=(15, 45, 35), outline=GREEN_CARD, width=5)
    draw.rounded_rectangle([(120, 720), (430, 775)], radius=15, fill=GREEN_CARD)
    draw.text((275, 747), "✅ NATIVE UPGRADE", fill=WHITE, font=f_tag, anchor="mm")

    f_adv = load_font(95, bold=True)
    draw.text((WIDTH // 2, 860), item["advanced"], fill=WHITE, font=f_adv, anchor="mm")

    f_phonetic = load_font(36, bold=False)
    draw.text((WIDTH // 2, 960), f'{item["ipa"]}  •  {item["syllables"]}', fill=GOLD, font=f_phonetic, anchor="mm")

    # 5. Example Sentence Card
    draw.rounded_rectangle([(80, 1100), (WIDTH - 80, 1420)], radius=30, fill=CARD_BG_DARK, outline=(71, 85, 105), width=2)
    f_ex_lbl = load_font(30, bold=True)
    draw.text((120, 1145), "📝 NATURAL CONTEXT EXAMPLE:", fill=GOLD, font=f_ex_lbl, anchor="lm")

    # Render wrapped example text
    f_sentence = load_font(44, bold=True)
    ex_text = item["example"].replace("**", "")
    words = ex_text.split()
    lines = []
    cur_line = []
    for w in words:
        test_line = " ".join(cur_line + [w])
        wb = draw.textbbox((0, 0), test_line, font=f_sentence)
        if wb[2] - wb[0] > (WIDTH - 240):
            lines.append(" ".join(cur_line))
            cur_line = [w]
        else:
            cur_line.append(w)
    if cur_line:
        lines.append(" ".join(cur_line))

    start_y = 1230
    for l_idx, line in enumerate(lines):
        draw.text((WIDTH // 2, start_y + l_idx * 65), f'"{line}"', fill=WHITE, font=f_sentence, anchor="mm")

    # 6. Spoken Caption Pill (What speaker is currently saying)
    draw.rounded_rectangle([(80, 1490), (WIDTH - 80, 1720)], radius=25, fill=(20, 30, 50), outline=GOLD, width=3)
    f_cap_lbl = load_font(26, bold=True)
    draw.text((120, 1530), f"🗣️ NATIVE SPEAKER EXPLANATION (Step {step_idx+1}/{total_steps}):", fill=GOLD, font=f_cap_lbl, anchor="lm")

    cur_speech = item["script"][step_idx].replace("**", "")
    f_speech = load_font(38, bold=True)
    draw.text((WIDTH // 2, 1630), cur_speech[:55] + ("..." if len(cur_speech) > 55 else ""), fill=WHITE, font=f_speech, anchor="mm")

    # 7. Bottom Call to Action
    f_cta = load_font(32, bold=True)
    draw.text((WIDTH // 2, 1800), "❤️ Like • 💬 Comment • 💾 Save For Later", fill=GOLD, font=f_cta, anchor="mm")
    f_page = load_font(26, bold=False)
    draw.text((WIDTH // 2, 1850), "Follow for Daily English Upgrades!", fill=TEXT_MUTED, font=f_page, anchor="mm")

    canvas.convert("RGB").save(out_path, quality=95)

async def assemble_vocab_reel(item, run_dir):
    frames_dir = run_dir / "frames"
    clips_dir = run_dir / "clips"
    audio_dir = run_dir / "audio"
    for d in [frames_dir, clips_dir, audio_dir]:
        d.mkdir(parents=True, exist_ok=True)

    clips = []
    total_steps = len(item["script"])

    for s_idx, text in enumerate(item["script"]):
        mp3_p = audio_dir / f"step_{s_idx}.mp3"
        clean = text.replace("**", "")
        await edge_tts.Communicate(clean, VOICE_NATIVE, rate="-10%").save(str(mp3_p))

        # ffprobe duration
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(mp3_p)],
            capture_output=True, text=True, check=True
        )
        dur = float(r.stdout.strip())

        frame_p = frames_dir / f"frame_{s_idx}.png"
        render_vocab_frame(item, s_idx, total_steps, str(frame_p))

        clip_p = clips_dir / f"clip_{s_idx}.mp4"
        subprocess.run([
            "ffmpeg", "-y", "-loop", "1", "-i", str(frame_p), "-i", str(mp3_p),
            "-vf", f"scale={WIDTH}:{HEIGHT},fps={FPS}",
            "-c:v", "libx264", "-c:a", "aac", "-b:a", "192k",
            "-pix_fmt", "yuv420p", "-preset", "fast", "-t", f"{dur:.3f}", str(clip_p)
        ], check=True, capture_output=True)

        clips.append(clip_p)

    concat_txt = run_dir / "concat.txt"
    with open(concat_txt, "w") as f:
        for c in clips:
            f.write(f"file '{c.resolve().as_posix()}'\n")

    final_v = run_dir / "vocab_upgrade_reel.mp4"
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_txt), "-c", "copy", str(final_v)], check=True, capture_output=True)
    return final_v

async def run_vocab_generation(item_idx=0):
    item = ITEMS[item_idx % len(ITEMS)]
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = OUTPUT_DIR / f"run_{ts}"
    run_dir.mkdir(parents=True, exist_ok=True)

    print(f"[Vocab Upgrade] Generating Reel for: Stop Saying '{item['basic']}' -> Say '{item['advanced']}'...")
    final_video = await assemble_vocab_reel(item, run_dir)

    meta = {
        "title": f"Stop saying '{item['basic']}'! Say '{item['advanced']}' instead! ⚡ English Upgrade",
        "description": f"Don't sound basic! Upgrade your English vocabulary: replace '{item['basic']}' with '{item['advanced']}'. Follow our page for daily 1-minute English upgrades! 🚀📚",
        "basic": item["basic"],
        "advanced": item["advanced"]
    }
    with open(run_dir / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print(f"[Vocab Upgrade] Reel created: {final_video}")
    return final_video, meta
