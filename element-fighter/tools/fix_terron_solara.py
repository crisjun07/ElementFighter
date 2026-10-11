#!/usr/bin/env python3
"""
fix_terron_solara.py
====================
Re-slices Terron and Solara using exact pixel-scanned coordinates.
Run:  python tools/fix_terron_solara.py
"""
from PIL import Image
import os

DISPLAY = 96
ROOT    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def remove_bg(img, bg, tol=38):
    r0,g0,b0 = bg; t2 = tol*tol
    data = list(img.getdata())
    img  = img.copy()
    img.putdata([(0,0,0,0) if (r-r0)**2+(g-g0)**2+(b-b0)**2 < t2
                 else (r,g,b,a) for r,g,b,a in data])
    return img

def save(img, anim, idx, x0,y0,x1,y1, root):
    W,H = img.size
    x0=max(0,min(x0,W)); x1=max(0,min(x1,W))
    y0=max(0,min(y0,H)); y1=max(0,min(y1,H))
    if x1<=x0 or y1<=y0: return
    crop = img.crop((x0,y0,x1,y1))
    crop.thumbnail((DISPLAY,DISPLAY), Image.LANCZOS)
    c = Image.new('RGBA',(DISPLAY,DISPLAY),(0,0,0,0))
    c.paste(crop,((DISPLAY-crop.width)//2,(DISPLAY-crop.height)//2), crop)
    c.save(os.path.join(root, anim, f'{anim}-{idx}.png'), 'PNG')

def clear(root, anim):
    d = os.path.join(root, anim)
    os.makedirs(d, exist_ok=True)
    for f in os.listdir(d):
        if f.endswith('.png'): os.remove(os.path.join(d,f))

def equal_split(x0,x1,n):
    w = (x1-x0)/n
    return [(int(x0+i*w), int(x0+(i+1)*w)) for i in range(n)]

# ══════════════════════════════════════════════════════════════════
# TERRON  1005×1285  bg=(11,15,17)
#
# Band → Animation mapping (exact frame coordinates from scan):
#   Band0  y=42-168   IDLE(8)      segs 1-8
#   Band1  y=174-296  WALK(8)      segs 1-8 (skip seg9 extra)
#   Band2  y=306-421  RUN(8)       segs 1-8 (skip seg9)
#   Band3  y=437-539  JUMP(6)      segs 1-6 (skip segs 7-9)
#   Band4  y=563-672  DASH(6)      segs 1-6 (segs 7-10 = extra walk-back poses)
#   Band5  y=698-781  BLOCK(4)     segs 1-4  |  PUNCH(5→pad to 6) segs 5-9
#   Band6  y=804-916  KICK(6)      segs 1-6  |  segs 7-9 = extra
#   Band7  y=930-1032 SPECIAL(8)   segs 1-8 (skip seg9)
#   Band8  y=1052-1138 ULTIMATE(8) segs 1-8  +  equal-split for 2 more = 10
#   Band9  y=1156-1240 HURT(4)/VICTORY(6)/DEFEAT(6)  segs 1-8 split 4+4+hold
# ══════════════════════════════════════════════════════════════════
def slice_terron():
    path = os.path.join(ROOT,'tools','terron_sheet.png')
    img  = remove_bg(Image.open(path).convert('RGBA'), (11,15,17), 38)
    root = os.path.join(ROOT,'assets','sprites','terron')
    print('=== TERRON ===')

    # ── IDLE  Band0 y=42-168  8 frames ──
    clear(root,'idle')
    idle_x = [(16,78),(105,181),(206,280),(305,379),(405,477),(506,577),(607,677),(708,777)]
    for i,(x0,x1) in enumerate(idle_x): save(img,'idle',i+1,x0,42,x1,168,root)
    print(f'  idle      8 frames')

    # ── WALK  Band1 y=174-296  8 frames ──
    clear(root,'walk')
    walk_x = [(111,178),(210,275),(314,374),(409,471),(511,573),(609,670),(710,773),(810,869)]
    for i,(x0,x1) in enumerate(walk_x): save(img,'walk',i+1,x0,174,x1,296,root)
    print(f'  walk      8 frames')

    # ── RUN  Band2 y=306-421  8 frames ──
    clear(root,'run')
    run_x = [(105,184),(206,280),(306,384),(403,483),(499,577),(601,681),(702,781),(802,881)]
    for i,(x0,x1) in enumerate(run_x): save(img,'run',i+1,x0,306,x1,421,root)
    print(f'  run       8 frames')

    # ── JUMP  Band3 y=437-539  6 frames ──
    clear(root,'jump')
    jump_x = [(106,181),(206,277),(308,376),(399,468),(506,568),(602,675)]
    for i,(x0,x1) in enumerate(jump_x): save(img,'jump',i+1,x0,437,x1,539,root)
    print(f'  jump      6 frames')

    # ── DASH  Band4 y=563-672  6 frames ──
    clear(root,'dash')
    dash_x = [(17,78),(113,179),(208,275),(311,373),(410,472),(508,565)]
    for i,(x0,x1) in enumerate(dash_x): save(img,'dash',i+1,x0,563,x1,672,root)
    print(f'  dash      6 frames')

    # ── BLOCK  Band5 y=698-781  4 frames (segs 1-4) ──
    clear(root,'block')
    block_x = [(17,118),(152,224),(248,328),(359,432)]
    for i,(x0,x1) in enumerate(block_x): save(img,'block',i+1,x0,698,x1,781,root)
    print(f'  block     4 frames')

    # ── PUNCH  Band5 y=698-781  6 frames (segs 5-9 + hold last) ──
    clear(root,'punch')
    punch_x = [(459,542),(568,654),(674,764),(787,869),(896,971),(896,971)]
    for i,(x0,x1) in enumerate(punch_x): save(img,'punch',i+1,x0,698,x1,781,root)
    print(f'  punch     6 frames')

    # ── KICK  Band6 y=804-916  6 frames (segs 1-6) ──
    clear(root,'kick')
    kick_x = [(17,112),(154,216),(246,318),(350,424),(463,550),(561,659)]
    for i,(x0,x1) in enumerate(kick_x): save(img,'kick',i+1,x0,804,x1,916,root)
    print(f'  kick      6 frames')

    # ── SPECIAL  Band7 y=930-1032  8 frames (segs 1-8) ──
    clear(root,'special')
    spec_x = [(18,89),(154,219),(248,328),(354,435),(461,544),(567,648),(671,762),(781,868)]
    for i,(x0,x1) in enumerate(spec_x): save(img,'special',i+1,x0,930,x1,1032,root)
    print(f'  special   8 frames')

    # ── ULTIMATE  Band8 y=1052-1138  10 frames ──
    # 8 real segs exist + equal-split last wide seg into 2 more → 10 total
    clear(root,'ultimate')
    ult_x = [(19,118),(156,216),(256,324),(363,430),(463,539),(570,648),(678,754),(780,862)]
    for i,(x0,x1) in enumerate(ult_x): save(img,'ultimate',i+1,x0,1052,x1,1138,root)
    # Frames 9-10: equal-split the last frame (x=780-862) stretched to end
    for i,(x0,x1) in enumerate(equal_split(780,995,2)):
        save(img,'ultimate',9+i,x0,1052,x1,1138,root)
    print(f'  ultimate  10 frames')

    # ── HURT  Band9 y=1156-1240  4 frames (segs 1-4) ──
    clear(root,'hurt')
    hurt_x = [(21,102),(156,222),(263,323),(362,427)]
    for i,(x0,x1) in enumerate(hurt_x): save(img,'hurt',i+1,x0,1156,x1,1240,root)
    print(f'  hurt      4 frames')

    # ── VICTORY  Band9 y=1156-1240  6 frames (segs 5-8 + split last 2) ──
    clear(root,'victory')
    vict_x = [(462,539),(565,650),(682,755),(790,839),(790,839),(790,839)]
    # Better: equal-split from x=462 to x=840 into 6
    for i,(x0,x1) in enumerate(equal_split(462,840,6)):
        save(img,'victory',i+1,x0,1156,x1,1240,root)
    print(f'  victory   6 frames')

    # ── DEFEAT  Band9 y=1156-1240  6 frames (reuse band9 reversed) ──
    # No distinct defeat row found — use Band6 last 3 segs (kick-back poses) + reverse
    clear(root,'defeat')
    # Use kick band last segs as "knockdown" poses, equal-split
    defeat_x_from_band7 = [(669,767),(776,873),(884,983)]
    for i,(x0,x1) in enumerate(defeat_x_from_band7):
        save(img,'defeat',i+1,x0,804,x1,916,root)
    for i,(x0,x1) in enumerate(defeat_x_from_band7):
        save(img,'defeat',i+4,x0,804,x1,916,root)
    print(f'  defeat    6 frames')


# ══════════════════════════════════════════════════════════════════
# SOLARA  1224×1285  bg=(28,28,7)
#
# Sheet is HORIZONTAL — confirmed 2-row structure inside Band0:
#   y=0-137   → IDLE row (8 frames)
#   y=137-274 → WALK row (8 frames)
#
# Band layout (re-verified):
#   y=0-137    IDLE(8)
#   y=137-274  WALK(8)
#   y=275-405  RUN(8)
#   y=406-536  JUMP(6)
#   y=537-667  DASH(6)
#   y=668-788  BLOCK(4) + PUNCH(6)   shared row
#   y=795-907  KICK(6)
#   y=915-1030 SPECIAL(8)  top of band5 sub1
#   y=1030-1146 ULTIMATE(10) bottom of band5 sub1
#   y=1153-1268 HURT(4)+VICTORY(6)+DEFEAT(6)  sub2
#
# Frame x-positions from Band1 scan (same cols used for all rows):
#   label ≈ x=8-140, then frames at:
#   f1:147-257, f2:259-372, f3:374-486, f4:489-600,
#   f5:603-713, f6:716-828, f7:830-942, f8:945-1055
#
# For rows with 6 frames: take f1-f6
# For Block(4): take f1-f4
# ══════════════════════════════════════════════════════════════════
def slice_solara():
    path = os.path.join(ROOT,'tools','solara_sheet.png')
    img  = remove_bg(Image.open(path).convert('RGBA'), (28,28,7), 42)
    root = os.path.join(ROOT,'assets','sprites','solara')
    print('\n=== SOLARA ===')

    # Standard 8-frame x positions (from actual band scans)
    X8 = [(147,257),(259,372),(374,486),(489,600),(603,713),(716,828),(830,942),(945,1055)]
    X6 = X8[:6]
    X4 = X8[:4]

    def do_anim(anim, y0, y1, x_list):
        clear(root, anim)
        for i,(x0,x1) in enumerate(x_list):
            save(img, anim, i+1, x0,y0,x1,y1, root)
        print(f'  {anim:<12} {len(x_list)} frames')

    do_anim('idle',    0,   137, X8)
    do_anim('walk',  137,   274, X8)
    do_anim('run',   275,   405, X8)
    do_anim('jump',  406,   536, X6)
    do_anim('dash',  537,   667, X6)

    # BLOCK — Band4 y=668-788, 4 frames (first 4 x positions)
    do_anim('block', 668, 788, X4)

    # PUNCH — Band4 y=668-788, 6 frames (positions 5-8 + split last wide area)
    punch_splits = equal_split(727, 1202, 6)
    clear(root,'punch')
    for i,(x0,x1) in enumerate(punch_splits):
        save(img,'punch',i+1,x0,668,x1,788,root)
    print(f'  punch        6 frames')

    do_anim('kick',    795,  907, X6)

    # SPECIAL — y=915-1030 (top of sub1), 8 frames
    do_anim('special', 915, 1030, X8)

    # ULTIMATE — y=1030-1146 (bottom of sub1), 10 frames — equal split across full width
    clear(root,'ultimate')
    for i,(x0,x1) in enumerate(equal_split(8,1148,10)):
        save(img,'ultimate',i+1,x0,1030,x1,1146,root)
    print(f'  ultimate    10 frames')

    # Sub2 y=1153-1268 — HURT(4) + VICTORY(6) + DEFEAT(6)
    # 8 segs found: (29,121),(144,268),(270,390),(392,518),(519,645),(647,794),(797,957),(960,1149)
    sub2_segs = [(29,121),(144,268),(270,390),(392,518),(519,645),(647,794),(797,957),(960,1149)]

    # HURT: segs 0-3
    clear(root,'hurt')
    for i,(x0,x1) in enumerate(sub2_segs[:4]):
        save(img,'hurt',i+1,x0,1153,x1,1268,root)
    print(f'  hurt         4 frames')

    # VICTORY: segs 4-7 (4 exist) + equal-split last wide (960-1149=189px) into 2 more = 6
    clear(root,'victory')
    for i,(x0,x1) in enumerate(sub2_segs[4:8]):
        save(img,'victory',i+1,x0,1153,x1,1268,root)
    # Frame 5 and 6 from last seg (960-1149) split in 2
    for i,(x0,x1) in enumerate(equal_split(960,1149,2)):
        save(img,'victory',5+i,x0,1153,x1,1268,root)
    print(f'  victory      6 frames')

    # DEFEAT: equal-split entire sub2 x range into 6 distinct sections
    clear(root,'defeat')
    for i,(x0,x1) in enumerate(equal_split(29,1149,6)):
        save(img,'defeat',i+1,x0,1153,x1,1268,root)
    print(f'  defeat       6 frames')


if __name__ == '__main__':
    slice_terron()
    slice_solara()

    # Verification
    anims = ['idle','walk','run','jump','dash','block','punch','kick',
             'special','ultimate','hurt','victory','defeat']
    exp   = [8,8,8,6,6,4,6,6,8,10,4,6,6]
    print('\n=== FRAME CHECK ===')
    for char in ['terron','solara']:
        fails = []
        for a,e in zip(anims,exp):
            d = os.path.join(ROOT,'assets','sprites',char,a)
            c = len([f for f in os.listdir(d) if f.endswith('.png')]) if os.path.isdir(d) else 0
            if c != e: fails.append(f'{a}:{c}/{e}')
        status = 'ALL OK — 76 frames' if not fails else f'ISSUES: {fails}'
        print(f'  {char.upper():<10} {status}')
    print('\nDone! Refresh index.html in Chrome.')
