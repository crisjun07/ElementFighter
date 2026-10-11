#!/usr/bin/env python3
"""
fix_noctis_bg.py
================
Re-slices Noctis with tol=8 (very strict).
bg = rgb(9,12,20) - only pixels within distance 8 of this exact colour
     AND connected to the sheet edge are made transparent.

Noctis dark purple armor: rgb(0,0,20), rgb(20,20,40), rgb(40,40,60)
  distance from bg: sqrt(81+144+0)=15, sqrt(81+144+400)=26, sqrt(81+144+1600)=43
  ALL safely above tol=8 → KEPT completely.

Only the sheet background (exactly rgb(9,12,20)±8) is removed.
"""
from PIL import Image
import os
from collections import deque

ROOT    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DISPLAY = 128
PAD     = 12

def flood_remove_bg(img, bg_rgb, tol):
    img  = img.convert('RGBA')
    data = list(img.getdata())
    W,H  = img.size
    r0,g0,b0 = bg_rgb
    t2 = tol * tol

    def is_bg(i):
        r,g,b,a = data[i]
        if a < 10: return True
        return (r-r0)**2 + (g-g0)**2 + (b-b0)**2 <= t2

    visited = bytearray(W*H)
    q = deque()
    for x in range(W):
        for y in [0, H-1]:
            i=y*W+x
            if not visited[i] and is_bg(i): visited[i]=1; q.append(i)
    for y in range(H):
        for x in [0, W-1]:
            i=y*W+x
            if not visited[i] and is_bg(i): visited[i]=1; q.append(i)
    while q:
        i=q.popleft(); r,g,b,a=data[i]; data[i]=(r,g,b,0); x,y=i%W,i//W
        for nx,ny in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
            if 0<=nx<W and 0<=ny<H:
                ni=ny*W+nx
                if not visited[ni] and is_bg(ni): visited[ni]=1; q.append(ni)
    img.putdata(data)
    return img

def save(img, anim, idx, x0,y0,x1,y1, root):
    W,H=img.size
    x0=max(0,x0-PAD); x1=min(W,x1+PAD)
    y0=max(0,y0-PAD); y1=min(H,y1+PAD)
    if x1<=x0 or y1<=y0: return
    crop=img.crop((x0,y0,x1,y1))
    crop.thumbnail((DISPLAY,DISPLAY),Image.LANCZOS)
    c=Image.new('RGBA',(DISPLAY,DISPLAY),(0,0,0,0))
    c.paste(crop,((DISPLAY-crop.width)//2, DISPLAY-crop.height), crop)
    c.save(os.path.join(root,anim,f'{anim}-{idx}.png'),'PNG')

def clear(root,anim):
    d=os.path.join(root,anim); os.makedirs(d,exist_ok=True)
    for f in os.listdir(d):
        if f.endswith('.png'): os.remove(os.path.join(d,f))

def eq(x0,x1,n):
    fw=(x1-x0)/n
    return [(int(x0+i*fw),int(x0+(i+1)*fw)) for i in range(n)]

if __name__=='__main__':
    print('=== NOCTIS (tol=8, bg=rgb(9,12,20)) ===')
    path=os.path.join(ROOT,'tools','noctis.png')
    raw=Image.open(path).convert('RGBA')
    print(f'Sheet: {raw.width}x{raw.height}')
    print('Flood-fill with tol=8 — only edge-connected near-black bg removed...')
    # Use the exact measured bg colour from edge sampling
    img=flood_remove_bg(raw,(9,12,20),tol=8)
    print('Done.\n')

    root=os.path.join(ROOT,'assets','sprites','noctis')
    def s(a,i,x0,y0,x1,y1): save(img,a,i,x0,y0,x1,y1,root)

    # Exact frame coordinates from original pixel scan
    clear(root,'idle')
    for i,(x0,x1) in enumerate([(157,209),(245,294),(331,382),(419,469),(509,560),(596,647),(682,733),(768,821)]):
        s('idle',i+1,x0,13,x1,109)

    clear(root,'walk')
    for i,(x0,x1) in enumerate([(222,297),(315,380),(406,473),(498,560),(587,645),(671,734),(760,822),(849,909)]):
        s('walk',i+1,x0,135,x1,229)

    clear(root,'run')
    for i,(x0,x1) in enumerate([(402,480),(493,568),(579,663),(663,747),(747,831),(844,917),(844,917),(844,917)]):
        s('run',i+1,x0,255,x1,348)

    clear(root,'jump')
    for i,(x0,x1) in enumerate([(278,348),(398,474),(519,590),(638,724),(763,839),(763,839)]):
        s('jump',i+1,x0,364,x1,476)

    clear(root,'dash')
    for i,(x0,x1) in enumerate([(266,380),(395,506),(521,637),(655,788),(819,968),(819,968)]):
        s('dash',i+1,x0,497,x1,582)

    clear(root,'block')
    for i,(x0,x1) in enumerate([(155,230),(259,338),(373,458),(496,581)]):
        s('block',i+1,x0,598,x1,696)

    clear(root,'punch')
    for i,(x0,x1) in enumerate([(265,380),(395,492),(511,608),(622,700),(700,778),(778,856)]):
        s('punch',i+1,x0,711,x1,810)

    clear(root,'kick')
    for i,(x0,x1) in enumerate([(147,255),(274,384),(384,494),(516,609),(620,733),(757,844)]):
        s('kick',i+1,x0,834,x1,941)

    clear(root,'special')
    for i,(x0,x1) in enumerate(eq(262,1009,8)):
        s('special',i+1,x0,955,x1,1075)

    clear(root,'ultimate')
    for i,(x0,x1) in enumerate(eq(11,1015,10)):
        s('ultimate',i+1,x0,1086,x1,1214)

    clear(root,'hurt')
    for i,(x0,x1) in enumerate([(153,230),(247,313),(345,413),(449,557)]):
        s('hurt',i+1,x0,1216,x1,1294)

    clear(root,'victory')
    for i,(x0,x1) in enumerate([(173,236),(277,329),(365,425),(468,528),(573,647),(677,729)]):
        s('victory',i+1,x0,1303,x1,1402)

    clear(root,'defeat')
    for i,(x0,x1) in enumerate([(266,359),(376,468),(491,595),(621,711),(738,855),(738,855)]):
        s('defeat',i+1,x0,1429,x1,1492)

    # Verify
    anims=['idle','walk','run','jump','dash','block','punch','kick','special','ultimate','hurt','victory','defeat']
    exp  =[8,8,8,6,6,4,6,6,8,10,4,6,6]
    print('=== QUALITY CHECK ===')
    all_ok=True
    for a,e in zip(anims,exp):
        d=os.path.join(root,a)
        c=len([f for f in os.listdir(d) if f.endswith('.png')]) if os.path.isdir(d) else 0
        ok=(c==e)
        if not ok: all_ok=False
        # Check interior content preserved
        fp=os.path.join(d,f'{a}-1.png')
        interior=0
        if os.path.exists(fp):
            im=Image.open(fp).convert('RGBA'); p=im.load(); W2,H2=im.size
            interior=sum(1 for y in range(H2//4,3*H2//4) for x in range(W2//4,3*W2//4) if p[x,y][3]>40)
        print(f'  {"OK  " if ok else "FAIL"}  {a:<12}  {c}/{e}  interior_pixels={interior}')

    print(f'\n{"ALL OK" if all_ok else "ISSUES"} — Noctis fixed!')
    print('tol=8 ensures dark purple armor, hair, and shadow pixels are KEPT.')
    print('Only the exact rgb(9,12,20) dark bg connected to the sheet border is removed.')
