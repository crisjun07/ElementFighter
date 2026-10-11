/* ═══════════════════════════════════════════════════════════════
   js/audio.js  —  AudioManager
   Uses Web Audio API to generate placeholder sounds procedurally.
   Replace generateXxx() methods with real audio file loading.

   TO ADD REAL AUDIO:
     Instead of calling generate…(), call:
       AudioManager.loadSound('punch', 'assets/sounds/punch.mp3')
     Then play with: AudioManager.play('punch')
════════════════════════════════════════════════════════════════ */

const AudioManager = (() => {
  let ctx = null;
  let musicVol = 0.5;
  let sfxVol   = 0.8;
  let bgmNode  = null;
  let bgmGain  = null;
  const sfxBuffers = {};

  function ensureCtx() {
    if (!ctx) {
      try { ctx = new (window.AudioContext || window.webkitAudioContext)(); }
      catch { ctx = null; }
    }
    if (ctx && ctx.state === 'suspended') ctx.resume();
    return ctx;
  }

  // ── Procedural SFX generators ─────────────────────────────────

  function playTone(freq, type, duration, vol, decay) {
    const c = ensureCtx(); if (!c) return;
    const osc  = c.createOscillator();
    const gain = c.createGain();
    osc.type = type;
    osc.frequency.setValueAtTime(freq, c.currentTime);
    osc.frequency.exponentialRampToValueAtTime(freq * decay, c.currentTime + duration);
    gain.gain.setValueAtTime(vol * sfxVol, c.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, c.currentTime + duration);
    osc.connect(gain); gain.connect(c.destination);
    osc.start(); osc.stop(c.currentTime + duration);
  }

  function playNoise(duration, vol) {
    const c = ensureCtx(); if (!c) return;
    const bufSize = c.sampleRate * duration;
    const buf = c.createBuffer(1, bufSize, c.sampleRate);
    const data = buf.getChannelData(0);
    for (let i = 0; i < bufSize; i++) data[i] = (Math.random() * 2 - 1) * (1 - i / bufSize);
    const src  = c.createBufferSource();
    const gain = c.createGain();
    src.buffer = buf;
    gain.gain.setValueAtTime(vol * sfxVol, c.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, c.currentTime + duration);
    src.connect(gain); gain.connect(c.destination);
    src.start();
  }

  // ── Named sound effects ───────────────────────────────────────
  const sounds = {
    punch()    { playTone(180, 'square', 0.08, 0.4, 0.5); playNoise(0.05, 0.3); },
    kick()     { playTone(120, 'sawtooth', 0.12, 0.5, 0.4); playNoise(0.07, 0.4); },
    special()  { playTone(440, 'sine', 0.25, 0.6, 2.0); playTone(660, 'sine', 0.2, 0.3, 1.5); },
    ultimate() {
      for (let i = 0; i < 3; i++) {
        setTimeout(() => playTone(220 + i*110, 'sawtooth', 0.4, 0.5, 0.5), i * 80);
      }
      playNoise(0.5, 0.6);
    },
    hit()      { playNoise(0.06, 0.5); playTone(200, 'square', 0.06, 0.3, 0.3); },
    block()    { playTone(600, 'square', 0.05, 0.3, 0.8); },
    victory()  {
      const notes = [523, 659, 784, 1047];
      notes.forEach((n, i) => setTimeout(() => playTone(n, 'sine', 0.3, 0.4, 1.0), i * 120));
    },
    defeat()   {
      const notes = [523, 415, 330, 262];
      notes.forEach((n, i) => setTimeout(() => playTone(n, 'sine', 0.4, 0.35, 0.8), i * 160));
    },
    click()    { playTone(800, 'sine', 0.05, 0.2, 1.2); },
    combo()    { playTone(880, 'sine', 0.15, 0.4, 1.5); },
    levelUp()  {
      [523,659,784,1047,1319].forEach((n,i)=>setTimeout(()=>playTone(n,'sine',.25,.5,1),i*100));
    },
    gacha()    {
      for (let i = 0; i < 8; i++)
        setTimeout(()=>playTone(400+i*60,'sine',.2,.3,1.5), i*80);
    },
    jump()     { playTone(300, 'sine', 0.1, 0.2, 2.0); },
    dash()     { playNoise(0.05, 0.25); playTone(500, 'sine', 0.08, 0.15, 0.5); },
  };

  // ── BGM (simple procedural loop) ─────────────────────────────
  function startBGM(theme) {
    const c = ensureCtx(); if (!c) return;
    stopBGM();
    // A simple drone + arpeggiated loop per theme
    const freqMap = {
      fire: [220,277,330,415], water:[196,247,294,370],
      earth:[165,220,277,330], lightning:[330,415,494,622],
      wind:[247,311,370,466],  ice:[262,330,392,494],
      nature:[196,247,294,370],light:[330,415,494,622],
      dark:[185,233,277,370],  poison:[220,277,330,415],
      menu:[220,277,330,440],  default:[220,277,330,415],
    };
    const notes = freqMap[theme] || freqMap.default;
    bgmGain = c.createGain();
    bgmGain.gain.setValueAtTime(musicVol * 0.18, c.currentTime);
    bgmGain.connect(c.destination);

    let beatTime = c.currentTime;
    const BPM = 90, beatLen = 60 / BPM;
    const pattern = [0,2,1,3, 0,2,3,1];

    function scheduleBeat(time, idx) {
      const osc = c.createOscillator();
      const g   = c.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(notes[pattern[idx % pattern.length]], time);
      g.gain.setValueAtTime(0.6, time);
      g.gain.exponentialRampToValueAtTime(0.001, time + beatLen * 0.8);
      osc.connect(g); g.connect(bgmGain);
      osc.start(time); osc.stop(time + beatLen * 0.8);
    }

    let i = 0;
    function scheduleAhead() {
      while (beatTime < c.currentTime + 2.0) {
        scheduleBeat(beatTime, i++);
        beatTime += beatLen;
      }
    }
    scheduleAhead();
    bgmNode = setInterval(scheduleAhead, 1000);
  }

  function stopBGM() {
    if (bgmNode) { clearInterval(bgmNode); bgmNode = null; }
    if (bgmGain) { try { bgmGain.disconnect(); } catch {} bgmGain = null; }
  }

  function setMusicVol(v) {
    musicVol = v / 100;
    if (bgmGain) bgmGain.gain.setValueAtTime(musicVol * 0.18, ctx.currentTime);
  }

  function setSfxVol(v) { sfxVol = v / 100; }

  function play(name) {
    if (sounds[name]) {
      try { sounds[name](); } catch {}
    }
  }

  return { play, startBGM, stopBGM, setMusicVol, setSfxVol, ensureCtx };
})();
