/* ═══════════════════════════════════════════════════════════════
   js/progression.js  —  ProgressionSystem
   XP thresholds, level-up logic, stat scaling.
════════════════════════════════════════════════════════════════ */

const ProgressionSystem = (() => {
  // XP required to REACH each level (index = level - 1)
  const XP_TABLE = [
    0,      // Lv 1  (starting)
    100,    // Lv 2
    250,    // Lv 3
    450,    // Lv 4
    700,    // Lv 5
    1000,   // Lv 6
    1350,   // Lv 7
    1750,   // Lv 8
    2200,   // Lv 9
    2700,   // Lv 10
    3250,   // Lv 11
    3850,   // Lv 12
    4500,   // Lv 13
    5200,   // Lv 14
    5950,   // Lv 15
    6750,   // Lv 16
    7600,   // Lv 17
    8500,   // Lv 18
    9450,   // Lv 19
    10450,  // Lv 20 (cap)
  ];
  const MAX_LEVEL = XP_TABLE.length;

  function xpForLevel(lv) {
    return XP_TABLE[Math.min(lv - 1, MAX_LEVEL - 1)] || 0;
  }

  /** Returns the XP needed to reach next level from current level */
  function xpToNextLevel(currentLevel) {
    if (currentLevel >= MAX_LEVEL) return Infinity;
    return XP_TABLE[currentLevel] - XP_TABLE[currentLevel - 1];
  }

  /** Excess XP above current level threshold */
  function xpProgressInLevel(totalXp, currentLevel) {
    const base = XP_TABLE[currentLevel - 1] || 0;
    const next = XP_TABLE[currentLevel]     || Infinity;
    return {
      current: totalXp - base,
      needed:  next - base,
      pct:     next === Infinity ? 1 : Math.min(1, (totalXp - base) / (next - base)),
    };
  }

  /** Returns the level that corresponds to a given total XP */
  function levelFromXp(totalXp) {
    for (let i = XP_TABLE.length - 1; i >= 0; i--) {
      if (totalXp >= XP_TABLE[i]) return i + 1;
    }
    return 1;
  }

  /**
   * Add XP to save data. Returns { leveledUp, newLevel, oldLevel }.
   */
  function addXp(saveData, amount) {
    const oldLevel = saveData.level;
    saveData.xp = (saveData.xp || 0) + amount;
    const newLevel = Math.min(levelFromXp(saveData.xp), MAX_LEVEL);
    saveData.level = newLevel;
    return { leveledUp: newLevel > oldLevel, newLevel, oldLevel };
  }

  /** Score formula */
  function calcScore({ punches=0, kicks=0, specials=0, ultimates=0,
                        maxCombo=0, victory=false, bossKill=false }) {
    let score = 0;
    score += punches  * 10;
    score += kicks    * 15;
    score += specials * 30;
    score += ultimates* 75;
    score += maxCombo * maxCombo * 5; // quadratic combo bonus
    if (victory) score += 200;
    if (bossKill) score += 500;
    return score;
  }

  /** Apply player level bonuses to combat stats */
  function applyPlayerLevel(charData, playerLevel) {
    const scale = 1 + (playerLevel - 1) * 0.04;
    return Object.assign({}, charData, {
      maxHP:       Math.round(charData.maxHP * scale),
      attackDmg:   Math.round(charData.attackDmg * scale),
      kickDmg:     Math.round(charData.kickDmg * scale),
      specialDmg:  Math.round(charData.specialDmg * scale),
      ultimateDmg: Math.round(charData.ultimateDmg * scale),
      energyGain:  charData.energyGain + (playerLevel - 1) * 0.5,
    });
  }

  return {
    xpForLevel, xpToNextLevel, xpProgressInLevel, levelFromXp,
    addXp, calcScore, applyPlayerLevel, MAX_LEVEL,
  };
})();
