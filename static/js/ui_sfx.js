/* ═══════════════════════════════════════════════════════
   NoFlash — Hextech UI Sound Design (WebAudio API)
   Sonidos táctiles sutiles estilo Cliente Oficial de LoL (0ms latencia)
   ═══════════════════════════════════════════════════════ */

class HextechUISfx {
  constructor() {
    this.ctx = null;
    this.enabled = localStorage.getItem('NoFlash_sfx_enabled') !== 'false';
    this.bindGlobalDelegation();
  }

  _ctx() {
    if (!this.enabled) return null;
    if (!this.ctx) {
      const AC = window.AudioContext || window.webkitAudioContext;
      if (AC) this.ctx = new AC();
    }
    if (this.ctx && this.ctx.state === 'suspended') {
      this.ctx.resume().catch(() => {});
    }
    return this.ctx;
  }

  _tone(freqStart, freqEnd, dur, type = 'sine', vol = 0.06, delay = 0) {
    const ctx = this._ctx();
    if (!ctx) return;
    const t = ctx.currentTime + delay;
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = type;
    osc.frequency.setValueAtTime(freqStart, t);
    if (freqEnd && freqEnd !== freqStart) {
      osc.frequency.exponentialRampToValueAtTime(freqEnd, t + dur);
    }
    gain.gain.setValueAtTime(0.0001, t);
    gain.gain.linearRampToValueAtTime(vol, t + 0.01);
    gain.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start(t);
    osc.stop(t + dur + 0.02);
  }

  // Cambio de pestaña suave y cristalino
  playTab() {
    this._tone(540, 720, 0.075, 'triangle', 0.045);
  }

  // Click táctil Hextech en botones
  playClick() {
    this._tone(420, 560, 0.055, 'sine', 0.04);
  }

  // Click de cronómetro al marcar hechizo enemigo en partida
  playSpellTick() {
    this._tone(880, 620, 0.08, 'triangle', 0.065);
  }

  // Enviar intento en Flashdle (flip suave)
  playTileFlip() {
    this._tone(360, 480, 0.06, 'triangle', 0.05, 0);
    this._tone(480, 600, 0.06, 'triangle', 0.04, 0.055);
  }

  // Éxito / Runas importadas / Análisis listo / Copia
  playSuccess() {
    this._tone(523.25, 523.25, 0.12, 'triangle', 0.065, 0);
    this._tone(659.25, 659.25, 0.14, 'triangle', 0.07, 0.07);
    this._tone(783.99, 1046.5, 0.22, 'sine', 0.07, 0.14);
  }

  // Detección de Draft en vivo o Partida iniciada (acorde Hextech profundo)
  playLockIn() {
    this._tone(220, 330, 0.16, 'triangle', 0.07, 0);
    this._tone(440, 659.25, 0.24, 'sine', 0.065, 0.09);
  }

  // Victoria en Flashdle
  playVictory() {
    [523.25, 659.25, 783.99, 1046.5].forEach((f, i) => {
      this._tone(f, f * 1.01, 0.22, 'triangle', 0.075, i * 0.08);
    });
  }

  bindGlobalDelegation() {
    document.addEventListener('click', (e) => {
      const target = e.target;
      if (!target || typeof target.closest !== 'function') return;

      if (target.closest('.nav-tab, .warmup-tab, .role-tab, .role-btn')) {
        this.playTab();
      } else if (target.closest('.ig-spell-btn')) {
        this.playSpellTick();
      } else if (target.closest('.btn-analyze, .btn-import-lcu, .btn-copy-chat, .btn-switch-account, .btn-otra-cuenta, .idle-btn, .champ-card, .win-btn, .tb-util-btn, .btn-habit-test')) {
        this.playClick();
      }
    }, { passive: true });
  }
}

window.uiSfx = new HextechUISfx();
