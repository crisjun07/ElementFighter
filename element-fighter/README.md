# ELEMENT FIGHTER

> A 2D browser-based elemental fighting game. 10 characters, 10 chapters, 50 levels.

---

## How to Run

1. Open `index.html` directly in a modern browser (Chrome, Firefox, Edge, Safari).
2. No build step. No server required.
3. Register a username and password (stored locally in `localStorage`).
4. Select your fighter and battle your way through 10 chapters.

---

## Controls (Desktop Keyboard)

| Key          | Action         |
|--------------|----------------|
| A / ←        | Move Left      |
| D / →        | Move Right     |
| SPACE        | Jump           |
| SHIFT        | Dash           |
| J            | Punch          |
| I            | Kick           |
| K            | Special Attack |
| E            | Ultimate (energy must be full) |
| B            | Block          |
| ESC          | Pause          |

### Combos
- `J → J → I` — Punch–Punch–Kick
- `J → J → K` — Punch–Punch–Special  
- `J → J → J → K` — Blazing Rush (4-hit)
- `SPACE → I` — Air Kick

---

## Mobile Controls

Touch buttons are displayed at the bottom of the battle screen.  
Enable "Show Mobile Controls" in Settings to force them on desktop.

---

## File Structure

```
element-fighter/
├── index.html          # All screen containers
├── style.css           # Full UI stylesheet
├── game.js             # Entry point / boot loader
│
├── data/
│   ├── characters.js   # All 10 character definitions + stats
│   └── chapters.js     # 10 chapters × 5 levels data
│
├── js/
│   ├── save.js         # SaveSystem (localStorage)
│   ├── audio.js        # AudioManager (Web Audio API)
│   ├── sprites.js      # SpriteManager (procedural canvas renderer)
│   ├── progression.js  # XP/level tables, score formula
│   ├── gacha.js        # GachaSystem (character unlock)
│   ├── ai.js           # AISystem (enemy FSM)
│   ├── combat.js       # CombatSystem + ComboSystem + Fighter class
│   ├── battle.js       # BattleManager (game loop, rendering)
│   └── ui.js           # UIManager (all screen logic)
│
└── assets/
    ├── sprites/        # Sprite sheets go here (see below)
    └── sounds/         # Audio files go here (see below)
```

---

## How to Add a New Character

1. Open `data/characters.js`.
2. Copy an existing character object and push it into the `CHARACTERS` array.
3. Change `id`, `name`, `element`, `elementKey`, `colors`, `special`, `ultimate`, and stats.
4. Set `unlocked: false` and `startUnlocked: false` (player unlocks via Gacha).
5. Add sprite paths under `sprites: {}`.

---

## How to Add Sprite Sheets

The game checks for real sprite images and falls back to procedural canvas art if they are missing.

1. Create a folder: `assets/sprites/<characterId>/`
2. Add PNG files matching these names:
   - `idle.png`, `walk.png`, `run.png`, `jump.png`, `dash.png`
   - `block.png`, `punch.png`, `kick.png`, `hurt.png`
   - `special.png`, `ultimate.png`, `victory.png`
3. Each file should be a **horizontal sprite strip** (all frames in one row).
4. Update the character's `animations` config in `data/characters.js`:
   ```js
   animations: {
     idle: { frames: 6, fps: 8 },
     // ...
   }
   ```
5. To actually render the sheet, update `js/sprites.js` → `drawCharacter()`:
   Replace the procedural drawing block with:
   ```js
   const img = imageCache[char.sprites[anim]];
   if (img) {
     const fw = img.width / (char.animations[anim]?.frames || 1);
     ctx.drawImage(img, fw * frame, 0, fw, img.height, x - fw/2, y - img.height, fw, img.height);
   }
   ```

---

## How to Add Sound Files

`AudioManager` currently generates all sounds procedurally via Web Audio API.

To use real audio files:

1. Drop your `.mp3` / `.ogg` files into `assets/sounds/`.
2. In `js/audio.js`, replace the procedural `sounds` object entries with:
   ```js
   punch() { playBuffer('punch'); },
   ```
3. Add a `loadBuffer(name, src)` function:
   ```js
   async function loadBuffer(name, src) {
     const resp   = await fetch(src);
     const arrBuf = await resp.arrayBuffer();
     sfxBuffers[name] = await ctx.decodeAudioData(arrBuf);
   }
   ```
4. Call `loadBuffer('punch', 'assets/sounds/punch.mp3')` during loading.

---

## How to Modify Stats

All character stats live in `data/characters.js`.  
Key fields per character:

| Field         | Description                            |
|---------------|----------------------------------------|
| `maxHP`       | Starting hit points                    |
| `moveSpeed`   | Pixels per frame of movement           |
| `jumpForce`   | Upward velocity on jump                |
| `attackDmg`   | Punch damage                           |
| `kickDmg`     | Kick damage                            |
| `specialDmg`  | Special attack damage                  |
| `ultimateDmg` | Ultimate attack damage                 |
| `defenseRate` | % damage reduction when blocking (0–1) |
| `energyGain`  | Energy gained per successful hit       |

Level scaling is handled in `js/progression.js` → `applyPlayerLevel()`.

---

## How to Add Chapters

1. Open `data/chapters.js`.
2. Push a new object into the `CHAPTERS` array following the existing format.
3. Fields: `id`, `name`, `description`, `theme`, `bgColor` (array of 3 hex), `enemies`, `boss`, `bossName`, `rewards`.
4. The chapter becomes available after the previous chapter's boss is defeated.

---

## Save System

All progress is stored in `localStorage` under the key `elementFighterSave_v1_<username>`.

The save object shape:
```json
{
  "username": "player",
  "coins": 500,
  "xp": 250,
  "level": 3,
  "potions": 2,
  "unlockedCharacters": ["blazor", "aquara"],
  "selectedCharacter": "blazor",
  "chapterProgress": 1,
  "levelProgress": { "0_1": true, "0_2": true },
  "bestScore": 1850,
  "settings": {
    "musicVol": 50,
    "sfxVol": 80,
    "showMobile": false,
    "aiDifficulty": "normal"
  }
}
```

---

## Architecture Notes

- **No framework dependencies** — pure HTML5 / CSS3 / Vanilla JS.
- **Canvas API** is used for the battle scene only; all menus are DOM/CSS.
- **Sprite system** is designed to swap procedural art for real spritesheets without touching game logic.
- **AI** uses a finite-state machine with difficulty scaling from 0 (easy) to 1 (hard).
- **Combat** uses AABB hit boxes; projectiles travel as physics objects.
- **Combos** are detected by recording attack sequences within a time window.

---

*Element Fighter — prototype v1.0*
