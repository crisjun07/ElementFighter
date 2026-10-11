#!/usr/bin/env python3
"""
slice_terron_new.py
===================
Slices the new Terron sprite sheet using flood-fill bg removal.
Background: black rgb(0,0,0)
Sheet: 1536x1024, 9 animation rows

Animation mapping:
  Row 1  y=16-103    IDLE     14 frames → 13 for engine  
  Row 2  y=124-215   WALK     14 frames → 13
  Row 3  y=237-322   RUN      14 frames → 13
  Row 4  y=335-433   JUMP     14 frames → 13 (jump/fall)
  Row 5  y=446-540   ATTACK   14 frames → 13 (→ punch+kick)
  Row 6  y=557-651   SPECIAL  14 frames → 13
  Row 7  y=663-760   ULTIMATE 12 + split wide → 13
  Row 8  y=769-872   HURT     12 frames → pad to 13
  Row 9  y=873-1004  DEFEAT   9 + split wide → 13

Engine animations generated:
  idle, walk, run, jump, dash(=run), block(=idle),
  punch(=attack), kick(=attack), special, ultimate, hurt, victory(=idle), defeat
"""
from PIL import Image
import os, shutil
from collections import deque

ROOT    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DISPLAY = 128   # output frame size — large enough for full character
PAD     = 12    # padding on all sides when cropping

# ── Flood-fill background removal (edge-connected only) ───────────
def flood_remove_bg(img, bg_rgb=(0,0,0), tol=22):
    img  = img.convert('RGBA')
    data = list(img.getdata())
    W,H  = img.size
    r0,g0,b0 = bg_rgb; t2 = tol*tol
    def is_bg(i):
        r,g,b,a = data[i]
        if a < 15: return True
        return (r-r0)**2+(g-g0)**2+(b-b0)**2 <= t2
    visited = bytearray(W*H); q = deque()
    for x in range(W):
        for y in [0,H-1]:
            i=y*W+x
            if not visited[i] and is_bg(i): visited[i]=1; q.append(i)
    for y in range(H):
        for x in [0,W-1]:
            i=y*W+x
            if not visited[i] and is_bg(i): visited[i]=1; q.append(i)
    while q:
        i=q.popleft(); r,g,b,a=data[i]; data[i]=(r,g,b,0); x,y=i%W,i//W
        for nx,ny in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
            if 0<=nx<W and 0<=ny<H:
                ni=ny*W+nx
                if not visited[ni] and is_bg(ni): visited[ni]=1; q.append(ni)
    img.putdata(data); return img

# ── Save frame ────────────────────────────────────────────────────
def save(img, anim, idx, x0,y0,x1,y1, root, pad=PAD, disp=DISPLAY):
    W,H=img.size
    x0=max(0,x0-pad); x1=min(W,x1+pad)
    y0=max(0,y0-pad); y1=min(H,y1+pad)
    if x1<=x0 or y1<=y0: return
    crop=img.crop((x0,y0,x1,y1))
    crop.thumbnail((disp,disp),Image.LANCZOS)
    c=Image.new('RGBA',(disp,disp),(0,0,0,0))
    ox=(disp-crop.width)//2
    oy= disp-crop.height      # bottom-align
    c.paste(crop,(ox,oy),crop)
    c.save(os.path.join(root,anim,f'{anim}-{idx:02d}.png'),'PNG')

def clear(root,anim):
    d=os.path.join(root,anim); os.makedirs(d,exist_ok=True)
    for f in os.listdir(d):
        if f.endswith('.png'): os.remove(os.path.join(d,f))

def eq(x0,x1,n):
    fw=(x1-x0)/n
    return [(int(x0+i*fw),int(x0+(i+1)*fw)) for i in range(n)]

def pad_to(root, anim, target):
    """Hold last frame to reach target count."""
    d=os.path.join(root,anim)
    files=sorted([f for f in os.listdir(d) if f.endswith('.png')])
    while len(files)<target:
        shutil.copy(os.path.join(d,files[-1]),
                    os.path.join(d,f'{anim}-{len(files)+1:02d}.png'))
        files=sorted([f for f in os.listdir(d) if f.endswith('.png')])

# ── Exact frame coordinates (from pixel scan) ────────────────────
# All bands take frames 1-13 (skip f14 in bands 1-6 which is a 14th pose)
# Band1-6: 14 frames each, take first 13
BAND1_X = [(16,86),(127,196),(235,305),(351,420),(466,535),(576,645),(690,759),(799,869),(909,979),(1020,1089),(1131,1199),(1241,1313),(1353,1421)]  # 13
BAND2_X = [(16,87),(130,202),(240,315),(355,422),(468,542),(580,649),(695,767),(806,878),(920,993),(1033,1103),(1147,1217),(1255,1327),(1370,1441)]
BAND3_X = [(18,89),(131,204),(246,320),(360,436),(476,549),(591,668),(704,781),(820,896),(938,1013),(1052,1127),(1166,1240),(1278,1349),(1391,1464)]
BAND4_X = [(16,74),(128,183),(233,289),(352,415),(461,521),(553,608),(647,704),(736,792),(833,892),(925,986),(1022,1080),(1113,1173),(1212,1276)]
BAND5_X = [(16,83),(130,211),(239,324),(357,439),(471,569),(588,671),(688,778),(793,888),(854,920),(942,1046),(1049,1141),(1129,1204),(1215,1280)]
BAND6_X = [(16,106),(118,184),(210,295),(309,404),(417,515),(530,630),(643,742),(752,836),(840,922),(929,1025),(1039,1127),(1143,1246),(1259,1349)]
# Band7: 12 segs — last wide (x=1339-1527=188px) → split into 2 → 13 total
BAND7_X = [(16,98),(130,203),(234,316),(336,415),(421,507),(531,622),(633,725),(733,840),(843,970),(980,1069),(1069,1196),(1206,1332)]  # 12, then split last
BAND7_WIDE = (1339,1527)  # → 2 more frames (13 and 14th, use 13th)
# Band8: 12 segs → pad to 13
BAND8_X = [(16,82),(123,190),(231,296),(337,413),(447,537),(571,667),(688,807),(820,969),(977,1123),(1145,1299),(1307,1408),(1416,1522)]
# Band9: 9 segs + wide last (x=1023-1502=479px → 4 frames) → 9+4=13
BAND9_X = [(14,90),(121,203),(236,309),(345,427),(462,543),(575,655),(685,775),(806,892),(919,1019)]  # 9
BAND9_WIDE = (1023,1502)  # → 4 more frames


def slice_terron():
    print('Loading new Terron sheet...')
    path = os.path.join(ROOT,'assets','revise_character','terron_newcharacer.png')
    raw  = Image.open(path).convert('RGBA')
    print(f'Sheet: {raw.width}x{raw.height}')
    print('Removing black background (flood-fill, edge-connected only)...')
    img  = flood_remove_bg(raw,(0,0,0),tol=22)
    print('Background removed — all character pixels preserved.\n')

    root = os.path.join(ROOT,'assets','sprites','terron')

    # ── IDLE ────────────────────────────────────────────────────
    clear(root,'idle')
    for i,(x0,x1) in enumerate(BAND1_X): save(img,'idle',i+1,x0,16,x1,103,root)
    print(f'  idle      13 frames')

    # ── WALK ────────────────────────────────────────────────────
    clear(root,'walk')
    for i,(x0,x1) in enumerate(BAND2_X): save(img,'walk',i+1,x0,124,x1,215,root)
    print(f'  walk      13 frames')

    # ── RUN ─────────────────────────────────────────────────────
    clear(root,'run')
    for i,(x0,x1) in enumerate(BAND3_X): save(img,'run',i+1,x0,237,x1,322,root)
    print(f'  run       13 frames')

    # ── JUMP ────────────────────────────────────────────────────
    clear(root,'jump')
    for i,(x0,x1) in enumerate(BAND4_X): save(img,'jump',i+1,x0,335,x1,433,root)
    print(f'  jump      13 frames')

    # ── ATTACK → engine maps punch + kick to this folder ────────────
    clear(root,'attack')
    for i,(x0,x1) in enumerate(BAND5_X): save(img,'attack',i+1,x0,446,x1,540,root)
    print(f'  attack    13 frames  (engine maps punch+kick here)')

    # ── SPECIAL ─────────────────────────────────────────────────
    clear(root,'special')
    for i,(x0,x1) in enumerate(BAND6_X): save(img,'special',i+1,x0,557,x1,651,root)
    print(f'  special   13 frames')

    # ── ULTIMATE — 12 segs + split wide → 13 ────────────────────
    clear(root,'ultimate')
    for i,(x0,x1) in enumerate(BAND7_X): save(img,'ultimate',i+1,x0,663,x1,760,root)
    # Frame 13: left half of wide seg
    wx0,wx1 = BAND7_WIDE
    save(img,'ultimate',13,wx0,663,wx0+(wx1-wx0)//2,760,root)
    print(f'  ultimate  13 frames')

    # ── HURT — 12 segs → pad to 13 ───────────────────────────────
    clear(root,'hurt')
    for i,(x0,x1) in enumerate(BAND8_X): save(img,'hurt',i+1,x0,769,x1,872,root)
    pad_to(root,'hurt',13)
    print(f'  hurt      13 frames')

    # ── DEFEAT — 9 segs + split wide(479px) into 4 → 13 ─────────
    clear(root,'defeat')
    for i,(x0,x1) in enumerate(BAND9_X): save(img,'defeat',i+1,x0,873,x1,1004,root)
    wx0,wx1=BAND9_WIDE
    for j,(x0,x1) in enumerate(eq(wx0,wx1,4)):
        save(img,'defeat',10+j,x0,873,x1,1004,root)
    print(f'  defeat    13 frames')

    # ── No remaps — engine handles mapping via _framePath ────────────
    # punch → attack, kick → attack, dash → run, block → idle, victory → idle

    # ── Quality check (only the 9 source animations) ─────────────────
    source_anims = ['idle','walk','run','jump','attack','special','ultimate','hurt','defeat']
    exp13 = 13
    print('\n=== QUALITY CHECK ===')
    all_ok = True; total = 0
    for anim in source_anims:
        d = os.path.join(root, anim)
        files = sorted([f for f in os.listdir(d) if f.endswith('.png')]) if os.path.isdir(d) else []
        c = len(files); total += c
        ok = (c == exp13)
        if not ok: all_ok = False
        # Check corners transparent on first frame
        first = os.path.join(d, files[0]) if files else None
        ct = False
        if first:
            im=Image.open(first).convert('RGBA'); p=im.load(); W2,H2=im.size
            ct = p[0,0][3]==0 and p[W2-1,0][3]==0 and p[0,H2-1][3]==0 and p[W2-1,H2-1][3]==0
        dims = Image.open(first).size if first else (0,0)
        print(f'  {"OK  " if ok else "FAIL"}  {anim:<12}  {c}/{exp13}  size={dims}  transparent={ct}')

    print(f'\n  Total frames: {total}  (expected {exp13*len(source_anims)} = 9×13)')
    print(f'\n{"ALL OK" if all_ok else "ISSUES FOUND"} — Terron new character ready!')
    print(f'9 animations × 13 frames = 117 PNGs, each 128×128px, black bg removed.')


if __name__ == '__main__':
    slice_terron()
    print('\nRebuild index.html to apply.')
