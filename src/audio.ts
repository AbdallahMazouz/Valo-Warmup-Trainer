// =====================================================================
// audio.ts — Procedural audio feedback (no external files required)
// =====================================================================

export class AudioManager {
  private ctx: AudioContext | null = null;
  private volume = 0.6;
  private ready = false;

  init(): void {
    try {
      this.ctx = new AudioContext();
      this.ready = true;
    } catch {
      console.warn('[Audio] AudioContext not available');
    }
  }

  setVolume(v: number): void {
    this.volume = Math.max(0, Math.min(1, v));
  }

  // ── Sounds ──────────────────────────────────────────────────────────
  playHit(headshot = false): void {
    if (headshot) {
      this._beep(1200, 0.06, 'square', 0.18);
    } else {
      this._beep(880,  0.07, 'sine',   0.14);
    }
  }

  playMiss(): void {
    this._beep(180, 0.05, 'sawtooth', 0.08);
  }

  playFlash(): void {
    this._noise(0.3, 0.6);
  }

  playSpawn(): void {
    this._beep(440, 0.03, 'sine', 0.07);
  }

  playPB(): void {
    // Rising arpeggio
    [523, 659, 784, 1046].forEach((f, i) => {
      setTimeout(() => this._beep(f, 0.12, 'sine', 0.25), i * 90);
    });
  }

  playStart(): void {
    this._beep(660, 0.08, 'sine', 0.2);
  }

  playEnd(): void {
    this._beep(330, 0.2, 'sine', 0.2);
  }

  // ── Private synthesis ───────────────────────────────────────────────
  private _beep(
    freq: number,
    dur: number,
    type: OscillatorType = 'sine',
    vol: number = 0.1,
  ): void {
    if (!this.ready || !this.ctx) return;
    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();
    osc.type = type;
    osc.frequency.setValueAtTime(freq, this.ctx.currentTime);
    gain.gain.setValueAtTime(vol * this.volume, this.ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.0001, this.ctx.currentTime + dur);
    osc.connect(gain);
    gain.connect(this.ctx.destination);
    osc.start();
    osc.stop(this.ctx.currentTime + dur + 0.01);
  }

  private _noise(dur: number, vol: number): void {
    if (!this.ready || !this.ctx) return;
    const buf = this.ctx.createBuffer(1, this.ctx.sampleRate * dur, this.ctx.sampleRate);
    const data = buf.getChannelData(0);
    for (let i = 0; i < data.length; i++) data[i] = Math.random() * 2 - 1;
    const src  = this.ctx.createBufferSource();
    const gain = this.ctx.createGain();
    const filt = this.ctx.createBiquadFilter();
    filt.type = 'bandpass';
    filt.frequency.value = 800;
    src.buffer = buf;
    gain.gain.setValueAtTime(vol * this.volume, this.ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.0001, this.ctx.currentTime + dur);
    src.connect(filt);
    filt.connect(gain);
    gain.connect(this.ctx.destination);
    src.start();
  }

  resume(): void {
    if (this.ctx && this.ctx.state === 'suspended') {
      this.ctx.resume().catch(() => {});
    }
  }
}
