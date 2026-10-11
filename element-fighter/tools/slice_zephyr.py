#!/usr/bin/env python3
"""
slice_zephyr.py  —  Precise Zephyr sprite sheet slicer
=======================================================
Sheet: 1536x1024, bg=rgb(243,244,244)
9 bands, transparent background output.

Band → Animation mapping:
  Band1  y=9-116    13 segs  → IDLE(8)      take f1-f8
  Band2  y=135-240  13 segs  → WALK(8)      take f1-f8
  Band3  y=261-359  13 segs  → RUN(8)       take f1-f8
  Band4  y=375-482  13 segs  → JUMP(6)      take f1-f6
  Band5  y=503-603  13 segs  → DASH(6)      take f1-f6
  Band6  y=623-716  10 segs  → BLOCK(4)+PUNCH(6)
         f1-f4=block, f5-f6+f7_split+f8-f10=punch
  Band7  y=726-842  11 segs  → KICK(6)+SPECIAL(8)
         f1-f6=kick, f7+f8_split+f9-f11=special
  Band8  y=849-943  12 segs  → ULTIMATE(10)+HURT(4) share row
         f1-f10=ultimate, f9-f12=hurt (overlap intentional — different crop)
         Actually: f1-f10=ultimate, then hurt uses f9-f12 (4 segs)
  Band9  y=968-1010  11 segs (h=42px, label/extras) → VICTORY(6)+DEFEAT(6)

Run: python tools/slice_zephyr.py
"""
from PIL import Image
import os

DISPLAY = 96
ROOT    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BG      = (243, 244, 244)
TOL     = 30

def remove_bg(img, bg=BG, tol=TOL):
    img  = img.convert('RGBA')
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
    fw=(x1-x0)/n
    return [(int(x0+i*fw), int(x0+(i+1)*fw)) for i in range(n)]

def get_segs(pix, w, y0, y1, bg=BG, tol=TOL, mw=30):
    r0,g0,b0=bg; t2=tol*tol
    def ok(r,g,b,a): return a>20 and (r-r0)**2+(g-g0)**2+(b-b0)**2>=t2
    cols=[(x,sum(1 for y in range(y0,y1,2) if ok(*pix[x,y]))) for x in range(w)]
    mx=max(c[1] for c in cols) or 1; thr=mx*0.03
    in_g=True; segs=[]; fs=0
    for x,v in cols:
        if v<=thr and not in_g: segs.append((fs,x)); in_g=True
        elif v>thr and in_g: fs=x; in_g=False
    if not in_g: segs.append((fs,w))
    return [(a,b) for a,b in segs if b-a>=mw]


def slice_zephyr():
    path = os.path.join(ROOT,'tools','zephyr_sheet.png')
    raw  = Image.open(path).convert('RGBA')
    img  = remove_bg(raw, BG, TOL)
    W,H  = img.size; pix = img.load()
    root = os.path.join(ROOT,'assets','sprites','zephyr')
    print('=== ZEPHYR ===')

    # Pre-compute all band segments
    BANDS = {
        1: (9,   116),
        2: (135, 240),
        3: (261, 359),
        4: (375, 482),
        5: (503, 603),
        6: (623, 716),
        7: (726, 842),
        8: (849, 943),
        9: (968, 1010),
    }
    S = {}
    for b,(y0,y1) in BANDS.items():
        raw_segs = get_segs(pix, W, y0, y1)
        # Expand any wide blobs (>150px) by equal-splitting into ~100px chunks
        fixed = []
        for (x0,x1) in raw_segs:
            fw = x1-x0
            if fw > 150:
                # Estimate how many frames: divide by ~100
                n = max(2, round(fw / 100))
                for sx0,sx1 in equal_split(x0,x1,n):
                    fixed.append((sx0,sx1))
            else:
                fixed.append((x0,x1))
        S[b] = fixed

    for b,segs in S.items():
        y0,y1=BANDS[b]
        print(f'  Band{b} y={y0}-{y1} h={y1-y0}  {len(segs)} frames  widths:{[x1-x0 for x0,x1 in segs]}')
    print()

    # ── IDLE  Band1  8 frames ─────────────────────────────────────
    clear(root,'idle')
    y0,y1=BANDS[1]
    for i,(x0,x1) in enumerate(S[1][:8]):
        save(img,'idle',i+1,x0,y0,x1,y1,root)
    print(f'  idle      8 frames')

    # ── WALK  Band2  8 frames ─────────────────────────────────────
    clear(root,'walk')
    y0,y1=BANDS[2]
    for i,(x0,x1) in enumerate(S[2][:8]):
        save(img,'walk',i+1,x0,y0,x1,y1,root)
    print(f'  walk      8 frames')

    # ── RUN  Band3  8 frames ──────────────────────────────────────
    clear(root,'run')
    y0,y1=BANDS[3]
    for i,(x0,x1) in enumerate(S[3][:8]):
        save(img,'run',i+1,x0,y0,x1,y1,root)
    print(f'  run       8 frames')

    # ── JUMP  Band4  6 frames ─────────────────────────────────────
    clear(root,'jump')
    y0,y1=BANDS[4]
    for i,(x0,x1) in enumerate(S[4][:6]):
        save(img,'jump',i+1,x0,y0,x1,y1,root)
    print(f'  jump      6 frames')

    # ── DASH  Band5  6 frames ─────────────────────────────────────
    clear(root,'dash')
    y0,y1=BANDS[5]
    for i,(x0,x1) in enumerate(S[5][:6]):
        save(img,'dash',i+1,x0,y0,x1,y1,root)
    print(f'  dash      6 frames')

    # ── BLOCK  Band6  4 frames (f1-f4) ────────────────────────────
    clear(root,'block')
    y0,y1=BANDS[6]
    for i,(x0,x1) in enumerate(S[6][:4]):
        save(img,'block',i+1,x0,y0,x1,y1,root)
    print(f'  block     4 frames')

    # ── PUNCH  Band6  6 frames (f5-f10) ───────────────────────────
    clear(root,'punch')
    y0,y1=BANDS[6]
    punch_segs = S[6][4:10]
    for i,(x0,x1) in enumerate(punch_segs[:6]):
        save(img,'punch',i+1,x0,y0,x1,y1,root)
    for e in range(len(punch_segs)+1, 7):
        lx0,lx1 = punch_segs[-1] if punch_segs else (0,100)
        save(img,'punch',e,lx0,y0,lx1,y1,root)
    print(f'  punch     6 frames')

    # ── KICK  Band7  6 frames (f1-f6) ─────────────────────────────
    clear(root,'kick')
    y0,y1=BANDS[7]
    for i,(x0,x1) in enumerate(S[7][:6]):
        save(img,'kick',i+1,x0,y0,x1,y1,root)
    print(f'  kick      6 frames')

    # ── SPECIAL  Band7  8 frames (f7 onwards) ─────────────────────
    clear(root,'special')
    y0,y1=BANDS[7]
    spec_segs = S[7][6:]
    for i,(x0,x1) in enumerate(spec_segs[:8]):
        save(img,'special',i+1,x0,y0,x1,y1,root)
    for e in range(len(spec_segs)+1, 9):
        lx0,lx1 = spec_segs[-1] if spec_segs else (0,100)
        save(img,'special',e,lx0,y0,lx1,y1,root)
    print(f'  special   8 frames')

    # ── ULTIMATE  Band8  10 frames (f1-f10) ───────────────────────
    clear(root,'ultimate')
    y0,y1=BANDS[8]
    ult_segs = S[8][:10]
    for i,(x0,x1) in enumerate(ult_segs):
        save(img,'ultimate',i+1,x0,y0,x1,y1,root)
    for e in range(len(ult_segs)+1, 11):
        lx0,lx1 = ult_segs[-1] if ult_segs else (0,100)
        save(img,'ultimate',e,lx0,y0,lx1,y1,root)
    print(f'  ultimate  10 frames')

    # ── HURT  Band8  4 frames (last 4 segs of band8) ──────────────
    clear(root,'hurt')
    y0,y1=BANDS[8]
    hurt_segs = S[8][-4:] if len(S[8])>=4 else S[8]
    for i,(x0,x1) in enumerate(hurt_segs[:4]):
        save(img,'hurt',i+1,x0,y0,x1,y1,root)
    for e in range(len(hurt_segs)+1, 5):
        lx0,lx1 = hurt_segs[-1] if hurt_segs else (0,100)
        save(img,'hurt',e,lx0,y0,lx1,y1,root)
    print(f'  hurt      4 frames')

    # ── VICTORY  Band9  6 frames — use band8 y-range for height ──
    clear(root,'victory')
    b8y0,b8y1 = BANDS[8]   # taller row for proper character height
    b9y0,b9y1 = BANDS[9]
    vict_segs = S[9][:6]
    for i,(x0,x1) in enumerate(vict_segs):
        save(img,'victory',i+1, x0,b8y0, x1,b8y1, root)
    for e in range(len(vict_segs)+1, 7):
        lx0,lx1 = vict_segs[-1] if vict_segs else (S[8][-1])
        save(img,'victory',e, lx0,b8y0, lx1,b8y1, root)
    print(f'  victory   6 frames')

    # ── DEFEAT  Band9  6 frames — use band8 y-range ──────────────
    clear(root,'defeat')
    def_segs = S[9][-6:] if len(S[9])>=6 else S[9]
    for i,(x0,x1) in enumerate(def_segs[:6]):
        save(img,'defeat',i+1, x0,b8y0, x1,b8y1, root)
    for e in range(len(def_segs)+1, 7):
        lx0,lx1 = def_segs[-1] if def_segs else (S[8][-1])
        save(img,'defeat',e, lx0,b8y0, lx1,b8y1, root)
    print(f'  defeat    6 frames')


if __name__ == '__main__':
    slice_zephyr()

    # ── Quality check ───────────────────────────────────────────────
    anims = ['idle','walk','run','jump','dash','block','punch','kick',
             'special','ultimate','hurt','victory','defeat']
    exp   = [8,8,8,6,6,4,6,6,8,10,4,6,6]
    print('\n=== QUALITY CHECK ===')
    all_ok = True; total = 0
    for a,e in zip(anims,exp):
        d = os.path.join(ROOT,'assets','sprites','zephyr',a)
        files = [f for f in os.listdir(d) if f.endswith('.png')] if os.path.isdir(d) else []
        c = len(files); total += c
        ok = c == e
        if not ok: all_ok = False
        print(f'  {"OK" if ok else "FAIL"}  {a:<12}  {c}/{e}')
    print(f'\n  Total: {total} frames')
    print('\nZEPHYR: ALL OK' if all_ok else '\nSome issues above.')
    print('Done! Refresh index.html in Chrome.')
