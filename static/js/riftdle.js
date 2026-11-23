/* ═══════════════════════════════════════════════════════
   NoFlash — Riftdle (Mini-Juego interactivo estilo LoLdle)
   Para pasar el rato mientras esperás cola en LoL
   ═══════════════════════════════════════════════════════ */

class RiftdleGame {
  constructor() {
    this.champions = [];
    this.secret = null;
    this.guesses = [];
    this.won = false;
    this.hintUsed = false;
    this.streak = parseInt(localStorage.getItem('riftdle_streak') || '0', 10);

    this.inputEl = document.getElementById('riftdle-input');
    this.dropdownEl = document.getElementById('riftdle-dropdown');
    this.boardEl = document.getElementById('riftdle-board');
    this.streakEl = document.getElementById('riftdle-streak');
    this.hintBoxEl = document.getElementById('riftdle-hint-box');
    this.winBannerEl = document.getElementById('riftdle-win-banner');
    this.btnHint = document.getElementById('btn-riftdle-hint');
    this.btnNew = document.getElementById('btn-riftdle-new');

    if (!this.inputEl) return;
    this.bindEvents();
    this.loadAndStart();
  }

  async loadAndStart() {
    try {
      const res = await fetch('/api/champions');
      if (res.ok) {
        const data = await res.json();
        this.champions = (data.champions || []).filter(c => c.name && c.roles && c.roles.length > 0);
      }
    } catch {}
    if (this.champions.length > 0) {
      this.newRound();
    }
  }

  newRound() {
    if (this.champions.length === 0) return;
    this.secret = this.champions[Math.floor(Math.random() * this.champions.length)];
    this.guesses = [];
    this.won = false;
    this.hintUsed = false;

    if (this.inputEl) {
      this.inputEl.value = '';
      this.inputEl.disabled = false;
    }
    if (this.dropdownEl) this.dropdownEl.style.display = 'none';
    if (this.hintBoxEl) {
      this.hintBoxEl.style.display = 'none';
      this.hintBoxEl.textContent = '';
    }
    if (this.winBannerEl) this.winBannerEl.style.display = 'none';
    this.updateStreakUI();
    this.renderBoard();
  }

  updateStreakUI() {
    if (this.streakEl) {
      const isEn = typeof getCurrentLang === 'function' && getCurrentLang() !== 'es';
      this.streakEl.textContent = `🔥 ${isEn ? 'Streak' : 'Racha'}: ${this.streak}`;
    }
  }

  bindEvents() {
    this.inputEl.addEventListener('input', () => {
      const q = this.inputEl.value.trim().toLowerCase();
      if (!q || this.won) {
        this.dropdownEl.style.display = 'none';
        return;
      }
      const guessedNames = new Set(this.guesses.map(g => g.name));
      const matches = this.champions
        .filter(c => !guessedNames.has(c.name) && (
          c.name.toLowerCase().includes(q) ||
          displayName(c.name).toLowerCase().includes(q)
        ))
        .slice(0, 8);

      if (matches.length === 0) {
        this.dropdownEl.style.display = 'none';
        return;
      }
      this.dropdownEl.innerHTML = matches.map(c => `
        <div class="riftdle-opt" data-name="${c.name}">
          <img src="${champImgUrl(c.name)}" alt="${displayName(c.name)}">
          <span>${displayName(c.name)}</span>
        </div>
      `).join('');
      this.dropdownEl.style.display = 'flex';
    });

    this.inputEl.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        const first = this.dropdownEl.querySelector('.riftdle-opt');
        if (first) this.submitGuess(first.dataset.name);
      }
    });

    this.dropdownEl.addEventListener('click', (e) => {
      const opt = e.target.closest('.riftdle-opt');
      if (!opt) return;
      this.submitGuess(opt.dataset.name);
    });

    if (this.btnHint) {
      this.btnHint.addEventListener('click', () => {
        if (!this.secret || this.won) return;
        this.hintUsed = true;
        const isEn = typeof getCurrentLang === 'function' && getCurrentLang() !== 'es';
        const dName = displayName(this.secret.name);
        const firstLetter = dName[0];
        const roles = (this.secret.roles || []).map(r => r.toUpperCase()).join(' / ');
        this.hintBoxEl.textContent = isEn
          ? `💡 Hint: Starts with "${firstLetter}" · Main role: ${roles}`
          : `💡 Pista: Empieza con "${firstLetter}" · Rol principal: ${roles}`;
        this.hintBoxEl.style.display = 'block';
      });
    }

    if (this.btnNew) {
      this.btnNew.addEventListener('click', () => this.newRound());
    }
  }

  _compareArray(guessArr, secretArr) {
    const gSet = new Set((guessArr || []).map(x => x.toLowerCase()));
    const sSet = new Set((secretArr || []).map(x => x.toLowerCase()));
    if (gSet.size === sSet.size && [...gSet].every(x => sSet.has(x))) return 'exact';
    if ([...gSet].some(x => sSet.has(x))) return 'partial';
    return 'miss';
  }

  submitGuess(champName) {
    if (this.won || !this.secret) return;
    const champ = this.champions.find(c => c.name === champName);
    if (!champ) return;

    this.guesses.unshift(champ);
    this.inputEl.value = '';
    this.dropdownEl.style.display = 'none';

    if (champ.name === this.secret.name) {
      this.won = true;
      this.inputEl.disabled = true;
      this.streak += 1;
      localStorage.setItem('riftdle_streak', String(this.streak));
      this.updateStreakUI();
      this.showWinBanner();
    }
    this.renderBoard();
  }

  showWinBanner() {
    if (!this.winBannerEl || !this.secret) return;
    const isEn = typeof getCurrentLang === 'function' && getCurrentLang() !== 'es';
    const dName = displayName(this.secret.name);
    const tries = this.guesses.length;
    this.winBannerEl.style.backgroundImage = `url('https://ddragon.leagueoflegends.com/cdn/img/champion/splash/${this.secret.name}_0.jpg')`;
    this.winBannerEl.innerHTML = `
      <div class="riftdle-win-inner">
        <h4>🎉 ${isEn ? `You got it! It was ${dName}` : `¡Acertaste! Era ${dName}`}</h4>
        <p>${isEn ? `Solved in ${tries} ${tries === 1 ? 'try' : 'tries'}!` : `¡Resuelto en ${tries} ${tries === 1 ? 'intento' : 'intentos'}!`}</p>
        <button class="btn-analyze" id="btn-riftdle-again" style="max-width:200px;margin-top:0.5rem;">
          <i class="fa-solid fa-play"></i> ${isEn ? 'Play Again' : 'Jugar otra vez'}
        </button>
      </div>
    `;
    this.winBannerEl.style.display = 'block';
    const again = document.getElementById('btn-riftdle-again');
    if (again) again.addEventListener('click', () => this.newRound());
  }

  renderBoard() {
    if (!this.boardEl || !this.secret) return;
    if (this.guesses.length === 0) {
      const isEn = typeof getCurrentLang === 'function' && getCurrentLang() !== 'es';
      this.boardEl.innerHTML = `<p class="coach-muted" style="text-align:center;padding:1.25rem;">${isEn ? 'Type any champion above to start guessing!' : '¡Escribí cualquier campeón arriba para empezar a adivinar!'}</p>`;
      return;
    }

    this.boardEl.innerHTML = this.guesses.map(g => {
      const isExactChamp = g.name === this.secret.name ? 'exact' : 'miss';
      const roleMatch = this._compareArray(g.roles, this.secret.roles);
      const dmgMatch = (g.damage || '').toLowerCase() === (this.secret.damage || '').toLowerCase() ? 'exact' : 'miss';
      const classMatch = this._compareArray(g.class, this.secret.class);

      return `
        <div class="riftdle-row">
          <div class="rd-cell champ ${isExactChamp}">
            <img src="${champImgUrl(g.name)}" alt="${displayName(g.name)}">
            <span>${displayName(g.name)}</span>
          </div>
          <div class="rd-cell ${roleMatch}">${(g.roles || []).map(r => r.toUpperCase()).join(' / ')}</div>
          <div class="rd-cell ${dmgMatch}">${g.damage || '—'}</div>
          <div class="rd-cell ${classMatch}">${(g.class || []).join(' / ')}</div>
        </div>
      `;
    }).join('');
  }
}

document.addEventListener('DOMContentLoaded', () => {
  window.riftdle = new RiftdleGame();
});


/* ═══════════════════════════════════════════════════════
   MICRO WARM-UP (20s Aim & Reflexes) + MACRO/BUILDS QUIZ + IDLE POPUP
   ═══════════════════════════════════════════════════════ */

const QUIZ_BANK = [
  {
    cat: 'BUILD',
    es: {
      q: 'Jugás ADC (Jinx) contra Malphite, Rammus y Nautilus que ya cerraron ítems de armadura. ¿Cuál es tu mejor 3er ítem?',
      opts: ['Recuerdos de Lord Dominik (LDR)', 'Sanguinaria', 'Cañón de Fuego Rápido', 'Ángel Guardián'],
      ans: 0,
      exp: 'Contra múltiples tanques con armadura, penetración porcentual (LDR o Recordatorio Mortal) multiplica tu DPS mucho más que cualquier otro ítem.',
    },
    en: {
      q: 'Playing ADC (Jinx) into Malphite, Rammus, and Nautilus stacking armor. What is your best 3rd item?',
      opts: ['Lord Dominik’s Regards', 'Bloodthirster', 'Rapid Firecannon', 'Guardian Angel'],
      ans: 0,
      exp: 'Against multiple armor-stacking tanks, % armor penetration (LDR / Mortal Reminder) spikes your DPS far more than any flat AD item.',
    },
  },
  {
    cat: 'BUILD',
    es: {
      q: 'El equipo rival tiene Soraka, Aatrox y Vladimir. ¿Cuál es el mejor timing para comprar Cortacuras?',
      opts: ['Primer objeto completo al min 5', 'Componente de 800g tras tu 1er ítem (o 2do back si sufrís en línea)', 'Esperar al 5to ítem', 'Nunca comprar cortacuras'],
      ans: 1,
      exp: 'El componente de 800g (Llamado del Verdugo / Orbe del Olvido) da el 100% del efecto de Heridas Graves sin retrasar tu spike principal.',
    },
    en: {
      q: 'Enemy team has Soraka, Aatrox, and Vladimir. What is the best timing for Anti-Heal?',
      opts: ['Rush the full item first', '800g component after your 1st item (or early if lane demands it)', 'Wait until 5th item', 'Never build anti-heal'],
      ans: 1,
      exp: 'Sitting on the 800g component (Executioner’s / Oblivion Orb) gives full Grievous Wounds without delaying your core spike.',
    },
  },
  {
    cat: 'MACRO',
    es: {
      q: 'Faltan 45 segundos para Dragón y tenés ventaja de oleada en Mid/Bot. ¿Cuál es la jugada óptima?',
      opts: ['Quedarse farmeando en línea hasta que nazca', 'Empujar oleada, backear a gastar oro y llegar 20s antes a poner visión', 'Buscar una kill 1v2 en la jungla rival', 'Ir directo a Dragón con 2000g sin gastar'],
      ans: 1,
      exp: 'Resetear 40–45s antes de un objetivo te permite llegar con ítems nuevos, vida llena y Control Wards para dominar el río primero.',
    },
    en: {
      q: '45 seconds until Drake spawns and you have lane prio. What is the optimal macro play?',
      opts: ['Stay in lane until it spawns', 'Crash wave, reset to spend gold, and arrive 20s early for vision control', 'Force a 1v2 in enemy jungle', 'Start Drake sitting on 2000 unspent gold'],
      ans: 1,
      exp: 'Resetting 40–45s before an objective lets you arrive with fresh items, full HP, and Control Wards to own river vision first.',
    },
  },
  {
    cat: 'MACRO',
    es: {
      q: 'Minuto 4:00. Sos Jungla en lado Bot y ves al jungla enemigo gankeando Top con doble buff. ¿Qué hacés?',
      opts: ['Correr caminando hasta Top (llegás tarde)', 'Invadir su jungla de bot / asegurar Dragón o gankear Bot libre', 'Backear inmediatamente', 'Hacer solo tus propios campamentos'],
      ans: 1,
      exp: 'Cross-mapping: cada vez que el jungla rival se muestra en el lado opuesto, castigá robando sus campamentos, gankeando bot o tomando objetivo.',
    },
    en: {
      q: 'Minute 4:00. You are Jungler on Bot side and spot the enemy jungler ganking Top. What do you do?',
      opts: ['Walk all the way to Top', 'Cross-map: invade their bot jungle, gank Bot, or take Drake', 'Recall immediately', 'Only farm your own camps'],
      ans: 1,
      exp: 'Cross-mapping punishes enemy jungler plays on the opposite side with free camps, bot ganks, or neutral objectives.',
    },
  },
  {
    cat: 'BUILD',
    es: {
      q: 'Sos mago/carry contra Zed, Diana y Leona. ¿Qué compra defensiva te da más valor en teamfights?',
      opts: ['Más daño puro sin defensa', 'Zhonya (AP) / Fajín + Ángel Guardián (AD) + Botas defensivas', 'Warmog', 'Solo comprar vida plana'],
      ans: 1,
      exp: 'Contra doble asesino + engage de CC, sobrevivir al primer combo con Zhonya o Fajín/GA te permite ganar la pelea entera.',
    },
    en: {
      q: 'You are a carry facing Zed, Diana, and Leona. Which defensive setup gives the most teamfight value?',
      opts: ['Pure glass cannon', 'Zhonya’s (AP) / QSS + GA (AD) with defensive boots', 'Warmog’s Armor', 'Only flat HP'],
      ans: 1,
      exp: 'Against dive + hard CC, surviving the initial burst via Zhonya’s or QSS/GA lets you clean up the entire teamfight.',
    },
  },
  {
    cat: 'MACRO',
    es: {
      q: 'Ganaron una pelea en minuto 26 y mataron a 3 enemigos cerca de Mid, pero tu equipo está a mitad de vida. ¿Prioridad #1?',
      opts: ['Perseguir al support enemigo hasta su base', 'Asegurar Barón Nashor o tirar inhibidor/torre gratis y resetear', 'Ir a farmear lobos y picuchillos', 'Backear sin tomar nada del mapa'],
      ans: 1,
      exp: 'En mid/late game, cada pick debe convertirse inmediatamente en Barón, Dragón o torres antes de que revivan.',
    },
    en: {
      q: 'You win a fight at 26 min killing 3 enemies near Mid while your team is half HP. Priority #1?',
      opts: ['Chase the enemy support to their fountain', 'Secure Baron Nashor or take free mid towers and reset', 'Farm jungle camps', 'Recall without taking any objective'],
      ans: 1,
      exp: 'In mid/late game, convert every numbers advantage straight into Baron, Drake, or turrets before death timers end.',
    },
  },
];

class WarmupHub {
  constructor() {
    this.tabs = document.querySelectorAll('#warmup-tabs .warmup-tab');
    this.panes = document.querySelectorAll('.warmup-pane');
    if (this.tabs.length === 0) return;

    this.tabs.forEach(tab => {
      tab.addEventListener('click', () => this.openMode(tab.dataset.mode));
    });

    this.initMicro();
    this.initQuiz();
    this.initIdlePopup();
  }

  openMode(mode) {
    this.tabs.forEach(t => t.classList.toggle('active', t.dataset.mode === mode));
    this.panes.forEach(p => p.classList.toggle('active', p.id === `pane-${mode}`));
    if (mode === 'quiz' && !this.quizLoaded) {
      this.quizLoaded = true;
      this.loadQuizQuestion();
    }
  }

  /* ── Modo 2: Micro Aim & Reflexes (20s) ── */
  initMicro() {
    this.arena = document.getElementById('micro-arena');
    this.overlay = document.getElementById('micro-overlay');
    this.timeEl = document.getElementById('micro-time');
    this.scoreEl = document.getElementById('micro-score');
    this.rtEl = document.getElementById('micro-rt');
    this.accEl = document.getElementById('micro-acc');
    this.bestEl = document.getElementById('micro-best');
    this.microBest = parseInt(localStorage.getItem('NoFlash_micro_best') || '0', 10);
    const isEnInit = typeof getCurrentLang === 'function' && getCurrentLang() !== 'es';
    if (this.bestEl) this.bestEl.textContent = `🏆 ${isEnInit ? 'Best' : 'Récord'}: ${this.microBest}`;

    const startHandler = () => this.startMicro();
    document.getElementById('btn-micro-start')?.addEventListener('click', startHandler);
    document.getElementById('btn-micro-start-big')?.addEventListener('click', startHandler);

    this.arena?.addEventListener('click', (e) => {
      if (!this.microRunning) return;
      if (e.target === this.arena) {
        this.microClicks += 1;
        this._updateMicroStats();
      }
    });
  }

  startMicro() {
    if (!this.arena) return;
    this.stopMicro(false);
    this.microRunning = true;
    this.microScore = 0;
    this.microHits = 0;
    this.microClicks = 0;
    this.microRts = [];
    this.microEndAt = Date.now() + 20000;

    if (this.overlay) this.overlay.style.display = 'none';
    this.arena.querySelectorAll('.micro-target').forEach(el => el.remove());
    this._updateMicroStats();

    this._spawnTarget();
    this._spawnTarget();

    this.microTimer = setInterval(() => {
      const rem = Math.max(0, (this.microEndAt - Date.now()) / 1000);
      if (this.timeEl) this.timeEl.textContent = `${rem.toFixed(1)}s`;
      if (rem <= 0) this.stopMicro(true);
    }, 100);
  }

  _spawnTarget() {
    if (!this.microRunning || !this.arena) return;
    const isBad = Math.random() < 0.22;
    const t = document.createElement('div');
    t.className = `micro-target ${isBad ? 'bad' : 'gold'}`;
    t.textContent = isBad ? '✕' : '⚡';
    const x = 10 + Math.random() * 80;
    const y = 14 + Math.random() * 72;
    t.style.left = `${x}%`;
    t.style.top = `${y}%`;
    const bornAt = performance.now();

    const life = setTimeout(() => {
      if (t.parentNode) {
        t.remove();
        if (this.microRunning && !isBad) this._spawnTarget();
      }
    }, isBad ? 1500 : 1900);

    t.addEventListener('click', (e) => {
      e.stopPropagation();
      clearTimeout(life);
      t.remove();
      this.microClicks += 1;
      if (isBad) {
        this.microScore = Math.max(0, this.microScore - 2);
      } else {
        this.microHits += 1;
        this.microScore += 1;
        this.microRts.push(Math.round(performance.now() - bornAt));
      }
      this._updateMicroStats();
      if (this.microRunning) this._spawnTarget();
    });

    this.arena.appendChild(t);
    if (isBad && this.microRunning) {
      setTimeout(() => {
        if (this.microRunning && this.arena.querySelectorAll('.micro-target.gold').length < 2) {
          this._spawnTarget();
        }
      }, 250);
    }
  }

  _updateMicroStats() {
    if (this.scoreEl) this.scoreEl.textContent = String(this.microScore || 0);
    const avgRt = this.microRts && this.microRts.length > 0
      ? Math.round(this.microRts.reduce((a, b) => a + b, 0) / this.microRts.length)
      : null;
    if (this.rtEl) this.rtEl.textContent = avgRt != null ? `${avgRt} ms` : '— ms';
    const acc = this.microClicks > 0 ? Math.round((this.microHits / this.microClicks) * 100) : 100;
    if (this.accEl) this.accEl.textContent = `${acc}%`;
  }

  stopMicro(showSummary) {
    this.microRunning = false;
    if (this.microTimer) clearInterval(this.microTimer);
    this.arena?.querySelectorAll('.micro-target').forEach(el => el.remove());

    if (showSummary && this.overlay) {
      const isEnEnd = typeof getCurrentLang === 'function' && getCurrentLang() !== 'es';
      if (this.microScore > this.microBest) {
        this.microBest = this.microScore;
        localStorage.setItem('NoFlash_micro_best', String(this.microBest));
        if (this.bestEl) this.bestEl.textContent = `🏆 ${isEnEnd ? 'Best' : 'Récord'}: ${this.microBest}`;
      }
      const avgRt = this.microRts.length > 0
        ? Math.round(this.microRts.reduce((a, b) => a + b, 0) / this.microRts.length)
        : 0;
      this.overlay.innerHTML = isEnEnd ? `
        <p><strong>Warm-Up Complete!</strong><br>Score: <strong>${this.microScore}</strong> · Avg reaction: <strong>${avgRt} ms</strong></p>
        <button class="btn-analyze" id="btn-micro-retry" style="max-width:220px;margin:0.5rem auto 0;">
          <i class="fa-solid fa-rotate-right"></i> Play Again
        </button>
      ` : `
        <p><strong>¡Calentamiento terminado!</strong><br>Puntaje: <strong>${this.microScore}</strong> · Reacción promedio: <strong>${avgRt} ms</strong></p>
        <button class="btn-analyze" id="btn-micro-retry" style="max-width:220px;margin:0.5rem auto 0;">
          <i class="fa-solid fa-rotate-right"></i> Jugar otra vez
        </button>
      `;
      this.overlay.style.display = 'flex';
      document.getElementById('btn-micro-retry')?.addEventListener('click', () => this.startMicro());
    }
  }

  /* ── Modo 3: Quiz de Macro & Builds ── */
  initQuiz() {
    this.quizIndex = Math.floor(Math.random() * QUIZ_BANK.length);
    this.quizCorrect = 0;
    this.quizTotal = 0;
    document.getElementById('btn-quiz-next')?.addEventListener('click', () => {
      this.quizIndex = (this.quizIndex + 1) % QUIZ_BANK.length;
      this.loadQuizQuestion();
    });
  }

  loadQuizQuestion() {
    const item = QUIZ_BANK[this.quizIndex % QUIZ_BANK.length];
    const isEn = typeof getCurrentLang === 'function' && getCurrentLang() !== 'es';
    const data = isEn ? item.en : item.es;

    const catEl = document.getElementById('quiz-category');
    const qEl = document.getElementById('quiz-question');
    const optsEl = document.getElementById('quiz-options');
    const fbEl = document.getElementById('quiz-feedback');
    if (!qEl || !optsEl) return;

    if (catEl) catEl.textContent = item.cat;
    qEl.textContent = data.q;
    if (fbEl) fbEl.style.display = 'none';

    optsEl.innerHTML = data.opts.map((opt, idx) => `
      <button class="quiz-opt-btn" data-idx="${idx}">${opt}</button>
    `).join('');

    optsEl.querySelectorAll('.quiz-opt-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const picked = parseInt(btn.dataset.idx, 10);
        this.quizTotal += 1;
        optsEl.querySelectorAll('.quiz-opt-btn').forEach((b, i) => {
          b.disabled = true;
          if (i === data.ans) b.classList.add('correct');
          else if (i === picked) b.classList.add('wrong');
        });
        if (picked === data.ans) this.quizCorrect += 1;
        const pill = document.getElementById('quiz-score-pill');
        if (pill) pill.textContent = `✅ ${this.quizCorrect} / ${this.quizTotal}`;
        if (fbEl) {
          fbEl.innerHTML = `<strong>${picked === data.ans ? (isEn ? '✅ Correct!' : '✅ ¡Correcto!') : (isEn ? '❌ Not quite!' : '❌ No era esa!')}</strong> ${data.exp}`;
          fbEl.style.display = 'block';
        }
      });
    });
  }

  /* ── Pop-up amigable cuando el usuario está inactivo / esperando cola ── */
  initIdlePopup() {
    const popup = document.getElementById('idle-popup');
    const closeBtn = document.getElementById('idle-popup-close');
    if (!popup) return;

    this.idleShown = false;
    let lastActivity = Date.now();
    const resetActivity = () => { lastActivity = Date.now(); };
    ['mousemove', 'keydown', 'click'].forEach(ev => window.addEventListener(ev, resetActivity, { passive: true }));

    closeBtn?.addEventListener('click', () => {
      popup.style.display = 'none';
      this.idleShown = true;
    });

    popup.querySelectorAll('.idle-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        popup.style.display = 'none';
        this.idleShown = true;
        if (window.app) window.app.switchView('riftdle');
        this.openMode(btn.dataset.go);
      });
    });

    // Si lleva 45s sin actividad en búsqueda/análisis (no en draft ni en partida), ofrecer Warm-Up
    setInterval(() => {
      if (this.idleShown) return;
      const curView = window.app?.state?.currentView;
      if (curView === 'riftdle' || curView === 'draft' || curView === 'ingame') return;
      if (Date.now() - lastActivity >= 45000) {
        this.idleShown = true;
        popup.style.display = 'block';
      }
    }, 5000);
  }
}

document.addEventListener('DOMContentLoaded', () => {
  window.warmupHub = new WarmupHub();
});
