"""
Datos hardcodeados de counters, sinergias y tags de campeones para el MVP.
Estos datos se pueden actualizar manualmente o eventualmente consumir
desde una fuente externa.
"""

# ── COUNTER_DATA ────────────────────────────────────────────────────
# Para cada campeón: quiénes lo countean ("countered_by") y a quiénes
# countea ("counters"). Mínimo 30 campeones populares.
COUNTER_DATA: dict[str, dict[str, list[str]]] = {
    "Aatrox": {
        "counters": ["Irelia", "Riven", "Fiora"],
        "countered_by": ["Fiora", "Irelia", "Vayne"],
    },
    "Ahri": {
        "counters": ["Veigar", "Twisted Fate", "Lux"],
        "countered_by": ["Kassadin", "Fizz", "Zed"],
    },
    "Akali": {
        "counters": ["Kassadin", "Katarina", "Veigar"],
        "countered_by": ["Galio", "Malzahar", "Annie"],
    },
    "Amumu": {
        "counters": ["Master Yi", "Kha'Zix", "Kindred"],
        "countered_by": ["Morgana", "Olaf", "Shaco"],
    },
    "Aphelios": {
        "counters": ["Kog'Maw", "Sivir", "Varus"],
        "countered_by": ["Draven", "Lucian", "Tristana"],
    },
    "Ashe": {
        "counters": ["Kog'Maw", "Varus", "Sivir"],
        "countered_by": ["Draven", "Lucian", "Samira"],
    },
    "Blitzcrank": {
        "counters": ["Lux", "Sona", "Soraka"],
        "countered_by": ["Morgana", "Sivir", "Ezreal"],
    },
    "Brand": {
        "counters": ["Lux", "Xerath", "Ziggs"],
        "countered_by": ["Fizz", "Zed", "Yasuo"],
    },
    "Caitlyn": {
        "counters": ["Vayne", "Kog'Maw", "Sivir"],
        "countered_by": ["Draven", "Lucian", "Tristana"],
    },
    "Camille": {
        "counters": ["Jax", "Fiora", "Renekton"],
        "countered_by": ["Jax", "Darius", "Mordekaiser"],
    },
    "Darius": {
        "counters": ["Garen", "Nasus", "Mordekaiser"],
        "countered_by": ["Vayne", "Quinn", "Kayle"],
    },
    "Diana": {
        "counters": ["Lux", "Xerath", "Ahri"],
        "countered_by": ["Kassadin", "Galio", "Malzahar"],
    },
    "Draven": {
        "counters": ["Ashe", "Caitlyn", "Jinx"],
        "countered_by": ["Ezreal", "Sivir", "Vayne"],
    },
    "Ezreal": {
        "counters": ["Draven", "Lucian", "Vayne"],
        "countered_by": ["Sivir", "Kog'Maw", "Jinx"],
    },
    "Fiora": {
        "counters": ["Aatrox", "Darius", "Garen"],
        "countered_by": ["Malphite", "Teemo", "Quinn"],
    },
    "Fizz": {
        "counters": ["Ahri", "Lux", "Brand"],
        "countered_by": ["Galio", "Malzahar", "Lissandra"],
    },
    "Garen": {
        "counters": ["Nasus", "Kayle", "Teemo"],
        "countered_by": ["Darius", "Vayne", "Quinn"],
    },
    "Graves": {
        "counters": ["Evelynn", "Karthus", "Nidalee"],
        "countered_by": ["Rammus", "Amumu", "Sejuani"],
    },
    "Hecarim": {
        "counters": ["Evelynn", "Karthus", "Amumu"],
        "countered_by": ["Warwick", "Rammus", "Poppy"],
    },
    "Irelia": {
        "counters": ["Aatrox", "Riven", "Fiora"],
        "countered_by": ["Volibear", "Tryndamere", "Renekton"],
    },
    "Jax": {
        "counters": ["Camille", "Irelia", "Tryndamere"],
        "countered_by": ["Malphite", "Teemo", "Kennen"],
    },
    "Jinx": {
        "counters": ["Kog'Maw", "Sivir", "Varus"],
        "countered_by": ["Draven", "Lucian", "Tristana"],
    },
    "Kai'Sa": {
        "counters": ["Kog'Maw", "Varus", "Ashe"],
        "countered_by": ["Draven", "Caitlyn", "Miss Fortune"],
    },
    "Kassadin": {
        "counters": ["Ahri", "Akali", "Diana"],
        "countered_by": ["Talon", "Zed", "Lucian"],
    },
    "Katarina": {
        "counters": ["Veigar", "Lux", "Xerath"],
        "countered_by": ["Galio", "Kassadin", "Diana"],
    },
    "Kayn": {
        "counters": ["Kha'Zix", "Evelynn", "Nidalee"],
        "countered_by": ["Rammus", "Poppy", "Warwick"],
    },
    "Kha'Zix": {
        "counters": ["Evelynn", "Nidalee", "Kindred"],
        "countered_by": ["Rammus", "Lee Sin", "Elise"],
    },
    "Lee Sin": {
        "counters": ["Kha'Zix", "Evelynn", "Amumu"],
        "countered_by": ["Rammus", "Warwick", "Vi"],
    },
    "Leona": {
        "counters": ["Lulu", "Sona", "Soraka"],
        "countered_by": ["Morgana", "Janna", "Alistar"],
    },
    "Lucian": {
        "counters": ["Ashe", "Jinx", "Caitlyn"],
        "countered_by": ["Vayne", "Kog'Maw", "Sivir"],
    },
    "Lulu": {
        "counters": ["Blitzcrank", "Leona", "Nautilus"],
        "countered_by": ["Sona", "Soraka", "Nami"],
    },
    "Lux": {
        "counters": ["Xerath", "Ziggs", "Veigar"],
        "countered_by": ["Fizz", "Zed", "Yasuo"],
    },
    "Malphite": {
        "counters": ["Jax", "Fiora", "Irelia"],
        "countered_by": ["Darius", "Mordekaiser", "Sylas"],
    },
    "Miss Fortune": {
        "counters": ["Kog'Maw", "Varus", "Ashe"],
        "countered_by": ["Draven", "Lucian", "Samira"],
    },
    "Mordekaiser": {
        "counters": ["Garen", "Nasus", "Darius"],
        "countered_by": ["Vayne", "Fiora", "Tryndamere"],
    },
    "Morgana": {
        "counters": ["Blitzcrank", "Leona", "Thresh"],
        "countered_by": ["Lulu", "Soraka", "Sona"],
    },
    "Nasus": {
        "counters": ["Kayle", "Teemo", "Vladimir"],
        "countered_by": ["Darius", "Riven", "Renekton"],
    },
    "Nautilus": {
        "counters": ["Lulu", "Sona", "Soraka"],
        "countered_by": ["Morgana", "Alistar", "Braum"],
    },
    "Pyke": {
        "counters": ["Sona", "Soraka", "Lulu"],
        "countered_by": ["Morgana", "Alistar", "Leona"],
    },
    "Renekton": {
        "counters": ["Irelia", "Riven", "Nasus"],
        "countered_by": ["Vayne", "Quinn", "Kennen"],
    },
    "Riven": {
        "counters": ["Nasus", "Kayle", "Gangplank"],
        "countered_by": ["Renekton", "Volibear", "Poppy"],
    },
    "Samira": {
        "counters": ["Ashe", "Miss Fortune", "Jinx"],
        "countered_by": ["Ezreal", "Caitlyn", "Draven"],
    },
    "Sejuani": {
        "counters": ["Graves", "Nidalee", "Kindred"],
        "countered_by": ["Olaf", "Master Yi", "Lillia"],
    },
    "Senna": {
        "counters": ["Lulu", "Soraka", "Nami"],
        "countered_by": ["Blitzcrank", "Nautilus", "Leona"],
    },
    "Sylas": {
        "counters": ["Malphite", "Lissandra", "Galio"],
        "countered_by": ["Cassiopeia", "Anivia", "Zed"],
    },
    "Thresh": {
        "counters": ["Lulu", "Sona", "Soraka"],
        "countered_by": ["Morgana", "Alistar", "Braum"],
    },
    "Tristana": {
        "counters": ["Jinx", "Ashe", "Caitlyn"],
        "countered_by": ["Draven", "Vayne", "Ezreal"],
    },
    "Twisted Fate": {
        "counters": ["Xerath", "Ziggs", "Lux"],
        "countered_by": ["Fizz", "Zed", "Kassadin"],
    },
    "Varus": {
        "counters": ["Kog'Maw", "Sivir", "Ashe"],
        "countered_by": ["Draven", "Lucian", "Samira"],
    },
    "Vayne": {
        "counters": ["Darius", "Garen", "Malphite"],
        "countered_by": ["Draven", "Caitlyn", "Miss Fortune"],
    },
    "Veigar": {
        "counters": ["Xerath", "Lux", "Ziggs"],
        "countered_by": ["Fizz", "Zed", "Kassadin"],
    },
    "Vi": {
        "counters": ["Evelynn", "Karthus", "Amumu"],
        "countered_by": ["Olaf", "Lee Sin", "Morgana"],
    },
    "Yasuo": {
        "counters": ["Lux", "Brand", "Ahri"],
        "countered_by": ["Renekton", "Malphite", "Rammus"],
    },
    "Yone": {
        "counters": ["Lux", "Ahri", "Xerath"],
        "countered_by": ["Renekton", "Malphite", "Pantheon"],
    },
    "Zed": {
        "counters": ["Ahri", "Lux", "Twisted Fate"],
        "countered_by": ["Malzahar", "Lissandra", "Galio"],
    },
    "Zeri": {
        "counters": ["Kog'Maw", "Varus", "Ashe"],
        "countered_by": ["Draven", "Lucian", "Caitlyn"],
    },
}


# ── SYNERGY_DATA ────────────────────────────────────────────────────
# Pares / grupos de campeones que tienen sinergia notable.
# Cada clave mapea a una lista de campeones con los que tiene sinergia
# y una breve razón.
SYNERGY_DATA: dict[str, list[dict[str, str]]] = {
    "Yasuo": [
        {"champion": "Malphite", "reason": "Knock-up para Last Breath"},
        {"champion": "Diana", "reason": "Knock-up grupal con ult"},
        {"champion": "Gragas", "reason": "Knock-up con Body Slam / ult"},
        {"champion": "Yone", "reason": "Knock-ups compartidos y sinergia de hermanos"},
        {"champion": "Alistar", "reason": "Knock-ups constantes del soporte"},
    ],
    "Yone": [
        {"champion": "Malphite", "reason": "Engage doble con ults"},
        {"champion": "Yasuo", "reason": "Sinergia de hermanos del viento"},
        {"champion": "Leona", "reason": "CC encadenado para all-in"},
    ],
    "Jinx": [
        {"champion": "Thresh", "reason": "Lantern + Chompers para picks"},
        {"champion": "Lulu", "reason": "Peel y buffs para hypercarry"},
        {"champion": "Nautilus", "reason": "CC pesado para proteger/iniciar"},
    ],
    "Kog'Maw": [
        {"champion": "Lulu", "reason": "Combo clásico de protect-the-carry"},
        {"champion": "Braum", "reason": "Peel tanky para hypercarry"},
        {"champion": "Janna", "reason": "Shields y peel para escalar"},
    ],
    "Miss Fortune": [
        {"champion": "Amumu", "reason": "AoE combo devastador con ults"},
        {"champion": "Leona", "reason": "Lockdown para Bullet Time"},
        {"champion": "Nautilus", "reason": "CC para garantizar ult completa"},
    ],
    "Samira": [
        {"champion": "Nautilus", "reason": "CC constante para stacks de pasiva"},
        {"champion": "Leona", "reason": "All-in agresivo con CC chain"},
        {"champion": "Alistar", "reason": "Knock-ups y engage para Samira"},
    ],
    "Vayne": [
        {"champion": "Lulu", "reason": "Peel y buffs para late game carry"},
        {"champion": "Janna", "reason": "Protección y disengage"},
        {"champion": "Nami", "reason": "Sustain y buffs de movimiento"},
    ],
    "Kai'Sa": [
        {"champion": "Nautilus", "reason": "CC para seguir con ult"},
        {"champion": "Leona", "reason": "Hard engage para follow up"},
        {"champion": "Thresh", "reason": "Versatilidad en engage y peel"},
    ],
    "Lucian": [
        {"champion": "Nami", "reason": "Electrocute procs con E de Nami"},
        {"champion": "Braum", "reason": "Pasiva proc rápida con doble auto"},
        {"champion": "Thresh", "reason": "Agresión en lane con lantern"},
    ],
    "Malphite": [
        {"champion": "Yasuo", "reason": "Combo clásico de knock-up + ult"},
        {"champion": "Orianna", "reason": "Ball delivery con ult"},
        {"champion": "Miss Fortune", "reason": "AoE combo con ults"},
    ],
    "Orianna": [
        {"champion": "Malphite", "reason": "Ball delivery para Shockwave"},
        {"champion": "Hecarim", "reason": "Ball delivery con carga"},
        {"champion": "Jarvan IV", "reason": "Atrapados en Cataclysm + Shockwave"},
    ],
    "Rengar": [
        {"champion": "Ivern", "reason": "Bushes para pasiva de Rengar"},
        {"champion": "Orianna", "reason": "Ball en Rengar invisible"},
    ],
    "Twitch": [
        {"champion": "Lulu", "reason": "Buffs + ult para teamfights"},
        {"champion": "Rakan", "reason": "Engage mientras Twitch flanquea"},
    ],
    "Jarvan IV": [
        {"champion": "Orianna", "reason": "Ball delivery con flag+drag/ult"},
        {"champion": "Miss Fortune", "reason": "Cataclysm + Bullet Time"},
        {"champion": "Brand", "reason": "AoE encerrado en Cataclysm"},
    ],
}


# ── CHAMPION_TAGS ───────────────────────────────────────────────────
# Tags por campeón: roles, tipo de daño y clase.
# Al menos 50 campeones populares.
CHAMPION_TAGS: dict[str, dict[str, list[str] | str]] = {
    "Aatrox": {"roles": ["top"], "damage": "AD", "class": ["fighter", "bruiser"]},
    "Ahri": {"roles": ["mid"], "damage": "AP", "class": ["mage", "assassin"]},
    "Akali": {"roles": ["mid", "top"], "damage": "AP", "class": ["assassin"]},
    "Alistar": {"roles": ["sup"], "damage": "AP", "class": ["tank", "support"]},
    "Amumu": {"roles": ["jg", "sup"], "damage": "AP", "class": ["tank"]},
    "Annie": {"roles": ["mid", "sup"], "damage": "AP", "class": ["mage"]},
    "Aphelios": {"roles": ["adc"], "damage": "AD", "class": ["marksman"]},
    "Ashe": {"roles": ["adc", "sup"], "damage": "AD", "class": ["marksman"]},
    "Blitzcrank": {"roles": ["sup"], "damage": "AP", "class": ["tank", "support"]},
    "Brand": {"roles": ["sup", "mid"], "damage": "AP", "class": ["mage"]},
    "Braum": {"roles": ["sup"], "damage": "mixed", "class": ["tank", "support"]},
    "Caitlyn": {"roles": ["adc"], "damage": "AD", "class": ["marksman"]},
    "Camille": {"roles": ["top"], "damage": "mixed", "class": ["fighter", "bruiser"]},
    "Darius": {"roles": ["top"], "damage": "AD", "class": ["fighter", "bruiser"]},
    "Diana": {"roles": ["mid", "jg"], "damage": "AP", "class": ["assassin", "fighter"]},
    "Draven": {"roles": ["adc"], "damage": "AD", "class": ["marksman"]},
    "Ekko": {"roles": ["mid", "jg"], "damage": "AP", "class": ["assassin"]},
    "Evelynn": {"roles": ["jg"], "damage": "AP", "class": ["assassin"]},
    "Ezreal": {"roles": ["adc"], "damage": "mixed", "class": ["marksman"]},
    "Fiora": {"roles": ["top"], "damage": "AD", "class": ["fighter", "duelist"]},
    "Fizz": {"roles": ["mid"], "damage": "AP", "class": ["assassin"]},
    "Galio": {"roles": ["mid", "sup"], "damage": "AP", "class": ["tank", "mage"]},
    "Gangplank": {"roles": ["top", "mid"], "damage": "AD", "class": ["fighter"]},
    "Garen": {"roles": ["top"], "damage": "AD", "class": ["fighter", "tank"]},
    "Graves": {"roles": ["jg"], "damage": "AD", "class": ["marksman", "fighter"]},
    "Hecarim": {"roles": ["jg"], "damage": "AD", "class": ["fighter", "tank"]},
    "Irelia": {"roles": ["top", "mid"], "damage": "AD", "class": ["fighter", "bruiser"]},
    "Janna": {"roles": ["sup"], "damage": "AP", "class": ["support", "enchanter"]},
    "Jarvan IV": {"roles": ["jg", "top"], "damage": "AD", "class": ["fighter", "tank"]},
    "Jax": {"roles": ["top", "jg"], "damage": "mixed", "class": ["fighter", "bruiser"]},
    "Jinx": {"roles": ["adc"], "damage": "AD", "class": ["marksman"]},
    "Kai'Sa": {"roles": ["adc"], "damage": "mixed", "class": ["marksman", "assassin"]},
    "Kassadin": {"roles": ["mid"], "damage": "AP", "class": ["assassin", "mage"]},
    "Katarina": {"roles": ["mid"], "damage": "mixed", "class": ["assassin"]},
    "Kayle": {"roles": ["top"], "damage": "mixed", "class": ["fighter", "marksman"]},
    "Kayn": {"roles": ["jg"], "damage": "AD", "class": ["assassin", "fighter"]},
    "Kennen": {"roles": ["top"], "damage": "AP", "class": ["mage", "marksman"]},
    "Kha'Zix": {"roles": ["jg"], "damage": "AD", "class": ["assassin"]},
    "Kindred": {"roles": ["jg"], "damage": "AD", "class": ["marksman"]},
    "Lee Sin": {"roles": ["jg"], "damage": "AD", "class": ["fighter", "assassin"]},
    "Leona": {"roles": ["sup"], "damage": "AP", "class": ["tank", "support"]},
    "Lissandra": {"roles": ["mid"], "damage": "AP", "class": ["mage"]},
    "Lucian": {"roles": ["adc", "mid"], "damage": "AD", "class": ["marksman"]},
    "Lulu": {"roles": ["sup"], "damage": "AP", "class": ["support", "enchanter"]},
    "Lux": {"roles": ["mid", "sup"], "damage": "AP", "class": ["mage", "support"]},
    "Malphite": {"roles": ["top", "sup"], "damage": "mixed", "class": ["tank"]},
    "Malzahar": {"roles": ["mid"], "damage": "AP", "class": ["mage"]},
    "Master Yi": {"roles": ["jg"], "damage": "AD", "class": ["assassin", "fighter"]},
    "Miss Fortune": {"roles": ["adc"], "damage": "AD", "class": ["marksman"]},
    "Mordekaiser": {"roles": ["top"], "damage": "AP", "class": ["fighter", "mage"]},
    "Morgana": {"roles": ["sup", "mid"], "damage": "AP", "class": ["mage", "support"]},
    "Nami": {"roles": ["sup"], "damage": "AP", "class": ["support", "enchanter"]},
    "Nasus": {"roles": ["top"], "damage": "AD", "class": ["fighter", "tank"]},
    "Nautilus": {"roles": ["sup"], "damage": "AP", "class": ["tank", "support"]},
    "Orianna": {"roles": ["mid"], "damage": "AP", "class": ["mage"]},
    "Pantheon": {"roles": ["mid", "top", "sup"], "damage": "AD", "class": ["fighter", "assassin"]},
    "Poppy": {"roles": ["top", "jg"], "damage": "AD", "class": ["tank", "fighter"]},
    "Pyke": {"roles": ["sup"], "damage": "AD", "class": ["assassin", "support"]},
    "Quinn": {"roles": ["top"], "damage": "AD", "class": ["marksman", "assassin"]},
    "Rammus": {"roles": ["jg"], "damage": "AP", "class": ["tank"]},
    "Renekton": {"roles": ["top"], "damage": "AD", "class": ["fighter", "bruiser"]},
    "Rengar": {"roles": ["jg", "top"], "damage": "AD", "class": ["assassin", "fighter"]},
    "Riven": {"roles": ["top"], "damage": "AD", "class": ["fighter", "bruiser"]},
    "Samira": {"roles": ["adc"], "damage": "AD", "class": ["marksman", "assassin"]},
    "Sejuani": {"roles": ["jg"], "damage": "AP", "class": ["tank"]},
    "Senna": {"roles": ["sup", "adc"], "damage": "AD", "class": ["marksman", "support"]},
    "Seraphine": {"roles": ["sup", "mid"], "damage": "AP", "class": ["mage", "support"]},
    "Sett": {"roles": ["top", "sup"], "damage": "AD", "class": ["fighter", "tank"]},
    "Sivir": {"roles": ["adc"], "damage": "AD", "class": ["marksman"]},
    "Sona": {"roles": ["sup"], "damage": "AP", "class": ["support", "enchanter"]},
    "Soraka": {"roles": ["sup"], "damage": "AP", "class": ["support", "enchanter"]},
    "Sylas": {"roles": ["mid", "top"], "damage": "AP", "class": ["mage", "fighter"]},
    "Syndra": {"roles": ["mid"], "damage": "AP", "class": ["mage"]},
    "Talon": {"roles": ["mid", "jg"], "damage": "AD", "class": ["assassin"]},
    "Teemo": {"roles": ["top"], "damage": "AP", "class": ["marksman", "mage"]},
    "Thresh": {"roles": ["sup"], "damage": "mixed", "class": ["tank", "support"]},
    "Tristana": {"roles": ["adc", "mid"], "damage": "AD", "class": ["marksman"]},
    "Tryndamere": {"roles": ["top"], "damage": "AD", "class": ["fighter", "assassin"]},
    "Twisted Fate": {"roles": ["mid"], "damage": "AP", "class": ["mage"]},
    "Twitch": {"roles": ["adc"], "damage": "AD", "class": ["marksman", "assassin"]},
    "Varus": {"roles": ["adc"], "damage": "mixed", "class": ["marksman"]},
    "Vayne": {"roles": ["adc", "top"], "damage": "AD", "class": ["marksman", "assassin"]},
    "Veigar": {"roles": ["mid"], "damage": "AP", "class": ["mage"]},
    "Vi": {"roles": ["jg"], "damage": "AD", "class": ["fighter", "bruiser"]},
    "Viktor": {"roles": ["mid"], "damage": "AP", "class": ["mage"]},
    "Vladimir": {"roles": ["mid", "top"], "damage": "AP", "class": ["mage"]},
    "Volibear": {"roles": ["top", "jg"], "damage": "mixed", "class": ["fighter", "tank"]},
    "Warwick": {"roles": ["jg", "top"], "damage": "mixed", "class": ["fighter", "tank"]},
    "Xerath": {"roles": ["mid", "sup"], "damage": "AP", "class": ["mage"]},
    "Yasuo": {"roles": ["mid", "top"], "damage": "AD", "class": ["fighter", "assassin"]},
    "Yone": {"roles": ["mid", "top"], "damage": "mixed", "class": ["fighter", "assassin"]},
    "Zed": {"roles": ["mid"], "damage": "AD", "class": ["assassin"]},
    "Zeri": {"roles": ["adc"], "damage": "AD", "class": ["marksman"]},
    "Ziggs": {"roles": ["mid", "adc"], "damage": "AP", "class": ["mage"]},
    "Zyra": {"roles": ["sup"], "damage": "AP", "class": ["mage", "support"]},
}

# ID numérico a nombre de campeón (los más comunes, para mapear desde la API)
CHAMPION_ID_TO_NAME: dict[int, str] = {
    1: "Annie", 2: "Olaf", 3: "Galio", 4: "Twisted Fate", 5: "Xin Zhao",
    6: "Urgot", 7: "LeBlanc", 8: "Vladimir", 9: "Fiddlesticks", 10: "Kayle",
    11: "Master Yi", 12: "Alistar", 13: "Ryze", 14: "Sion", 15: "Sivir",
    16: "Soraka", 17: "Teemo", 18: "Tristana", 19: "Warwick", 20: "Nunu & Willump",
    21: "Miss Fortune", 22: "Ashe", 23: "Tryndamere", 24: "Jax", 25: "Morgana",
    26: "Zilean", 27: "Singed", 28: "Evelynn", 29: "Twitch", 30: "Karthus",
    31: "Cho'Gath", 32: "Amumu", 33: "Rammus", 34: "Anivia", 35: "Shaco",
    36: "Dr. Mundo", 37: "Sona", 38: "Kassadin", 39: "Irelia", 40: "Janna",
    41: "Gangplank", 42: "Corki", 43: "Karma", 44: "Taric", 45: "Veigar",
    48: "Trundle", 50: "Swain", 51: "Caitlyn", 53: "Blitzcrank", 54: "Malphite",
    55: "Katarina", 56: "Nocturne", 57: "Maokai", 58: "Renekton", 59: "Jarvan IV",
    60: "Elise", 61: "Orianna", 62: "Wukong", 63: "Brand", 64: "Lee Sin",
    67: "Vayne", 68: "Rumble", 69: "Cassiopeia", 72: "Skarner", 74: "Heimerdinger",
    75: "Nasus", 76: "Nidalee", 77: "Udyr", 78: "Poppy", 79: "Gragas",
    80: "Pantheon", 81: "Ezreal", 82: "Mordekaiser", 83: "Yorick", 84: "Akali",
    85: "Kennen", 86: "Garen", 89: "Leona", 90: "Malzahar", 91: "Talon",
    92: "Riven", 96: "Kog'Maw", 98: "Shen", 99: "Lux", 101: "Xerath",
    102: "Shyvana", 103: "Ahri", 104: "Graves", 105: "Fizz", 106: "Volibear",
    107: "Rengar", 110: "Varus", 111: "Nautilus", 112: "Viktor", 113: "Sejuani",
    114: "Fiora", 115: "Ziggs", 117: "Lulu", 119: "Draven", 120: "Hecarim",
    121: "Kha'Zix", 122: "Darius", 126: "Jayce", 127: "Lissandra", 131: "Diana",
    133: "Quinn", 134: "Syndra", 136: "Aurelion Sol", 141: "Kayn", 142: "Zoe",
    143: "Zyra", 145: "Kai'Sa", 147: "Seraphine", 150: "Gnar", 154: "Zac",
    157: "Yasuo", 161: "Vel'Koz", 163: "Taliyah", 164: "Camille",
    166: "Akshan", 200: "Bel'Veth", 201: "Braum", 202: "Jhin", 203: "Kindred",
    221: "Zeri", 222: "Jinx", 223: "Tahm Kench", 234: "Viego",
    235: "Senna", 236: "Lucian", 238: "Zed", 240: "Kled",
    245: "Ekko", 246: "Qiyana", 254: "Vi", 266: "Aatrox", 267: "Nami",
    268: "Azir", 350: "Yuumi", 360: "Samira", 412: "Thresh",
    420: "Illaoi", 421: "Rek'Sai", 427: "Ivern", 429: "Kalista",
    432: "Bard", 497: "Rakan", 498: "Xayah", 516: "Ornn",
    517: "Sylas", 518: "Neeko", 523: "Aphelios", 526: "Rell",
    555: "Pyke", 711: "Vex", 777: "Yone", 875: "Sett",
    876: "Lillia", 887: "Gwen", 888: "Renata Glasc", 895: "Nilah",
    897: "K'Sante", 901: "Smolder", 902: "Milio", 950: "Naafiri",
}
