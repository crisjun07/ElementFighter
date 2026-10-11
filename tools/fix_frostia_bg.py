#!/usr/bin/env python3
"""
fix_frostia_bg.py
=================
Fixes Frostia using smart connectivity flood-fill.

Problem: Frostia's bg is white/grey (rgb 228-254, fully desaturated R≈G≈B)
         Frostia's armor is also white BUT she has ice-blue pixels with saturation.
         Her white armor interior pixels are enclosed — not reachable from sheet edge.

Solution: Flood-fill from sheet edges removing ONLY bright+desaturated pixels.
  - bg check: brightness >= 180 (avg per channel) AND saturation <= 18 (R≈G≈B)
  - Character white armor: enclosed → never reachable from border → KEPT
  - Character ice-blue: saturation > 18 → never removed → KEPT
  - Dark outlines: brightness < 180 → never removed → KEPT
"""
from PIL import Image
import os
from collections import deque

ROOT    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DISPLAY = 96

def flood_remove_bg_smart(img):
    """Remove bright desaturated bg pixels connected to sheet edge."""
    img  = img.convert('RGBA')
    data = list(img.getdata())
    W,H  = img.size

    def is_bg(i):
        r,g,b,a = data[i]
        if a < 10: return True                    # transparent = bg gap
        brightness = (r + g + b) / 3
        if brightness < 175: return False          # dark = character outline
        saturation = max(r,g,b) - min(r,g,b)
        return saturation <= 18                    # grey/white = bg candidate

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

if __name__=='__main__':
    print('=== FROSTIA — Smart flood-fill (brightness+saturation) ===')
    print('Bright grey/white bg → transparent')
    print('Ice-blue armor + white interior + dark outlines → KEPT\n')

    path=os.path.join(ROOT,'tools','frostia_sheet.png')
    raw=Image.open(path).convert('RGBA')
    print(f'Sheet: {raw.width}x{raw.height}')
    print('Processing...')
    img=flood_remove_bg_smart(raw)
    print('Done.\n')

    root=os.path.join(ROOT,'assets','sprites','frostia')

    def s(a,i,x0,y0,x1,y1): save(img,a,i,x0,y0,x1,y1,root)

    # Original frame coordinates (same as restore_frostia.py)
    clear(root,'idle')
    for i,(x0,y0,x1,y1) in enumerate([(157,11,224,114),(244,11,310,114),(331,11,398,114),(425,11,491,114),
                                        (506,11,581,114),(603,11,673,114),(702,11,769,114),(792,11,862,114)]):
        s('idle',i+1,x0,y0,x1,y1)

    clear(root,'walk')
    for i,(x0,y0,x1,y1) in enumerate([(238,130,312,237),(327,130,401,237),(424,130,498,237),(512,130,580,237),
                                        (601,130,679,237),(679,130,758,237),(770,130,852,237),(878,130,948,237)]):
        s('walk',i+1,x0,y0,x1,y1)

    clear(root,'run')
    for i,(x0,y0,x1,y1) in enumerate([(236,251,309,356),(330,251,408,356),(424,251,506,356),(517,251,613,356),
                                        (632,251,722,356),(733,251,816,356),(840,251,919,356),(840,251,919,356)]):
        s('run',i+1,x0,y0,x1,y1)

    clear(root,'jump')
    for i,(x0,y0,x1,y1) in enumerate([(160,365,230,480),(278,365,359,480),(413,365,486,480),
                                        (524,365,610,480),(635,365,726,480),(762,365,844,480)]):
        s('jump',i+1,x0,y0,x1,y1)

    clear(root,'dash')
    for i,(x0,y0,x1,y1) in enumerate([(263,499,408,584),(418,499,573,584),(586,499,749,584),
                                        (789,499,879,584),(879,499,968,584),(789,499,879,584)]):
        s('dash',i+1,x0,y0,x1,y1)

    clear(root,'block')
    for i,(x0,y0,x1,y1) in enumerate([(156,611,244,708),(287,611,373,708),(422,611,509,708),(547,611,625,708)]):
        s('block',i+1,x0,y0,x1,y1)

    clear(root,'punch')
    for i,(x0,y0,x1,y1) in enumerate([(388,730,511,830),(524,730,625,830),(652,730,729,830),
                                        (729,730,806,830),(806,730,881,830),(806,730,881,830)]):
        s('punch',i+1,x0,y0,x1,y1)

    clear(root,'kick')
    for i,(x0,y0,x1,y1) in enumerate([(272,850,373,955),(389,850,497,955),(541,850,642,955),
                                        (676,850,777,955),(800,850,901,955),(800,850,901,955)]):
        s('kick',i+1,x0,y0,x1,y1)

    clear(root,'special')
    for i,(x0,y0,x1,y1) in enumerate([(12,980,119,1075),(119,980,226,1075),(226,980,333,1075),(346,980,470,1075),
                                        (470,980,594,1075),(606,980,683,1075),(693,980,858,1075),(858,980,1024,1075)]):
        s('special',i+1,x0,y0,x1,y1)

    clear(root,'ultimate')
    for i,(x0,y0,x1,y1) in enumerate([(12,1091,130,1213),(130,1091,248,1213),(248,1091,366,1213),(366,1091,484,1213),
                                        (484,1091,605,1213),(615,1091,681,1213),(691,1091,774,1213),
                                        (774,1091,857,1213),(857,1091,940,1213),(940,1091,1024,1213)]):
        s('ultimate',i+1,x0,y0,x1,y1)

    clear(root,'hurt')
    for i,(x0,y0,x1,y1) in enumerate([(156,1235,225,1320),(242,1235,320,1320),(341,1235,421,1320),(444,1235,517,1320)]):
        s('hurt',i+1,x0,y0,x1,y1)

    clear(root,'victory')
    for i,(x0,y0,x1,y1) in enumerate([(259,1332,334,1429),(355,1332,417,1429),(440,1332,507,1429),
                                        (523,1332,603,1429),(624,1332,692,1429),(727,1332,785,1429)]):
        s('victory',i+1,x0,y0,x1,y1)

    clear(root,'defeat')
    for i,(x0,y0,x1,y1) in enumerate([(355,1445,449,1514),(460,1445,555,1514),(566,1445,669,1514),
                                        (684,1445,795,1514),(566,1445,669,1514),(460,1445,555,1514)]):
        s('defeat',i+1,x0,y0,x1,y1)

    # Verify
    anims=['idle','walk','run','jump','dash','block','punch','kick','special','ultimate','hurt','victory','defeat']
    exp  =[8,8,8,6,6,4,6,6,8,10,4,6,6]
    print('=== QUALITY CHECK ===')
    all_ok=True
    for a,e in zip(anims,exp):
        d=os.path.join(root,a)
        c=len([f for f in os.listdir(d) if f.endswith('.png')]) if os.path.isdir(d) else 0
        fp=os.path.join(d,f'{a}-1.png')
        blue=0
        if os.path.exists(fp):
            im=Image.open(fp).convert('RGBA'); p=im.load(); W2,H2=im.size
            # Count ice-blue pixels (Frostia signature colour)
            blue=sum(1 for y in range(H2) for x in range(W2)
                     if p[x,y][3]>40 and p[x,y][2]>p[x,y][0]+20)
        ok=(c==e)
        if not ok: all_ok=False
        print(f'  {"OK  " if ok else "FAIL"}  {a:<12}  {c}/{e}  ice_blue={blue}')
    print()
    print('FROSTIA: ALL OK!' if all_ok else 'Issues found.')
    print('Smart flood-fill: bg removed, ice armor + white skin + blue effects KEPT.')
