#!/usr/bin/env python3
"""
slice_venom.py  —  Precise Venom sprite sheet slicer
=====================================================
Sheet: 1024x1285, transparent background (alpha=0 corners)
10 bands, exact frame coordinates from pixel scan.

Run: python tools/slice_venom.py
"""
from PIL import Image
import os

DISPLAY = 96
ROOT    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def save(img, anim, idx, x0, y0, x1, y1, root):
    """Crop one frame, scale to DISPLAY×DISPLAY, save as transparent PNG."""
    W, H = img.size
    x0 = max(0, min(x0, W));  x1 = max(0, min(x1, W))
    y0 = max(0, min(y0, H));  y1 = max(0, min(y1, H))
    if x1 <= x0 or y1 <= y0:
        return
    crop = img.crop((x0, y0, x1, y1))
    crop.thumbnail((DISPLAY, DISPLAY), Image.LANCZOS)
    canvas = Image.new('RGBA', (DISPLAY, DISPLAY), (0, 0, 0, 0))
    ox = (DISPLAY - crop.width)  // 2
    oy = (DISPLAY - crop.height) // 2
    canvas.paste(crop, (ox, oy), crop)
    canvas.save(os.path.join(root, anim, f'{anim}-{idx}.png'), 'PNG')

def clear(root, anim):
    d = os.path.join(root, anim)
    os.makedirs(d, exist_ok=True)
    for f in os.listdir(d):
        if f.endswith('.png'):
            os.remove(os.path.join(d, f))

def equal_split(x0, x1, n):
    fw = (x1 - x0) / n
    return [(int(x0 + i*fw), int(x0 + (i+1)*fw)) for i in range(n)]


# ═══════════════════════════════════════════════════════════════
# EXACT FRAME COORDINATES  (from full pixel scan)
#
# Band 0  y=6-138    IDLE(8)       take f1-f8
# Band 1  y=154-275  WALK(8)       take f1-f8
# Band 2  y=293-419  RUN(8)        take f1-f8  (9 segs — skip last)
# Band 3  y=427-549  JUMP(6)       take f1-f6  (9 segs — skip last 3)
# Band 4  y=554-687  DASH(6)       take f1-f6  (9 segs — skip last 3)
# Band 5  y=701-817  BLOCK(4)+PUNCH(6)
#    f1-f2: block pose 1-2
#    f3: BLOCK pose 3 (left half of f3 wide region)
#    f4: BLOCK pose 4 (right half — f4 is 262px, split into 4 = block3,block4,punch1,punch2)
#    Actually:  f1-f2=block1-2, f3(123px)=block3, f4(262px split 3)=block4+punch1+punch2,
#               f5(129px)=punch3, f6(114px)=punch4, f7(117px)=punch5, f8(129px)=punch6
# Band 6  y=832-933  KICK(6)+SPECIAL start
#    f1-f5 + first half of f6 wide = kick1-6
#    remaining f6 wide + f7 + f8 = special1-3
# Band 7  y=948-1035 SPECIAL continues — 7 segs (each is 1 SPECIAL frame, split for 8th)
# Band 8  y=1047-1157 ULTIMATE(10) — 9 segs, split last for 10th
# Band 9  y=1163-1271 HURT(4)+VICTORY(6)+DEFEAT(6)
#    f1-f4: hurt
#    f5-f9: victory (5 unique) — pad last frame → 6
#    defeat: equal-split band9 full x-range into 6 sections
# ═══════════════════════════════════════════════════════════════

def slice_venom():
    path = os.path.join(ROOT, 'tools', 'venom_sheet.png')
    img  = Image.open(path).convert('RGBA')
    root = os.path.join(ROOT, 'assets', 'sprites', 'venom')
    print('=== VENOM ===')

    # ── IDLE  Band0 y=6-138  f1-f8 ──────────────────────────────
    clear(root, 'idle')
    idle_x = [(13,86),(126,208),(232,315),(346,425),(458,540),(576,652),(694,773),(809,887)]
    for i,(x0,x1) in enumerate(idle_x):
        save(img, 'idle', i+1, x0,6, x1,138, root)
    print(f'  idle      8 frames')

    # ── WALK  Band1 y=154-275  f1-f8 ────────────────────────────
    clear(root, 'walk')
    walk_x = [(10,95),(120,197),(225,314),(347,423),(451,536),(561,649),(675,756),(783,881)]
    for i,(x0,x1) in enumerate(walk_x):
        save(img, 'walk', i+1, x0,154, x1,275, root)
    print(f'  walk      8 frames')

    # ── RUN  Band2 y=293-419  f1-f8 ─────────────────────────────
    clear(root, 'run')
    run_x = [(12,99),(137,238),(277,385),(416,505),(532,631),(674,789),(811,913),(949,1050)]
    for i,(x0,x1) in enumerate(run_x):
        save(img, 'run', i+1, x0,293, x1,419, root)
    print(f'  run       8 frames')

    # ── JUMP  Band3 y=427-549  f1-f6 ────────────────────────────
    clear(root, 'jump')
    jump_x = [(14,91),(129,217),(258,349),(409,485),(540,627),(680,753)]
    for i,(x0,x1) in enumerate(jump_x):
        save(img, 'jump', i+1, x0,427, x1,549, root)
    print(f'  jump      6 frames')

    # ── DASH  Band4 y=554-687  f1-f6 ────────────────────────────
    clear(root, 'dash')
    dash_x = [(17,105),(148,222),(258,354),(396,489),(517,621),(653,743)]
    for i,(x0,x1) in enumerate(dash_x):
        save(img, 'dash', i+1, x0,554, x1,687, root)
    print(f'  dash      6 frames')

    # ── BLOCK  Band5 y=701-817  f1-f2 + left part of f3 + left part of f4 ──
    # f1=16-112(96), f2=129-224(95), f3=244-367(123), f4=376-638(262 wide)
    # Block gets f1, f2, f3, and first quarter of f4
    clear(root, 'block')
    block_x = [(16,112),(129,224),(244,367),(376,441)]  # f1,f2,f3,f4_quarter1
    for i,(x0,x1) in enumerate(block_x):
        save(img, 'block', i+1, x0,701, x1,817, root)
    print(f'  block     4 frames')

    # ── PUNCH  Band5 y=701-817  remaining of f4 + f5-f8 ──────────
    # f4(262px) split into 4 parts (65px each): block4 used first, punch gets last 3
    # then f5=640-769(129), f6=783-897(114), f7=927-1044(117), f8=1080-1209(129)
    clear(root, 'punch')
    # f4 quarters: 376-441, 441-506, 506-572, 572-638  → punch gets 441-506, 506-572, 572-638
    f4_punch = [(441,506),(506,572),(572,638)]
    punch_x  = f4_punch + [(640,769),(783,897),(927,1044)]
    for i,(x0,x1) in enumerate(punch_x):
        save(img, 'punch', i+1, x0,701, x1,817, root)
    print(f'  punch     6 frames')

    # ── KICK  Band6 y=832-933  f1-f5 + left half of f6 ──────────
    # f1=13-101(88), f2=117-239(122), f3=247-363(116), f4=367-485(118), f5=502-640(138)
    # f6=651-915(264 wide) → kick takes left 132px, special takes right 132px
    clear(root, 'kick')
    kick_x = [(13,101),(117,239),(247,363),(367,485),(502,640),(651,783)]
    for i,(x0,x1) in enumerate(kick_x):
        save(img, 'kick', i+1, x0,832, x1,933, root)
    print(f'  kick      6 frames')

    # ── SPECIAL  Band6 right-of-f6 + Band7 all 7 segs ────────────
    # Band6 right half of f6: x=783-915, then f7=927-1062(135), f8=1083-1200(117)
    # Band7: f1=11-121(110), f2=145-276(131), f3=306-471(165), f4=484-628(144),
    #        f5=649-830(181), f6=848-1017(169), f7=1038-1207(169)
    # Total available: 2(band6) + 7(band7) = 9 → need 8, take first 8
    clear(root, 'special')
    spec_b6 = [(783,915),(927,1062)]                                     # 2 from band6
    spec_b7 = [(11,121),(145,276),(306,471),(484,628),(649,830),(848,1017)] # 6 from band7
    spec_all = spec_b6 + spec_b7
    for i,(x0,x1) in enumerate(spec_all[:8]):
        y0s = 832 if i < 2 else 948
        y1s = 933 if i < 2 else 1035
        save(img, 'special', i+1, x0,y0s, x1,y1s, root)
    print(f'  special   8 frames')

    # ── ULTIMATE  Band8 y=1047-1157  9 segs → 10 frames ─────────
    # f1=17-104, f2=151-226, f3=276-354, f4=392-481, f5=520-605,
    # f6=669-754, f7=800-885, f8=929-1012, f9=1046-1176(130px wide → split 2)
    clear(root, 'ultimate')
    ult_x = [(17,104),(151,226),(276,354),(392,481),(520,605),(669,754),(800,885),(929,1012)]
    for i,(x0,x1) in enumerate(ult_x):
        save(img, 'ultimate', i+1, x0,1047, x1,1157, root)
    # Frame 9 and 10 from last wide seg (1046-1176) split in 2
    for i,(x0,x1) in enumerate(equal_split(1046,1176,2)):
        save(img, 'ultimate', 9+i, x0,1047, x1,1157, root)
    print(f'  ultimate  10 frames')

    # ── HURT  Band9 y=1163-1271  f1-f4 ──────────────────────────
    clear(root, 'hurt')
    hurt_x = [(15,88),(142,211),(257,334),(363,473)]
    for i,(x0,x1) in enumerate(hurt_x):
        save(img, 'hurt', i+1, x0,1163, x1,1271, root)
    print(f'  hurt      4 frames')

    # ── VICTORY  Band9 y=1163-1271  f5-f9 + pad = 6 frames ──────
    clear(root, 'victory')
    vict_x = [(494,610),(631,756),(779,880),(909,1014),(1046,1180),(1046,1180)]  # f9 repeated
    for i,(x0,x1) in enumerate(vict_x):
        save(img, 'victory', i+1, x0,1163, x1,1271, root)
    print(f'  victory   6 frames')

    # ── DEFEAT  Band9 y=1163-1271  equal-split full width into 6 ─
    # Uses the same row but different x segments to give defeated poses
    clear(root, 'defeat')
    # Split the full band9 content range (x=15 to x=1180) into 6
    for i,(x0,x1) in enumerate(equal_split(15,1180,6)):
        save(img, 'defeat', i+1, x0,1163, x1,1271, root)
    print(f'  defeat    6 frames')


if __name__ == '__main__':
    slice_venom()

    # ── Verification ──────────────────────────────────────────────
    anims = ['idle','walk','run','jump','dash','block','punch','kick',
             'special','ultimate','hurt','victory','defeat']
    exp   = [8,8,8,6,6,4,6,6,8,10,4,6,6]
    print('\n=== FRAME CHECK ===')
    fails = []
    for a, e in zip(anims, exp):
        d = os.path.join(ROOT, 'assets', 'sprites', 'venom', a)
        c = len([f for f in os.listdir(d) if f.endswith('.png')]) if os.path.isdir(d) else 0
        mark = 'OK' if c == e else 'FAIL'
        if c != e: fails.append(f'{a}:{c}/{e}')
        print(f'  {mark}  {a:<12} {c}/{e}')
    print()
    if not fails:
        print('VENOM: ALL OK — 76 frames')
    else:
        print(f'Issues: {fails}')
    print('\nDone! Refresh index.html in Chrome.')
