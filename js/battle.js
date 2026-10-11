/* ═══════════════════════════════════════════════════════════════
   js/battle.js  —  BattleManager
   ───────────────────────────────────────────────────────────────
   Render loop now calls fighter.draw(ctx, t) which routes through
   SpriteAnimator → real PNG frames (if loaded) OR procedural art.
   Animation states are driven entirely by CombatSystem via
   fighter.setAnim().
════════════════════════════════════════════════════════════════ */

const BattleManager = (() => {

  let canvas, ctx;
  let player, enemy;
  let ai;
  let comboTracker;
  let levelData;
  let battleTimer;
  let timerInterval;
  let rafId;
  let lastTime;
  let paused      = false;
  let battleOver  = false;
  let scoreData;
  let keys        = {};
  let mobileInputs= {};

  // ── Init ──────────────────────────────────────────────────────
  function init(playerCharData, enemyCharData, lvlData) {
    canvas = document.getElementById('battle-canvas');
    ctx    = canvas.getContext('2d');

    levelData = lvlData || {
      bgColors: ['#050a14','#0a1428','#1a2840'],
      theme: 'fire', enemyLevel: 1, bossMultiplier: 1,
    };

    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    // Create fighters (Fighter constructor creates SpriteAnimator internally)
    player = new Fighter(playerCharData, true,  canvas.width, canvas.height);
    enemy  = new Fighter(enemyCharData,  false, canvas.width, canvas.height);

    // Boss multiplier
    if (levelData.bossMultiplier > 1) {
      const m = levelData.bossMultiplier;
      enemy.maxHP  *= m;
      enemy.hp      = enemy.maxHP;
      enemy.charData = Object.assign({}, enemy.charData, {
        attackDmg:   Math.round(enemy.charData.attackDmg   * m),
        kickDmg:     Math.round(enemy.charData.kickDmg     * m),
        specialDmg:  Math.round(enemy.charData.specialDmg  * m),
        ultimateDmg: Math.round(enemy.charData.ultimateDmg * m),
      });
    }

    // AI + combo
    const diff = levelData.aiDifficulty !== undefined ? levelData.aiDifficulty : 0.5;
    ai           = AISystem.createAI(diff);
    comboTracker = ComboSystem.createTracker();
    CombatSystem.resetProjectiles();

    battleTimer = 60;
    scoreData   = {
      punches: 0, kicks: 0, specials: 0, ultimates: 0,
      maxCombo: 0, victory: false, bossKill: levelData.isBoss || false,
    };

    keys = {}; mobileInputs = {};
    paused = false; battleOver = false;

    updateHUD();
    setupMobileControls();
    AudioManager.startBGM(levelData.theme || 'fire');

    clearInterval(timerInterval);
    timerInterval = setInterval(() => {
      if (paused || battleOver) return;
      battleTimer--;
      const el = document.getElementById('battle-timer');
      if (el) el.textContent = Math.max(0, battleTimer);
      if (battleTimer <= 0) timeUp();
    }, 1000);

    lastTime = performance.now();
    if (rafId) cancelAnimationFrame(rafId);
    rafId = requestAnimationFrame(loop);
  }

  function resizeCanvas() {
    if (!canvas) return;
    const p = canvas.parentElement;
    canvas.width  = p.clientWidth  || window.innerWidth;
    canvas.height = p.clientHeight || window.innerHeight;
    if (player) {
      player.canvasW  = canvas.width;
      player.canvasH  = canvas.height;
      player.groundY  = SpriteManager.getGroundY(canvas.height);
    }
    if (enemy) {
      enemy.canvasW   = canvas.width;
      enemy.canvasH   = canvas.height;
      enemy.groundY   = SpriteManager.getGroundY(canvas.height);
    }
  }

  // ── Game loop ─────────────────────────────────────────────────
  function loop(timestamp) {
    const dt = Math.min(timestamp - lastTime, 50);
    lastTime  = timestamp;
    if (!paused && !battleOver) update(dt);
    render();
    rafId = requestAnimationFrame(loop);
  }

  // ── Update ────────────────────────────────────────────────────
  function update(dt) {
    const inputs   = buildPlayerInputs();
    const aiInputs = AISystem.update(ai, enemy, player, dt);

    CombatSystem.applyInputs(player, inputs,   dt, enemy);
    CombatSystem.applyInputs(enemy,  aiInputs, dt, player);

    // Player lands hit on enemy
    if (CombatSystem.checkHits(player, enemy)) {
      const type   = player.state;
      const result = ComboSystem.recordHit(comboTracker, type, player.charData);
      showCombo(result);
      trackScore(type);
      spawnDamageNumber(enemy, getDmg(player, type), false);
    }

    // Enemy lands hit on player
    if (CombatSystem.checkHits(enemy, player)) {
      spawnDamageNumber(player, getDmg(enemy, enemy.state), true);
    }

    CombatSystem.updateProjectiles(dt, player, enemy);
    ComboSystem.tick(comboTracker, dt);
    if (comboTracker.count === 0) {
      const cd = document.getElementById('combo-display');
      if (cd) cd.textContent = '';
    }

    updateHUD();
    checkBattleEnd();
  }

  function getDmg(fighter, type) {
    if (type === 'punch')    return fighter.charData.attackDmg;
    if (type === 'kick')     return fighter.charData.kickDmg;
    if (type === 'special')  return fighter.charData.specialDmg;
    if (type === 'ultimate') return fighter.charData.ultimateDmg;
    return 0;
  }

  function trackScore(type) {
    if (type === 'punch')    scoreData.punches++;
    if (type === 'kick')     scoreData.kicks++;
    if (type === 'special')  scoreData.specials++;
    if (type === 'ultimate') scoreData.ultimates++;
  }

  // ── Render ────────────────────────────────────────────────────
  function render() {
    const w = canvas.width;
    const h = canvas.height;
    const t = performance.now();

    ctx.clearRect(0, 0, w, h);
    SpriteManager.drawArena(ctx, w, h, levelData.bgColors, levelData.theme, t, levelData.mapPath || null);
    renderProjectiles();

    // Draw fighters via their SpriteAnimator
    player.draw(ctx, t);
    enemy.draw(ctx, t);

    // Block shield overlay
    if (player.isBlocking) renderShield(player, t);
    if (enemy.isBlocking)  renderShield(enemy,  t);
  }

  function renderProjectiles() {
    const t = performance.now();
    for (const proj of CombatSystem.getProjectiles()) {
      if (proj.hit || proj.life <= 0) continue;
      ctx.save();
      ctx.globalAlpha = 0.85;
      const g = ctx.createRadialGradient(proj.x, proj.y, 2, proj.x, proj.y, proj.width / 2);
      g.addColorStop(0,   '#fff');
      g.addColorStop(0.3, proj.color);
      g.addColorStop(1,   'transparent');
      ctx.fillStyle   = g;
      ctx.shadowBlur  = 20;
      ctx.shadowColor = proj.glow;
      ctx.beginPath();
      ctx.arc(proj.x, proj.y, proj.width / 2, 0, Math.PI * 2);
      ctx.fill();

      // Elemental trail particles
      ctx.globalAlpha = 0.4;
      ctx.fillStyle   = proj.color;
      ctx.shadowBlur  = 8;
      for (let i = 1; i <= 3; i++) {
        const tx = proj.x - proj.dir * i * 10;
        ctx.beginPath();
        ctx.arc(tx, proj.y + (Math.sin(t * 0.01 + i) * 4), (proj.width / 2) * (1 - i * 0.25), 0, Math.PI * 2);
        ctx.fill();
      }
      ctx.restore();
    }
  }

  function renderShield(fighter, t) {
    const pulse = 0.5 + Math.sin(t * 0.008) * 0.2;
    ctx.save();
    ctx.globalAlpha = 0.35 * pulse;
    ctx.strokeStyle = fighter.charData.colors.accent;
    ctx.lineWidth   = 3;
    ctx.shadowBlur  = 12;
    ctx.shadowColor = fighter.charData.colors.glow;
    ctx.beginPath();
    ctx.ellipse(
      fighter.x, fighter.y - fighter.height / 2,
      fighter.width * 0.75, fighter.height * 0.55,
      0, 0, Math.PI * 2
    );
    ctx.stroke();
    ctx.restore();
  }

  // ── HUD ───────────────────────────────────────────────────────
  function updateHUD() {
    if (!player || !enemy) return;
    setBarWidth('player-hp-bar',     player.hp     / player.maxHP);
    setBarWidth('enemy-hp-bar',      enemy.hp      / enemy.maxHP);
    setBarWidth('player-energy-bar', player.energy / 100);
    setBarWidth('enemy-energy-bar',  enemy.energy  / 100);
    const pEBar = document.getElementById('player-energy-bar');
    if (pEBar) pEBar.classList.toggle('energy-full', player.energy >= 100);
  }

  function setBarWidth(id, pct) {
    const el = document.getElementById(id);
    if (el) el.style.width = Math.round(Math.max(0, pct) * 100) + '%';
  }

  // ── Combo / special text ──────────────────────────────────────
  function showCombo(result) {
    scoreData.maxCombo = Math.max(scoreData.maxCombo, result.count);
    if (result.count >= 2) {
      const el = document.getElementById('combo-display');
      if (el) el.textContent = result.text;
      AudioManager.play('combo');
      if (result.comboName) {
        showSpecialText(result.comboName, player.charData.colors.accent);
      }
    }
  }

  function showSpecialText(text, color) {
    const el = document.getElementById('special-text');
    if (!el) return;
    el.textContent = text;
    el.style.color = color || '#fff';
    el.classList.remove('show');
    void el.offsetWidth;
    el.classList.add('show');
    setTimeout(() => el.classList.remove('show'), 900);
  }

  function spawnDamageNumber(fighter, dmg, isPlayer) {
    if (!dmg) return;
    const container = document.getElementById('damage-numbers');
    if (!container) return;
    const el = document.createElement('div');
    el.className   = 'dmg-num ' + (isPlayer ? 'dmg-player' : 'dmg-enemy');
    el.textContent = '-' + dmg;
    el.style.left  = ((fighter.x / canvas.width)  * 100) + '%';
    el.style.top   = (((fighter.y - fighter.height) / canvas.height) * 100) + '%';
    container.appendChild(el);
    setTimeout(() => el.remove(), 1000);
  }

  // ── Input handling ────────────────────────────────────────────
  function buildPlayerInputs() {
    return {
      left:     !!(keys['KeyA']       || keys['ArrowLeft']    || mobileInputs.left),
      right:    !!(keys['KeyD']       || keys['ArrowRight']   || mobileInputs.right),
      jump:     !!(keys['Space']                               || mobileInputs.jump),
      dash:     !!(keys['ShiftLeft']  || keys['ShiftRight']   || mobileInputs.dash),
      punch:    !!(keys['KeyJ']                                || mobileInputs.punch),
      kick:     !!(keys['KeyI']                                || mobileInputs.kick),
      special:  !!(keys['KeyK']                                || mobileInputs.special),
      ultimate: !!(keys['KeyE']                                || mobileInputs.ultimate),
      block:    !!(keys['KeyB']                                || mobileInputs.block),
    };
  }

  function onKeyDown(e) {
    keys[e.code] = true;
    if (['Space','KeyJ','KeyI','KeyK','KeyE','KeyB','ShiftLeft','ShiftRight'].includes(e.code))
      e.preventDefault();
    if (e.code === 'Escape') togglePause();
  }
  function onKeyUp(e) { keys[e.code] = false; }

  // ── Mobile controls ───────────────────────────────────────────
  function setupMobileControls() {
    const map = {
      'mob-left':   'left',  'mob-right': 'right', 'mob-jump':    'jump',
      'mob-dash':   'dash',  'mob-punch': 'punch',  'mob-kick':    'kick',
      'mob-special':'special','mob-ult':  'ultimate','mob-block':  'block',
    };
    Object.entries(map).forEach(([id, action]) => {
      const btn = document.getElementById(id);
      if (!btn) return;
      const on  = () => { mobileInputs[action] = true;  };
      const off = () => { mobileInputs[action] = false; };
      btn.addEventListener('touchstart', e => { e.preventDefault(); on();  }, { passive: false });
      btn.addEventListener('touchend',   e => { e.preventDefault(); off(); }, { passive: false });
      btn.addEventListener('mousedown',  on);
      btn.addEventListener('mouseup',    off);
      btn.addEventListener('mouseleave', off);
    });
  }

  // ── Battle end ────────────────────────────────────────────────
  function checkBattleEnd() {
    if (battleOver) return;
    if (player.hp <= 0) endBattle(false);
    else if (enemy.hp  <= 0) endBattle(true);
  }

  function timeUp() {
    if (battleOver) return;
    endBattle(player.hp >= enemy.hp);
  }

  function endBattle(playerWon) {
    battleOver = true;
    clearInterval(timerInterval);
    AudioManager.stopBGM();

    scoreData.victory = playerWon;
    const finalScore  = ProgressionSystem.calcScore(scoreData);

    if (playerWon) {
      AudioManager.play('victory');
      // Play victory animation on player, defeat on enemy
      player.setAnim('victory');
      enemy.setAnim('defeat');
      setTimeout(() => {
        if (typeof UIManager !== 'undefined') UIManager.showVictory(finalScore, levelData);
      }, 1400);
    } else {
      AudioManager.play('defeat');
      player.setAnim('defeat');
      enemy.setAnim('victory');
      setTimeout(() => {
        if (typeof UIManager !== 'undefined') UIManager.showDefeat();
      }, 1400);
    }
  }

  // ── Pause ─────────────────────────────────────────────────────
  function togglePause() {
    paused = !paused;
    const ov = document.getElementById('overlay-pause');
    if (ov) ov.style.display = paused ? 'flex' : 'none';
  }

  function resume() {
    paused = false;
    const ov = document.getElementById('overlay-pause');
    if (ov) ov.style.display = 'none';
  }

  // ── Cleanup ───────────────────────────────────────────────────
  function destroy() {
    if (rafId) cancelAnimationFrame(rafId);
    clearInterval(timerInterval);
    AudioManager.stopBGM();
    window.removeEventListener('keydown', onKeyDown);
    window.removeEventListener('keyup',   onKeyUp);
    window.removeEventListener('resize',  resizeCanvas);
    const dc = document.getElementById('damage-numbers');
    if (dc) dc.innerHTML = '';
  }

  function attachKeys() {
    window.removeEventListener('keydown', onKeyDown);
    window.removeEventListener('keyup',   onKeyUp);
    window.addEventListener('keydown', onKeyDown);
    window.addEventListener('keyup',   onKeyUp);
  }

  function start(playerCharData, enemyCharData, lvlData) {
    attachKeys();
    init(playerCharData, enemyCharData, lvlData);
  }

  function getScoreData() { return scoreData; }
  function getPlayer()    { return player; }
  function getEnemy()     { return enemy;  }

  return { start, destroy, togglePause, resume, getScoreData, getPlayer, getEnemy };
})();
