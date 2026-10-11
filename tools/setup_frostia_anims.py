#!/usr/bin/env python3
"""Copy remapped Frostia animations to match engine animation names."""
import os, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
base = os.path.join(ROOT, 'assets', 'sprites', 'frostia')

# New sheet provides: idle, walk, run, jump, attack, special, ultimate, hurt, defeat
# Engine needs:       idle, walk, run, jump, dash, block, punch, kick, special, ultimate, hurt, victory, defeat
MAPPINGS = {
    'punch':   'attack',   # attack used for punch
    'kick':    'attack',   # attack used for kick
    'dash':    'run',      # run used for dash (faster movement)
    'block':   'walk',     # walk used for block (defensive stance)
    'victory': 'idle',     # idle used for victory
}

print('=== Remapping Frostia animations ===')
for target, source in MAPPINGS.items():
    src_dir = os.path.join(base, source)
    tgt_dir = os.path.join(base, target)
    os.makedirs(tgt_dir, exist_ok=True)
    # Clear
    for f in os.listdir(tgt_dir):
        if f.endswith('.png'): os.remove(os.path.join(tgt_dir, f))
    # Copy with renamed prefix
    files = sorted([f for f in os.listdir(src_dir) if f.endswith('.png')])
    for fname in files:
        new_name = fname.replace(source, target)
        shutil.copy(os.path.join(src_dir, fname), os.path.join(tgt_dir, new_name))
    print(f'  {target:<12} <- {source:<12}  {len(files)} frames')

print()
print('=== Final verification ===')
engine_anims = ['idle','walk','run','jump','dash','block','punch','kick',
                'special','ultimate','hurt','victory','defeat']
all_ok = True
for anim in engine_anims:
    d = os.path.join(base, anim)
    files = sorted([f for f in os.listdir(d) if f.endswith('.png')]) if os.path.isdir(d) else []
    first = files[0] if files else 'NONE'
    ok = len(files) == 13 and first == f'{anim}-01.png'
    if not ok: all_ok = False
    mark = 'OK  ' if ok else 'FAIL'
    print(f'  {mark}  {anim:<12}  {len(files)} frames  first={first}')

print()
if all_ok:
    print('ALL OK — Frostia new character fully ready!')
else:
    print('Issues found above.')
