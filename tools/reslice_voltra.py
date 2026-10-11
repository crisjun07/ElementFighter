#!/usr/bin/env python3
"""Re-slice Voltra with tol=42 flood-fill to remove all grey background."""
from PIL import Image
import os
from collections import deque

ROOT    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DISPLAY = 96

def flood_remove_bg(img, bg_rgb, tol):
    img=img.convert('RGBA'); data=list(img.getdata())
    W,H=img.size; r0,g0,b0=bg_rgb; t2=tol*tol
    def is_bg(i):
        r,g,b,a=data[i]; return (r-r0)**2+(g-g0)**2+(b-b0)**2<=t2
    visited=bytearray(W*H); q=deque()
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

def save(img, anim, idx, x0,y0,x1,y1, root):
    W,H=img.size
    x0=max(0,min(x0,W)); x1=max(0,min(x1,W))
    y0=max(0,min(y0,H)); y1=max(0,min(y1,H))
    if x1<=x0 or y1<=y0: return
    crop=img.crop((x0,y0,x1,y1))
    crop.thumbnail((DISPLAY,DISPLAY),Image.LANCZOS)
    c=Image.new('RGBA',(DISPLAY,DISPLAY),(0,0,0,0))
    c.paste(crop,((DISPLAY-crop.width)//2,(DISPLAY-crop.height)//2),crop)
    os.makedirs(os.path.join(root,anim),exist_ok=True)
    c.save(os.path.join(root,anim,f'{anim}-{idx}.png'),'PNG')

def clr(root,anim):
    d=os.path.join(root,anim); os.makedirs(d,exist_ok=True)
    for f in os.listdir(d):
        if f.endswith('.png'): os.remove(os.path.join(d,f))

def eq(x0,x1,n):
    fw=(x1-x0)/n
    return [(int(x0+i*fw),int(x0+(i+1)*fw)) for i in range(n)]

if __name__=='__main__':
    print('Re-slicing VOLTRA with flood-fill tol=42...')
    raw=Image.open(os.path.join(ROOT,'tools','voltra_sheet.png')).convert('RGBA')
    img=flood_remove_bg(raw,(241,242,243),42)
    root=os.path.join(ROOT,'assets','sprites','voltra')
    print('Background removed.\n')

    # IDLE Band1 y=7-117
    clr(root,'idle')
    for i,(x0,x1) in enumerate([(13,86),(126,208),(232,315),(346,425),(458,540),(576,652),(694,773),(809,887)]):
        save(img,'idle',i+1,x0,7,x1,117,root)

    # WALK Band2 y=134-248
    clr(root,'walk')
    for i,(x0,x1) in enumerate([(10,95),(120,197),(225,314),(347,423),(451,536),(561,649),(675,756),(783,881)]):
        save(img,'walk',i+1,x0,134,x1,248,root)

    # RUN Band3 y=263-365
    clr(root,'run')
    for i,(x0,x1) in enumerate([(12,99),(137,238),(277,385),(416,505),(532,631),(674,789),(811,913),(949,1050)]):
        save(img,'run',i+1,x0,263,x1,365,root)

    # JUMP Band4 y=372-490
    clr(root,'jump')
    for i,(x0,x1) in enumerate([(14,91),(129,217),(258,349),(409,485),(540,627),(680,753)]):
        save(img,'jump',i+1,x0,372,x1,490,root)

    # DASH Band5 y=503-613
    clr(root,'dash')
    for i,(x0,x1) in enumerate([(17,105),(148,222),(258,354),(396,489),(517,621),(653,743)]):
        save(img,'dash',i+1,x0,503,x1,613,root)

    # BLOCK Band6 y=630-730 first 4
    clr(root,'block')
    for i,(x0,x1) in enumerate([(16,112),(129,224),(244,367),(376,441)]):
        save(img,'block',i+1,x0,630,x1,730,root)

    # PUNCH Band6 y=630-730 segs 5-10
    clr(root,'punch')
    for i,(x0,x1) in enumerate([(441,506),(506,572),(572,638),(640,769),(783,897),(927,1044)]):
        save(img,'punch',i+1,x0,630,x1,730,root)

    # KICK Band7 y=736-852 first 6
    clr(root,'kick')
    for i,(x0,x1) in enumerate([(13,101),(117,239),(247,363),(367,485),(502,640),(651,783)]):
        save(img,'kick',i+1,x0,736,x1,852,root)

    # SPECIAL Band7 y=736-852 segs 7-14 (8 frames)
    clr(root,'special')
    spec=[(783,915),(927,1062),(13,101),(117,239),(247,363),(367,485),(502,640),(651,783)]
    for i,(x0,x1) in enumerate(spec[:8]):
        save(img,'special',i+1,x0,736,x1,852,root)

    # ULTIMATE Band8 y=848-1028 10 frames equal-split
    clr(root,'ultimate')
    for i,(x0,x1) in enumerate(eq(17,1176,10)):
        save(img,'ultimate',i+1,x0,848,x1,1028,root)

    # HURT Band8 4 frames
    clr(root,'hurt')
    for i,(x0,x1) in enumerate([(929,1012),(1046,1090),(1090,1134),(1134,1176)]):
        save(img,'hurt',i+1,x0,848,x1,1028,root)

    # VICTORY Band8 6 frames
    clr(root,'victory')
    for i,(x0,x1) in enumerate(eq(520,1176,6)):
        save(img,'victory',i+1,x0,848,x1,1028,root)

    # DEFEAT Band8 6 frames
    clr(root,'defeat')
    for i,(x0,x1) in enumerate(eq(17,1176,6)):
        save(img,'defeat',i+1,x0,848,x1,1028,root)

    # Verify
    anims=['idle','walk','run','jump','dash','block','punch','kick','special','ultimate','hurt','victory','defeat']
    exp  =[8,8,8,6,6,4,6,6,8,10,4,6,6]
    print('=== RESULT ===')
    all_ok=True
    for a,e in zip(anims,exp):
        d=os.path.join(root,a)
        c=len([f for f in os.listdir(d) if f.endswith('.png')]) if os.path.isdir(d) else 0
        fp=os.path.join(d,f'{a}-1.png')
        grey_edge=0
        if os.path.exists(fp):
            im=Image.open(fp).convert('RGBA'); p=im.load(); W2,H2=im.size
            edges=([(0,y) for y in range(H2)]+[(W2-1,y) for y in range(H2)]+
                   [(x,0) for x in range(W2)]+[(x,H2-1) for x in range(W2)])
            grey_edge=sum(1 for (x,y) in edges if p[x,y][3]>50 and p[x,y][0]>170 and p[x,y][1]>170)
        ok=c==e
        if not ok: all_ok=False
        print(f'  {"OK  " if ok else "FAIL"}  {a:<12}  {c}/{e}  grey_edge_pixels={grey_edge}')

    print(f'\n{"VOLTRA ALL OK" if all_ok else "ISSUES"}')
