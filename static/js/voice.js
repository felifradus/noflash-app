/* ═══════════════════════════════════════════════════════
   RiftMind — Voice Coach (Voz Neuronal Real vía /api/tts)
   Usa edge-tts (Elena AR, Aria US, Francisca BR, etc.) en HTML5 Audio
   ═══════════════════════════════════════════════════════ */

class VoiceCoach {
  constructor() {
    this.enabled = localStorage.getItem('riftmind_voice_enabled') !== 'false';
    this.spokenIds = new Set();
    this.lastSpokenText = '';
    this.lastSpokenAt = 0;
    this.currentAudio = null;
  }

  isEnabled() {
    return this.enabled;
  }

  toggle() {
    this.enabled = !this.enabled;
    localStorage.setItem('riftmind_voice_enabled', String(this.enabled));
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
    if (!force && text === this.lastSpokenText && now - this.lastSpokenAt < 15000) {
      return;
    }

    if (dedupeId) this.spokenIds.add(dedupeId);
    this.lastSpokenText = text;
    this.lastSpokenAt = now;

    this.stop();

    const lang = (typeof getCurrentLang === 'function') ? getCurrentLang() : 'es';
    const url = `/api/tts?text=${encodeURIComponent(text)}&lang=${encodeURIComponent(lang)}`;

    try {
      const audio = new Audio(url);
      audio.volume = 0.92;
      this.currentAudio = audio;
      await audio.play();
    } catch (err) {
      // Fallback a speechSynthesis si no hay conexión
      if ('speechSynthesis' in window) {
        try {
          const utter = new SpeechSynthesisUtterance(text);
          utter.lang = lang === 'es' ? 'es-AR' : lang;
          window.speechSynthesis.speak(utter);
        } catch {}
      }
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
