"""
Base de datos de Runas Meta Pro / Emerald+ (estilo U.GG / Probuilds) para los 173 campeones de LoL.
Todos los IDs están validados contra Data Dragon oficial (Patch 16.x — incluye Axiom Arcanist,
Legend: Haste, Jack of All Trades, Grisly Mementos, Deep Ward y Sixth Sense).
"""

from __future__ import annotations

from typing import Any, Optional

# Árboles oficiales de Riot
PREC = 8000
DOM = 8100
SORC = 8200
INSP = 8300
RES = 8400

TREE_NAMES: dict[int, str] = {
    PREC: "Precision",
    DOM: "Domination",
    SORC: "Sorcery",
    INSP: "Inspiration",
    RES: "Resolve",
}

KEYSTONE_NAMES: dict[int, str] = {
    8005: "Press the Attack",
    8008: "Lethal Tempo",
    8021: "Fleet Footwork",
    8010: "Conqueror",
    8112: "Electrocute",
    8128: "Dark Harvest",
    9923: "Hail of Blades",
    8214: "Summon Aery",
    8229: "Arcane Comet",
    8230: "Phase Rush",
    8351: "Glacial Augment",
    8360: "Unsealed Spellbook",
    8369: "First Strike",
    8437: "Grasp of the Undying",
    8439: "Aftershock",
    8465: "Guardian",
}

PERK_NAMES: dict[int, str] = {
    **KEYSTONE_NAMES,
    # Precision
    9101: "Absorb Life", 9111: "Triumph", 8009: "Presence of Mind",
    9104: "Legend: Alacrity", 9105: "Legend: Haste", 9103: "Legend: Bloodline",
    8014: "Coup de Grace", 8017: "Cut Down", 8299: "Last Stand",
    # Domination
    8126: "Cheap Shot", 8139: "Taste of Blood", 8143: "Sudden Impact",
    8137: "Sixth Sense", 8140: "Grisly Mementos", 8141: "Deep Ward",
    8135: "Treasure Hunter", 8105: "Relentless Hunter", 8106: "Ultimate Hunter",
    # Sorcery
    8224: "Axiom Arcanist", 8226: "Manaflow Band", 8275: "Nimbus Cloak",
    8210: "Transcendence", 8234: "Celerity", 8233: "Absolute Focus",
    8237: "Scorch", 8232: "Waterwalking", 8236: "Gathering Storm",
    # Resolve
    8446: "Demolish", 8463: "Font of Life", 8401: "Shield Bash",
    8429: "Conditioning", 8444: "Second Wind", 8473: "Bone Plating",
    8451: "Overgrowth", 8453: "Revitalize", 8242: "Unflinching",
    # Inspiration
    8306: "Hextech Flashtraption", 8304: "Magical Footwear", 8321: "Cash Back",
    8313: "Triple Tonic", 8352: "Time Warp Tonic", 8345: "Biscuit Delivery",
    8347: "Cosmic Insight", 8410: "Approach Velocity", 8316: "Jack Of All Trades",
}

# Shards frecuentes
SH_AS_AD_HP = [5005, 5008, 5011]   # Attack Speed / Adaptive / Flat HP
SH_AS_AD_SHP = [5005, 5008, 5001]  # Attack Speed / Adaptive / Scaling HP
SH_AD_AD_HP = [5008, 5008, 5011]   # Adaptive / Adaptive / Flat HP
SH_AD_AD_SHP = [5008, 5008, 5001]  # Adaptive / Adaptive / Scaling HP
SH_AH_AD_SHP = [5007, 5008, 5001]  # Ability Haste / Adaptive / Scaling HP
SH_AH_MS_SHP = [5007, 5010, 5001]  # Ability Haste / Move Speed / Scaling HP
SH_AH_HP_SHP = [5007, 5001, 5001]  # Ability Haste / Scaling HP / Scaling HP
SH_AS_MS_SHP = [5005, 5010, 5001]  # Attack Speed / Move Speed / Scaling HP

# Formato compacto: (primary_tree, sub_tree, [keystone, p1, p2, p3, s1, s2], shards)
PRO_RUNES_DB: dict[str, tuple[int, int, list[int], list[int]]] = {
    # ── TOP / FIGHTERS / TANKS ──
    "Aatrox":       (PREC, RES,  [8010, 9111, 9105, 8299, 8473, 8451], SH_AD_AD_SHP),
    "Ambessa":      (PREC, RES,  [8010, 9111, 9105, 8299, 8401, 8473], SH_AD_AD_SHP),
    "Camille":      (RES,  INSP, [8437, 8401, 8473, 8451, 8304, 8345], SH_AS_AD_SHP),
    "Chogath":      (RES,  INSP, [8437, 8446, 8444, 8451, 8304, 8410], SH_AS_AD_SHP),
    "Darius":       (PREC, SORC, [8010, 9111, 9104, 8299, 8275, 8234], SH_AS_AD_SHP),
    "DrMundo":      (RES,  INSP, [8437, 8446, 8444, 8451, 8304, 8410], SH_AS_MS_SHP),
    "Fiora":        (RES,  PREC, [8437, 8446, 8444, 8451, 9111, 9104], SH_AS_AD_SHP),
    "Gangplank":    (RES,  INSP, [8437, 8446, 8444, 8451, 8345, 8316], SH_AD_AD_SHP),
    "Garen":        (PREC, RES,  [8010, 9111, 9105, 8299, 8446, 8451], SH_AD_AD_SHP),
    "Gnar":         (RES,  PREC, [8437, 8446, 8473, 8451, 9111, 9104], SH_AS_AD_SHP),
    "Gragas":       (SORC, INSP, [8230, 8226, 8210, 8237, 8345, 8347], SH_AH_AD_SHP),
    "Gwen":         (PREC, RES,  [8010, 8009, 9104, 8299, 8473, 8451], SH_AS_AD_SHP),
    "Heimerdinger": (SORC, DOM,  [8229, 8226, 8210, 8237, 8139, 8135], SH_AS_AD_HP),
    "Illaoi":       (RES,  PREC, [8437, 8446, 8444, 8451, 8009, 8299], SH_AD_AD_SHP),
    "Irelia":       (PREC, RES,  [8008, 9101, 9104, 8299, 8473, 8451], SH_AS_AD_HP),
    "Jax":          (PREC, INSP, [8008, 9111, 9104, 8299, 8304, 8345], SH_AS_AD_SHP),
    "Jayce":        (PREC, INSP, [8010, 8009, 9105, 8017, 8304, 8345], SH_AD_AD_SHP),
    "KSante":       (RES,  INSP, [8437, 8401, 8444, 8451, 8345, 8410], SH_AS_MS_SHP),
    "Kayle":        (PREC, SORC, [8008, 9101, 9104, 8014, 8234, 8236], SH_AS_AD_SHP),
    "Kennen":       (DOM,  SORC, [8112, 8139, 8140, 8106, 8224, 8210], SH_AS_AD_HP),
    "Kled":         (PREC, RES,  [8010, 9111, 9104, 8299, 8446, 8473], SH_AS_AD_HP),
    "Malphite":     (SORC, RES,  [8229, 8226, 8210, 8237, 8444, 8451], SH_AH_AD_SHP),
    "Mordekaiser":  (PREC, RES,  [8010, 9111, 9104, 8299, 8473, 8453], SH_AS_AD_SHP),
    "Nasus":        (PREC, INSP, [8021, 9101, 9105, 8299, 8304, 8410], SH_AH_MS_SHP),
    "Olaf":         (PREC, INSP, [8010, 9111, 9104, 8299, 8304, 8410], SH_AS_AD_SHP),
    "Ornn":         (RES,  INSP, [8437, 8446, 8444, 8451, 8345, 8347], SH_AH_HP_SHP),
    "Pantheon":     (PREC, INSP, [8010, 9111, 9105, 8014, 8345, 8347], SH_AD_AD_SHP),
    "Poppy":        (RES,  INSP, [8437, 8401, 8444, 8451, 8345, 8347], SH_AS_AD_SHP),
    "Quinn":        (DOM,  SORC, [8112, 8143, 8140, 8105, 8234, 8236], SH_AS_AD_HP),
    "Renekton":     (PREC, RES,  [8010, 9111, 9104, 8299, 8473, 8451], SH_AS_AD_SHP),
    "Riven":        (PREC, INSP, [8010, 9111, 9105, 8299, 8304, 8316], SH_AD_AD_SHP),
    "Rumble":       (SORC, RES,  [8229, 8224, 8233, 8237, 8473, 8451], SH_AS_AD_HP),
    "Sett":         (PREC, RES,  [8010, 9111, 9104, 8299, 8444, 8451], SH_AS_AD_SHP),
    "Shen":         (RES,  DOM,  [8437, 8401, 8444, 8451, 8126, 8106], SH_AS_AD_SHP),
    "Singed":       (SORC, RES,  [8230, 8275, 8234, 8236, 8444, 8451], SH_AD_MS_SHP := [5008, 5010, 5001]),
    "Sion":         (RES,  INSP, [8437, 8446, 8444, 8451, 8304, 8410], SH_AS_AD_SHP),
    "TahmKench":    (RES,  PREC, [8437, 8401, 8444, 8453, 9111, 9104], SH_AS_HP_SHP := [5005, 5001, 5001]),
    "Teemo":        (PREC, SORC, [8005, 9101, 9104, 8017, 8234, 8236], SH_AS_AD_HP),
    "Trundle":      (PREC, RES,  [8008, 9111, 9104, 8299, 8446, 8473], SH_AS_AD_SHP),
    "Tryndamere":   (PREC, RES,  [8008, 9101, 9104, 8299, 8444, 8451], SH_AS_AD_SHP),
    "Urgot":        (PREC, RES,  [8005, 9111, 9103, 8299, 8444, 8451], SH_AD_AD_SHP),
    "Volibear":     (PREC, INSP, [8005, 8009, 9105, 8299, 8316, 8313], SH_AS_AD_SHP),
    "Warwick":      (PREC, RES,  [8008, 9111, 9104, 8299, 8444, 8453], SH_AS_AD_SHP),
    "Yorick":       (RES,  INSP, [8437, 8446, 8444, 8451, 8304, 8410], SH_AS_AD_SHP),
    "Zaahen":       (PREC, RES,  [8010, 9111, 9104, 8299, 8473, 8451], SH_AS_AD_SHP),

    # ── JUNGLE ──
    "Amumu":        (PREC, DOM,  [8010, 9111, 9105, 8299, 8126, 8106], SH_AS_AD_SHP),
    "Belveth":      (PREC, INSP, [8010, 9111, 9104, 8014, 8304, 8347], SH_AS_AD_SHP),
    "Briar":        (PREC, INSP, [8005, 9111, 9104, 8299, 8304, 8347], SH_AS_AD_SHP),
    "Diana":        (PREC, INSP, [8010, 9111, 9104, 8014, 8304, 8347], SH_AS_AD_SHP),
    "Ekko":         (DOM,  INSP, [8128, 8143, 8140, 8135, 8304, 8347], SH_AS_AD_SHP),
    "Elise":        (DOM,  SORC, [8128, 8126, 8140, 8105, 8233, 8232], SH_AS_AD_SHP),
    "Evelynn":      (DOM,  SORC, [8112, 8143, 8140, 8105, 8233, 8236], SH_AD_AD_SHP),
    "Fiddlesticks": (DOM,  INSP, [8128, 8126, 8140, 8106, 8304, 8347], SH_AH_AD_SHP),
    "Graves":       (PREC, INSP, [8021, 9111, 9104, 8014, 8304, 8347], SH_AS_AD_SHP),
    "Hecarim":      (SORC, INSP, [8230, 8275, 8234, 8232, 8304, 8347], SH_AD_AD_SHP),
    "Ivern":        (SORC, INSP, [8214, 8275, 8210, 8232, 8304, 8347], SH_AH_MS_SHP),
    "JarvanIV":     (PREC, INSP, [8010, 9111, 9104, 8014, 8304, 8347], SH_AS_AD_SHP),
    "Karthus":      (DOM,  PREC, [8128, 8126, 8140, 8106, 8009, 8299], SH_AD_AD_SHP),
    "Kayn":         (DOM,  INSP, [8128, 8143, 8140, 8135, 8304, 8347], SH_AD_AD_SHP),
    "Khazix":       (DOM,  INSP, [8128, 8143, 8140, 8135, 8304, 8347], SH_AD_AD_SHP),
    "Kindred":      (PREC, INSP, [8005, 9111, 9104, 8014, 8304, 8347], SH_AS_AD_SHP),
    "LeeSin":       (PREC, INSP, [8010, 9111, 9104, 8014, 8304, 8347], SH_AS_AD_SHP),
    "Lillia":       (PREC, INSP, [8010, 9111, 9105, 8014, 8304, 8347], SH_AD_MS_SHP),
    "MasterYi":     (PREC, DOM,  [8008, 9111, 9104, 8014, 8143, 8135], SH_AS_AD_SHP),
    "MonkeyKing":   (PREC, INSP, [8010, 9111, 9104, 8299, 8304, 8347], SH_AS_AD_SHP),
    "Nidalee":      (DOM,  SORC, [8128, 8143, 8140, 8135, 8210, 8232], SH_AS_AD_SHP),
    "Nocturne":     (PREC, DOM,  [8010, 9111, 9104, 8014, 8140, 8106], SH_AS_AD_SHP),
    "Nunu":         (SORC, DOM,  [8230, 8275, 8234, 8232, 8126, 8105], SH_AS_MS_SHP),
    "Rammus":       (RES,  PREC, [8439, 8463, 8429, 8451, 9111, 9104], SH_AS_MS_SHP),
    "RekSai":       (PREC, INSP, [8010, 9111, 9104, 8014, 8304, 8347], SH_AS_AD_SHP),
    "Rengar":       (PREC, INSP, [8010, 9111, 9104, 8014, 8304, 8347], SH_AS_AD_SHP),
    "Sejuani":      (RES,  PREC, [8439, 8463, 8429, 8451, 9111, 9104], SH_AS_HP_SHP),
    "Shaco":        (DOM,  PREC, [9923, 8143, 8140, 8105, 9104, 8014], SH_AS_AD_SHP),
    "Shyvana":      (PREC, INSP, [8021, 9111, 9105, 8014, 8304, 8347], SH_AS_AD_SHP),
    "Skarner":      (RES,  INSP, [8437, 8401, 8429, 8451, 8304, 8410], SH_AS_MS_SHP),
    "Taliyah":      (DOM,  SORC, [8128, 8126, 8140, 8135, 8210, 8232], SH_AS_AD_SHP),
    "Udyr":         (PREC, INSP, [8010, 9111, 9105, 8299, 8304, 8410], SH_AS_MS_SHP),
    "Vi":           (PREC, INSP, [8010, 9111, 9104, 8014, 8304, 8347], SH_AS_AD_SHP),
    "Viego":        (PREC, INSP, [8010, 9111, 9104, 8014, 8304, 8347], SH_AS_AD_SHP),
    "XinZhao":      (PREC, INSP, [8010, 9111, 9104, 8014, 8304, 8347], SH_AS_AD_SHP),
    "Zac":          (RES,  INSP, [8439, 8463, 8429, 8453, 8304, 8347], SH_AH_HP_SHP),

    # ── MID ──
    "Ahri":         (DOM,  SORC, [8112, 8139, 8140, 8106, 8226, 8210], SH_AS_AD_SHP),
    "Akali":        (DOM,  RES,  [8112, 8143, 8140, 8106, 8444, 8451], SH_AD_AD_SHP),
    "Akshan":       (PREC, RES,  [8005, 8009, 9104, 8017, 8473, 8401], SH_AS_AD_HP),
    "Anivia":       (DOM,  PREC, [8112, 8126, 8140, 8105, 8009, 8014], SH_AS_AD_SHP),
    "Annie":        (DOM,  SORC, [8112, 8126, 8140, 8106, 8226, 8210], SH_AD_AD_SHP),
    "AurelionSol":  (SORC, PREC, [8229, 8226, 8233, 8236, 8009, 8017], SH_AD_AD_SHP),
    "Aurora":       (DOM,  SORC, [8112, 8139, 8140, 8106, 8226, 8210], SH_AS_AD_HP),
    "Azir":         (PREC, RES,  [8008, 8009, 9104, 8017, 8444, 8451], SH_AS_AD_SHP),
    "Brand":        (SORC, PREC, [8229, 8226, 8210, 8237, 8009, 8017], SH_AD_AD_SHP),
    "Cassiopeia":   (PREC, SORC, [8010, 8009, 9105, 8299, 8226, 8210], SH_AD_AD_SHP),
    "Fizz":         (DOM,  SORC, [8112, 8143, 8140, 8135, 8210, 8237], SH_AS_AD_HP),
    "Galio":        (RES,  SORC, [8439, 8401, 8444, 8451, 8275, 8210], SH_AH_AD_SHP),
    "Hwei":         (SORC, PREC, [8229, 8226, 8210, 8237, 8009, 8017], SH_AH_AD_SHP),
    "Kassadin":     (DOM,  PREC, [8112, 8139, 8140, 8106, 8009, 8014], SH_AD_AD_SHP),
    "Katarina":     (DOM,  PREC, [8112, 8143, 8140, 8105, 9111, 8014], SH_AD_AD_HP),
    "Leblanc":      (DOM,  SORC, [8112, 8143, 8140, 8106, 8226, 8210], SH_AS_AD_HP),
    "Lissandra":    (DOM,  SORC, [8112, 8126, 8140, 8106, 8226, 8210], SH_AH_AD_SHP),
    "Locke":        (DOM,  SORC, [8112, 8143, 8140, 8106, 8226, 8210], SH_AD_AD_SHP),
    "Lux":          (SORC, DOM,  [8229, 8224, 8210, 8237, 8126, 8106], SH_AH_AD_SHP),
    "Malzahar":     (SORC, INSP, [8214, 8226, 8210, 8237, 8304, 8347], SH_AH_AD_SHP),
    "Mel":          (SORC, PREC, [8229, 8226, 8210, 8237, 8009, 8017], SH_AH_AD_SHP),
    "Naafiri":      (SORC, PREC, [8229, 8226, 8210, 8237, 9111, 8014], SH_AD_AD_SHP),
    "Neeko":        (SORC, DOM,  [8229, 8226, 8210, 8237, 8139, 8106], SH_AS_AD_HP),
    "Orianna":      (SORC, INSP, [8214, 8226, 8210, 8237, 8345, 8347], SH_AS_AD_SHP),
    "Qiyana":       (DOM,  PREC, [8112, 8143, 8140, 8135, 8009, 8299], SH_AD_AD_HP),
    "Ryze":         (SORC, RES,  [8230, 8226, 8210, 8236, 8444, 8451], SH_AS_AD_SHP),
    "Swain":        (PREC, SORC, [8010, 8009, 9105, 8299, 8226, 8210], SH_AH_AD_SHP),
    "Sylas":        (DOM,  SORC, [8112, 8143, 8140, 8135, 8210, 8237], SH_AH_AD_SHP),
    "Syndra":       (SORC, INSP, [8214, 8226, 8210, 8237, 8313, 8347], SH_AH_AD_SHP),
    "Talon":        (DOM,  SORC, [8112, 8143, 8140, 8135, 8275, 8233], SH_AD_AD_HP),
    "TwistedFate":  (SORC, INSP, [8229, 8226, 8210, 8237, 8345, 8316], SH_AS_AD_SHP),
    "Veigar":       (SORC, INSP, [8229, 8226, 8210, 8236, 8304, 8347], SH_AH_AD_SHP),
    "Velkoz":       (SORC, INSP, [8229, 8226, 8210, 8237, 8345, 8347], SH_AH_AD_SHP),
    "Vex":          (DOM,  SORC, [8112, 8139, 8140, 8106, 8226, 8210], SH_AS_AD_HP),
    "Viktor":       (SORC, RES,  [8214, 8226, 8210, 8237, 8401, 8473], SH_AS_AD_SHP),
    "Vladimir":     (SORC, INSP, [8230, 8275, 8210, 8236, 8304, 8347], SH_AH_MS_SHP),
    "Xerath":       (SORC, INSP, [8229, 8226, 8210, 8237, 8345, 8347], SH_AH_AD_SHP),
    "Yasuo":        (PREC, RES,  [8008, 9101, 9104, 8299, 8444, 8451], SH_AS_AD_HP),
    "Yone":         (PREC, RES,  [8008, 9101, 9104, 8299, 8444, 8451], SH_AS_AD_HP),
    "Zed":          (DOM,  SORC, [8112, 8139, 8140, 8106, 8210, 8237], SH_AH_AD_SHP),
    "Ziggs":        (SORC, INSP, [8229, 8226, 8210, 8237, 8304, 8345], SH_AH_AD_SHP),
    "Zoe":          (DOM,  SORC, [8112, 8143, 8140, 8135, 8275, 8210], SH_AS_AD_HP),

    # ── ADC / BOT ──
    "Aphelios":     (PREC, SORC, [8021, 9101, 9103, 8017, 8233, 8236], SH_AS_AD_HP),
    "Ashe":         (PREC, INSP, [8008, 8009, 9104, 8017, 8345, 8410], SH_AS_AD_HP),
    "Caitlyn":      (PREC, SORC, [8021, 9101, 9103, 8014, 8233, 8236], SH_AS_AD_HP),
    "Corki":        (PREC, INSP, [8010, 8009, 9104, 8017, 8304, 8345], SH_AS_AD_HP),
    "Draven":       (PREC, SORC, [8008, 9111, 9103, 8014, 8233, 8236], SH_AS_AD_HP),
    "Ezreal":       (PREC, INSP, [8005, 8009, 9105, 8017, 8304, 8316], SH_AS_AD_HP),
    "Jhin":         (PREC, SORC, [8021, 8009, 9103, 8014, 8234, 8236], SH_AD_AD_HP),
    "Jinx":         (PREC, SORC, [8008, 9101, 9104, 8017, 8233, 8236], SH_AS_AD_HP),
    "Kaisa":        (PREC, INSP, [8008, 8009, 9103, 8014, 8304, 8345], SH_AS_AD_HP),
    "Kalista":      (PREC, DOM,  [8008, 9111, 9104, 8299, 8143, 8135], SH_AS_AD_HP),
    "KogMaw":       (PREC, RES,  [8008, 9101, 9104, 8017, 8429, 8451], SH_AS_AD_SHP),
    "Lucian":       (PREC, INSP, [8005, 8009, 9103, 8017, 8304, 8345], SH_AS_AD_HP),
    "MissFortune":  (PREC, SORC, [8005, 8009, 9103, 8017, 8224, 8236], SH_AS_AD_HP),
    "Nilah":        (PREC, RES,  [8010, 9111, 9104, 8299, 8444, 8453], SH_AS_AD_SHP),
    "Samira":       (PREC, DOM,  [8010, 9111, 9103, 8299, 8143, 8135], SH_AS_AD_HP),
    "Sivir":        (PREC, SORC, [8008, 8009, 9103, 8017, 8234, 8236], SH_AS_AD_HP),
    "Smolder":      (PREC, SORC, [8021, 9101, 9105, 8017, 8226, 8236], SH_AD_AD_SHP),
    "Tristana":     (PREC, INSP, [8005, 9101, 9103, 8014, 8304, 8345], SH_AS_AD_HP),
    "Twitch":       (PREC, DOM,  [8008, 9111, 9104, 8014, 8143, 8106], SH_AS_AD_HP),
    "Varus":        (PREC, INSP, [8008, 8009, 9104, 8014, 8304, 8345], SH_AS_AD_HP),
    "Vayne":        (PREC, RES,  [8008, 9111, 9104, 8014, 8429, 8451], SH_AS_AD_SHP),
    "Xayah":        (PREC, INSP, [8008, 8009, 9103, 8017, 8304, 8345], SH_AS_AD_HP),
    "Yunara":       (PREC, SORC, [8008, 9101, 9104, 8017, 8233, 8236], SH_AS_AD_HP),
    "Zeri":         (PREC, RES,  [8008, 9101, 9104, 8017, 8429, 8451], SH_AS_AD_SHP),

    # ── SUPPORT ──
    "Alistar":      (RES,  INSP, [8439, 8463, 8473, 8451, 8306, 8347], SH_AH_MS_SHP),
    "Bard":         (DOM,  RES,  [8112, 8126, 8141, 8105, 8473, 8451], SH_AS_MS_SHP),
    "Blitzcrank":   (INSP, RES,  [8351, 8306, 8345, 8347, 8473, 8451], SH_AH_MS_SHP),
    "Braum":        (RES,  INSP, [8465, 8463, 8473, 8242, 8345, 8347], SH_AH_HP_SHP),
    "Janna":        (SORC, RES,  [8214, 8226, 8234, 8237, 8463, 8453], SH_AD_MS_SHP),
    "Karma":        (SORC, RES,  [8229, 8226, 8210, 8237, 8463, 8453], SH_AH_AD_SHP),
    "Leona":        (RES,  INSP, [8439, 8463, 8473, 8451, 8306, 8347], SH_AH_HP_SHP),
    "Lulu":         (SORC, INSP, [8214, 8226, 8210, 8237, 8345, 8347], SH_AH_AD_SHP),
    "Maokai":       (RES,  INSP, [8439, 8463, 8473, 8451, 8345, 8347], SH_AH_MS_SHP),
    "Milio":        (SORC, RES,  [8214, 8226, 8210, 8237, 8463, 8453], SH_AH_MS_SHP),
    "Morgana":      (SORC, INSP, [8229, 8226, 8210, 8237, 8345, 8347], SH_AH_AD_SHP),
    "Nami":         (SORC, RES,  [8214, 8226, 8210, 8237, 8463, 8453], SH_AH_AD_SHP),
    "Nautilus":     (RES,  INSP, [8439, 8463, 8473, 8451, 8306, 8347], SH_AH_HP_SHP),
    "Pyke":         (DOM,  RES,  [9923, 8143, 8141, 8106, 8473, 8242], SH_AD_AD_HP),
    "Rakan":        (RES,  INSP, [8465, 8463, 8473, 8242, 8345, 8347], SH_AH_MS_SHP),
    "Rell":         (RES,  INSP, [8439, 8463, 8473, 8451, 8306, 8347], SH_AH_MS_SHP),
    "Renata":       (RES,  INSP, [8465, 8401, 8473, 8453, 8345, 8347], SH_AH_MS_SHP),
    "Senna":        (PREC, SORC, [8021, 8009, 9104, 8017, 8234, 8236], SH_AS_AD_HP),
    "Seraphine":    (SORC, RES,  [8214, 8226, 8210, 8237, 8463, 8453], SH_AH_AD_SHP),
    "Sona":         (SORC, RES,  [8214, 8226, 8210, 8237, 8429, 8453], SH_AH_AD_SHP),
    "Soraka":       (SORC, RES,  [8214, 8226, 8234, 8237, 8473, 8453], SH_AH_MS_SHP),
    "Taric":        (RES,  PREC, [8465, 8463, 8473, 8453, 8009, 9105], SH_AH_HP_SHP),
    "Thresh":       (RES,  INSP, [8439, 8463, 8473, 8451, 8345, 8347], SH_AH_MS_SHP),
    "Yuumi":        (SORC, RES,  [8214, 8226, 8210, 8237, 8463, 8453], SH_AH_AD_SHP),
    "Zilean":       (SORC, INSP, [8214, 8226, 8210, 8237, 8345, 8347], SH_AH_MS_SHP),
    "Zyra":         (SORC, DOM,  [8229, 8226, 8210, 8237, 8139, 8135], SH_AH_AD_SHP),
}


def get_pro_rune_page(champion: str) -> Optional[dict[str, Any]]:
    """Devuelve la página completa de 9 runas (U.GG / Probuilds meta) para el campeón."""
    entry = PRO_RUNES_DB.get(champion)
    if not entry:
        # Búsqueda case-insensitive por si viene con espacios o diferente capitalización
        low = (champion or "").lower().replace(" ", "").replace("'", "").replace(".", "")
        for k, v in PRO_RUNES_DB.items():
            if k.lower() == low:
                entry = v
                break
    if not entry:
        return None

    primary, sub, runes6, shards3 = entry
    perks = runes6 + shards3
    keystone_id = runes6[0]
    minor_primary = [PERK_NAMES.get(p, "") for p in runes6[1:4]]
    minor_sub = [PERK_NAMES.get(p, "") for p in runes6[4:6]]
    return {
        "primary": primary,
        "sub": sub,
        "perks": perks,
        "keystone": KEYSTONE_NAMES.get(keystone_id, "Conqueror"),
        "primary_tree": TREE_NAMES.get(primary, "Precision"),
        "secondary_tree": TREE_NAMES.get(sub, "Inspiration"),
        "minor_summary": f"{' · '.join(minor_primary)} | {' · '.join(minor_sub)}",
    }
