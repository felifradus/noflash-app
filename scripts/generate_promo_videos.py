"""
Generador profesional de 3 videos promocionales verticales 9:16 (1080x1920 @ 30fps)
para TikTok, YouTube Shorts e Instagram Reels de NoFlash.
Usa Pillow + NumPy + edge-tts (HD Neural Voiceover) + ffmpeg (via imageio-ffmpeg).
"""

import asyncio
import math
import os
import subprocess
import wave
from pathlib import Path

import edge_tts
import httpx
import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "marketing" / "videos"
CACHE_DIR = ROOT / "scripts" / "assets_cache"
OUT_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)

W, H = 1080, 1920
FPS = 30
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

ASSETS = {
    "splash_sylas": "https://ddragon.leagueoflegends.com/cdn/img/champion/splash/Sylas_0.jpg",
    "splash_jinx": "https://ddragon.leagueoflegends.com/cdn/img/champion/splash/Jinx_0.jpg",
    "splash_asol": "https://ddragon.leagueoflegends.com/cdn/img/champion/splash/AurelionSol_0.jpg",
    "icon_jinx": "https://ddragon.leagueoflegends.com/cdn/16.23.1/img/champion/Jinx.png",
    "icon_cait": "https://ddragon.leagueoflegends.com/cdn/16.23.1/img/champion/Caitlyn.png",
    "icon_lee": "https://ddragon.leagueoflegends.com/cdn/16.23.1/img/champion/LeeSin.png",
    "icon_yasuo": "https://ddragon.leagueoflegends.com/cdn/16.23.1/img/champion/Yasuo.png",
    "icon_ezreal": "https://ddragon.leagueoflegends.com/cdn/16.23.1/img/champion/Ezreal.png",
    "icon_zed": "https://ddragon.leagueoflegends.com/cdn/16.23.1/img/champion/Zed.png",
}


def load_font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    candidates = [
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibrib.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


FONT_HUGE = load_font(86, True)
FONT_TITLE = load_font(64, True)
FONT_SUB = load_font(42, True)
FONT_BODY = load_font(34, False)
FONT_SMALL = load_font(28, True)
FONT_CAP = load_font(54, True)


def download_assets() -> dict[str, Image.Image]:
    imgs: dict[str, Image.Image] = {}
    with httpx.Client(timeout=20.0) as client:
        for key, url in ASSETS.items():
            fp = CACHE_DIR / f"{key}.jpg"
            if not fp.exists():
                r = client.get(url)
                r.raise_for_status()
                fp.write_bytes(r.content)
            imgs[key] = Image.open(fp).convert("RGBA")
    logo_fp = ROOT / "static" / "logo.jpg"
    if logo_fp.exists():
        imgs["logo"] = Image.open(logo_fp).convert("RGBA")
    return imgs


async def synth_voice(text: str, out_mp3: Path, voice: str = "en-US-AndrewMultilingualNeural") -> None:
    comm = edge_tts.Communicate(text, voice=voice, rate="+2%", pitch="-1Hz")
    data = bytearray()
    async for chunk in comm.stream():
        if chunk.get("type") == "audio":
            data.extend(chunk["data"])
    out_mp3.write_bytes(bytes(data))


def get_audio_duration(audio_path: Path) -> float:
    res = subprocess.run(
        [FFMPEG, "-i", str(audio_path)],
        capture_output=True,
        text=True,
    )
    import re
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", res.stderr)
    if m:
        return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
    return 15.0


def generate_hextech_beat(duration: float, out_wav: Path) -> None:
    """Genera un pulso electrónico Hextech sutil (bajo + arpegio suave) de fondo."""
    sr = 44100
    n = int(sr * duration)
    t = np.linspace(0, duration, n, endpoint=False)
    bpm = 118.0
    beat_period = 60.0 / bpm
    beat_phase = (t % beat_period) / beat_period

    # Kick suave + sub-bass Hextech
    kick = np.sin(2 * np.pi * (95 * np.exp(-beat_phase * 14) + 38) * t) * np.exp(-beat_phase * 9) * 0.22
    # Pad atmosférico en Re menor (D2 + A2 + F3)
    pad = (
        np.sin(2 * np.pi * 73.42 * t) * 0.08
        + np.sin(2 * np.pi * 110.0 * t) * 0.05
        + np.sin(2 * np.pi * 146.83 * t) * 0.04
    ) * (0.75 + 0.25 * np.sin(2 * np.pi * 0.5 * t))
    # Pulso hi-hat sutil
    eighth = ((t % (beat_period / 2)) / (beat_period / 2))
    hat = np.random.uniform(-1, 1, n) * np.exp(-eighth * 35) * 0.025

    mix = np.clip(kick + pad + hat, -0.95, 0.95)
    # Fade in/out
    fade = int(sr * 0.4)
    mix[:fade] *= np.linspace(0, 1, fade)
    mix[-fade:] *= np.linspace(1, 0, fade)

    pcm = (mix * 32767).astype(np.int16)
    with wave.open(str(out_wav), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm.tobytes())


def make_circle_avatar(img: Image.Image, size: int, border_color=(200, 155, 60, 255)) -> Image.Image:
    av = img.resize((size, size), Image.Resampling.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size, size), fill=255)
    out = Image.new("RGBA", (size + 8, size + 8), (0, 0, 0, 0))
    ImageDraw.Draw(out).ellipse((0, 0, size + 7, size + 7), fill=border_color)
    out.paste(av, (4, 4), mask)
    return out


def draw_centered_text(draw: ImageDraw.ImageDraw, text: str, y: int, font, fill, stroke_w=4, stroke_fill=(2, 10, 22, 255)):
    bbox = draw.textbbox((0, 0), text, font=font, stroke_width=stroke_w)
    tw = bbox[2] - bbox[0]
    draw.text(((W - tw) // 2, y), text, font=font, fill=fill, stroke_width=stroke_w, stroke_fill=stroke_fill)


def draw_bg_splash(splash: Image.Image, t: float, dur: float) -> Image.Image:
    zoom = 1.0 + 0.08 * (t / max(dur, 1.0))
    sw, sh = splash.size
    target_ratio = W / H
    crop_h = int(sh / zoom)
    crop_w = int(crop_h * target_ratio)
    if crop_w > sw:
        crop_w = int(sw / zoom)
        crop_h = int(crop_w / target_ratio)
    cx = sw // 2 + int(math.sin(t * 0.4) * 20)
    cy = sh // 2
    x1 = max(0, min(sw - crop_w, cx - crop_w // 2))
    y1 = max(0, min(sh - crop_h, cy - crop_h // 2))
    bg = splash.crop((x1, y1, x1 + crop_w, y1 + crop_h)).resize((W, H), Image.Resampling.BILINEAR)
    # Viñeta oscura Hextech
    overlay = Image.new("RGBA", (W, H), (3, 11, 24, 185))
    return Image.alpha_composite(bg, overlay)


def draw_header_brand(frame: Image.Image, draw: ImageDraw.ImageDraw, logo: Image.Image):
    av = make_circle_avatar(logo, 92, (246, 211, 101, 255))
    frame.alpha_composite(av, (70, 95))
    draw.text((190, 106), "NOFLASH", font=FONT_TITLE, fill=(246, 211, 101, 255), stroke_width=3, stroke_fill=(1, 10, 19, 255))
    draw.text((192, 174), "LIVE LOL COACH · ZERO OVERWOLF", font=FONT_SMALL, fill=(10, 200, 185, 255))
    draw.line([(70, 222), (W - 70, 222)], fill=(200, 155, 60, 140), width=2)


def draw_caption(draw: ImageDraw.ImageDraw, lines: list[str], y_base: int = 1540):
    for idx, line in enumerate(lines):
        draw_centered_text(draw, line, y_base + idx * 66, FONT_CAP, (255, 255, 255, 255), stroke_w=6)


def draw_cta_footer(draw: ImageDraw.ImageDraw, t: float):
    pulse = int(20 * math.sin(t * 6))
    box = [130, 1720, W - 130, 1825]
    draw.rounded_rectangle(box, radius=24, fill=(200, 155, 60, 235), outline=(255, 245, 214, 255), width=3)
    draw_centered_text(draw, "FREE WINDOWS BETA · LINK IN BIO", 1748, FONT_SUB, (1, 10, 19, 255), stroke_w=0)


def render_video(
    out_mp4: Path,
    script_text: str,
    voice: str,
    splash_img: Image.Image,
    assets: dict[str, Image.Image],
    captions: list[tuple[float, float, list[str]]],
    scene_drawer,
) -> None:
    tmp_voice = CACHE_DIR / f"{out_mp4.stem}_voice.mp3"
    tmp_beat = CACHE_DIR / f"{out_mp4.stem}_beat.wav"
    tmp_mix = CACHE_DIR / f"{out_mp4.stem}_mix.aac"

    asyncio.run(synth_voice(script_text, tmp_voice, voice=voice))
    dur = get_audio_duration(tmp_voice) + 1.2
    generate_hextech_beat(dur, tmp_beat)

    # Mezclar voz HD + pulso Hextech suave
    subprocess.run([
        FFMPEG, "-y",
        "-i", str(tmp_voice),
        "-i", str(tmp_beat),
        "-filter_complex", "[0:a]volume=1.15[v];[1:a]volume=0.32[b];[v][b]amix=inputs=2:duration=longest[a]",
        "-map", "[a]", "-c:a", "aac", "-b:a", "192k", str(tmp_mix),
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    total_frames = int(dur * FPS)
    proc = subprocess.Popen([
        FFMPEG, "-y",
        "-f", "rawvideo", "-vcodec", "rawvideo",
        "-s", f"{W}x{H}", "-pix_fmt", "rgb24", "-r", str(FPS),
        "-i", "-",
        "-i", str(tmp_mix),
        "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-pix_fmt", "yuv420p",
        "-c:a", "copy", "-shortest",
        str(out_mp4),
    ], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    logo = assets["logo"]
    for f in range(total_frames):
        t = f / FPS
        frame = draw_bg_splash(splash_img, t, dur)
        draw = ImageDraw.Draw(frame, "RGBA")
        draw_header_brand(frame, draw, logo)
        scene_drawer(frame, draw, t, dur, assets)

        for t0, t1, lines in captions:
            if t0 <= t <= t1:
                draw_caption(draw, lines)
                break

        draw_cta_footer(draw, t)
        proc.stdin.write(frame.convert("RGB").tobytes())

    proc.stdin.close()
    proc.wait()
    print(f"OK VIDEO: {out_mp4} ({out_mp4.stat().st_size / 1048576:.2f} MB, {dur:.1f}s)")


# ── Escena 1: Anti-Overwolf + Draft Coach + 1-Click Runes ──
def scene_anti_overwolf(frame, draw, t, dur, assets):
    if t < 4.0:
        draw_centered_text(draw, "STOP LETTING", 420, FONT_HUGE, (233, 69, 96, 255), stroke_w=6)
        draw_centered_text(draw, "OVERWOLF", 525, FONT_HUGE, (255, 255, 255, 255), stroke_w=6)
        draw_centered_text(draw, "TANK YOUR FPS.", 630, FONT_HUGE, (246, 211, 101, 255), stroke_w=6)
        draw.rounded_rectangle([140, 820, W - 140, 1050], radius=24, fill=(10, 22, 40, 225), outline=(233, 69, 96, 220), width=4)
        draw_centered_text(draw, "Heavy Bloatware  ->  -40 FPS", 865, FONT_SUB, (253, 164, 175, 255), stroke_w=2)
        draw_centered_text(draw, "NoFlash Native .exe  ->  0% Bloat", 955, FONT_SUB, (94, 234, 212, 255), stroke_w=2)
    else:
        # Tarjeta Live Draft Coach
        draw.rounded_rectangle([85, 310, W - 85, 1380], radius=28, fill=(8, 19, 36, 235), outline=(200, 155, 60, 235), width=4)
        draw.text((135, 355), "LIVE DRAFT COACH", font=FONT_SUB, fill=(246, 211, 101, 255))
        draw.rounded_rectangle([680, 350, 945, 412], radius=18, fill=(10, 200, 185, 55), outline=(10, 200, 185, 220), width=2)
        draw.text((712, 363), "1-CLICK RUNES", font=FONT_SMALL, fill=(94, 234, 212, 255))

        # Pick #1 Jinx
        draw.rounded_rectangle([125, 455, W - 125, 695], radius=20, fill=(14, 30, 54, 240), outline=(246, 211, 101, 220), width=3)
        frame.alpha_composite(make_circle_avatar(assets["icon_jinx"], 140), (155, 500))
        draw.text((330, 505), "JINX · TIER S+", font=FONT_SUB, fill=(255, 255, 255, 255))
        draw.text((330, 565), "58.2% WR (97 games) · Your Pool", font=FONT_BODY, fill=(94, 234, 212, 255))
        draw.text((330, 618), "Lethal Tempo · Flash / Cleanse", font=FONT_SMALL, fill=(246, 211, 101, 255))

        # Pick #2 Caitlyn
        draw.rounded_rectangle([125, 735, W - 125, 955], radius=20, fill=(14, 30, 54, 230), outline=(10, 200, 185, 160), width=2)
        frame.alpha_composite(make_circle_avatar(assets["icon_cait"], 124), (160, 778))
        draw.text((325, 785), "CAITLYN · TIER S", font=FONT_SUB, fill=(240, 230, 210, 255))
        draw.text((325, 845), "55.1% WR · Lane Prio & Range", font=FONT_BODY, fill=(180, 195, 215, 255))

        # Botón 1-Click pulsante
        glow = int(18 * abs(math.sin(t * 4)))
        draw.rounded_rectangle([160, 1030, W - 160, 1150], radius=20, fill=(10, 65, 78, 255), outline=(246, 211, 101, 255), width=4)
        draw_centered_text(draw, "IMPORT RUNES & SPELLS TO LOL", 1068, FONT_SUB, (255, 255, 255, 255), stroke_w=2)

        draw_centered_text(draw, "160-Game Local Cache · <2s Load", 1225, FONT_BODY, (154, 165, 177, 255), stroke_w=0)
        draw_centered_text(draw, "100% Riot API & Vanguard Safe", 1280, FONT_BODY, (94, 234, 212, 255), stroke_w=0)


# ── Escena 2: NEW Dodge Arena (Skillshot Survival + Flash!) + Flashdle ──
def scene_dodge_arena(frame, draw, t, dur, assets):
    draw.rounded_rectangle([320, 255, W - 320, 325], radius=30, fill=(249, 115, 22, 235), outline=(253, 224, 71, 255), width=3)
    draw_centered_text(draw, "NEW QUEUE MODE", 270, FONT_SMALL, (1, 10, 19, 255), stroke_w=0)
    draw_centered_text(draw, "DODGE ARENA", 350, FONT_HUGE, (246, 211, 101, 255), stroke_w=5)

    # Arena animada real con Lux R + Blitz Q + Morg Q + Ezreal Flasheando!
    ax1, ay1, ax2, ay2 = 80, 480, W - 80, 1280
    draw.rounded_rectangle([ax1, ay1, ax2, ay2], radius=24, fill=(5, 16, 32, 245), outline=(200, 155, 60, 240), width=4)
    # Grilla Hextech
    for gx in range(ax1 + 60, ax2, 80):
        draw.line([(gx, ay1), (gx, ay2)], fill=(200, 155, 60, 28), width=1)
    for gy in range(ay1 + 60, ay2, 80):
        draw.line([(ax1, gy), (ax2, gy)], fill=(200, 155, 60, 28), width=1)

    # HUD del juego
    score = int(t * 420)
    rank = "CHALLENGER" if score > 4500 else ("DIAMOND" if score > 2500 else "GOLD")
    draw.text((115, 505), f"SCORE: {score}", font=FONT_SUB, fill=(255, 255, 255, 255))
    draw.text((640, 505), f"RANK: {rank}", font=FONT_SUB, fill=(253, 224, 71, 255))

    # Posición del campeón (sidestepping + Flash al segundo 6.0!)
    flashed = (t % 5.0) > 2.8
    px = int(540 + math.cos(t * 2.4) * 190 + (150 if flashed else 0))
    py = int(890 + math.sin(t * 3.1) * 130)
    px = max(ax1 + 70, min(ax2 - 70, px))
    py = max(ay1 + 110, min(ay2 - 70, py))

    # Lux R Laser beam animado
    lux_phase = (t % 5.0)
    if 1.8 < lux_phase < 3.4:
        firing = lux_phase > 2.65
        col = (253, 224, 71, 245) if firing else (248, 113, 113, 190)
        lw = 38 if firing else 6
        draw.line([(ax1 + 20, ay1 + 240), (ax2 - 20, ay2 - 160)], fill=col, width=lw)
        if firing:
            draw.line([(ax1 + 20, ay1 + 240), (ax2 - 20, ay2 - 160)], fill=(255, 255, 255, 255), width=14)

    # Proyectiles Blitz Q + Morg Q + Ashe R
    bx = ax1 + int(((t * 360) % (ax2 - ax1)))
    by = 760
    draw.line([(max(ax1 + 10, bx - 90), by), (bx, by)], fill=(246, 211, 101, 170), width=8)
    draw.ellipse([bx - 22, by - 22, bx + 22, by + 22], fill=(246, 211, 101, 255), outline=(255, 255, 255, 255), width=3)

    mx = ax2 - int(((t * 240 + 300) % (ax2 - ax1)))
    my = 1040
    draw.ellipse([mx - 28, my - 28, mx + 28, my + 28], fill=(192, 132, 252, 245), outline=(255, 255, 255, 255), width=3)

    # Ziggs R AoE
    z_pct = (t % 2.4) / 2.4
    zx, zy, zr = 330, 990, 95
    draw.ellipse([zx - zr, zy - zr, zx + zr, zy + zr], fill=(239, 68, 68, 45), outline=(248, 113, 113, 220), width=3)
    ir = int(zr * z_pct)
    draw.ellipse([zx - ir, zy - ir, zx + ir, zy + ir], fill=(249, 115, 22, 95))

    # Avatar del jugador (Ezreal) + Flash Ring
    if 2.8 < lux_phase < 3.6:
        draw.ellipse([px - 68, py - 68, px + 68, py + 68], outline=(253, 224, 71, 255), width=6)
        draw.text((px - 150, py - 95), "CLUTCH FLASH +150!", font=FONT_SMALL, fill=(253, 224, 71, 255))
    av = make_circle_avatar(assets["icon_ezreal"], 72, (253, 224, 71, 255))
    frame.alpha_composite(av, (px - 40, py - 40))

    draw_centered_text(draw, "PRESS [F] TO FLASH · + FLASHDLE INCLUDED", 1325, FONT_SMALL, (94, 234, 212, 255), stroke_w=2)


# ── Escena 3: Calm Voice Minimap Check + Live 5v5 Scouting ──
def scene_calm_voice(frame, draw, t, dur, assets):
    draw_centered_text(draw, "STOP DYING TO", 300, FONT_TITLE, (255, 255, 255, 255), stroke_w=5)
    draw_centered_text(draw, "3:00 GANKS", 385, FONT_HUGE, (10, 200, 185, 255), stroke_w=6)

    # Tarjeta Voice Reminders
    draw.rounded_rectangle([85, 520, W - 85, 960], radius=24, fill=(8, 19, 36, 240), outline=(200, 155, 60, 235), width=4)
    draw.text((130, 560), "CALM VOICE REMINDERS (55% VOL)", font=FONT_SMALL, fill=(246, 211, 101, 255))
    rows = [
        ("Minimap Check", "Every 60s", (94, 234, 212, 255)),
        ("Vision & Wards", "Every 2 min", (246, 211, 101, 255)),
        ("Gold & Clean Reset", "Every 3 min", (147, 197, 253, 255)),
    ]
    for i, (lbl, iv, col) in enumerate(rows):
        ry = 635 + i * 95
        draw.rounded_rectangle([125, ry, W - 125, ry + 74], radius=16, fill=(14, 30, 54, 235), outline=(200, 155, 60, 130), width=2)
        draw.text((160, ry + 18), lbl, font=FONT_BODY, fill=(240, 230, 210, 255))
        draw.text((730, ry + 18), iv, font=FONT_BODY, fill=col)

    # Tarjeta Live 5v5 Scouting
    draw.rounded_rectangle([85, 1005, W - 85, 1410], radius=24, fill=(8, 19, 36, 240), outline=(10, 200, 185, 210), width=4)
    draw.text((130, 1042), "LIVE 5V5 MATCH SCOUTING", font=FONT_SMALL, fill=(94, 234, 212, 255))

    draw.rounded_rectangle([125, 1105, W - 125, 1235], radius=16, fill=(75, 18, 34, 185), outline=(233, 69, 96, 220), width=2)
    frame.alpha_composite(make_circle_avatar(assets["icon_lee"], 86), (150, 1125))
    draw.text((265, 1126), "THREAT: Enemy Lee Sin", font=FONT_BODY, fill=(253, 164, 175, 255))
    draw.text((265, 1176), "Master 120 LP · 61% WR · 420k", font=FONT_SMALL, fill=(240, 230, 210, 255))

    draw.rounded_rectangle([125, 1260, W - 125, 1380], radius=16, fill=(10, 62, 68, 185), outline=(10, 200, 185, 220), width=2)
    frame.alpha_composite(make_circle_avatar(assets["icon_yasuo"], 86), (150, 1276))
    draw.text((265, 1276), "CAMP TARGET: Enemy Yasuo", font=FONT_BODY, fill=(94, 234, 212, 255))
    draw.text((265, 1326), "43% WR · First Time · Punish!", font=FONT_SMALL, fill=(240, 230, 210, 255))


def main():
    print("Descargando assets oficiales de Data Dragon...")
    assets = download_assets()

    videos = [
        (
            OUT_DIR / "01_anti_overwolf_noflash.mp4",
            "Stop letting Overwolf tank your FPS. I built No Flash — a free, native Windows League coach. It analyzes your last 160 games, picks from your real champion pool, and imports optimal runes in one click. Zero bloatware. Download free in bio.",
            "en-US-AndrewMultilingualNeural",
            assets["splash_sylas"],
            [
                (0.0, 3.2, ["STOP letting Overwolf", "tank your FPS."]),
                (3.2, 7.5, ["Meet NoFlash — native", "Windows LoL Coach."]),
                (7.5, 12.2, ["160-game pool analysis", "+ 1-click LCU Runes."]),
                (12.2, 20.0, ["Zero Overwolf Bloat.", "Free Beta — Link in Bio!"]),
            ],
            scene_anti_overwolf,
        ),
        (
            OUT_DIR / "02_dodge_arena_queue.mp4",
            "Stuck in a six minute League queue? Stop scrolling and warm up your sidesteps in No Flash Dodge Arena. Dodge Lux ult, Blitz hooks, and Ziggs bombs, press F to Flash, and climb to Challenger before queue pops. Free download in bio.",
            "en-US-AndrewMultilingualNeural",
            assets["splash_jinx"],
            [
                (0.0, 3.8, ["6-minute LoL queue?", "Warm up your sidesteps."]),
                (3.8, 8.8, ["Dodge Lux R, Blitz Q", "& press [F] to FLASH!"]),
                (8.8, 13.5, ["Climb Iron to Challenger", "+ built-in Flashdle!"]),
                (13.5, 20.0, ["NEW in NoFlash Beta.", "Free Link in Bio!"]),
            ],
            scene_dodge_arena,
        ),
        (
            OUT_DIR / "03_calm_voice_minimap.mp4",
            "Here is how I stopped dying to three minute ganks. No Flash gives you a calm, low-distraction voice coach that reminds you to check your minimap every sixty seconds, plus live five v five scouting so you know who to camp. Try it free in bio.",
            "en-US-AndrewMultilingualNeural",
            assets["splash_asol"],
            [
                (0.0, 3.6, ["How I stopped dying", "to 3:00 ganks."]),
                (3.6, 8.8, ["Calm voice minimap check", "every 60 seconds."]),
                (8.8, 13.5, ["Live 5v5 Scout: spot", "the Threat & Camp Target."]),
                (13.5, 20.0, ["100% Riot API Safe.", "Download Free in Bio!"]),
            ],
            scene_calm_voice,
        ),
    ]

    for out_mp4, script_text, voice, splash_img, captions, scene_drawer in videos:
        render_video(out_mp4, script_text, voice, splash_img, assets, captions, scene_drawer)


if __name__ == "__main__":
    main()
