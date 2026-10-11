/* ═══════════════════════════════════════════════════════════════
   js/sprites.js  —  SpriteManager + SpriteAnimator
   ───────────────────────────────────────────────────────────────
   Two-tier rendering:
     TIER 1 — Real PNGs:  assets/sprites/<id>/<anim>/<anim>-N.png
              Loaded on demand; missing frames fall back to Tier 2.
     TIER 2 — Procedural: canvas-drawn humanoid with elemental fx.
              Always available, no files required.

   HOW TO ADD REAL SPRITES FOR ANY CHARACTER
   ──────────────────────────────────────────
   1. Run tools/slice_blazor.py to extract Blazor frames, OR
      manually place PNGs as:
        assets/sprites/<charId>/<animName>/<animName>-1.png
        assets/sprites/<charId>/<animName>/<animName>-2.png  …
   2. Update the character's animations block in data/characters.js
      with the correct { frames, fps, frameW, frameH } values.
   3. That's it — the engine detects PNGs automatically.
════════════════════════════════════════════════════════════════ */

/* ── roundRect polyfill (Safari < 15.4) ───────────────────────── */
if (typeof CanvasRenderingContext2D !== 'undefined' &&
    !CanvasRenderingContext2D.prototype.roundRect) {
  CanvasRenderingContext2D.prototype.roundRect = function (x, y, w, h, r) {
    r = Math.min(r, w / 2, h / 2);
    this.beginPath();
    this.moveTo(x + r, y);
    this.arcTo(x + w, y,     x + w, y + h, r);
    this.arcTo(x + w, y + h, x,     y + h, r);
    this.arcTo(x,     y + h, x,     y,     r);
    this.arcTo(x,     y,     x + w, y,     r);
    this.closePath();
    return this;
  };
}

/* ════════════════════════════════════════════════════════════════
   SpriteAnimator
   One instance per fighter in a battle.
   Tracks current animation, current frame, elapsed time,
   and draws the correct PNG (or procedural fallback).
════════════════════════════════════════════════════════════════ */
class SpriteAnimator {
  /**
   * @param {object} charData   Full character definition from CHARACTERS[]
   */
  constructor(charData) {
    this.charData   = charData;
    this.charId     = charData.id;

    // Current playback state
    this.currentAnim  = 'idle';
    this.frameIndex   = 0;
    this.elapsed      = 0;      // ms since last frame advance
    this.looping      = true;   // most anims loop; attacks play once
    this.onComplete   = null;   // callback when a one-shot anim ends

    // Per-animation config (from charData.animations or defaults)
    this.animDefs = charData.animations || {};

    // Image cache: key = "charId/anim/anim-N" → Image | null
    this._cache   = {};
    this._loading = {};          // promises in flight

    // Preload the idle strip immediately
    this._preloadAnim('idle');
  }

  /* ── Public API ─────────────────────────────────────────────── */

  /**
   * Change the playing animation.
   * @param {string}   name      Animation name ('idle','punch', …)
   * @param {boolean}  loop      Loop the animation? (default true)
   * @param {Function} onComplete Called when a non-looping anim finishes
   */
  play(name, loop = true, onComplete = null) {
    if (!this.animDefs[name] && !ANIM_DEFAULTS[name]) return; // unknown
    if (this.currentAnim === name) return; // already playing

    this.currentAnim = name;
    this.frameIndex  = 0;
    this.elapsed     = 0;
    this.looping     = loop;
    this.onComplete  = onComplete;

    this._preloadAnim(name);
  }

  /**
   * Advance the animation timer.
   * @param {number} dt  Delta-time in ms
   */
  update(dt) {
    const def      = this._def(this.currentAnim);
    const frameDur = 1000 / def.fps;          // ms per frame

    this.elapsed += dt;
    if (this.elapsed >= frameDur) {
      this.elapsed -= frameDur;
      this.frameIndex++;

      if (this.frameIndex >= def.frames) {
        if (this.looping) {
          this.frameIndex = 0;
        } else {
          this.frameIndex = def.frames - 1;   // hold last frame
          if (this.onComplete) {
            const cb = this.onComplete;
            this.onComplete = null;
            cb();
          }
        }
      }
    }
  }

  /**
   * Draw the current frame onto a canvas context.
   * Falls back to procedural rendering if PNG not available.
   *
   * @param {CanvasRenderingContext2D} ctx
   * @param {number}  x       Centre-bottom X on canvas
   * @param {number}  y       Centre-bottom Y on canvas
   * @param {boolean} flipX   Mirror horizontally (facing left)
   * @param {number}  t       performance.now() for procedural fx
   */
  draw(ctx, x, y, flipX, t) {
    const img = this._getFrame(this.currentAnim, this.frameIndex);

    ctx.save();
    if (flipX) {
      ctx.translate(x, y);
      ctx.scale(-1, 1);
      ctx.translate(-x, -y);
    }

    if (img) {
      this._drawSpritePNG(ctx, img, x, y);
    } else {
      SpriteManager.drawProceduralCharacter(
        ctx, this.charData, x, y, this.currentAnim, this.frameIndex, t
      );
    }

    ctx.restore();
  }

  /* ── Frame retrieval ────────────────────────────────────────── */

  _getFrame(anim, frameIdx) {
    const key = this._key(anim, frameIdx);
    // Return cached image (may be null = confirmed missing)
    if (this._cache[key] !== undefined) return this._cache[key] || null;
    // Not yet attempted — kick off load, return null for now
    this._loadFrame(anim, frameIdx);
    return null;
  }

  _key(anim, frameIdx) {
    return `${this.charId}/${anim}/${frameIdx}`;
  }

  _framePath(anim, frameIdx) {
    const n   = frameIdx + 1;
    const def = this._def(anim);

    // Zero-padded naming: used when frameW <= 80 (Frostia)
    const padded = def.frameW && def.frameW <= 80;
    const num    = padded ? String(n).padStart(2, '0') : String(n);

    return `assets/sprites/${this.charId}/${anim}/${anim}-${num}.png`;
  }

  _loadFrame(anim, frameIdx) {
    const key = this._key(anim, frameIdx);
    if (this._loading[key]) return;   // already in flight
    this._loading[key] = true;

    const src = this._framePath(anim, frameIdx);
    const img = new Image();
    img.onload  = () => { this._cache[key] = img; };
    img.onerror = () => { this._cache[key] = null; }; // mark as missing
    img.src = src;
  }

  /** Pre-load all frames for an animation in the background */
  _preloadAnim(anim) {
    const def = this._def(anim);
    for (let i = 0; i < def.frames; i++) this._loadFrame(anim, i);
  }

  /** Get animation definition, falling back to built-in defaults */
  _def(anim) {
    return (this.animDefs && this.animDefs[anim]) || ANIM_DEFAULTS[anim] || ANIM_DEFAULTS.idle;
  }

  /* ── PNG draw ───────────────────────────────────────────────── */

  _drawSpritePNG(ctx, img, cx, cy) {
    const def = this._def(this.currentAnim);

    // Display size — characters rendered at 128×128 on the battle canvas
    const DISPLAY_W = 128;
    const DISPLAY_H = 128;

    // Draw shadow
    ctx.save();
    ctx.globalAlpha = 0.25;
    ctx.fillStyle   = '#000';
    ctx.beginPath();
    ctx.ellipse(cx, cy - 3, DISPLAY_W * 0.38, 7, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();

    // Draw sprite — centred horizontally, bottom-anchored, scaled to display size
    ctx.drawImage(img, cx - DISPLAY_W / 2, cy - DISPLAY_H, DISPLAY_W, DISPLAY_H);
  }
}

/* ── Default animation specs (used when charData.animations is absent) ── */
const ANIM_DEFAULTS = {
  idle:     { frames: 8,  fps: 8,  frameW: 96, frameH: 96 },
  walk:     { frames: 8,  fps: 10, frameW: 96, frameH: 96 },
  run:      { frames: 8,  fps: 14, frameW: 96, frameH: 96 },
  jump:     { frames: 6,  fps: 10, frameW: 96, frameH: 96 },
  dash:     { frames: 6,  fps: 14, frameW: 96, frameH: 96 },
  block:    { frames: 4,  fps: 6,  frameW: 96, frameH: 96 },
  punch:    { frames: 6,  fps: 14, frameW: 96, frameH: 96 },
  kick:     { frames: 6,  fps: 14, frameW: 96, frameH: 96 },
  special:  { frames: 8,  fps: 12, frameW: 96, frameH: 96 },
  ultimate: { frames: 10, fps: 12, frameW: 96, frameH: 96 },
  hurt:     { frames: 4,  fps: 10, frameW: 96, frameH: 96 },
  victory:  { frames: 6,  fps: 8,  frameW: 96, frameH: 96 },
  defeat:   { frames: 6,  fps: 8,  frameW: 96, frameH: 96 },
};

/* ── Animation state rules ────────────────────────────────────────
   Which animations loop and which play once then signal completion.
────────────────────────────────────────────────────────────────── */
const ANIM_RULES = {
  //  name        loop    one-shot
  idle:     { loop: true  },
  walk:     { loop: true  },
  run:      { loop: true  },
  jump:     { loop: false },
  dash:     { loop: false },
  block:    { loop: true  },
  punch:    { loop: false },
  kick:     { loop: false },
  special:  { loop: false },
  ultimate: { loop: false },
  hurt:     { loop: false },
  victory:  { loop: true  },
  defeat:   { loop: false },
};

/* ════════════════════════════════════════════════════════════════
   SpriteManager (static utilities + procedural renderer)
   Accessed globally as SpriteManager.xxx
════════════════════════════════════════════════════════════════ */
const SpriteManager = (() => {

  /* ── Element visual effects ──────────────────────────────────── */
  const ELEMENT_EFFECTS = {
    fire:      { particle: '#ff6600', glow: '#ff4400', trail: true  },
    water:     { particle: '#44aaff', glow: '#0088ff', trail: true  },
    earth:     { particle: '#cc8833', glow: '#885522', trail: false },
    lightning: { particle: '#ffee00', glow: '#ffcc00', trail: true  },
    wind:      { particle: '#aaffaa', glow: '#66ee66', trail: true  },
    ice:       { particle: '#aaffff', glow: '#44ddee', trail: true  },
    nature:    { particle: '#88ff44', glow: '#44aa22', trail: false },
    light:     { particle: '#ffffaa', glow: '#ffee44', trail: true  },
    dark:      { particle: '#cc44ff', glow: '#8822cc', trail: true  },
    poison:    { particle: '#aaff44', glow: '#77ee22', trail: false },
  };

  /* ── Map image cache ─────────────────────────────────────────── */
  const _mapCache = {};   // path → Image | null

  function _loadMapImage(src) {
    if (_mapCache[src] !== undefined) return; // already loading/loaded
    _mapCache[src] = null; // mark as loading
    const img = new Image();
    img.onload  = () => { _mapCache[src] = img; };
    img.onerror = () => { _mapCache[src] = null; };
    img.src = src;
  }

  /* ── Arena background ────────────────────────────────────────── */
  /**
   * @param {string|null} mapPath  e.g. 'assets/maps/blazor_map.png'
   *   When provided, draws the real map PNG scaled to fill the canvas.
   *   Falls back to the procedural gradient if the image isn't loaded yet.
   */
  function drawArena(ctx, w, h, bgColors, theme, t, mapPath) {
    const time = t * 0.001;
    const ef   = ELEMENT_EFFECTS[theme] || ELEMENT_EFFECTS.fire;

    // ── Try real map PNG first ────────────────────────────────────
    if (mapPath) {
      _loadMapImage(mapPath);           // no-op if already cached
      const mapImg = _mapCache[mapPath];

      if (mapImg) {
        // Draw map scaled to fill canvas (cover mode)
        const scale  = Math.max(w / mapImg.width, h / mapImg.height);
        const dw     = mapImg.width  * scale;
        const dh     = mapImg.height * scale;
        const dx     = (w - dw) / 2;
        const dy     = (h - dh) / 2;
        ctx.drawImage(mapImg, dx, dy, dw, dh);

        // Subtle elemental overlay on top of the map
        ctx.save();
        ctx.globalAlpha = 0.18 + Math.sin(time * 0.8) * 0.04;
        const ov = ctx.createLinearGradient(0, 0, 0, h);
        ov.addColorStop(0,   'transparent');
        ov.addColorStop(0.7, 'transparent');
        ov.addColorStop(1,   'rgba(0,0,0,0.55)');
        ctx.fillStyle = ov;
        ctx.fillRect(0, 0, w, h);
        ctx.restore();

        // Ground glow line (always shown so fighters have a clear floor)
        const gY = getGroundY(h);
        ctx.save();
        ctx.shadowBlur  = 20; ctx.shadowColor = ef.glow;
        ctx.strokeStyle = ef.particle; ctx.lineWidth = 2.5;
        ctx.beginPath(); ctx.moveTo(0, gY); ctx.lineTo(w, gY); ctx.stroke();
        ctx.shadowBlur = 0;
        ctx.restore();

        // Elemental floating particles (always shown)
        ctx.save();
        ctx.globalAlpha = 0.25;
        for (let i = 0; i < 8; i++) {
          const px = ((i * 137.5 + time * 25) % w);
          const py = gY * 0.1 + ((i * 89 + time * 12) % (gY * 0.65));
          ctx.fillStyle = ef.particle;
          ctx.shadowBlur = 6; ctx.shadowColor = ef.particle;
          ctx.beginPath(); ctx.arc(px, py, 1.5 + (i % 3), 0, Math.PI * 2); ctx.fill();
        }
        ctx.shadowBlur = 0;
        ctx.restore();
        return;  // map drawn — skip procedural
      }
      // else: image not loaded yet → fall through to procedural
    }

    // ── Procedural gradient fallback ─────────────────────────────
    const grad = ctx.createLinearGradient(0, 0, 0, h);
    grad.addColorStop(0,   bgColors[0] || '#050a14');
    grad.addColorStop(0.6, bgColors[1] || '#0a1428');
    grad.addColorStop(1,   bgColors[2] || '#1a2840');
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, w, h);

    // Ambient glow orbs
    ctx.save();
    ctx.globalAlpha = 0.08 + Math.sin(time) * 0.03;
    const og1 = ctx.createRadialGradient(w*0.2, h*0.3, 10, w*0.2, h*0.3, w*0.3);
    og1.addColorStop(0, ef.glow); og1.addColorStop(1, 'transparent');
    ctx.fillStyle = og1; ctx.fillRect(0, 0, w, h);
    const og2 = ctx.createRadialGradient(w*0.8, h*0.4, 10, w*0.8, h*0.4, w*0.25);
    og2.addColorStop(0, ef.particle); og2.addColorStop(1, 'transparent');
    ctx.fillStyle = og2; ctx.fillRect(0, 0, w, h);
    ctx.restore();

    // Ground
    const gY = getGroundY(h);
    const gg = ctx.createLinearGradient(0, gY, 0, h);
    gg.addColorStop(0, bgColors[2] || '#1a2840');
    gg.addColorStop(1, '#000');
    ctx.fillStyle = gg;
    ctx.fillRect(0, gY, w, h - gY);

    // Ground glow line
    ctx.save();
    ctx.shadowBlur = 16; ctx.shadowColor = ef.glow;
    ctx.strokeStyle = ef.particle; ctx.lineWidth = 2;
    ctx.beginPath(); ctx.moveTo(0, gY); ctx.lineTo(w, gY); ctx.stroke();
    ctx.shadowBlur = 0;
    ctx.restore();

    // Floating bg particles
    ctx.save();
    ctx.globalAlpha = 0.15;
    for (let i = 0; i < 12; i++) {
      const px = ((i * 137.5 + time * 30) % w);
      const py = gY * 0.2 + ((i * 73 + time * 15) % (gY * 0.6));
      ctx.fillStyle = ef.particle;
      ctx.beginPath(); ctx.arc(px, py, 1.5 + (i % 3), 0, Math.PI * 2); ctx.fill();
    }
    ctx.restore();
  }

  function getGroundY(h) { return Math.floor(h * 0.82); }

  /* ── Bar drawing helper ──────────────────────────────────────── */
  function drawBar(ctx, x, y, w, h, pct, fillColor, bgColor) {
    bgColor = bgColor || 'rgba(0,0,0,0.5)';
    ctx.save();
    ctx.fillStyle = bgColor;
    ctx.beginPath(); ctx.roundRect(x, y, w, h, h / 2); ctx.fill();
    ctx.fillStyle = fillColor;
    ctx.beginPath(); ctx.roundRect(x, y, w * Math.max(0, pct), h, h / 2); ctx.fill();
    ctx.restore();
  }

  /* ────────────────────────────────────────────────────────────────
     PROCEDURAL CHARACTER RENDERER
     Draws a stylised humanoid from canvas primitives.
     Used automatically whenever a real PNG frame isn't loaded yet.
  ──────────────────────────────────────────────────────────────── */
  function drawProceduralCharacter(ctx, char, x, y, anim, frame, t) {
    const col  = char.colors;
    const ef   = ELEMENT_EFFECTS[char.elementKey] || ELEMENT_EFFECTS.fire;
    const time = t * 0.001;
    const pose = _getPose(anim, frame, time);

    const BASE_H = 160;  // procedural character height (scaled 2×)
    const bx = x;
    const by = y - BASE_H;

    // Shadow
    ctx.save();
    ctx.globalAlpha = 0.28;
    ctx.fillStyle = '#000';
    ctx.beginPath();
    ctx.ellipse(bx, y - 2, 22, 6, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();

    // Aura glow
    ctx.save();
    ctx.globalAlpha = 0.13 + Math.sin(time * 3) * 0.05;
    const ag = ctx.createRadialGradient(bx, by + BASE_H / 2, 10, bx, by + BASE_H / 2, 44);
    ag.addColorStop(0, ef.glow); ag.addColorStop(1, 'transparent');
    ctx.fillStyle = ag;
    ctx.beginPath();
    ctx.ellipse(bx, by + BASE_H / 2, 40, 50, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();

    // Legs
    _limb(ctx, bx + pose.llx, by + 54 + pose.lly,  bx + pose.llx + 6, by + BASE_H + pose.lly2, 8, col.primary);
    _limb(ctx, bx + pose.rlx, by + 54 + pose.rly,  bx + pose.rlx + 4, by + BASE_H + pose.rly2, 8, col.secondary);

    // Torso
    ctx.save();
    ctx.translate(bx + pose.bx, by + 28 + pose.by);
    ctx.rotate(pose.br);
    const tg = ctx.createLinearGradient(-14, -26, 14, 26);
    tg.addColorStop(0, col.primary); tg.addColorStop(1, col.secondary);
    ctx.fillStyle = tg;
    ctx.beginPath(); ctx.roundRect(-14, -26, 28, 52, 6); ctx.fill();
    ctx.fillStyle = 'rgba(255,255,255,0.1)';
    ctx.beginPath(); ctx.roundRect(-10, -22, 20, 20, 4); ctx.fill();
    ctx.restore();

    // Arms
    _limb(ctx, bx + pose.lax, by + 16 + pose.lay, bx + pose.lax + pose.lhx, by + 40 + pose.lhy, 7, col.primary);
    _limb(ctx, bx + pose.rax, by + 16 + pose.ray, bx + pose.rax + pose.rhx, by + 40 + pose.rhy, 7, col.secondary);

    // Attack effect
    if (anim === 'punch' || anim === 'special' || anim === 'ultimate') {
      _gauntlet(ctx, bx + pose.rax + pose.rhx, by + 40 + pose.rhy, col.accent, ef, time, anim);
    }
    if (anim === 'kick') {
      _gauntlet(ctx, bx + pose.llx + 6, by + BASE_H + pose.lly2, col.accent, ef, time, 'kick');
    }

    // Head
    ctx.save();
    ctx.translate(bx + pose.hx, by + pose.hy);
    ctx.rotate(pose.hr);
    ctx.fillStyle = col.primary;
    ctx.beginPath(); ctx.ellipse(0, 0, 14, 14, 0, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = '#050a14';
    ctx.beginPath(); ctx.ellipse(2, 2, 9, 9, 0, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = col.eyes;
    ctx.shadowBlur = 8; ctx.shadowColor = col.eyes;
    ctx.beginPath(); ctx.ellipse(-4, 0, 3, 2, 0, 0, Math.PI * 2); ctx.fill();
    ctx.beginPath(); ctx.ellipse( 4, 0, 3, 2, 0, 0, Math.PI * 2); ctx.fill();
    ctx.shadowBlur = 0;
    ctx.restore();

    // Flame hair
    _hair(ctx, bx + pose.hx, by + pose.hy - 14, col, ef, time, anim);

    // Elemental particles
    if (ef.trail) _particles(ctx, bx, by, ef, time, anim);
  }

  // ── Procedural helpers ────────────────────────────────────────
  function _limb(ctx, x1, y1, x2, y2, w, col) {
    ctx.save();
    ctx.strokeStyle = col; ctx.lineWidth = w; ctx.lineCap = 'round';
    ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke();
    ctx.restore();
  }

  function _gauntlet(ctx, gx, gy, col, ef, time, anim) {
    const r = anim === 'ultimate' ? 22 : anim === 'special' ? 16 : 10;
    ctx.save();
    ctx.globalAlpha = 0.7 + Math.sin(time * 8) * 0.3;
    const g = ctx.createRadialGradient(gx, gy, 2, gx, gy, r);
    g.addColorStop(0, '#fff'); g.addColorStop(0.4, col); g.addColorStop(1, 'transparent');
    ctx.fillStyle = g;
    ctx.beginPath(); ctx.arc(gx, gy, r, 0, Math.PI * 2); ctx.fill();
    ctx.restore();
  }

  function _hair(ctx, hx, hy, col, ef, time, anim) {
    ctx.save(); ctx.globalAlpha = 0.9;
    for (let i = -2; i <= 2; i++) {
      const px = hx + i * 5;
      const h  = 10 + Math.sin(time * 4 + i) * 4 + (anim === 'ultimate' ? 8 : 0);
      const g  = ctx.createLinearGradient(px, hy, px, hy - h);
      g.addColorStop(0, col.hair); g.addColorStop(1, 'transparent');
      ctx.strokeStyle = g; ctx.lineWidth = 3; ctx.lineCap = 'round';
      ctx.beginPath(); ctx.moveTo(px, hy); ctx.lineTo(px + Math.sin(time * 3 + i) * 3, hy - h); ctx.stroke();
    }
    ctx.restore();
  }

  function _particles(ctx, bx, by, ef, time, anim) {
    const count = anim === 'ultimate' ? 12 : anim === 'special' ? 6 : 3;
    ctx.save();
    for (let i = 0; i < count; i++) {
      const angle = time * 2 + i * (Math.PI * 2 / count);
      const dist  = 28 + Math.sin(time * 3 + i) * 8;
      const px    = bx + Math.cos(angle) * dist;
      const py    = by + 40 + Math.sin(angle * 0.7) * dist * 0.5 - dist * 0.3;
      ctx.globalAlpha = 0.4 + Math.sin(time * 3 + i) * 0.3;
      ctx.fillStyle   = ef.particle;
      ctx.shadowBlur  = 6; ctx.shadowColor = ef.particle;
      ctx.beginPath(); ctx.arc(px, py, 2 + Math.sin(time * 4 + i) * 1.5, 0, Math.PI * 2); ctx.fill();
    }
    ctx.shadowBlur = 0;
    ctx.restore();
  }

  // ── Pose system ───────────────────────────────────────────────
  function _getPose(anim, frame, time) {
    // Compact property names: b=body, h=head, la=leftArm, ra=rightArm
    //   ll=leftLeg, rl=rightLeg, lh=leftHand, rh=rightHand
    const p = {
      bx:0, by:0, br:0,
      hx:0, hy:-48, hr:0,
      lax:-18, lay:0,  lhx:0,  lhy:20,
      rax: 18, ray:0,  rhx:0,  rhy:20,
      llx:-10, lly:0,  lly2:0,
      rlx: 10, rly:0,  rly2:0,
    };
    switch (anim) {
      case 'idle': {
        const b = Math.sin(time * 2) * 2;
        p.by = b; p.hy = -48 + b; p.lay = b; p.ray = b; break;
      }
      case 'walk': case 'run': {
        const spd = anim === 'run' ? 9 : 5;
        const s   = Math.sin(time * spd);
        p.lly2 = s * 8; p.rly2 = -s * 8;
        p.lhy  = 20 + s * 5; p.rhy = 20 - s * 5;
        p.by   = Math.abs(s) * 2; break;
      }
      case 'jump': {
        p.by = -10; p.hy = -58;
        p.lly2 = -12; p.rly2 = -12;
        p.lay  = -8;  p.ray  = -8; break;
      }
      case 'dash': {
        p.br = -0.3; p.bx = 10; p.hx = 8;
        p.rax = 28; p.rhx = 10; break;
      }
      case 'block': {
        p.lax = -4;  p.lay = -10; p.lhx = 10; p.lhy = 0;
        p.rax =  4;  p.ray = -12; p.rhx = 10; p.rhy = 0;
        p.hy  = -40; break;
      }
      case 'punch': {
        const ext = (frame % 4 < 2) ? 20 : 0;
        p.rax = 18 + ext; p.rhx = ext; p.rhy = 18;
        p.br  = (frame % 4 < 2) ? 0.12 : 0; break;
      }
      case 'kick': {
        const ext = (frame % 5 < 3) ? 18 : 0;
        p.llx = -10 + ext; p.lly2 = -ext * 0.5;
        p.br  = (frame % 5 < 3) ? -0.1 : 0; break;
      }
      case 'hurt': {
        p.br = 0.2; p.bx = -8; p.hx = -6;
        p.rax = 28; p.rhx = 8; break;
      }
      case 'defeat': {
        p.br = 0.35; p.bx = -10; p.hy = -35;
        p.lly2 = 12; p.rly2 = 4; break;
      }
      case 'special': {
        const c = Math.sin(time * 12) * 4;
        p.rax = 24 + c; p.rhx = 8 + c; p.rhy = 15;
        p.lax = -24; p.lhx = -8; p.br = 0.18; break;
      }
      case 'ultimate': {
        const s = Math.sin(time * 10) * 5;
        p.by = -8 + s; p.hy = -56 + s;
        p.lax = -28; p.lay = -12; p.lhx = -10; p.lhy = -8;
        p.rax =  28; p.ray = -12; p.rhx =  10; p.rhy = -8; break;
      }
      case 'victory': {
        p.rax = 18; p.ray = -15; p.rhx = 0; p.rhy = -5;
        const b = Math.sin(time * 3) * 3;
        p.by = b; p.hy = -48 + b; break;
      }
    }
    return p;
  }

  /* ── Legacy single-call draw (used by UI portraits, char-select) */
  function drawCharacter(ctx, charData, x, y, flipX, anim, frame, t) {
    ctx.save();
    if (flipX) {
      ctx.translate(x, y); ctx.scale(-1, 1); ctx.translate(-x, -y);
    }
    drawProceduralCharacter(ctx, charData, x, y, anim, frame, t);
    ctx.restore();
  }

  /* ── Preload utility for character select thumbnails ──────────── */
  function preloadCharacter(charData) {
    // Fire-and-forget: try to load idle frames
    const frames = (charData.animations && charData.animations.idle)
                   ? charData.animations.idle.frames
                   : ANIM_DEFAULTS.idle.frames;
    for (let i = 0; i < frames; i++) {
      const src = `assets/sprites/${charData.id}/idle/idle-${i + 1}.png`;
      const img = new Image();
      img.src = src; // browser caches it; we don't need the result here
    }
  }

  return {
    drawArena, drawBar, getGroundY,
    drawCharacter,           // legacy portraits
    drawProceduralCharacter, // direct procedural draw
    preloadCharacter,
    ANIM_DEFAULTS,
    ANIM_RULES,
  };
})();
