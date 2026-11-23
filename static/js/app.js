/* ═══════════════════════════════════════════════════════
   LoL Draft Analyzer — app.js
   Vanilla JS, sin frameworks. UI en español.
   ═══════════════════════════════════════════════════════ */

/**
 * Mapeo de championId → nombre Data Dragon (para las imágenes).
 * Se carga del backend vía /api/champions si está disponible,
 * o se usa este fallback extenso con los campeones más populares.
 */
const CHAMPION_NAMES = {
  1: "Annie", 2: "OldeTrundle", 3: "Galio", 4: "TwistedFate", 5: "XinZhao",
  6: "Urgot", 7: "LeBlanc", 8: "Vladimir", 9: "Fiddlesticks", 10: "Kayle",
  11: "MasterYi", 12: "Alistar", 13: "Ryze", 14: "Sion", 15: "Sivir",
  16: "Soraka", 17: "Teemo", 18: "Tristana", 19: "Warwick", 20: "Nunu",
  21: "MissFortune", 22: "Ashe", 23: "Tryndamere", 24: "Jax", 25: "Morgana",
  26: "Zilean", 27: "Singed", 28: "Evelynn", 29: "Twitch", 30: "Karthus",
  31: "Chogath", 32: "Amumu", 33: "Rammus", 34: "Anivia", 35: "Shaco",
  36: "DrMundo", 37: "Sona", 38: "Kassadin", 39: "Irelia", 40: "Janna",
  41: "Gangplank", 42: "Corki", 43: "Karma", 44: "Taric", 45: "Veigar",
  48: "Trundle", 50: "Swain", 51: "Caitlyn", 53: "Blitzcrank", 54: "Malphite",
  55: "Katarina", 56: "Nocturne", 57: "Maokai", 58: "Renekton", 59: "JarvanIV",
  60: "Elise", 61: "Orianna", 62: "MonkeyKing", 63: "Brand", 64: "LeeSin",
  67: "Vayne", 68: "Rumble", 69: "Cassiopeia", 72: "Skarner", 74: "Heimerdinger",
  75: "Nasus", 76: "Nidalee", 77: "Udyr", 78: "Poppy", 79: "Gragas",
  80: "Pantheon", 81: "Ezreal", 82: "Mordekaiser", 83: "Yorick", 84: "Akali",
  85: "Kennen", 86: "Garen", 89: "Leona", 90: "Malzahar", 91: "Talon",
  92: "Riven", 96: "KogMaw", 98: "Shen", 99: "Lux", 101: "Xerath",
  102: "Shyvana", 103: "Ahri", 104: "Graves", 105: "Fizz", 106: "Volibear",
  107: "Rengar", 110: "Varus", 111: "Nautilus", 112: "Viktor", 113: "Sejuani",
  114: "Fiora", 115: "Ziggs", 117: "Lulu", 119: "Draven", 120: "Hecarim",
  121: "Khazix", 122: "Darius", 126: "Jayce", 127: "Lissandra", 131: "Diana",
  133: "Quinn", 134: "Syndra", 136: "AurelionSol", 141: "Kayn", 142: "Zoe",
  143: "Zyra", 145: "Kaisa", 147: "Seraphine", 150: "Gnar", 154: "Zac",
  157: "Yasuo", 161: "VelKoz", 163: "Taliyah", 164: "Camille", 166: "Akshan",
  200: "Belveth", 201: "Braum", 202: "Jhin", 203: "Kindred", 221: "Zeri",
  222: "Jinx", 223: "TahmKench", 233: "Briar", 234: "Viego",
  235: "Senna", 236: "Lucian", 238: "Zed", 240: "Kled", 245: "Ekko",
  246: "Qiyana", 254: "Vi", 266: "Aatrox", 267: "Nami", 268: "Azir",
  350: "Yuumi", 360: "Samira", 412: "Thresh", 420: "Illaoi", 421: "RekSai",
  427: "Ivern", 429: "Kalista", 432: "Bard", 497: "Rakan", 498: "Xayah",
  516: "Ornn", 517: "Sylas", 518: "Neeko", 523: "Aphelios", 526: "Rell",
  555: "Pyke", 711: "Vex", 777: "Yone", 875: "Sett", 876: "Lillia",
  887: "Gwen", 888: "Renata", 895: "Nilah", 897: "KSante", 901: "Smolder",
  902: "Milio", 910: "Hwei", 950: "Naafiri", 902: "Milio"
};

/* ── Nombre limpio para display ── */
function displayName(ddName) {
  if (!ddName) return '?';
  const map = {
    MonkeyKing: 'Wukong', MissFortune: 'Miss Fortune', TwistedFate: 'Twisted Fate',
    JarvanIV: 'Jarvan IV', MasterYi: 'Master Yi', DrMundo: 'Dr. Mundo',
    LeeSin: 'Lee Sin', KogMaw: "Kog'Maw", AurelionSol: 'Aurelion Sol',
    TahmKench: 'Tahm Kench', RekSai: "Rek'Sai", KSante: "K'Sante",
    Chogath: "Cho'Gath", Khazix: "Kha'Zix", VelKoz: "Vel'Koz",
    Fiddlesticks: 'Fiddlesticks', XinZhao: 'Xin Zhao', Heimerdinger: 'Heimerdinger',
    Renata: 'Renata Glasc'
  };
  return map[ddName] || ddName.replace(/([a-z])([A-Z])/g, '$1 $2');
}

/* ── Normalización a ID oficial de Data Dragon (evita 404 -> Aatrox) ── */
function normalizeChampionId(rawName) {
  if (!rawName) return 'Aatrox';
  const cleaned = String(rawName).trim();
  const key = cleaned.toLowerCase().replace(/[^a-z0-9]/g, '');
  const special = {
    wukong: 'MonkeyKing',
    monkeyking: 'MonkeyKing',
    jarvaniv: 'JarvanIV',
    leesin: 'LeeSin',
    masteryi: 'MasterYi',
    missfortune: 'MissFortune',
    twistedfate: 'TwistedFate',
    aurelionsol: 'AurelionSol',
    tahmkench: 'TahmKench',
    xinzhao: 'XinZhao',
    drmundo: 'DrMundo',
    chogath: 'Chogath',
    khazix: 'Khazix',
    kogmaw: 'KogMaw',
    reksai: 'RekSai',
    velkoz: 'Velkoz',
    belveth: 'Belveth',
    kaisa: 'Kaisa',
    ksante: 'KSante',
    leblanc: 'Leblanc',
    nunu: 'Nunu',
    nunuwillump: 'Nunu',
    renata: 'Renata',
    renataglasc: 'Renata',
    fiddlesticks: 'Fiddlesticks',
  };
  if (special[key]) return special[key];
  // Quitar espacios, puntos y apóstrofes (ej: "Lee Sin" -> "LeeSin")
  return cleaned.replace(/[\s'.&-]+/g, '');
}

/* ── Data Dragon URL ── */
function champImgUrl(championName) {
  const name = normalizeChampionId(championName);
  return `https://ddragon.leagueoflegends.com/cdn/16.23.1/img/champion/${name}.png`;
}

function champSplashUrl(championName) {
  const name = normalizeChampionId(championName);
  return `https://ddragon.leagueoflegends.com/cdn/img/champion/splash/${name}_0.jpg`;
}

function spellImgUrl(spellLabel, ddKey = '') {
  if (ddKey && ddKey.startsWith('Summoner')) {
    return `https://ddragon.leagueoflegends.com/cdn/16.23.1/img/spell/${ddKey}.png`;
  }
  const s = (spellLabel || '').toLowerCase();
  let key = 'SummonerFlash';
  if (s.includes('summonerbarrier') || s.includes('barrera') || s.includes('barrier') || s.includes('barreira')) key = 'SummonerBarrier';
  else if (s.includes('summonerboost') || s.includes('limpiar') || s.includes('cleanse') || s.includes('purificar')) key = 'SummonerBoost';
  else if (s.includes('summonerexhaust') || s.includes('extenua') || s.includes('exhaust') || s.includes('exaust')) key = 'SummonerExhaust';
  else if (s.includes('summonerdot') || s.includes('prender') || s.includes('ignite') || s.includes('incendi')) key = 'SummonerDot';
  else if (s.includes('summonerteleport') || s.includes('teletransport') || s.includes('teleport') || s.includes('(tp)')) key = 'SummonerTeleport';
  else if (s.includes('summonerhaste') || s.includes('fantasmal') || s.includes('ghost')) key = 'SummonerHaste';
  else if (s.includes('summonersmite') || s.includes('aplastar') || s.includes('smite') || s.includes('golpear')) key = 'SummonerSmite';
  else if (s.includes('summonerheal') || s.includes('curaci') || s.includes('curar') || s.includes('heal')) key = 'SummonerHeal';
  else if (s.includes('summonersnowball') || s.includes('mark') || s.includes('marca')) key = 'SummonerSnowball';
  return `https://ddragon.leagueoflegends.com/cdn/16.23.1/img/spell/${key}.png`;
}

function keystoneImgUrl(keystone) {
  const base = 'https://ddragon.leagueoflegends.com/cdn/img/perk-images/Styles/';
  const map = {
    'Compás Letal': 'Precision/LethalTempo/LethalTempoTemp.png',
    'Lethal Tempo': 'Precision/LethalTempo/LethalTempoTemp.png',
    'Pies Veloces': 'Precision/FleetFootwork/FleetFootwork.png',
    'Fleet Footwork': 'Precision/FleetFootwork/FleetFootwork.png',
    'Ataque Intensificado': 'Precision/PressTheAttack/PressTheAttack.png',
    'Press the Attack': 'Precision/PressTheAttack/PressTheAttack.png',
    'Conquistador': 'Precision/Conqueror/Conqueror.png',
    'Conqueror': 'Precision/Conqueror/Conqueror.png',
    'Electrocutar': 'Domination/Electrocute/Electrocute.png',
    'Electrocute': 'Domination/Electrocute/Electrocute.png',
    'Cometa Arcano': 'Sorcery/ArcaneComet/ArcaneComet.png',
    'Arcane Comet': 'Sorcery/ArcaneComet/ArcaneComet.png',
    'Invocar a Aery': 'Sorcery/SummonAery/SummonAery.png',
    'Summon Aery': 'Sorcery/SummonAery/SummonAery.png',
    'Irrupción de Fase': 'Sorcery/PhaseRush/PhaseRush.png',
    'Phase Rush': 'Sorcery/PhaseRush/PhaseRush.png',
    'Primer Golpe': 'Inspiration/FirstStrike/FirstStrike.png',
    'First Strike': 'Inspiration/FirstStrike/FirstStrike.png',
    'Réplica': 'Resolve/VeteranAftershock/VeteranAftershock.png',
    'Aftershock': 'Resolve/VeteranAftershock/VeteranAftershock.png',
    'Agarre del Perpetuo': 'Resolve/GraspOfTheUndying/GraspOfTheUndying.png',
    'Grasp of the Undying': 'Resolve/GraspOfTheUndying/GraspOfTheUndying.png',
    'Guardián': 'Resolve/Guardian/Guardian.png',
    'Guardian': 'Resolve/Guardian/Guardian.png',
  };
  return base + (map[keystone] || 'Precision/PressTheAttack/PressTheAttack.png');
}

function runeTreeImgUrl(treeName) {
  const base = 'https://ddragon.leagueoflegends.com/cdn/img/perk-images/Styles/';
  const map = {
    'Precisión': '7201_Precision.png', 'Precision': '7201_Precision.png',
    'Dominación': '7200_Domination.png', 'Domination': '7200_Domination.png',
    'Brujería': '7202_Sorcery.png', 'Sorcery': '7202_Sorcery.png',
    'Valor': '7204_Resolve.png', 'Resolve': '7204_Resolve.png',
    'Inspiración': '7203_Whimsy.png', 'Inspiration': '7203_Whimsy.png',
  };
  return base + (map[treeName] || '7203_Whimsy.png');
}

/* ── Region → Platform mapping ── */
const REGION_PLATFORM_MAP = {
  LAS:  [{ value: 'la2',  label: 'LA2' }],
  LAN:  [{ value: 'la1',  label: 'LA1' }],
  NA:   [{ value: 'na1',  label: 'NA1' }],
  EUW:  [{ value: 'euw1', label: 'EUW1' }],
  EUNE: [{ value: 'eun1', label: 'EUN1' }],
  BR:   [{ value: 'br1',  label: 'BR1' }],
  KR:   [{ value: 'kr',   label: 'KR' }],
  JP:   [{ value: 'jp1',  label: 'JP1' }],
  OCE:  [{ value: 'oc1',  label: 'OC1' }],
  TR:   [{ value: 'tr1',  label: 'TR1' }],
  RU:   [{ value: 'ru',   label: 'RU' }],
};

const ROLE_LABELS = {
  TOP: 'TOP', JUNGLE: 'JG', MIDDLE: 'MID', BOTTOM: 'ADC', UTILITY: 'SUP'
};

/* ══════════════════════════════════════
   DraftAnalyzer — Clase principal
   ══════════════════════════════════════ */
class DraftAnalyzer {
  constructor() {
    this.state = {
      currentView: 'search',
      playerData: null,
      championList: [],       // from /api/champions
      draftState: {
        allyPicks: [null, null, null, null, null],
        enemyPicks: [null, null, null, null, null],
        bans: [],
        myRole: 'MIDDLE',
        recommendations: [],
      },
      activeSlot: null,       // { side, index }
    };

    this.cacheDOM();
    this.bindEvents();
    this.loadChampionList();
    this.renderSavedAccounts();
    this.startLCUPolling();
    this.initVoiceControls();
    this.startLiveGamePolling();
    this.initDesktopPinButton();
  }

  /* ── Cache DOM refs ── */
  cacheDOM() {
    // Nav
    this.navTabs = document.querySelectorAll('.nav-tab');
    this.views = document.querySelectorAll('.view');
    this.navAnalysis = document.getElementById('nav-analysis');
    this.navDraft = document.getElementById('nav-draft');

    // Search
    this.searchForm = document.getElementById('search-form');
    this.gameNameInput = document.getElementById('game-name');
    this.tagLineInput = document.getElementById('tag-line');
    this.regionSelect = document.getElementById('region-select');
    this.platformSelect = document.getElementById('platform-select');
    this.loadingOverlay = document.getElementById('loading-overlay');

    // Analysis
    this.playerSummaryEl = document.getElementById('player-summary');
    this.playerProfileIconEl = document.getElementById('player-profile-icon');
    this.playerNameEl = document.getElementById('player-name');
    this.playerLevelEl = document.getElementById('player-level');
    this.playerRankEl = document.getElementById('player-rank');
    this.globalWinrateEl = document.getElementById('global-winrate');
    this.totalGamesEl = document.getElementById('total-games');
    this.playStyleEl = document.getElementById('play-style');
    this.poolDepthEl = document.getElementById('pool-depth');
    this.championGrid = document.getElementById('champion-grid');
    this.roleTabs = document.getElementById('role-tabs');
    this.roleChampGrid = document.getElementById('role-champion-grid');

    // Draft
    this.draftRoleButtons = document.getElementById('draft-role-buttons');
    this.allyPicksEl = document.getElementById('ally-picks');
    this.enemyPicksEl = document.getElementById('enemy-picks');
    this.champSearchWrapper = document.getElementById('champion-search-wrapper');
    this.champSearchInput = document.getElementById('champion-search-input');
    this.champSearchResults = document.getElementById('champion-search-results');
    this.searchSlotLabel = document.getElementById('search-slot-label');
    this.btnCloseSearch = document.getElementById('btn-close-search');
    this.recsListEl = document.getElementById('recommendations-list');

    // Coach Panel
    this.coachBansEl = document.getElementById('coach-bans');
    this.coachPickOrderEl = document.getElementById('coach-pick-order');
    this.coachAlertsEl = document.getElementById('coach-alerts');
    this.coachChatTextEl = document.getElementById('coach-chat-text');
    this.btnCopyChat = document.getElementById('btn-copy-chat');
    this.gameplanStatusEl = document.getElementById('gameplan-status');
    this.gameplanContentEl = document.getElementById('gameplan-content');

    // Saved Accounts / Smurf Mode
    this.savedAccountsWrap = document.getElementById('saved-accounts-wrap');
    this.savedAccountsList = document.getElementById('saved-accounts-list');
    this.btnSwitchAccount = document.getElementById('btn-switch-account');
    this.btnHeaderSwitch = document.getElementById('btn-header-switch');
    this.activeProfileLabel = document.getElementById('active-profile-label');
    this.manualProfileLocked = false;

    // Toast
    this.toastContainer = document.getElementById('toast-container');

    // LCU Live Sync
    this.lcuPill = document.getElementById('lcu-status-pill');
    this.lcuText = document.getElementById('lcu-status-text');
    this.btnPinWindow = document.getElementById('btn-pin-window');
    this.lcuLastSummoner = null;
    this.lcuLastDraftKey = '';
  }

  /* ── Bind Events ── */
  bindEvents() {
    // Nav tabs
    this.navTabs.forEach(tab => {
      tab.addEventListener('click', () => {
        if (tab.disabled) return;
        this.switchView(tab.dataset.view);
      });
    });

    // Region → Platform auto-fill
    this.regionSelect.addEventListener('change', () => {
      const region = this.regionSelect.value;
      this.platformSelect.innerHTML = '';
      const platforms = REGION_PLATFORM_MAP[region] || [];
      platforms.forEach(p => {
        const opt = document.createElement('option');
        opt.value = p.value;
        opt.textContent = p.label;
        this.platformSelect.appendChild(opt);
      });
      if (platforms.length === 1) this.platformSelect.value = platforms[0].value;
    });

    // Search form (selección manual -> bloquea que una smurf en el LoL pise este perfil)
    this.searchForm.addEventListener('submit', e => {
      e.preventDefault();
      this.manualProfileLocked = true;
      this.analyzePlayer();
    });

    // Botones "Cambiar cuenta / Otra cuenta" (Header + Draft)
    [this.btnSwitchAccount, this.btnHeaderSwitch].filter(Boolean).forEach(btn => {
      btn.addEventListener('click', () => {
        this.switchView('search');
        this.gameNameInput.focus();
        this.gameNameInput.select();
        this.showToast('Ingresá otra cuenta (Main o Smurf). El LoL seguirá leyendo tu draft en vivo.', 'info');
      });
    });

    // Role tabs (analysis)
    this.roleTabs.addEventListener('click', e => {
      const tab = e.target.closest('.role-tab');
      if (!tab) return;
      this.roleTabs.querySelectorAll('.role-tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      this.renderRoleChampions(tab.dataset.role);
    });

    // Draft role selector
    this.draftRoleButtons.addEventListener('click', e => {
      const btn = e.target.closest('.role-btn');
      if (!btn) return;
      this.draftRoleButtons.querySelectorAll('.role-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      this.state.draftState.myRole = btn.dataset.role;
      this.updateDraft();
    });

    // Pick slots click
    [this.allyPicksEl, this.enemyPicksEl].forEach(container => {
      container.addEventListener('click', e => {
        const slot = e.target.closest('.pick-slot');
        if (!slot) return;
        const side = slot.dataset.side;
        const idx = parseInt(slot.dataset.index);

        // If filled → remove
        if (slot.classList.contains('filled')) {
          if (side === 'ally') this.state.draftState.allyPicks[idx] = null;
          else this.state.draftState.enemyPicks[idx] = null;
          this.renderDraftBoard();
          this.updateDraft();
          return;
        }

        // Open champion search
        this.state.activeSlot = { side, index: idx };
        const isEnSlot = typeof getCurrentLang === 'function' && getCurrentLang() !== 'es';
        const label = side === 'ally' ? (isEnSlot ? 'Ally' : 'Aliado') : (isEnSlot ? 'Enemy' : 'Enemigo');
        this.searchSlotLabel.textContent = `${isEnSlot ? 'Select champion' : 'Seleccionar campeón'} — ${label} #${idx + 1}`;
        this.champSearchInput.value = '';
        this.renderChampionSearch('');
        this.champSearchWrapper.style.display = 'flex';
        this.champSearchInput.focus();
      });
    });

    // Champion search input
    this.champSearchInput.addEventListener('input', () => {
      this.renderChampionSearch(this.champSearchInput.value);
    });

    // Close search
    this.btnCloseSearch.addEventListener('click', () => {
      this.champSearchWrapper.style.display = 'none';
      this.state.activeSlot = null;
    });

    // Copiar mensaje sugerido del Coach al portapapeles
    if (this.btnCopyChat) {
      this.btnCopyChat.addEventListener('click', async () => {
        const msg = this.coachChatTextEl ? this.coachChatTextEl.textContent.trim() : '';
        if (!msg) return;
        const isEnCopy = typeof getCurrentLang === 'function' && getCurrentLang() !== 'es';
        try {
          await navigator.clipboard.writeText(msg);
          this.showToast(isEnCopy ? 'Copied! Paste it into Champ Select chat.' : '¡Mensaje copiado! Pegalo en el chat de Champ Select.', 'success');
        } catch {
          this.showToast(isEnCopy ? 'Could not copy automatically.' : 'No se pudo copiar automáticamente.', 'error');
        }
      });
    }

    // Champion search result click
    this.champSearchResults.addEventListener('click', e => {
      const item = e.target.closest('.search-champ-item');
      if (!item || item.classList.contains('disabled')) return;
      const champName = item.dataset.champ;
      const champId = parseInt(item.dataset.id);
      const { side, index } = this.state.activeSlot;
      const pickData = { id: champId, name: champName };

      if (side === 'ally') this.state.draftState.allyPicks[index] = pickData;
      else this.state.draftState.enemyPicks[index] = pickData;

      this.champSearchWrapper.style.display = 'none';
      this.state.activeSlot = null;
      this.renderDraftBoard();
      this.updateDraft();
    });
  }

  /* ── Toast notifications ── */
  showToast(message, type = 'info') {
    const icons = { error: 'fa-circle-exclamation', success: 'fa-circle-check', info: 'fa-circle-info' };
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `<i class="fa-solid ${icons[type] || icons.info}"></i> ${message}`;
    this.toastContainer.appendChild(toast);
    setTimeout(() => toast.remove(), 4200);
  }

  /* ── Load champion list from backend ── */
  async loadChampionList() {
    try {
      const res = await fetch('/api/champions');
      if (res.ok) {
        const data = await res.json();
        if (data.champions) {
          this.state.championList = data.champions;
        }
      }
    } catch {
      // Fallback: build from local map
      this.state.championList = Object.entries(CHAMPION_NAMES).map(([id, name]) => ({
        id: parseInt(id),
        name,
      }));
    }
    // If still empty, use local map
    if (this.state.championList.length === 0) {
      this.state.championList = Object.entries(CHAMPION_NAMES).map(([id, name]) => ({
        id: parseInt(id),
        name,
      }));
    }
  }

  /* ══════════════════════════════════════
     Navigation
     ══════════════════════════════════════ */
  switchView(view) {
    this.state.currentView = view;
    this.navTabs.forEach(t => t.classList.toggle('active', t.dataset.view === view));
    this.views.forEach(v => v.classList.toggle('active', v.id === `view-${view}`));
    if (view === 'draft' && this.state.playerData) {
      this.updateDraft();
    }
  }

  /* ══════════════════════════════════════
     Analyze Player
     ══════════════════════════════════════ */
  async analyzePlayer() {
    const gameName = this.gameNameInput.value.trim();
    const tagLine = this.tagLineInput.value.trim();
    const region = this.regionSelect.value;
    const platform = this.platformSelect.value;

    const isEnAn = typeof getCurrentLang === 'function' && getCurrentLang() !== 'es';
    if (!gameName || !tagLine || !region || !platform) {
      this.showToast(isEnAn ? 'Please fill in all fields before analyzing.' : 'Completá todos los campos antes de analizar.', 'error');
      return;
    }

    this.loadingOverlay.classList.remove('hidden');

    try {
      const res = await fetch('/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          game_name: gameName,
          tag_line: tagLine,
          region,
          platform,
          lang: typeof getCurrentLang === 'function' ? getCurrentLang() : 'es',
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || (isEnAn ? `Error ${res.status}: Could not analyze player.` : `Error ${res.status}: No se pudo analizar al jugador.`));
      }

      const data = await res.json();
      this.state.playerData = data;
      this.saveAccount({ gameName, tagLine, region, platform });
      if (this.activeProfileLabel) {
        this.activeProfileLabel.textContent = `${gameName}#${tagLine} · ${isEnAn ? 'Switch' : 'Cambiar'}`;
      }

      // Enable nav tabs
      this.navAnalysis.disabled = false;
      this.navDraft.disabled = false;

      // Render analysis view
      this.renderPlayerSummary(data);
      this.renderChampionPool(data);

      // Seleccionar automáticamente el rol más jugado por el jugador
      const mainRoleKey = this._detectMainRole(data);
      const roleToBtn = { TOP: 'TOP', JG: 'JUNGLE', MID: 'MIDDLE', ADC: 'BOTTOM', SUP: 'UTILITY' };
      const btnRole = roleToBtn[mainRoleKey] || 'TOP';

      this.roleTabs.querySelectorAll('.role-tab').forEach(t => {
        t.classList.toggle('active', t.dataset.role === btnRole);
      });
      this.renderRoleChampions(btnRole);

      this.state.draftState.myRole = btnRole;
      this.draftRoleButtons.querySelectorAll('.role-btn').forEach(b => {
        b.classList.toggle('active', b.dataset.role === btnRole);
      });

      // Switch to analysis
      this.switchView('analysis');
      window.uiSfx?.playSuccess();
      this.showToast(isEnAn ? 'Analysis complete!' : '¡Análisis completado!', 'success');
    } catch (err) {
      this.showToast(err.message, 'error');
    } finally {
      this.loadingOverlay.classList.add('hidden');
    }
  }

  /* ══════════════════════════════════════
     Render: Player Summary
     ══════════════════════════════════════ */
  renderPlayerSummary(data) {
    const player = data.player || {};
    const analysis = data.analysis || data;
    const summary = analysis.player_summary || {};
    const champStats = analysis.champion_stats || {};

    const fullName = player.game_name
      ? `${player.game_name}#${player.tag_line || ''}`
      : (data.summoner_name || summary.name || '—');
    this.playerNameEl.textContent = fullName;

    // Ícono real del invocador (Data Dragon)
    if (this.playerProfileIconEl && player.profile_icon_id) {
      this.playerProfileIconEl.src = `https://ddragon.leagueoflegends.com/cdn/16.23.1/img/profileicon/${player.profile_icon_id}.png`;
    }

    // Splash Art de fondo del mejor campeón del jugador (estilo Cliente de LoL)
    const bestChamps = analysis.best_champions || [];
    if (this.playerSummaryEl && bestChamps.length > 0) {
      const topChamp = bestChamps[0].champion || bestChamps[0].champion_name;
      if (topChamp) {
        this.playerSummaryEl.style.backgroundImage = `url('https://ddragon.leagueoflegends.com/cdn/img/champion/splash/${topChamp}_0.jpg')`;
      }
    }

    const level = player.summoner_level || data.summoner_level || summary.level || '—';
    const lvlWord = typeof t === 'function' ? t('lvl_prefix') : 'Nivel';
    this.playerLevelEl.innerHTML = `<i class="fa-solid fa-star"></i> ${lvlWord} ${level}`;

    const tier = summary.tier || summary.rank || data.rank || 'Sin clasificar';
    const lpText = summary.lp ? ` · ${summary.lp} LP` : '';
    this.playerRankEl.innerHTML = `<i class="fa-solid fa-trophy"></i> ${tier}${lpText}`;

    // Global win rate
    let totalWins = 0, totalGames = 0;
    Object.values(champStats).forEach(c => {
      totalWins += (c.wins || 0);
      totalGames += (c.games || 0);
    });
    const globalWr = totalGames > 0 ? ((totalWins / totalGames) * 100).toFixed(1) : '—';
    this.globalWinrateEl.textContent = globalWr !== '—' ? `${globalWr}%` : '—%';
    const totalAnalyzed = summary.total_games_analyzed || totalGames || 0;
    this.totalGamesEl.textContent = totalAnalyzed || '—';
    const coachBadge = document.querySelector('.coach-badge');
    if (coachBadge && totalAnalyzed > 0) {
      const pre = typeof t === 'function' ? t('coach_badge_prefix') : 'Últimas';
      const suf = typeof t === 'function' ? t('coach_badge_suffix') : 'partidas + Maestría';
      coachBadge.textContent = `${pre} ${totalAnalyzed} ${suf}`;
    }

    // Rol principal con porcentaje de partidas en ese rol
    const roleAnalysis = analysis.role_analysis || {};
    let mainRoleName = '—';
    let mainRoleGames = 0;
    let allRoleGames = 0;
    for (const [rKey, rChamps] of Object.entries(roleAnalysis)) {
      if (!Array.isArray(rChamps)) continue;
      const g = rChamps.reduce((acc, c) => acc + (c.games || 0), 0);
      allRoleGames += g;
      if (g > mainRoleGames) {
        mainRoleGames = g;
        mainRoleName = rKey;
      }
    }
    const rolePct = allRoleGames > 0 ? Math.round((mainRoleGames / allRoleGames) * 100) : 0;
    this.playStyleEl.textContent = mainRoleName !== '—' ? `${mainRoleName} (${rolePct}%)` : '—';

    const depth = summary.pool_depth || summary.champion_pool_depth || '—';
    this.poolDepthEl.textContent = depth;

    // Render Pulso de Sesión (Anti-Tilt) + Errores recientes
    this.renderPlayerVibeAndTrophies(data, globalWr, totalAnalyzed);
    this.renderGpiAndPoroTags(data, globalWr, totalAnalyzed);

    const mc = analysis.mental_check;
    const mentalSection = document.getElementById('mental-section');
    if (mc && mentalSection) {
      mentalSection.style.display = 'grid';
      const card = document.getElementById('mental-card');
      if (card) card.className = `mental-card status-${mc.status || 'ok'}`;
      const titleEl = document.getElementById('mental-title');
      if (titleEl) titleEl.textContent = mc.title || '';
      const streakEl = document.getElementById('mental-streak');
      if (streakEl) streakEl.textContent = mc.streak_label || '';
      const msgEl = document.getElementById('mental-message');
      if (msgEl) msgEl.textContent = mc.message || '';

      const mistakesEl = document.getElementById('mistakes-list');
      if (mistakesEl) {
        const list = mc.mistakes || [];
        mistakesEl.innerHTML = list.map(m => `
          <div class="mistake-item">
            <strong>${m.icon || '•'} ${m.title}</strong>
            ${m.detail}
          </div>
        `).join('');
      }
    }

    // Render Némesis, Víctima Favorita, Mejor Aliado y Fun Facts
    this.renderFunFacts(analysis.fun_facts);
  }

  renderFunFacts(ff) {
    const sec = document.getElementById('fun-facts-section');
    const triadEl = document.getElementById('matchup-triad');
    const recEl = document.getElementById('fun-records-grid');
    if (!sec || !triadEl || !recEl || !ff) return;

    const isEn = typeof getCurrentLang === 'function' && getCurrentLang() !== 'es';
    const wChar = isEn ? 'W' : 'V';
    const lChar = isEn ? 'L' : 'D';

    const items = [];
    if (ff.nemesis) {
      items.push({ cls: 'nemesis', tag: isEn ? '😈 Your Nemesis' : '😈 Tu Némesis', data: ff.nemesis });
    }
    if (ff.victim) {
      items.push({ cls: 'victim', tag: isEn ? '🎯 Free LP (Best Matchup)' : '🎯 Tu Víctima Favorita', data: ff.victim });
    }
    if (ff.best_ally) {
      items.push({ cls: 'ally', tag: isEn ? '🤝 Best Ally to Play With' : '🤝 Mejor Aliado', data: ff.best_ally });
    }

    triadEl.innerHTML = items.map(it => `
      <div class="triad-card ${it.cls}">
        <img src="${champImgUrl(it.data.champion)}" alt="${displayName(it.data.champion)}" onerror="this.src='${champImgUrl('Aatrox')}'">
        <div>
          <div class="triad-tag">${it.tag}</div>
          <div class="triad-name">${displayName(it.data.champion)}</div>
          <div class="triad-stat">${it.data.win_rate}% WR (${it.data.wins}${wChar} - ${it.data.losses}${lChar})</div>
        </div>
      </div>
    `).join('');

    recEl.innerHTML = (ff.records || []).map(r => `
      <div class="fun-record-card">
        <div class="fun-record-icon">${r.icon}</div>
        <div class="fun-record-val">${r.value}</div>
        <div class="fun-record-lbl">${r.label}</div>
        <div class="fun-record-sub">${r.sub}</div>
      </div>
    `).join('');

    sec.style.display = 'block';
  }

  /* ══════════════════════════════════════
     Render: Champion Pool Grid
     ══════════════════════════════════════ */
  renderChampionPool(data) {
    const analysis = data.analysis || data;
    const best = analysis.best_champions || [];
    const champStats = analysis.champion_stats || {};
    this.championGrid.innerHTML = '';

    if (best.length === 0) {
      this.championGrid.innerHTML = '<p class="no-data-msg">No se encontraron campeones en el historial reciente.</p>';
      return;
    }

    best.forEach(entry => {
      const name = entry.champion || entry.champion_name;
      const fullStats = champStats[name] || {};
      const merged = { ...fullStats, ...entry, champion_name: name };
      const card = this._buildChampCard(merged);
      this.championGrid.appendChild(card);
    });
  }

  /* Build a single champion card */
  _buildChampCard(champ) {
    const champName = champ.champion_name || champ.champion || CHAMPION_NAMES[champ.champion_id] || 'Unknown';
    const rawWr = champ.win_rate != null ? Number(champ.win_rate) : 0;
    // Backend devuelve 0-100; si viniera 0-1 lo normalizamos
    const wrPctNum = rawWr > 1 ? rawWr : rawWr * 100;
    const wrPct = Math.min(100, Math.max(0, wrPctNum)).toFixed(1);
    const wrClass = wrPctNum > 55 ? 'green' : wrPctNum >= 45 ? 'yellow' : 'red';
    const kda = champ.avg_kda != null ? Number(champ.avg_kda).toFixed(2) : '—';
    const games = champ.games || 0;
    const csMin = champ.avg_cs_per_min != null ? Number(champ.avg_cs_per_min).toFixed(1) : '—';

    const rawComfort = champ.score != null ? Number(champ.score) : (champ.comfort_score != null ? Number(champ.comfort_score) : 0);
    const comfortNorm = rawComfort > 1 ? rawComfort / 100 : rawComfort;

    // roles_played puede venir como array o como dict {ADC: 10}
    let roles = [];
    if (Array.isArray(champ.roles_played)) {
      roles = champ.roles_played;
    } else if (champ.roles_played && typeof champ.roles_played === 'object') {
      roles = Object.keys(champ.roles_played);
    }

    const card = document.createElement('div');
    card.className = 'champion-card';

    const _t = (k, fb) => (typeof t === 'function' ? t(k) : fb);
    let trustLabel = _t('trust_low', '📊 Muestra chica');
    let trustClass = 'trust-low';
    if (games >= 8 && wrPctNum >= 55) {
      trustLabel = _t('trust_high', '🔥 Pick Seguro');
      trustClass = 'trust-high';
    } else if (games >= 4 && wrPctNum >= 50) {
      trustLabel = _t('trust_mid', '✅ Sólido');
      trustClass = 'trust-mid';
    } else if (games >= 5 && wrPctNum < 45) {
      trustLabel = _t('trust_warn', '⚠️ Bajo WR');
      trustClass = 'trust-warn';
    }
    const masteryPts = champ.mastery_points || 0;
    const masteryBadge = masteryPts >= 10000
      ? `<span class="champ-pill mastery">${Math.round(masteryPts / 1000)}k pts</span>`
      : '';

    const lastWord = _t('last_n', 'Últimas');
    const wChar = _t('w_short', 'V');
    const lChar = _t('l_short', 'D');
    let formHtml = '';
    if (Array.isArray(champ.recent_form) && champ.recent_form.length > 0) {
      const sample = champ.recent_form.slice(0, 5);
      const winsRecent = sample.filter(r => r === true || r === 'W' || r === 1).length;
      const lossesRecent = sample.length - winsRecent;
      const badgeClass = winsRecent >= lossesRecent ? 'win' : 'loss';
      formHtml = `<span class="champ-pill ${badgeClass}">${lastWord} ${sample.length}: ${winsRecent}${wChar} - ${lossesRecent}${lChar}</span>`;
    } else if (champ.recent_form != null && games > 0) {
      const n = Math.min(games, 5);
      const winsRecent = Math.round((Number(champ.recent_form) / 100) * n);
      const lossesRecent = Math.max(0, n - winsRecent);
      const badgeClass = winsRecent >= lossesRecent ? 'win' : 'loss';
      formHtml = `<span class="champ-pill ${badgeClass}">${lastWord} ${n}: ${winsRecent}${wChar} - ${lossesRecent}${lChar}</span>`;
    }

    // Roles labels
    const rolesStr = roles.map(r => ROLE_LABELS[r] || r).join(', ') || '—';
    const gamesWord = _t('games_word', 'partidas');

    card.innerHTML = `
      <div class="champ-icon-wrap">
        <img src="${champImgUrl(champName)}" alt="${displayName(champName)}"
             onerror="this.src='${champImgUrl('Aatrox')}'">
      </div>
      <div class="champ-info">
        <div class="champ-name">${displayName(champName)}</div>
        <div class="champ-roles">${rolesStr}</div>
        <div class="wr-bar-wrap">
          <div class="wr-bar"><div class="wr-bar-fill ${wrClass}" style="width:${wrPct}%"></div></div>
          <span class="wr-value ${wrClass}">${wrPct}%</span>
        </div>
        <div class="champ-stats-row">
          <span><i class="fa-solid fa-crosshairs"></i> KDA ${kda}</span>
          <span><i class="fa-solid fa-gamepad"></i> ${games} ${gamesWord}</span>
          <span><i class="fa-solid fa-wheat-awn"></i> ${csMin} CS/m</span>
        </div>
        <div class="champ-badges-row">
          <span class="champ-pill ${trustClass}">${trustLabel}</span>
          ${formHtml}
          ${masteryBadge}
        </div>
      </div>
    `;
    card.title = (typeof getCurrentLang === 'function' && getCurrentLang() !== 'es')
      ? 'Click for detailed champion breakdown'
      : 'Click para ver análisis detallado de este campeón';
    card.addEventListener('click', () => this.openChampionModal(champName));
    return card;
  }

  /* ── Refuerzo Positivo: Bienvenida, Racha Diaria y Trofeos de la Grieta ── */
  _getDailyStreak() {
    try {
      const today = new Date().toISOString().slice(0, 10);
      const lastDay = localStorage.getItem('NoFlash_last_day');
      let streak = parseInt(localStorage.getItem('NoFlash_daily_streak') || '0', 10);
      if (lastDay !== today) {
        const yest = new Date(Date.now() - 86400000).toISOString().slice(0, 10);
        streak = (lastDay === yest) ? streak + 1 : 1;
        localStorage.setItem('NoFlash_last_day', today);
        localStorage.setItem('NoFlash_daily_streak', String(streak));
      }
      return Math.max(1, streak);
    } catch {
      return 1;
    }
  }

  renderPlayerVibeAndTrophies(data, globalWr, totalAnalyzed) {
    const bar = document.getElementById('player-vibe-bar');
    const greetEl = document.getElementById('vibe-greeting');
    const streakEl = document.getElementById('daily-streak-pill');
    const trophiesEl = document.getElementById('trophies-row');
    if (!bar || !greetEl || !trophiesEl) return;

    const isEn = typeof getCurrentLang === 'function' ? getCurrentLang() !== 'es' : true;
    const player = data.player || {};
    const analysis = data.analysis || data;
    const champStats = analysis.champion_stats || {};
    const bestChamps = analysis.best_champions || [];
    const mc = analysis.mental_check || {};
    const name = player.game_name || 'Summoner';

    const dailyStreak = this._getDailyStreak();
    if (streakEl) {
      streakEl.textContent = isEn ? `🔥 Day ${dailyStreak} Streak` : `🔥 Racha Día ${dailyStreak}`;
    }

    const top = bestChamps[0];
    const topName = top ? displayName(top.champion || top.champion_name) : '';
    const topStats = top ? champStats[top.champion || top.champion_name] : null;
    const wrNum = parseFloat(globalWr);

    let msg = '';
    if (mc.status === 'hot' || (mc.win_streak || 0) >= 3) {
      msg = isEn
        ? `🔥 You're on fire, ${name}! Keep that momentum rolling — you're in peak carry form.`
        : `🔥 ¡Estás prendido fuego, ${name}! Aprovechá este momentum que venís imparable.`;
    } else if (mc.status === 'tilt' || mc.status === 'caution') {
      msg = isEn
        ? `Fresh lobby, clean mental, ${name}. Rough streaks happen to every high-elo player — you've got this.`
        : `Lobby nuevo, mente limpia, ${name}. Las rachas duras le pasan a todos — hoy se remonta.`;
    } else if (topName && topStats && topStats.games >= 5 && topStats.win_rate >= 52) {
      msg = isEn
        ? `Welcome back, ${name} — your ${topName} is sitting at ${topStats.win_rate}% WR over ${topStats.games} games. Let's climb.`
        : `¡Qué bueno verte, ${name}! Tu ${topName} está en ${topStats.win_rate}% WR en ${topStats.games} partidas. A subir LP.`;
    } else {
      msg = isEn
        ? `Welcome back, ${name} — ${totalAnalyzed || 0} games analyzed and ready. Let's make today's session clean.`
        : `¡Bienvenido de vuelta, ${name}! ${totalAnalyzed || 0} partidas listas. Vamos por una gran sesión hoy.`;
    }
    greetEl.textContent = msg;

    // Calcular Trofeos reales ganados por sus estadísticas
    const trophies = [];
    const allStats = Object.values(champStats);

    const otp = allStats.find(s => (s.games || 0) >= 35 && (s.win_rate || 0) >= 52);
    if (otp) trophies.push({ cls: 'gold', text: isEn ? '👑 One-Trick Legend' : '👑 Leyenda Main' });

    if (!Number.isNaN(wrNum) && wrNum >= 53 && totalAnalyzed >= 15) {
      trophies.push({ cls: 'cyan', text: isEn ? `⚡ Clutch Climber (${wrNum}% WR)` : `⚡ Escalador (${wrNum}% WR)` });
    }

    const bestCs = Math.max(0, ...allStats.filter(s => (s.games || 0) >= 5).map(s => Number(s.avg_cs_per_min || 0)));
    if (bestCs >= 7.0) {
      trophies.push({ cls: 'cyan', text: isEn ? `🎯 Farm Machine (${bestCs.toFixed(1)} CS/m)` : `🎯 Máquina de Farm (${bestCs.toFixed(1)} CS/m)` });
    }

    const bestDmg = Math.max(0, ...allStats.filter(s => (s.games || 0) >= 5).map(s => Number(s.avg_damage_share || 0)));
    if (bestDmg >= 24) {
      trophies.push({ cls: 'gold', text: isEn ? `💥 Team Carry (${Math.round(bestDmg)}% DMG)` : `💥 Carry de Daño (${Math.round(bestDmg)}% DMG)` });
    }

    const lowDeaths = allStats.some(s => (s.games || 0) >= 8 && Number(s.avg_deaths || 99) <= 4.3);
    if (lowDeaths) {
      trophies.push({ cls: 'green', text: isEn ? '🛡️ Unkillable Positioning' : '🛡️ Posicionamiento Sólido' });
    }

    const rdStreak = parseInt(localStorage.getItem('riftdle_streak') || '0', 10);
    const microBest = parseInt(localStorage.getItem('NoFlash_micro_best') || '0', 10);
    if (rdStreak >= 3 || microBest >= 18) {
      trophies.push({ cls: 'purple', text: isEn ? '🎮 Warm-Up Grinder' : '🎮 Grinder de Warm-Up' });
    }

    if (trophies.length === 0) {
      trophies.push({ cls: 'cyan', text: isEn ? '⚡ Ready to Climb' : '⚡ Listo para Subir' });
    }

    trophiesEl.innerHTML = trophies
      .slice(0, 5)
      .map(tr => `<span class="trophy-badge ${tr.cls}">${tr.text}</span>`)
      .join('');
    bar.style.display = 'flex';
  }

  /* ── Mobalytics-style 5-Pillar GPI Radar + Porofessor-style Player Tags ── */
  renderGpiAndPoroTags(data, globalWr, totalAnalyzed) {
    const sec = document.getElementById('gpi-poro-section');
    const radarWrap = document.getElementById('gpi-radar-wrap');
    const listWrap = document.getElementById('gpi-pillars-list');
    const gradeEl = document.getElementById('gpi-overall-grade');
    const tagsEl = document.getElementById('poro-tags-grid');
    if (!sec || !radarWrap || !listWrap || !tagsEl) return;

    const analysis = data.analysis || data;
    const champStats = Object.values(analysis.champion_stats || {});
    if (champStats.length === 0) {
      sec.style.display = 'none';
      return;
    }

    const isEn = typeof getCurrentLang === 'function' ? getCurrentLang() !== 'es' : true;
    const totalG = champStats.reduce((a, c) => a + (c.games || 0), 0) || 1;
    const wAvg = (fn) => champStats.reduce((a, c) => a + (fn(c) || 0) * (c.games || 0), 0) / totalG;

    const avgCs = wAvg(c => Number(c.avg_cs_per_min || 0));
    const avgDeaths = wAvg(c => Number(c.avg_deaths || 5.5));
    const avgKda = wAvg(c => Number(c.avg_kda || 2.5));
    const avgDmgShare = wAvg(c => Number(c.avg_damage_share || 20));
    const avgKp = wAvg(c => Number((c.deep_analysis?.metrics?.avg_kp) || 52));
    const avgTurrets = wAvg(c => Number((c.deep_analysis?.metrics?.avg_turrets) || 1.2));
    const wrNum = parseFloat(globalWr) || 50;

    const clamp = (v) => Math.max(22, Math.min(99, Math.round(v)));
    const pillars = [
      { key: isEn ? 'Fighting' : 'Peleas', val: clamp(40 + avgKda * 11 + (avgDmgShare - 18) * 1.4) },
      { key: isEn ? 'Farming' : 'Farmeo', val: clamp((avgCs / 8.5) * 95) },
      { key: isEn ? 'Survivability' : 'Supervivencia', val: clamp(102 - avgDeaths * 8.5) },
      { key: isEn ? 'Objectives' : 'Objetivos', val: clamp(42 + avgTurrets * 22 + (avgKp - 45) * 0.6) },
      { key: isEn ? 'Consistency' : 'Consistencia', val: clamp(45 + (wrNum - 45) * 3.2 + Math.min(12, totalAnalyzed / 15)) },
    ];

    const overall = Math.round(pillars.reduce((a, p) => a + p.val, 0) / pillars.length);
    const toGrade = (v) => v >= 90 ? 'S+' : v >= 82 ? 'S' : v >= 74 ? 'A+' : v >= 66 ? 'A' : v >= 56 ? 'B' : 'C';
    if (gradeEl) gradeEl.textContent = toGrade(overall);

    // Construir SVG Pentagon Radar ligero y nítido
    const cx = 110, cy = 105, maxR = 72;
    const ptsFor = (scaleArr) => scaleArr.map((v, i) => {
      const ang = -Math.PI / 2 + (i * 2 * Math.PI) / 5;
      const r = (v / 100) * maxR;
      return `${(cx + Math.cos(ang) * r).toFixed(1)},${(cy + Math.sin(ang) * r).toFixed(1)}`;
    }).join(' ');

    const gridRings = [25, 50, 75, 100].map(r =>
      `<polygon points="${ptsFor([r, r, r, r, r])}" fill="none" stroke="rgba(200,155,60,0.2)" stroke-width="1"/>`
    ).join('');
    const axes = pillars.map((p, i) => {
      const ang = -Math.PI / 2 + (i * 2 * Math.PI) / 5;
      const x2 = cx + Math.cos(ang) * maxR;
      const y2 = cy + Math.sin(ang) * maxR;
      const lx = cx + Math.cos(ang) * (maxR + 18);
      const ly = cy + Math.sin(ang) * (maxR + 14);
      return `
        <line x1="${cx}" y1="${cy}" x2="${x2.toFixed(1)}" y2="${y2.toFixed(1)}" stroke="rgba(200,155,60,0.22)" stroke-width="1"/>
        <text x="${lx.toFixed(1)}" y="${ly.toFixed(1)}" fill="#cbd5e1" font-size="9.5" font-weight="700" text-anchor="middle">${p.key}</text>
      `;
    }).join('');

    radarWrap.innerHTML = `
      <svg viewBox="0 0 220 210" class="gpi-svg">
        ${gridRings}
        ${axes}
        <polygon points="${ptsFor(pillars.map(p => p.val))}" fill="rgba(10, 200, 185, 0.28)" stroke="#0ac8b9" stroke-width="2.2"/>
      </svg>
    `;

    listWrap.innerHTML = pillars.map(p => `
      <div class="gpi-pillar-row">
        <span class="gpi-p-name">${p.key}</span>
        <div class="gpi-p-bar"><div class="gpi-p-fill" style="width:${p.val}%"></div></div>
        <span class="gpi-p-grade">${toGrade(p.val)}</span>
      </div>
    `).join('');

    // Porofessor-style Green / Gold / Red Player Tags
    const pTags = [];
    if (avgCs >= 6.8) pTags.push({ cls: 'good', title: isEn ? 'High CS' : 'Alto Farmeo', sub: `${avgCs.toFixed(1)} CS/min` });
    else if (avgCs > 0 && avgCs < 5.0) pTags.push({ cls: 'bad', title: isEn ? 'Low CS/min' : 'Farmeo Bajo', sub: `${avgCs.toFixed(1)} CS/min` });

    if (avgDmgShare >= 24) pTags.push({ cls: 'good', title: isEn ? 'Damage Carry' : 'Carry de Daño', sub: `${Math.round(avgDmgShare)}% team DMG` });
    if (avgTurrets >= 1.8) pTags.push({ cls: 'good', title: isEn ? 'Tower Crusher' : 'Destructor de Torres', sub: `${avgTurrets.toFixed(1)} / game` });
    if (avgDeaths <= 4.5) pTags.push({ cls: 'good', title: isEn ? 'Unkillable' : 'Difícil de Matar', sub: `${avgDeaths.toFixed(1)} deaths/g` });
    else if (avgDeaths >= 6.5) pTags.push({ cls: 'bad', title: isEn ? 'Vulnerable to Ganks' : 'Muertes Altas', sub: `${avgDeaths.toFixed(1)} deaths/g` });

    if (avgKp >= 56) pTags.push({ cls: 'good', title: isEn ? 'Teamfighter' : 'Alta Participación', sub: `${Math.round(avgKp)}% KP` });
    if (wrNum >= 54) pTags.push({ cls: 'gold', title: isEn ? 'Consistent Climber' : 'Escalador Constante', sub: `${wrNum.toFixed(1)}% WR` });

    const topChamp = (analysis.best_champions || [])[0];
    if (topChamp && (topChamp.games || 0) >= 25) {
      pTags.push({ cls: 'gold', title: `${displayName(topChamp.champion || topChamp.champion_name)} Main`, sub: `${topChamp.games} games` });
    }
    if (pTags.length < 3) {
      pTags.push({ cls: 'gold', title: isEn ? 'Adaptive Pool' : 'Pool Flexible', sub: `${champStats.length} champs` });
    }

    tagsEl.innerHTML = pTags.slice(0, 6).map(tg => `
      <div class="poro-tag ${tg.cls}">
        <strong>${tg.title}</strong>
        <span>${tg.sub}</span>
      </div>
    `).join('');

    sec.style.display = 'grid';
  }

  /* ── Modal de Análisis Profundo por Campeón ── */
  openChampionModal(champName) {
    if (!this.state.playerData) return;
    const analysis = this.state.playerData.analysis || this.state.playerData;
    const stats = (analysis.champion_stats || {})[champName];
    if (!stats) return;

    const modal = document.getElementById('champ-modal');
    if (!modal) return;

    const hero = document.getElementById('champ-modal-hero');
    const icon = document.getElementById('champ-modal-icon');
    const nameEl = document.getElementById('champ-modal-name');
    const subEl = document.getElementById('champ-modal-sub');
    const metricsEl = document.getElementById('champ-modal-metrics');
    const strengthsEl = document.getElementById('champ-modal-strengths');
    const improvementsEl = document.getElementById('champ-modal-improvements');

    const _tM = (k, fb) => (typeof t === 'function' ? t(k) : fb);
    if (hero) hero.style.backgroundImage = `url('https://ddragon.leagueoflegends.com/cdn/img/champion/splash/${champName}_0.jpg')`;
    if (icon) icon.src = champImgUrl(champName);
    if (nameEl) nameEl.textContent = displayName(champName);
    if (subEl) subEl.textContent = `${stats.win_rate}% Win Rate · ${stats.games} ${_tM('games_word', 'partidas')} (${stats.wins}${_tM('w_short', 'V')} - ${stats.losses}${_tM('l_short', 'D')}) · ${stats.avg_kda} KDA`;

    const deep = stats.deep_analysis || { metrics: {}, strengths: [], improvements: [] };
    const m = deep.metrics || {};

    if (metricsEl) {
      metricsEl.className = 'modal-bars-wrap';
      const csVal = Number(stats.avg_cs_per_min || 0);
      const csPct = Math.min(100, Math.round((csVal / 9.5) * 100));
      const dpmVal = Number(m.avg_dpm || 0);
      const dpmPct = Math.min(100, Math.round((dpmVal / 950) * 100));
      const kpVal = Number(m.avg_kp || 0);
      const kpPct = Math.min(100, Math.round(kpVal));
      const deathsVal = Number(m.avg_deaths || 5);
      const survPct = Math.max(15, Math.min(100, Math.round(((10 - deathsVal) / 8) * 100)));

      const _t = (k, fb) => (typeof t === 'function' ? t(k) : fb);
      const isEn = typeof getCurrentLang === 'function' && getCurrentLang() !== 'es';
      const bars = [
        { lbl: _t('bar_farm', '🌾 Farmeo'), val: `${csVal} CS/m${m.avg_cs10 != null ? ` · ${m.avg_cs10} @10m` : ''}`, pct: csPct, cls: csVal >= 7.5 ? 'high' : csVal >= 6 ? 'mid' : 'low' },
        { lbl: _t('bar_dmg', '💥 Daño / min'), val: `${dpmVal} DPM · ${stats.avg_damage_share || 0}%`, pct: dpmPct, cls: dpmVal >= 750 ? 'gold' : dpmVal >= 500 ? 'mid' : 'low' },
        { lbl: _t('bar_kp', '⚔️ Participación'), val: m.avg_kp != null ? `${kpVal}% KP` : '—', pct: kpPct, cls: kpVal >= 55 ? 'high' : kpVal >= 42 ? 'mid' : 'low' },
        { lbl: _t('bar_surv', '🛡️ Supervivencia'), val: `${deathsVal} ${_t('deaths_per_g', 'muertes/p')}`, pct: survPct, cls: deathsVal <= 4.5 ? 'high' : deathsVal <= 6.2 ? 'gold' : 'low' },
      ];

      metricsEl.innerHTML = bars.map(b => `
        <div class="modal-bar-item">
          <div class="modal-bar-top">
            <span class="modal-bar-label">${b.lbl}</span>
            <span class="modal-bar-val">${b.val}</span>
          </div>
          <div class="modal-bar-track">
            <div class="modal-bar-fill ${b.cls}" style="width:${b.pct}%"></div>
          </div>
        </div>
      `).join('');
    }

    // Construir chips visuales cortos bilingües (en vez de párrafos largos)
    const isEnModal = typeof getCurrentLang === 'function' && getCurrentLang() !== 'es';
    const goodTags = [];
    const badTags = [];
    if (stats.avg_cs_per_min >= 7.5) goodTags.push({ icon: '🌾', text: isEnModal ? 'Top Farming' : 'Farm Top', stat: `${stats.avg_cs_per_min}/m` });
    else if (stats.avg_cs_per_min < 6.0 && !(stats.roles_played || []).includes('SUP')) badTags.push({ icon: '🌾', text: isEnModal ? 'Low CS' : 'CS Bajo', stat: `${stats.avg_cs_per_min}/m` });

    if (m.avg_cs10 != null && m.avg_cs10 >= 72) goodTags.push({ icon: '⏱️', text: 'Early Farm', stat: `${m.avg_cs10} @10m` });
    else if (m.avg_cs10 != null && m.avg_cs10 < 58 && !(stats.roles_played || []).includes('SUP')) badTags.push({ icon: '⏱️', text: 'Early CS', stat: `${m.avg_cs10} @10m` });

    if ((m.avg_dpm || 0) >= 720 || (stats.avg_damage_share || 0) >= 25) goodTags.push({ icon: '💥', text: isEnModal ? 'High Damage' : 'Alto Daño', stat: `${m.avg_dpm} DPM` });
    if ((m.avg_turrets || 0) >= 2.0) goodTags.push({ icon: '🏰', text: isEnModal ? 'Turret Pressure' : 'Presión Torres', stat: `${m.avg_turrets}/g` });
    if ((m.solo_kills || 0) >= 5) goodTags.push({ icon: '🗡️', text: 'Solo Kills', stat: `${m.solo_kills}` });
    if ((m.avg_deaths || 9) <= 4.3) goodTags.push({ icon: '🛡️', text: isEnModal ? 'Low Deaths' : 'Pocas Muertes', stat: `${m.avg_deaths}/g` });

    if (m.deaths_in_wins != null && m.deaths_in_losses != null && (m.deaths_in_losses - m.deaths_in_wins) >= 2.0) {
      badTags.push({ icon: '💀', text: isEnModal ? 'Deaths in losses' : 'Muertes en derrota', stat: `${m.deaths_in_losses} vs ${m.deaths_in_wins}` });
    } else if ((m.avg_deaths || 0) >= 6.2) {
      badTags.push({ icon: '💀', text: isEnModal ? 'High Deaths' : 'Muertes altas', stat: `${m.avg_deaths}/g` });
    }
    if ((m.avg_pinks || 0) < 1.0) badTags.push({ icon: '👁️', text: 'Control Wards', stat: `${m.avg_pinks}/g` });
    if (m.avg_kp != null && m.avg_kp < 44) badTags.push({ icon: '⚔️', text: isEnModal ? 'Low KP' : 'Baja KP', stat: `${m.avg_kp}%` });

    if (goodTags.length === 0) goodTags.push({ icon: '✅', text: isEnModal ? 'Steady KDA' : 'KDA Consistente', stat: `${stats.avg_kda}` });
    if (badTags.length === 0) badTags.push({ icon: '🌟', text: isEnModal ? 'No major weaknesses' : 'Sin debilidades claras', stat: 'Top' });

    if (strengthsEl) {
      strengthsEl.className = 'modal-tags-grid';
      strengthsEl.innerHTML = goodTags.map(tg => `<span class="modal-tag-pill good">${tg.icon} ${tg.text} <span class="modal-tag-stat">${tg.stat}</span></span>`).join('');
    }
    if (improvementsEl) {
      improvementsEl.className = 'modal-tags-grid';
      improvementsEl.innerHTML = badTags.map(tg => `<span class="modal-tag-pill bad">${tg.icon} ${tg.text} <span class="modal-tag-stat">${tg.stat}</span></span>`).join('');
    }

    modal.style.display = 'flex';

    // Cerrar con X o click afuera
    const closeBtn = document.getElementById('champ-modal-close');
    if (closeBtn) closeBtn.onclick = () => { modal.style.display = 'none'; };
    modal.onclick = (e) => { if (e.target === modal) modal.style.display = 'none'; };
  }

  /* ══════════════════════════════════════
     Render: Role-specific Champions
     ══════════════════════════════════════ */
  renderRoleChampions(role) {
    this.roleChampGrid.innerHTML = '';
    if (!this.state.playerData) return;

    const analysis = this.state.playerData.analysis || this.state.playerData;
    const roleAnalysis = analysis.role_analysis || {};
    const champStats = analysis.champion_stats || {};
    const mappedRole = ROLE_LABELS[role] || role;
    const champs = roleAnalysis[mappedRole] || roleAnalysis[role] || [];

    if (champs.length === 0) {
      this.roleChampGrid.innerHTML = `<p class="no-data-msg">No se encontraron campeones para el rol ${mappedRole}.</p>`;
      return;
    }

    champs.forEach(entry => {
      const name = typeof entry === 'string' ? entry : (entry.champion || entry.champion_name);
      const fullStats = champStats[name] || {};
      const merged = typeof entry === 'string'
        ? { ...fullStats, champion_name: name }
        : { ...fullStats, ...entry, champion_name: name };
      const card = this._buildChampCard(merged);
      this.roleChampGrid.appendChild(card);
    });
  }

  /* ══════════════════════════════════════
     Draft: Render Board
     ══════════════════════════════════════ */
  renderDraftBoard() {
    const { allyPicks, enemyPicks } = this.state.draftState;

    this._renderPickSlots(this.allyPicksEl, allyPicks);
    this._renderPickSlots(this.enemyPicksEl, enemyPicks);
  }

  _renderPickSlots(container, picks) {
    const slots = container.querySelectorAll('.pick-slot');
    slots.forEach((slot, i) => {
      const pick = picks[i];
      if (pick) {
        slot.classList.add('filled');
        slot.querySelector('.pick-slot-inner').innerHTML = `
          <img class="pick-champ-icon" src="${champImgUrl(pick.name)}" alt="${displayName(pick.name)}"
               onerror="this.src='${champImgUrl('Aatrox')}'">
          <span class="pick-champ-name">${displayName(pick.name)}</span>
          <span class="pick-remove"><i class="fa-solid fa-xmark"></i></span>
        `;
      } else {
        slot.classList.remove('filled');
        slot.querySelector('.pick-slot-inner').innerHTML = `<i class="fa-solid fa-plus"></i>`;
      }
    });
  }

  /* ══════════════════════════════════════
     Draft: Champion Search
     ══════════════════════════════════════ */
  renderChampionSearch(query) {
    const q = query.toLowerCase().trim();
    const { allyPicks, enemyPicks } = this.state.draftState;
    const pickedNames = new Set(
      [...allyPicks, ...enemyPicks].filter(Boolean).map(p => p.name)
    );

    // Build list from championList or fallback
    let champions = this.state.championList.length > 0
      ? this.state.championList
      : Object.entries(CHAMPION_NAMES).map(([id, name]) => ({ id: parseInt(id), name }));

    // Filter by query
    if (q) {
      champions = champions.filter(c =>
        (c.name || '').toLowerCase().includes(q) ||
        displayName(c.name).toLowerCase().includes(q)
      );
    }

    // Sort alphabetically by display name
    champions.sort((a, b) => displayName(a.name).localeCompare(displayName(b.name)));

    // Limit display
    const show = champions.slice(0, 60);

    this.champSearchResults.innerHTML = show.map(c => {
      const disabled = pickedNames.has(c.name) ? 'disabled' : '';
      return `
        <div class="search-champ-item ${disabled}" data-champ="${c.name}" data-id="${c.id}">
          <img src="${champImgUrl(c.name)}" alt="${displayName(c.name)}"
               onerror="this.src='${champImgUrl('Aatrox')}'">
          <span>${displayName(c.name)}</span>
        </div>
      `;
    }).join('');
  }

  /* ══════════════════════════════════════
     Draft: Update → fetch recommendations
     ══════════════════════════════════════ */
  async updateDraft() {
    if (!this.state.playerData) return;

    const { allyPicks, enemyPicks, bans, myRole } = this.state.draftState;

    // We need at least the role selected to request recs
    try {
      const res = await fetch('/api/draft', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          player_analysis: this.state.playerData.analysis || this.state.playerData,
          ally_picks: allyPicks.filter(Boolean).map(p => p.name),
          enemy_picks: enemyPicks.filter(Boolean).map(p => p.name),
          bans: bans || [],
          role: myRole,
          lang: typeof getCurrentLang === 'function' ? getCurrentLang() : 'es',
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || 'Error al obtener recomendaciones.');
      }

      const data = await res.json();
      this.state.draftState.recommendations = data.recommendations || [];
      this.state.draftState.coach = data.coach || null;
      this.renderCoachPanel();
      this.renderRecommendations();
    } catch (err) {
      // Silently fail or show subtle error
      console.error('Draft update error:', err);
    }
  }

  /* ══════════════════════════════════════
     Render: Coach Strategic Panel
     ══════════════════════════════════════ */
  renderCoachPanel() {
    const coach = this.state.draftState.coach;
    if (!coach) return;

    // 0. Medidor de Draft Diff + Semáforo de Dodge
    const de = coach.draft_eval;
    const diffBox = document.getElementById('draft-diff-box');
    if (de && diffBox) {
      diffBox.style.display = 'block';
      const aEl = document.getElementById('diff-ally-pct');
      const eEl = document.getElementById('diff-enemy-pct');
      const vEl = document.getElementById('diff-verdict');
      const fEl = document.getElementById('draft-diff-fill');
      const isEn = typeof getCurrentLang === 'function' && getCurrentLang() !== 'es';
      if (aEl) aEl.textContent = `${de.ally_pct}% ${isEn ? 'Allies' : 'Aliados'}`;
      if (eEl) eEl.textContent = `${de.enemy_pct}% ${isEn ? 'Enemies' : 'Enemigos'}`;
      if (vEl) vEl.textContent = de.label || '';
      if (fEl) fEl.style.width = `${de.ally_pct}%`;
    }

    // 1. Bans recomendados
    const isEnCoach = typeof getCurrentLang === 'function' && getCurrentLang() !== 'es';
    if (this.coachBansEl) {
      const bans = coach.recommended_bans || [];
      if (bans.length === 0) {
        this.coachBansEl.innerHTML = `<span class="coach-muted">${isEnCoach ? 'No critical threats detected.' : 'Sin amenazas críticas detectadas.'}</span>`;
      } else {
        this.coachBansEl.innerHTML = bans.map(b => `
          <div class="coach-ban-chip">
            <img src="${champImgUrl(b.champion)}" alt="${displayName(b.champion)}"
                 onerror="this.src='${champImgUrl('Aatrox')}'">
            <div class="coach-ban-info">
              <span class="coach-ban-name">${isEnCoach ? 'Ban' : 'Banear'} ${displayName(b.champion)}</span>
              <span class="coach-ban-reason">${b.reason}</span>
            </div>
          </div>
        `).join('');
      }
    }

    // 2. Orden de pick / Swap
    if (this.coachPickOrderEl) {
      this.coachPickOrderEl.textContent = coach.pick_order_advice || '';
    }

    // 3. Alertas de composición
    if (this.coachAlertsEl) {
      const alerts = coach.team_alerts || [];
      this.coachAlertsEl.innerHTML = alerts.map(a => `
        <div class="coach-alert ${a.type === 'warning' ? 'warning' : 'ok'}">
          <strong>${a.type === 'warning' ? '⚠️' : '✅'} ${a.title}</strong>
          ${a.detail}
        </div>
      `).join('');
    }

    // 4. Mensaje sugerido para el equipo
    if (this.coachChatTextEl) {
      this.coachChatTextEl.textContent = coach.teammate_chat_tip || '';
    }

    // 5. Plan de Partida (Gameplan)
    const gp = coach.gameplan;
    if (gp && this.gameplanStatusEl && this.gameplanContentEl) {
      this.gameplanStatusEl.textContent = gp.status_label || '';
      if (!gp.ready) {
        this.gameplanContentEl.innerHTML = `<p class="coach-muted" style="grid-column:1/-1;margin:0;">${gp.win_condition}</p>`;
      } else {
        this.gameplanContentEl.innerHTML = `
          <div class="gameplan-item">
            <strong>🎯 Win Condition</strong>
            ${gp.win_condition}
          </div>
          <div class="gameplan-item">
            <strong>⚡ Early Game (0-14 min)</strong>
            ${gp.early_game}
          </div>
          <div class="gameplan-item">
            <strong>⚔️ Teamfights (Mid/Late)</strong>
            ${gp.teamfights}
          </div>
          <div class="gameplan-item">
            <strong>🛡️ ${isEnCoach ? 'Threats & Itemization' : 'Amenazas e Itemización'}</strong>
            ${gp.itemization}
          </div>
        `;
      }
    }
  }

  /* ── Custom Saved Runes & Spells per Champion ── */
  getCustomRunesMap() {
    try {
      return JSON.parse(localStorage.getItem('NoFlash_custom_runes_v1') || '{}');
    } catch {
      return {};
    }
  }

  getCustomRunes(champName) {
    const key = normalizeChampionId(champName);
    return this.getCustomRunesMap()[key] || null;
  }

  saveCustomRunes(champName, cfg) {
    const map = this.getCustomRunesMap();
    map[normalizeChampionId(champName)] = cfg;
    localStorage.setItem('NoFlash_custom_runes_v1', JSON.stringify(map));
  }

  async _importSetupToLoL(champion, keystone, spells, btnEl = null) {
    if (btnEl) btnEl.disabled = true;
    const isEn = typeof getCurrentLang === 'function' ? getCurrentLang() !== 'es' : true;
    try {
      const res = await fetch('/api/lcu/import-setup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ champion, keystone, spells }),
      });
      const data = await res.json();
      if (data.success) window.uiSfx?.playSuccess();
      this.showToast(data.message || (isEn ? 'Runes & Spells imported!' : 'Importación completada.'), data.success ? 'success' : 'error');
    } catch {
      this.showToast(isEn ? 'Could not connect to League Client.' : 'Error al conectar con el cliente de LoL.', 'error');
    } finally {
      if (btnEl) btnEl.disabled = false;
    }
  }

  openRuneEditor(champName, currentSetup) {
    const modal = document.getElementById('rune-editor-modal');
    if (!modal) return;
    const norm = normalizeChampionId(champName);
    const saved = this.getCustomRunes(norm);
    const ks = (saved?.keystone || currentSetup?.keystone || 'Lethal Tempo');
    const spArr = (saved?.spells || currentSetup?.spells || ['Flash', 'Barrier']).map(s => String(s).split('(')[0].trim());

    document.getElementById('re-champ-icon').src = champImgUrl(norm);
    document.getElementById('re-champ-title').textContent = `${displayName(norm)} — Custom Runes & Spells`;

    const ksSel = document.getElementById('re-keystone');
    const sp1Sel = document.getElementById('re-spell1');
    const sp2Sel = document.getElementById('re-spell2');
    if (ksSel) {
      const opt = [...ksSel.options].find(o => o.value.toLowerCase() === ks.toLowerCase());
      if (opt) ksSel.value = opt.value;
    }
    const matchSpell = (sel, raw) => {
      if (!sel || !raw) return;
      const low = raw.toLowerCase();
      const mapEs = { destello: 'Flash', barrera: 'Barrier', limpiar: 'Cleanse', extenuar: 'Exhaust', prender: 'Ignite', teleportación: 'Teleport', fantasmal: 'Ghost', curar: 'Heal', aplastar: 'Smite' };
      const target = mapEs[low] || raw;
      const opt = [...sel.options].find(o => o.value.toLowerCase() === target.toLowerCase());
      if (opt) sel.value = opt.value;
    };
    matchSpell(sp1Sel, spArr[0] || 'Flash');
    matchSpell(sp2Sel, spArr[1] || 'Barrier');

    this._editingRuneChamp = norm;
    modal.style.display = 'flex';

    if (!this._runeEditorBound) {
      this._runeEditorBound = true;
      const close = () => { modal.style.display = 'none'; };
      document.getElementById('rune-editor-close')?.addEventListener('click', close);
      modal.addEventListener('click', (e) => { if (e.target === modal) close(); });

      const readForm = () => ({
        keystone: document.getElementById('re-keystone').value,
        spells: [document.getElementById('re-spell1').value, document.getElementById('re-spell2').value],
      });

      document.getElementById('re-btn-save')?.addEventListener('click', () => {
        const cfg = readForm();
        this.saveCustomRunes(this._editingRuneChamp, cfg);
        window.uiSfx?.playSuccess();
        this.showToast(`Saved custom runes for ${displayName(this._editingRuneChamp)}!`, 'success');
        close();
        this.renderRecommendations();
      });

      document.getElementById('re-btn-save-import')?.addEventListener('click', async (e) => {
        const cfg = readForm();
        this.saveCustomRunes(this._editingRuneChamp, cfg);
        close();
        this.renderRecommendations();
        await this._importSetupToLoL(this._editingRuneChamp, cfg.keystone, cfg.spells, e.currentTarget);
      });
    }
  }

  /* ══════════════════════════════════════
     Render: Recommendations (#1 Spotlight + Full List)
     ══════════════════════════════════════ */
  renderRecommendations() {
    const recs = this.state.draftState.recommendations;
    const spotlightEl = document.getElementById('top-pick-spotlight');

    if (!recs || recs.length === 0) {
      if (spotlightEl) spotlightEl.style.display = 'none';
      const emptyMsg = typeof t === 'function' ? t('empty_recs') : 'Select your role and add picks to get recommendations.';
      this.recsListEl.innerHTML = `
        <div class="empty-recs">
          <i class="fa-solid fa-wand-magic-sparkles"></i>
          <p>${emptyMsg}</p>
        </div>
      `;
      return;
    }

    const isEn = typeof getCurrentLang === 'function' ? getCurrentLang() !== 'es' : true;

    // ── #1 RECOMMENDED PICK SPOTLIGHT (EN PRIMER PLANO ARRIBA DE TODO) ──
    if (spotlightEl) {
      const top = recs[0];
      const topChamp = top.champion || top.champion_name || CHAMPION_NAMES[top.champion_id] || 'Unknown';
      const topScore = top.draft_score != null ? (top.draft_score * 100).toFixed(0) : '—';
      const topTier = top.tier || 'S+';
      const savedTop = this.getCustomRunes(topChamp);
      const topSetup = savedTop
        ? { ...(top.setup || {}), keystone: savedTop.keystone, spells: savedTop.spells, isCustom: true }
        : (top.setup || { keystone: 'Lethal Tempo', spells: ['Flash', 'Barrier'] });
      const splash = champSplashUrl(topChamp);
      const spIcons = (topSetup.spells || []).map(sp => `<img src="${spellImgUrl(sp)}" alt="${sp}" title="${sp}">`).join('');

      spotlightEl.style.backgroundImage = `linear-gradient(90deg, rgba(6,16,32,0.95) 0%, rgba(9,22,42,0.86) 55%, rgba(6,16,32,0.92) 100%), url('${splash}')`;
      spotlightEl.innerHTML = `
        <div class="spotlight-left">
          <img src="${champImgUrl(topChamp)}" alt="${displayName(topChamp)}" class="spotlight-avatar">
          <div class="spotlight-info">
            <div class="spotlight-kicker">👑 ${isEn ? '#1 BEST PICK FOR YOU NOW' : '👑 MEJOR PICK #1 PARA VOS AHORA'} ${topSetup.isCustom ? '<span class="saved-rune-pill">★ Custom Runes</span>' : ''}</div>
            <div class="spotlight-name-row">
              <span class="spotlight-champ">${displayName(topChamp)}</span>
              <span class="tier-badge tier-sp">${topTier}</span>
              <span class="spotlight-score">${topScore} PTS</span>
            </div>
            <div class="spotlight-setup-row">
              <img src="${keystoneImgUrl(topSetup.keystone)}" alt="${topSetup.keystone}" class="spotlight-ks-icon">
              <span>${topSetup.keystone || 'Optimal Runes'}</span>
              <span class="spotlight-spells">${spIcons}</span>
            </div>
          </div>
        </div>
        <div class="spotlight-actions">
          <button class="btn-import-hero" id="btn-spotlight-import">
            <i class="fa-solid fa-bolt"></i> ${isEn ? 'IMPORT RUNES & SPELLS TO LOL' : 'IMPORTAR RUNAS Y HECHIZOS AL LOL'}
          </button>
          <button class="btn-edit-runes" id="btn-spotlight-edit">
            <i class="fa-solid fa-sliders"></i> ${isEn ? 'Edit & Save Runes' : 'Editar y Guardar Runas'}
          </button>
        </div>
      `;
      spotlightEl.style.display = 'flex';

      document.getElementById('btn-spotlight-import')?.addEventListener('click', (e) => {
        this._importSetupToLoL(topChamp, topSetup.keystone, topSetup.spells || [], e.currentTarget);
      });
      document.getElementById('btn-spotlight-edit')?.addEventListener('click', () => {
        this.openRuneEditor(topChamp, topSetup);
      });
    }

    this.recsListEl.innerHTML = recs.map((rec, idx) => {
      const champName = rec.champion || rec.champion_name || CHAMPION_NAMES[rec.champion_id] || 'Unknown';
      const score = rec.draft_score != null ? (rec.draft_score * 100).toFixed(0) : '—';
      const scorePct = rec.draft_score != null ? Math.min(100, Math.max(0, rec.draft_score * 100)).toFixed(0) : 0;
      const tier = rec.tier || 'A';
      const tierClass = tier === 'S+' ? 'tier-sp' : tier === 'S' ? 'tier-s' : tier === 'A' ? 'tier-a' : 'tier-b';
      const tag = rec.tag || '';

      const bd = rec.scores_breakdown || {};
      const comfortVal = bd.player_comfort != null ? bd.player_comfort : rec.comfort;
      const counterVal = bd.counter_value != null ? bd.counter_value : rec.counter_value;
      const synergyVal = bd.team_synergy != null ? bd.team_synergy : rec.synergy;
      const metaVal = bd.meta_strength != null ? bd.meta_strength : rec.meta_strength;

      const comfort = comfortVal != null ? (comfortVal * 100).toFixed(0) : '—';
      const counter = counterVal != null ? (counterVal * 100).toFixed(0) : '—';
      const synergy = synergyVal != null ? (synergyVal * 100).toFixed(0) : '—';
      const meta = metaVal != null ? (metaVal * 100).toFixed(0) : '—';
      const explanation = rec.explanation || '';
      const _t = (k, fb) => (typeof t === 'function' ? t(k) : fb);
      const setup = rec.setup || null;
      const setupHtml = setup ? `
        <div class="rec-setup">
          <div class="setup-pill spells">
            <div class="setup-pill-title"><i class="fa-solid fa-wand-sparkles"></i> ${_t('spells_title', 'Hechizos')}</div>
            <div class="setup-icons-row">
              <div class="spell-icons">
                ${(setup.spells || []).map(sp => `<img class="spell-icon-img" src="${spellImgUrl(sp)}" alt="${sp}" title="${sp}">`).join('')}
              </div>
              <div>
                <div class="setup-pill-main">${(setup.spells || []).join(' + ')}</div>
                <div class="setup-pill-sub">${setup.spell_reason || ''}</div>
              </div>
            </div>
          </div>
          <div class="setup-pill runes">
            <div class="setup-pill-title"><i class="fa-solid fa-gem"></i> ${_t('runes_title', 'Runas')}</div>
            <div class="setup-icons-row">
              <div class="rune-icons">
                <img class="rune-keystone-img" src="${keystoneImgUrl(setup.keystone)}" alt="${setup.keystone}" title="${setup.keystone}">
                <img class="rune-tree-img" src="${runeTreeImgUrl(setup.secondary_tree)}" alt="${setup.secondary_tree}" title="${setup.secondary_tree}">
              </div>
              <div>
                <div class="setup-pill-main">${setup.keystone} (${setup.primary_tree} + ${setup.secondary_tree})</div>
                <div class="setup-pill-sub">${setup.rune_tip || ''}</div>
              </div>
            </div>
          </div>
        </div>
      ` : '';

      return `
        <div class="rec-card ${idx === 0 ? 'top-rec' : ''}">
          <div class="rec-card-header">
            <img src="${champImgUrl(champName)}" alt="${displayName(champName)}"
                 onerror="this.src='${champImgUrl('Aatrox')}'">
            <div class="rec-title-group">
              <span class="rec-champ-name">${displayName(champName)}</span>
              <span class="rec-tier ${tierClass}">Tier ${tier}</span>
              ${tag ? `<span class="rec-tag">${tag}</span>` : ''}
            </div>
            <span class="rec-score">${score}</span>
          </div>
          <div class="rec-score-bar"><div class="rec-score-bar-fill" style="width:${scorePct}%"></div></div>
          <div class="rec-breakdown">
            <span><span class="bd-label">${_t('bd_comfort', 'Comfort')}:</span> <span class="bd-value">${comfort}</span></span>
            <span><span class="bd-label">${_t('bd_counter', 'Counter')}:</span> <span class="bd-value">${counter}</span></span>
            <span><span class="bd-label">${_t('bd_synergy', 'Sinergia')}:</span> <span class="bd-value">${synergy}</span></span>
            <span><span class="bd-label">${_t('bd_meta', 'Comp/Meta')}:</span> <span class="bd-value">${meta}</span></span>
          </div>
          ${explanation ? `<div class="rec-explanation">${explanation}</div>` : ''}
          ${setupHtml}
          ${(() => {
            const custom = this.getCustomRunes(champName);
            const effKs = custom?.keystone || setup?.keystone || 'Lethal Tempo';
            const effSp = custom?.spells || setup?.spells || ['Flash', 'Barrier'];
            return `
              <div class="rec-action-row">
                <button class="btn-import-lol"
                        data-champ="${champName}"
                        data-keystone="${effKs}"
                        data-spells="${effSp.join('|')}">
                  <i class="fa-solid fa-bolt"></i> ${isEn ? 'Import Runes & Spells to LoL' : 'Importar Runas y Hechizos al LoL'}${custom ? ' ★' : ''}
                </button>
                <button class="btn-edit-runes-sm" data-champ="${champName}" data-keystone="${effKs}" data-spells="${effSp.join('|')}" title="Edit & Save Custom Runes">
                  <i class="fa-solid fa-sliders"></i>
                </button>
              </div>
            `;
          })()}
        </div>
      `;
    }).join('');

    // Wire 1-click LCU Import + Edit Runes buttons
    this.recsListEl.querySelectorAll('.btn-import-lol').forEach(btn => {
      btn.addEventListener('click', () => {
        const spells = (btn.dataset.spells || '').split('|').filter(Boolean);
        this._importSetupToLoL(btn.dataset.champ, btn.dataset.keystone, spells, btn);
      });
    });
    this.recsListEl.querySelectorAll('.btn-edit-runes-sm').forEach(btn => {
      btn.addEventListener('click', () => {
        const spells = (btn.dataset.spells || '').split('|').filter(Boolean);
        this.openRuneEditor(btn.dataset.champ, { keystone: btn.dataset.keystone, spells });
      });
    });
  }

  /* ── Detect player's most played role ── */
  _detectMainRole(data) {
    const analysis = data.analysis || data;
    const roleAnalysis = analysis.role_analysis || {};
    let bestRole = 'MID';
    let maxGames = -1;
    for (const [role, champs] of Object.entries(roleAnalysis)) {
      if (!Array.isArray(champs)) continue;
      const total = champs.reduce((acc, c) => acc + (c.games || 1), 0);
      if (total > maxGames) {
        maxGames = total;
        bestRole = role;
      }
    }
    return bestRole;
  }

  /* ══════════════════════════════════════
     LCU Live Sync (Cliente de LoL en PC)
     ══════════════════════════════════════ */
  startLCUPolling() {
    if (!this.lcuPill) return;
    this.lcuAutoAnalyzedId = null;
    this.lcuAnalyzing = false;

    this.lcuPill.addEventListener('click', () => {
      if (!this.lcuLastSummoner) {
        this.showToast('Abrí el cliente de League of Legends para conectar automáticamente.', 'info');
        return;
      }
      this._triggerAutoAnalyze(this.lcuLastSummoner, true);
    });

    const loop = async () => {
      const inDraft = await this.pollLCU();
      // 1.5s durante Champ Select (tiempo real), 4s cuando estás en el lobby
      setTimeout(loop, inDraft ? 1500 : 4000);
    };
    loop();
  }

  async _triggerAutoAnalyze(summoner, force = false) {
    if (!summoner || !summoner.game_name || this.lcuAnalyzing) return;
    const key = `${summoner.game_name}#${summoner.tag_line || ''}`;
    if (!force && this.lcuAutoAnalyzedId === key && this.state.playerData) return;

    this.lcuAnalyzing = true;
    this.lcuAutoAnalyzedId = key;
    this.gameNameInput.value = summoner.game_name;
    if (summoner.tag_line) this.tagLineInput.value = summoner.tag_line;

    // Mapear región del cliente de LoL (ej: BR1 -> BR, LA2 -> LAS, LA1 -> LAN)
    const rawRegion = (summoner.region || '').toUpperCase();
    const lcuRegionAlias = {
      LA2: 'LAS', LAS: 'LAS',
      LA1: 'LAN', LAN: 'LAN',
      BR1: 'BR',  BR: 'BR',
      NA1: 'NA',  NA: 'NA',
      EUW1: 'EUW', EUW: 'EUW',
      EUN1: 'EUNE', EUNE: 'EUNE',
      OC1: 'OCE', OCE: 'OCE',
      KR: 'KR', JP1: 'JP', TR1: 'TR', RU: 'RU',
    };
    const mappedRegion = lcuRegionAlias[rawRegion];
    if (mappedRegion && REGION_PLATFORM_MAP[mappedRegion]) {
      this.regionSelect.value = mappedRegion;
      this.regionSelect.dispatchEvent(new Event('change'));
    }

    try {
      await this.analyzePlayer();
    } finally {
      this.lcuAnalyzing = false;
    }
  }

  async pollLCU() {
    try {
      const res = await fetch('/api/lcu/status');
      if (!res.ok) return false;
      const status = await res.json();

      if (!status.connected) {
        this.lcuLastSummoner = null;
        this.lcuPill.className = 'lcu-pill';
        this.lcuText.textContent = typeof t === 'function' ? t('lcu_not_found') : 'LoL: Sin detectar';
        return false;
      }

      this.lcuLastSummoner = status.summoner || null;
      const isEnLcu = typeof getCurrentLang === 'function' && getCurrentLang() !== 'es';
      const sName = status.summoner?.game_name
        ? `${status.summoner.game_name}#${status.summoner.tag_line || ''}`
        : (isEnLcu ? 'Connected' : 'Conectado');

      // Auto-analizar cuenta logueada solo si el usuario no eligió manualmente otra cuenta (ej: modo smurf)
      if (this.lcuLastSummoner && !this.state.playerData && !this.lcuAnalyzing && !this.manualProfileLocked) {
        this._triggerAutoAnalyze(this.lcuLastSummoner, false);
      }

      if (status.in_champ_select) {
        this.lcuPill.className = 'lcu-pill in-draft';
        this.lcuText.textContent = typeof t === 'function' ? t('lcu_live_draft') : 'EN DRAFT EN VIVO';
        await this.syncLiveChampSelect();
        return true;
      } else {
        this.lcuPill.className = 'lcu-pill connected';
        this.lcuText.textContent = `LoL: ${sName}`;
        this.lcuLastDraftKey = '';
        return false;
      }
    } catch {
      return false;
    }
  }

  async syncLiveChampSelect() {
    try {
      const res = await fetch('/api/lcu/champ-select');
      if (!res.ok) return;
      const cs = await res.json();
      if (!cs.in_champ_select) return;

      const draftKey = JSON.stringify({
        role: cs.my_role,
        ally: cs.ally_picks,
        enemy: cs.enemy_picks,
        bans: cs.bans,
      });
      if (draftKey === this.lcuLastDraftKey) return;
      this.lcuLastDraftKey = draftKey;

      // Actualizar rol detectado
      if (cs.my_role) {
        const roleToBtn = { TOP: 'TOP', JG: 'JUNGLE', MID: 'MIDDLE', ADC: 'BOTTOM', SUP: 'UTILITY' };
        const btnRole = roleToBtn[cs.my_role] || 'MIDDLE';
        this.state.draftState.myRole = btnRole;
        this.draftRoleButtons.querySelectorAll('.role-btn').forEach(b => {
          b.classList.toggle('active', b.dataset.role === btnRole);
        });
      }

      // Actualizar picks aliados, enemigos y bans en el tablero
      const toSlots = (names) => {
        const arr = [null, null, null, null, null];
        (names || []).slice(0, 5).forEach((name, idx) => {
          arr[idx] = { id: 0, name };
        });
        return arr;
      };

      this.state.draftState.allyPicks = toSlots(cs.ally_picks);
      this.state.draftState.enemyPicks = toSlots(cs.enemy_picks);
      this.state.draftState.bans = cs.bans || [];
      this.renderDraftBoard();

      if (this.state.playerData) {
        if (this.state.currentView !== 'draft') {
          this.switchView('draft');
          window.uiSfx?.playLockIn();
          const isEnCs = typeof getCurrentLang === 'function' && getCurrentLang() !== 'es';
          this.showToast(isEnCs ? 'Live draft detected! Updating recommendations...' : '¡Draft en vivo detectado! Recomendando en tiempo real...', 'success');
        }
        this.updateDraft();
      }
    } catch {
      // Ignorar errores transitorios
    }
  }

  /* ── Cuentas guardadas en localStorage (Main / Smurf) ── */
  getSavedAccounts() {
    try {
      return JSON.parse(localStorage.getItem('lol_draft_saved_accounts') || '[]');
    } catch {
      return [];
    }
  }

  saveAccount(acc) {
    const list = this.getSavedAccounts().filter(
      a => !(a.gameName.toLowerCase() === acc.gameName.toLowerCase() &&
             a.tagLine.toLowerCase() === acc.tagLine.toLowerCase() &&
             a.region === acc.region)
    );
    list.unshift(acc);
    localStorage.setItem('lol_draft_saved_accounts', JSON.stringify(list.slice(0, 6)));
    this.renderSavedAccounts();
  }

  removeSavedAccount(idx) {
    const list = this.getSavedAccounts();
    list.splice(idx, 1);
    localStorage.setItem('lol_draft_saved_accounts', JSON.stringify(list));
    this.renderSavedAccounts();
  }

  renderSavedAccounts() {
    if (!this.savedAccountsWrap || !this.savedAccountsList) return;
    const list = this.getSavedAccounts();
    if (list.length === 0) {
      this.savedAccountsWrap.style.display = 'none';
      return;
    }
    // Pre-rellenar automáticamente el último nick/región analizado al abrir la app
    if (this.gameNameInput && !this.gameNameInput.value.trim() && list[0]) {
      this.gameNameInput.value = list[0].gameName || '';
      if (this.tagLineInput) this.tagLineInput.value = list[0].tagLine || '';
      if (this.regionSelect && list[0].region) {
        this.regionSelect.value = list[0].region;
        this.regionSelect.dispatchEvent(new Event('change'));
        if (this.platformSelect && list[0].platform) {
          this.platformSelect.value = list[0].platform;
        }
      }
    }
    this.savedAccountsWrap.style.display = 'flex';
    this.savedAccountsList.innerHTML = list.map((acc, idx) => `
      <span class="saved-account-chip" data-idx="${idx}">
        <span>${acc.gameName}#${acc.tagLine}</span>
        <span class="chip-region">${acc.region}</span>
        <i class="fa-solid fa-xmark chip-remove" data-remove="${idx}" title="Quitar"></i>
      </span>
    `).join('');

    this.savedAccountsList.querySelectorAll('.saved-account-chip').forEach(chip => {
      chip.addEventListener('click', (e) => {
        if (e.target.dataset.remove != null) {
          e.stopPropagation();
          this.removeSavedAccount(parseInt(e.target.dataset.remove));
          return;
        }
        const acc = list[parseInt(chip.dataset.idx)];
        if (!acc) return;
        this.gameNameInput.value = acc.gameName;
        this.tagLineInput.value = acc.tagLine;
        this.regionSelect.value = acc.region;
        this.regionSelect.dispatchEvent(new Event('change'));
        if (acc.platform) this.platformSelect.value = acc.platform;
        this.manualProfileLocked = true;
        this.analyzePlayer();
      });
    });
  }

  /* ══════════════════════════════════════
     Voice Coach + Live In-Game Monitor
     ══════════════════════════════════════ */
  initVoiceControls() {
    this.btnVoiceToggle = document.getElementById('btn-voice-toggle');
    this.voiceStatusText = document.getElementById('voice-status-text');
    this.btnSpeakCoach = document.getElementById('btn-speak-coach');
    this.btnTestVoiceDemo = document.getElementById('btn-test-voice-demo');

    const syncVoiceUI = () => {
      if (!this.btnVoiceToggle || !window.voiceCoach) return;
      const on = window.voiceCoach.isEnabled();
      this.btnVoiceToggle.classList.toggle('active-voice', on);
      const icon = this.btnVoiceToggle.querySelector('i');
      if (icon) icon.className = on ? 'fa-solid fa-volume-high' : 'fa-solid fa-volume-xmark';
      if (this.voiceStatusText) this.voiceStatusText.textContent = on ? 'Voz ON' : 'Voz OFF';
    };
    syncVoiceUI();

    if (this.btnVoiceToggle) {
      this.btnVoiceToggle.addEventListener('click', () => {
        if (!window.voiceCoach) return;
        const on = window.voiceCoach.toggle();
        syncVoiceUI();
        if (on) {
          window.voiceCoach.speak('Coach por voz de NoFlash activado.', { force: true });
        }
      });
    }

    if (this.btnSpeakCoach) {
      this.btnSpeakCoach.addEventListener('click', () => {
        if (!window.voiceCoach) return;
        const { recommendations, coach } = this.state.draftState;
        if (!recommendations || recommendations.length === 0) {
          const isEnV = typeof getCurrentLang === 'function' && getCurrentLang() !== 'es';
          window.voiceCoach.speak(isEnV ? 'First analyze your account and select your role to get draft recommendations.' : 'Primero analizá tu cuenta y seleccioná tu rol para darte recomendaciones.', { force: true });
          return;
        }
        window.voiceCoach.speakDraftAdvice(recommendations, coach, true);
      });
    }

    if (this.btnTestVoiceDemo) {
      this.btnTestVoiceDemo.addEventListener('click', () => {
        if (!window.voiceCoach) return;
        const lang = (typeof getCurrentLang === 'function') ? getCurrentLang() : 'es';
        const msg = lang === 'es'
          ? 'Hola, soy tu Coach de NoFlash. Durante el draft te digo qué banear y qué pickear, y en partida te aviso los objetivos y las ventanas de gankeo.'
          : 'Hey, I am your NoFlash Coach. During draft I call out bans and best picks, and in-game I track objectives and enemy spikes for you.';
        window.voiceCoach.speak(msg, { force: true });
      });
    }
  }

  startLiveGamePolling() {
    this.igWaitingEl = document.getElementById('ingame-waiting');
    this.igActiveEl = document.getElementById('ingame-active');
    this.igTimeEl = document.getElementById('ig-time');
    this.igChampEl = document.getElementById('ig-champ');
    this.igCsEl = document.getElementById('ig-cs');
    this.igKdaEl = document.getElementById('ig-kda');
    this.igGoldEl = document.getElementById('ig-gold');
    this.igAlertsEl = document.getElementById('ig-alerts-list');
    this.igEnemiesEl = document.getElementById('ig-enemies-list');

    this.liveInGameWasActive = false;
    this.enemySpellTimers = {}; // key: "Champ_0" -> { endAt, champ, spellName }
    this.lastLiveEnemiesKey = '';
    this.lastLiveScoutKey = '';
    this.lastLiveState = null;

    document.getElementById('btn-rescout-live')?.addEventListener('click', () => {
      if (this.lastLiveState) {
        this.lastLiveScoutKey = '';
        this.runLiveMatchScout(this.lastLiveState, true);
      }
    });

    const pollLive = async () => {
      try {
        const curLang = typeof getCurrentLang === 'function' ? getCurrentLang() : 'es';
        const isEnLive = curLang !== 'es';
        const res = await fetch(`/api/live-game?lang=${encodeURIComponent(curLang)}`);
        if (!res.ok) return;
        const state = await res.json();

        if (!state.in_game) {
          if (this.liveInGameWasActive) {
            this.liveInGameWasActive = false;
            this.enemySpellTimers = {};
            this.lastLiveEnemiesKey = '';
            this.lastLiveScoutKey = '';
            this.lastLiveState = null;

            // Generar y abrir automáticamente el Resumen Post-Partida si duró >= 3 min
            const tr = this._matchTracker;
            if (tr && tr.durationSec >= 180) {
              const report = this.buildPostGameReport(tr);
              try {
                localStorage.setItem('noflash_last_match_report', JSON.stringify(report));
              } catch {}
              this._refreshLastReportBtn();
              this.openPostGameModal(report);
            } else {
              this.showToast(
                isEnLive
                  ? 'GG! Great match — take a 60s breather, grab some water, and queue up fresh.'
                  : '¡GG! Buena partida — tomate 60s, tomá agua y volvé fresco a la próxima.',
                'success'
              );
            }
            this._matchTracker = null;
          }
          if (this.igWaitingEl) this.igWaitingEl.style.display = 'block';
          if (this.igActiveEl) this.igActiveEl.style.display = 'none';
          return;
        }

        this.lastLiveState = state;
        const scoutKey = JSON.stringify(
          [...(state.allies || []), ...(state.enemies || [])].map(p => `${p.game_name}#${p.tag_line}:${p.champion}`)
        );
        if (scoutKey && scoutKey !== '[]' && scoutKey !== this.lastLiveScoutKey) {
          this.lastLiveScoutKey = scoutKey;
          this.runLiveMatchScout(state, false);
        }

        if (!this.liveInGameWasActive) {
          this.liveInGameWasActive = true;
          this.switchView('ingame');
          window.uiSfx?.playLockIn();
          this.showToast(isEnLive ? 'Live match detected! Activating In-Game Coach.' : '¡Partida en vivo detectada! Activando Coach In-Game.', 'success');
          if (window.voiceCoach) {
            window.voiceCoach.speak(isEnLive ? 'Match detected. Good luck on the Rift.' : 'Partida detectada. Mucha suerte en la Grieta.', { dedupeId: 'game_start' });
          }
        }

        if (this.igWaitingEl) this.igWaitingEl.style.display = 'none';
        if (this.igActiveEl) this.igActiveEl.style.display = 'block';

        const ap = state.active_player || {};
        if (this.igTimeEl) this.igTimeEl.textContent = state.game_time_formatted || '00:00';
        if (this.igChampEl) this.igChampEl.textContent = displayName(ap.champion || '—');
        if (this.igCsEl) this.igCsEl.textContent = `${ap.cs_per_min ?? 0} (${ap.cs ?? 0})`;
        if (this.igKdaEl) this.igKdaEl.textContent = ap.kda || '0/0/0';
        if (this.igGoldEl) this.igGoldEl.textContent = `${ap.current_gold ?? 0}g`;

        // Registrar telemetría en vivo para el Resumen Post-Partida (muertes con minuto y oro)
        this._recordLiveTelemetry(state, ap);

        // Render alertas + hablarlas una sola vez
        const alerts = state.alerts || [];
        if (this.igAlertsEl && alerts.length > 0) {
          this.igAlertsEl.innerHTML = alerts.map(a => `
            <div class="ig-alert-item ${a.type || ''}">
              <strong>${a.title}</strong>
              ${a.message}
            </div>
          `).join('');
          alerts.forEach(a => {
            if (window.voiceCoach) {
              window.voiceCoach.speak(a.message, { dedupeId: a.id });
            }
          });
        }

        // Render enemigos + botones de cooldown manual + Live Counter-Build Cheat Sheet
        const enemies = state.enemies || [];
        const enemiesKey = JSON.stringify(enemies.map(e => `${e.champion}_${e.level}`));
        if (enemies.length > 0) this.renderLiveCounterBuild(enemies);
        if (this.igEnemiesEl && enemiesKey !== this.lastLiveEnemiesKey) {
          this.lastLiveEnemiesKey = enemiesKey;
          this.igEnemiesEl.innerHTML = enemies.map(e => {
            const spellsHtml = (e.spells || []).map((sp, sIdx) => {
              const tKey = `${e.champion}_${sIdx}`;
              return `
                <button class="ig-spell-btn" data-tkey="${tKey}" data-champ="${e.champion}" data-spell="${sp.name}" data-cd="${sp.cooldown}" title="${sp.name} (${sp.cooldown}s) — Click al gastar">
                  <img src="${spellImgUrl(sp.name, sp.dd_key)}" alt="${sp.name}">
                  <span class="ig-spell-cd-overlay" id="cd-${tKey}"></span>
                </button>
              `;
            }).join('');

            return `
              <div class="ig-enemy-row">
                <div class="ig-enemy-info">
                  <img src="${champImgUrl(e.champion)}" alt="${displayName(e.champion)}" onerror="this.src='${champImgUrl('Aatrox')}'">
                  <div>
                    <div class="ig-enemy-name">${displayName(e.champion)}</div>
                    <div class="ig-enemy-lvl">${typeof t === 'function' ? t('lvl_prefix') : 'Nivel'} ${e.level}</div>
                  </div>
                </div>
                <div class="ig-enemy-spells">${spellsHtml}</div>
              </div>
            `;
          }).join('');

          this.igEnemiesEl.querySelectorAll('.ig-spell-btn').forEach(btn => {
            btn.addEventListener('click', () => {
              const tKey = btn.dataset.tkey;
              const cd = parseInt(btn.dataset.cd, 10) || 210;
              const champ = btn.dataset.champ;
              const spellName = btn.dataset.spell;
              if (this.enemySpellTimers[tKey]) {
                delete this.enemySpellTimers[tKey];
              } else {
                this.enemySpellTimers[tKey] = {
                  endAt: Date.now() + cd * 1000,
                  champ,
                  spellName,
                };
              }
              this._tickSpellTimers();
            });
          });
        }
      } catch {
        // Silencioso si no hay partida activa
      }
    };

    pollLive();
    setInterval(pollLive, 3000);
    setInterval(() => this._tickSpellTimers(), 1000);
    this.initHabitReminders();
    this.initPostGameReview();
  }

  /* ── Post-Game Match Review (telemetría en vivo + resumen automático al terminar) ── */
  initPostGameReview() {
    this._refreshLastReportBtn();
    document.getElementById('btn-open-last-report')?.addEventListener('click', () => {
      try {
        const raw = localStorage.getItem('noflash_last_match_report');
        if (raw) this.openPostGameModal(JSON.parse(raw));
      } catch {}
    });

    const modal = document.getElementById('postgame-modal');
    if (!modal || this._pgBound) return;
    this._pgBound = true;
    const close = () => { modal.style.display = 'none'; };
    document.getElementById('postgame-close')?.addEventListener('click', close);
    document.getElementById('pg-btn-done')?.addEventListener('click', close);
    modal.addEventListener('click', (e) => { if (e.target === modal) close(); });
    document.getElementById('pg-btn-reanalyze')?.addEventListener('click', () => {
      close();
      if (this.gameNameInput?.value.trim()) {
        this.analyzePlayer();
      } else {
        this.switchView('search');
      }
    });
  }

  _refreshLastReportBtn() {
    const btn = document.getElementById('btn-open-last-report');
    if (!btn) return;
    try {
      const has = !!localStorage.getItem('noflash_last_match_report');
      btn.style.display = has ? 'inline-flex' : 'none';
    } catch {
      btn.style.display = 'none';
    }
  }

  _recordLiveTelemetry(state, ap) {
    const gameSec = Number(state.game_time || 0);
    if (!this._matchTracker || gameSec < (this._matchTracker.durationSec - 30)) {
      this._matchTracker = {
        champion: ap.champion || 'Aatrox',
        role: (ap.position || state.my_position || '').toUpperCase(),
        durationSec: 0,
        durationStr: '00:00',
        kills: 0,
        deaths: 0,
        assists: 0,
        cs: 0,
        csPerMin: 0,
        peakGold: 0,
        deathsLog: [],
        lastDeaths: 0,
        finishedAt: Date.now(),
      };
    }

    const tr = this._matchTracker;
    const parts = String(ap.kda || '0/0/0').split('/').map(n => parseInt(n, 10) || 0);
    const [k, d, a] = parts;
    const curGold = Math.round(Number(ap.current_gold || 0));

    if (d > tr.lastDeaths) {
      const diff = Math.min(3, d - tr.lastDeaths);
      for (let i = 0; i < diff; i++) {
        tr.deathsLog.push({
          timeSec: gameSec,
          timeStr: state.game_time_formatted || '00:00',
          phase: gameSec < 720 ? 'early' : gameSec < 1380 ? 'mid' : 'late',
          goldHeld: curGold,
          level: Number(ap.level || 1),
        });
      }
      tr.lastDeaths = d;
    }

    tr.champion = ap.champion || tr.champion;
    if (ap.position) tr.role = String(ap.position).toUpperCase();
    tr.durationSec = Math.max(tr.durationSec, gameSec);
    tr.durationStr = state.game_time_formatted || tr.durationStr;
    tr.kills = k;
    tr.deaths = d;
    tr.assists = a;
    tr.cs = Number(ap.cs || 0);
    tr.csPerMin = Number(ap.cs_per_min || 0);
    tr.peakGold = Math.max(tr.peakGold, curGold);
    tr.finishedAt = Date.now();
  }

  buildPostGameReport(tr) {
    const isEn = typeof getCurrentLang === 'function' && getCurrentLang() !== 'es';
    const isSup = tr.role === 'UTILITY' || tr.role === 'SUP' || tr.role === 'SUPPORT';
    const kdaNum = (tr.kills + tr.assists) / Math.max(1, tr.deaths);
    const deathsPer10 = tr.deaths / Math.max(0.5, tr.durationSec / 600);
    const greedyDeaths = tr.deathsLog.filter(x => x.goldHeld >= 1200);
    const earlyDeaths = tr.deathsLog.filter(x => x.phase === 'early');
    const lateDeaths = tr.deathsLog.filter(x => x.phase === 'late');

    // Score & Grade (S+, S, A, B, C)
    let pts = 65;
    if (kdaNum >= 4.5) pts += 18;
    else if (kdaNum >= 3.0) pts += 10;
    else if (kdaNum < 1.5) pts -= 14;
    if (tr.deaths <= 2) pts += 12;
    else if (tr.deaths <= 4) pts += 5;
    else if (tr.deaths >= 7) pts -= 15;
    if (!isSup) {
      if (tr.csPerMin >= 7.5) pts += 12;
      else if (tr.csPerMin >= 6.5) pts += 6;
      else if (tr.csPerMin < 5.2) pts -= 10;
    }
    if (greedyDeaths.length >= 2) pts -= 6;
    const grade = pts >= 92 ? 'S+' : pts >= 82 ? 'S' : pts >= 70 ? 'A' : pts >= 56 ? 'B' : 'C';

    const good = [];
    const fix = [];

    // Strengths
    if (tr.deaths === 0) {
      good.push(isEn ? 'Deathless game (0 deaths) — you never gave away shutdowns or tempo.' : 'Partida sin muertes (0 muertes) — nunca regalaste bounty ni tempo.');
    } else if (tr.deaths <= 3) {
      good.push(isEn ? `Disciplined survival (only ${tr.deaths} deaths in ${tr.durationStr}).` : `Muy buena supervivencia (solo ${tr.deaths} muertes en ${tr.durationStr}).`);
    }
    if (kdaNum >= 3.5) {
      good.push(isEn ? `High combat impact (${kdaNum.toFixed(1)} KDA — ${tr.kills}/${tr.deaths}/${tr.assists}).` : `Alto impacto en peleas (${kdaNum.toFixed(1)} KDA — ${tr.kills}/${tr.deaths}/${tr.assists}).`);
    }
    if (!isSup && tr.csPerMin >= 7.0) {
      good.push(isEn ? `Strong gold income (${tr.csPerMin} CS/min · ${tr.cs} total CS).` : `Excelente farmeo (${tr.csPerMin} CS/min · ${tr.cs} CS totales).`);
    }
    if (greedyDeaths.length === 0 && tr.peakGold < 2300) {
      good.push(isEn ? 'Clean recall tempo — you spent your gold before major fights.' : 'Buen tempo de backs — gastaste tu oro antes de pelear.');
    }
    if (good.length === 0) {
      good.push(isEn ? `Stayed active through ${tr.durationStr} (${tr.kills + tr.assists} takedowns).` : `Te mantuviste activo durante ${tr.durationStr} (${tr.kills + tr.assists} participaciones).`);
    }

    // Fixes
    if (greedyDeaths.length > 0) {
      fix.push(
        isEn
          ? `You died ${greedyDeaths.length}x holding 1,200g+ unspent — recall before forcing fights.`
          : `Moriste ${greedyDeaths.length} vez/veces con +1,200g sin gastar — backeá antes de forzar pelea.`
      );
    }
    if (earlyDeaths.length >= 2) {
      fix.push(
        isEn
          ? `${earlyDeaths.length} early deaths before 12:00 — track enemy jungle & respect Lv3/Lv6 spikes.`
          : `${earlyDeaths.length} muertes tempranas antes del min 12 — respetá los spikes de Lv3/Lv6 y al jungla rival.`
      );
    }
    if (lateDeaths.length >= 2) {
      fix.push(
        isEn
          ? `${lateDeaths.length} late-game deaths (after 23:00) — stay grouped and hold Flash for objectives.`
          : `${lateDeaths.length} muertes en late (después del min 23) — jugá pegado al equipo y guardá Flash para objetivos.`
      );
    }
    if (!isSup && tr.csPerMin < 6.2) {
      fix.push(
        isEn
          ? `Farm was ${tr.csPerMin} CS/min — aim for 6.5–7.5+ by catching side waves between fights.`
          : `Tu farm fue ${tr.csPerMin} CS/min — buscá llegar a 6.5–7.5+ limpiando oleadas entre peleas.`
      );
    }
    if (tr.peakGold >= 2400) {
      fix.push(
        isEn
          ? `Peak unspent gold reached ${tr.peakGold}g — sitting on a full item weakens your spikes.`
          : `Llegaste a tener ${tr.peakGold}g sin gastar en mano — no tardes tanto en comprar tu ítem.`
      );
    }
    if (deathsPer10 >= 2.2 && fix.length < 4) {
      fix.push(
        isEn
          ? `High death rate (${tr.deaths} deaths) — avoid trading 1-for-1 when ahead or without vision.`
          : `Muchas muertes (${tr.deaths}) — evitá tradear 1 por 1 sin visión o cuando tenés ventaja.`
      );
    }
    if (fix.length === 0) {
      fix.push(isEn ? 'Keep pushing your tempo lead into Dragons, Grubs, and towers faster.' : 'Seguí convirtiendo tu ventaja en Dragones, Grubs y torres más rápido.');
    }

    return {
      champion: tr.champion,
      role: tr.role || 'FLEX',
      durationStr: tr.durationStr,
      kdaStr: `${tr.kills} / ${tr.deaths} / ${tr.assists}`,
      kdaNum: kdaNum.toFixed(1),
      cs: tr.cs,
      csPerMin: tr.csPerMin,
      deaths: tr.deaths,
      peakGold: tr.peakGold,
      grade,
      good,
      fix,
      deathsLog: tr.deathsLog,
    };
  }

  openPostGameModal(report) {
    const modal = document.getElementById('postgame-modal');
    if (!modal || !report) return;
    const isEn = typeof getCurrentLang === 'function' && getCurrentLang() !== 'es';

    document.getElementById('pg-champ-icon').src = champImgUrl(report.champion);
    document.getElementById('pg-title').textContent = `${displayName(report.champion)} — ${isEn ? 'Match Summary' : 'Resumen de tu Partida'}`;
    document.getElementById('pg-sub').textContent = `${report.role} · ${report.durationStr} · ${report.kdaStr}`;

    const gradeEl = document.getElementById('pg-grade');
    gradeEl.textContent = report.grade;
    gradeEl.className = `pg-grade-badge grade-${report.grade.replace('+', 'plus').toLowerCase()}`;

    document.getElementById('pg-stats-strip').innerHTML = `
      <div class="pg-stat"><span>KDA</span><strong>${report.kdaStr}</strong><small>${report.kdaNum} ratio</small></div>
      <div class="pg-stat"><span>CS</span><strong>${report.cs}</strong><small>${report.csPerMin} / min</small></div>
      <div class="pg-stat"><span>${isEn ? 'Deaths' : 'Muertes'}</span><strong>${report.deaths}</strong><small>${report.deaths <= 3 ? 'Clean' : 'Focus'}</small></div>
      <div class="pg-stat"><span>${isEn ? 'Peak Unspent' : 'Oro Máx.'}</span><strong>${report.peakGold}g</strong><small>${report.peakGold >= 2200 ? 'Back sooner' : 'Good tempo'}</small></div>
    `;

    document.getElementById('pg-good-title').textContent = isEn ? 'What You Did Well' : 'Lo que hiciste bien';
    document.getElementById('pg-fix-title').textContent = isEn ? 'Things To Fix Next Game' : 'Cosas a corregir';
    document.getElementById('pg-deaths-title').textContent = isEn
      ? `Your Deaths Breakdown (${report.deaths})`
      : `Detalle de tus Muertes (${report.deaths})`;

    document.getElementById('pg-good-list').innerHTML = (report.good || []).map(x => `<li>${x}</li>`).join('');
    document.getElementById('pg-fix-list').innerHTML = (report.fix || []).map(x => `<li>${x}</li>`).join('');

    const deathsEl = document.getElementById('pg-deaths-list');
    if (!report.deathsLog || report.deathsLog.length === 0) {
      deathsEl.innerHTML = `<div class="pg-death-zero">🏆 ${isEn ? 'Deathless match! Zero deaths recorded.' : '¡Partida perfecta sin muertes!'}</div>`;
    } else {
      deathsEl.innerHTML = report.deathsLog.map((d, i) => {
        const phaseLbl = d.phase === 'early'
          ? (isEn ? 'Early Lane' : 'Early')
          : d.phase === 'mid'
            ? 'Mid Game'
            : (isEn ? 'Late / Objectives' : 'Late / Objetivos');
        const tip = d.goldHeld >= 1200
          ? (isEn ? `Holding ${d.goldHeld}g unspent — recall before fighting.` : `Tenías ${d.goldHeld}g sin gastar — backeá antes de pelear.`)
          : d.phase === 'early'
            ? (isEn ? 'Check enemy jungle/spikes before trading.' : 'Chequeá jungla rival y spikes antes de tradear.')
            : d.phase === 'late'
              ? (isEn ? 'High death timer — stay behind frontline.' : 'Timer largo en late — cuidá el posicionamiento.')
              : (isEn ? 'Verify river vision before extending.' : 'Revisá visión del río antes de avanzar.');
        return `
          <div class="pg-death-row">
            <span class="pg-death-num">#${i + 1}</span>
            <span class="pg-death-time">${d.timeStr}</span>
            <span class="pg-death-phase ${d.phase}">${phaseLbl} · Lv${d.level}</span>
            <span class="pg-death-tip">${tip}</span>
          </div>
        `;
      }).join('');
    }

    modal.style.display = 'flex';
    window.uiSfx?.playSuccess();
  }

  /* ── Custom In-Game Voice Habit Reminders (Minimap, Wards, Tempo, Mental, Custom) ── */
  initHabitReminders() {
    const listEl = document.getElementById('habit-list');
    if (!listEl) return;

    const STORAGE_KEY = 'NoFlash_habit_reminders_v2';
    const DIALOGUES = {
      situational: {
        en: ['You have over 1800 gold — look for a clean recall.', 'Objective spawning soon — prep river vision.'],
        es: ['Tenés más de 1800 de oro — buscá un buen back.', 'Objetivo en breve — prepará visión en el río.'],
      },
      minimap: {
        en: ['Minimap check.', 'Quick map glance.', 'Check minimap.'],
        es: ['Chequeo de mapa.', 'Mirá el minimapa.', 'Ojo al mapa.'],
      },
      wards: {
        en: ['Check your wards.', 'Drop river vision.', 'Ward before pushing.'],
        es: ['Revisá tus wards.', 'Visión en el río.'],
      },
      tempo: {
        en: ['Check your gold.', 'Look for a clean reset.', 'Crash wave before reset.'],
        es: ['Revisá tu oro.', 'Buscá un buen back.'],
      },
      water: {
        en: ['Take a quick sip of water.', 'Hydration check — drink some water.'],
        es: ['Tomá un sorbo de agua.', 'Recordatorio: hidratate un poco.'],
      },
      mental: {
        en: ['Deep breath. Stay focused.', 'Calm reset. Next wave clean.'],
        es: ['Respirá hondo. Mantené el foco.', 'Calma y a jugar limpio.'],
      },
    };

    const defaults = {
      situational: { enabled: true, interval: 1800 }, // interval = umbral de oro (1500/1800/2200/2600g)
      minimap: { enabled: false, interval: 60 },
      wards: { enabled: false, interval: 120 },
      tempo: { enabled: false, interval: 180 },
      water: { enabled: false, interval: 600 },
      mental: { enabled: false, interval: 300 },
      custom: { enabled: false, interval: 90, text: '' },
    };

    let cfg = defaults;
    try {
      const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || 'null');
      if (saved) cfg = { ...defaults, ...saved };
    } catch {}
    this.habitCfg = cfg;

    const saveCfg = () => {
      try { localStorage.setItem(STORAGE_KEY, JSON.stringify(cfg)); } catch {}
    };

    const lastFired = {};
    const dialogueIdx = {};
    const getPhrase = (key) => {
      const lang = (typeof getCurrentLang === 'function' && getCurrentLang() === 'es') ? 'es' : 'en';
      if (key === 'custom') {
        const txt = (cfg.custom?.text || '').trim();
        return txt || (lang === 'es' ? 'Recordatorio personalizado de No Flash.' : 'Custom No Flash reminder.');
      }
      const arr = (DIALOGUES[key] && DIALOGUES[key][lang]) || DIALOGUES[key]?.en || [];
      if (arr.length === 0) return '';
      const i = (dialogueIdx[key] || 0) % arr.length;
      dialogueIdx[key] = i + 1;
      return arr[i];
    };

    const customInput = document.getElementById('habit-custom-text');
    if (customInput) {
      customInput.value = cfg.custom?.text || '';
      customInput.addEventListener('input', () => {
        cfg.custom.text = customInput.value;
        saveCfg();
      });
    }

    listEl.querySelectorAll('.habit-row').forEach(row => {
      const key = row.dataset.habit;
      const cb = row.querySelector('.habit-cb');
      const sel = row.querySelector('.habit-interval');
      const testBtn = row.querySelector('.btn-habit-test');
      if (!key || !cfg[key]) return;

      if (cb) {
        cb.checked = !!cfg[key].enabled;
        cb.addEventListener('change', () => {
          cfg[key].enabled = cb.checked;
          lastFired[key] = Date.now();
          saveCfg();
        });
      }
      if (sel) {
        sel.value = String(cfg[key].interval || 60);
        sel.addEventListener('change', () => {
          cfg[key].interval = parseInt(sel.value, 10) || 60;
          lastFired[key] = Date.now();
          saveCfg();
        });
      }
      if (testBtn) {
        testBtn.addEventListener('click', () => {
          const phrase = getPhrase(key);
          if (phrase && window.voiceCoach) {
            window.voiceCoach.speak(phrase, { force: true });
          }
        });
      }
    });

    // Solo dispara recordatorios mientras hay una partida de LoL activa (min > 1:30)
    setInterval(() => {
      if (!this.liveInGameWasActive || !window.voiceCoach || !window.voiceCoach.isEnabled()) return;
      const gTime = this.lastLiveState?.game_time || 0;
      if (gTime < 90) return;

      const now = Date.now();
      // Situational High-Gold Trigger (basado en gameplay real, no reloj fijo, máx 1 vez cada 3.5 min)
      if (cfg.situational?.enabled) {
        const goldThresh = Number(cfg.situational.interval) || 1800;
        const curGold = Number(this.lastLiveState?.active_player?.current_gold || 0);
        if (curGold >= goldThresh && gTime >= 240 && (!lastFired.situational_gold || now - lastFired.situational_gold >= 210000)) {
          lastFired.situational_gold = now;
          const isEs = typeof getCurrentLang === 'function' && getCurrentLang() === 'es';
          const gMsg = isEs
            ? `Tenés ${curGold} de oro sin gastar — buscá un buen back.`
            : `You have ${curGold} unspent gold — look for a clean recall.`;
          window.voiceCoach.speak(gMsg, { force: false });
          return;
        }
      }

      for (const key of ['minimap', 'wards', 'tempo', 'water', 'mental', 'custom']) {
        const item = cfg[key];
        if (!item || !item.enabled) continue;
        if (key === 'custom' && !(item.text || '').trim()) continue;
        const intervalMs = Math.max(30, Number(item.interval) || 60) * 1000;
        if (!lastFired[key]) {
          lastFired[key] = now;
          continue;
        }
        if (now - lastFired[key] >= intervalMs) {
          lastFired[key] = now;
          const phrase = getPhrase(key);
          if (phrase) {
            window.voiceCoach.speak(phrase, { force: false });
          }
          break; // Máximo 1 recordatorio por ciclo para no pisarse
        }
      }
    }, 5000);
  }

  /* ── U.GG / Blitz-style Live Counter-Build & Boots Cheat Sheet ── */
  renderLiveCounterBuild(enemies) {
    const card = document.getElementById('ig-build-card');
    const grid = document.getElementById('ig-build-grid');
    if (!card || !grid || !enemies || enemies.length === 0) return;

    const norms = enemies.map(e => normalizeChampionId(e.champion).toLowerCase());
    const key = norms.join(',');
    if (this._lastBuildKey === key) return;
    this._lastBuildKey = key;

    const isEn = typeof getCurrentLang === 'function' ? getCurrentLang() !== 'es' : true;
    const itemUrl = (id) => `https://ddragon.leagueoflegends.com/cdn/16.23.1/img/item/${id}.png`;

    const HEALERS = new Set(['soraka','aatrox','vladimir','sylas','warwick','briar','drmundo','swain','yuumi','sona','nami','fiora','irelia','olaf','redkayn','kayn','zac']);
    const TANKS = new Set(['malphite','ornn','sejuani','rammus','sion','nautilus','leona','braum','alistar','zac','maokai','ksante','tahmkench','drmundo','chogath','amumu','rell','skarner','poppy','shen']);
    const ASSASSINS = new Set(['zed','fizz','talon','rengar','khazix','evelynn','diana','akali','katarina','nocturne','vi','qiyana','naafiri','ekko','shaco','bluekayn','kayn']);
    const HARD_CC = new Set(['malzahar','mordekaiser','ashe','leona','nautilus','lissandra','amumu','skarner','morgana','thresh','sejuani','annie','twistedfate','warwick','vi']);
    const AP_CHAMPS = new Set(['ahri','lux','syndra','orianna','viktor','vladimir','diana','fizz','akali','katarina','evelynn','brand','zyra','xerath','velkoz','hwei','cassiopeia','ryze','anivia','veigar','malzahar','swain','karthus','taliyah','aurora','mel']);

    const healCnt = norms.filter(c => HEALERS.has(c)).length;
    const tankCnt = norms.filter(c => TANKS.has(c)).length;
    const assCnt = norms.filter(c => ASSASSINS.has(c)).length;
    const ccCnt = norms.filter(c => HARD_CC.has(c)).length;
    const apCnt = norms.filter(c => AP_CHAMPS.has(c)).length;

    const recs = [];
    // 1. Botas recomendadas
    if (ccCnt >= 2 || apCnt >= 3) {
      recs.push({ id: 3111, name: "Mercury's Treads", reason: isEn ? `Heavy CC/AP (${ccCnt} CC, ${apCnt} AP)` : `Mucho CC/AP rival` });
    } else if (apCnt <= 1) {
      recs.push({ id: 3047, name: 'Plated Steelcaps', reason: isEn ? 'Heavy AD enemy team' : 'Equipo rival muy AD' });
    } else {
      recs.push({ id: 3006, name: 'Offensive Boots', reason: isEn ? 'Balanced enemy damage' : 'Daño rival mixto' });
    }

    // 2. Situacionales clave
    if (healCnt >= 2) {
      recs.push({ id: 3123, name: isEn ? 'Anti-Heal (800g)' : 'Cortacuras (800g)', reason: isEn ? `${healCnt} enemy healers — buy early!` : `${healCnt} curadores rivales` });
    }
    if (tankCnt >= 2) {
      recs.push({ id: 3036, name: isEn ? '% Armor / Magic Pen' : 'Penetración %', reason: isEn ? `${tankCnt} frontline tanks` : `${tankCnt} tanques rivales` });
    }
    if (assCnt >= 2) {
      recs.push({ id: 3157, name: "Zhonya's / GA", reason: isEn ? `${assCnt} assassins/divers` : `${assCnt} asesinos rivales` });
    }
    if (ccCnt >= 2) {
      recs.push({ id: 3140, name: 'Quicksilver Sash', reason: isEn ? 'Key cleanse vs lockdown CC' : 'Clave contra CC fuerte' });
    }

    grid.innerHTML = recs.slice(0, 4).map(r => `
      <div class="ig-build-chip">
        <img src="${itemUrl(r.id)}" alt="${r.name}">
        <div>
          <strong>${r.name}</strong>
          <span>${r.reason}</span>
        </div>
      </div>
    `).join('');
    card.style.display = 'block';
  }

  /* ── Scouting en vivo de los 10 jugadores (Aliados + Rivales) ── */
  async runLiveMatchScout(liveState, manualTrigger = false) {
    const gridEl = document.getElementById('ig-scout-grid');
    const summaryEl = document.getElementById('ig-scout-summary');
    if (!gridEl) return;

    const curLang = typeof getCurrentLang === 'function' ? getCurrentLang() : 'es';
    const isEn = curLang !== 'es';
    const platform = this.platformSelect?.value
      || this.lcuLastSummoner?.platform
      || 'la2';

    const players = [
      ...(liveState.allies || []).map(p => ({
        game_name: p.game_name || '',
        tag_line: p.tag_line || '',
        champion: p.champion || '',
        team_side: 'ally',
        position: p.position || '',
        is_me: !!p.is_me,
      })),
      ...(liveState.enemies || []).map(p => ({
        game_name: p.game_name || '',
        tag_line: p.tag_line || '',
        champion: p.champion || '',
        team_side: 'enemy',
        position: p.position || '',
        is_me: false,
      })),
    ];

    if (players.length === 0) return;

    gridEl.innerHTML = `<p class="coach-muted" style="grid-column:1/-1;text-align:center;padding:1rem;">${isEn ? 'Scouting all 10 players in this match...' : 'Analizando a los 10 jugadores de la partida...'}</p>`;
    if (summaryEl) summaryEl.style.display = 'none';

    try {
      const res = await fetch('/api/live-scout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ platform, lang: curLang, players }),
      });
      if (!res.ok) throw new Error('Scout API error');
      const data = await res.json();
      if (!data.success) return;

      const s = data.summary || {};
      if (summaryEl && (s.key_threat || s.camp_target)) {
        const threat = s.key_threat;
        const target = s.camp_target;
        const formatRank = (p) => p && p.tier && p.tier !== 'UNRANKED'
          ? `${p.tier} ${p.rank} (${p.lp} LP)` : 'Unranked';
        summaryEl.innerHTML = `
          ${threat ? `<div class="scout-callout threat"><strong>⚠️ ${isEn ? 'Main Threat' : 'Amenaza Principal'}:</strong> ${displayName(threat.champion)} (${threat.game_name}) · ${formatRank(threat)}${threat.win_rate != null ? ` · ${threat.win_rate}% WR` : ''}</div>` : ''}
          ${target && (!threat || target.champion !== threat.champion) ? `<div class="scout-callout target"><strong>🎯 ${isEn ? 'Best Target to Punish' : 'Mejor Target para Castigar'}:</strong> ${displayName(target.champion)} (${target.game_name}) · ${formatRank(target)}${target.win_rate != null ? ` · ${target.win_rate}% WR` : ''}</div>` : ''}
        `;
        summaryEl.style.display = 'grid';
      }

      if (s.voice_summary && window.voiceCoach && !manualTrigger) {
        window.voiceCoach.speak(s.voice_summary, { dedupeId: `scout_${this.lastLiveScoutKey}` });
      }

      const renderPlayerRow = (p) => {
        const rankTxt = p.tier && p.tier !== 'UNRANKED'
          ? `${p.tier} ${p.rank} · ${p.lp} LP`
          : 'Unranked';
        const wrTxt = p.win_rate != null
          ? `<span class="scout-wr ${p.win_rate >= 54 ? 'high' : p.win_rate <= 46 ? 'low' : ''}">${p.win_rate}% WR</span> <span class="scout-games">(${p.games}G)</span>`
          : `<span class="scout-games">—</span>`;
        const ptsTxt = p.mastery_points >= 1000
          ? `M${p.mastery_level} · ${Math.round(p.mastery_points / 1000)}k`
          : (p.mastery_level > 0 ? `M${p.mastery_level}` : (isEn ? 'New' : 'Nuevo'));
        const tagsHtml = (p.tags || []).map(tg => `<span class="scout-tag ${tg.cls}">${tg.text}</span>`).join('');
        return `
          <div class="scout-row ${p.is_me ? 'is-me' : ''}">
            <img src="${champImgUrl(p.champion)}" alt="${displayName(p.champion)}" class="scout-avatar" onerror="this.src='${champImgUrl('Aatrox')}'">
            <div class="scout-info">
              <div class="scout-top-line">
                <span class="scout-champ">${displayName(p.champion)}</span>
                <span class="scout-name">${p.game_name || '—'}${p.is_me ? (isEn ? ' (You)' : ' (Vos)') : ''}</span>
              </div>
              <div class="scout-meta-line">
                <span class="scout-rank">${rankTxt}</span>
                <span>·</span>
                ${wrTxt}
                <span>·</span>
                <span class="scout-mastery">${ptsTxt}</span>
              </div>
              ${tagsHtml ? `<div class="scout-tags">${tagsHtml}</div>` : ''}
            </div>
          </div>
        `;
      };

      const allyAvg = s.ally_avg_wr != null ? ` · ${isEn ? 'Avg' : 'Prom'} ${s.ally_avg_wr}% WR` : '';
      const enemyAvg = s.enemy_avg_wr != null ? ` · ${isEn ? 'Avg' : 'Prom'} ${s.enemy_avg_wr}% WR` : '';

      gridEl.innerHTML = `
        <div class="scout-col ally-col">
          <div class="scout-col-title ally">🔵 ${isEn ? 'ALLIES' : 'ALIADOS'}${allyAvg}</div>
          ${(data.allies || []).map(renderPlayerRow).join('')}
        </div>
        <div class="scout-col enemy-col">
          <div class="scout-col-title enemy">🔴 ${isEn ? 'ENEMIES' : 'RIVALES'}${enemyAvg}</div>
          ${(data.enemies || []).map(renderPlayerRow).join('')}
        </div>
      `;
    } catch {
      gridEl.innerHTML = `<p class="coach-muted" style="grid-column:1/-1;text-align:center;padding:1rem;">${isEn ? 'Could not scout players right now (check Riot API key or click Rescout).' : 'No se pudo completar el scouting ahora (revisá tu API key o tocá Re-escanear).'}</p>`;
    }
  }

  _tickSpellTimers() {
    const now = Date.now();
    for (const [tKey, timer] of Object.entries(this.enemySpellTimers)) {
      const rem = Math.ceil((timer.endAt - now) / 1000);
      const overlay = document.getElementById(`cd-${tKey}`);
      const btn = overlay ? overlay.closest('.ig-spell-btn') : null;
      if (rem <= 0) {
        delete this.enemySpellTimers[tKey];
        if (overlay) overlay.textContent = '';
        if (btn) btn.classList.remove('on-cd');
        if (window.voiceCoach) {
          const spClean = timer.spellName.split('(')[0].trim();
          const isEnSp = typeof getCurrentLang === 'function' && getCurrentLang() !== 'es';
          window.voiceCoach.speak(isEnSp ? `${displayName(timer.champ)}'s ${spClean} is back up.` : `${spClean} de ${displayName(timer.champ)} volvió.`, { force: false });
        }
      } else {
        const mins = Math.floor(rem / 60);
        const secs = String(rem % 60).padStart(2, '0');
        if (overlay) overlay.textContent = `${mins}:${secs}`;
        if (btn) btn.classList.add('on-cd');
      }
    }
  }

  /* ── Botones nativos de escritorio (Siempre encima + Auto-abrir con LoL + HUD Flotante) ── */
  initDesktopPinButton() {
    const toggleHud = async () => {
      const isEnDesk = () => typeof getCurrentLang === 'function' && getCurrentLang() !== 'es';
      const btnHud = document.getElementById('btn-hud-overlay');
      if (window.pywebview?.api?.toggle_overlay) {
        try {
          const isOpen = await window.pywebview.api.toggle_overlay();
          if (btnHud) btnHud.classList.toggle('connected', isOpen);
          this.showToast(
            isOpen
              ? (isEnDesk()
                ? 'Floating Flash HUD active! Use LoL Borderless mode to see it over the game.'
                : '¡HUD flotante activado! Usá LoL en modo Sin bordes para verlo arriba del juego.')
              : (isEnDesk() ? 'Floating Flash HUD closed.' : 'HUD flotante cerrado.'),
            'info'
          );
        } catch (err) {
          console.error('Error toggling HUD overlay:', err);
        }
      } else {
        window.open('/overlay', 'NoFlashHUD', 'width=168,height=228,menubar=no,toolbar=no,location=no,status=no');
      }
    };

    document.getElementById('btn-ingame-hud')?.addEventListener('click', toggleHud);

    const setupDesktop = async () => {
      if (!window.pywebview || !window.pywebview.api) return;
      const isEnDesk = () => typeof getCurrentLang === 'function' && getCurrentLang() !== 'es';

      const btnHud = document.getElementById('btn-hud-overlay');
      if (btnHud && typeof window.pywebview.api.toggle_overlay === 'function') {
        btnHud.style.display = 'inline-flex';
        btnHud.addEventListener('click', toggleHud);
      }

      if (this.btnPinWindow) {
        this.btnPinWindow.style.display = 'inline-flex';
        this.btnPinWindow.addEventListener('click', async () => {
          try {
            const isOnTop = await window.pywebview.api.toggle_on_top();
            this.btnPinWindow.classList.toggle('connected', isOnTop);
            this.showToast(
              isOnTop
                ? (isEnDesk() ? 'Window pinned Always-on-Top.' : 'Ventana fijada siempre encima del LoL.')
                : (isEnDesk() ? 'Window set to normal mode.' : 'Ventana en modo normal.'),
              'info'
            );
          } catch (err) {
            console.error('Error toggling always-on-top:', err);
          }
        });
      }

      const winControls = document.getElementById('win-controls');
      if (winControls && typeof window.pywebview.api.win_close === 'function') {
        winControls.style.display = 'flex';
        document.getElementById('btn-win-min')?.addEventListener('click', () => window.pywebview.api.win_minimize());
        document.getElementById('btn-win-max')?.addEventListener('click', () => window.pywebview.api.win_toggle_maximize());
        document.getElementById('btn-win-close')?.addEventListener('click', () => window.pywebview.api.win_close());
      }

      const btnAutoLol = document.getElementById('btn-auto-lol');
      if (btnAutoLol && typeof window.pywebview.api.get_auto_launch === 'function') {
        btnAutoLol.style.display = 'inline-flex';
        try {
          const enabled = await window.pywebview.api.get_auto_launch();
          btnAutoLol.classList.toggle('connected', !!enabled);
        } catch {}

        btnAutoLol.addEventListener('click', async () => {
          try {
            const nowEnabled = await window.pywebview.api.toggle_auto_launch();
            btnAutoLol.classList.toggle('connected', !!nowEnabled);
            this.showToast(
              nowEnabled
                ? (isEnDesk() ? 'Auto-open with LoL enabled! NoFlash will launch automatically when you open League.' : '¡Auto-abrir con LoL activado! NoFlash se abrirá solo cuando inicies League of Legends.')
                : (isEnDesk() ? 'Auto-open with LoL disabled.' : 'Auto-abrir con LoL desactivado.'),
              nowEnabled ? 'success' : 'info'
            );
          } catch (err) {
            console.error('Error toggling auto-launch:', err);
          }
        });
      }
    };

    if (window.pywebview) {
      setupDesktop();
    } else {
      window.addEventListener('pywebviewready', setupDesktop);
    }
  }

  /* ── Refrescar análisis en el nuevo idioma desde el caché local (~1s) ── */
  async refreshPlayerLanguage() {
    const gameName = this.gameNameInput.value.trim();
    const tagLine = this.tagLineInput.value.trim();
    const region = this.regionSelect.value;
    const platform = this.platformSelect.value;
    if (!gameName || !tagLine || !region || !platform) return;
    try {
      const res = await fetch('/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          game_name: gameName,
          tag_line: tagLine,
          region,
          platform,
          lang: typeof getCurrentLang === 'function' ? getCurrentLang() : 'es',
        }),
      });
      if (!res.ok) return;
      const data = await res.json();
      this.state.playerData = data;
      this.renderPlayerSummary(data);
      this.renderChampionPool(data);
      const activeRoleTab = document.querySelector('#role-tabs .role-tab.active');
      if (activeRoleTab) this.renderRoleChampions(activeRoleTab.dataset.role);
      this.updateDraft();
    } catch {
      // Silencioso
    }
  }

  /* ── Search champion by query (utility) ── */
  searchChampion(query) {
    const q = query.toLowerCase().trim();
    if (!q) return this.state.championList;
    return this.state.championList.filter(c =>
      (c.name || '').toLowerCase().includes(q) ||
      displayName(c.name).toLowerCase().includes(q)
    );
  }
}

/* ══════════════════════════════════════
   Boot
   ══════════════════════════════════════ */
document.addEventListener('DOMContentLoaded', () => {
  window.app = new DraftAnalyzer();

  // Inicializar selector de idioma (i18n)
  if (typeof applyLanguage === 'function') {
    applyLanguage(getCurrentLang());
    const langSelect = document.getElementById('lang-select');
    if (langSelect) {
      langSelect.addEventListener('change', (e) => {
        applyLanguage(e.target.value);
      });
    }
  }

  // Habilitar F5 para recargar en la app de escritorio (pywebview)
  window.addEventListener('keydown', (e) => {
    if (e.key === 'F5') {
      e.preventDefault();
      window.location.reload();
    }
  });
});
