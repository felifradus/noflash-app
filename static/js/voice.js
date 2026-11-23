/* ═══════════════════════════════════════════════════════
   NoFlash — Voice Coach (Voz Neuronal Real vía /api/tts)
   Usa edge-tts (Elena AR, Aria US, Francisca BR, etc.) en HTML5 Audio
   ═══════════════════════════════════════════════════════ */

const VOICE_PREVIEWS = {
  calm_f: {
    en: 'No Flash is ready. Soft voice, short callouts, zero distractions.',
    es: 'No Flash listo. Voz calma y avisos cortos para mantener el foco.',
  },
  calm_m: {
    en: 'No Flash is ready. Calm callouts so you stay focused in-game.',
    es: 'No Flash listo. Avisos tranquilos para que no pierdas la concentración.',
  },
  announcer: {
    en: 'Welcome to Summoner’s Rift. No Flash is online.',
    es: 'Bienvenido a la Grieta. No Flash está activo.',
  },
  caster: {
    en: 'Draft is live. Stay sharp and control river vision.',
    es: 'Draft en vivo. Mantené el foco y controlá el río.',
  },
};

class VoiceCoach {
  constructor() {
    this.enabled = localStorage.getItem('NoFlash_voice_enabled') !== 'false';
    const saved = localStorage.getItem('NoFlash_voice_persona') || 'calm_m';
    this.persona = VOICE_PREVIEWS[saved] ? saved : 'calm_m';
    this.volume = parseFloat(localStorage.getItem('NoFlash_voice_vol') || '0.55');
    if (Number.isNaN(this.volume) || this.volume < 0.1 || this.volume > 1.0) this.volume = 0.55;
    this.spokenIds = new Set();
    this.lastSpokenText = '';
    this.lastSpokenAt = 0;
    this.currentAudio = null;
  }

  setVolume(v) {
    this.volume = Math.min(1.0, Math.max(0.1, Number(v) || 0.55));
    localStorage.setItem('NoFlash_voice_vol', String(this.volume));
    if (this.currentAudio) this.currentAudio.volume = this.volume;
  }

  getPersona() {
    return this.persona;
  }

  setPersona(persona, playPreview = true) {
    this.persona = persona || 'pro_f';
    localStorage.setItem('NoFlash_voice_persona', this.persona);
    if (playPreview) {
      const lang = (typeof getCurrentLang === 'function') ? getCurrentLang() : 'es';
      const lines = VOICE_PREVIEWS[this.persona] || VOICE_PREVIEWS.pro_f;
      const line = lang === 'es' ? lines.es : lines.en;
      this.speak(line, { force: true });
    }
  }

  isEnabled() {
    return this.enabled;
  }

  toggle() {
    this.enabled = !this.enabled;
    localStorage.setItem('NoFlash_voice_enabled', String(this.enabled));
    if (!this.enabled) {
      this.stop();
    }
    return this.enabled;
  }

  stop() {
    if (this.currentAudio) {
      try {
        this.currentAudio.pause();
        this.currentAudio.currentTime = 0;
      } catch {}
      this.currentAudio = null;
    }
    if ('speechSynthesis' in window) {
      try { window.speechSynthesis.cancel(); } catch {}
    }
  }

  async speak(text, { force = false, dedupeId = null } = {}) {
    if (!force && !this.enabled) return;
    if (!text || !text.trim()) return;
    if (dedupeId && this.spokenIds.has(dedupeId)) return;

    const now = Date.now();
    // Anti-spam: mínimo 25s entre avisos automáticos para no desconcentrar en partida
    if (!force && now - this.lastSpokenAt < 25000) {
      return;
    }
    if (!force && text === this.lastSpokenText && now - this.lastSpokenAt < 60000) {
      return;
    }

    if (dedupeId) this.spokenIds.add(dedupeId);
    this.lastSpokenText = text;
    this.lastSpokenAt = now;

    this.stop();
    this._reqId = (this._reqId || 0) + 1;
    const myReqId = this._reqId;

    const lang = (typeof getCurrentLang === 'function') ? getCurrentLang() : 'en';
    const url = `/api/tts?text=${encodeURIComponent(text)}&lang=${encodeURIComponent(lang)}&persona=${encodeURIComponent(this.persona)}`;

    try {
      const res = await fetch(url);
      if (!res.ok || myReqId !== this._reqId) return;
      const blob = await res.blob();
      if (myReqId !== this._reqId) return;
      const objUrl = URL.createObjectURL(blob);
      const audio = new Audio(objUrl);
      audio.volume = this.volume;
      audio.onended = () => URL.revokeObjectURL(objUrl);
      this.currentAudio = audio;
      await audio.play();
    } catch (err) {
      // Silencioso: NUNCA usar speechSynthesis robótico de Windows
    }
  }

  speakDraftAdvice(recommendations, coach, force = false) {
    if (!recommendations || recommendations.length === 0) return;
    const top = recommendations[0];
    const lang = (typeof getCurrentLang === 'function') ? getCurrentLang() : 'es';
    const isEs = lang === 'es';
    const parts = [];

    if (coach && coach.recommended_bans && coach.recommended_bans.length > 0 && force) {
      parts.push(
        isEs
          ? `Te recomiendo banear ${coach.recommended_bans[0].champion}.`
          : `Recommended ban: ${coach.recommended_bans[0].champion}.`
      );
    }

    parts.push(
      isEs
        ? `Tu mejor pick ahora es ${top.champion}.`
        : `Your best pick right now is ${top.champion}.`
    );

    if (top.setup && top.setup.spells && top.setup.spells.length === 2) {
      const sp2 = top.setup.spells[1].split('(')[0].trim();
      const low = sp2.toLowerCase();
      if (low.includes('limpiar') || low.includes('cleanse') || low.includes('extenuar') || low.includes('exhaust')) {
        parts.push(isEs ? `Llevá ${sp2} por la composición enemiga.` : `Take ${sp2} against this enemy comp.`);
      }
    }

    this.speak(parts.join(' '), { force });
  }
}

window.voiceCoach = new VoiceCoach();

document.addEventListener('DOMContentLoaded', () => {
  const sel = document.getElementById('voice-persona-select');
  if (sel) {
    sel.value = window.voiceCoach.getPersona();
    sel.addEventListener('change', () => {
      window.voiceCoach.setPersona(sel.value, true);
    });
  }
  const slider = document.getElementById('voice-volume-slider');
  const lbl = document.getElementById('voice-volume-label');
  if (slider) {
    const pct = Math.round((window.voiceCoach.volume || 0.55) * 100);
    slider.value = String(pct);
    if (lbl) lbl.textContent = `${pct}%`;
    slider.addEventListener('input', () => {
      const val = parseInt(slider.value, 10) || 55;
      window.voiceCoach.setVolume(val / 100);
      if (lbl) lbl.textContent = `${val}%`;
    });
  }
});
