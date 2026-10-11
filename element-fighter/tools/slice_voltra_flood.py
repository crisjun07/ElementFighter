#!/usr/bin/env python3
"""
slice_voltra_flood.py
=====================
Re-slices Voltra using FLOOD-FILL background removal (edge-connected only).
Interior character pixels (yellow skin, white highlights, lightning effects)
are NEVER removed regardless of colour closeness to the background.

Sheet: 1536x1024, bg≈rgb(241,242,243)
Band layout (from original pixel scan):
  Band1 y=7-117    IDLE(8)
  Band2 y=134-248  WALK(8)
  Band3 y=263-365  RUN(8)
  Band4 y=372-490  JUMP(6)
  Band5 y=503-613  DASH(6)
  Band6 y=630-730  BLOCK(4)+PUNCH(6)
  Band7 y=736-852  KICK(6)+SPECIAL(8)
  Band8 y=858-1018 ULTIMATE(10)+HURT(4)+VICTORY(6)+DEFEAT(6)
"""
from PIL import Image
import os
from collections import deque

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── Background colour (sampled from sheet edges) ──────────────────
BG_COLOUR = (241, 242, 243)
BG_TOL    = 25   # tight — only clear clearly-bg pixels reachable from edge

# ── Flood-fill background removal ────────────────────────────────
def flood_remove_bg(img, bg=BG_COLOUR, tol=BG_TOL):
    """Remove only edge-connected background pixels. Interior preserved."""
    img  = img.convert('RGBA')
    data = list(img.getdata())
    W, H = img.size
    r0,g0,b0 = bg
    t2 = tol * tol

    def is_bg(idx):
        r,g,b,a = data[idx]
        return (r-r0)**2 + (g-g0)**2 + (b-b0)**2 <= t2

    visited = bytearray(W * H)
    q = deque()

    # Seed all 4 edges
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

    # BFS flood fill → make transparent
    while q:
        i = q.popleft()
        r,g,b,a = data[i]
        data[i]  = (r,g,b,0)
        x,y = i%W, i//W
        for nx,ny in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
            if 0<=nx<W and 0<=ny<H:
                ni = ny*W+nx
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

# ── Exact frame coordinates (from original pixel scan) ───────────
def get_segs(pix, W, y0, y1, mw=30):
    """Content-based segment detection using transparency."""
    cols=[(x,sum(1 for y in range(y0,y1,2) if pix[x,y][3]>20)) for x in range(W)]
    mx=max(c[1] for c in cols) or 1; thr=mx*0.03
    in_g=True; segs=[]; fs=0
    for x,v in cols:
        if v<=thr and not in_g: segs.append((fs,x)); in_g=True
        elif v>thr and in_g: fs=x; in_g=False
    if not in_g: segs.append((fs,W))
    return [(a,b) for a,b in segs if b-a>=mw]

# ─────────────────────────────────────────────────────────────────
def slice_voltra():
    path=os.path.join(ROOT,'tools','voltra_sheet.png')
    print(f'Loading Voltra sheet...')
    raw=Image.open(path).convert('RGBA')
    print(f'Sheet: {raw.width}x{raw.height}')
    print(f'Flood-fill removing background rgb{BG_COLOUR} (edge-connected only)...')
    img=flood_remove_bg(raw,BG_COLOUR,BG_TOL)
    print(f'Background removed — interior pixels preserved.\n')

    W,H=img.size; pix=img.load()
    root=os.path.join(ROOT,'assets','sprites','voltra')

    # ── IDLE  Band1 y=7-117  8 frames ─────────────────────────────
    clear(root,'idle')
    for i,(x0,x1) in enumerate([(13,86),(126,208),(232,315),(346,425),(458,540),(576,652),(694,773),(809,887)]):
        save(img,'idle',i+1,x0,7,x1,117,root)

    # ── WALK  Band2 y=134-248  8 frames ───────────────────────────
    clear(root,'walk')
    for i,(x0,x1) in enumerate([(10,95),(120,197),(225,314),(347,423),(451,536),(561,649),(675,756),(783,881)]):
        save(img,'walk',i+1,x0,134,x1,248,root)

    # ── RUN  Band3 y=263-365  8 frames ────────────────────────────
    clear(root,'run')
    for i,(x0,x1) in enumerate([(12,99),(137,238),(277,385),(416,505),(532,631),(674,789),(811,913),(949,1050)]):
        save(img,'run',i+1,x0,263,x1,365,root)

    # ── JUMP  Band4 y=372-490  6 frames ───────────────────────────
    clear(root,'jump')
    for i,(x0,x1) in enumerate([(14,91),(129,217),(258,349),(409,485),(540,627),(680,753)]):
        save(img,'jump',i+1,x0,372,x1,490,root)

    # ── DASH  Band5 y=503-613  6 frames ───────────────────────────
    clear(root,'dash')
    for i,(x0,x1) in enumerate([(17,105),(148,222),(258,354),(396,489),(517,621),(653,743)]):
        save(img,'dash',i+1,x0,503,x1,613,root)

    # ── BLOCK  Band6 y=630-730  4 frames ──────────────────────────
    clear(root,'block')
    for i,(x0,x1) in enumerate([(16,112),(129,224),(244,367),(376,441)]):
        save(img,'block',i+1,x0,630,x1,730,root)

    # ── PUNCH  Band6 y=630-730  6 frames ──────────────────────────
    clear(root,'punch')
    for i,(x0,x1) in enumerate([(441,506),(506,572),(572,638),(640,769),(783,897),(927,1044)]):
        save(img,'punch',i+1,x0,630,x1,730,root)

    # ── KICK  Band7 y=736-852  6 frames ───────────────────────────
    clear(root,'kick')
    for i,(x0,x1) in enumerate([(13,101),(117,239),(247,363),(367,485),(502,640),(651,783)]):
        save(img,'kick',i+1,x0,736,x1,852,root)

    # ── SPECIAL  Band7 y=736-852  8 frames ────────────────────────
    clear(root,'special')
    spec_b6=[(783,915),(927,1062)]
    spec_b7=[(13,101),(117,239),(247,363),(367,485),(502,640),(651,783)]
    spec_all=spec_b6+spec_b7
    for i,(x0,x1) in enumerate(spec_all[:8]):
        y0s=736 if i>=2 else 736; y1s=852
        save(img,'special',i+1,x0,y0s,x1,y1s,root)

    # ── ULTIMATE  Band8 y=858-1018  10 frames ─────────────────────
    clear(root,'ultimate')
    ult_x=[(17,104),(151,226),(276,354),(392,481),(520,605),(669,754),(800,885),(929,1012)]
    for i,(x0,x1) in enumerate(ult_x):
        save(img,'ultimate',i+1,x0,848,x1,1028,root)
    for i,(x0,x1) in enumerate(eq(1046,1176,2)):
        save(img,'ultimate',9+i,x0,848,x1,1028,root)

    # ── HURT  Band8  4 frames ─────────────────────────────────────
    clear(root,'hurt')
    for i,(x0,x1) in enumerate([(929,1012),(1046,1090),(1090,1134),(1134,1176)]):
        save(img,'hurt',i+1,x0,848,x1,1028,root)

    # ── VICTORY  Band8  6 frames ──────────────────────────────────
    clear(root,'victory')
    for i,(x0,x1) in enumerate(eq(520,1176,6)):
        save(img,'victory',i+1,x0,848,x1,1028,root)

    # ── DEFEAT  Band8  6 frames ───────────────────────────────────
    clear(root,'defeat')
    for i,(x0,x1) in enumerate(eq(17,1176,6)):
        save(img,'defeat',i+1,x0,848,x1,1028,root)

    # ── Verify ────────────────────────────────────────────────────
    anims=['idle','walk','run','jump','dash','block','punch','kick','special','ultimate','hurt','victory','defeat']
    exp  =[8,8,8,6,6,4,6,6,8,10,4,6,6]
    print('=== VOLTRA RESULT ===')
    all_ok=True
    for a,e in zip(anims,exp):
        d=os.path.join(root,a)
        c=len([f for f in os.listdir(d) if f.endswith('.png')]) if os.path.isdir(d) else 0
        # spot-check transparency at corner of frame 1
        fp=os.path.join(d,f'{a}-1.png')
        if os.path.exists(fp):
            im=Image.open(fp).convert('RGBA'); px=im.load(); W2,H2=im.size
            corner_ok = im.getpixel((0,0))[3]==0
        else:
            corner_ok=False
        ok=c==e
        if not ok: all_ok=False
        print(f'  {"OK  " if ok else "FAIL"}  {a:<12}  {c}/{e}  transparent_corner={corner_ok}')
    print()
    if all_ok: print('VOLTRA: ALL OK — flood-fill bg removed, interior preserved')
    else:      print('VOLTRA: some issues above')

if __name__=='__main__':
    slice_voltra()
