/* ═══════════════════════════════════════════════════════════════
   data/chapters.js  —  10 chapters × 5 levels = 50 levels

   MAP FILES  (all in assets/maps/)
   ─────────────────────────────────────────────────────────────
   Ch 1  blazor_map.png   — The Lost Valley  (Fire ruins)
   Ch 2  frostia_map.png  — Frozen Ruins     (Ice)
   Ch 3  voltra_map.png   — Thunder Peaks    (Lightning)
   Ch 4  floren_map.png   — Whispering Forest(Nature)
   Ch 5  aquara_map.png   — Sunken Temple    (Water)
   Ch 6  solara_map.png   — Crystal Caverns  (Light)
   Ch 7  zephyr_map.png   — Sky Citadel      (Wind)
   Ch 8  noctis_map.png   — Shadow Marsh     (Dark)
   Ch 9  venom_map.png    — Venom Wastes     (Poison)
   Ch 10 terron_map.png   — Final Elemental Core (Earth/Ruins)

   HOW TO ADD A NEW MAP
   ─────────────────────
   1. Drop PNG into  assets/maps/<name>_map.png
   2. Set  mapPath: 'assets/maps/<name>_map.png'  in the chapter.
   3. Engine loads it automatically; falls back to gradient if missing.
════════════════════════════════════════════════════════════════ */

const CHAPTERS = [
  {
    id: 1,
    name: 'The Lost Valley',
    description: 'Ancient ruins hidden in a forgotten valley, where warriors first harnessed elemental power.',
    theme: 'fire',
    bgColor: ['#1a0f05', '#2a1a0a', '#3a2510'],
    mapPath: 'assets/maps/blazor_map.png',
    enemies: ['blazor','aquara','terron','voltra'],
    boss:    'terron',
    bossName: 'STONE LORD',
    unlocked: true,
    rewards: { coins: 50, xp: 50, bossCoin: 120, bossXp: 100 },
  },
  {
    id: 2,
    name: 'Frozen Ruins',
    description: 'A civilization flash-frozen by an ice calamity. Danger lurks beneath the permafrost.',
    theme: 'ice',
    bgColor: ['#050d1a', '#0a1a2a', '#102535'],
    mapPath: 'assets/maps/frostia_map.png',
    enemies: ['frostia','zephyr','aquara','voltra'],
    boss:    'frostia',
    bossName: 'FROST QUEEN',
    unlocked: false,
    rewards: { coins: 55, xp: 60, bossCoin: 140, bossXp: 110 },
  },
  {
    id: 3,
    name: 'Thunder Peaks',
    description: 'Lightning storms are eternal here. Only the fastest survive.',
    theme: 'lightning',
    bgColor: ['#1a1400', '#2a2000', '#352800'],
    mapPath: 'assets/maps/voltra_map.png',
    enemies: ['voltra','zephyr','aquara','blazor'],
    boss:    'voltra',
    bossName: 'STORM KING',
    unlocked: false,
    rewards: { coins: 60, xp: 70, bossCoin: 150, bossXp: 120 },
  },
  {
    id: 4,
    name: 'Whispering Forest',
    description: 'A forest so alive it breathes. The trees remember every battle.',
    theme: 'nature',
    bgColor: ['#041008', '#07200d', '#0a2e12'],
    mapPath: 'assets/maps/floren_map.png',
    enemies: ['floren','aquara','zephyr','frostia'],
    boss:    'floren',
    bossName: 'FOREST ELDER',
    unlocked: false,
    rewards: { coins: 65, xp: 75, bossCoin: 160, bossXp: 130 },
  },
  {
    id: 5,
    name: 'Sunken Temple',
    description: 'An ancient temple submerged beneath a mystical ocean. Currents of water power flow endlessly.',
    theme: 'water',
    bgColor: ['#001520', '#002030', '#002d40'],
    mapPath: 'assets/maps/aquara_map.png',
    enemies: ['aquara','frostia','floren','voltra'],
    boss:    'aquara',
    bossName: 'TIDE WARDEN',
    unlocked: false,
    rewards: { coins: 70, xp: 80, bossCoin: 170, bossXp: 140 },
  },
  {
    id: 6,
    name: 'Crystal Caverns',
    description: 'Deep underground crystals amplify all elemental powers to dangerous extremes.',
    theme: 'light',
    bgColor: ['#1a1530', '#252040', '#302850'],
    mapPath: 'assets/maps/solara_map.png',
    enemies: ['solara','frostia','noctis','floren'],
    boss:    'solara',
    bossName: 'CRYSTAL SEER',
    unlocked: false,
    rewards: { coins: 80, xp: 90, bossCoin: 180, bossXp: 150 },
  },
  {
    id: 7,
    name: 'Sky Citadel',
    description: 'A floating fortress above the clouds. Wind warriors rule this domain.',
    theme: 'wind',
    bgColor: ['#0a1020', '#121825', '#1a2235'],
    mapPath: 'assets/maps/zephyr_map.png',
    enemies: ['zephyr','voltra','solara','aquara'],
    boss:    'zephyr',
    bossName: 'WIND SOVEREIGN',
    unlocked: false,
    rewards: { coins: 85, xp: 100, bossCoin: 190, bossXp: 160 },
  },
  {
    id: 8,
    name: 'Shadow Marsh',
    description: 'A cursed swampland where darkness consumes light itself.',
    theme: 'dark',
    bgColor: ['#07000f', '#0d0018', '#140022'],
    mapPath: 'assets/maps/noctis_map.png',
    enemies: ['noctis','venom','blazor','floren'],
    boss:    'noctis',
    bossName: 'SHADOW MASTER',
    unlocked: false,
    rewards: { coins: 90, xp: 110, bossCoin: 200, bossXp: 175 },
  },
  {
    id: 9,
    name: 'Venom Wastes',
    description: 'A blighted wasteland where every breath is toxic and every touch is deadly.',
    theme: 'poison',
    bgColor: ['#0a1200', '#101a00', '#162200'],
    mapPath: 'assets/maps/venom_map.png',
    enemies: ['venom','noctis','floren','terron'],
    boss:    'venom',
    bossName: 'VENOM LORD',
    unlocked: false,
    rewards: { coins: 100, xp: 120, bossCoin: 220, bossXp: 190 },
  },
  {
    id: 10,
    name: 'Final Elemental Core',
    description: 'The convergence of all elements. Face the ultimate champion to master them all.',
    theme: 'fire',
    bgColor: ['#200500', '#300800', '#3d0a00'],
    mapPath: 'assets/maps/terron_map.png',
    enemies: ['blazor','noctis','solara','aquara'],
    boss:    'blazor',
    bossName: 'ELEMENTAL OVERLORD',
    isFinalBoss: true,
    unlocked: false,
    rewards: { coins: 120, xp: 150, bossCoin: 280, bossXp: 250 },
  },
];

/**
 * Build a level object for a given chapter + level number (1–5).
 * Level 5 is always the boss fight.
 */
function buildLevel(chapterIndex, levelNum) {
  const ch     = CHAPTERS[chapterIndex];
  const isBoss = levelNum === 5;
  const enemyId = isBoss
    ? ch.boss
    : ch.enemies[(levelNum - 1) % ch.enemies.length];

  const difficulty = (chapterIndex * 5 + levelNum) / 50;

  return {
    chapterIndex,
    chapterId:      ch.id,
    levelNum,
    isBoss,
    enemyId,
    enemyName:      isBoss ? ch.bossName : getCharacter(enemyId).name,
    enemyLevel:     chapterIndex * 2 + levelNum,
    bossMultiplier: isBoss ? 2.5 : 1.0,
    aiDifficulty:   Math.min(1, 0.25 + difficulty * 0.75),
    rewards: isBoss
      ? { coins: ch.rewards.bossCoin, xp: ch.rewards.bossXp, potionChance: 0.6 }
      : { coins: ch.rewards.coins,    xp: ch.rewards.xp,     potionChance: 0.2 },
    bgColors: ch.bgColor,
    theme:    ch.theme,
    mapPath:  ch.mapPath || null,
  };
}

/** Get all chapters with unlock status based on save progress */
function getUnlockedChapters(chapterProgress) {
  return CHAPTERS.map((ch, i) => ({
    ...ch,
    unlocked:  i === 0 || chapterProgress >= i,
    completed: chapterProgress > i,
  }));
}
