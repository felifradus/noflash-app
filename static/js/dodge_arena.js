/* ═══════════════════════════════════════════════════════
   NEW FEATURE: DODGE ARENA (60fps LoL Skillshot Survival + Flash + WebAudio SFX + APM)
   Right-Click / Left-Click or Cursor Follow + Press F / Space to FLASH!
   ═══════════════════════════════════════════════════════ */

const DODGE_RANKS = [
  { min: 0,    name: 'IRON',       color: '#94a3b8' },
  { min: 400,  name: 'BRONZE',     color: '#cd7f32' },
  { min: 900,  name: 'SILVER',     color: '#cbd5e1' },
  { min: 1500, name: 'GOLD',       color: '#f6d365' },
  { min: 2300, name: 'PLATINUM',   color: '#2dd4bf' },
  { min: 3300, name: 'EMERALD',    color: '#10b981' },
  { min: 4500, name: 'DIAMOND',    color: '#60a5fa' },
  { min: 6000, name: 'MASTER',     color: '#c084fc' },
  { min: 8000, name: 'CHALLENGER', color: '#fde047' },
];

/* ── Sintetizador WebAudio sutil y orgánico (whoosh / thud suave, cero 8-bit) ── */
class ArenaSFX {
  constructor() {
    this.ctx = null;
    this.muted = false;
  }
  _ensure() {
    if (this.muted) return null;
    if (!this.ctx) {
      const AC = window.AudioContext || window.webkitAudioContext;
      if (AC) this.ctx = new AC();
    }
    if (this.ctx && this.ctx.state === 'suspended') this.ctx.resume().catch(() => {});
    return this.ctx;
  }
  _noiseBurst(dur, filterFreq, q, vol) {
    const ctx = this._ensure();
    if (!ctx) return;
    const buf = ctx.createBuffer(1, Math.floor(ctx.sampleRate * dur), ctx.sampleRate);
    const data = buf.getChannelData(0);
    for (let i = 0; i < data.length; i++) data[i] = Math.random() * 2 - 1;
    const src = ctx.createBufferSource();
    src.buffer = buf;
    const flt = ctx.createBiquadFilter();
    flt.type = 'bandpass';
    flt.frequency.setValueAtTime(filterFreq, ctx.currentTime);
    flt.Q.setValueAtTime(q, ctx.currentTime);
    const gain = ctx.createGain();
    gain.gain.setValueAtTime(vol, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + dur);
    src.connect(flt); flt.connect(gain); gain.connect(ctx.destination);
    src.start();
  }
  playFlash() {
    this._noiseBurst(0.16, 1600, 1.4, 0.08);
  }
  playCloseDodge() {
    this._noiseBurst(0.06, 1100, 2.5, 0.045);
  }
  playLaser() {
    this._noiseBurst(0.22, 420, 1.2, 0.08);
  }
  playHit() {
    const ctx = this._ensure();
    if (!ctx) return;
    const now = ctx.currentTime;
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = 'sine';
    osc.frequency.setValueAtTime(115, now);
    osc.frequency.exponentialRampToValueAtTime(40, now + 0.16);
    gain.gain.setValueAtTime(0.11, now);
    gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.18);
    osc.connect(gain); gain.connect(ctx.destination);
    osc.start(now); osc.stop(now + 0.19);
  }
  playRankUp() {
    window.uiSfx?.playSuccess();
  }
}

class WarmupHub {
  constructor() {
    this.tabs = document.querySelectorAll('#warmup-tabs .warmup-tab');
    this.panes = document.querySelectorAll('.warmup-pane');
    if (this.tabs.length === 0) return;

    this.sfx = new ArenaSFX();
    this.tabs.forEach(tab => {
      tab.addEventListener('click', () => this.openMode(tab.dataset.mode));
    });

    this.initDodgeArena();
    this.initIdlePopup();
  }

  loadQuizQuestion() {}

  openMode(mode) {
    const targetMode = (mode === 'micro' || mode === 'quiz') ? 'dodge' : mode;
    this.tabs.forEach(t => t.classList.toggle('active', t.dataset.mode === targetMode));
    this.panes.forEach(p => p.classList.toggle('active', p.id === `pane-${targetMode}`));
    if (targetMode !== 'dodge' && this.running) {
      this.stopDodge(false);
    }
  }

  /* ── DODGE ARENA ENGINE (60fps Canvas + SFX + APM + Trail + Rank-Ups) ── */
  initDodgeArena() {
    this.canvas = document.getElementById('dodge-canvas');
    if (!this.canvas) return;
    this.ctx = this.canvas.getContext('2d');
    this.W = this.canvas.width;
    this.H = this.canvas.height;

    this.overlayEl = document.getElementById('dodge-overlay');
    this.timeEl = document.getElementById('dodge-time');
    this.scoreEl = document.getElementById('dodge-score');
    this.rankEl = document.getElementById('dodge-rank');
    this.hpEl = document.getElementById('dodge-hp');
    this.flashEl = document.getElementById('dodge-flash-pill');
    this.bestEl = document.getElementById('dodge-best');
    this.ctrlBtn = document.getElementById('btn-dodge-control');

    this.bestScore = parseInt(localStorage.getItem('NoFlash_dodge_best') || '0', 10);
    this.microBest = this.bestScore;
    this.updateBestUI();

    this.followMode = false;
    this.running = false;
    this.mouse = { x: this.W / 2, y: this.H / 2 };

    this.playerImg = new Image();
    this.playerImg.crossOrigin = 'anonymous';
    this.playerImg.src = 'https://ddragon.leagueoflegends.com/cdn/16.23.1/img/champion/Ezreal.png';

    const startHandler = () => this.startDodge();
    document.getElementById('btn-dodge-start')?.addEventListener('click', startHandler);
    document.getElementById('btn-dodge-start-big')?.addEventListener('click', startHandler);

    this.ctrlBtn?.addEventListener('click', () => {
      this.followMode = !this.followMode;
      this.ctrlBtn.textContent = this.followMode ? '🖱️ Cursor Follow' : '🖱️ Click Move';
    });

    const getCanvasPos = (e) => {
      const rect = this.canvas.getBoundingClientRect();
      return {
        x: (e.clientX - rect.left) * (this.W / rect.width),
        y: (e.clientY - rect.top) * (this.H / rect.height),
      };
    };

    this.canvas.addEventListener('mousemove', (e) => {
      const pos = getCanvasPos(e);
      if (this.running && this.followMode) {
        if (Math.hypot(pos.x - this.mouse.x, pos.y - this.mouse.y) > 22) {
          this.actions += 0.35; // Contar cambios de dirección reales en Cursor Follow
        }
        this.target.x = pos.x;
        this.target.y = pos.y;
      }
      this.mouse = pos;
    });

    const onMoveClick = (e) => {
      e.preventDefault();
      if (!this.running) return;
      const pos = getCanvasPos(e);
      this.mouse = pos;
      this.target = { x: pos.x, y: pos.y };
      this.actions += 1;
      this.ripples.push({ x: pos.x, y: pos.y, r: 4, maxR: 22, alpha: 0.9, color: '#22c55e' });
    };
    this.canvas.addEventListener('contextmenu', onMoveClick);
    this.canvas.addEventListener('mousedown', onMoveClick);

    window.addEventListener('keydown', (e) => {
      if (!this.running) return;
      if (e.code === 'KeyF' || e.code === 'Space') {
        e.preventDefault();
        this.actions += 1;
        this.triggerFlash();
      }
    });

    this._drawIdleBg(0);
  }

  _syncPlayerChampAvatar() {
    try {
      const best = window.app?.state?.playerData?.analysis?.best_champions?.[0];
      const cName = best?.champion || best?.champion_name;
      if (cName && typeof champImgUrl === 'function') {
        const nextUrl = champImgUrl(cName);
        if (this.playerImg.src !== nextUrl) this.playerImg.src = nextUrl;
      }
    } catch {}
  }

  updateBestUI() {
    if (!this.bestEl) return;
    const isEn = typeof getCurrentLang === 'function' ? getCurrentLang() !== 'es' : true;
    this.bestEl.textContent = `🏆 ${isEn ? 'Best' : 'Récord'}: ${this.bestScore}`;
  }

  _getRank(score) {
    let cur = DODGE_RANKS[0];
    for (const r of DODGE_RANKS) {
      if (score >= r.min) cur = r;
    }
    return cur;
  }

  startDodge() {
    this.stopDodge(false);
    this._syncPlayerChampAvatar();
    this.running = true;
    this.startTime = performance.now();
    this.lastFrame = this.startTime;
    this.elapsed = 0;
    this.score = 0;
    this.hp = 3;
    this.actions = 0;
    this.closeDodges = 0;
    this.clutchFlashes = 0;
    this.lastRankName = 'IRON';
    this.rankBanner = null;
    this.invulnUntil = 0;
    this.flashReadyAt = 0;
    this.shakeTime = 0;
    this.spawnTimer = 0.45;
    this.luxTimer = 4.8;
    this.ziggsTimer = 6.2;

    this.player = { x: this.W / 2, y: this.H / 2, r: 18, speed: 310 };
    this.target = { x: this.W / 2, y: this.H / 2 };
    this.trail = [];
    this.projectiles = [];
    this.lasers = [];
    this.aoes = [];
    this.particles = [];
    this.ripples = [];
    this.floatTexts = [];

    if (this.overlayEl) this.overlayEl.style.display = 'none';
    this._loop(performance.now());
  }

  stopDodge(showGameOver) {
    this.running = false;
    if (this.rafId) cancelAnimationFrame(this.rafId);
    if (showGameOver && this.overlayEl) {
      const finalScore = Math.floor(this.score);
      const rank = this._getRank(finalScore);
      const mins = Math.max(0.08, this.elapsed / 60);
      const apm = Math.round(this.actions / mins);
      const isNewBest = finalScore > this.bestScore;
      if (isNewBest) {
        this.bestScore = finalScore;
        this.microBest = finalScore;
        localStorage.setItem('NoFlash_dodge_best', String(this.bestScore));
        localStorage.setItem('NoFlash_micro_best', String(Math.min(99, Math.floor(finalScore / 100))));
        this.updateBestUI();
      }
      const isEn = typeof getCurrentLang === 'function' ? getCurrentLang() !== 'es' : true;
      const apmFlavor = apm >= 210
        ? (isEn ? 'Korean Challenger hands!' : '¡Manos de Challenger coreano!')
        : apm >= 140
          ? (isEn ? 'Clean Master+ micro!' : '¡Micro súper limpio de Master+!')
          : apm >= 85
            ? (isEn ? 'Smooth, steady rhythm.' : 'Buen ritmo y control.')
            : (isEn ? 'Warming up — click faster to sidestep!' : 'Entrando en calor — ¡clickeá más rápido para esquivar!');

      this.overlayEl.innerHTML = `
        <div class="dodge-overlay-badge">${isNewBest ? (isEn ? '🔥 NEW PERSONAL BEST!' : '🔥 ¡NUEVO RÉCORD!') : `🎖️ ${rank.name}`}</div>
        <h3 style="font-family:'Cinzel',serif;color:${rank.color};margin:0.25rem 0;">${finalScore} PTS · ${this.elapsed.toFixed(1)}s</h3>
        <div class="dodge-end-stats">
          <div class="dodge-stat-box"><span>⚡ APM</span><strong>${apm}</strong></div>
          <div class="dodge-stat-box"><span>💨 ${isEn ? 'Close Dodges' : 'Esquives Justos'}</span><strong>${this.closeDodges}</strong></div>
          <div class="dodge-stat-box"><span>✨ ${isEn ? 'Clutch Flashes' : 'Flash Clutches'}</span><strong>${this.clutchFlashes}</strong></div>
        </div>
        <p style="margin:0.45rem 0 0.75rem;color:#cbd5e1;font-size:0.86rem;">${apmFlavor}</p>
        <button class="btn-analyze" id="btn-dodge-retry" style="max-width:220px;margin:0 auto;">
          <i class="fa-solid fa-rotate-right"></i> ${isEn ? 'Play Again' : 'Jugar otra vez'}
        </button>
      `;
      this.overlayEl.style.display = 'flex';
      document.getElementById('btn-dodge-retry')?.addEventListener('click', () => this.startDodge());
    }
  }

  triggerFlash() {
    const now = performance.now();
    if (now < this.flashReadyAt) return;
    this.flashReadyAt = now + 5500;
    this.invulnUntil = Math.max(this.invulnUntil, now + 260);
    this.sfx.playFlash();

    const dx = this.mouse.x - this.player.x;
    const dy = this.mouse.y - this.player.y;
    const dist = Math.hypot(dx, dy) || 1;
    const blink = Math.min(165, Math.max(95, dist));
    const oldX = this.player.x;
    const oldY = this.player.y;

    this.player.x = Math.max(24, Math.min(this.W - 24, this.player.x + (dx / dist) * blink));
    this.player.y = Math.max(24, Math.min(this.H - 24, this.player.y + (dy / dist) * blink));
    this.target.x = this.player.x;
    this.target.y = this.player.y;

    this.ripples.push({ x: oldX, y: oldY, r: 8, maxR: 46, alpha: 1, color: '#fde047' });
    this.ripples.push({ x: this.player.x, y: this.player.y, r: 6, maxR: 52, alpha: 1, color: '#f6d365' });
    for (let i = 0; i < 22; i++) {
      const ang = Math.random() * Math.PI * 2;
      const spd = 60 + Math.random() * 155;
      this.particles.push({
        x: this.player.x, y: this.player.y,
        vx: Math.cos(ang) * spd, vy: Math.sin(ang) * spd,
        life: 0.48, color: i % 2 === 0 ? '#fde047' : '#0ac8b9', size: 4,
      });
    }

    const nearDanger = this.projectiles.some(p => Math.hypot(p.x - oldX, p.y - oldY) < 100)
      || this.aoes.some(a => Math.hypot(a.x - oldX, a.y - oldY) < a.maxR + 20)
      || this.lasers.some(l => this._pointLineDist(oldX, oldY, l.x1, l.y1, l.x2, l.y2) < 46);
    if (nearDanger) {
      this.score += 150;
      this.clutchFlashes += 1;
      this.floatTexts.push({ x: this.player.x, y: this.player.y - 26, text: '✨ CLUTCH FLASH +150', color: '#fde047', life: 1.0 });
    }
  }

  _spawnProjectile(diff) {
    const types = [
      { kind: 'blitz', name: 'BLITZ Q', r: 12, speed: 345 + diff * 28, color: '#f6d365', glow: '#0ac8b9' },
      { kind: 'morg',  name: 'MORG Q',  r: 18, speed: 225 + diff * 20, color: '#c084fc', glow: '#9333ea' },
      { kind: 'ashe',  name: 'ASHE R',  r: 16, speed: 300 + diff * 24, color: '#38bdf8', glow: '#e0f2fe' },
    ];
    const t = types[Math.floor(Math.random() * types.length)];
    const side = Math.floor(Math.random() * 4);
    let x = 0, y = 0;
    if (side === 0) { x = -20; y = Math.random() * this.H; }
    else if (side === 1) { x = this.W + 20; y = Math.random() * this.H; }
    else if (side === 2) { x = Math.random() * this.W; y = -20; }
    else { x = Math.random() * this.W; y = this.H + 20; }

    const spread = (Math.random() - 0.5) * 75;
    const tx = this.player.x + spread;
    const ty = this.player.y + spread;
    const ang = Math.atan2(ty - y, tx - x);
    this.projectiles.push({
      ...t,
      x, y,
      vx: Math.cos(ang) * t.speed,
      vy: Math.sin(ang) * t.speed,
      ang,
      closeAwarded: false,
    });
  }

  _spawnLuxLaser() {
    const ang = Math.random() * Math.PI * 2;
    const cx = this.player.x + (Math.random() - 0.5) * 40;
    const cy = this.player.y + (Math.random() - 0.5) * 40;
    const len = 1100;
    this.lasers.push({
      x1: cx - Math.cos(ang) * len,
      y1: cy - Math.sin(ang) * len,
      x2: cx + Math.cos(ang) * len,
      y2: cy + Math.sin(ang) * len,
      warnTime: 0.92,
      fireTime: 0.34,
      age: 0,
      width: 30,
      hitDone: false,
      sfxPlayed: false,
    });
  }

  _spawnZiggsBomb() {
    const tx = Math.max(70, Math.min(this.W - 70, this.player.x + (Math.random() - 0.5) * 110));
    const ty = Math.max(70, Math.min(this.H - 70, this.player.y + (Math.random() - 0.5) * 110));
    this.aoes.push({
      x: tx, y: ty,
      maxR: 68,
      warnTime: 1.05,
      age: 0,
      exploded: false,
    });
  }

  _pointLineDist(px, py, x1, y1, x2, y2) {
    const A = px - x1, B = py - y1, C = x2 - x1, D = y2 - y1;
    const dot = A * C + B * D;
    const lenSq = C * C + D * D || 1;
    const t = Math.max(0, Math.min(1, dot / lenSq));
    return Math.hypot(px - (x1 + t * C), py - (y1 + t * D));
  }

  _takeHit(now) {
    if (now < this.invulnUntil) return;
    this.hp -= 1;
    this.invulnUntil = now + 950;
    this.shakeTime = 0.28;
    this.sfx.playHit();
    for (let i = 0; i < 18; i++) {
      const a = Math.random() * Math.PI * 2;
      const s = 70 + Math.random() * 140;
      this.particles.push({
        x: this.player.x, y: this.player.y,
        vx: Math.cos(a) * s, vy: Math.sin(a) * s,
        life: 0.45, color: '#ef4444', size: 4,
      });
    }
    if (this.hp <= 0) {
      this.stopDodge(true);
    }
  }

  _loop(now) {
    if (!this.running) return;
    const dt = Math.min(0.05, (now - this.lastFrame) / 1000);
    this.lastFrame = now;
    this.elapsed = (now - this.startTime) / 1000;
    const diff = Math.min(9, this.elapsed / 9);
    this.score += dt * (45 + diff * 12);

    // Check Rank Promotion!
    const curRank = this._getRank(Math.floor(this.score));
    if (curRank.name !== this.lastRankName) {
      this.lastRankName = curRank.name;
      this.rankBanner = { text: `PROMOTED TO ${curRank.name}!`, color: curRank.color, life: 1.6 };
      this.sfx.playRankUp();
    }
    if (this.rankBanner) {
      this.rankBanner.life -= dt;
      if (this.rankBanner.life <= 0) this.rankBanner = null;
    }

    const dx = this.target.x - this.player.x;
    const dy = this.target.y - this.player.y;
    const dist = Math.hypot(dx, dy);
    if (dist > 3) {
      const step = Math.min(dist, this.player.speed * dt);
      this.player.x += (dx / dist) * step;
      this.player.y += (dy / dist) * step;
      this.trail.push({ x: this.player.x, y: this.player.y, life: 0.25 });
    }
    for (let i = this.trail.length - 1; i >= 0; i--) {
      this.trail[i].life -= dt;
      if (this.trail[i].life <= 0) this.trail.splice(i, 1);
    }

    this.spawnTimer -= dt;
    if (this.spawnTimer <= 0) {
      this._spawnProjectile(diff);
      if (diff >= 3 && Math.random() < 0.35) this._spawnProjectile(diff);
      this.spawnTimer = Math.max(0.32, 0.92 - diff * 0.068);
    }
    this.luxTimer -= dt;
    if (this.luxTimer <= 0) {
      this._spawnLuxLaser();
      this.luxTimer = Math.max(2.6, 5.2 - diff * 0.32);
    }
    this.ziggsTimer -= dt;
    if (this.ziggsTimer <= 0) {
      this._spawnZiggsBomb();
      this.ziggsTimer = Math.max(2.4, 4.8 - diff * 0.28);
    }

    for (let i = this.projectiles.length - 1; i >= 0; i--) {
      const p = this.projectiles[i];
      p.x += p.vx * dt;
      p.y += p.vy * dt;
      const d = Math.hypot(p.x - this.player.x, p.y - this.player.y);
      if (d < p.r + this.player.r - 3) {
        this.projectiles.splice(i, 1);
        this._takeHit(now);
        continue;
      }
      if (!p.closeAwarded && d < p.r + this.player.r + 22) {
        p.closeAwarded = true;
        this.score += 100;
        this.closeDodges += 1;
        this.sfx.playCloseDodge();
        this.floatTexts.push({ x: this.player.x, y: this.player.y - 22, text: '⚡ CLOSE DODGE +100', color: '#5eead4', life: 0.85 });
      }
      if (p.x < -60 || p.x > this.W + 60 || p.y < -60 || p.y > this.H + 60) {
        this.projectiles.splice(i, 1);
      }
    }

    for (let i = this.lasers.length - 1; i >= 0; i--) {
      const l = this.lasers[i];
      l.age += dt;
      if (l.age >= l.warnTime && !l.sfxPlayed) {
        l.sfxPlayed = true;
        this.sfx.playLaser();
      }
      if (l.age >= l.warnTime && l.age < l.warnTime + l.fireTime && !l.hitDone) {
        const d = this._pointLineDist(this.player.x, this.player.y, l.x1, l.y1, l.x2, l.y2);
        if (d < l.width / 2 + this.player.r - 4) {
          l.hitDone = true;
          this._takeHit(now);
        }
      }
      if (l.age >= l.warnTime + l.fireTime) this.lasers.splice(i, 1);
    }

    for (let i = this.aoes.length - 1; i >= 0; i--) {
      const a = this.aoes[i];
      a.age += dt;
      if (a.age >= a.warnTime && !a.exploded) {
        a.exploded = true;
        const d = Math.hypot(a.x - this.player.x, a.y - this.player.y);
        if (d < a.maxR + this.player.r - 5) this._takeHit(now);
        this.ripples.push({ x: a.x, y: a.y, r: a.maxR * 0.4, maxR: a.maxR + 14, alpha: 0.9, color: '#f97316' });
      }
      if (a.age >= a.warnTime + 0.22) this.aoes.splice(i, 1);
    }

    for (let i = this.particles.length - 1; i >= 0; i--) {
      const pt = this.particles[i];
      pt.x += pt.vx * dt; pt.y += pt.vy * dt; pt.life -= dt;
      if (pt.life <= 0) this.particles.splice(i, 1);
    }
    for (let i = this.ripples.length - 1; i >= 0; i--) {
      const rp = this.ripples[i];
      rp.r += 110 * dt; rp.alpha -= 2.2 * dt;
      if (rp.alpha <= 0 || rp.r >= rp.maxR) this.ripples.splice(i, 1);
    }
    for (let i = this.floatTexts.length - 1; i >= 0; i--) {
      const ft = this.floatTexts[i];
      ft.y -= 36 * dt; ft.life -= dt;
      if (ft.life <= 0) this.floatTexts.splice(i, 1);
    }
    if (this.shakeTime > 0) this.shakeTime -= dt;

    this._render(now);
    this._updateHud(now);
    if (this.running) this.rafId = requestAnimationFrame((t) => this._loop(t));
  }

  _updateHud(now) {
    if (this.timeEl) this.timeEl.textContent = `${this.elapsed.toFixed(1)}s`;
    const sc = Math.floor(this.score);
    if (this.scoreEl) this.scoreEl.textContent = String(sc);
    const rank = this._getRank(sc);
    if (this.rankEl) {
      this.rankEl.textContent = rank.name;
      this.rankEl.style.color = rank.color;
    }
    if (this.hpEl) this.hpEl.textContent = '❤️'.repeat(Math.max(0, this.hp)) || '💀';
    if (this.flashEl) {
      const rem = Math.max(0, (this.flashReadyAt - now) / 1000);
      if (rem <= 0) {
        this.flashEl.textContent = '⚡ FLASH: READY (F)';
        this.flashEl.classList.remove('on-cd');
      } else {
        this.flashEl.textContent = `⚡ FLASH: ${rem.toFixed(1)}s`;
        this.flashEl.classList.add('on-cd');
      }
    }
  }

  _drawIdleBg(now) {
    const ctx = this.ctx;
    if (!ctx) return;
    const grad = ctx.createRadialGradient(this.W / 2, this.H / 2, 20, this.W / 2, this.H / 2, this.W * 0.65);
    grad.addColorStop(0, '#0d2642');
    grad.addColorStop(0.6, '#061529');
    grad.addColorStop(1, '#020812');
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, this.W, this.H);

    // Anillo rúnico central estilo Grieta del Invocador
    ctx.save();
    ctx.strokeStyle = 'rgba(200, 155, 60, 0.14)';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(this.W / 2, this.H / 2, 115, 0, Math.PI * 2);
    ctx.stroke();
    ctx.strokeStyle = 'rgba(10, 200, 185, 0.10)';
    ctx.setLineDash([12, 12]);
    ctx.beginPath();
    ctx.arc(this.W / 2, this.H / 2, 165, 0, Math.PI * 2);
    ctx.stroke();
    ctx.restore();

    ctx.strokeStyle = 'rgba(200, 155, 60, 0.05)';
    ctx.lineWidth = 1;
    for (let x = 0; x < this.W; x += 45) {
      ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, this.H); ctx.stroke();
    }
    for (let y = 0; y < this.H; y += 45) {
      ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(this.W, y); ctx.stroke();
    }
  }

  _render(now) {
    const ctx = this.ctx;
    ctx.save();
    if (this.shakeTime > 0) {
      ctx.translate((Math.random() - 0.5) * 11, (Math.random() - 0.5) * 11);
    }
    this._drawIdleBg(now);

    for (const a of this.aoes) {
      const pct = Math.min(1, a.age / a.warnTime);
      ctx.beginPath();
      ctx.arc(a.x, a.y, a.maxR, 0, Math.PI * 2);
      ctx.fillStyle = a.exploded ? 'rgba(249, 115, 22, 0.65)' : 'rgba(239, 68, 68, 0.14)';
      ctx.fill();
      ctx.strokeStyle = a.exploded ? '#fde047' : 'rgba(248, 113, 113, 0.75)';
      ctx.lineWidth = 2;
      ctx.stroke();
      if (!a.exploded) {
        ctx.beginPath();
        ctx.arc(a.x, a.y, a.maxR * pct, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(249, 115, 22, 0.28)';
        ctx.fill();
      }
    }

    for (const l of this.lasers) {
      ctx.save();
      if (l.age < l.warnTime) {
        ctx.strokeStyle = `rgba(248, 113, 113, ${0.4 + 0.5 * (l.age / l.warnTime)})`;
        ctx.lineWidth = 3;
        ctx.setLineDash([10, 8]);
        ctx.beginPath(); ctx.moveTo(l.x1, l.y1); ctx.lineTo(l.x2, l.y2); ctx.stroke();
      } else {
        ctx.strokeStyle = 'rgba(253, 224, 71, 0.95)';
        ctx.shadowColor = '#f6d365';
        ctx.shadowBlur = 24;
        ctx.lineWidth = l.width;
        ctx.beginPath(); ctx.moveTo(l.x1, l.y1); ctx.lineTo(l.x2, l.y2); ctx.stroke();
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 10;
        ctx.beginPath(); ctx.moveTo(l.x1, l.y1); ctx.lineTo(l.x2, l.y2); ctx.stroke();
      }
      ctx.restore();
    }

    for (const rp of this.ripples) {
      ctx.beginPath();
      ctx.arc(rp.x, rp.y, rp.r, 0, Math.PI * 2);
      ctx.strokeStyle = rp.color;
      ctx.globalAlpha = Math.max(0, rp.alpha);
      ctx.lineWidth = 2.5;
      ctx.stroke();
      ctx.globalAlpha = 1;
    }

    // Estela suave de movimiento del campeón
    for (const tr of this.trail) {
      ctx.beginPath();
      ctx.arc(tr.x, tr.y, 10 * (tr.life / 0.25), 0, Math.PI * 2);
      ctx.fillStyle = `rgba(10, 200, 185, ${tr.life * 0.8})`;
      ctx.fill();
    }

    for (const p of this.projectiles) {
      ctx.save();
      ctx.shadowColor = p.glow;
      ctx.shadowBlur = 16;
      if (p.kind === 'blitz') {
        ctx.strokeStyle = 'rgba(246, 211, 101, 0.5)';
        ctx.lineWidth = 4;
        ctx.beginPath();
        ctx.moveTo(p.x - Math.cos(p.ang) * 44, p.y - Math.sin(p.ang) * 44);
        ctx.lineTo(p.x, p.y);
        ctx.stroke();
      }
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fillStyle = p.color;
      ctx.fill();
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = 2;
      ctx.stroke();
      ctx.restore();
    }

    const isInvuln = now < this.invulnUntil;
    ctx.save();
    if (isInvuln) ctx.globalAlpha = 0.55 + 0.4 * Math.sin(now / 35);
    ctx.beginPath();
    ctx.arc(this.player.x, this.player.y, this.player.r, 0, Math.PI * 2);
    ctx.closePath();
    ctx.clip();
    if (this.playerImg && this.playerImg.complete && this.playerImg.naturalWidth > 0) {
      ctx.drawImage(this.playerImg, this.player.x - this.player.r, this.player.y - this.player.r, this.player.r * 2, this.player.r * 2);
    } else {
      ctx.fillStyle = '#0ac8b9';
      ctx.fill();
    }
    ctx.restore();

    ctx.beginPath();
    ctx.arc(this.player.x, this.player.y, this.player.r + 1, 0, Math.PI * 2);
    ctx.strokeStyle = isInvuln ? '#fde047' : '#c89b3c';
    ctx.lineWidth = 3;
    ctx.stroke();

    for (const pt of this.particles) {
      ctx.fillStyle = pt.color;
      ctx.globalAlpha = Math.max(0, pt.life * 2);
      ctx.fillRect(pt.x - pt.size / 2, pt.y - pt.size / 2, pt.size, pt.size);
    }
    ctx.globalAlpha = 1;

    ctx.font = 'bold 13px Inter, sans-serif';
    ctx.textAlign = 'center';
    for (const ft of this.floatTexts) {
      ctx.fillStyle = ft.color;
      ctx.globalAlpha = Math.max(0, ft.life);
      ctx.fillText(ft.text, ft.x, ft.y);
    }
    ctx.globalAlpha = 1;

    // Banner de Promoción de Rango en vivo
    if (this.rankBanner) {
      ctx.save();
      ctx.globalAlpha = Math.min(1, this.rankBanner.life);
      ctx.font = '800 22px Cinzel, Georgia, serif';
      ctx.fillStyle = this.rankBanner.color;
      ctx.shadowColor = this.rankBanner.color;
      ctx.shadowBlur = 14;
      ctx.fillText(this.rankBanner.text, this.W / 2, 46);
      ctx.restore();
    }

    ctx.restore();
  }

  /* ── Pop-up amigable cuando el usuario está esperando cola ── */
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

    setInterval(() => {
      if (this.idleShown) return;
      const curView = window.app?.state?.currentView;
      if (curView === 'riftdle' || curView === 'draft' || curView === 'ingame') return;
      if (Date.now() - lastActivity >= 30000) {
        this.idleShown = true;
        popup.style.display = 'block';
      }
    }, 5000);
  }
}

document.addEventListener('DOMContentLoaded', () => {
  window.warmupHub = new WarmupHub();
});
