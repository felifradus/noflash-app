/* ═══════════════════════════════════════════════════════
   NoFlash — Subtle Modern UI Sound Design (Riot Client / macOS vibe)
   Micro-taps suaves filtrados (cero beeps 8-bit / arcade)
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

  // Micro-tap orgánico de baja frecuencia (suena como vidrio/metal suave, nunca beep)
  _softTap(freq = 280, dur = 0.032, vol = 0.032) {
    const ctx = this._ctx();
    if (!ctx) return;
    const t = ctx.currentTime;
    const osc = ctx.createOscillator();
    const filter = ctx.createBiquadFilter();
    const gain = ctx.createGain();
    osc.type = 'sine';
    osc.frequency.setValueAtTime(freq, t);
    osc.frequency.exponentialRampToValueAtTime(freq * 0.55, t + dur);
    filter.type = 'lowpass';
    filter.frequency.setValueAtTime(750, t);
    gain.gain.setValueAtTime(0.0001, t);
    gain.gain.linearRampToValueAtTime(vol, t + 0.004);
    gain.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    osc.connect(filter);
    filter.connect(gain);
    gain.connect(ctx.destination);
    osc.start(t);
    osc.stop(t + dur + 0.01);
  }

  // Acorde atmosférico muy sutil (sin arpegio arcade)
  _softChord(freqs, dur = 0.24, vol = 0.025) {
    const ctx = this._ctx();
    if (!ctx) return;
    const t = ctx.currentTime;
    const filter = ctx.createBiquadFilter();
    filter.type = 'lowpass';
    filter.frequency.setValueAtTime(900, t);
    filter.connect(ctx.destination);

    freqs.forEach((f) => {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(f, t);
      gain.gain.setValueAtTime(0.0001, t);
      gain.gain.linearRampToValueAtTime(vol, t + 0.025);
      gain.gain.exponentialRampToValueAtTime(0.0001, t + dur);
      osc.connect(gain);
      gain.connect(filter);
      osc.start(t);
      osc.stop(t + dur + 0.02);
    });
  }

  playTab()       { this._softTap(320, 0.028, 0.026); }
  playClick()     { this._softTap(240, 0.024, 0.024); }
  playSpellTick() { this._softTap(460, 0.035, 0.038); }
  playTileFlip()  { this._softTap(290, 0.030, 0.028); }
  playSuccess()   { this._softChord([329.63, 493.88], 0.28, 0.028); }
  playLockIn()    { this._softChord([196.00, 293.66], 0.32, 0.032); }
  playVictory()   { this._softChord([261.63, 329.63, 392.00], 0.36, 0.030); }

  bindGlobalDelegation() {
    document.addEventListener('click', (e) => {
      const target = e.target;
      if (!target || typeof target.closest !== 'function') return;

      if (target.closest('.nav-tab, .warmup-tab, .role-tab, .role-btn')) {
        this.playTab();
      } else if (target.closest('.ig-spell-btn')) {
        this.playSpellTick();
      } else if (target.closest('.btn-analyze, .btn-import-lcu, .btn-copy-chat')) {
        this.playClick();
      }
    }, { passive: true });
  }
}

window.uiSfx = new HextechUISfx();
