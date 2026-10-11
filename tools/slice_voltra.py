#!/usr/bin/env python3
"""
slice_voltra.py  —  Precise Voltra sprite sheet slicer
=======================================================
Sheet: 1536x1024, light-grey background rgb(240,241,242)
Layout: 8 content bands, each with 11-12 frames.
Background removed → transparent PNG output.

Run: python tools/slice_voltra.py
"""
from PIL import Image
import os

DISPLAY = 96   # output frame size (square)
ROOT    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BG      = (240, 241, 242)   # background colour to remove
BG_TOL  = 32                # colour distance tolerance


# ─────────────────────────────────────────────────────────────────
def remove_bg(img, bg=BG, tol=BG_TOL):
    """Replace background colour with full transparency."""
    img = img.convert('RGBA')
    r0,g0,b0 = bg; t2 = tol*tol
    data = list(img.getdata())
    out  = [(0,0,0,0) if (r-r0)**2+(g-g0)**2+(b-b0)**2 < t2
            else (r,g,b,a) for r,g,b,a in data]
    img  = img.copy(); img.putdata(out)
    return img

def save(img, anim, idx, x0,y0,x1,y1, root):
    """Crop, scale, centre, and save one frame."""
    W,H = img.size
    x0=max(0,min(x0,W)); x1=max(0,min(x1,W))
    y0=max(0,min(y0,H)); y1=max(0,min(y1,H))
    if x1<=x0 or y1<=y0: return
    crop = img.crop((x0,y0,x1,y1))
    crop.thumbnail((DISPLAY,DISPLAY), Image.LANCZOS)
    c = Image.new('RGBA',(DISPLAY,DISPLAY),(0,0,0,0))
    c.paste(crop,((DISPLAY-crop.width)//2,(DISPLAY-crop.height)//2), crop)
    fname = f'{anim}-{idx:02d}.png'
    c.save(os.path.join(root, anim, fname), 'PNG')

def clear_dir(root, anim):
    d = os.path.join(root, anim)
    os.makedirs(d, exist_ok=True)
    for f in os.listdir(d):
        if f.endswith('.png'): os.remove(os.path.join(d,f))

def get_frame_segs(pix, w, y0, y1, bg=BG, tol=BG_TOL, min_w=30, thr_pct=0.03):
    """Return list of (x0,x1) content regions in the given row band."""
    r0,g0,b0=bg; t2=tol*tol
    def ok(r,g,b,a): return a>20 and (r-r0)**2+(g-g0)**2+(b-b0)**2>=t2
    cols = [(x, sum(1 for y in range(y0,y1,2) if ok(*pix[x,y])))
            for x in range(w)]
    mx  = max(c[1] for c in cols) or 1
    thr = mx * thr_pct
    in_g=True; segs=[]; fs=0
    for x,v in cols:
        if v<=thr and not in_g: segs.append((fs,x)); in_g=True
        elif v>thr and in_g: fs=x; in_g=False
    if not in_g: segs.append((fs,w))
    return [(a,b) for a,b in segs if b-a>=min_w]

def equal_split(x0,x1,n):
    w = (x1-x0)/n
    return [(int(x0+i*w), int(x0+(i+1)*w)) for i in range(n)]


# ─────────────────────────────────────────────────────────────────
# EXACT FRAME COORDINATES  (pixel-scanned from 1536×1024 sheet)
#
# Band/Row mapping:
#   Band1  y=7-117    → IDLE       12 frames
#   Band2  y=134-248  → WALK       12 frames
#   Band3  y=263-365  → RUN        12 frames
#   Band4  y=372-490  → JUMP       12 frames
#   Band5  y=503-613  → DASH       12 frames  (5th anim = dash/fall)
#   Band6  y=630-730  → BLOCK      12 frames  (slower, wider poses)
#   Band7  y=736-852  → PUNCH      12 frames  (f8 wide 248px = 2 frames)
#   Band8  y=858-1018 → KICK/SPECIAL/ULTIMATE/HURT/DEFEAT shared row
#
# NOTE: The sheet has 8 content rows × 12 frames = 96 source frames.
# Voltra's game animations mapped as follows:
#   idle    → Band1  12 frames
#   walk    → Band2  12 frames (pad last to 13 if needed; use 8 for engine)
#   run     → Band3  12 frames
#   jump    → Band4   8 frames (first 8)
#   dash    → Band5   6 frames (first 6)
#   block   → Band6   4 frames (first 4)
#   punch   → Band6  segs 5-10 = 6 frames
#   kick    → Band7  first 6 frames
#   special → Band7  frames 7-10 + 2 split of f8
#   ultimate→ Band8  first 10 frames
#   hurt    → Band8  frames 5-8 = 4 frames
#   victory → Band8  frames 9-12 = 6 frames (pad to 6)
#   defeat  → Band8  frames 9-12 = 6 frames (reuse + reverse)
# ─────────────────────────────────────────────────────────────────

def slice_voltra():
    path = os.path.join(ROOT,'tools','voltra_sheet.png')
    raw  = Image.open(path).convert('RGBA')
    img  = remove_bg(raw, BG, BG_TOL)
    W,H  = img.size
    pix  = img.load()
    root = os.path.join(ROOT,'assets','sprites','voltra')
    print('=== VOLTRA ===')
    print(f'Sheet: {W}×{H}  Background removed: rgb{BG}\n')

    # Pre-compute frame segments for each band
    bands = {
        1: (7,   117),
        2: (134, 248),
        3: (263, 365),
        4: (372, 490),
        5: (503, 613),
        6: (630, 730),
        7: (736, 852),
        8: (858, 1018),
    }

    segs = {}
    for b,(y0,y1) in bands.items():
        s = get_frame_segs(pix, W, y0, y1)
        # Band7 f8 (wide 248px) needs splitting into 2
        if b == 7:
            fixed = []
            for (x0,x1) in s:
                if x1-x0 > 180:  # this is the double frame
                    for sx0,sx1 in equal_split(x0,x1,2):
                        fixed.append((sx0,sx1))
                else:
                    fixed.append((x0,x1))
            s = fixed
        segs[b] = s

    for b,s in segs.items():
        y0,y1 = bands[b]
        print(f'  Band{b} y={y0}-{y1}  {len(s)} frames: widths {[x1-x0 for x0,x1 in s]}')
    print()

    # ── IDLE  Band1  8 frames ──────────────────────────────────────
    clear_dir(root,'idle')
    y0,y1 = bands[1]
    for i,(x0,x1) in enumerate(segs[1][:8]):
        save(img,'idle',i+1,x0,y0,x1,y1,root)
    print(f'  idle      8 frames')

    # ── WALK  Band2  8 frames ──────────────────────────────────────
    clear_dir(root,'walk')
    y0,y1 = bands[2]
    for i,(x0,x1) in enumerate(segs[2][:8]):
        save(img,'walk',i+1,x0,y0,x1,y1,root)
    print(f'  walk      8 frames')

    # ── RUN  Band3  8 frames ───────────────────────────────────────
    clear_dir(root,'run')
    y0,y1 = bands[3]
    for i,(x0,x1) in enumerate(segs[3][:8]):
        save(img,'run',i+1,x0,y0,x1,y1,root)
    print(f'  run       8 frames')

    # ── JUMP  Band4  6 frames ──────────────────────────────────────
    clear_dir(root,'jump')
    y0,y1 = bands[4]
    for i,(x0,x1) in enumerate(segs[4][:6]):
        save(img,'jump',i+1,x0,y0,x1,y1,root)
    print(f'  jump      6 frames')

    # ── DASH  Band5  6 frames ──────────────────────────────────────
    clear_dir(root,'dash')
    y0,y1 = bands[5]
    for i,(x0,x1) in enumerate(segs[5][:6]):
        save(img,'dash',i+1,x0,y0,x1,y1,root)
    print(f'  dash      6 frames')

    # ── BLOCK  Band6  4 frames (first 4 segs) ─────────────────────
    clear_dir(root,'block')
    y0,y1 = bands[6]
    for i,(x0,x1) in enumerate(segs[6][:4]):
        save(img,'block',i+1,x0,y0,x1,y1,root)
    print(f'  block     4 frames')

    # ── PUNCH  Band6  6 frames (segs 5-10) ────────────────────────
    clear_dir(root,'punch')
    y0,y1 = bands[6]
    punch_segs = segs[6][4:10]
    for i,(x0,x1) in enumerate(punch_segs):
        save(img,'punch',i+1,x0,y0,x1,y1,root)
    # Pad to 6 if short
    while len(punch_segs) < 6:
        save(img,'punch',len(punch_segs)+1,*punch_segs[-1],y0,y1,root)
        punch_segs.append(punch_segs[-1])
    print(f'  punch     6 frames')

    # ── KICK  Band7  6 frames (first 6) ───────────────────────────
    clear_dir(root,'kick')
    y0,y1 = bands[7]
    for i,(x0,x1) in enumerate(segs[7][:6]):
        save(img,'kick',i+1,x0,y0,x1,y1,root)
    print(f'  kick      6 frames')

    # ── SPECIAL  Band7  8 frames (segs 7-12, pad last 2) ──────────
    clear_dir(root,'special')
    y0,y1 = bands[7]
    spec_segs = segs[7][6:]  # segs 7-12 = 6 frames
    for i,(x0,x1) in enumerate(spec_segs):
        save(img,'special',i+1,x0,y0,x1,y1,root)
    # Pad frames 7 and 8 by holding the last frame
    while len(spec_segs) < 8:
        lx0,lx1 = spec_segs[-1]
        save(img,'special',len(spec_segs)+1,lx0,y0,lx1,y1,root)
        spec_segs.append((lx0,lx1))
    print(f'  special   8 frames')

    # ── ULTIMATE  Band8  10 frames (first 10) ─────────────────────
    clear_dir(root,'ultimate')
    y0,y1 = bands[8]
    ult_segs = segs[8][:10]
    for i,(x0,x1) in enumerate(ult_segs):
        save(img,'ultimate',i+1,x0,y0,x1,y1,root)
    if len(ult_segs) < 10 and ult_segs:
        for e in range(len(ult_segs)+1, 11):
            save(img,'ultimate',e,*ult_segs[-1],y0,y1,root)
    print(f'  ultimate  10 frames')

    # ── HURT  Band8  4 frames (frames 5-8 of band8 if enough, else 1-4) ──
    clear_dir(root,'hurt')
    y0,y1 = bands[8]
    hurt_src = segs[8][4:8] if len(segs[8]) >= 8 else segs[8][:4]
    for i,(x0,x1) in enumerate(hurt_src[:4]):
        save(img,'hurt',i+1,x0,y0,x1,y1,root)
    if len(hurt_src) < 4 and hurt_src:
        for e in range(len(hurt_src)+1,5):
            save(img,'hurt',e,*hurt_src[-1],y0,y1,root)
    print(f'  hurt      4 frames')

    # ── VICTORY  Band8  6 frames (last 6 of band8 or equal-split) ─
    clear_dir(root,'victory')
    y0,y1 = bands[8]
    vict_src = segs[8][-6:] if len(segs[8]) >= 6 else segs[8]
    for i,(x0,x1) in enumerate(vict_src[:6]):
        save(img,'victory',i+1,x0,y0,x1,y1,root)
    if len(vict_src) < 6 and vict_src:
        for e in range(len(vict_src)+1,7):
            save(img,'victory',e,*vict_src[-1],y0,y1,root)
    print(f'  victory   6 frames')

    # ── DEFEAT  Band8  6 frames (equal-split second half of band8) ─
    clear_dir(root,'defeat')
    y0,y1 = bands[8]
    # Get the x range of band8 content
    all8 = segs[8]
    if all8:
        x_start = all8[0][0]
        x_end   = all8[-1][1]
        # Split second half of content range into 6 equal sections
        mid = (x_start + x_end) // 2
        for i,(x0,x1) in enumerate(equal_split(mid, x_end, 6)):
            save(img,'defeat',i+1,x0,y0,x1,y1,root)
    print(f'  defeat    6 frames')


if __name__ == '__main__':
    slice_voltra()

    # Quality check
    anims = ['idle','walk','run','jump','dash','block','punch','kick',
             'special','ultimate','hurt','victory','defeat']
    exp   = [8,8,8,6,6,4,6,6,8,10,4,6,6]
    print('\n=== QUALITY CHECK ===')
    all_ok = True
    total  = 0
    for a,e in zip(anims, exp):
        d = os.path.join(ROOT,'assets','sprites','voltra',a)
        files = [f for f in os.listdir(d) if f.endswith('.png')] if os.path.isdir(d) else []
        c     = len(files)
        total += c
        ok    = c == e
        if not ok: all_ok = False
        print(f'  {"OK" if ok else "FAIL"}  {a:<12}  {c}/{e}')
    print(f'\n  Total frames: {total}')
    if all_ok:
        print('\nVOLTRA: ALL OK')
    else:
        print('\nSome issues above.')
    print('Done! Refresh index.html in Chrome.')
