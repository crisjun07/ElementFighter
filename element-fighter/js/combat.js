/* ═══════════════════════════════════════════════════════════════
   js/combat.js  —  Fighter class + CombatSystem + ComboSystem
   ───────────────────────────────────────────────────────────────
   Fighter now owns a SpriteAnimator.  Every state change calls
   fighter.setAnim() which drives the animator and enforces
   one-shot vs looping rules from SpriteManager.ANIM_RULES.
════════════════════════════════════════════════════════════════ */

/* ══════════════════════════════════════════════════════════════
   Fighter
══════════════════════════════════════════════════════════════ */
class Fighter {
  constructor(charData, isPlayer, canvasW, canvasH) {
    this.charData  = charData;
    this.isPlayer  = isPlayer;
    this.canvasW   = canvasW;
    this.canvasH   = canvasH;

    // Position — centre-bottom
    this.x       = isPlayer ? canvasW * 0.25 : canvasW * 0.75;
    this.groundY = SpriteManager.getGroundY(canvasH);
    this.y       = this.groundY;

    // Stats
    this.maxHP     = charData.maxHP;
    this.hp        = charData.maxHP;
    this.maxEnergy = 100;
    this.energy    = 0;

    // Physics
    this.vx       = 0;
    this.vy       = 0;
    this.onGround = true;
    this.facing   = isPlayer ? 1 : -1;   // 1 = right, -1 = left

    // State machine
    this.state      = 'idle';
    this.stateTimer = 0;       // ms remaining in transient state

    // Combat flags
    this.inHurtStun      = false;
    this.isBlocking      = false;
    this.attackActive    = false;
    this.hitThisAttack   = false;
    this.dashCooldown    = 0;
    this.specialCooldown = 0;

    // Collision size — matches the 192px render height
    this.width  = 80;
    this.height = 160;

    // Score counters
    this.punchCount    = 0;
    this.kickCount     = 0;
    this.specialCount  = 0;
    this.ultimateCount = 0;

    // ── Sprite animator ──────────────────────────────────────
    this.animator = new SpriteAnimator(charData);
    // Pre-warm movement animations in background
    ['walk','run','jump','dash','block','punch','kick',
     'special','ultimate','hurt','victory','defeat'].forEach(a => {
      this.animator._preloadAnim(a);
    });
  }

  /* ── Facing ──────────────────────────────────────────────── */
  get flipX() { return this.facing < 0; }

  /* ── Hitbox (body) ───────────────────────────────────────── */
  get hitbox() {
    return {
      x: this.x - this.width / 2,
      y: this.y - this.height,
      w: this.width,
      h: this.height,
    };
  }

  /* ── Attack reach box ────────────────────────────────────── */
  get attackBox() {
    if (!this.attackActive) return null;
    const reach = this.state === 'kick'     ? 140 :
                  this.state === 'special'  ? 180 :
                  this.state === 'ultimate' ? 260 : 120;
    return {
      x: this.x + (this.facing > 0 ? 0 : -reach),
      y: this.y - this.height * 0.7,
      w: reach,
      h: this.height * 0.55,
    };
  }

  /* ── Animation driver ────────────────────────────────────── */
  /**
   * Change the animation state, respecting loop/one-shot rules.
   * @param {string}   name        Animation name
   * @param {Function} [onDone]    Called when a one-shot finishes
   */
  setAnim(name, onDone) {
    const rule = (SpriteManager.ANIM_RULES && SpriteManager.ANIM_RULES[name])
               || { loop: true };
    this.animator.play(name, rule.loop, onDone || null);
  }

  /* ── Tick animator ───────────────────────────────────────── */
  updateAnimator(dt) {
    this.animator.update(dt);
  }

  /* ── Draw self ───────────────────────────────────────────── */
  draw(ctx, t) {
    this.animator.draw(ctx, this.x, this.y, this.flipX, t);
  }

  /* ── Reset for rematch ───────────────────────────────────── */
  resetForRound(canvasW, canvasH) {
    this.canvasW = canvasW;
    this.canvasH = canvasH;
    this.x       = this.isPlayer ? canvasW * 0.25 : canvasW * 0.75;
    this.groundY = SpriteManager.getGroundY(canvasH);
    this.y       = this.groundY;
    this.vx = 0; this.vy = 0;
    this.hp = this.maxHP; this.energy = 0;
    this.onGround = true;
    this.facing   = this.isPlayer ? 1 : -1;
    this.state = 'idle'; this.stateTimer = 0;
    this.inHurtStun = false; this.isBlocking = false;
    this.attackActive = false; this.hitThisAttack = false;
    this.specialCooldown = 0; this.dashCooldown = 0;
    this.setAnim('idle');
  }
}

/* ══════════════════════════════════════════════════════════════
   CombatSystem
══════════════════════════════════════════════════════════════ */
const CombatSystem = (() => {

  const GRAVITY        = 0.9;
  const JUMP_FORCE     = 22;
  const DASH_SPEED     = 18;
  const DASH_DURATION  = 180;   // ms
  const HURT_DURATION  = 480;   // ms — longer stun, hits feel heavier

  // How long each attack animation state lasts (ms)
  const ATTACK_DURATION = {
    punch:   280,
    kick:    380,
    special: 500,
    ultimate:700,
  };

  // ── Projectiles ──────────────────────────────────────────────
  let projectiles = [];

  function createProjectile(owner, x, y, dir, charData, type) {
    return {
      owner, x, y, dir,
      speed:  type === 'ultimate' ? 14 : 10,
      width:  type === 'ultimate' ? 50 : 32,
      height: type === 'ultimate' ? 50 : 24,
      damage: type === 'ultimate' ? charData.ultimateDmg : charData.specialDmg,
      color:  charData.colors.accent,
      glow:   charData.colors.glow,
      type,
      hit:  false,
      life: 1200,
    };
  }

  function resetProjectiles() { projectiles = []; }
  function getProjectiles()   { return projectiles; }

  // ── Main input → physics → state machine ─────────────────────
  function applyInputs(fighter, inputs, dt, other) {

    // ── Dead ─────────────────────────────────────────────────
    if (fighter.hp <= 0) {
      if (fighter.state !== 'defeat') {
        fighter.state = 'defeat';
        fighter.setAnim('defeat');
      }
      fighter.updateAnimator(dt);
      return;
    }

    const TRANSIENT = ['punch','kick','special','ultimate','hurt','dash'];
    const inTransient = TRANSIENT.includes(fighter.state);

    // ── Transient state tick ──────────────────────────────────
    if (inTransient) {
      fighter.stateTimer -= dt;

      // Hitbox window: active 35%–65% of total attack duration
      const totalDur = ATTACK_DURATION[fighter.state];
      if (totalDur) {
        const elapsed     = totalDur - fighter.stateTimer;
        const activeStart = totalDur * 0.35;
        const activeEnd   = totalDur * 0.65;
        fighter.attackActive = !fighter.hitThisAttack
          && elapsed >= activeStart && elapsed <= activeEnd;
      }

      // Dash movement
      if (fighter.state === 'dash') fighter.x += fighter.vx;

      // State expired → return to idle
      if (fighter.stateTimer <= 0) {
        if (fighter.state === 'dash') fighter.vx = 0;
        fighter.state        = 'idle';
        fighter.stateTimer   = 0;
        fighter.attackActive = false;
        fighter.hitThisAttack= false;
        fighter.inHurtStun   = false;
        // Return to correct idle/walk/jump anim
        _refreshIdleAnim(fighter);
      }

      _applyGravity(fighter);
      _clamp(fighter);
      fighter.updateAnimator(dt);
      return;
    }

    // ── Cooldowns ─────────────────────────────────────────────
    fighter.dashCooldown    = Math.max(0, fighter.dashCooldown    - dt);
    fighter.specialCooldown = Math.max(0, fighter.specialCooldown - dt);

    // ── Auto-face ─────────────────────────────────────────────
    if (!inputs.left && !inputs.right) {
      fighter.facing = other.x > fighter.x ? 1 : -1;
    }

    // ── Movement ──────────────────────────────────────────────
    let moving = false;
    if (inputs.left) {
      fighter.x -= fighter.charData.moveSpeed * (dt / 16);
      fighter.facing = -1; moving = true;
    }
    if (inputs.right) {
      fighter.x += fighter.charData.moveSpeed * (dt / 16);
      fighter.facing = 1;  moving = true;
    }

    // ── Block ─────────────────────────────────────────────────
    fighter.isBlocking = !!(inputs.block && fighter.onGround && !moving);

    // ── Jump ──────────────────────────────────────────────────
    if (inputs.jump && fighter.onGround) {
      fighter.vy       = -(fighter.charData.jumpForce || JUMP_FORCE);
      fighter.onGround = false;
      fighter.setAnim('jump');
      AudioManager.play('jump');
    }

    // ── Dash ──────────────────────────────────────────────────
    if (inputs.dash && fighter.dashCooldown <= 0 && fighter.onGround) {
      _startTransient(fighter, 'dash', DASH_DURATION);
      fighter.vx            = fighter.facing * DASH_SPEED;
      fighter.dashCooldown  = 800;
      AudioManager.play('dash');
    }

    // ── Attacks ───────────────────────────────────────────────
    else if (!fighter.isBlocking) {
      if (inputs.punch && fighter.state === 'idle') {
        _startAttack(fighter, 'punch');
        AudioManager.play('punch');
        fighter.punchCount++;

      } else if (inputs.kick && (fighter.state === 'idle' || !fighter.onGround)) {
        _startAttack(fighter, 'kick');
        AudioManager.play('kick');
        fighter.kickCount++;

      } else if (inputs.special && fighter.specialCooldown <= 0) {
        _startAttack(fighter, 'special');
        fighter.specialCooldown = fighter.charData.special.cooldown;
        fighter.specialCount++;
        AudioManager.play('special');
        if (fighter.charData.special.projectile) {
          projectiles.push(createProjectile(
            fighter, fighter.x, fighter.y - 50, fighter.facing, fighter.charData, 'special'
          ));
        }

      } else if (inputs.ultimate && fighter.energy >= 100) {
        _startAttack(fighter, 'ultimate');
        fighter.energy = 0;
        fighter.ultimateCount++;
        AudioManager.play('ultimate');
        projectiles.push(createProjectile(
          fighter, fighter.x, fighter.y - 55, fighter.facing, fighter.charData, 'ultimate'
        ));
      }
    }

    // ── Idle animation selector ───────────────────────────────
    if (fighter.state === 'idle') {
      if (!fighter.onGround)    fighter.setAnim('jump');
      else if (fighter.isBlocking) fighter.setAnim('block');
      else if (moving)          fighter.setAnim('walk');
      else                      fighter.setAnim('idle');
    }

    _applyGravity(fighter);
    _clamp(fighter);
    fighter.updateAnimator(dt);
  }

  /* ── Helpers ─────────────────────────────────────────────── */

  function _startTransient(fighter, state, duration) {
    fighter.state      = state;
    fighter.stateTimer = duration;
    fighter.setAnim(state);
  }

  function _startAttack(fighter, type) {
    fighter.state        = type;
    fighter.stateTimer   = ATTACK_DURATION[type];
    fighter.attackActive = false;
    fighter.hitThisAttack= false;
    fighter.setAnim(type);
  }

  function _refreshIdleAnim(fighter) {
    if (!fighter.onGround)     fighter.setAnim('jump');
    else if (fighter.isBlocking) fighter.setAnim('block');
    else                        fighter.setAnim('idle');
  }

  function _applyGravity(fighter) {
    if (!fighter.onGround) {
      fighter.vy += GRAVITY;
      fighter.y  += fighter.vy;
      if (fighter.y >= fighter.groundY) {
        fighter.y        = fighter.groundY;
        fighter.vy       = 0;
        fighter.onGround = true;
      }
    }
  }

  function _clamp(fighter) {
    const m = fighter.width / 2;
    fighter.x = Math.max(m, Math.min(fighter.canvasW - m, fighter.x));
  }

  // ── Projectile physics + collision ───────────────────────────
  function updateProjectiles(dt, player, enemy) {
    projectiles = projectiles.filter(p => !p.hit && p.life > 0);
    for (const proj of projectiles) {
      proj.x   += proj.dir * proj.speed * (dt / 16);
      proj.life -= dt;

      for (const fighter of [player, enemy]) {
        if (fighter === proj.owner) continue;
        if (fighter.hp <= 0) continue;
        if (_rectsOverlap(
          { x: proj.x - proj.width / 2, y: proj.y - proj.height / 2, w: proj.width,  h: proj.height },
          fighter.hitbox
        )) {
          if (!proj.hit) {
            proj.hit = true;
            applyHit(proj.owner, fighter, proj.damage, proj.type);
          }
        }
      }

      if (proj.x < -100 || proj.x > player.canvasW + 100) proj.life = 0;
    }
  }

  // ── Melee hit detection ───────────────────────────────────────
  function checkHits(attacker, defender) {
    if (attacker.hp <= 0 || defender.hp <= 0) return false;
    if (attacker.hitThisAttack)               return false;
    const aBox = attacker.attackBox;
    if (!aBox) return false;

    if (_rectsOverlap(aBox, defender.hitbox)) {
      const t   = attacker.state;
      const dmg = t === 'punch'    ? attacker.charData.attackDmg   :
                  t === 'kick'     ? attacker.charData.kickDmg     :
                  t === 'special'  ? attacker.charData.specialDmg  :
                  t === 'ultimate' ? attacker.charData.ultimateDmg : 0;
      applyHit(attacker, defender, dmg, t);
      attacker.hitThisAttack = true;
      return true;
    }
    return false;
  }

  // ── Damage application ────────────────────────────────────────
  function applyHit(attacker, defender, rawDmg, type) {
    let dmg     = rawDmg;
    let blocked = false;

    if (defender.isBlocking) {
      dmg     = Math.floor(dmg * (1 - defender.charData.defenseRate));
      blocked = true;
      AudioManager.play('block');
    } else {
      AudioManager.play('hit');
      // Hurt stun — play hurt animation
      defender.state      = 'hurt';
      defender.stateTimer = HURT_DURATION;
      defender.inHurtStun = true;
      defender.setAnim('hurt');
      // Knockback
      const kbDir   = defender.x > attacker.x ? 1 : -1;
      const kbForce = type === 'ultimate' ? 36 :
                      type === 'special'  ? 20 :
                      type === 'kick'     ? 14 : 8;
      defender.x += kbDir * kbForce;
    }

    defender.hp = Math.max(0, defender.hp - dmg);

    // Energy gain
    const atkGain = Math.floor(attacker.charData.energyGain * (type === 'ultimate' ? 0 : 1));
    const defGain = Math.floor(defender.charData.energyGain * 0.5);
    attacker.energy = Math.min(100, attacker.energy + atkGain);
    if (!blocked) defender.energy = Math.min(100, defender.energy + defGain);

    return { dmg, blocked };
  }

  function _rectsOverlap(a, b) {
    return a.x < b.x + b.w && a.x + a.w > b.x &&
           a.y < b.y + b.h && a.y + a.h > b.y;
  }

  return {
    applyInputs, checkHits, updateProjectiles,
    applyHit, resetProjectiles, getProjectiles, createProjectile,
  };
})();

/* ══════════════════════════════════════════════════════════════
   ComboSystem
══════════════════════════════════════════════════════════════ */
const ComboSystem = (() => {
  const COMBO_WINDOW = 1200; // ms

  function createTracker() {
    return { sequence: [], timer: 0, count: 0, maxCombo: 0, lastText: '' };
  }

  function recordHit(tracker, attackType, charData) {
    if (tracker.timer <= 0) tracker.sequence = [];
    tracker.sequence.push(attackType);
    tracker.count++;
    tracker.maxCombo = Math.max(tracker.maxCombo, tracker.count);
    tracker.timer    = COMBO_WINDOW;

    const seq       = tracker.sequence.join(',');
    let comboName   = null;
    let bonusDmg    = 0;
    for (const combo of (charData.combos || [])) {
      if (seq.endsWith(combo.sequence.join(','))) {
        comboName = combo.name;
        bonusDmg  = combo.bonusDmg;
        break;
      }
    }

    const text = tracker.count >= 2
      ? `${tracker.count} HIT COMBO!${comboName ? '  ' + comboName : ''}`
      : '';
    tracker.lastText = text;
    return { count: tracker.count, text, bonusDmg, comboName };
  }

  function tick(tracker, dt) {
    if (tracker.timer > 0) {
      tracker.timer -= dt;
      if (tracker.timer <= 0) { tracker.sequence = []; tracker.count = 0; }
    }
  }

  function reset(tracker) {
    tracker.sequence = []; tracker.timer = 0;
    tracker.count = 0;     tracker.lastText = '';
  }

  return { createTracker, recordHit, tick, reset };
})();
