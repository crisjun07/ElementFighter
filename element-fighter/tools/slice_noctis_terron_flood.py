#!/usr/bin/env python3
"""
slice_noctis_terron_flood.py
=============================
Re-slices Noctis and Terron using FLOOD-FILL background removal.
Only pixels CONNECTED TO THE SHEET EDGE become transparent.
Interior skin, armour, glow, and shadow effects are NEVER removed.

Noctis: 1024x1536  bg≈rgb(10,15,23)   dark bg
Terron: 1005x1285  bg≈rgb(11,15,17)   dark bg
"""
from PIL import Image
import os, shutil
from collections import deque

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── Flood-fill background removal ────────────────────────────────
def flood_remove_bg(img, bg_rgb, tol=28):
    """Remove only edge-connected background. Interior always preserved."""
    img  = img.convert('RGBA')
    data = list(img.getdata())
    W, H = img.size
    r0,g0,b0 = bg_rgb
    t2 = tol * tol

    def is_bg(idx):
        r,g,b,a = data[idx]
        return (r-r0)**2+(g-g0)**2+(b-b0)**2 <= t2

    visited = bytearray(W*H)
    q = deque()

    # Seed all 4 edges
    for x in range(W):
        for y in [0, H-1]:
            i=y*W+x
            if not visited[i] and is_bg(i):
                visited[i]=1; q.append(i)
    for y in range(H):
        for x in [0, W-1]:
            i=y*W+x
            if not visited[i] and is_bg(i):
                visited[i]=1; q.append(i)

    while q:
        i=q.popleft()
        r,g,b,a=data[i]; data[i]=(r,g,b,0)
        x,y=i%W, i//W
        for nx,ny in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
            if 0<=nx<W and 0<=ny<H:
                ni=ny*W+nx
                if not visited[ni] and is_bg(ni):
                    visited[ni]=1; q.append(ni)

    img.putdata(data)
    return img

# ── Save one frame ────────────────────────────────────────────────
DISPLAY = 96

def save(img, anim, idx, x0,y0,x1,y1, root):
    W,H=img.size
    x0=max(0,min(x0,W)); x1=max(0,min(x1,W))
    y0=max(0,min(y0,H)); y1=max(0,min(y1,H))
    if x1<=x0 or y1<=y0: return
    crop=img.crop((x0,y0,x1,y1))
    crop.thumbnail((DISPLAY,DISPLAY),Image.LANCZOS)
    c=Image.new('RGBA',(DISPLAY,DISPLAY),(0,0,0,0))
    c.paste(crop,((DISPLAY-crop.width)//2,(DISPLAY-crop.height)//2),crop)
    c.save(os.path.join(root,anim,f'{anim}-{idx}.png'),'PNG')

def clear(root,anim):
    d=os.path.join(root,anim); os.makedirs(d,exist_ok=True)
    for f in os.listdir(d):
        if f.endswith('.png'): os.remove(os.path.join(d,f))

def eq(x0,x1,n):
    fw=(x1-x0)/n
    return [(int(x0+i*fw),int(x0+(i+1)*fw)) for i in range(n)]

def check(root, anim, expected):
    d=os.path.join(root,anim)
    c=len([f for f in os.listdir(d) if f.endswith('.png')]) if os.path.isdir(d) else 0
    ok=c==expected
    print(f'  {"OK  " if ok else "FAIL"}  {anim:<12}  {c}/{expected}')
    return ok

# ══════════════════════════════════════════════════════════════════
# NOCTIS  1024×1536  bg=rgb(10,15,23)
# Band layout (from original pixel scan):
#   Band0  y=13-109    IDLE(8)
#   Band1  y=135-229   WALK(8)
#   Band2  y=255-348   RUN(8)
#   Band3  y=364-476   JUMP(6)
#   Band4  y=497-582   DASH(6)
#   Band5  y=598-696   BLOCK(4)
#   Band6  y=711-810   PUNCH(6)
#   Band7  y=834-941   KICK(6)
#   Band8  y=963-1067  SPECIAL(8)
#   Band9  y=1094-1206 ULTIMATE(10)
#   Band10 y=1216-1294 HURT(4)
#   Band11 y=1303-1402 VICTORY(6)
#   Band12 y=1429-1492 DEFEAT(6)
# ══════════════════════════════════════════════════════════════════
def slice_noctis():
    print('\n=== NOCTIS (flood-fill) ===')
    path=os.path.join(ROOT,'tools','noctis.png')
    raw=Image.open(path).convert('RGBA')
    print(f'Sheet: {raw.width}x{raw.height}  BG: rgb(10,15,23)')
    print('Flood-filling edges...')
    img=flood_remove_bg(raw,(10,15,23),tol=28)
    print('Done.\n')

    root=os.path.join(ROOT,'assets','sprites','noctis')

    # IDLE
    clear(root,'idle')
    for i,(x0,x1) in enumerate([(157,209),(245,294),(331,382),(419,469),(509,560),(596,647),(682,733),(768,821)]):
        save(img,'idle',i+1,x0,13,x1,109,root)

    # WALK
    clear(root,'walk')
    for i,(x0,x1) in enumerate([(222,297),(315,380),(406,473),(498,560),(587,645),(671,734),(760,822),(849,909)]):
        save(img,'walk',i+1,x0,135,x1,229,root)

    # RUN
    clear(root,'run')
    for i,(x0,x1) in enumerate([(402,480),(493,568),(579,663),(663,747),(747,831),(844,917),(844,917),(844,917)]):
        save(img,'run',i+1,x0,255,x1,348,root)

    # JUMP
    clear(root,'jump')
    for i,(x0,x1) in enumerate([(278,348),(398,474),(519,590),(638,724),(763,839),(763,839)]):
        save(img,'jump',i+1,x0,364,x1,476,root)

    # DASH
    clear(root,'dash')
    for i,(x0,x1) in enumerate([(266,380),(395,506),(521,637),(655,788),(819,968),(819,968)]):
        save(img,'dash',i+1,x0,497,x1,582,root)

    # BLOCK
    clear(root,'block')
    for i,(x0,x1) in enumerate([(155,230),(259,338),(373,458),(496,581)]):
        save(img,'block',i+1,x0,598,x1,696,root)

    # PUNCH
    clear(root,'punch')
    for i,(x0,x1) in enumerate([(265,380),(395,492),(511,608),(622,700),(700,778),(778,856)]):
        save(img,'punch',i+1,x0,711,x1,810,root)

    # KICK
    clear(root,'kick')
    for i,(x0,x1) in enumerate([(147,255),(274,384),(384,494),(516,609),(620,733),(757,844)]):
        save(img,'kick',i+1,x0,834,x1,941,root)

    # SPECIAL (8 frames — equal-split full content range)
    clear(root,'special')
    for i,(x0,x1) in enumerate(eq(262,1009,8)):
        save(img,'special',i+1,x0,955,x1,1075,root)

    # ULTIMATE (10 frames — equal-split)
    clear(root,'ultimate')
    for i,(x0,x1) in enumerate(eq(11,1015,10)):
        save(img,'ultimate',i+1,x0,1086,x1,1214,root)

    # HURT
    clear(root,'hurt')
    for i,(x0,x1) in enumerate([(153,230),(247,313),(345,413),(449,557)]):
        save(img,'hurt',i+1,x0,1216,x1,1294,root)

    # VICTORY
    clear(root,'victory')
    for i,(x0,x1) in enumerate([(173,236),(277,329),(365,425),(468,528),(573,647),(677,729)]):
        save(img,'victory',i+1,x0,1303,x1,1402,root)

    # DEFEAT
    clear(root,'defeat')
    for i,(x0,x1) in enumerate([(266,359),(376,468),(491,595),(621,711),(738,855),(738,855)]):
        save(img,'defeat',i+1,x0,1429,x1,1492,root)

    print('Results:')
    anims=['idle','walk','run','jump','dash','block','punch','kick','special','ultimate','hurt','victory','defeat']
    exp  =[8,8,8,6,6,4,6,6,8,10,4,6,6]
    all_ok=True
    for a,e in zip(anims,exp):
        if not check(root,a,e): all_ok=False
    print(f'\n  {"NOCTIS ALL OK" if all_ok else "NOCTIS HAS ISSUES"}')

# ══════════════════════════════════════════════════════════════════
# TERRON  1005×1285  bg=rgb(11,15,17)
# Band layout (from original pixel scan):
#   Band0  y=42-168    IDLE(8)
#   Band1  y=174-296   WALK(8)
#   Band2  y=306-421   RUN(8)
#   Band3  y=437-539   JUMP(6)
#   Band4  y=563-672   DASH(6)
#   Band5  y=698-781   BLOCK(4) + PUNCH(6)
#   Band6  y=804-916   KICK(6)
#   Band7  y=930-1032  SPECIAL(8)
#   Band8  y=1052-1138 ULTIMATE(10)
#   Band9  y=1156-1240 HURT(4) + VICTORY(6)
#   Extra  y=1247-1285 DEFEAT(6)
# ══════════════════════════════════════════════════════════════════
def slice_terron():
    print('\n=== TERRON (flood-fill) ===')
    path=os.path.join(ROOT,'tools','terron_sheet.png')
    raw=Image.open(path).convert('RGBA')
    print(f'Sheet: {raw.width}x{raw.height}  BG: rgb(11,15,17)')
    print('Flood-filling edges...')
    img=flood_remove_bg(raw,(11,15,17),tol=28)
    print('Done.\n')

    root=os.path.join(ROOT,'assets','sprites','terron')

    # IDLE  Band0 y=42-168
    clear(root,'idle')
    for i,(x0,x1) in enumerate([(16,78),(105,181),(206,280),(305,379),(405,477),(506,577),(607,677),(708,777)]):
        save(img,'idle',i+1,x0,42,x1,168,root)

    # WALK  Band1 y=174-296
    clear(root,'walk')
    for i,(x0,x1) in enumerate([(111,178),(210,275),(314,374),(409,471),(511,573),(609,670),(710,773),(810,869)]):
        save(img,'walk',i+1,x0,174,x1,296,root)

    # RUN  Band2 y=306-421
    clear(root,'run')
    for i,(x0,x1) in enumerate([(105,184),(206,280),(306,384),(403,483),(499,577),(601,681),(702,781),(802,881)]):
        save(img,'run',i+1,x0,306,x1,421,root)

    # JUMP  Band3 y=437-539
    clear(root,'jump')
    for i,(x0,x1) in enumerate([(106,181),(206,277),(308,376),(399,468),(506,568),(602,675)]):
        save(img,'jump',i+1,x0,437,x1,539,root)

    # DASH  Band4 y=563-672
    clear(root,'dash')
    for i,(x0,x1) in enumerate([(17,78),(113,179),(208,275),(311,373),(410,472),(508,565)]):
        save(img,'dash',i+1,x0,563,x1,672,root)

    # BLOCK  Band5 y=698-781  (first 4 segs)
    clear(root,'block')
    for i,(x0,x1) in enumerate([(17,118),(152,224),(248,328),(359,432)]):
        save(img,'block',i+1,x0,698,x1,781,root)

    # PUNCH  Band5 y=698-781  (segs 5-10)
    clear(root,'punch')
    for i,(x0,x1) in enumerate([(459,542),(568,654),(674,764),(787,869),(896,971),(896,971)]):
        save(img,'punch',i+1,x0,698,x1,781,root)

    # KICK  Band6 y=804-916
    clear(root,'kick')
    for i,(x0,x1) in enumerate([(17,112),(154,216),(246,318),(350,424),(463,550),(561,659)]):
        save(img,'kick',i+1,x0,804,x1,916,root)

    # SPECIAL  Band7 y=930-1032
    clear(root,'special')
    for i,(x0,x1) in enumerate([(18,89),(154,219),(248,328),(354,435),(461,544),(567,648),(671,762),(781,868)]):
        save(img,'special',i+1,x0,930,x1,1032,root)

    # ULTIMATE  Band8 y=1052-1138  10 frames
    clear(root,'ultimate')
    ult8=[(19,118),(156,216),(256,324),(363,430),(463,539),(570,648),(678,754),(780,862)]
    for i,(x0,x1) in enumerate(ult8):
        save(img,'ultimate',i+1,x0,1052,x1,1138,root)
    for i,(x0,x1) in enumerate(eq(780,995,2)):
        save(img,'ultimate',9+i,x0,1052,x1,1138,root)

    # HURT  Band9 y=1156-1240  (first 4 segs)
    clear(root,'hurt')
    for i,(x0,x1) in enumerate([(21,102),(156,222),(263,323),(362,427)]):
        save(img,'hurt',i+1,x0,1156,x1,1240,root)

    # VICTORY  Band9 y=1156-1240  (equal-split second half)
    clear(root,'victory')
    for i,(x0,x1) in enumerate(eq(462,840,6)):
        save(img,'victory',i+1,x0,1156,x1,1240,root)

    # DEFEAT  Extra row y=1247-1285  (equal-split big seg 414-993)
    clear(root,'defeat')
    for i,(x0,x1) in enumerate(eq(414,993,6)):
        save(img,'defeat',i+1,x0,1247,x1,1285,root)

    print('Results:')
    anims=['idle','walk','run','jump','dash','block','punch','kick','special','ultimate','hurt','victory','defeat']
    exp  =[8,8,8,6,6,4,6,6,8,10,4,6,6]
    all_ok=True
    for a,e in zip(anims,exp):
        if not check(root,a,e): all_ok=False
    print(f'\n  {"TERRON ALL OK" if all_ok else "TERRON HAS ISSUES"}')

# ══════════════════════════════════════════════════════════════════
if __name__=='__main__':
    slice_noctis()
    slice_terron()

    # Quick interior pixel check — dark skins should still have non-dark opaque pixels
    print('\n=== INTERIOR PIXEL CHECK ===')
    for char,anim in [('noctis','idle'),('terron','idle')]:
        fp=f'assets/sprites/{char}/{anim}/{anim}-1.png'
        if not os.path.exists(fp): print(f'  {char} {anim}-1: MISSING'); continue
        img=Image.open(fp).convert('RGBA')
        p=img.load(); w,h=img.size
        opaque=sum(1 for y in range(h) for x in range(w) if p[x,y][3]>40)
        # non-dark opaque = skin/highlight pixels
        bright=sum(1 for y in range(h) for x in range(w)
                   if p[x,y][3]>100 and max(p[x,y][:3])>60)
        corner_ok=p[0,0][3]==0 and p[w-1,0][3]==0
        print(f'  {char} {anim}-1:  opaque={opaque} ({round(opaque/(w*h)*100,1)}%)  '
              f'bright_interior={bright}  corners_transparent={corner_ok}')

    print('\nDone! Rebuild index.html to apply.')
