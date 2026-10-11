/* ═══════════════════════════════════════════════════════════════
   js/gacha.js  —  GachaSystem
   Handles the Element Core spin mechanic.
════════════════════════════════════════════════════════════════ */

const GachaSystem = (() => {
  const SPIN_COST  = 300;
  const SPIN10_COST = 2700;

  /** Perform n spins. Returns array of result objects. */
  function spin(saveData, count = 1) {
    const cost = count === 1 ? SPIN_COST : SPIN10_COST;
    if (saveData.coins < cost) return { ok: false, msg: 'Not enough coins!', results: [] };

    saveData.coins -= cost;
    const results = [];

    for (let i = 0; i < count; i++) {
      results.push(doSingleSpin(saveData));
    }
    return { ok: true, results };
  }

  function doSingleSpin(saveData) {
    const locked = CHARACTERS.filter(c => !saveData.unlockedCharacters.includes(c.id));

    if (locked.length > 0) {
      // 70% chance to unlock a locked character
      if (Math.random() < 0.70) {
        const char = locked[Math.floor(Math.random() * locked.length)];
        saveData.unlockedCharacters.push(char.id);
        return { type: 'character', charId: char.id, name: char.name, isNew: true };
      }
    }

    // Otherwise — duplicate or bonus
    const roll = Math.random();
    if (roll < 0.45) {
      // Coins bonus — smaller amounts (harder to accumulate)
      const bonus = 20 + Math.floor(Math.random() * 40);
      saveData.coins += bonus;
      return { type: 'coins', amount: bonus, name: `+${bonus} Coins` };
    } else if (roll < 0.75) {
      // Potion
      saveData.potions = (saveData.potions || 0) + 1;
      return { type: 'potion', name: '+1 Potion' };
    } else {
      // XP bonus
      const xp = 30 + Math.floor(Math.random() * 60);
      ProgressionSystem.addXp(saveData, xp);
      return { type: 'xp', amount: xp, name: `+${xp} XP` };
    }
  }

  return { spin, SPIN_COST, SPIN10_COST };
})();
