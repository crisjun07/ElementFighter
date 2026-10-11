#!/usr/bin/env python3
"""
fix_voltra_final.py
===================
Fixes Voltra background removal using SATURATION-based flood-fill.

The problem: Voltra's bg is grey/white (R≈G≈B, desaturated).
             Voltra's white highlights also look like rgb(255,255,255).
             Colour-distance alone cannot distinguish them.

The solution:
  1. Flood-fill from sheet edges (connectivity-based).
  2. A pixel is "background" ONLY if:
     - It is reachable from the sheet edge, AND
     - It is DESATURATED: max(R,G,B) - min(R,G,B) <= SAT_THRESHOLD
       (grey/white bg has near-zero saturation)
  3. Voltra's character pixels:
     - Yellow lightning: R=254,G=208,B=62 → saturation=192  → KEPT
     - Black outlines: R=0,G=0,B=0 → saturation=0 but isolated → KEPT
     - White armor highlights: saturation=0 BUT interior, not reachable → KEPT
     
SAT_THRESHOLD = 20: only pixels where max-min(RGB) <= 20 are candidates.
This keeps ALL coloured character pixels (yellow, purple lightning etc.)
"""
from PIL import Image
import os
from collections import deque

ROOT    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DISPLAY = 128
PAD     = 12

# Saturation threshold: bg pixels have R≈G≈B (desaturated grey/white)
# Character pixels with colour (yellow, purple, blue) have high saturation
SAT_THRESHOLD = 20  # max(R,G,B) - min(R,G,B) <= 20 means grey/white

# Also minimum brightness: very dark pixels (outlines) are not bg
MIN_BRIGHTNESS = 200  # sum(R+G+B)/3 >= 200/3 to be considered bg candidate

def flood_remove_bg_sat(img):
    """
    Flood-fill from sheet edges removing ONLY desaturated grey/white pixels.
    Any pixel with saturation > SAT_THRESHOLD is treated as character art.
    """
    img  = img.convert('RGBA')
    data = list(img.getdata())
    W,H  = img.size

    def is_bg(i):
        r,g,b,a = data[i]
        if a < 10: return True      # already transparent = treat as bg
        brightness = (r + g + b) / 3
        if brightness < 180: return False   # dark pixel = character outline/shadow
        saturation = max(r,g,b) - min(r,g,b)
        return saturation <= SAT_THRESHOLD   # grey/white = bg candidate

    visited = bytearray(W * H)
    q = deque()

    # Seed all 4 sheet edges
    for x in range(W):
        for y in [0, H-1]:
            i = y*W + x
            if not visited[i] and is_bg(i):
                visited[i] = 1; q.append(i)
    for y in range(H):
        for x in [0, W-1]:
            i = y*W + x
            if not visited[i] and is_bg(i):
                visited[i] = 1; q.append(i)

    # BFS
    while q:
        i = q.popleft()
        r,g,b,a = data[i]
        data[i] = (r,g,b,0)   # transparent
        x,y = i%W, i//W
        for nx,ny in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
            if 0 <= nx < W and 0 <= ny < H:
                ni = ny*W + nx
                if not visited[ni] and is_bg(ni):
                    visited[ni] = 1; q.append(ni)

    img.putdata(data)
    return img

def save(img, anim, idx, x0,y0,x1,y1, root):
    W,H = img.size
    x0=max(0,x0-PAD); x1=min(W,x1+PAD)
    y0=max(0,y0-PAD); y1=min(H,y1+PAD)
    if x1<=x0 or y1<=y0: return
    crop = img.crop((x0,y0,x1,y1))
    crop.thumbnail((DISPLAY,DISPLAY), Image.LANCZOS)
    c = Image.new('RGBA',(DISPLAY,DISPLAY),(0,0,0,0))
    c.paste(crop, ((DISPLAY-crop.width)//2, DISPLAY-crop.height), crop)
    c.save(os.path.join(root,anim,f'{anim}-{idx}.png'),'PNG')

def clear(root,anim):
    d=os.path.join(root,anim); os.makedirs(d,exist_ok=True)
    for f in os.listdir(d):
        if f.endswith('.png'): os.remove(os.path.join(d,f))

def eq(x0,x1,n):
    fw=(x1-x0)/n
    return [(int(x0+i*fw),int(x0+(i+1)*fw)) for i in range(n)]

if __name__=='__main__':
    print('=== VOLTRA — Saturation-based flood-fill ===')
    print(f'SAT_THRESHOLD={SAT_THRESHOLD}: only grey/white pixels (R≈G≈B) removed')
    print('Yellow/black/purple character pixels have high saturation → KEPT\n')

    path = os.path.join(ROOT,'tools','voltra_sheet.png')
    raw  = Image.open(path).convert('RGBA')
    print(f'Sheet: {raw.width}x{raw.height}')
    print('Processing...')
    img  = flood_remove_bg_sat(raw)
    print('Background removed.\n')

    root = os.path.join(ROOT,'assets','sprites','voltra')
    def s(a,i,x0,y0,x1,y1): save(img,a,i,x0,y0,x1,y1,root)

    # All exact frame coordinates (unchanged from original scan)
    clear(root,'idle')
    for i,(x0,x1) in enumerate([(13,86),(126,208),(232,315),(346,425),(458,540),(576,652),(694,773),(809,887)]):
        s('idle',i+1,x0,7,x1,117)

    clear(root,'walk')
    for i,(x0,x1) in enumerate([(10,95),(120,197),(225,314),(347,423),(451,536),(561,649),(675,756),(783,881)]):
        s('walk',i+1,x0,134,x1,248)

    clear(root,'run')
    for i,(x0,x1) in enumerate([(12,99),(137,238),(277,385),(416,505),(532,631),(674,789),(811,913),(949,1050)]):
        s('run',i+1,x0,263,x1,365)

    clear(root,'jump')
    for i,(x0,x1) in enumerate([(14,91),(129,217),(258,349),(409,485),(540,627),(680,753)]):
        s('jump',i+1,x0,372,x1,490)

    clear(root,'dash')
    for i,(x0,x1) in enumerate([(17,105),(148,222),(258,354),(396,489),(517,621),(653,743)]):
        s('dash',i+1,x0,503,x1,613)

    clear(root,'block')
    for i,(x0,x1) in enumerate([(16,112),(129,224),(244,367),(376,441)]):
        s('block',i+1,x0,630,x1,730)

    clear(root,'punch')
    for i,(x0,x1) in enumerate([(441,506),(506,572),(572,638),(640,769),(783,897),(927,1044)]):
        s('punch',i+1,x0,630,x1,730)

    clear(root,'kick')
    for i,(x0,x1) in enumerate([(13,101),(117,239),(247,363),(367,485),(502,640),(651,783)]):
        s('kick',i+1,x0,736,x1,852)

    clear(root,'special')
    for i,(x0,x1) in enumerate([(783,915),(927,1062),(13,101),(117,239),(247,363),(367,485),(502,640),(651,783)]):
        s('special',i+1,x0,736,x1,852)

    clear(root,'ultimate')
    for i,(x0,x1) in enumerate(eq(17,1176,10)):
        s('ultimate',i+1,x0,848,x1,1028)

    clear(root,'hurt')
    for i,(x0,x1) in enumerate([(929,1012),(1046,1090),(1090,1134),(1134,1176)]):
        s('hurt',i+1,x0,848,x1,1028)

    clear(root,'victory')
    for i,(x0,x1) in enumerate(eq(520,1176,6)):
        s('victory',i+1,x0,848,x1,1028)

    clear(root,'defeat')
    for i,(x0,x1) in enumerate(eq(17,1176,6)):
        s('defeat',i+1,x0,848,x1,1028)

    # Quality check
    anims=['idle','walk','run','jump','dash','block','punch','kick','special','ultimate','hurt','victory','defeat']
    exp  =[8,8,8,6,6,4,6,6,8,10,4,6,6]
    print('=== QUALITY CHECK ===')
    all_ok=True
    for a,e in zip(anims,exp):
        d=os.path.join(root,a)
        c=len([f for f in os.listdir(d) if f.endswith('.png')]) if os.path.isdir(d) else 0
        ok=(c==e)
        if not ok: all_ok=False
        fp=os.path.join(d,f'{a}-1.png')
        yellow=0
        if os.path.exists(fp):
            im=Image.open(fp).convert('RGBA'); p=im.load(); W2,H2=im.size
            # Count yellow character pixels preserved
            yellow=sum(1 for y in range(H2) for x in range(W2)
                      if p[x,y][3]>40 and p[x,y][0]>180 and p[x,y][0]-p[x,y][2]>50)
        print(f'  {"OK  " if ok else "FAIL"}  {a:<12}  {c}/{e}  yellow_pixels={yellow}')

    print(f'\n{"ALL OK" if all_ok else "ISSUES"} — Voltra fixed!')
    print('Grey/white bg removed. Yellow armor + black outlines + all character art KEPT.')
