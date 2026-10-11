/* ═══════════════════════════════════════════════════════════════
   js/ai.js  —  AISystem
   Finite-state machine AI for the enemy fighter.
   States: IDLE, APPROACH, ATTACK, RETREAT, BLOCK, JUMP, DASH, SPECIAL, ULTIMATE, HURT, DEFEATED
════════════════════════════════════════════════════════════════ */

const AISystem = (() => {
  // ── AI State Machine ─────────────────────────────────────────
  const STATE = {
    IDLE:     'idle',
    APPROACH: 'approach',
    ATTACK:   'attack',
    RETREAT:  'retreat',
    BLOCK:    'block',
    JUMP:     'jump',
    DASH:     'dash',
    SPECIAL:  'special',
    ULTIMATE: 'ultimate',
    HURT:     'hurt',
    DEFEATED: 'defeated',
  };

  function createAI(difficulty = 0.5) {
    return {
      state:          STATE.IDLE,
      stateTimer:     0,       // ms remaining in current state
      thinkTimer:     0,       // ms until next decision
      attackCooldown: 0,
      specialCooldown:0,
      difficulty,              // 0 = easy, 1 = hard
      lastAction:     null,
      comboChain:     0,
      blockChance:    0.15 + difficulty * 0.3,
      attackChance:   0.4  + difficulty * 0.4,
      specialChance:  0.15 + difficulty * 0.25,
      ultimateChance: 0.3  + difficulty * 0.4,
      retreatChance:  0.1  + difficulty * 0.15,
    };
  }

  /**
   * Update AI state, returns an input object mirroring player inputs.
   * @param {object} ai        - AI state object from createAI()
   * @param {object} enemy     - enemy fighter object
   * @param {object} player    - player fighter object
   * @param {number} dt        - delta time in ms
   * @returns {object} inputs  - { left, right, jump, dash, punch, kick, special, ultimate, block }
   */
  function update(ai, enemy, player, dt) {
    const inputs = {
      left:false, right:false, jump:false, dash:false,
      punch:false, kick:false, special:false, ultimate:false, block:false,
    };

    // Don't act if dead or in hurt stun
    if (enemy.hp <= 0)           { ai.state = STATE.DEFEATED; return inputs; }
    if (enemy.inHurtStun)        { ai.state = STATE.HURT;     return inputs; }

    // Cool down timers
    ai.thinkTimer     = Math.max(0, ai.thinkTimer     - dt);
    ai.attackCooldown = Math.max(0, ai.attackCooldown - dt);
    ai.specialCooldown= Math.max(0, ai.specialCooldown- dt);
    ai.stateTimer     = Math.max(0, ai.stateTimer     - dt);

    const dist   = Math.abs(enemy.x - player.x);
    const hpPct  = enemy.hp / enemy.maxHP;
    const facing = enemy.x > player.x ? -1 : 1; // -1=left, 1=right

    // ── Decision phase ──────────────────────────────────────────
    if (ai.thinkTimer <= 0) {
      ai.thinkTimer = getThinkInterval(ai.difficulty);
      decide(ai, enemy, player, dist, hpPct, facing);
    }

    // ── Execute current state ────────────────────────────────────
    switch (ai.state) {
      case STATE.APPROACH:
        if (facing === 1) inputs.right = true; else inputs.left = true;
        break;

      case STATE.RETREAT:
        if (facing === 1) inputs.left = true; else inputs.right = true;
        if (ai.stateTimer <= 0) ai.state = STATE.IDLE;
        break;

      case STATE.ATTACK:
        if (dist > 80) {
          // Close gap first
          if (facing === 1) inputs.right = true; else inputs.left = true;
        } else {
          // Within striking range
          if (ai.attackCooldown <= 0) {
            const roll = Math.random();
            if (roll < 0.55) {
              inputs.punch = true;
              ai.attackCooldown = 350 + (1 - ai.difficulty) * 250;
            } else {
              inputs.kick = true;
              ai.attackCooldown = 500 + (1 - ai.difficulty) * 300;
            }
          }
        }
        if (ai.stateTimer <= 0) ai.state = STATE.IDLE;
        break;

      case STATE.BLOCK:
        inputs.block = true;
        if (ai.stateTimer <= 0) ai.state = STATE.IDLE;
        break;

      case STATE.JUMP:
        inputs.jump = true;
        ai.state = STATE.IDLE;
        break;

      case STATE.DASH:
        inputs.dash  = true;
        if (facing === 1) inputs.right = true; else inputs.left = true;
        ai.state = STATE.IDLE;
        break;

      case STATE.SPECIAL:
        if (ai.specialCooldown <= 0) {
          if (dist > 80 && dist < 400) {
            inputs.special = true;
            ai.specialCooldown = enemy.charData.special.cooldown + 500;
          }
          ai.state = STATE.IDLE;
        }
        break;

      case STATE.ULTIMATE:
        if (enemy.energy >= 100) {
          inputs.ultimate = true;
        }
        ai.state = STATE.IDLE;
        break;

      case STATE.IDLE:
      default:
        // Drift slowly toward player when idle
        if (dist > 200) {
          if (facing === 1) inputs.right = true; else inputs.left = true;
        }
        break;
    }

    return inputs;
  }

  function decide(ai, enemy, player, dist, hpPct, facing) {
    // Ultimate if energy full
    if (enemy.energy >= 100 && Math.random() < ai.ultimateChance) {
      ai.state = STATE.ULTIMATE; return;
    }
    // Use special if off cooldown and in range
    if (ai.specialCooldown <= 0 && dist < 380 && Math.random() < ai.specialChance) {
      ai.state = STATE.SPECIAL; return;
    }
    // Retreat if low HP
    if (hpPct < 0.2 && Math.random() < ai.retreatChance) {
      ai.state = STATE.RETREAT;
      ai.stateTimer = 600 + Math.random() * 400;
      return;
    }
    // Block if player is very close
    if (dist < 90 && Math.random() < ai.blockChance) {
      ai.state = STATE.BLOCK;
      ai.stateTimer = 300 + Math.random() * 400;
      return;
    }
    // Jump occasionally
    if (Math.random() < 0.06) {
      ai.state = STATE.JUMP; return;
    }
    // Dash in if far away
    if (dist > 300 && Math.random() < 0.15 + ai.difficulty * 0.2) {
      ai.state = STATE.DASH; return;
    }
    // Attack
    if (dist < 180 && Math.random() < ai.attackChance) {
      ai.state = STATE.ATTACK;
      ai.stateTimer = 600 + (1 - ai.difficulty) * 500;
      return;
    }
    // Approach
    if (dist > 120) {
      ai.state = STATE.APPROACH; return;
    }
    ai.state = STATE.IDLE;
  }

  function getThinkInterval(difficulty) {
    // Easy AI thinks slowly, hard AI reacts fast
    const base = 400;
    const min  = 80;
    return Math.max(min, base - difficulty * (base - min)) + Math.random() * 100;
  }

  return { createAI, update, STATE };
})();
