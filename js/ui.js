/* ═══════════════════════════════════════════════════════════════
   js/ui.js  —  UIManager
   All screen transitions, DOM population, event wiring.
════════════════════════════════════════════════════════════════ */

const UIManager = (() => {

  // Current game state
  let saveData     = null;
  let selectedChar = null;   // character id
  let currentMode  = null;   // 'adventure' | 'vsbot'
  let currentLevel = null;   // levelData from buildLevel()
  let pendingChapter = null; // chapter index for level select

  // ── Profile image cache ───────────────────────────────────────
  // Loads assets/profile/<charId>_profile.png automatically.
  // Falls back to procedural canvas art if image is missing.
  const _profileCache = {};

  function _loadProfile(charData) {
    const src = charData.profileImg || `assets/profile/${charData.id}_profile.png`;
    if (_profileCache[src] !== undefined) return _profileCache[src];
    _profileCache[src] = null; // loading
    const img = new Image();
    img.onload  = () => { _profileCache[src] = img; };
    img.onerror = () => { _profileCache[src] = false; };
    img.src = src;
    return null;
  }

  /**
   * Draw a character portrait onto a canvas element.
   * Uses the real profile PNG if loaded, otherwise procedural art.
   * @param {HTMLCanvasElement} canvas
   * @param {object}  charData
   * @param {string}  [anim='idle']   fallback anim state for procedural
   */
  function drawPortraitOnCanvas(canvas, charData, anim) {
    anim = anim || 'idle';
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const w   = canvas.width;
    const h   = canvas.height;

    // Background fill
    ctx.fillStyle = charData.colors.primary;
    ctx.fillRect(0, 0, w, h);

    // Try real profile image
    const src = charData.profileImg || `assets/profile/${charData.id}_profile.png`;
    const img = _profileCache[src];

    if (img) {
      // Draw image cover-fit (square crop from centre)
      const scale = Math.max(w / img.width, h / img.height);
      const dw    = img.width  * scale;
      const dh    = img.height * scale;
      const dx    = (w - dw) / 2;
      const dy    = (h - dh) / 2;
      ctx.drawImage(img, dx, dy, dw, dh);

      // Elemental glow rim
      ctx.save();
      const rim = ctx.createLinearGradient(0, 0, w, h);
      rim.addColorStop(0, 'transparent');
      rim.addColorStop(0.7, 'transparent');
      rim.addColorStop(1, charData.colors.glow + '99');
      ctx.fillStyle = rim;
      ctx.fillRect(0, 0, w, h);
      ctx.restore();

    } else {
      // Trigger load then draw procedural for now
      _loadProfile(charData);
      SpriteManager.drawCharacter(ctx, charData,
        Math.floor(w / 2), Math.floor(h * 0.95),
        false, anim, 0, performance.now());
    }
  }

  /** Set a DOM element's background to the profile image (for non-canvas elements) */
  function applyProfileBg(el, charData) {
    if (!el) return;
    el.style.background = charData.colors.primary;
    el.style.boxShadow  = `0 0 14px ${charData.colors.glow}`;
    const src = charData.profileImg || `assets/profile/${charData.id}_profile.png`;

    // Try immediately
    const cached = _profileCache[src];
    if (cached) {
      el.style.backgroundImage  = `url('${src}')`;
      el.style.backgroundSize   = 'cover';
      el.style.backgroundPosition = 'center top';
      return;
    }
    // Trigger load, then poll once loaded
    _loadProfile(charData);
    const interval = setInterval(() => {
      if (_profileCache[src]) {
        el.style.backgroundImage    = `url('${src}')`;
        el.style.backgroundSize     = 'cover';
        el.style.backgroundPosition = 'center top';
        clearInterval(interval);
      } else if (_profileCache[src] === false) {
        clearInterval(interval); // missing — keep gradient bg
      }
    }, 100);
  }
  function showScreen(id) {
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    const el = document.getElementById(id);
    if (el) el.classList.add('active');
  }

  // ── LOADING SCREEN ────────────────────────────────────────────
  function runLoadingScreen(onDone) {
    showScreen('screen-loading');
    const bar  = document.getElementById('loading-bar');
    const text = document.getElementById('loading-text');
    const steps = [
      [10,  'Loading character data…'],
      [25,  'Preparing arena…'],
      [45,  'Initialising combat engine…'],
      [60,  'Loading audio system…'],
      [75,  'Building sprite renderer…'],
      [90,  'Almost ready…'],
      [100, 'Welcome to Element Fighter!'],
    ];
    let idx = 0;
    function tick() {
      if (idx >= steps.length) { setTimeout(onDone, 400); return; }
      const [pct, msg] = steps[idx++];
      if (bar)  bar.style.width  = pct + '%';
      if (text) text.textContent = msg;
      setTimeout(tick, 250 + Math.random() * 180);
    }
    tick();
  }

  // ── LOGIN SCREEN ──────────────────────────────────────────────
  function initLoginScreen() {
    showScreen('screen-login');

    document.getElementById('btn-login').onclick = () => {
      AudioManager.play('click');
      const username = document.getElementById('login-username').value.trim();
      const password = document.getElementById('login-password').value;
      const result   = SaveSystem.login(username, password);
      if (result.ok) {
        saveData = SaveSystem.loadGame(username);
        goToMenu();
      } else {
        showLoginError(result.msg);
      }
    };

    document.getElementById('btn-register').onclick = () => {
      AudioManager.play('click');
      const username = document.getElementById('login-username').value.trim();
      const password = document.getElementById('login-password').value;
      const result   = SaveSystem.register(username, password);
      if (result.ok) {
        saveData = SaveSystem.loadGame(username);
        goToMenu();
      } else {
        showLoginError(result.msg);
      }
    };

    // Enter key
    ['login-username','login-password'].forEach(id => {
      document.getElementById(id).addEventListener('keydown', e => {
        if (e.key === 'Enter') document.getElementById('btn-login').click();
      });
    });
  }

  function showLoginError(msg) {
    const el = document.getElementById('login-error');
    if (el) { el.textContent = msg; setTimeout(() => { el.textContent = ''; }, 3000); }
  }

  // ── MAIN MENU ─────────────────────────────────────────────────
  function goToMenu() {
    SaveSystem.saveGame(saveData);
    populateHUD();
    showScreen('screen-menu');
    AudioManager.startBGM('menu');

    document.getElementById('btn-adventure').onclick  = () => { AudioManager.play('click'); openAdventure(); };
    document.getElementById('btn-vsbot').onclick      = () => { AudioManager.play('click'); openVsBot(); };
    document.getElementById('btn-characters').onclick = () => { AudioManager.play('click'); openCharacterSelect('menu'); };
    document.getElementById('btn-gacha').onclick      = () => { AudioManager.play('click'); openGacha(); };
    document.getElementById('btn-settings').onclick   = () => { AudioManager.play('click'); openSettings(); };
    document.getElementById('btn-logout').onclick     = () => {
      AudioManager.play('click');
      SaveSystem.saveGame(saveData);
      saveData = null;
      initLoginScreen();
    };
  }

  function populateHUD() {
    if (!saveData) return;
    setText('hud-username', saveData.username);
    setText('hud-level',    saveData.level);
    setText('hud-xp',       saveData.xp);
    setText('hud-coins',    saveData.coins);
    setText('hud-potions',  saveData.potions);
    setText('hud-chars',    saveData.unlockedCharacters.length);
    setText('hud-best',     saveData.bestScore);

    // XP bar
    const prog = ProgressionSystem.xpProgressInLevel(saveData.xp, saveData.level);
    const fill = document.getElementById('hud-xp-fill');
    if (fill) fill.style.width = (prog.pct * 100) + '%';

    // Chapter progress
    const chIdx = saveData.chapterProgress || 0;
    const ch    = CHAPTERS[Math.min(chIdx, CHAPTERS.length - 1)];
    setText('hud-chapter', `Chapter ${ch.id} · ${ch.name}`);

    // Avatar — draw selected char with real profile image
    const avatar = document.getElementById('hud-avatar');
    if (avatar) {
      const char = getCharacter(saveData.selectedCharacter || 'blazor');
      applyProfileBg(avatar, char);
    }
  }

  // ── CHARACTER SELECT ──────────────────────────────────────────
  function openCharacterSelect(returnTo) {
    currentMode = returnTo === 'vsbot' ? 'vsbot' : 'adventure';
    showScreen('screen-characters');
    buildCharGrid(returnTo);
  }

  function buildCharGrid(returnTo) {
    const grid = document.getElementById('char-grid');
    if (!grid) return;
    grid.innerHTML = '';
    selectedChar = saveData.selectedCharacter || 'blazor';

    CHARACTERS.forEach(char => {
      const isUnlocked = saveData.unlockedCharacters.includes(char.id);
      const card = document.createElement('div');
      card.className = `char-card ${isUnlocked ? '' : 'locked-card'} ${char.id === selectedChar ? 'selected-card' : ''}`;
      card.innerHTML = `
        <div class="char-portrait" style="background:${char.colors.primary};box-shadow:inset 0 0 20px ${char.colors.glow};">
          <canvas width="80" height="80" data-charid="${char.id}"></canvas>
        </div>
        <div class="char-card-name el-${char.elementKey}">${char.name}</div>
        <div class="char-card-element">${char.element}</div>
        ${!isUnlocked ? '<div class="char-lock-icon">🔒</div>' : ''}
      `;
      if (isUnlocked) {
        card.onclick = () => {
          AudioManager.play('click');
          selectedChar = char.id;
          document.querySelectorAll('.char-card').forEach(c => c.classList.remove('selected-card'));
          card.classList.add('selected-card');
          showCharDetail(char);
          document.getElementById('btn-select-char').disabled = false;
        };
      }
      grid.appendChild(card);

      // Draw portrait — real profile image or procedural fallback
      const miniCanvas = card.querySelector('canvas');
      if (miniCanvas) {
        drawPortraitOnCanvas(miniCanvas, char, 'idle');
        // Redraw when profile loads (in case it wasn't cached yet)
        const src = char.profileImg || `assets/profile/${char.id}_profile.png`;
        if (!_profileCache[src]) {
          const tid = setInterval(() => {
            if (_profileCache[src] !== null) {
              drawPortraitOnCanvas(miniCanvas, char, 'idle');
              clearInterval(tid);
            }
          }, 150);
          setTimeout(() => clearInterval(tid), 5000); // give up after 5s
        }
      }
    });

    // Show detail for current selected
    showCharDetail(getCharacter(selectedChar));
    document.getElementById('btn-select-char').disabled = false;

    document.getElementById('btn-select-char').onclick = () => {
      AudioManager.play('click');
      saveData.selectedCharacter = selectedChar;
      SaveSystem.saveGame(saveData);
      if (returnTo === 'vsbot') startVsBot();
      else if (returnTo === 'menu') goToMenu();
      else openAdventure();
    };

    document.getElementById('btn-back-menu-chars').onclick = () => {
      AudioManager.play('click');
      goToMenu();
    };
  }

  function showCharDetail(char) {
    const portrait = document.getElementById('char-detail-portrait');
    const info     = document.getElementById('char-detail-info');
    if (!portrait || !info) return;

    portrait.style.background = char.colors.primary;
    portrait.style.boxShadow  = `inset 0 0 20px ${char.colors.glow}`;
    portrait.innerHTML = `<canvas width="100" height="100" id="detail-canvas"></canvas>`;
    const dc = document.getElementById('detail-canvas');
    if (dc) {
      drawPortraitOnCanvas(dc, char, 'idle');
      // Redraw when loaded
      const src = char.profileImg || `assets/profile/${char.id}_profile.png`;
      if (!_profileCache[src]) {
        const tid = setInterval(() => {
          if (_profileCache[src] !== null) { drawPortraitOnCanvas(dc, char, 'idle'); clearInterval(tid); }
        }, 150);
        setTimeout(() => clearInterval(tid), 5000);
      }
    }

    const isUnlocked = saveData.unlockedCharacters.includes(char.id);
    const statBar = (label, val, max, color) =>
      `<div class="stat-bar-row">
        <span class="stat-label">${label}</span>
        <div class="stat-bar"><div class="stat-fill" style="width:${(val/max)*100}%;background:${color}"></div></div>
        <span class="stat-val">${val}</span>
      </div>`;

    info.innerHTML = `
      <div class="detail-name el-${char.elementKey}">${char.name}</div>
      <div class="detail-element">${char.element} · ${char.role}</div>
      <p style="font-size:.8rem;color:var(--text-dim);margin-bottom:8px;">${char.description}</p>
      <div class="stat-bars">
        ${statBar('POWER',   char.power,   5, char.colors.accent)}
        ${statBar('SPEED',   char.speed,   5, char.colors.secondary)}
        ${statBar('DEFENSE', char.defense, 5, char.colors.primary)}
      </div>
      <div class="detail-special">⚡ Special: <strong>${char.special.name}</strong> — ${char.special.description}</div>
      <div class="detail-ult">✨ Ultimate: <strong>${char.ultimate.name}</strong> — ${char.ultimate.description}</div>
      ${!isUnlocked ? '<p style="color:#ff8888;margin-top:8px;">🔒 Unlock via Gacha</p>' : ''}
    `;
  }

  // ── ADVENTURE MODE ────────────────────────────────────────────
  function openAdventure() {
    showScreen('screen-adventure');
    buildChapterGrid();

    document.getElementById('btn-back-menu-adv').onclick = () => {
      AudioManager.play('click'); goToMenu();
    };
  }

  function buildChapterGrid() {
    const grid = document.getElementById('chapter-grid');
    if (!grid) return;
    grid.innerHTML = '';
    const chapters = getUnlockedChapters(saveData.chapterProgress);

    chapters.forEach((ch, i) => {
      const levelsBeaten = countChapterLevelsBeaten(i);
      const card = document.createElement('div');
      card.className = `chapter-card ${ch.unlocked ? '' : 'locked-chapter'} ${i === saveData.chapterProgress && !ch.completed ? 'current-chapter' : ''}`;
      card.innerHTML = `
        <div class="chapter-num">${ch.id}</div>
        <div class="chapter-name el-${ch.theme}">${ch.name}</div>
        <div class="chapter-prog">${ch.completed ? '<span class="chapter-done">✔ Complete</span>' : `${levelsBeaten}/5 levels`}</div>
        ${!ch.unlocked ? '<div class="char-lock-icon">🔒</div>' : ''}
      `;
      if (ch.unlocked) {
        card.onclick = () => { AudioManager.play('click'); openLevelSelect(i); };
      }
      grid.appendChild(card);
    });
  }

  function countChapterLevelsBeaten(chapterIndex) {
    let count = 0;
    for (let l = 1; l <= 5; l++) {
      if (SaveSystem.isLevelCompleted(saveData, chapterIndex, l)) count++;
    }
    return count;
  }

  // ── LEVEL SELECT ──────────────────────────────────────────────
  function openLevelSelect(chapterIndex) {
    pendingChapter = chapterIndex;
    const ch = CHAPTERS[chapterIndex];
    setText('level-chapter-title', `Chapter ${ch.id}: ${ch.name}`);
    showScreen('screen-levels');
    buildLevelGrid(chapterIndex);

    document.getElementById('btn-back-adventure').onclick = () => {
      AudioManager.play('click'); openAdventure();
    };
  }

  function buildLevelGrid(chapterIndex) {
    const grid = document.getElementById('level-grid');
    if (!grid) return;
    grid.innerHTML = '';

    for (let lv = 1; lv <= 5; lv++) {
      const completed = SaveSystem.isLevelCompleted(saveData, chapterIndex, lv);
      const isUnlocked = lv === 1 || SaveSystem.isLevelCompleted(saveData, chapterIndex, lv - 1) || completed;
      const isBoss = lv === 5;

      const btn = document.createElement('div');
      btn.className = `level-btn ${!isUnlocked ? 'locked-level' : ''} ${isBoss ? 'boss-level' : ''} ${completed ? 'completed-level' : ''}`;
      btn.innerHTML = `
        <div class="lv-num">${completed ? '✔' : lv}</div>
        <div class="lv-type">${isBoss ? '👹 BOSS' : 'Battle'}</div>
      `;
      if (isUnlocked) {
        btn.onclick = () => {
          AudioManager.play('click');
          startAdventureLevel(chapterIndex, lv);
        };
      }
      grid.appendChild(btn);
    }
  }

  // ── START BATTLE ──────────────────────────────────────────────
  function startAdventureLevel(chapterIndex, levelNum) {
    currentMode  = 'adventure';
    currentLevel = buildLevel(chapterIndex, levelNum);

    const playerCharData = getScaledCharacter(saveData.selectedCharacter, saveData.level);
    const scaled = ProgressionSystem.applyPlayerLevel(playerCharData, saveData.level);

    const enemyBase  = getScaledCharacter(currentLevel.enemyId, currentLevel.enemyLevel);
    // Scale enemy HP display
    const enemyData  = Object.assign({}, enemyBase);

    showBattleScreen(scaled, enemyData, currentLevel);
  }

  function startVsBot() {
    currentMode = 'vsbot';
    // Random opponent (not the same as player)
    const playerCharData = getScaledCharacter(saveData.selectedCharacter, saveData.level);
    const scaled = ProgressionSystem.applyPlayerLevel(playerCharData, saveData.level);

    const available = CHARACTERS.filter(c => c.id !== saveData.selectedCharacter);
    const opp = available[Math.floor(Math.random() * available.length)];
    const enemyData = getScaledCharacter(opp.id, saveData.level + 1);

    currentLevel = {
      bgColors: ['#050a14','#0a1428','#1a2840'],
      theme: opp.elementKey,
      mapPath: `assets/maps/${opp.id}_map.png`,   // uses opponent's map if available
      enemyLevel: saveData.level + 1,
      bossMultiplier: 1,
      aiDifficulty: 0.4 + (saveData.level / 20) * 0.4,
      rewards: { coins: 50, xp: 50, potionChance: 0.15 },
      isBoss: false,
    };

    showBattleScreen(scaled, enemyData, currentLevel);
  }

  function showBattleScreen(playerCharData, enemyCharData, lvlData) {
    // Populate names / levels in HUD
    setText('player-name', playerCharData.name);
    setText('enemy-name',  enemyCharData.name);
    setText('player-lv',   saveData.level);
    setText('enemy-lv',    lvlData.enemyLevel || 1);
    setText('battle-timer', '60');

    // Portraits
    renderPortrait('player-portrait', playerCharData);
    renderPortrait('enemy-portrait',  enemyCharData);

    // Show/hide mobile controls — now always shown, but can be force-hidden on desktop
    const mob = document.getElementById('mobile-controls');
    if (mob) {
      const forceHide = saveData.settings?.showMobile === false && window.innerWidth > 700;
      mob.classList.toggle('force-hide', false); // always show
    }

    // Show battle screen
    AudioManager.stopBGM();
    BattleManager.destroy();
    showScreen('screen-battle');

    // Slight delay to let screen render
    setTimeout(() => BattleManager.start(playerCharData, enemyCharData, lvlData), 100);

    // Pause controls
    document.getElementById('btn-pause').onclick  = () => { AudioManager.play('click'); BattleManager.togglePause(); };
    document.getElementById('btn-resume').onclick = () => { AudioManager.play('click'); BattleManager.resume(); };
    document.getElementById('btn-quit-battle').onclick = () => {
      AudioManager.play('click');
      BattleManager.destroy();
      document.getElementById('overlay-pause').style.display = 'none';
      goToMenu();
    };
  }

  function renderPortrait(id, charData) {
    const el = document.getElementById(id);
    if (!el) return;
    el.innerHTML = `<canvas width="52" height="52"></canvas>`;
    const c = el.querySelector('canvas');
    if (!c) return;
    // Draw with real profile or procedural fallback
    drawPortraitOnCanvas(c, charData, 'idle');
    // Redraw if image loads after initial draw
    const src = charData.profileImg || `assets/profile/${charData.id}_profile.png`;
    if (!_profileCache[src]) {
      const tid = setInterval(() => {
        if (_profileCache[src] !== null) { drawPortraitOnCanvas(c, charData, 'idle'); clearInterval(tid); }
      }, 150);
      setTimeout(() => clearInterval(tid), 5000);
    }
  }

  // ── VS BOT ────────────────────────────────────────────────────
  function openVsBot() {
    currentMode = 'vsbot';
    showScreen('screen-characters');
    buildCharGrid('vsbot');
  }

  // ── VICTORY SCREEN ────────────────────────────────────────────
  function showVictory(finalScore, lvlData) {
    BattleManager.destroy();

    // Calculate rewards
    const rewards = lvlData.rewards || { coins:120, xp:50, potionChance:0.2 };
    const coinReward    = rewards.coins;
    const xpReward      = rewards.xp;
    const potionReward  = Math.random() < (rewards.potionChance || 0.2) ? 1 : 0;

    // Apply
    saveData.coins   += coinReward;
    saveData.potions += potionReward;
    const lvlResult   = ProgressionSystem.addXp(saveData, xpReward);
    saveData.bestScore = Math.max(saveData.bestScore, finalScore);

    // Mark level done (adventure only)
    if (currentMode === 'adventure' && currentLevel) {
      SaveSystem.markLevelCompleted(saveData, currentLevel.chapterIndex, currentLevel.levelNum);
    }
    SaveSystem.saveGame(saveData);

    // Populate
    setText('reward-coins',  `+${coinReward}`);
    setText('reward-xp',     `+${xpReward}`);
    setText('reward-potion', potionReward > 0 ? '+1' : '0');
    setText('reward-score',  finalScore);

    const lvlUpRow = document.getElementById('levelup-row');
    if (lvlUpRow) {
      lvlUpRow.style.display = lvlResult.leveledUp ? 'flex' : 'none';
      if (lvlResult.leveledUp) {
        setText('reward-level', `Lv.${lvlResult.newLevel}`);
        AudioManager.play('levelUp');
      }
    }

    // Victory char portrait
    const vc = document.getElementById('victory-char');
    if (vc) {
      const char = getCharacter(saveData.selectedCharacter);
      vc.innerHTML = `<canvas width="120" height="120"></canvas>`;
      const vc_c = vc.querySelector('canvas');
      if (vc_c) {
        vc_c.style.borderRadius = '50%';
        drawPortraitOnCanvas(vc_c, char, 'victory');
        const src = char.profileImg || `assets/profile/${char.id}_profile.png`;
        if (!_profileCache[src]) {
          const tid = setInterval(() => {
            if (_profileCache[src] !== null) { drawPortraitOnCanvas(vc_c, char, 'victory'); clearInterval(tid); }
          }, 150);
          setTimeout(() => clearInterval(tid), 5000);
        }
      }
    }

    showScreen('screen-victory');
    AudioManager.startBGM(currentLevel?.theme || 'menu');

    // Buttons
    document.getElementById('btn-next-level').onclick = () => {
      AudioManager.play('click');
      if (currentMode === 'adventure') advanceToNextLevel();
      else { startVsBot(); }
    };
    document.getElementById('btn-retry-win').onclick  = () => { AudioManager.play('click'); retryLevel(); };
    document.getElementById('btn-menu-win').onclick   = () => { AudioManager.play('click'); goToMenu(); };
  }

  function advanceToNextLevel() {
    if (!currentLevel) { goToMenu(); return; }
    let { chapterIndex, levelNum } = currentLevel;
    levelNum++;
    if (levelNum > 5) {
      chapterIndex++;
      levelNum = 1;
    }
    if (chapterIndex >= CHAPTERS.length) {
      // Game complete
      goToMenu(); return;
    }
    startAdventureLevel(chapterIndex, levelNum);
  }

  function retryLevel() {
    if (!currentLevel) { goToMenu(); return; }
    if (currentMode === 'adventure') startAdventureLevel(currentLevel.chapterIndex, currentLevel.levelNum);
    else startVsBot();
  }

  // ── DEFEAT SCREEN ─────────────────────────────────────────────
  function showDefeat() {
    BattleManager.destroy();

    const dc = document.getElementById('defeat-char');
    if (dc) {
      const char = getCharacter(saveData.selectedCharacter);
      dc.innerHTML = `<canvas width="120" height="120"></canvas>`;
      const dc_c = dc.querySelector('canvas');
      if (dc_c) {
        dc_c.style.borderRadius = '50%';
        // Draw with slight dark tint overlay for defeat feel
        drawPortraitOnCanvas(dc_c, char, 'hurt');
        const dctx = dc_c.getContext('2d');
        dctx.save();
        dctx.globalAlpha = 0.45;
        dctx.fillStyle = '#330000';
        dctx.beginPath(); dctx.arc(60,60,60,0,Math.PI*2); dctx.fill();
        dctx.restore();
        const src = char.profileImg || `assets/profile/${char.id}_profile.png`;
        if (!_profileCache[src]) {
          const tid = setInterval(() => {
            if (_profileCache[src] !== null) {
              drawPortraitOnCanvas(dc_c, char, 'hurt');
              const c2 = dc_c.getContext('2d');
              c2.save(); c2.globalAlpha=0.45; c2.fillStyle='#330000';
              c2.beginPath(); c2.arc(60,60,60,0,Math.PI*2); c2.fill(); c2.restore();
              clearInterval(tid);
            }
          }, 150);
          setTimeout(() => clearInterval(tid), 5000);
        }
      }
    }

    showScreen('screen-defeat');
    AudioManager.startBGM('dark');

    document.getElementById('btn-retry-loss').onclick = () => { AudioManager.play('click'); retryLevel(); };
    document.getElementById('btn-menu-loss').onclick  = () => { AudioManager.play('click'); goToMenu(); };
  }

  // ── GACHA SCREEN ──────────────────────────────────────────────
  function openGacha() {
    showScreen('screen-gacha');
    setText('gacha-coins', saveData.coins);
    const result = document.getElementById('gacha-result');
    if (result) result.style.display = 'none';

    AudioManager.startBGM('light');

    document.getElementById('btn-spin-1').onclick  = () => { AudioManager.play('click'); doGacha(1); };
    document.getElementById('btn-spin-10').onclick = () => { AudioManager.play('click'); doGacha(10); };
    document.getElementById('btn-back-menu-gacha').onclick = () => { AudioManager.play('click'); goToMenu(); };
  }

  function doGacha(count) {
    const result = GachaSystem.spin(saveData, count);
    if (!result.ok) {
      alert(result.msg);
      return;
    }
    SaveSystem.saveGame(saveData);
    setText('gacha-coins', saveData.coins);

    // Animate core
    const core = document.getElementById('gacha-core');
    if (core) {
      core.classList.add('spinning');
      AudioManager.play('gacha');
      setTimeout(() => {
        core.classList.remove('spinning');
        showGachaResult(result.results[result.results.length - 1]); // show last result
      }, 1200);
    }
  }

  function showGachaResult(res) {
    const panel = document.getElementById('gacha-result');
    const rChar = document.getElementById('gacha-result-char');
    const rName = document.getElementById('gacha-result-name');
    const rType = document.getElementById('gacha-result-type');

    if (!panel) return;
    panel.style.display = 'block';

    if (res.type === 'character') {
      const char = getCharacter(res.charId);
      rName.textContent = res.isNew ? `✨ NEW! ${char.name}` : char.name;
      rType.textContent = `${char.element} · ${char.role}`;

      // Show real profile image if available, otherwise canvas portrait
      const profileSrc = char.profileImg || `assets/profile/${char.id}_profile.png`;
      rChar.style.background = char.colors.primary;
      rChar.style.boxShadow  = `0 0 24px ${char.colors.glow}, 0 0 48px ${char.colors.glow}55`;
      rChar.style.border     = `3px solid ${char.colors.accent}`;

      const tryImg = new Image();
      tryImg.onload = () => {
        rChar.innerHTML = `<img src="${profileSrc}" style="width:100%;height:100%;object-fit:cover;border-radius:50%;" />`;
      };
      tryImg.onerror = () => {
        // Fallback: canvas draw
        rChar.innerHTML = `<canvas width="80" height="80" style="border-radius:50%;background:${char.colors.primary}"></canvas>`;
        const gc = rChar.querySelector('canvas');
        if (gc) {
          const gctx = gc.getContext('2d');
          SpriteManager.drawCharacter(gctx, char, 40, 75, false, 'victory', 0, 0);
        }
      };
      tryImg.src = profileSrc;

      // Big flash animation for new character
      if (res.isNew) {
        panel.style.animation = 'none';
        void panel.offsetWidth;
        panel.style.animation = 'gachaFlash 0.6s ease-out';
      }
    } else {
      rChar.style.boxShadow = '';
      rChar.style.border    = '2px solid var(--gold)';
      rChar.innerHTML = res.type === 'potion' ? '<span style="font-size:3rem">🧪</span>' :
                        res.type === 'coins'  ? '<span style="font-size:3rem">🪙</span>' :
                                               '<span style="font-size:3rem">⭐</span>';
      rName.textContent = res.name;
      rType.textContent = '';
    }
  }

  // ── SETTINGS SCREEN ───────────────────────────────────────────
  function openSettings() {
    showScreen('screen-settings');
    const s = saveData.settings || {};
    document.getElementById('music-vol').value   = s.musicVol     ?? 50;
    document.getElementById('sfx-vol').value     = s.sfxVol       ?? 80;
    document.getElementById('show-mobile').checked = s.showMobile ?? false;
    document.getElementById('ai-difficulty').value = s.aiDifficulty ?? 'normal';

    document.getElementById('btn-save-settings').onclick = () => {
      AudioManager.play('click');
      saveData.settings = {
        musicVol:     parseInt(document.getElementById('music-vol').value),
        sfxVol:       parseInt(document.getElementById('sfx-vol').value),
        showMobile:   document.getElementById('show-mobile').checked,
        aiDifficulty: document.getElementById('ai-difficulty').value,
      };
      AudioManager.setMusicVol(saveData.settings.musicVol);
      AudioManager.setSfxVol(saveData.settings.sfxVol);
      SaveSystem.saveGame(saveData);
      goToMenu();
    };

    document.getElementById('btn-reset-game').onclick = () => {
      if (confirm('Reset ALL progress? This cannot be undone.')) {
        saveData = SaveSystem.resetGame(saveData.username);
        SaveSystem.saveGame(saveData);
        goToMenu();
      }
    };

    document.getElementById('btn-back-menu-set').onclick = () => { AudioManager.play('click'); goToMenu(); };
  }

  // ── Utilities ─────────────────────────────────────────────────
  function setText(id, value) {
    const el = document.getElementById(id);
    if (el) el.textContent = value;
  }

  function getSaveData() { return saveData; }

  // ── Boot ─────────────────────────────────────────────────────
  function boot() {
    AudioManager.ensureCtx();
    runLoadingScreen(() => initLoginScreen());
  }

  return {
    boot, showScreen, showVictory, showDefeat,
    goToMenu, getSaveData,
  };
})();
