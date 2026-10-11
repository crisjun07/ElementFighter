/* ═══════════════════════════════════════════════════════════════
   js/save.js  —  SaveSystem
   localStorage-based persistence. Swap saveToServer() / loadFromServer()
   to connect a real backend later.
════════════════════════════════════════════════════════════════ */

const SaveSystem = (() => {
  const STORAGE_KEY = 'elementFighterSave_v1';
  const USERS_KEY   = 'elementFighterUsers_v1';

  // ── Default save template ─────────────────────────────────────
  function defaultSave(username) {
    return {
      username,
      coins:    100,          // starting coins (harder economy)
      xp:       0,
      level:    1,
      potions:  2,
      unlockedCharacters: ['blazor'],
      selectedCharacter:  'blazor',
      chapterProgress: 0,     // highest chapter index beaten
      levelProgress:   {},    // { 'ch_lv': true } completed levels
      bestScore: 0,
      settings: {
        musicVol:     50,
        sfxVol:       80,
        showMobile:   false,
        aiDifficulty: 'normal',
      },
      createdAt: Date.now(),
      lastSaved: Date.now(),
    };
  }

  // ── User registry (username → hashed-ish password) ───────────
  function getUsers() {
    try { return JSON.parse(localStorage.getItem(USERS_KEY)) || {}; }
    catch { return {}; }
  }
  function saveUsers(users) {
    localStorage.setItem(USERS_KEY, JSON.stringify(users));
  }

  /** Very simple hash — not cryptographic, prototype only */
  function hashPassword(pw) {
    let h = 0;
    for (let i = 0; i < pw.length; i++) h = (Math.imul(31, h) + pw.charCodeAt(i)) | 0;
    return h.toString(16);
  }

  // ── Public API ────────────────────────────────────────────────
  function register(username, password) {
    const uname = username.trim().toLowerCase();
    if (!uname || uname.length < 2) return { ok: false, msg: 'Username too short (min 2 chars).' };
    if (!password || password.length < 3) return { ok: false, msg: 'Password too short (min 3 chars).' };
    const users = getUsers();
    if (users[uname]) return { ok: false, msg: 'Username already taken.' };
    users[uname] = hashPassword(password);
    saveUsers(users);
    // Create fresh save
    const save = defaultSave(uname);
    localStorage.setItem(`${STORAGE_KEY}_${uname}`, JSON.stringify(save));
    return { ok: true };
  }

  function login(username, password) {
    const uname = username.trim().toLowerCase();
    const users = getUsers();
    if (!users[uname]) return { ok: false, msg: 'Username not found.' };
    if (users[uname] !== hashPassword(password)) return { ok: false, msg: 'Incorrect password.' };
    return { ok: true };
  }

  function loadGame(username) {
    const uname = username.trim().toLowerCase();
    try {
      const raw = localStorage.getItem(`${STORAGE_KEY}_${uname}`);
      if (!raw) return defaultSave(uname);
      const save = JSON.parse(raw);
      // Migrate missing fields from future versions
      return Object.assign(defaultSave(uname), save);
    } catch {
      return defaultSave(uname);
    }
  }

  function saveGame(data) {
    if (!data || !data.username) return;
    data.lastSaved = Date.now();
    localStorage.setItem(`${STORAGE_KEY}_${data.username}`, JSON.stringify(data));
  }

  function resetGame(username) {
    const uname = username.trim().toLowerCase();
    const fresh = defaultSave(uname);
    localStorage.setItem(`${STORAGE_KEY}_${uname}`, JSON.stringify(fresh));
    return fresh;
  }

  function isLevelCompleted(saveData, chapterIndex, levelNum) {
    return !!(saveData.levelProgress && saveData.levelProgress[`${chapterIndex}_${levelNum}`]);
  }

  function markLevelCompleted(saveData, chapterIndex, levelNum) {
    if (!saveData.levelProgress) saveData.levelProgress = {};
    saveData.levelProgress[`${chapterIndex}_${levelNum}`] = true;
    // Unlock next chapter if boss beaten
    if (levelNum === 5) {
      saveData.chapterProgress = Math.max(saveData.chapterProgress, chapterIndex + 1);
    }
  }

  return { register, login, loadGame, saveGame, resetGame, isLevelCompleted, markLevelCompleted, defaultSave };
})();
