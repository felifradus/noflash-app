"""
Reconocimiento y parseo de comandos de voz para el Mini-HUD de NoFlash.
Permite decir cosas como:
  - "Mid no flash" / "ADC sin flash" / "Jinx no flash" / "Top TP" / "Supp exhaust"
  - "No flash" / "Sin flash" (apunta automáticamente a tu rival de línea si no nombraste rol/campeón)
Ignora conversaciones normales (Discord) si no contienen un trigger de hechizo válido.
"""

from __future__ import annotations

import io
import logging
import re
import unicodedata
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Sinónimos de roles (ES + EN + fonética común de reconocimiento de voz)
ROLE_ALIASES: dict[str, list[str]] = {
    "TOP": ["top", "toplaner", "top laner", "arriba", "el top", "la top"],
    "JUNGLE": ["jg", "jng", "jungla", "jungle", "jungler", "selva", "el jg", "la jungla"],
    "MIDDLE": ["mid", "medio", "midlaner", "mid laner", "el mid", "la mid", "mit"],
    "BOTTOM": ["adc", "ad", "bot", "tirador", "carry", "ad carry", "el adc", "la adc", "a de ce"],
    "UTILITY": ["sup", "supp", "support", "soporte", "apoyo", "suport", "el sup", "la sup"],
}

# Sinónimos de Summoner Spells -> dd_key oficial de Data Dragon
SPELL_ALIASES: list[tuple[str, list[str]]] = [
    ("SummonerFlash", [
        "no flash", "sin flash", "flash", "flasheo", "flashe", "flashea",
        "destello", "sin destello", "no destello", "gasto flash", "tiro flash",
        "no f", "sin f", "f",
    ]),
    ("SummonerTeleport", [
        "tp", "tepe", "teleport", "teletransportacion", "teletransporte", "no tp", "sin tp",
    ]),
    ("SummonerDot", [
        "ignite", "ignit", "prender", "no ignite", "sin ignite", "prendio",
    ]),
    ("SummonerExhaust", [
        "exhaust", "exaust", "extenuar", "extenuacion", "no exhaust", "sin exhaust",
    ]),
    ("SummonerBarrier", [
        "barrier", "barrera", "escudo", "no barrier", "sin barrier",
    ]),
    ("SummonerHeal", [
        "heal", "curar", "curacion", "no heal", "sin heal",
    ]),
    ("SummonerBoost", [
        "cleanse", "clens", "limpiar", "purificar", "no cleanse", "sin cleanse",
    ]),
    ("SummonerHaste", [
        "ghost", "fantasmal", "fantasma", "no ghost", "sin ghost",
    ]),
    ("SummonerSmite", [
        "smite", "aplastar", "no smite", "sin smite",
    ]),
]

# Abreviaturas populares de campeones en voz (ES/EN)
CHAMP_NICKNAMES: dict[str, str] = {
    "mf": "missfortune",
    "tf": "twistedfate",
    "lee": "leesin",
    "yi": "masteryi",
    "mundo": "drmundo",
    "cait": "caitlyn",
    "ez": "ezreal",
    "ezre": "ezreal",
    "kaisa": "kaisa",
    "kai sa": "kaisa",
    "kha": "khazix",
    "cho": "chogath",
    "kog": "kogmaw",
    "vel": "velkoz",
    "rek": "reksai",
    "bel": "belveth",
    "j4": "jarvaniv",
    "jarvan": "jarvaniv",
    "wu": "monkeyking",
    "wukong": "monkeyking",
    "mono": "monkeyking",
    "xin": "xinzhao",
    "tahm": "tahmkench",
    "kench": "tahmkench",
    "asol": "aurelionsol",
    "aurelion": "aurelionsol",
    "morg": "morgana",
    "kat": "katarina",
    "kata": "katarina",
    "cass": "cassiopeia",
    "cassio": "cassiopeia",
    "malph": "malphite",
    "malza": "malzahar",
    "morde": "mordekaiser",
    "naut": "nautilus",
    "blitz": "blitzcrank",
    "trist": "tristana",
    "ori": "orianna",
    "gp": "gangplank",
    "panth": "pantheon",
    "vlad": "vladimir",
    "volibear": "volibear",
    "voli": "volibear",
    "ww": "warwick",
    "fid": "fiddlesticks",
    "fiddle": "fiddlesticks",
    "heca": "hecarim",
    "sej": "sejuani",
    "rene": "renekton",
    "renek": "renekton",
    "cam": "camille",
    "gwen": "gwen",
    "lb": "leblanc",
    "ali": "alistar",
    "sera": "seraphine",
    "renata": "renata",
}


def _normalize(text: str) -> str:
    s = unicodedata.normalize("NFKD", (text or "").lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def _norm_pos(pos: str, idx: int) -> str:
    p = (pos or "").upper()
    if p in ("TOP", "JUNGLE", "MIDDLE", "BOTTOM", "UTILITY"):
        return p
    if p == "JG":
        return "JUNGLE"
    if p == "MID":
        return "MIDDLE"
    if p == "ADC":
        return "BOTTOM"
    if p in ("SUP", "SUPPORT"):
        return "UTILITY"
    order = ["TOP", "JUNGLE", "MIDDLE", "BOTTOM", "UTILITY"]
    return order[idx] if 0 <= idx < 5 else "UNKNOWN"


def _has_word(norm_text: str, phrase: str) -> bool:
    return bool(re.search(rf"(?:^|\s){re.escape(phrase)}(?:\s|$)", norm_text))


def _match_spell(norm_text: str) -> Optional[str]:
    # Evitar falso positivo por la letra "f" suelta en frases largas de Discord
    words = norm_text.split()
    for dd_key, aliases in SPELL_ALIASES:
        for alias in aliases:
            if alias == "f":
                if len(words) <= 3 and _has_word(norm_text, "f"):
                    return dd_key
                continue
            if _has_word(norm_text, alias):
                return dd_key
    return None


def _match_enemy_index(
    norm_text: str,
    enemies: list[dict[str, Any]],
    my_position: str = "",
) -> Optional[int]:
    if not enemies:
        return None

    # 1. Buscar por nombre o apodo de campeón enemigo presente en la partida
    compact_text = norm_text.replace(" ", "")
    for idx, en in enumerate(enemies[:5]):
        champ_norm = _normalize(en.get("champion", "")).replace(" ", "")
        if not champ_norm:
            continue
        if len(champ_norm) >= 3 and champ_norm in compact_text:
            return idx
        # Chequear apodos (ej. "mf", "lee", "morg", "j4")
        for nick, target_champ in CHAMP_NICKNAMES.items():
            if target_champ == champ_norm and _has_word(norm_text, nick):
                return idx

    # 2. Buscar por rol (Top / Jungla / Mid / ADC / Supp)
    for role_key, aliases in ROLE_ALIASES.items():
        if any(_has_word(norm_text, a) for a in aliases):
            for idx, en in enumerate(enemies[:5]):
                if _norm_pos(en.get("position", ""), idx) == role_key:
                    return idx

    # 3. Atajo inteligente: si dijo literalmente "no flash" / "sin flash" sin nombrar rol,
    #    apuntar a su rival directo de línea (my_position) si está disponible.
    is_bare_no_flash = any(
        _has_word(norm_text, p)
        for p in ("no flash", "sin flash", "no destello", "sin destello", "flasheo", "gasto flash")
    )
    if is_bare_no_flash and my_position:
        my_norm = _norm_pos(my_position, -1)
        for idx, en in enumerate(enemies[:5]):
            if _norm_pos(en.get("position", ""), idx) == my_norm:
                return idx

    return None


def parse_voice_command(
    transcript: str,
    enemies: list[dict[str, Any]],
    my_position: str = "",
) -> dict[str, Any]:
    """
    Analiza una transcripción de voz y devuelve el enemigo + hechizo a iniciar,
    o {matched: False} si era charla normal (anti-Discord).
    """
    norm = _normalize(transcript)
    if not norm:
        return {"matched": False, "transcript": transcript}

    spell_dd_key = _match_spell(norm)
    if not spell_dd_key:
        return {"matched": False, "transcript": transcript}

    enemy_idx = _match_enemy_index(norm, enemies, my_position=my_position)
    if enemy_idx is None:
        return {"matched": False, "transcript": transcript}

    en = enemies[enemy_idx]
    spells = en.get("spells") or []
    spell_idx = None
    for s_idx, sp in enumerate(spells[:2]):
        if (sp.get("dd_key") or "").lower() == spell_dd_key.lower():
            spell_idx = s_idx
            break

    # Si no encontramos ese hechizo exacto en el enemigo, no disparamos nada erróneo
    if spell_idx is None:
        return {
            "matched": False,
            "transcript": transcript,
            "reason": "spell_not_equipped",
        }

    sp_obj = spells[spell_idx]
    return {
        "matched": True,
        "transcript": transcript,
        "enemy_idx": enemy_idx,
        "spell_idx": spell_idx,
        "champion": en.get("champion", ""),
        "role": _norm_pos(en.get("position", ""), enemy_idx),
        "spell_name": sp_obj.get("name", spell_dd_key),
        "spell_dd_key": sp_obj.get("dd_key", spell_dd_key),
    }


def transcribe_wav_bytes(wav_bytes: bytes, lang: str = "es-AR") -> str:
    """Transcribe un clip corto WAV (16kHz mono) usando SpeechRecognition (sin API key)."""
    if not wav_bytes or len(wav_bytes) < 1000:
        return ""
    try:
        import speech_recognition as sr
    except ImportError:
        logger.warning("SpeechRecognition no está instalado.")
        return ""

    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(io.BytesIO(wav_bytes)) as source:
            audio = recognizer.record(source)
        # Intentar primero en el idioma configurado (es-AR / en-US)
        try:
            return recognizer.recognize_google(audio, language=lang)
        except sr.UnknownValueError:
            # Si estaba en español y dijo algo en inglés ("mid no flash"), probar fallback rápido
            fallback = "en-US" if not lang.lower().startswith("en") else "es-AR"
            try:
                return recognizer.recognize_google(audio, language=fallback)
            except Exception:
                return ""
    except Exception as e:
        logger.debug(f"Error transcribiendo audio de voz: {e}")
        return ""
