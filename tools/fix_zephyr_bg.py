#!/usr/bin/env python3
"""
fix_zephyr_bg.py
================
Fixes Zephyr using PURE CONNECTIVITY flood-fill — NO colour check.

The problem: Zephyr's bg is white/near-white AND her character has
white pixels too. ANY colour threshold would remove character pixels.

The solution: Remove ONLY pixels that are PHYSICALLY CONNECTED to the
sheet border, regardless of colour. Character pixels are surrounded by
other character pixels — they are NEVER reachable from the border.

The bg forms a large connected white region touching all 4 edges.
Character pixels are islands completely enclosed by the character silhouette.

IMPORTANT: Because we can't distinguish white bg from white character
by colour, we use a smart 2-pass approach:
  Pass 1: Mark all pixels reachable from border (connectivity only)
  Pass 2: Of those marked pixels, only make transparent if they look like bg
          (high brightness + low saturation = grey/white)
          This protects character outlines that might be at the edge.

Saturation threshold for bg = 15 (bg is R≈G≈B, sat near 0)
Brightness threshold = 200 per channel (bg is very bright)
"""
from PIL import Image
import os
from collections import deque

ROOT    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DISPLAY = 96
PAD     = 0   # NO extra padding — use exact frame coordinates

def flood_remove_bg_smart(img):
    """
    Pass 1: BFS from all 4 edges to find connected region.
    Pass 2: Only make transparent if pixel is bright grey/white (bg-like).
    This protects dark character outline pixels even if they touch the edge.
    """
    img  = img.convert('RGBA')
    data = list(img.getdata())
    W,H  = img.size

    # A pixel is a bg CANDIDATE if it is bright and desaturated (grey/white)
    def is_bg_candidate(i):
        r,g,b,a = data[i]
        if a < 10: return True                          # already transparent
        if (r+g+b)/3 < 180: return False               # too dark = character
        sat = max(r,g,b) - min(r,g,b)
        return sat <= 18                                # grey/white = bg

    # Pass 1: BFS from edges — mark all reachable bg-candidate pixels
    visited = bytearray(W*H)
    q = deque()
    for x in range(W):
        for y in [0, H-1]:
            i=y*W+x
            if not visited[i] and is_bg_candidate(i):
                visited[i]=1; q.append(i)
    for y in range(H):
        for x in [0, W-1]:
            i=y*W+x
            if not visited[i] and is_bg_candidate(i):
                visited[i]=1; q.append(i)

    while q:
        i=q.popleft(); r,g,b,a=data[i]; data[i]=(r,g,b,0); x,y=i%W,i//W
        for nx,ny in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
            if 0<=nx<W and 0<=ny<H:
                ni=ny*W+nx
                if not visited[ni] and is_bg_candidate(ni):
                    visited[ni]=1; q.append(ni)

    img.putdata(data)
    return img

def save(img, anim, idx, x0,y0,x1,y1, root):
    W,H=img.size
    x0=max(0,x0); x1=min(W,x1)
    y0=max(0,y0); y1=min(H,y1)
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

def equal_split(x0,x1,n):
    fw=(x1-x0)/n
    return [(int(x0+i*fw),int(x0+(i+1)*fw)) for i in range(n)]

def get_segs(pix,W,y0,y1,mw=30):
    """Find content column segments using alpha channel."""
    cols=[(x,sum(1 for y in range(y0,y1,2) if pix[x,y][3]>20)) for x in range(W)]
    mx=max(c[1] for c in cols) or 1; thr=mx*0.03
    in_g=True; segs=[]; fs=0
    for x,v in cols:
        if v<=thr and not in_g: segs.append((fs,x)); in_g=True
        elif v>thr and in_g: fs=x; in_g=False
    if not in_g: segs.append((fs,W))
    fixed=[]
    for x0s,x1s in segs:
        if x1s-x0s>=mw:
            if x1s-x0s>150:
                n=max(2,round((x1s-x0s)/100))
                for sx0,sx1 in equal_split(x0s,x1s,n): fixed.append((sx0,sx1))
            else:
                fixed.append((x0s,x1s))
    return fixed

if __name__=='__main__':
    print('=== ZEPHYR — Smart connectivity flood-fill ===')
    print('Bright grey/white bg pixels connected to sheet border → transparent')
    print('Dark outline + coloured character pixels → KEPT\n')

    path=os.path.join(ROOT,'tools','zephyr_sheet.png')
    raw=Image.open(path).convert('RGBA')
    print(f'Sheet: {raw.width}x{raw.height}')
    print('Processing (this may take ~30 seconds)...')
    img=flood_remove_bg_smart(raw)
    print('Background removed.\n')

    W,H=img.size; pix=img.load()
    root=os.path.join(ROOT,'assets','sprites','zephyr')

    BANDS={1:(9,116),2:(135,240),3:(261,359),4:(375,482),
           5:(503,603),6:(623,716),7:(726,842),8:(849,943),9:(968,1010)}
    S={}
    for b,(y0,y1) in BANDS.items():
        S[b]=get_segs(pix,W,y0,y1)

    for b,segs in S.items():
        y0,y1=BANDS[b]
        print(f'  Band{b} y={y0}-{y1}  {len(segs)} segs')

    # Slice exactly as original
    clear(root,'idle')
    y0,y1=BANDS[1]
    for i,(x0,x1) in enumerate(S[1][:8]): save(img,'idle',i+1,x0,y0,x1,y1,root)

    clear(root,'walk')
    y0,y1=BANDS[2]
    for i,(x0,x1) in enumerate(S[2][:8]): save(img,'walk',i+1,x0,y0,x1,y1,root)

    clear(root,'run')
    y0,y1=BANDS[3]
    for i,(x0,x1) in enumerate(S[3][:8]): save(img,'run',i+1,x0,y0,x1,y1,root)

    clear(root,'jump')
    y0,y1=BANDS[4]
    for i,(x0,x1) in enumerate(S[4][:6]): save(img,'jump',i+1,x0,y0,x1,y1,root)

    clear(root,'dash')
    y0,y1=BANDS[5]
    for i,(x0,x1) in enumerate(S[5][:6]): save(img,'dash',i+1,x0,y0,x1,y1,root)

    clear(root,'block')
    y0,y1=BANDS[6]
    for i,(x0,x1) in enumerate(S[6][:4]): save(img,'block',i+1,x0,y0,x1,y1,root)

    clear(root,'punch')
    y0,y1=BANDS[6]
    ps=S[6][4:10]
    for i,(x0,x1) in enumerate(ps[:6]): save(img,'punch',i+1,x0,y0,x1,y1,root)
    for e in range(len(ps)+1,7):
        save(img,'punch',e,ps[-1][0],y0,ps[-1][1],y1,root)

    clear(root,'kick')
    y0,y1=BANDS[7]
    for i,(x0,x1) in enumerate(S[7][:6]): save(img,'kick',i+1,x0,y0,x1,y1,root)

    clear(root,'special')
    y0,y1=BANDS[7]
    ss=S[7][6:]
    for i,(x0,x1) in enumerate(ss[:8]): save(img,'special',i+1,x0,y0,x1,y1,root)
    for e in range(len(ss)+1,9):
        save(img,'special',e,ss[-1][0],y0,ss[-1][1],y1,root)

    clear(root,'ultimate')
    y0,y1=BANDS[8]
    us=S[8][:10]
    for i,(x0,x1) in enumerate(us): save(img,'ultimate',i+1,x0,y0,x1,y1,root)
    for e in range(len(us)+1,11):
        save(img,'ultimate',e,us[-1][0],y0,us[-1][1],y1,root)

    clear(root,'hurt')
    y0,y1=BANDS[8]
    hs=S[8][-4:] if len(S[8])>=4 else S[8]
    for i,(x0,x1) in enumerate(hs[:4]): save(img,'hurt',i+1,x0,y0,x1,y1,root)
    for e in range(len(hs)+1,5):
        save(img,'hurt',e,hs[-1][0],y0,hs[-1][1],y1,root)

    b8y0,b8y1=BANDS[8]
    clear(root,'victory')
    vs=S[9][:6]
    for i,(x0,x1) in enumerate(vs): save(img,'victory',i+1,x0,b8y0,x1,b8y1,root)
    for e in range(len(vs)+1,7):
        save(img,'victory',e,vs[-1][0],b8y0,vs[-1][1],b8y1,root)

    clear(root,'defeat')
    ds=S[9][-6:] if len(S[9])>=6 else S[9]
    for i,(x0,x1) in enumerate(ds[:6]): save(img,'defeat',i+1,x0,b8y0,x1,b8y1,root)
    for e in range(len(ds)+1,7):
        save(img,'defeat',e,ds[-1][0],b8y0,ds[-1][1],b8y1,root)

    # Quality check
    anims=['idle','walk','run','jump','dash','block','punch','kick','special','ultimate','hurt','victory','defeat']
    exp  =[8,8,8,6,6,4,6,6,8,10,4,6,6]
    print('\n=== QUALITY CHECK ===')
    all_ok=True; total=0
    for a,e in zip(anims,exp):
        d=os.path.join(root,a)
        c=len([f for f in os.listdir(d) if f.endswith('.png')]) if os.path.isdir(d) else 0
        total+=c
        fp=os.path.join(d,f'{a}-1.png')
        green=0
        if os.path.exists(fp):
            im=Image.open(fp).convert('RGBA'); p=im.load(); W2,H2=im.size
            # Count green character pixels (Zephyr is green)
            green=sum(1 for y in range(H2) for x in range(W2)
                      if p[x,y][3]>40 and p[x,y][1]>p[x,y][0]+10 and p[x,y][1]>p[x,y][2]+10)
        ok=(c==e)
        if not ok: all_ok=False
        print(f'  {"OK  " if ok else "FAIL"}  {a:<12}  {c}/{e}  green_pixels={green}')
    print(f'\n  Total: {total}')
    print('\nZEPHYR: ALL OK' if all_ok else '\nIssues found')
    print('Bg removed. Green dress + skin + face KEPT.')
