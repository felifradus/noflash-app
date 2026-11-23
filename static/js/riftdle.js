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
    this.hintLevel = 0;

    if (this.inputEl) {
      this.inputEl.value = '';
      this.inputEl.disabled = false;
    }
    if (this.dropdownEl) this.dropdownEl.style.display = 'none';
    if (this.hintBoxEl) {
      this.hintBoxEl.style.display = 'none';
      this.hintBoxEl.innerHTML = '';
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
        this.hintLevel = Math.min(2, (this.hintLevel || 0) + 1);
        const isEn = typeof getCurrentLang === 'function' && getCurrentLang() !== 'es';
        const dName = displayName(this.secret.name);
        const firstLetter = dName[0];
        const roles = (this.secret.roles || []).map(r => r.toUpperCase()).join(' / ');
        const rng = this.secret.range || 'Melee';
        const res = this.secret.resource || 'Mana';
        const textHint = isEn
          ? `💡 Hint 1: Starts with "<strong>${firstLetter}</strong>" · Role: <strong>${roles}</strong> · ${rng} · ${res}`
          : `💡 Pista 1: Empieza con "<strong>${firstLetter}</strong>" · Rol: <strong>${roles}</strong> · ${rng} · ${res}`;
        if (this.hintLevel >= 2) {
          const splash = typeof champSplashUrl === 'function'
            ? champSplashUrl(this.secret.name)
            : `https://ddragon.leagueoflegends.com/cdn/img/champion/splash/${this.secret.name}_0.jpg`;
          this.hintBoxEl.innerHTML = `
            <div>${textHint}</div>
            <div class="flashdle-splash-hint">
              <span>${isEn ? '🎨 Hint 2 (Splash Silhouette):' : '🎨 Pista 2 (Silueta del Splash):'}</span>
              <div class="flashdle-blur-img" style="background-image:url('${splash}')"></div>
            </div>
          `;
        } else {
          this.hintBoxEl.innerHTML = `${textHint} <span class="coach-muted">(${isEn ? 'Click Hint again for Splash Art!' : '¡Tocá Pista de nuevo para ver el Splash!'})</span>`;
        }
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
      window.uiSfx?.playVictory();
    } else {
      window.uiSfx?.playTileFlip();
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

    this.boardEl.innerHTML = this.guesses.map((g, idx) => {
      const isExactChamp = g.name === this.secret.name ? 'exact' : 'miss';
      const roleMatch = this._compareArray(g.roles, this.secret.roles);
      const dmgMatch = (g.damage || '').toLowerCase() === (this.secret.damage || '').toLowerCase() ? 'exact' : 'miss';
      const rangeMatch = (g.range || '').toLowerCase() === (this.secret.range || '').toLowerCase() ? 'exact' : 'miss';
      const resMatch = (g.resource || '').toLowerCase() === (this.secret.resource || '').toLowerCase() ? 'exact' : 'miss';
      const classMatch = this._compareArray(g.class, this.secret.class);

      return `
        <div class="riftdle-row flashdle-6cols ${idx === 0 ? 'tile-flip-in' : ''}">
          <div class="rd-cell champ ${isExactChamp}">
            <img src="${champImgUrl(g.name)}" alt="${displayName(g.name)}">
            <span>${displayName(g.name)}</span>
          </div>
          <div class="rd-cell ${roleMatch}">${(g.roles || []).map(r => r.toUpperCase()).join(' / ')}</div>
          <div class="rd-cell ${dmgMatch}">${g.damage || '—'}</div>
          <div class="rd-cell ${rangeMatch}">${g.range || '—'}</div>
          <div class="rd-cell ${resMatch}">${g.resource || '—'}</div>
          <div class="rd-cell ${classMatch}">${(g.class || []).join(' / ')}</div>
        </div>
      `;
    }).join('');
  }
}

document.addEventListener('DOMContentLoaded', () => {
  window.riftdle = new RiftdleGame();
});

