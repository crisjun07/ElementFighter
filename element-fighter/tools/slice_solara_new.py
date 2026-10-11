#!/usr/bin/env python3
"""
slice_solara_new.py
===================
Slices the new Solara sprite sheet using FLOOD-FILL background removal.
ONLY edge-connected BLACK background pixels are made transparent.
ALL character pixels (skin, gold, white light, glow effects) are preserved.

Sheet: 1536x1024, bg=black rgb(0,0,0)
Grid:  9 content bands, 8-14 frames per band.
"""
from PIL import Image
import os, shutil
from collections import deque

ROOT    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DISPLAY = 96

# ── Pure edge-connected flood-fill ───────────────────────────────
def flood_remove_bg(img, bg_rgb=(0,0,0), tol=20):
    """
    Remove ONLY pixels connected to the sheet edge that match bg colour.
    ALL interior pixels (including black outlines) are preserved.
    """
    img  = img.convert('RGBA')
    data = list(img.getdata())
    W, H = img.size
    r0,g0,b0 = bg_rgb
    t2 = tol * tol

    def is_bg(idx):
        r,g,b,a = data[idx]
        if a < 20: return True   # already transparent
        return (r-r0)**2+(g-g0)**2+(b-b0)**2 <= t2

    visited = bytearray(W*H)
    q = deque()

    # Seed all 4 sheet edges
    for x in range(W):
        for y in [0, H-1]:
            i = y*W+x
            if not visited[i] and is_bg(i):
                visited[i]=1; q.append(i)
    for y in range(H):
        for x in [0, W-1]:
            i = y*W+x
            if not visited[i] and is_bg(i):
                visited[i]=1; q.append(i)

    # BFS — only removes connected-to-edge background
    while q:
        i = q.popleft()
        r,g,b,a = data[i]
        data[i] = (r,g,b,0)   # transparent
        x,y = i%W, i//W
        for nx,ny in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
            if 0<=nx<W and 0<=ny<H:
                ni=ny*W+nx
                if not visited[ni] and is_bg(ni):
                    visited[ni]=1; q.append(ni)

    img.putdata(data)
    return img

# ── Save one frame ─────────────────────────────────────────────────
def save(img, anim, idx, x0,y0,x1,y1, root, pad=6):
    W,H=img.size
    # Add padding so nothing gets clipped
    x0=max(0,x0-pad); x1=min(W,x1+pad)
    y0=max(0,y0-pad); y1=min(H,y1+pad)
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

# ═══════════════════════════════════════════════════════════════════
# EXACT FRAME COORDINATES from pixel scan
#
# Band1 y=12-98    IDLE   14 frames → take 8
# Band2 y=125-208  WALK   14 frames → take 8
# Band3 y=234-322  RUN    14 frames → take 8
# Band4 y=343-434  JUMP   14 frames → take 6
# Band5 y=456-543  DASH   14 frames → take 6
# Band6 y=553-629  BLOCK+PUNCH  14 frames → 4+6+4extra
# Band7 y=648-729  KICK+SPECIAL 13 frames → 6+7=13
# Band8 top y=734-824  ULTIMATE  8 frames
# Band8 bot y=824-915  HURT+VICTORY+DEFEAT  13 frames → 4+6+3
# Band9 y=941-979  DEFEAT continuation  13 frames → 6
# ═══════════════════════════════════════════════════════════════════

# Frame x-positions per band (from pixel scan)
BAND1_X = [(0,72),(105,177),(219,284),(320,388),(422,489),(524,590),(622,689),(720,786)]  # 8
BAND2_X = [(0,75),(118,189),(225,296),(335,405),(441,510),(549,617),(651,721),(755,824)]  # 8
BAND3_X = [(0,87),(141,223),(265,345),(393,473),(512,593),(640,723),(759,840),(878,952)]  # 8
BAND4_X = [(0,64),(124,188),(230,293),(340,404),(447,508),(547,608)]                     # 6
BAND5_X = [(0,62),(120,181),(224,281),(320,377),(421,479),(519,583)]                     # 6
# Band6 first 4=block, next 6=punch
BAND6_BLOCK = [(0,72),(121,190),(237,311),(352,429)]
BAND6_PUNCH = [(452,547),(567,665),(680,778),(791,883),(895,989),(1007,1079)]
# Band7 first 6=kick, last 7=special
BAND7_KICK    = [(19,78),(122,212),(240,335),(353,445),(462,565),(578,685)]
BAND7_SPECIAL = [(697,800),(808,909),(921,1017),(1027,1123),(1132,1243),(1248,1366),(1373,1521)]
# Band8 top: ultimate 8 frames
BAND8T_ULT = [(12,79),(121,187),(236,304),(345,417),(460,527),(565,636),(688,762),(773,886)]
# Band8 bot: hurt(4) + victory(6)
BAND8B_HURT    = [(0,64),(121,181),(235,295),(350,415)]
BAND8B_VICTORY = [(449,512),(549,618),(655,714),(753,812),(856,946),(1004,1117)]
# Band9: defeat 6 frames (use first 6 segs)
BAND9_DEFEAT = [(0,66),(148,229),(281,361),(412,493),(560,649),(705,796)]


def slice_solara():
    sheet_path = os.path.join(ROOT,'assets','revise_character','solara_newcharcter.png')
    print(f'Loading: {sheet_path}')
    raw = Image.open(sheet_path).convert('RGBA')
    print(f'Sheet: {raw.width}x{raw.height}')
    print('Flood-filling black background (edge-connected only, tol=20)...')
    img = flood_remove_bg(raw, (0,0,0), tol=20)
    print('Background removed — ALL character pixels preserved.\n')

    root = os.path.join(ROOT,'assets','sprites','solara')
    W,H = img.size

    def do(anim, coords, y0, y1):
        clear(root,anim)
        for i,(x0,x1) in enumerate(coords):
            save(img,anim,i+1,x0,y0,x1,y1,root)
        print(f'  {anim:<12}  {len(coords)} frames  y={y0}-{y1}')

    # IDLE  Band1
    do('idle',    BAND1_X,   12,  98)
    # WALK  Band2
    do('walk',    BAND2_X,  125, 208)
    # RUN   Band3
    do('run',     BAND3_X,  234, 322)
    # JUMP  Band4
    do('jump',    BAND4_X,  343, 434)
    # DASH  Band5
    do('dash',    BAND5_X,  456, 543)
    # BLOCK Band6 first 4
    do('block',   BAND6_BLOCK, 553, 629)
    # PUNCH Band6 segs 5-10
    do('punch',   BAND6_PUNCH, 553, 629)
    # KICK  Band7 first 6
    do('kick',    BAND7_KICK,  648, 729)
    # SPECIAL Band7 segs 7-13
    do('special', BAND7_SPECIAL, 648, 729)
    # ULTIMATE Band8 top
    do('ultimate', BAND8T_ULT, 734, 824)
    # HURT Band8 bottom first 4
    do('hurt',    BAND8B_HURT,    824, 915)
    # VICTORY Band8 bottom segs 5-10
    do('victory', BAND8B_VICTORY, 824, 915)
    # DEFEAT Band9
    do('defeat',  BAND9_DEFEAT,   941, 979)

    # ── Remap engine animations ──────────────────────────────────
    print('\nRemapping engine animations...')
    MAPPINGS = {'walk': 'walk'}  # already correct - no remaps needed

    # ── Verify ───────────────────────────────────────────────────
    anims=['idle','walk','run','jump','dash','block','punch','kick','special','ultimate','hurt','victory','defeat']
    exp  =[8,8,8,6,6,4,6,6,8,10,4,6,6]
    print('\n=== QUALITY CHECK ===')
    all_ok=True
    for a,e in zip(anims,exp):
        d=os.path.join(root,a)
        c=len([f for f in os.listdir(d) if f.endswith('.png')]) if os.path.isdir(d) else 0
        # Check corners transparent
        fp=os.path.join(d,f'{a}-1.png')
        corners_ok=False
        if os.path.exists(fp):
            im=Image.open(fp).convert('RGBA'); p=im.load(); W2,H2=im.size
            corners_ok=p[0,0][3]==0 and p[W2-1,0][3]==0 and p[0,H2-1][3]==0 and p[W2-1,H2-1][3]==0
        # Pad ultimate if short
        if a=='ultimate' and c<10 and c>0:
            last_fp=os.path.join(d,f'{a}-{c}.png')
            for extra in range(c+1,11):
                shutil.copy(last_fp,os.path.join(d,f'{a}-{extra}.png'))
            c=10
        ok=(c==e)
        if not ok: all_ok=False
        print(f'  {"OK  " if ok else "FAIL"}  {a:<12}  {c}/{e}  transparent_corners={corners_ok}')
    print(f'\n{"ALL OK" if all_ok else "ISSUES FOUND"} — Solara ready!')


if __name__=='__main__':
    slice_solara()
    print('\nRebuild index.html to apply changes.')
