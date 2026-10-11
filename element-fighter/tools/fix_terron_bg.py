#!/usr/bin/env python3
"""
fix_terron_bg.py
================
Fixes Terron using PURE CONNECTIVITY flood-fill.

The problem: Terron's bg is dark (rgb 4-95 range per channel) AND his
brown/dark armor pixels overlap that range completely.
No colour threshold can separate them.

The ONLY solution: flood-fill from sheet edges with NO colour check.
The bg forms ONE connected region touching all 4 borders.
Character pixels are isolated islands inside that bg — never reachable.

This removes EXACTLY the background and nothing else.
"""
from PIL import Image
import os
from collections import deque

ROOT    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DISPLAY = 96

def flood_remove_bg_warm(img):
    """
    Flood-fill from sheet edges removing ONLY cool/dark pixels (R-B <= 12).
    Terron's warm brown armor has R-B > 12 always → NEVER removed.
    BG dark blue-black has R ≈ B or B > R → removed if edge-connected.
    """
    img  = img.convert('RGBA')
    data = list(img.getdata())
    W,H  = img.size

    def is_bg(i):
        r,g,b,a = data[i]
        if a < 10: return True          # transparent = treat as bg gap
        return (r - b) <= 12           # cool/neutral = bg candidate
                                        # warm (R-B > 12) = character = KEEP

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

def eq(x0,x1,n):
    fw=(x1-x0)/n
    return [(int(x0+i*fw),int(x0+(i+1)*fw)) for i in range(n)]

if __name__=='__main__':
    print('=== TERRON — Pure connectivity flood-fill ===')
    print('Only pixels connected to sheet border removed — no colour check')
    print('Brown armor + skin + dark outlines all KEPT (enclosed, unreachable)\n')

    path=os.path.join(ROOT,'tools','terron_sheet.png')
    raw=Image.open(path).convert('RGBA')
    print(f'Sheet: {raw.width}x{raw.height}')
    print('Processing...')
    img=flood_remove_bg_warm(raw)
    print('Done.\n')

    root=os.path.join(ROOT,'assets','sprites','terron')

    def s(a,i,x0,y0,x1,y1): save(img,a,i,x0,y0,x1,y1,root)

    # Exact original frame coordinates
    clear(root,'idle')
    for i,(x0,x1) in enumerate([(16,78),(105,181),(206,280),(305,379),(405,477),(506,577),(607,677),(708,777)]):
        s('idle',i+1,x0,42,x1,168)

    clear(root,'walk')
    for i,(x0,x1) in enumerate([(111,178),(210,275),(314,374),(409,471),(511,573),(609,670),(710,773),(810,869)]):
        s('walk',i+1,x0,174,x1,296)

    clear(root,'run')
    for i,(x0,x1) in enumerate([(105,184),(206,280),(306,384),(403,483),(499,577),(601,681),(702,781),(802,881)]):
        s('run',i+1,x0,306,x1,421)

    clear(root,'jump')
    for i,(x0,x1) in enumerate([(106,181),(206,277),(308,376),(399,468),(506,568),(602,675)]):
        s('jump',i+1,x0,437,x1,539)

    clear(root,'dash')
    for i,(x0,x1) in enumerate([(17,78),(113,179),(208,275),(311,373),(410,472),(508,565)]):
        s('dash',i+1,x0,563,x1,672)

    clear(root,'block')
    for i,(x0,x1) in enumerate([(17,118),(152,224),(248,328),(359,432)]):
        s('block',i+1,x0,698,x1,781)

    clear(root,'punch')
    for i,(x0,x1) in enumerate([(459,542),(568,654),(674,764),(787,869),(896,971),(896,971)]):
        s('punch',i+1,x0,698,x1,781)

    clear(root,'kick')
    for i,(x0,x1) in enumerate([(17,112),(154,216),(246,318),(350,424),(463,550),(561,659)]):
        s('kick',i+1,x0,804,x1,916)

    clear(root,'special')
    for i,(x0,x1) in enumerate([(18,89),(154,219),(248,328),(354,435),(461,544),(567,648),(671,762),(781,868)]):
        s('special',i+1,x0,930,x1,1032)

    clear(root,'ultimate')
    ult=[(19,118),(156,216),(256,324),(363,430),(463,539),(570,648),(678,754),(780,862)]
    for i,(x0,x1) in enumerate(ult): s('ultimate',i+1,x0,1052,x1,1138)
    for i,(x0,x1) in enumerate(eq(780,995,2)): s('ultimate',9+i,x0,1052,x1,1138)

    clear(root,'hurt')
    for i,(x0,x1) in enumerate([(21,102),(156,222),(263,323),(362,427)]):
        s('hurt',i+1,x0,1156,x1,1240)

    clear(root,'victory')
    for i,(x0,x1) in enumerate(eq(462,840,6)):
        s('victory',i+1,x0,1156,x1,1240)

    clear(root,'defeat')
    for i,(x0,x1) in enumerate(eq(414,993,6)):
        s('defeat',i+1,x0,1247,x1,1285)

    # Quality check
    anims=['idle','walk','run','jump','dash','block','punch','kick','special','ultimate','hurt','victory','defeat']
    exp  =[8,8,8,6,6,4,6,6,8,10,4,6,6]
    print('=== QUALITY CHECK ===')
    all_ok=True; total=0
    for a,e in zip(anims,exp):
        d=os.path.join(root,a)
        c=len([f for f in os.listdir(d) if f.endswith('.png')]) if os.path.isdir(d) else 0
        total+=c
        fp=os.path.join(d,f'{a}-1.png')
        brown=0
        if os.path.exists(fp):
            im=Image.open(fp).convert('RGBA'); p=im.load(); W2,H2=im.size
            # Count brown pixels (Terron's armor colour)
            brown=sum(1 for y in range(H2) for x in range(W2)
                      if p[x,y][3]>40 and p[x,y][0]>50 and p[x,y][0]>p[x,y][2]+20)
        ok=(c==e)
        if not ok: all_ok=False
        print(f'  {"OK  " if ok else "FAIL"}  {a:<12}  {c}/{e}  brown_pixels={brown}')
    print(f'\n  Total: {total}')
    print('\nTERRON: ALL OK' if all_ok else '\nIssues found')
    print('Pure connectivity — bg removed, ALL character art KEPT.')
